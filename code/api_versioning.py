"""
API Versioning Module for Research Collaboration System
Implements semantic versioning and backward compatibility for REST APIs
"""

from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional, Callable
from functools import wraps
import re
import logging

logger = logging.getLogger(__name__)

# API Version Constants
CURRENT_VERSION = "1.0.0"
MINIMUM_SUPPORTED_VERSION = "1.0.0"
DEPRECATED_VERSIONS = []  # Versions that work but show deprecation warning

# Semantic version regex
VERSION_REGEX = re.compile(r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9]+))?$')


class APIVersion:
    """Represents an API version with comparison support"""
    
    def __init__(self, version_string: str):
        match = VERSION_REGEX.match(version_string)
        if not match:
            raise ValueError(f"Invalid version format: {version_string}")
        
        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = int(match.group(3))
        self.prerelease = match.group(4)
        self.version_string = version_string
    
    def __str__(self) -> str:
        return self.version_string
    
    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            other = APIVersion(other)
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __lt__(self, other) -> bool:
        if isinstance(other, str):
            other = APIVersion(other)
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __le__(self, other) -> bool:
        return self == other or self < other
    
    def __gt__(self, other) -> bool:
        return not self <= other
    
    def __ge__(self, other) -> bool:
        return not self < other
    
    def is_compatible_with(self, other: 'APIVersion') -> bool:
        """Check if versions are compatible (same major version)"""
        if isinstance(other, str):
            other = APIVersion(other)
        return self.major == other.major


class VersionedAPIRouter(APIRouter):
    """
    API Router with version support.
    Allows mounting different versions of endpoints.
    """
    
    def __init__(self, version: str, **kwargs):
        self.api_version = APIVersion(version)
        prefix = kwargs.pop('prefix', '')
        super().__init__(prefix=f"/v{self.api_version.major}{prefix}", **kwargs)
        
        # Add version info to responses
        @self.middleware("http")
        async def add_version_header(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-API-Version"] = str(self.api_version)
            return response


def version_deprecated(deprecated_in: str, removed_in: Optional[str] = None, alternative: Optional[str] = None):
    """
    Decorator to mark an endpoint as deprecated.
    
    Args:
        deprecated_in: Version when the endpoint was deprecated
        removed_in: Version when the endpoint will be removed
        alternative: Alternative endpoint to use
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)
            
            # Add deprecation headers
            warning_msg = f"Deprecated since v{deprecated_in}"
            if removed_in:
                warning_msg += f", will be removed in v{removed_in}"
            if alternative:
                warning_msg += f". Use {alternative} instead"
            
            if isinstance(response, JSONResponse):
                response.headers["Deprecation"] = "true"
                response.headers["X-Deprecation-Warning"] = warning_msg
                if alternative:
                    response.headers["Link"] = f'<{alternative}>; rel="successor-version"'
            
            logger.warning(f"Deprecated endpoint called: {func.__name__} - {warning_msg}")
            return response
        
        # Add deprecation info to OpenAPI docs
        wrapper.__doc__ = f"**DEPRECATED**: {func.__doc__ or ''}\n\n{warning_msg}"
        return wrapper
    return decorator


async def validate_api_version(
    x_api_version: Optional[str] = Header(None, description="API version to use")
) -> APIVersion:
    """
    Dependency to validate and parse API version from request header.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(version: APIVersion = Depends(validate_api_version)):
            ...
    """
    if not x_api_version:
        return APIVersion(CURRENT_VERSION)
    
    try:
        requested_version = APIVersion(x_api_version)
    except ValueError:
        return APIVersion(CURRENT_VERSION)
    
    min_version = APIVersion(MINIMUM_SUPPORTED_VERSION)
    current_version = APIVersion(CURRENT_VERSION)
    
    # Check if version is supported
    if requested_version < min_version:
        raise ValueError(
            f"API version {x_api_version} is no longer supported. "
            f"Minimum supported version is {MINIMUM_SUPPORTED_VERSION}"
        )
    
    if requested_version > current_version:
        logger.warning(f"Requested future API version {x_api_version}, using {CURRENT_VERSION}")
        return current_version
    
    # Check for deprecation
    if x_api_version in DEPRECATED_VERSIONS:
        logger.warning(f"Deprecated API version {x_api_version} requested")
    
    return requested_version


# Version-specific router instances
v1_router = VersionedAPIRouter(version="1.0.0", tags=["v1"])


def create_versioned_app_info():
    """Create API version information for OpenAPI docs"""
    return {
        "title": "Research Collaboration System API",
        "description": """
## API Versioning

This API uses semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Current Version
`{current}`

### Minimum Supported Version
`{minimum}`

### Version Header
Include `X-API-Version` header in requests to specify the API version.

### Backward Compatibility
- All v1.x.x versions are backward compatible
- Deprecated endpoints include `Deprecation` header
- Breaking changes increment major version
        """.format(current=CURRENT_VERSION, minimum=MINIMUM_SUPPORTED_VERSION),
        "version": CURRENT_VERSION,
        "contact": {
            "name": "API Support",
            "email": "api-support@research-collab.example.com"
        },
        "license_info": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    }


# Export all
__all__ = [
    'APIVersion',
    'VersionedAPIRouter',
    'version_deprecated',
    'validate_api_version',
    'v1_router',
    'create_versioned_app_info',
    'CURRENT_VERSION',
    'MINIMUM_SUPPORTED_VERSION',
]
