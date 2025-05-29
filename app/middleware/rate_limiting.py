import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timedelta
import ipaddress

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with per-IP and per-endpoint tracking.
    """
    
    def __init__(
        self,
        default_calls: int = 100,
        default_period: int = 60,
        burst_calls: int = 10,
        burst_period: int = 1
    ):
        self.default_calls = default_calls  # calls per period
        self.default_period = default_period  # period in seconds
        self.burst_calls = burst_calls  # burst calls per burst period
        self.burst_period = burst_period  # burst period in seconds
        
        # Storage for rate limiting data
        self.clients: Dict[str, Dict] = defaultdict(lambda: {
            'calls': [],
            'burst_calls': [],
            'blocked_until': None
        })
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            '/auth/login': {'calls': 5, 'period': 60, 'burst': 3},
            '/auth/forgot-password': {'calls': 3, 'period': 300, 'burst': 1},
            '/auth/reset-password': {'calls': 3, 'period': 300, 'burst': 1},
            '/users/': {'calls': 50, 'period': 60, 'burst': 10},
        }
        
        # Whitelist for internal IPs
        self.whitelist = [
            ipaddress.ip_network('127.0.0.0/8'),
            ipaddress.ip_network('10.0.0.0/8'),
            ipaddress.ip_network('172.16.0.0/12'),
            ipaddress.ip_network('192.168.0.0/16'),
        ]

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else '127.0.0.1'

    def _is_whitelisted(self, ip: str) -> bool:
        """Check if IP is in whitelist."""
        try:
            client_ip = ipaddress.ip_address(ip)
            return any(client_ip in network for network in self.whitelist)
        except ValueError:
            return False

    def _clean_old_calls(self, calls: list, period: int) -> list:
        """Remove calls older than the specified period."""
        current_time = time.time()
        return [call_time for call_time in calls if current_time - call_time < period]

    def _get_limits(self, endpoint: str) -> Tuple[int, int, int]:
        """Get rate limits for specific endpoint."""
        if endpoint in self.endpoint_limits:
            limits = self.endpoint_limits[endpoint]
            return limits['calls'], limits['period'], limits['burst']
        return self.default_calls, self.default_period, self.burst_calls

    async def is_allowed(self, request: Request) -> Tuple[bool, Optional[Dict]]:
        """
        Check if request is allowed based on rate limits.
        Returns (is_allowed, error_info)
        """
        client_ip = self._get_client_ip(request)
        
        # Skip rate limiting for whitelisted IPs
        if self._is_whitelisted(client_ip):
            return True, None

        current_time = time.time()
        endpoint = request.url.path
        client_data = self.clients[client_ip]

        # Check if client is currently blocked
        if client_data['blocked_until'] and current_time < client_data['blocked_until']:
            remaining_time = int(client_data['blocked_until'] - current_time)
            return False, {
                'error': 'rate_limit_exceeded',
                'message': f'Too many requests. Try again in {remaining_time} seconds.',
                'retry_after': remaining_time
            }

        # Get limits for this endpoint
        calls_limit, period, burst_limit = self._get_limits(endpoint)

        # Clean old calls
        client_data['calls'] = self._clean_old_calls(client_data['calls'], period)
        client_data['burst_calls'] = self._clean_old_calls(client_data['burst_calls'], self.burst_period)

        # Check burst limit (short-term)
        if len(client_data['burst_calls']) >= burst_limit:
            # Block for burst period
            client_data['blocked_until'] = current_time + self.burst_period
            return False, {
                'error': 'burst_limit_exceeded',
                'message': f'Too many requests in short time. Try again in {self.burst_period} seconds.',
                'retry_after': self.burst_period
            }

        # Check regular limit (long-term)
        if len(client_data['calls']) >= calls_limit:
            # Block for remaining period
            oldest_call = min(client_data['calls']) if client_data['calls'] else current_time
            retry_after = int(period - (current_time - oldest_call))
            client_data['blocked_until'] = current_time + retry_after
            
            return False, {
                'error': 'rate_limit_exceeded',
                'message': f'Rate limit exceeded. Try again in {retry_after} seconds.',
                'retry_after': retry_after
            }

        # Request is allowed, record it
        client_data['calls'].append(current_time)
        client_data['burst_calls'].append(current_time)
        
        return True, None

    def get_rate_limit_headers(self, request: Request) -> Dict[str, str]:
        """Get rate limit headers for response."""
        client_ip = self._get_client_ip(request)
        
        if self._is_whitelisted(client_ip):
            return {}

        endpoint = request.url.path
        calls_limit, period, _ = self._get_limits(endpoint)
        client_data = self.clients[client_ip]
        
        # Clean old calls for accurate count
        current_time = time.time()
        client_data['calls'] = self._clean_old_calls(client_data['calls'], period)
        
        remaining = max(0, calls_limit - len(client_data['calls']))
        reset_time = int(current_time + period)
        
        return {
            'X-RateLimit-Limit': str(calls_limit),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset_time),
            'X-RateLimit-Window': str(period)
        }

    async def cleanup_old_entries(self):
        """Periodic cleanup of old rate limit entries."""
        current_time = time.time()
        cleanup_threshold = 3600  # Clean entries older than 1 hour
        
        clients_to_remove = []
        for client_ip, data in self.clients.items():
            # Remove old calls
            data['calls'] = self._clean_old_calls(data['calls'], cleanup_threshold)
            data['burst_calls'] = self._clean_old_calls(data['burst_calls'], cleanup_threshold)
            
            # Remove blocked status if expired
            if data['blocked_until'] and current_time > data['blocked_until']:
                data['blocked_until'] = None
            
            # Mark empty entries for removal
            if (not data['calls'] and not data['burst_calls'] and 
                data['blocked_until'] is None):
                clients_to_remove.append(client_ip)
        
        # Remove empty entries
        for client_ip in clients_to_remove:
            del self.clients[client_ip]
        
        logger.info(f"Rate limiter cleanup: removed {len(clients_to_remove)} old entries")


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware.
    """
    # Skip rate limiting for health check and docs
    if request.url.path in ['/health', '/docs', '/redoc', '/openapi.json']:
        response = await call_next(request)
        return response

    # Check rate limit
    is_allowed, error_info = await rate_limiter.is_allowed(request)
    
    if not is_allowed:
        logger.warning(
            f"Rate limit exceeded for IP {rate_limiter._get_client_ip(request)} "
            f"on endpoint {request.url.path}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "error": {
                    "code": error_info['error'],
                    "message": error_info['message'],
                    "retry_after": error_info['retry_after']
                }
            },
            headers={"Retry-After": str(error_info['retry_after'])}
        )

    # Process request
    response = await call_next(request)
    
    # Add rate limit headers
    headers = rate_limiter.get_rate_limit_headers(request)
    for key, value in headers.items():
        response.headers[key] = value
    
    return response


