"""
Request and response compression middleware
"""
import gzip
try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic request/response compression
    
    Supports:
    - gzip compression
    - brotli compression (better compression ratio)
    
    Automatically compresses responses if:
    - Client supports compression (Accept-Encoding header)
    - Response size > minimum_size threshold
    - Content-Type is compressible
    """
    
    # Compressible content types
    COMPRESSIBLE_TYPES = {
        "text/",
        "application/json",
        "application/javascript",
        "application/xml",
        "application/rss+xml",
        "application/atom+xml",
        "application/rdf+xml",
        "image/svg+xml",
    }
    
    # Non-compressible types (already compressed)
    NON_COMPRESSIBLE_TYPES = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "video/",
        "audio/",
        "application/gzip",
        "application/zip",
        "application/x-gzip",
        "application/x-compress",
    }
    
    def __init__(
        self,
        app,
        minimum_size: int = 1024,  # 1KB minimum to compress
        compress_level: int = 6,  # gzip compression level (1-9)
        prefer_brotli: bool = True
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compress_level = compress_level
        self.prefer_brotli = prefer_brotli
    
    def _should_compress(self, content_type: str, content_length: int) -> bool:
        """Check if response should be compressed"""
        # Check size
        if content_length < self.minimum_size:
            return False
        
        # Check if already compressed
        for non_compressible in self.NON_COMPRESSIBLE_TYPES:
            if non_compressible in content_type:
                return False
        
        # Check if compressible
        for compressible in self.COMPRESSIBLE_TYPES:
            if compressible in content_type:
                return True
        
        return False
    
    def _get_compression_method(self, accept_encoding: str) -> Optional[str]:
        """Determine compression method from Accept-Encoding header"""
        accept_encoding = accept_encoding.lower()
        
        if self.prefer_brotli and "br" in accept_encoding:
            return "br"  # Brotli
        elif "gzip" in accept_encoding:
            return "gzip"
        elif "deflate" in accept_encoding:
            return "deflate"
        
        return None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and compress response if applicable"""
        response = await call_next(request)
        
        # Skip compression for streaming responses
        if isinstance(response, StreamingResponse):
            return response
        
        # Get content type and length
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        content_encoding = response.headers.get("Content-Encoding", "")
        
        # Skip if already compressed
        if content_encoding:
            return response
        
        # Check if should compress
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                content_length = int(content_length)
            except (ValueError, TypeError):
                content_length = 0
        else:
            content_length = 0
        
        if not self._should_compress(content_type, content_length):
            return response
        
        # Get client's preferred compression method
        accept_encoding = request.headers.get("Accept-Encoding", "")
        compression_method = self._get_compression_method(accept_encoding)
        
        # Fallback to gzip if brotli requested but not available
        if compression_method == "br" and not BROTLI_AVAILABLE:
            compression_method = "gzip" if "gzip" in accept_encoding.lower() else None
        
        if not compression_method:
            return response
        
        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Compress body
        try:
            if compression_method == "br":
                compressed_body = brotli.compress(body, quality=self.compress_level)
            elif compression_method == "gzip":
                compressed_body = gzip.compress(body, compresslevel=self.compress_level)
            elif compression_method == "deflate":
                import zlib
                compressed_body = zlib.compress(body, level=self.compress_level)
            else:
                return response
            
            # Only compress if it actually reduces size
            if len(compressed_body) >= len(body):
                return response
            
            # Create new response with compressed body
            compressed_response = Response(
                content=compressed_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            compressed_response.headers["Content-Encoding"] = compression_method
            compressed_response.headers["Content-Length"] = str(len(compressed_body))
            compressed_response.headers["Vary"] = "Accept-Encoding"
            
            return compressed_response
        
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            # Return original response if compression fails
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )


def setup_compression(app, minimum_size: int = 1024, prefer_brotli: bool = True):
    """
    Setup compression middleware for FastAPI app
    
    Args:
        app: FastAPI application
        minimum_size: Minimum response size to compress (bytes)
        prefer_brotli: Prefer brotli over gzip if supported
    """
    app.add_middleware(
        CompressionMiddleware,
        minimum_size=minimum_size,
        prefer_brotli=prefer_brotli
    )

