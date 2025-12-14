"""
API Versioning utilities for GenNet services
"""
from fastapi import APIRouter, Request, Header, HTTPException, status
from typing import Optional, Callable
from enum import Enum
import re


class APIVersion(str, Enum):
    """API Version enumeration"""
    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"


def get_api_version(request: Request, default: APIVersion = APIVersion.V1) -> APIVersion:
    """
    Extract API version from request
    
    Checks in order:
    1. URL path (/v1/, /v2/, etc.)
    2. Accept header (application/vnd.gennet.v1+json)
    3. X-API-Version header
    4. Default version
    
    Args:
        request: FastAPI request object
        default: Default version if not specified
    
    Returns:
        APIVersion enum
    """
    # Check URL path
    path = request.url.path
    version_match = re.search(r'/v(\d+)/', path)
    if version_match:
        version_num = version_match.group(1)
        if version_num == "1":
            return APIVersion.V1
        elif version_num == "2":
            return APIVersion.V2
    
    # Check Accept header (e.g., application/vnd.gennet.v1+json)
    accept_header = request.headers.get("Accept", "")
    version_match = re.search(r'vnd\.gennet\.v(\d+)', accept_header)
    if version_match:
        version_num = version_match.group(1)
        if version_num == "1":
            return APIVersion.V1
        elif version_num == "2":
            return APIVersion.V2
    
    # Check X-API-Version header
    api_version_header = request.headers.get("X-API-Version", "").lower()
    if api_version_header == "v1" or api_version_header == "1":
        return APIVersion.V1
    elif api_version_header == "v2" or api_version_header == "2":
        return APIVersion.V2
    elif api_version_header == "latest":
        return APIVersion.LATEST
    
    return default


def require_version(*allowed_versions: APIVersion):
    """
    Dependency to require specific API version(s)
    
    Usage:
        @app.get("/networks")
        async def list_networks(
            version: APIVersion = Depends(require_version(APIVersion.V1, APIVersion.V2))
        ):
            ...
    """
    def version_check(request: Request) -> APIVersion:
        version = get_api_version(request)
        
        # If LATEST is requested, map to most recent version
        if version == APIVersion.LATEST:
            version = max(allowed_versions, key=lambda v: v.value)
        
        if version not in allowed_versions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"API version {version.value} not supported. Supported versions: {[v.value for v in allowed_versions]}"
            )
        
        return version
    
    return version_check


def create_versioned_router(base_path: str = "/api", default_version: APIVersion = APIVersion.V1):
    """
    Create a versioned API router
    
    Usage:
        v1_router = create_versioned_router("/api", APIVersion.V1)
        v2_router = create_versioned_router("/api", APIVersion.V2)
        
        @v1_router.get("/networks")
        async def list_networks_v1():
            ...
        
        @v2_router.get("/networks")
        async def list_networks_v2():
            ...
        
        app.include_router(v1_router)
        app.include_router(v2_router)
    """
    version = default_version.value
    router = APIRouter(
        prefix=f"{base_path}/{version}",
        tags=[f"API {version.upper()}"]
    )
    return router


class VersionedRouter:
    """
    Router that supports multiple API versions
    
    Usage:
        router = VersionedRouter("/api")
        
        @router.get("/networks", versions=[APIVersion.V1, APIVersion.V2])
        async def list_networks(version: APIVersion):
            if version == APIVersion.V1:
                return {"networks": [...]}  # V1 format
            else:
                return {"data": {"networks": [...]}, "meta": {...}}  # V2 format
    """
    
    def __init__(self, base_path: str = "/api"):
        self.base_path = base_path
        self.routes = {}
    
    def _register_route(
        self,
        method: str,
        path: str,
        endpoint: Callable,
        versions: list[APIVersion],
        **kwargs
    ):
        """Register a route for multiple versions"""
        for version in versions:
            full_path = f"{self.base_path}/{version.value}{path}"
            key = (method, full_path)
            self.routes[key] = {
                "endpoint": endpoint,
                "version": version,
                "kwargs": kwargs
            }
    
    def get(self, path: str, versions: list[APIVersion] = None, **kwargs):
        """Register GET route for specified versions"""
        if versions is None:
            versions = [APIVersion.V1]
        
        def decorator(func: Callable):
            self._register_route("GET", path, func, versions, **kwargs)
            return func
        return decorator
    
    def post(self, path: str, versions: list[APIVersion] = None, **kwargs):
        """Register POST route for specified versions"""
        if versions is None:
            versions = [APIVersion.V1]
        
        def decorator(func: Callable):
            self._register_route("POST", path, func, versions, **kwargs)
            return func
        return decorator
    
    def put(self, path: str, versions: list[APIVersion] = None, **kwargs):
        """Register PUT route for specified versions"""
        if versions is None:
            versions = [APIVersion.V1]
        
        def decorator(func: Callable):
            self._register_route("PUT", path, func, versions, **kwargs)
            return func
        return decorator
    
    def delete(self, path: str, versions: list[APIVersion] = None, **kwargs):
        """Register DELETE route for specified versions"""
        if versions is None:
            versions = [APIVersion.V1]
        
        def decorator(func: Callable):
            self._register_route("DELETE", path, func, versions, **kwargs)
            return func
        return decorator


def add_version_header(response, version: APIVersion):
    """
    Add API version header to response
    
    Usage:
        @app.get("/networks")
        async def list_networks(version: APIVersion = Depends(require_version(APIVersion.V1))):
            response = JSONResponse(content={"networks": [...]})
            add_version_header(response, version)
            return response
    """
    response.headers["X-API-Version"] = version.value
    return response

