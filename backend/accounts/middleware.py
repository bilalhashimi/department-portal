import jwt
import logging
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()
security_logger = logging.getLogger('security')


class SecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive security middleware for request auditing and protection
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming requests for security checks"""
        
        # Skip security checks for health and static endpoints
        if self._should_skip_security_check(request):
            return None
        
        # Log request details for audit
        self._log_request(request)
        
        # Check for suspicious patterns
        if self._is_suspicious_request(request):
            security_logger.warning(
                f"Suspicious request detected from {self._get_client_ip(request)}: "
                f"{request.method} {request.path}"
            )
        
        return None
    
    def process_response(self, request, response):
        """Process responses for audit logging"""
        
        if self._should_skip_security_check(request):
            return response
        
        # Log security-relevant responses
        if response.status_code in [401, 403, 404, 500]:
            self._log_security_response(request, response)
        
        return response
    
    def _should_skip_security_check(self, request):
        """Determine if security checks should be skipped"""
        skip_paths = [
            '/health/',
            '/static/',
            '/media/',
            '/admin/jsi18n/',
        ]
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _log_request(self, request):
        """Log request details for audit"""
        user = getattr(request, 'user', None)
        user_info = 'Anonymous'
        
        if user and user.is_authenticated:
            user_info = f"{user.email} (role: {user.role})"
        
        security_logger.debug(
            f"Request: {request.method} {request.path} - "
            f"User: {user_info} - "
            f"IP: {self._get_client_ip(request)} - "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
        )
    
    def _log_security_response(self, request, response):
        """Log security-relevant responses"""
        user = getattr(request, 'user', None)
        user_info = 'Anonymous'
        
        if user and user.is_authenticated:
            user_info = f"{user.email} (role: {user.role})"
        
        security_logger.warning(
            f"Security Response {response.status_code}: {request.method} {request.path} - "
            f"User: {user_info} - "
            f"IP: {self._get_client_ip(request)}"
        )
    
    def _is_suspicious_request(self, request):
        """Detect suspicious request patterns"""
        suspicious_patterns = [
            # SQL injection attempts
            "union select", "drop table", "insert into", "delete from",
            # XSS attempts
            "<script>", "javascript:", "onload=", "onerror=",
            # Path traversal
            "../", "..\\", "..\\/",
            # Command injection
            "; ls", "; cat", "; rm", "| ls", "| cat", "| rm",
        ]
        
        # Check query parameters and POST data
        request_data = ""
        if hasattr(request, 'GET'):
            request_data += str(request.GET)
        if hasattr(request, 'POST'):
            request_data += str(request.POST)
        
        request_data = request_data.lower()
        
        return any(pattern in request_data for pattern in suspicious_patterns)
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class EnhancedJWTMiddleware(MiddlewareMixin):
    """
    Enhanced JWT middleware for custom token validation and role enforcement
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process JWT tokens and add user context"""
        
        # Skip JWT processing for certain paths
        if self._should_skip_jwt_processing(request):
            return None
        
        # Extract and validate JWT token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            try:
                # Validate token and get user
                validated_token = self.jwt_auth.get_validated_token(token)
                user = self.jwt_auth.get_user(validated_token)
                
                # Add enhanced user context to request
                request.user = user
                request.jwt_payload = validated_token.payload
                
                # Check if user is still active and verified
                if not user.is_active:
                    security_logger.warning(f"Inactive user attempted access: {user.email}")
                    return JsonResponse(
                        {'error': 'Account has been deactivated'},
                        status=401
                    )
                
                # Log token usage for high-privilege accounts
                if user.role in ['admin', 'department_head']:
                    security_logger.info(
                        f"Privileged access: {user.email} (role: {user.role}) "
                        f"accessed {request.path}"
                    )
                
            except (InvalidToken, TokenError) as e:
                security_logger.warning(
                    f"Invalid JWT token from {self._get_client_ip(request)}: {str(e)}"
                )
                # Don't block the request here - let the view handle authentication
                pass
            except Exception as e:
                security_logger.error(f"JWT processing error: {str(e)}")
                pass
        
        return None
    
    def _should_skip_jwt_processing(self, request):
        """Determine if JWT processing should be skipped"""
        skip_paths = [
            '/health/',
            '/static/',
            '/media/',
            '/api/v1/accounts/auth/login/',
            '/api/v1/accounts/auth/register/',
            '/api/v1/documents/shared/',  # Public document access
        ]
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware for security
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}  # In production, use Redis or database
        super().__init__(get_response)
    
    def process_request(self, request):
        """Apply rate limiting"""
        
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limiting(request):
            return None
        
        ip = self._get_client_ip(request)
        current_time = timezone.now()
        
        # Simple rate limiting: 100 requests per minute per IP
        minute_key = f"{ip}_{current_time.strftime('%Y%m%d%H%M')}"
        
        if minute_key not in self.request_counts:
            self.request_counts[minute_key] = 0
        
        self.request_counts[minute_key] += 1
        
        # Clean old entries (basic cleanup)
        if len(self.request_counts) > 10000:
            old_keys = [k for k in self.request_counts.keys() 
                       if k.split('_')[1] < (current_time - timezone.timedelta(minutes=5)).strftime('%Y%m%d%H%M')]
            for key in old_keys:
                del self.request_counts[key]
        
        # Check rate limit
        if self.request_counts[minute_key] > 100:
            security_logger.warning(f"Rate limit exceeded for IP {ip}")
            return JsonResponse(
                {'error': 'Rate limit exceeded. Please try again later.'},
                status=429
            )
        
        return None
    
    def _should_skip_rate_limiting(self, request):
        """Determine if rate limiting should be skipped"""
        skip_paths = [
            '/health/',
            '/static/',
            '/media/',
        ]
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 