async def cleanup_task():
    """Background task for periodic cleanup."""
    while True:
        try:
            await rate_limiter.cleanup_old_entries()
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Error in rate limiter cleanup task: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying


def setup_rate_limiting(app: FastAPI):
    """
    Setup rate limiting middleware for FastAPI app.
    """
    app.middleware("http")(rate_limit_middleware)
    
    # Start cleanup task
    @app.on_event("startup")
    async def start_cleanup_task():
        asyncio.create_task(cleanup_task())
    
    logger.info("Rate limiting middleware configured")
    
    # Add endpoint to check rate limit status (useful for debugging)
    @app.get("/rate-limit-status")
    async def get_rate_limit_status(request: Request):
        """Get current rate limit status for debugging."""
        client_ip = rate_limiter._get_client_ip(request)
        
        if rate_limiter._is_whitelisted(client_ip):
            return {"status": "whitelisted", "limits": "none"}
        
        client_data = rate_limiter.clients.get(client_ip, {})
        current_time = time.time()
        
        # Clean old calls for accurate status
        calls = rate_limiter._clean_old_calls(
            client_data.get('calls', []), 
            rate_limiter.default_period
        )
        burst_calls = rate_limiter._clean_old_calls(
            client_data.get('burst_calls', []), 
            rate_limiter.burst_period
        )
        
        return {
            "client_ip": client_ip,
            "current_calls": len(calls),
            "max_calls": rate_limiter.default_calls,
            "current_burst_calls": len(burst_calls),
            "max_burst_calls": rate_limiter.burst_calls,
            "blocked_until": client_data.get('blocked_until'),
            "is_blocked": (
                client_data.get('blocked_until', 0) > current_time
                if client_data.get('blocked_until') else False
            )
        }