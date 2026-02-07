#!/usr/bin/env python3
"""
Redis Repository - مستودع Redis
يتعامل مع التخزين المؤقت (Caching) والجلسات (Sessions)
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional
import redis

# Configure logging
logger = logging.getLogger(__name__)


class RedisRepository:
    """Redis Repository for caching and session management"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client = None
        
    def connect(self):
        """Establish Redis connection"""
        try:
            self.client = redis.from_url(
                self.connection_string,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            logger.info("Redis disconnected")
    
    # ==================== CACHING OPERATIONS ====================
    
    def cache_researcher_profile(self, researcher_id: str, profile_data: Dict, ttl: int = 1800) -> bool:
        """Cache researcher profile with TTL"""
        try:
            key = f"researcher_profile:{researcher_id}"
            self.client.setex(key, ttl, json.dumps(profile_data, default=str))
            logger.info(f"Cached researcher profile: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache researcher profile: {e}")
            return False
    
    def get_cached_researcher_profile(self, researcher_id: str) -> Optional[Dict]:
        """Get cached researcher profile"""
        try:
            key = f"researcher_profile:{researcher_id}"
            cached_data = self.client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached researcher profile: {e}")
            return None
    
    def update_researcher_stats(self, researcher_id: str, stats: Dict) -> bool:
        """Update researcher statistics in cache"""
        try:
            key = f"researcher_stats:{researcher_id}"
            self.client.hset(key, mapping={k: str(v) for k, v in stats.items()})
            self.client.expire(key, 3600)  # 1 hour TTL
            logger.info(f"Updated researcher stats: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to update researcher stats: {e}")
            return False
    
    def get_top_researchers_by_metric(self, metric: str, limit: int = 10) -> List[str]:
        """Get top researchers by specified metric"""
        try:
            key = f"top_researchers:by_{metric}"
            researchers = self.client.zrevrange(key, 0, limit - 1, withscores=False)
            return researchers
        except Exception as e:
            logger.error(f"Failed to get top researchers: {e}")
            return []

    # ==================== SESSION MANAGEMENT ====================

    def create_session(self, user_id: str, session_data: Dict, ttl: int = 3600) -> str:
        """Create a new session"""
        try:
            session_token = str(uuid.uuid4())
            key = f"session:{session_token}"
            session_data['user_id'] = user_id
            session_data['created_at'] = datetime.utcnow().isoformat()
            self.client.setex(key, ttl, json.dumps(session_data, default=str))
            # Also store reverse mapping
            self.client.setex(f"user_session:{user_id}", ttl, session_token)
            logger.info(f"Created session for user {user_id}")
            return session_token
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return ""

    def get_session(self, session_token: str) -> Optional[Dict]:
        """Get session data by token"""
        try:
            key = f"session:{session_token}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None

    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session"""
        try:
            key = f"session:{session_token}"
            # Get user_id before deleting
            session_data = self.get_session(session_token)
            if session_data and 'user_id' in session_data:
                self.client.delete(f"user_session:{session_data['user_id']}")
            
            result = self.client.delete(key)
            logger.info(f"Invalidated session: {session_token}")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            return False

    def extend_session(self, session_token: str, additional_time: int = 3600) -> bool:
        """Extend session TTL"""
        try:
            key = f"session:{session_token}"
            current_ttl = self.client.ttl(key)
            if current_ttl > 0:
                new_ttl = current_ttl + additional_time
                self.client.expire(key, new_ttl)
                logger.info(f"Extended session {session_token} by {additional_time} seconds")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to extend session: {e}")
            return False

    # ==================== SEARCH CACHE ====================

    def cache_search_results(self, query_hash: str, results: List[Dict], ttl: int = 300) -> bool:
        """Cache search results"""
        try:
            key = f"search_cache:{query_hash}"
            self.client.setex(key, ttl, json.dumps(results, default=str))
            logger.info(f"Cached search results: {query_hash}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache search results: {e}")
            return False

    def get_cached_search_results(self, query_hash: str) -> Optional[List[Dict]]:
        """Get cached search results"""
        try:
            key = f"search_cache:{query_hash}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached search results: {e}")
            return None

    # ==================== ACTIVITY TRACKING ====================

    def add_recent_activity(self, user_id: str, activity: Dict, max_items: int = 50) -> bool:
        """Add activity to user's recent activity list"""
        try:
            key = f"recent_activity:{user_id}"
            activity['timestamp'] = datetime.utcnow().isoformat()
            self.client.lpush(key, json.dumps(activity, default=str))
            self.client.ltrim(key, 0, max_items - 1)
            self.client.expire(key, 86400 * 7)  # Keep for 7 days
            return True
        except Exception as e:
            logger.error(f"Failed to add recent activity: {e}")
            return False

    def get_recent_activities(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get user's recent activities"""
        try:
            key = f"recent_activity:{user_id}"
            activities = self.client.lrange(key, 0, limit - 1)
            return [json.loads(a) for a in activities]
        except Exception as e:
            logger.error(f"Failed to get recent activities: {e}")
            return []

    # ==================== CACHE INVALIDATION & STATS ====================

    def invalidate_researcher_cache(self, researcher_id: str) -> bool:
        """Invalidate all cache entries for a researcher"""
        try:
            keys = [
                f"researcher_profile:{researcher_id}",
                f"researcher_stats:{researcher_id}"
            ]
            for key in keys:
                self.client.delete(key)
            logger.info(f"Invalidated cache for researcher {researcher_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate researcher cache: {e}")
            return False

    def invalidate_all_cache(self, pattern: str = "researcher_*") -> int:
        """Invalidate all cache entries matching a pattern"""
        try:
            count = 0
            for key in self.client.scan_iter(match=pattern):
                self.client.delete(key)
                count += 1
            logger.info(f"Invalidated {count} cache entries matching '{pattern}'")
            return count
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return 0

    def get_cache_statistics(self) -> Dict:
        """Get Redis cache statistics"""
        try:
            info = self.client.info()
            db_info = self.client.info('keyspace')
            
            stats = {
                'used_memory': info.get('used_memory_human'),
                'used_memory_peak': info.get('used_memory_peak_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'hit_rate': round(
                    info.get('keyspace_hits', 0) / 
                    max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100, 2
                ),
                'uptime_in_seconds': info.get('uptime_in_seconds'),
                'db_info': db_info
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {}

    def update_leaderboard(self, metric: str, researcher_id: str, score: float) -> bool:
        """Update researcher score in a leaderboard"""
        try:
            key = f"leaderboard:{metric}"
            self.client.zadd(key, {researcher_id: score})
            logger.info(f"Updated leaderboard {metric}: {researcher_id} = {score}")
            return True
        except Exception as e:
            logger.error(f"Failed to update leaderboard: {e}")
            return False

    def get_leaderboard(self, metric: str, limit: int = 10) -> List[Dict]:
        """Get top entries from a leaderboard"""
        try:
            key = f"leaderboard:{metric}"
            entries = self.client.zrevrange(key, 0, limit - 1, withscores=True)
            return [{'researcher_id': e[0], 'score': e[1]} for e in entries]
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            return []


# Backward compatibility alias
RedisManager = RedisRepository
