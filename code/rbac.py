"""
Role-Based Access Control (RBAC) Module for Research Collaboration System
Implements fine-grained permission management with roles and permissions
"""

import logging
from enum import Enum
from typing import List, Optional, Dict, Set
from functools import wraps
from fastapi import HTTPException, Depends, status
from pydantic import BaseModel

from auth_handler import get_current_user, TokenData

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System permissions enumeration"""
    # Researcher permissions
    RESEARCHER_READ = "researcher:read"
    RESEARCHER_CREATE = "researcher:create"
    RESEARCHER_UPDATE = "researcher:update"
    RESEARCHER_DELETE = "researcher:delete"
    
    # Publication permissions
    PUBLICATION_READ = "publication:read"
    PUBLICATION_CREATE = "publication:create"
    PUBLICATION_UPDATE = "publication:update"
    PUBLICATION_DELETE = "publication:delete"
    
    # Project permissions
    PROJECT_READ = "project:read"
    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    
    # Analytics permissions
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    
    # Admin permissions
    USER_MANAGE = "user:manage"
    ROLE_MANAGE = "role:manage"
    SYSTEM_CONFIG = "system:config"
    AUDIT_VIEW = "audit:view"
    CACHE_MANAGE = "cache:manage"


class Role(str, Enum):
    """System roles enumeration"""
    GUEST = "guest"
    RESEARCHER = "researcher"
    DEPARTMENT_HEAD = "department_head"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.GUEST: {
        Permission.RESEARCHER_READ,
        Permission.PUBLICATION_READ,
        Permission.PROJECT_READ,
    },
    
    Role.RESEARCHER: {
        # Read permissions
        Permission.RESEARCHER_READ,
        Permission.PUBLICATION_READ,
        Permission.PROJECT_READ,
        Permission.ANALYTICS_VIEW,
        # Write own data
        Permission.PUBLICATION_CREATE,
        Permission.PUBLICATION_UPDATE,
        Permission.PROJECT_CREATE,
    },
    
    Role.DEPARTMENT_HEAD: {
        # All researcher permissions
        Permission.RESEARCHER_READ,
        Permission.PUBLICATION_READ,
        Permission.PROJECT_READ,
        Permission.PUBLICATION_CREATE,
        Permission.PUBLICATION_UPDATE,
        Permission.PROJECT_CREATE,
        # Additional permissions
        Permission.RESEARCHER_CREATE,
        Permission.RESEARCHER_UPDATE,
        Permission.PROJECT_UPDATE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
    },
    
    Role.ADMIN: {
        # All previous permissions
        Permission.RESEARCHER_READ,
        Permission.RESEARCHER_CREATE,
        Permission.RESEARCHER_UPDATE,
        Permission.RESEARCHER_DELETE,
        Permission.PUBLICATION_READ,
        Permission.PUBLICATION_CREATE,
        Permission.PUBLICATION_UPDATE,
        Permission.PUBLICATION_DELETE,
        Permission.PROJECT_READ,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        # Admin permissions
        Permission.USER_MANAGE,
        Permission.AUDIT_VIEW,
        Permission.CACHE_MANAGE,
    },
    
    Role.SUPER_ADMIN: {
        # All permissions
        *[p for p in Permission],
    },
}


class UserRole(BaseModel):
    """User role assignment model"""
    user_id: str
    role: Role
    department_id: Optional[str] = None  # For department-scoped roles
    granted_by: Optional[str] = None
    granted_at: Optional[str] = None


class RBACManager:
    """RBAC Manager for permission checking"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self._role_cache: Dict[str, Role] = {}
    
    def get_user_role(self, user_id: str) -> Role:
        """Get user's role from cache or database"""
        if user_id in self._role_cache:
            return self._role_cache[user_id]
        
        # In production, fetch from database
        if self.db_manager:
            try:
                user = self.db_manager.mongodb.get_researcher(user_id)
                if user:
                    role_str = user.get('role', 'researcher')
                    role = Role(role_str) if role_str in [r.value for r in Role] else Role.RESEARCHER
                    self._role_cache[user_id] = role
                    return role
            except Exception as e:
                logger.error(f"Failed to get user role: {e}")
        
        return Role.RESEARCHER  # Default role
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user based on their role"""
        role = self.get_user_role(user_id)
        return ROLE_PERMISSIONS.get(role, set())
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        permissions = self.get_user_permissions(user_id)
        return permission in permissions
    
    def has_any_permission(self, user_id: str, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        user_perms = self.get_user_permissions(user_id)
        return bool(user_perms.intersection(set(permissions)))
    
    def has_all_permissions(self, user_id: str, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions"""
        user_perms = self.get_user_permissions(user_id)
        return set(permissions).issubset(user_perms)
    
    def invalidate_cache(self, user_id: str):
        """Invalidate role cache for a user"""
        if user_id in self._role_cache:
            del self._role_cache[user_id]
    
    def assign_role(self, user_id: str, role: Role, granted_by: str) -> bool:
        """Assign a role to a user"""
        try:
            if self.db_manager:
                self.db_manager.mongodb.update_researcher(
                    user_id, 
                    {"role": role.value, "role_granted_by": granted_by}
                )
            self._role_cache[user_id] = role
            logger.info(f"Assigned role {role.value} to user {user_id} by {granted_by}")
            return True
        except Exception as e:
            logger.error(f"Failed to assign role: {e}")
            return False


# Global RBAC manager instance
rbac_manager = RBACManager()


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission for an endpoint.
    
    Usage:
        @app.get("/admin/users")
        @require_permission(Permission.USER_MANAGE)
        async def list_users(current_user: TokenData = Depends(get_current_user)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: TokenData = Depends(get_current_user), **kwargs):
            user_id = current_user.username
            
            if not rbac_manager.has_permission(user_id, permission):
                logger.warning(
                    f"Permission denied: user={user_id}, permission={permission.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value} required"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[Permission]):
    """Decorator to require any of the specified permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: TokenData = Depends(get_current_user), **kwargs):
            user_id = current_user.username
            
            if not rbac_manager.has_any_permission(user_id, permissions):
                perm_list = ", ".join([p.value for p in permissions])
                logger.warning(
                    f"Permission denied: user={user_id}, required_any={perm_list}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: one of [{perm_list}] required"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_role(role: Role):
    """Decorator to require a specific role or higher"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: TokenData = Depends(get_current_user), **kwargs):
            user_id = current_user.username
            user_role = rbac_manager.get_user_role(user_id)
            
            # Define role hierarchy
            role_hierarchy = [Role.GUEST, Role.RESEARCHER, Role.DEPARTMENT_HEAD, Role.ADMIN, Role.SUPER_ADMIN]
            
            if role_hierarchy.index(user_role) < role_hierarchy.index(role):
                logger.warning(
                    f"Role denied: user={user_id}, has={user_role.value}, required={role.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {role.value} or higher required"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# FastAPI dependency for getting current user's permissions
async def get_current_permissions(
    current_user: TokenData = Depends(get_current_user)
) -> Set[Permission]:
    """Dependency to get current user's permissions"""
    return rbac_manager.get_user_permissions(current_user.username)


async def get_current_role(
    current_user: TokenData = Depends(get_current_user)
) -> Role:
    """Dependency to get current user's role"""
    return rbac_manager.get_user_role(current_user.username)


# Export all
__all__ = [
    'Permission',
    'Role',
    'UserRole',
    'RBACManager',
    'rbac_manager',
    'require_permission',
    'require_any_permission',
    'require_role',
    'get_current_permissions',
    'get_current_role',
    'ROLE_PERMISSIONS',
]
