#!/usr/bin/env python3
"""
Cassandra Repository - مستودع Cassandra
يتعامل مع بيانات التحليلات والسلاسل الزمنية (Analytics & Time-series)
"""

import uuid
import logging
from datetime import date, timedelta
from typing import Dict, List
import os

# Configure logging
logger = logging.getLogger(__name__)

# Check if Cassandra driver is available
try:
    from cassandra.cluster import Cluster
    from cassandra.policies import DCAwareRoundRobinPolicy
    CASSANDRA_AVAILABLE = True
except ImportError:
    CASSANDRA_AVAILABLE = False
    logger.warning("cassandra-driver not installed. Cassandra features will be disabled.")


class CassandraRepository:
    """Cassandra Repository for analytics metrics"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.cluster = None
        self.session = None
        
    def connect(self):
        """Establish Cassandra connection (with Python 3.12+ compatibility)"""
        if not CASSANDRA_AVAILABLE:
            logger.warning("Cassandra not available, skipping connection")
            return
            
        import time
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # Create cluster with load balancing policy
                load_balancing_policy = DCAwareRoundRobinPolicy()
                
                connection_params = {
                    'contact_points': [self.host],
                    'port': self.port,
                    'load_balancing_policy': load_balancing_policy,
                    'connect_timeout': 10
                }
                
                # For Python 3.12+ compatibility, try to use AsyncioConnection
                try:
                    from cassandra.io.asyncioreactor import AsyncioConnection
                    connection_params['connection_class'] = AsyncioConnection
                    logger.info("Using AsyncioConnection for Cassandra")
                except ImportError:
                    pass
                
                self.cluster = Cluster(**connection_params)
                
                # First connect without keyspace to ensure it exists
                self.session = self.cluster.connect()
                
                # Create keyspace if it doesn't exist
                self.session.execute("""
                    CREATE KEYSPACE IF NOT EXISTS research_analytics
                    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
                """)
                
                # Connect to keyspace
                self.session.set_keyspace('research_analytics')
                
                logger.info("Cassandra connected successfully")
                return
            except Exception as e:
                logger.error(f"Cassandra connection attempt {attempt + 1} failed: {e}")
                if self.cluster:
                    self.cluster.shutdown()
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    self.session = None
                    logger.error("All Cassandra connection attempts failed")
    
    def disconnect(self):
        """Close Cassandra connection"""
        if self.cluster:
            self.cluster.shutdown()
            logger.info("Cassandra disconnected")
    
    def insert_publication_metrics(self, publication_id: str, metrics: Dict, 
                                 metric_date: date = None) -> bool:
        """Insert publication metrics"""
        try:
            if not self.session:
                return False
                
            if metric_date is None:
                metric_date = date.today()
            
            query = """
            INSERT INTO publication_metrics 
            (publication_id, metric_date, citation_count, download_count, 
             view_count, h_index_contribution)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.session.execute(query, (
                uuid.UUID(publication_id),
                metric_date,
                metrics.get('citation_count', 0),
                metrics.get('download_count', 0),
                metrics.get('view_count', 0),
                metrics.get('h_index_contribution', 0)
            ))
            logger.info(f"Inserted publication metrics for {publication_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert publication metrics: {e}")
            return False
    
    def get_department_analytics(self, department_id: str, days: int = 30) -> List[Dict]:
        """Get department analytics for specified period"""
        try:
            if not self.session:
                return []
                
            # Calculate start date
            start_date = date.today() - timedelta(days=days)
            
            query = """
            SELECT * FROM department_analytics 
            WHERE department_id = %s 
            AND analytics_date >= %s
            ORDER BY analytics_date DESC
            """
            rows = self.session.execute(query, (department_id, start_date))
            
            analytics = []
            for row in rows:
                analytics.append({
                    'department_id': row.department_id,
                    'analytics_date': row.analytics_date,
                    'active_researchers': row.active_researchers,
                    'total_publications': row.total_publications,
                    'total_citations': row.total_citations,
                    'avg_h_index': float(row.avg_h_index),
                    'collaboration_rate': float(row.collaboration_rate),
                    'project_count': row.project_count,
                    'funding_total': float(row.funding_total)
                })
            
            return analytics
        except Exception as e:
            logger.error(f"Failed to get department analytics: {e}")
            return []


# Backward compatibility alias
CassandraManager = CassandraRepository
