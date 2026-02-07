#!/usr/bin/env python3
"""
MongoDB Repository - مستودع MongoDB
يتعامل مع جميع عمليات قاعدة بيانات MongoDB
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pymongo import MongoClient

# Configure logging
logger = logging.getLogger(__name__)


class MongoDBRepository:
    """MongoDB Repository for all MongoDB operations"""
    
    def __init__(self, connection_string: str, database_name: str):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
        
    def connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            # Test connection
            self.client.admin.command('ping')
            logger.info("MongoDB connected successfully")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnected")
    
    # ==================== RESEARCHER OPERATIONS ====================
    
    def create_researcher(self, researcher_data: Dict) -> str:
        """Create a new researcher record"""
        try:
            # Add metadata
            researcher_data['metadata'] = {
                'created_at': datetime.utcnow(),
                'last_updated': datetime.utcnow(),
                'status': 'active',
                'verified': False
            }
            
            # Generate ID if not provided
            if '_id' not in researcher_data:
                researcher_data['_id'] = str(uuid.uuid4())
            
            result = self.db.researchers.insert_one(researcher_data)
            logger.info(f"Created researcher with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create researcher: {e}")
            raise
    
    def get_researcher(self, researcher_id: str) -> Optional[Dict]:
        """Get researcher by ID (supports both string and ObjectId)"""
        try:
            if not researcher_id:
                return None
                
            # Try as provided (usually string)
            researcher = self.db.researchers.find_one({'_id': researcher_id})
            
            # If not found and it's a string that looks like an ObjectId, try converting
            if not researcher and isinstance(researcher_id, str) and len(researcher_id) == 24:
                from bson.objectid import ObjectId
                try:
                    researcher = self.db.researchers.find_one({'_id': ObjectId(researcher_id)})
                except:
                    pass
            
            if researcher:
                # Convert ObjectId to string for JSON serialization
                researcher['_id'] = str(researcher['_id'])
            return researcher
        except Exception as e:
            logger.error(f"Failed to get researcher {researcher_id}: {e}")
            return None
    
    def search_researchers(self, query: Dict, limit: int = 0) -> List[Dict]:
        """Search researchers with query criteria"""
        try:
            cursor = self.db.researchers.find(query)
            if limit > 0:
                cursor.limit(limit)
            researchers = list(cursor)
            # Convert ObjectId to string
            for researcher in researchers:
                researcher['_id'] = str(researcher['_id'])
            return researchers
        except Exception as e:
            logger.error(f"Failed to search researchers: {e}")
            return []
    
    def update_researcher(self, researcher_id: str, update_data: Dict) -> bool:
        """Update researcher record"""
        try:
            update_data['metadata.last_updated'] = datetime.utcnow()
            result = self.db.researchers.update_one(
                {'_id': researcher_id},
                {'$set': update_data}
            )
            logger.info(f"Updated researcher {researcher_id}: {result.modified_count} documents modified")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update researcher {researcher_id}: {e}")
            return False
    
    def delete_researcher(self, researcher_id: str) -> bool:
        """Delete a researcher by ID"""
        try:
            result = self.db.researchers.delete_one({'_id': researcher_id})
            logger.info(f"Deleted researcher {researcher_id}: {result.deleted_count} documents deleted")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete researcher {researcher_id}: {e}")
            return False
    
    # ==================== PROJECT OPERATIONS ====================
    
    def create_project(self, project_data: Dict) -> str:
        """Create a new project record"""
        try:
            # Add metadata if not present, otherwise update it
            if 'metadata' not in project_data:
                project_data['metadata'] = {}
            
            project_data['metadata'].update({
                'created_at': datetime.utcnow(),
                'last_updated': datetime.utcnow(),
                'status': project_data.get('status', 'active')
            })
            
            # Preserve creation_date from web interface if it exists
            if 'creation_date' not in project_data.get('metadata', {}):
                project_data['metadata']['creation_date'] = datetime.utcnow().isoformat()
            
            # Generate ID if not provided
            if '_id' not in project_data:
                project_data['_id'] = str(uuid.uuid4())
            
            result = self.db.projects.insert_one(project_data)
            logger.info(f"Created project with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID (supports both string and ObjectId)"""
        try:
            if not project_id:
                return None
            project = self.db.projects.find_one({'_id': project_id})
            
            if not project and isinstance(project_id, str) and len(project_id) == 24:
                from bson.objectid import ObjectId
                try:
                    project = self.db.projects.find_one({'_id': ObjectId(project_id)})
                except:
                    pass
                    
            if project:
                project['_id'] = str(project['_id'])
            return project
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None
    
    def search_projects(self, query: Dict, limit: int = 0) -> List[Dict]:
        """Search projects with query criteria"""
        try:
            cursor = self.db.projects.find(query)
            if limit > 0:
                cursor.limit(limit)
            projects = list(cursor)
            for project in projects:
                project['_id'] = str(project['_id'])
            return projects
        except Exception as e:
            logger.error(f"Failed to search projects: {e}")
            return []
    
    def update_project(self, project_id: str, update_data: Dict) -> bool:
        """Update project record"""
        try:
            update_data['metadata.last_updated'] = datetime.utcnow()
            result = self.db.projects.update_one(
                {'_id': project_id},
                {'$set': update_data}
            )
            logger.info(f"Updated project {project_id}: {result.modified_count} documents modified")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID"""
        try:
            result = self.db.projects.delete_one({'_id': project_id})
            logger.info(f"Deleted project {project_id}: {result.deleted_count} documents deleted")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            return False
    
    # ==================== PUBLICATION OPERATIONS ====================
    
    def create_publication(self, publication_data: Dict) -> str:
        """Create a new publication record"""
        try:
            # Add metadata if not present
            if 'metadata' not in publication_data:
                publication_data['metadata'] = {}
                
            publication_data['metadata'].update({
                'created_at': datetime.utcnow(),
                'last_updated': datetime.utcnow(),
                'status': publication_data.get('status', 'published')
            })
            
            # Generate ID if not provided
            if '_id' not in publication_data:
                publication_data['_id'] = str(uuid.uuid4())
            
            result = self.db.publications.insert_one(publication_data)
            logger.info(f"Created publication with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create publication: {e}")
            raise
    
    def get_publication(self, publication_id: str) -> Optional[Dict]:
        """Get publication by ID (supports both string and ObjectId)"""
        try:
            if not publication_id:
                return None
            publication = self.db.publications.find_one({'_id': publication_id})
            
            if not publication and isinstance(publication_id, str) and len(publication_id) == 24:
                from bson.objectid import ObjectId
                try:
                    publication = self.db.publications.find_one({'_id': ObjectId(publication_id)})
                except:
                    pass
                    
            if publication:
                publication['_id'] = str(publication['_id'])
            return publication
        except Exception as e:
            logger.error(f"Failed to get publication {publication_id}: {e}")
            return None
    
    def search_publications(self, query: Dict, limit: int = 0) -> List[Dict]:
        """Search publications with query criteria"""
        try:
            cursor = self.db.publications.find(query)
            if limit > 0:
                cursor = cursor.limit(limit)
            
            publications = list(cursor)
            for pub in publications:
                pub['_id'] = str(pub['_id'])
            return publications
        except Exception as e:
            logger.error(f"Failed to search publications: {e}")
            return []
    
    def update_publication(self, publication_id: str, update_data: Dict) -> bool:
        """Update publication record"""
        try:
            update_data['metadata.last_updated'] = datetime.utcnow()
            result = self.db.publications.update_one(
                {'_id': publication_id},
                {'$set': update_data}
            )
            logger.info(f"Updated publication {publication_id}: {result.modified_count} documents modified")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update publication {publication_id}: {e}")
            return False
    
    def delete_publication(self, publication_id: str) -> bool:
        """Delete a publication by ID"""
        try:
            result = self.db.publications.delete_one({'_id': publication_id})
            logger.info(f"Deleted publication {publication_id}: {result.deleted_count} documents deleted")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete publication {publication_id}: {e}")
            return False
    
    # ==================== UTILITY OPERATIONS ====================
    
    def count_documents(self, collection_name: str, query: Dict = None) -> int:
        """Count documents in a collection"""
        try:
            return self.db[collection_name].count_documents(query or {})
        except Exception as e:
            logger.error(f"Failed to count documents in {collection_name}: {e}")
            return 0
            
    def find_documents(self, collection_name: str, query: Dict = None, sort_by: List = None, limit: int = 0) -> List[Dict]:
        """Find documents in a collection"""
        try:
            cursor = self.db[collection_name].find(query or {})
            if sort_by:
                cursor.sort(sort_by)
            if limit > 0:
                cursor.limit(limit)
                
            results = list(cursor)
            # Convert ObjectId to string
            for doc in results:
                doc['_id'] = str(doc['_id'])
            return results
        except Exception as e:
            logger.error(f"Failed to find documents in {collection_name}: {e}")
            return []
    
    # ==================== USER MANAGEMENT ====================
    
    def hash_password(self, password: str) -> str:
        """Hash a password for storing"""
        try:
            from passlib.context import CryptContext
            # Add scrypt to schemes for backward compatibility
            # Make scrypt default to avoid 72 byte limit of bcrypt
            pwd_context = CryptContext(schemes=["scrypt", "bcrypt"], deprecated="auto")
            
            # Check for bcrypt 72 byte limit (only if bcrypt is used, but we switched default)
            # Keeping check just in case fallback happens or for verifying old passwords re-hashing
            if len(password.encode('utf-8')) >= 72 and pwd_context.default_scheme() == "bcrypt":
                raise ValueError("Password is too long (max 72 characters)")
                
            return pwd_context.hash(password)
        except ValueError as ve:
            # Re-raise value errors (like length check)
            raise ve
        except Exception as e:
            logger.error(f"Failed to hash password: {e}")
            # If it's the specific bcrypt error, rephrase it
            if "72 bytes" in str(e):
                raise ValueError("Password is too long (max 72 characters)")
            raise

    def create_user(self, user_data: Dict) -> str:
        """Create a new user"""
        try:
            user_data['created_at'] = datetime.now()
            user_data['status'] = 'active'
            
            # Hash password if provided
            if 'password' in user_data:
                user_data['password'] = self.hash_password(user_data['password'])
            
            result = self.db.users.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            user = self.db.users.find_one({'email': email})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        try:
            from bson.objectid import ObjectId
            user = self.db.users.find_one({'_id': ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None

    def verify_password(self, hashed_password: str, plain_password: str) -> bool:
        """Verify a password against a hashed password"""
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["scrypt", "bcrypt"], deprecated="auto")
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return False



    def update_user(self, user_id: str, update_data: Dict) -> bool:
        """Update user information"""
        try:
            from bson.objectid import ObjectId
                
            update_data['updated_at'] = datetime.now()
            
            # Hash password if it's being updated
            if 'password' in update_data:
                update_data['password'] = self.hash_password(update_data['password'])
            
            result = self.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return False


# Backward compatibility alias
MongoDBManager = MongoDBRepository
