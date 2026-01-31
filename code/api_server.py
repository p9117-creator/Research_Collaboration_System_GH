#!/usr/bin/env python3
"""
FastAPI Server for Research Collaboration System
Provides REST API endpoints for all database operations
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
import sys

# Add code directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import ResearchDatabaseManager, load_database_config
from query_engine import ResearchQueryEngine
from auth_handler import AuthHandler, Token, get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Research Collaboration System API",
    description="API for managing research collaboration data across multiple NoSQL databases",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connections
db_manager: Optional[ResearchDatabaseManager] = None
query_engine: Optional[ResearchQueryEngine] = None


# Pydantic models for request/response
class ResearcherCreate(BaseModel):
    first_name: str = Field(..., description="Researcher's first name")
    last_name: str = Field(..., description="Researcher's last name")
    email: str = Field(..., description="Researcher's email address")
    department_id: str = Field(..., description="Department ID")
    position: str = Field(..., description="Academic position")
    research_interests: List[str] = Field(default_factory=list, description="Research interests")
    orcid_id: Optional[str] = Field(None, description="ORCID identifier")


class ResearcherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[str] = None
    position: Optional[str] = None
    research_interests: Optional[List[str]] = None


class ResearcherSearch(BaseModel):
    department: Optional[str] = None
    position: Optional[str] = None
    interests: Optional[List[str]] = None
    min_h_index: Optional[int] = None
    max_h_index: Optional[int] = None
    min_publications: Optional[int] = None
    max_publications: Optional[int] = None
    name_search: Optional[str] = None
    sort_by: Optional[str] = "h_index"
    sort_order: Optional[int] = -1
    limit: Optional[int] = 20
    include_collaboration: Optional[bool] = False


class PublicationSearch(BaseModel):
    author_name: Optional[str] = None
    journal: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    keywords: Optional[List[str]] = None
    min_citations: Optional[int] = None
    sort_by: Optional[str] = "citation_count"
    limit: Optional[int] = 20


class CollaborationPairSearch(BaseModel):
    department: Optional[str] = None
    min_collaborations: Optional[int] = 3


class ProjectCreate(BaseModel):
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Project description")
    status: str = Field(default="active", description="Project status")
    principal_investigators: List[str] = Field(default_factory=list, description="List of PI researcher IDs")
    co_investigators: List[str] = Field(default_factory=list, description="List of Co-I researcher IDs")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    funding_amount: Optional[float] = None
    funding_source: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    end_date: Optional[str] = None
    funding_amount: Optional[float] = None


class PublicationCreate(BaseModel):
    title: str = Field(..., description="Publication title")
    publication_type: str = Field(..., description="Type of publication")
    authors: List[str] = Field(default_factory=list, description="List of author researcher IDs")
    journal: Optional[str] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class PublicationUpdate(BaseModel):
    title: Optional[str] = None
    journal: Optional[str] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    keywords: Optional[List[str]] = None


class CollaborationCreate(BaseModel):
    researcher1_id: str
    researcher2_id: str
    collaboration_type: str = Field(default="CO_AUTHORED_WITH", description="Type of collaboration")
    properties: Optional[Dict] = None


class SupervisionCreate(BaseModel):
    supervisor_id: str
    student_id: str
    supervision_type: str = Field(default="phd", description="Type of supervision (phd, masters, postdoc)")
    properties: Optional[Dict] = None


# Dependency to get database connections
async def get_db_manager():
    global db_manager, query_engine
    if db_manager is None:
        config = load_database_config()
        db_manager = ResearchDatabaseManager(config)
        if not db_manager.connect_all():
            raise HTTPException(status_code=500, detail="Failed to connect to databases")
        query_engine = ResearchQueryEngine(db_manager)
    return db_manager


async def get_query_engine():
    global query_engine
    if query_engine is None:
        await get_db_manager()
    return query_engine


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# ============ Authentication Endpoints ============

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Login endpoint to get JWT token"""
    user = db.mongodb.get_user_by_email(form_data.username)
    if not user or not AuthHandler.verify_password(form_data.password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = AuthHandler.create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Researcher endpoints
@app.get("/researchers/{researcher_id}")
async def get_researcher_profile(
    researcher_id: str,
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Get complete researcher profile"""
    try:
        profile = qe.get_researcher_profile_complete(researcher_id)
        if "error" in profile:
            raise HTTPException(status_code=404, detail=profile["error"])
        return profile
    except Exception as e:
        logger.error(f"Failed to get researcher profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/researchers/search")
async def search_researchers(
    search: ResearcherSearch,
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Advanced researcher search"""
    try:
        criteria = search.dict()
        results = qe.search_researchers_advanced(criteria)
        return {
            "results": results,
            "count": len(results),
            "query": criteria
        }
    except Exception as e:
        logger.error(f"Researcher search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/researchers")
async def list_researchers(
    department: Optional[str] = Query(None, description="Filter by department"),
    limit: int = Query(50, description="Number of results to return"),
    skip: int = Query(0, description="Number of results to skip"),
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """List researchers with optional filtering"""
    try:
        query = {}
        if department:
            query["academic_profile.department_id"] = department
        
        db = qe.db_manager.mongodb
        researchers = db.search_researchers(query)
        
        # Apply pagination
        total_count = len(researchers)
        paginated_researchers = researchers[skip:skip + limit]
        
        # Add basic collaboration info
        for researcher in paginated_researchers:
            researcher_id = researcher["_id"]
            collaborators = qe.db_manager.neo4j.find_collaborators(researcher_id, max_depth=1)
            researcher["collaborator_count"] = len(collaborators)
        
        return {
            "researchers": paginated_researchers,
            "total_count": total_count,
            "limit": limit,
            "skip": skip,
            "has_more": skip + limit < total_count
        }
    except Exception as e:
        logger.error(f"Failed to list researchers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Collaboration endpoints
@app.post("/collaborations/pairs")
async def find_collaboration_pairs(
    search: CollaborationPairSearch,
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Find collaboration pairs"""
    try:
        criteria = search.dict()
        pairs = qe.find_collaboration_pairs(
            criteria.get("department"),
            criteria.get("min_collaborations", 3)
        )
        return {
            "pairs": pairs,
            "count": len(pairs),
            "criteria": criteria
        }
    except Exception as e:
        logger.error(f"Failed to find collaboration pairs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collaborations/network/{researcher_id}")
async def get_collaboration_network(
    researcher_id: str,
    max_depth: int = Query(2, description="Maximum depth of network traversal"),
    limit: int = Query(20, description="Maximum number of collaborators to return"),
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Get collaboration network for a researcher"""
    try:
        collaborators = qe.db_manager.neo4j.find_collaborators(researcher_id, max_depth)
        
        # Limit results
        network = collaborators[:limit]
        
        # Add profile information for each collaborator
        for collaborator in network:
            profile = qe.get_researcher_profile_complete(collaborator["id"])
            if "error" not in profile:
                collaborator["profile"] = {
                    "basic_info": profile.get("basic_info", {}),
                    "academic_profile": profile.get("academic_profile", {}),
                    "research_interests": profile.get("research_interests", [])
                }
        
        return {
            "researcher_id": researcher_id,
            "network": network,
            "network_size": len(network),
            "max_depth": max_depth
        }
    except Exception as e:
        logger.error(f"Failed to get collaboration network: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics endpoints
@app.get("/analytics/department/{department_id}")
async def get_department_analytics(
    department_id: str,
    days: int = Query(30, description="Number of days for analytics"),
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Get department analytics"""
    try:
        analytics = qe.get_department_analytics(department_id, days)
        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])
        return analytics
    except Exception as e:
        logger.error(f"Failed to get department analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/publications")
async def get_publication_analytics(
    days: int = Query(365, description="Number of days for analytics"),
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Get publication analytics"""
    try:
        analytics = qe.get_publication_analytics(days)
        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])
        return analytics
    except Exception as e:
        logger.error(f"Failed to get publication analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/research-trends")
async def get_research_trends(
    department: Optional[str] = Query(None, description="Filter by department"),
    days: int = Query(365, description="Number of days for analysis"),
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Get research trends analysis"""
    try:
        trends = qe.get_research_trends(department, days)
        if "error" in trends:
            raise HTTPException(status_code=500, detail=trends["error"])
        return trends
    except Exception as e:
        logger.error(f"Failed to get research trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Publication endpoints
@app.post("/publications/search")
async def search_publications(
    search: PublicationSearch,
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Advanced publication search"""
    try:
        criteria = search.dict()
        results = qe.search_publications_advanced(criteria)
        return {
            "publications": results,
            "count": len(results),
            "query": criteria
        }
    except Exception as e:
        logger.error(f"Publication search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/publications/{publication_id}")
async def get_publication(
    publication_id: str,
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Get publication details"""
    try:
        publications = qe.db_manager.mongodb.search_researchers({"_id": publication_id})
        if not publications:
            raise HTTPException(status_code=404, detail="Publication not found")
        
        publication = publications[0]
        
        # Add author details
        authors_with_details = []
        for author in publication.get("authors", []):
            author_profile = qe.get_researcher_profile_complete(author.get("researcher_id", ""))
            if "error" not in author_profile:
                authors_with_details.append({
                    "researcher_id": author.get("researcher_id"),
                    "author_order": author.get("author_order"),
                    "contribution": author.get("contribution"),
                    "name": f"{author_profile.get('basic_info', {}).get('first_name', '')} {author_profile.get('basic_info', {}).get('last_name', '')}",
                    "department": author_profile.get('academic_profile', {}).get('department_id', '')
                })
        
        publication["authors_with_details"] = authors_with_details
        
        return publication
    except Exception as e:
        logger.error(f"Failed to get publication: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics endpoints
@app.get("/stats/overview")
async def get_system_overview(
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Get system overview statistics"""
    try:
        # Get basic counts
        db = qe.db_manager.mongodb
        
        total_researchers = len(db.search_researchers({}))
        total_projects = len(db.search_researchers({"status": {"$exists": True}}))  # projects collection
        total_publications = len(db.search_researchers({"title": {"$exists": True}}))  # publications collection
        
        # Get department stats
        departments = ["dept_cs", "dept_bio", "dept_chem", "dept_math", "dept_physics"]
        dept_stats = {}
        
        for dept in departments:
            researchers = db.search_researchers({"academic_profile.department_id": dept})
            dept_stats[dept] = {
                "researcher_count": len(researchers),
                "avg_h_index": sum(r.get("collaboration_metrics", {}).get("h_index", 0) for r in researchers) / max(len(researchers), 1)
            }
        
        # Get recent activity
        recent_date = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
        recent_publications = db.search_researchers({
            "bibliographic_info.publication_date": {"$gte": recent_date}
        })
        
        return {
            "total_researchers": total_researchers,
            "total_projects": total_projects,
            "total_publications": total_publications,
            "department_statistics": dept_stats,
            "recent_activity": {
                "recent_publications": len(recent_publications)
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Cache management endpoints
@app.post("/cache/clear")
async def clear_cache(
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Clear Redis cache"""
    try:
        redis_client = qe.db_manager.redis.client
        redis_client.flushdb()  # Clear current database
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
async def get_cache_stats(
    qe: ResearchQueryEngine = Depends(get_query_engine)
):
    """Get Redis cache statistics"""
    try:
        redis_client = qe.db_manager.redis.client
        info = redis_client.info()
        
        return {
            "used_memory": info.get("used_memory"),
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
            "cache_hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Database status endpoints
@app.get("/db/status")
async def get_database_status(
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Get database connection status"""
    try:
        status = {
            "mongodb": "connected",
            "neo4j": "connected", 
            "redis": "connected",
            "cassandra": "connected"
        }
        
        # Test each connection
        try:
            db.mongodb.client.admin.command('ping')
        except:
            status["mongodb"] = "disconnected"
            
        try:
            with db.neo4j.driver.session() as session:
                session.run("RETURN 1")
        except:
            status["neo4j"] = "disconnected"
            
        try:
            db.redis.client.ping()
        except:
            status["redis"] = "disconnected"
            
        try:
            db.cassandra.session.execute("SELECT 1")
        except:
            status["cassandra"] = "disconnected"
        
        return status
    except Exception as e:
        logger.error(f"Failed to get database status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Researcher CRUD Endpoints ============

@app.post("/researchers", tags=["Researchers"])
async def create_researcher(
    researcher: ResearcherCreate,
    db: ResearchDatabaseManager = Depends(get_db_manager),
    current_user: dict = Depends(get_current_user)
):
    """Create a new researcher"""
    try:
        researcher_data = {
            "personal_info": {
                "first_name": researcher.first_name,
                "last_name": researcher.last_name,
                "email": researcher.email
            },
            "academic_profile": {
                "department_id": researcher.department_id,
                "position": researcher.position
            },
            "research_interests": researcher.research_interests,
            "collaboration_metrics": {
                "total_publications": 0,
                "h_index": 0,
                "collaboration_score": 0
            }
        }
        if researcher.orcid_id:
            researcher_data["personal_info"]["orcid_id"] = researcher.orcid_id
        
        researcher_id = db.create_researcher_comprehensive(researcher_data)
        return {"researcher_id": researcher_id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create researcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/researchers/{researcher_id}", tags=["Researchers"])
async def update_researcher(
    researcher_id: str,
    researcher: ResearcherUpdate,
    db: ResearchDatabaseManager = Depends(get_db_manager),
    current_user: dict = Depends(get_current_user)
):
    """Update a researcher"""
    try:
        update_data = {}
        if researcher.first_name:
            update_data["personal_info.first_name"] = researcher.first_name
        if researcher.last_name:
            update_data["personal_info.last_name"] = researcher.last_name
        if researcher.email:
            update_data["personal_info.email"] = researcher.email
        if researcher.department_id:
            update_data["academic_profile.department_id"] = researcher.department_id
        if researcher.position:
            update_data["academic_profile.position"] = researcher.position
        if researcher.research_interests:
            update_data["research_interests"] = researcher.research_interests
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        success = db.update_researcher_comprehensive(researcher_id, update_data)
        if success:
            return {"researcher_id": researcher_id, "status": "updated"}
        else:
            raise HTTPException(status_code=404, detail="Researcher not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update researcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/researchers/{researcher_id}", tags=["Researchers"])
async def delete_researcher(
    researcher_id: str,
    db: ResearchDatabaseManager = Depends(get_db_manager),
    current_user: dict = Depends(get_current_user)
):
    """Delete a researcher from all databases"""
    try:
        success = db.delete_researcher_comprehensive(researcher_id)
        if success:
            return {"researcher_id": researcher_id, "status": "deleted"}
        else:
            raise HTTPException(status_code=404, detail="Researcher not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete researcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/researchers/{researcher_id}/relationships", tags=["Researchers"])
async def get_researcher_relationships(
    researcher_id: str,
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Get all relationships for a researcher"""
    try:
        relationships = db.neo4j.get_researcher_relationships(researcher_id)
        return relationships
    except Exception as e:
        logger.error(f"Failed to get researcher relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/researchers/{researcher_id}/supervision-chain", tags=["Researchers"])
async def get_supervision_chain(
    researcher_id: str,
    direction: str = Query("up", description="Direction: 'up' for supervisors, 'down' for students"),
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Get supervision chain (academic genealogy)"""
    try:
        chain = db.neo4j.find_supervision_chain(researcher_id, direction)
        return {"researcher_id": researcher_id, "direction": direction, "chain": chain}
    except Exception as e:
        logger.error(f"Failed to get supervision chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Project CRUD Endpoints ============

@app.post("/projects", tags=["Projects"])
async def create_project(
    project: ProjectCreate,
    db: ResearchDatabaseManager = Depends(get_db_manager),
    current_user: dict = Depends(get_current_user)
):
    """Create a new project"""
    try:
        project_data = {
            "title": project.title,
            "description": project.description,
            "status": project.status,
            "participants": {
                "principal_investigators": [{"researcher_id": pid} for pid in project.principal_investigators],
                "co_investigators": [{"researcher_id": cid} for cid in project.co_investigators]
            }
        }
        if project.start_date:
            project_data["timeline"] = {"start_date": project.start_date}
        if project.end_date:
            project_data.setdefault("timeline", {})["end_date"] = project.end_date
        if project.funding_amount:
            project_data["funding"] = {"amount": project.funding_amount}
        if project.funding_source:
            project_data.setdefault("funding", {})["source"] = project.funding_source
        
        project_id = db.create_project_comprehensive(project_data)
        return {"project_id": project_id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}", tags=["Projects"])
async def get_project(
    project_id: str,
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Get project details"""
    try:
        project = db.mongodb.get_project(project_id)
        if project:
            return project
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/projects/{project_id}", tags=["Projects"])
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Update a project"""
    try:
        update_data = {}
        if project.title:
            update_data["title"] = project.title
        if project.description:
            update_data["description"] = project.description
        if project.status:
            update_data["status"] = project.status
        if project.end_date:
            update_data["timeline.end_date"] = project.end_date
        if project.funding_amount:
            update_data["funding.amount"] = project.funding_amount
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        success = db.update_project_comprehensive(project_id, update_data)
        if success:
            return {"project_id": project_id, "status": "updated"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/projects/{project_id}", tags=["Projects"])
async def delete_project(
    project_id: str,
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Delete a project"""
    try:
        success = db.delete_project_comprehensive(project_id)
        if success:
            return {"project_id": project_id, "status": "deleted"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects", tags=["Projects"])
async def list_projects(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of results"),
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """List projects"""
    try:
        query = {}
        if status:
            query["status"] = status
        projects = db.mongodb.search_projects(query, limit=limit)
        return {"projects": projects, "count": len(projects)}
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Publication CRUD Endpoints ============

@app.post("/publications", tags=["Publications"])
async def create_publication(
    publication: PublicationCreate,
    db: ResearchDatabaseManager = Depends(get_db_manager),
    current_user: dict = Depends(get_current_user)
):
    """Create a new publication"""
    try:
        pub_data = {
            "title": publication.title,
            "publication_type": publication.publication_type,
            "authors": [{"researcher_id": aid, "author_order": i+1} for i, aid in enumerate(publication.authors)],
            "keywords": publication.keywords
        }
        if publication.journal:
            pub_data["bibliographic_info"] = {"journal": publication.journal}
        if publication.publication_date:
            pub_data.setdefault("bibliographic_info", {})["publication_date"] = publication.publication_date
        if publication.doi:
            pub_data.setdefault("bibliographic_info", {})["doi"] = publication.doi
        
        pub_id = db.create_publication_comprehensive(pub_data)
        return {"publication_id": pub_id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create publication: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/publications/{publication_id}", tags=["Publications"])
async def update_publication(
    publication_id: str,
    publication: PublicationUpdate,
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Update a publication"""
    try:
        update_data = {}
        if publication.title:
            update_data["title"] = publication.title
        if publication.journal:
            update_data["bibliographic_info.journal"] = publication.journal
        if publication.publication_date:
            update_data["bibliographic_info.publication_date"] = publication.publication_date
        if publication.doi:
            update_data["bibliographic_info.doi"] = publication.doi
        if publication.keywords:
            update_data["keywords"] = publication.keywords
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        success = db.update_publication_comprehensive(publication_id, update_data)
        if success:
            return {"publication_id": publication_id, "status": "updated"}
        else:
            raise HTTPException(status_code=404, detail="Publication not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update publication: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/publications/{publication_id}", tags=["Publications"])
async def delete_publication(
    publication_id: str,
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Delete a publication"""
    try:
        success = db.delete_publication_comprehensive(publication_id)
        if success:
            return {"publication_id": publication_id, "status": "deleted"}
        else:
            raise HTTPException(status_code=404, detail="Publication not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete publication: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/publications", tags=["Publications"])
async def list_publications(
    limit: int = Query(50, description="Number of results"),
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """List publications"""
    try:
        publications = db.mongodb.search_publications({}, limit=limit)
        return {"publications": publications, "count": len(publications)}
    except Exception as e:
        logger.error(f"Failed to list publications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Collaboration & Supervision Endpoints ============

@app.post("/collaborations", tags=["Collaborations"])
async def create_collaboration(
    collab: CollaborationCreate,
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Create a collaboration relationship"""
    try:
        success = db.add_collaboration(
            collab.researcher1_id,
            collab.researcher2_id,
            collab.collaboration_type,
            collab.properties
        )
        if success:
            return {"status": "created", "type": collab.collaboration_type}
        else:
            raise HTTPException(status_code=500, detail="Failed to create collaboration")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create collaboration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/supervisions", tags=["Collaborations"])
async def create_supervision(
    supervision: SupervisionCreate,
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Create a supervision relationship"""
    try:
        success = db.neo4j.create_supervision_relationship(
            supervision.supervisor_id,
            supervision.student_id,
            supervision.supervision_type,
            supervision.properties
        )
        if success:
            return {"status": "created", "type": supervision.supervision_type}
        else:
            raise HTTPException(status_code=500, detail="Failed to create supervision")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create supervision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ System Statistics Endpoints ============

@app.get("/stats/system", tags=["Statistics"])
async def get_system_statistics(
    db: ResearchDatabaseManager = Depends(get_db_manager)
):
    """Get comprehensive system statistics from all databases"""
    try:
        stats = db.get_system_statistics()
        return stats
    except Exception as e:
        logger.error(f"Failed to get system statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.utcnow().isoformat()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.utcnow().isoformat()}
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connections on startup"""
    try:
        logger.info("Starting Research Collaboration System API...")
        config = load_database_config()
        global db_manager, query_engine
        db_manager = ResearchDatabaseManager(config)
        if db_manager.connect_all():
            query_engine = ResearchQueryEngine(db_manager)
            logger.info("Database connections established successfully")
        else:
            logger.error("Failed to establish database connections")
    except Exception as e:
        logger.error(f"Startup failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown"""
    try:
        logger.info("Shutting down Research Collaboration System API...")
        if db_manager:
            db_manager.disconnect_all()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
