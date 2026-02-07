"""
Repositories Module - مستودعات قواعد البيانات
يحتوي على جميع كذا للتعامل مع قواعد البيانات المختلفة
"""

from .mongo_repo import MongoDBRepository, MongoDBManager
from .neo4j_repo import Neo4jRepository, Neo4jManager
from .redis_repo import RedisRepository, RedisManager
from .cassandra_repo import CassandraRepository, CassandraManager

__all__ = [
    'MongoDBRepository',
    'Neo4jRepository',
    'RedisRepository', 
    'CassandraRepository',
    # Backward compatibility
    'MongoDBManager',
    'Neo4jManager',
    'RedisManager',
    'CassandraManager',
]
