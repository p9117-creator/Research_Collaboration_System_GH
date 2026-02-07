#!/usr/bin/env python3
"""
Neo4j Repository - مستودع Neo4j
يتعامل مع جميع عمليات قاعدة بيانات Neo4j (Graph Database)
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from neo4j import GraphDatabase

# Configure logging
logger = logging.getLogger(__name__)


class Neo4jRepository:
    """Neo4j Repository for graph database operations"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
    def connect(self):
        """Establish Neo4j connection"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j connected successfully")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j disconnected")
    
    # ==================== RESEARCHER NODE OPERATIONS ====================
    
    def create_researcher_node(self, researcher_data: Dict) -> bool:
        """Create researcher node in graph"""
        try:
            with self.driver.session() as session:
                # Extract researcher properties
                props = {
                    'id': researcher_data.get('_id'),
                    'name': f"{researcher_data['personal_info']['first_name']} {researcher_data['personal_info']['last_name']}",
                    'email': researcher_data['personal_info']['email'],
                    'department': researcher_data['academic_profile']['department_id'],
                    'position': researcher_data['academic_profile']['position'],
                    'h_index': researcher_data['collaboration_metrics']['h_index'],
                    'publication_count': researcher_data['collaboration_metrics']['total_publications'],
                    'orcid_id': researcher_data.get('orcid_id')
                }
                
                query = """
                CREATE (r:Researcher $props)
                RETURN r
                """
                result = session.run(query, props=props)
                logger.info(f"Created Neo4j researcher node: {props['id']}")
                return True
        except Exception as e:
            logger.error(f"Failed to create Neo4j researcher node: {e}")
            return False

    def update_researcher_node(self, researcher_id: str, update_data: Dict) -> bool:
        """Update researcher node in graph"""
        try:
            with self.driver.session() as session:
                set_clauses = []
                params = {"id": researcher_id}
                
                if 'personal_info' in update_data:
                    info = update_data['personal_info']
                    if 'first_name' in info and 'last_name' in info:
                        set_clauses.append("r.name = $name")
                        params["name"] = f"{info['first_name']} {info['last_name']}"
                    if 'email' in info:
                        set_clauses.append("r.email = $email")
                        params["email"] = info['email']
                
                if 'academic_profile' in update_data:
                    profile = update_data['academic_profile']
                    if 'department_id' in profile:
                        set_clauses.append("r.department = $department")
                        params["department"] = profile['department_id']
                    if 'position' in profile:
                        set_clauses.append("r.position = $position")
                        params["position"] = profile['position']
                
                if 'collaboration_metrics' in update_data:
                    metrics = update_data['collaboration_metrics']
                    if 'h_index' in metrics:
                        set_clauses.append("r.h_index = $h_index")
                        params["h_index"] = metrics['h_index']
                    if 'total_publications' in metrics:
                        set_clauses.append("r.publication_count = $publication_count")
                        params["publication_count"] = metrics['total_publications']

                if not set_clauses:
                    return True  # Nothing to update in Neo4j

                query = f"MATCH (r:Researcher {{id: $id}}) SET {', '.join(set_clauses)} RETURN r"
                session.run(query, **params)
                logger.info(f"Updated Neo4j researcher node: {researcher_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update Neo4j researcher node: {e}")
            return False

    def delete_researcher_node(self, researcher_id: str) -> bool:
        """Delete researcher node and all its relationships"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (r:Researcher {id: $researcher_id})
                DETACH DELETE r
                """
                session.run(query, researcher_id=researcher_id)
                logger.info(f"Deleted Neo4j researcher node: {researcher_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete Neo4j researcher node: {e}")
            return False

    # ==================== COLLABORATION OPERATIONS ====================

    def add_collaboration(self, researcher1_id: str, researcher2_id: str) -> bool:
        """Add collaboration relationship between two researchers with node existence check"""
        try:
            with self.driver.session() as session:
                # Use MERGE for nodes to ensure they exist in Neo4j before creating relationship
                query = """
                MERGE (r1:Researcher {id: $id1})
                MERGE (r2:Researcher {id: $id2})
                WITH r1, r2
                MERGE (r1)-[c:CO_AUTHORED_WITH]-(r2)
                ON CREATE SET c.strength = 1
                ON MATCH SET c.strength = c.strength + 1
                RETURN c
                """
                session.run(query, id1=researcher1_id, id2=researcher2_id)
                logger.info(f"Updated collaboration (Neo4j) between {researcher1_id} and {researcher2_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to add collaboration: {e}")
            return False

    def remove_collaboration(self, researcher1_id: str, researcher2_id: str) -> bool:
        """Remove collaboration relationship between two specific researchers"""
        try:
            with self.driver.session() as session:
                # Use undirected relationship match to find and delete specifically the link between these two
                query = """
                MATCH (r1:Researcher {id: $id1})-[c:CO_AUTHORED_WITH]-(r2:Researcher {id: $id2})
                DELETE c
                """
                session.run(query, id1=researcher1_id, id2=researcher2_id)
                logger.info(f"Removed specific collaboration (Neo4j) between {researcher1_id} and {researcher2_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to remove collaboration: {e}")
            return False
    
    def create_collaboration_relationship(self, researcher1_id: str, researcher2_id: str, 
                                        relationship_type: str, properties: Dict = None) -> bool:
        """Create collaboration relationship between researchers"""
        try:
            with self.driver.session() as session:
                props = properties or {}
                query = f"""
                MATCH (r1:Researcher {{id: $researcher1_id}})
                MATCH (r2:Researcher {{id: $researcher2_id}})
                MERGE (r1)-[rel:{relationship_type}]->(r2)
                SET rel += $props
                RETURN rel
                """
                result = session.run(query, 
                                   researcher1_id=researcher1_id,
                                   researcher2_id=researcher2_id,
                                   props=props)
                logger.info(f"Created {relationship_type} relationship between {researcher1_id} and {researcher2_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to create collaboration relationship: {e}")
            return False
    
    def find_collaborators(self, researcher_id: str, max_depth: int = 2) -> List[Dict]:
        """Find collaborators within specified depth"""
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (r:Researcher {{id: $researcher_id}})
                MATCH path = (r)-[:CO_AUTHORED_WITH*1..{max_depth}]-(collaborator)
                RETURN DISTINCT collaborator, length(path) as distance
                ORDER BY distance, collaborator.h_index DESC
                LIMIT 20
                """
                result = session.run(query, researcher_id=researcher_id)
                
                collaborators = []
                for record in result:
                    collaborator = dict(record['collaborator'])
                    collaborator['distance'] = record['distance']
                    collaborators.append(collaborator)
                
                return collaborators
        except Exception as e:
            logger.error(f"Failed to find collaborators: {e}")
            return []

    # ==================== SUPERVISION & MENTORSHIP ====================

    def create_supervision_relationship(self, supervisor_id: str, student_id: str, 
                                         supervision_type: str = "phd", properties: Dict = None) -> bool:
        """Create supervision relationship between researchers"""
        try:
            with self.driver.session() as session:
                props = properties or {}
                props['supervision_type'] = supervision_type
                props['created_at'] = datetime.utcnow().isoformat()
                query = """
                MATCH (supervisor:Researcher {id: $supervisor_id})
                MATCH (student:Researcher {id: $student_id})
                MERGE (supervisor)-[rel:SUPERVISES]->(student)
                SET rel += $props
                RETURN rel
                """
                session.run(query, supervisor_id=supervisor_id, student_id=student_id, props=props)
                logger.info(f"Created SUPERVISES relationship: {supervisor_id} -> {student_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to create supervision relationship: {e}")
            return False

    def create_mentorship_relationship(self, mentor_id: str, mentee_id: str,
                                        mentorship_type: str = "research", properties: Dict = None) -> bool:
        """Create mentorship relationship between researchers"""
        try:
            with self.driver.session() as session:
                props = properties or {}
                props['mentorship_type'] = mentorship_type
                props['created_at'] = datetime.utcnow().isoformat()
                query = """
                MATCH (mentor:Researcher {id: $mentor_id})
                MATCH (mentee:Researcher {id: $mentee_id})
                MERGE (mentor)-[rel:MENTORS]->(mentee)
                SET rel += $props
                RETURN rel
                """
                session.run(query, mentor_id=mentor_id, mentee_id=mentee_id, props=props)
                logger.info(f"Created MENTORS relationship: {mentor_id} -> {mentee_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to create mentorship relationship: {e}")
            return False

    # ==================== RELATIONSHIP QUERIES ====================

    def get_researcher_relationships(self, researcher_id: str) -> Dict:
        """Get all relationships for a researcher"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (r:Researcher {id: $researcher_id})-[rel]-(other:Researcher)
                RETURN type(rel) as rel_type, 
                       other.id as other_id, 
                       other.name as other_name,
                       startNode(rel).id = $researcher_id as is_outgoing,
                       properties(rel) as rel_props
                """
                result = session.run(query, researcher_id=researcher_id)
                
                relationships = {
                    'collaborations': [],
                    'supervisions': [],
                    'mentorships': [],
                    'other': []
                }
                
                for record in result:
                    rel_data = {
                        'other_id': record['other_id'],
                        'other_name': record['other_name'],
                        'is_outgoing': record['is_outgoing'],
                        'properties': dict(record['rel_props']) if record['rel_props'] else {}
                    }
                    
                    rel_type = record['rel_type']
                    if rel_type == 'CO_AUTHORED_WITH':
                        relationships['collaborations'].append(rel_data)
                    elif rel_type == 'SUPERVISES':
                        relationships['supervisions'].append(rel_data)
                    elif rel_type == 'MENTORS':
                        relationships['mentorships'].append(rel_data)
                    else:
                        rel_data['type'] = rel_type
                        relationships['other'].append(rel_data)
                
                return relationships
        except Exception as e:
            logger.error(f"Failed to get researcher relationships: {e}")
            return {}

    def find_supervision_chain(self, researcher_id: str, direction: str = "up") -> List[Dict]:
        """Find supervision chain (academic genealogy)"""
        try:
            with self.driver.session() as session:
                if direction == "up":
                    # Find supervisors (ancestors)
                    query = """
                    MATCH path = (r:Researcher {id: $researcher_id})<-[:SUPERVISES*1..5]-(ancestor)
                    RETURN ancestor, length(path) as distance
                    ORDER BY distance
                    """
                else:
                    # Find students (descendants)
                    query = """
                    MATCH path = (r:Researcher {id: $researcher_id})-[:SUPERVISES*1..5]->(descendant)
                    RETURN descendant as ancestor, length(path) as distance
                    ORDER BY distance
                    """
                
                result = session.run(query, researcher_id=researcher_id)
                
                chain = []
                for record in result:
                    node = dict(record['ancestor'])
                    node['distance'] = record['distance']
                    chain.append(node)
                
                return chain
        except Exception as e:
            logger.error(f"Failed to find supervision chain: {e}")
            return []

    # ==================== STATISTICS ====================

    def get_collaboration_statistics(self) -> Dict:
        """Get overall collaboration statistics from the graph"""
        try:
            with self.driver.session() as session:
                stats = {}
                
                # Total researchers
                result = session.run("MATCH (r:Researcher) RETURN count(r) as count")
                stats['total_researchers'] = result.single()['count']
                
                # Total collaboration relationships
                result = session.run("MATCH ()-[r:CO_AUTHORED_WITH]->() RETURN count(r) as count")
                stats['total_collaborations'] = result.single()['count']
                
                # Total supervision relationships
                result = session.run("MATCH ()-[r:SUPERVISES]->() RETURN count(r) as count")
                stats['total_supervisions'] = result.single()['count']
                
                # Total mentorship relationships
                result = session.run("MATCH ()-[r:MENTORS]->() RETURN count(r) as count")
                stats['total_mentorships'] = result.single()['count']
                
                # Average collaborations per researcher
                result = session.run("""
                    MATCH (r:Researcher)
                    OPTIONAL MATCH (r)-[:CO_AUTHORED_WITH]-(other)
                    WITH r, count(distinct other) as collab_count
                    RETURN avg(collab_count) as avg_collaborations
                """)
                stats['avg_collaborations_per_researcher'] = round(result.single()['avg_collaborations'] or 0, 2)
                
                # Most connected researchers
                result = session.run("""
                    MATCH (r:Researcher)-[:CO_AUTHORED_WITH]-(other)
                    WITH r, count(distinct other) as connections
                    RETURN r.id as id, r.name as name, connections
                    ORDER BY connections DESC
                    LIMIT 5
                """)
                stats['most_connected'] = [dict(record) for record in result]
                
                return stats
        except Exception as e:
            logger.error(f"Failed to get collaboration statistics: {e}")
            return {}


# Backward compatibility alias
Neo4jManager = Neo4jRepository
