#!/usr/bin/env python3
"""
Query Engine for Research Collaboration System
Implements complex queries across multiple NoSQL databases
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date, timedelta
import json
import statistics
from database_manager import ResearchDatabaseManager, load_database_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchQueryEngine:
    """Advanced query engine for research collaboration data"""
    
    def __init__(self, db_manager: ResearchDatabaseManager):
        self.db_manager = db_manager
        
    def get_researcher_profile_complete(self, researcher_id: str) -> Dict[str, Any]:
        """Get complete researcher profile combining data from all databases"""
        try:
            profile = {
                "researcher_id": researcher_id,
                "basic_info": {},
                "academic_profile": {},
                "collaboration_network": {},
                "publications": {},
                "projects": {},
                "analytics": {},
                "cache_status": "miss"
            }
            
            # Retrieve researcher data
            researcher_data = None
            
            # Get from cache first
            cached_profile = self.db_manager.redis.get_cached_researcher_profile(researcher_id)
            if cached_profile:
                researcher_data = cached_profile
                profile["cache_status"] = "hit"
                logger.info(f"Retrieved researcher profile from cache: {researcher_id}")
            else:
                # Get from MongoDB (primary source)
                mongo_profile = self.db_manager.mongodb.get_researcher(researcher_id)
                if not mongo_profile:
                    logger.warning(f"Researcher not found: {researcher_id}")
                    return {"error": "Researcher not found"}
                
                researcher_data = mongo_profile
                # Cache the profile
                self.db_manager.redis.cache_researcher_profile(researcher_id, mongo_profile)
                logger.info(f"Cached researcher profile: {researcher_id}")
            
            # Map raw data to profile structure consistently
            profile["basic_info"] = researcher_data.get("personal_info", {})
            profile["academic_profile"] = researcher_data.get("academic_profile", {})
            profile["research_interests"] = researcher_data.get("research_interests", [])
            profile["collaboration_metrics"] = researcher_data.get("collaboration_metrics", {})
            
            # Get collaboration network from Neo4j
            collaborators = self.db_manager.neo4j.find_collaborators(researcher_id)
            profile["collaboration_network"] = {
                "collaborators": collaborators,
                "collaboration_count": len(collaborators),
                "network_depth": 2
            }
            
            # Get publications from MongoDB
            publications = self.db_manager.mongodb.find_documents("publications", {
                "authors.researcher_id": researcher_id
            })
            
            # Filter and process publications
            researcher_publications = []
            for pub in publications:
                for author in pub.get("authors", []):
                    if author.get("researcher_id") == researcher_id:
                        researcher_publications.append({
                            "publication_id": pub.get("_id"),
                            "title": pub.get("title"),
                            "bibliographic_info": pub.get("bibliographic_info", {}),
                            "author_order": author.get("author_order"),
                            "contribution": author.get("contribution"),
                            "metrics": pub.get("metrics", {})
                        })
            
            profile["publications"] = {
                "list": researcher_publications,
                "count": len(researcher_publications),
                "total_citations": sum(p["metrics"].get("citation_count", 0) for p in researcher_publications)
            }
            
            # Get projects from MongoDB
            projects = self.db_manager.mongodb.find_documents("projects", {
                "$or": [
                    {"participants.principal_investigators.researcher_id": researcher_id},
                    {"participants.co_investigators.researcher_id": researcher_id},
                    {"participants.research_assistants.researcher_id": researcher_id}
                ]
            })
            
            profile["projects"] = {
                "list": projects,
                "count": len(projects)
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get complete researcher profile: {e}")
            return {"error": str(e)}
    
    def search_researchers_advanced(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advanced researcher search with multiple criteria"""
        try:
            query = {}
            
            # Department filter
            if criteria.get("department"):
                query["academic_profile.department_id"] = criteria["department"]
            
            # Position filter
            if criteria.get("position"):
                query["academic_profile.position"] = criteria["position"]
            
            # Research interests filter
            if criteria.get("interests"):
                interests = criteria["interests"] if isinstance(criteria["interests"], list) else [criteria["interests"]]
                query["research_interests"] = {"$in": interests}
            
            # H-index range
            if criteria.get("min_h_index") or criteria.get("max_h_index"):
                h_index_query = {}
                if criteria.get("min_h_index"):
                    h_index_query["$gte"] = criteria["min_h_index"]
                if criteria.get("max_h_index"):
                    h_index_query["$lte"] = criteria["max_h_index"]
                query["collaboration_metrics.h_index"] = h_index_query
            
            # Publication count range
            if criteria.get("min_publications") or criteria.get("max_publications"):
                pub_query = {}
                if criteria.get("min_publications"):
                    pub_query["$gte"] = criteria["min_publications"]
                if criteria.get("max_publications"):
                    pub_query["$lte"] = criteria["max_publications"]
                query["collaboration_metrics.total_publications"] = pub_query
            
            # Name search

            if criteria.get("name_search"):
                name_query = criteria["name_search"].strip()
                tokens = name_query.split()
                
                if len(tokens) > 1:
                    # For multi-word queries, each token must match part of the name
                    and_conditions = []
                    for token in tokens:
                        and_conditions.append({
                            "$or": [
                                {"personal_info.first_name": {"$regex": token, "$options": "i"}},
                                {"personal_info.last_name": {"$regex": token, "$options": "i"}}
                            ]
                        })
                    
                    # Add to main query
                    if "$and" in query:
                        query["$and"].extend(and_conditions)
                    else:
                        query["$and"] = and_conditions
                else:
                    # Single word query
                    query["$or"] = [
                        {"personal_info.first_name": {"$regex": name_query, "$options": "i"}},
                        {"personal_info.last_name": {"$regex": name_query, "$options": "i"}}
                    ]
            
            # Execute search
            researchers = self.db_manager.mongodb.search_researchers(query)
            
            # Ensure IDs are strings
            for r in researchers:
                if '_id' in r:
                    r['_id'] = str(r['_id'])
            
            # Add collaboration data for top results
            if criteria.get("include_collaboration") and researchers:
                for researcher in researchers[:10]:  # Limit to top 10 for performance
                    collaborators = self.db_manager.neo4j.find_collaborators(researcher["_id"], max_depth=1)
                    researcher["collaborators"] = collaborators
            
            # Sort results
            sort_by = criteria.get("sort_by", "collaboration_metrics.h_index")
            sort_order = criteria.get("sort_order", -1)  # Descending by default
            
            if sort_by in ["h_index", "publication_count", "citation_count"]:
                researchers.sort(
                    key=lambda x: x.get("collaboration_metrics", {}).get(sort_by.replace("_", "_"), 0),
                    reverse=sort_order < 0
                )
            
            # Limit results
            limit = criteria.get("limit", 20)
            return researchers[:limit]
            
        except Exception as e:
            logger.error(f"Advanced researcher search failed: {e}")
            return []
    
    def find_collaboration_pairs(self, department: str = None, min_collaborations: int = 1) -> List[Dict[str, Any]]:
        """Find most collaborative researcher pairs efficiently"""
        try:
            # 1. Get researchers for the department form MongoDB
            query = {}
            if department:
                query["academic_profile.department_id"] = department
            
            researchers = self.db_manager.mongodb.search_researchers(query)
            
            # Create a map for quick access to names and filter IDs
            researcher_map = {}
            for r in researchers:
                # Handle _id being ObjectId or string
                r_id = str(r["_id"])
                name = f"{r.get('personal_info', {}).get('first_name', '')} {r.get('personal_info', {}).get('last_name', '')}"
                researcher_map[r_id] = name
                
            researcher_ids = list(researcher_map.keys())
            
            if not researcher_ids:
                return []

            # 2. Query Neo4j for relationships between these researchers
            # We use the driver directly to execute a custom query
            with self.db_manager.neo4j.driver.session() as session:
                cypher_query = """
                MATCH (r1:Researcher)-[c:CO_AUTHORED_WITH]-(r2:Researcher)
                WHERE r1.id IN $ids AND r2.id IN $ids AND elementId(r1) < elementId(r2)
                RETURN r1.id as source_id, r2.id as target_id, c.strength as strength
                ORDER BY c.strength DESC
                LIMIT 20
                """
                # Note: elementId(r1) < elementId(r2) ensures we only get one direction for each pair
                
                result = session.run(cypher_query, ids=researcher_ids)
                
                collaboration_pairs = []
                
                for record in result:
                    strength = record['strength']
                    # Handle if strength is None
                    if strength is None:
                        strength = 0
                        
                    if strength < min_collaborations:
                        continue
                        
                    source_id = record['source_id']
                    target_id = record['target_id']

                    collaboration_pairs.append({
                        "researcher1_id": source_id,
                        "researcher1_name": researcher_map.get(source_id, "Unknown"),
                        "researcher2_id": target_id,
                        "researcher2_name": researcher_map.get(target_id, "Unknown"),
                        "collaboration_strength": strength,
                        "department": department
                    })
            
            return collaboration_pairs
            
        except Exception as e:
            logger.error(f"Failed to find collaboration pairs: {e}")
            return []
    
    def _get_researcher_name(self, researcher_id: str) -> str:
        """Get researcher name by ID"""
        researcher = self.db_manager.mongodb.get_researcher(researcher_id)
        if researcher:
            personal_info = researcher.get("personal_info", {})
            return f"{personal_info.get('first_name', '')} {personal_info.get('last_name', '')}"
        return "Unknown"
    
    def get_department_analytics(self, department_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive department analytics"""
        try:
            # Get researchers in department
            researchers = self.db_manager.mongodb.search_researchers({
                "academic_profile.department_id": department_id
            })
            
            # Calculate basic metrics
            total_researchers = len(researchers)
            total_publications = sum(r.get("collaboration_metrics", {}).get("total_publications", 0) for r in researchers)
            total_citations = sum(r.get("collaboration_metrics", {}).get("citation_count", 0) for r in researchers)
            h_indices = [r.get("collaboration_metrics", {}).get("h_index", 0) for r in researchers if r.get("collaboration_metrics", {}).get("h_index", 0) > 0]
            avg_h_index = statistics.mean(h_indices) if h_indices else 0
            
            # Get active projects
            active_projects = self.db_manager.mongodb.find_documents("projects", {
                "status": "active",
                "participants.principal_investigators.researcher_id": {"$in": [r["_id"] for r in researchers]}
            })
            
            # Get recent publications (last 30 days)
            recent_date = (date.today() - timedelta(days=30)).isoformat()
            # Get recent publications (last 30 days)
            recent_date = (date.today() - timedelta(days=30)).isoformat()
            recent_publications = self.db_manager.mongodb.find_documents("publications", {
                "authors.researcher_id": {"$in": [r["_id"] for r in researchers]},
                "bibliographic_info.publication_date": {"$gte": recent_date}
            })
            
            # Get collaboration network stats
            collaboration_stats = self._calculate_department_collaboration_stats(researchers)
            
            # Get time-series data from Cassandra
            cassandra_analytics = self.db_manager.cassandra.get_department_analytics(department_id, days)
            
            analytics = {
                "department_id": department_id,
                "period_days": days,
                "basic_metrics": {
                    "total_researchers": total_researchers,
                    "total_publications": total_publications,
                    "total_citations": total_citations,
                    "average_h_index": round(avg_h_index, 2),
                    "active_projects": len(active_projects),
                    "recent_publications": len(recent_publications)
                },
                "collaboration_stats": collaboration_stats,
                "time_series": cassandra_analytics,
                "top_researchers": self._get_top_researchers_by_metric(researchers, "h_index", 5),
                "research_areas": self._extract_research_areas(researchers),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get department analytics: {e}")
            return {"error": str(e)}
    
    def _calculate_department_collaboration_stats(self, researchers: List[Dict]) -> Dict[str, Any]:
        """Calculate collaboration statistics for department"""
        try:
            researcher_ids = [r["_id"] for r in researchers]
            
            # Count unique collaboration relationships
            collaboration_count = 0
            collaboration_strengths = []
            
            for researcher_id in researcher_ids:
                collaborators = self.db_manager.neo4j.find_collaborators(researcher_id, max_depth=1)
                for collaborator in collaborators:
                    if collaborator["id"] in researcher_ids:
                        collaboration_count += 1
                        collaboration_strengths.append(collaborator.get("collaboration_strength", 0))
            
            # Avoid double counting (each collaboration counted twice)
            collaboration_count = collaboration_count // 2
            
            # Calculate collaboration metrics
            avg_collaboration_strength = statistics.mean(collaboration_strengths) if collaboration_strengths else 0
            max_collaboration_strength = max(collaboration_strengths) if collaboration_strengths else 0
            
            # Calculate collaboration rate
            total_possible_collaborations = len(researcher_ids) * (len(researcher_ids) - 1) // 2
            collaboration_rate = collaboration_count / total_possible_collaborations if total_possible_collaborations > 0 else 0
            
            return {
                "total_collaborations": collaboration_count,
                "average_collaboration_strength": round(avg_collaboration_strength, 2),
                "max_collaboration_strength": round(max_collaboration_strength, 2),
                "collaboration_rate": round(collaboration_rate, 3),
                "total_possible_collaborations": total_possible_collaborations
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate collaboration stats: {e}")
            return {}
    
    def _get_top_researchers_by_metric(self, researchers: List[Dict], metric: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top researchers by specified metric"""
        try:
            # Sort researchers by metric
            sorted_researchers = sorted(
                researchers,
                key=lambda x: x.get("collaboration_metrics", {}).get(metric, 0),
                reverse=True
            )
            
            top_researchers = []
            for researcher in sorted_researchers[:limit]:
                personal_info = researcher.get("personal_info", {})
                top_researchers.append({
                    "researcher_id": researcher["_id"],
                    "name": f"{personal_info.get('first_name', '')} {personal_info.get('last_name', '')}",
                    "metric_value": researcher.get("collaboration_metrics", {}).get(metric, 0),
                    "department": researcher.get("academic_profile", {}).get("department_id", ""),
                    "position": researcher.get("academic_profile", {}).get("position", "")
                })
            
            return top_researchers
            
        except Exception as e:
            logger.error(f"Failed to get top researchers: {e}")
            return []
    
    def _extract_research_areas(self, researchers: List[Dict]) -> Dict[str, int]:
        """Extract and count research areas from researchers"""
        try:
            research_areas = {}
            
            for researcher in researchers:
                interests = researcher.get("research_interests", [])
                for interest in interests:
                    research_areas[interest] = research_areas.get(interest, 0) + 1
            
            # Sort by frequency
            sorted_areas = dict(sorted(research_areas.items(), key=lambda x: x[1], reverse=True))
            
            return sorted_areas
            
        except Exception as e:
            logger.error(f"Failed to extract research areas: {e}")
            return {}
    
    def get_publication_analytics(self, time_period: int = 365) -> Dict[str, Any]:
        """Get publication analytics across all databases"""
        try:
            # Get publications from MongoDB
            start_date = (date.today() - timedelta(days=time_period)).isoformat()
            
            publications = self.db_manager.mongodb.find_documents("publications", {
                "bibliographic_info.publication_date": {"$gte": start_date}
            })
            
            # Calculate metrics
            total_publications = len(publications)
            total_citations = sum(p.get("metrics", {}).get("citation_count", 0) for p in publications)
            avg_citations = total_citations / total_publications if total_publications > 0 else 0
            
            # Get department distribution
            dept_distribution = {}
            for pub in publications:
                for author in pub.get("authors", []):
                    researcher = self.db_manager.mongodb.get_researcher(author.get("researcher_id", ""))
                    if researcher:
                        dept = researcher.get("academic_profile", {}).get("department_id", "Unknown")
                        dept_distribution[dept] = dept_distribution.get(dept, 0) + 1
            
            # Get publication type distribution
            type_distribution = {}
            for pub in publications:
                pub_type = pub.get("publication_type", "Unknown")
                type_distribution[pub_type] = type_distribution.get(pub_type, 0) + 1
            
            # Get top journals
            journal_distribution = {}
            for pub in publications:
                journal = pub.get("bibliographic_info", {}).get("journal", "Unknown")
                journal_distribution[journal] = journal_distribution.get(journal, 0) + 1
            
            # Sort top journals
            top_journals = dict(sorted(journal_distribution.items(), key=lambda x: x[1], reverse=True)[:10])
            
            analytics = {
                "time_period_days": time_period,
                "basic_metrics": {
                    "total_publications": total_publications,
                    "total_citations": total_citations,
                    "average_citations_per_publication": round(avg_citations, 2)
                },
                "department_distribution": dept_distribution,
                "publication_type_distribution": type_distribution,
                "top_journals": top_journals,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get publication analytics: {e}")
            return {"error": str(e)}
    
    def search_publications_advanced(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advanced publication search"""
        try:
            query = {}
            
            # Author filter
            if criteria.get("author_name"):
                author_query = criteria["author_name"]
                query["$or"] = [
                    {"authors.researcher_id": {"$in": self._find_researchers_by_name(author_query)}}
                ]
            
            # Journal filter
            if criteria.get("journal"):
                query["bibliographic_info.journal"] = {"$regex": criteria["journal"], "$options": "i"}
            
            # Date range
            if criteria.get("start_date") or criteria.get("end_date"):
                date_query = {}
                if criteria.get("start_date"):
                    date_query["$gte"] = criteria["start_date"]
                if criteria.get("end_date"):
                    date_query["$lte"] = criteria["end_date"]
                query["bibliographic_info.publication_date"] = date_query
            
            # Keywords
            if criteria.get("keywords"):
                keywords = criteria["keywords"] if isinstance(criteria["keywords"], list) else [criteria["keywords"]]
                query["$or"] = [
                    {"keywords": {"$in": keywords}},
                    {"title": {"$regex": "|".join(keywords), "$options": "i"}}
                ]
            
            # Citation threshold
            if criteria.get("min_citations"):
                query["metrics.citation_count"] = {"$gte": criteria["min_citations"]}
            
            # Execute search
            publications = self.db_manager.mongodb.find_documents("publications", query)
            
            # Process results
            processed_publications = []
            for pub in publications:
                processed_pub = {
                    "publication_id": pub.get("_id"),
                    "title": pub.get("title"),
                    "authors": [
                        {
                            "researcher_id": author.get("researcher_id"),
                            "name": self._get_researcher_name(author.get("researcher_id", "")),
                            "author_order": author.get("author_order"),
                            "contribution": author.get("contribution")
                        }
                        for author in pub.get("authors", [])
                    ],
                    "bibliographic_info": pub.get("bibliographic_info", {}),
                    "metrics": pub.get("metrics", {}),
                    "keywords": pub.get("keywords", [])
                }
                processed_publications.append(processed_pub)
            
            # Sort by citations
            sort_by = criteria.get("sort_by", "metrics.citation_count")
            processed_publications.sort(
                key=lambda x: x.get(sort_by, {}).get("citation_count", 0) if isinstance(sort_by, str) and sort_by.startswith("metrics.") else 0,
                reverse=True
            )
            
            # Limit results
            limit = criteria.get("limit", 20)
            return processed_publications[:limit]
            
        except Exception as e:
            logger.error(f"Advanced publication search failed: {e}")
            return []
    
    def _find_researchers_by_name(self, name_query: str) -> List[str]:
        """Find researchers by name query"""
        try:
            name_query = name_query.strip()
            tokens = name_query.split()
            
            query = {}
            if len(tokens) > 1:
                # For multi-word queries
                and_conditions = []
                for token in tokens:
                    and_conditions.append({
                        "$or": [
                            {"personal_info.first_name": {"$regex": token, "$options": "i"}},
                            {"personal_info.last_name": {"$regex": token, "$options": "i"}}
                        ]
                    })
                query["$and"] = and_conditions
            else:
                 query["$or"] = [
                    {"personal_info.first_name": {"$regex": name_query, "$options": "i"}},
                    {"personal_info.last_name": {"$regex": name_query, "$options": "i"}}
                ]

            researchers = self.db_manager.mongodb.search_researchers(query)
            return [r["_id"] for r in researchers]
        except Exception as e:
            logger.error(f"Failed to find researchers by name: {e}")
            return []
    
    def get_research_trends(self, department: str = None, time_period: int = 365) -> Dict[str, Any]:
        """Analyze research trends over time"""
        try:
            # Get publications for analysis
            start_date = (date.today() - timedelta(days=time_period)).isoformat()
            query = {"bibliographic_info.publication_date": {"$gte": start_date}}
            
            if department:
                # Filter by department through authors
                dept_researchers = self.db_manager.mongodb.search_researchers({
                    "academic_profile.department_id": department
                })
                researcher_ids = [r["_id"] for r in dept_researchers]
                query["authors.researcher_id"] = {"$in": researcher_ids}
            
            publications = self.db_manager.mongodb.find_documents("publications", query)
            
            # Analyze trends by month
            monthly_trends = {}
            research_area_trends = {}
            
            for pub in publications:
                pub_date = pub.get("bibliographic_info", {}).get("publication_date")
                if pub_date:
                    try:
                        # Parse date and get month-year
                        pub_datetime = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        month_key = pub_datetime.strftime("%Y-%m")
                        monthly_trends[month_key] = monthly_trends.get(month_key, 0) + 1
                        
                        # Research area trends
                        for area in pub.get("research_areas", []):
                            if month_key not in research_area_trends:
                                research_area_trends[month_key] = {}
                            research_area_trends[month_key][area] = research_area_trends[month_key].get(area, 0) + 1
                    except:
                        continue
            
            # Get top research areas overall
            all_areas = {}
            for pub in publications:
                for area in pub.get("research_areas", []):
                    all_areas[area] = all_areas.get(area, 0) + 1
            
            top_areas = dict(sorted(all_areas.items(), key=lambda x: x[1], reverse=True)[:10])
            
            trends = {
                "department": department,
                "time_period_days": time_period,
                "monthly_publication_trends": monthly_trends,
                "research_area_trends": research_area_trends,
                "top_research_areas": top_areas,
                "total_publications": len(publications),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to analyze research trends: {e}")
            return {"error": str(e)}


def main():
    """Test the query engine"""
    config = load_database_config()
    db_manager = ResearchDatabaseManager(config)
    query_engine = ResearchQueryEngine(db_manager)
    
    try:
        if db_manager.connect_all():
            print("Testing Query Engine...")
            
            # Test 1: Get complete researcher profile
            print("\n1. Testing complete researcher profile retrieval...")
            # Note: This would require a valid researcher_id from the database
            # profile = query_engine.get_researcher_profile_complete("some_researcher_id")
            # print(f"Profile retrieved: {bool(profile and 'error' not in profile)}")
            
            # Test 2: Advanced researcher search
            print("\n2. Testing advanced researcher search...")
            search_results = query_engine.search_researchers_advanced({
                "department": "dept_cs",
                "min_h_index": 10,
                "sort_by": "h_index",
                "limit": 5
            })
            print(f"Found {len(search_results)} researchers")
            
            # Test 3: Collaboration pairs
            print("\n3. Finding collaboration pairs...")
            pairs = query_engine.find_collaboration_pairs("dept_cs", min_collaborations=1)
            print(f"Found {len(pairs)} collaboration pairs")
            
            # Test 4: Department analytics
            print("\n4. Getting department analytics...")
            analytics = query_engine.get_department_analytics("dept_cs", days=30)
            print(f"Analytics generated: {bool(analytics and 'error' not in analytics)}")
            
            print("\nQuery Engine tests completed!")
            
        else:
            print("Failed to connect to databases")
            
    finally:
        db_manager.disconnect_all()


if __name__ == "__main__":
    main()
