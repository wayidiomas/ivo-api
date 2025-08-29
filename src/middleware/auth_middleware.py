from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, List
from src.services.auth_service import AuthService
from src.models.auth import TokenInfo
import logging

logger = logging.getLogger(__name__)

class BearerTokenMiddleware:
    """Middleware para validação de tokens Bearer nos endpoints V2"""
    
    def __init__(self):
        self.auth_service = AuthService()
        
        # Endpoints que não requerem autenticação
        self.public_endpoints = [
            "/health",
            "/system/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/create-user",
            "/debug/",
            "/"
        ]
        
        # Endpoints V2 que requerem autenticação
        self.protected_v2_patterns = [
            "/api/v2/"
        ]
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Verificar se o endpoint é público"""
        return any(path.startswith(pattern) for pattern in self.public_endpoints)
    
    def _is_protected_v2_endpoint(self, path: str) -> bool:
        """Verificar se o endpoint V2 requer autenticação"""
        return any(path.startswith(pattern) for pattern in self.protected_v2_patterns)
    
    def _extract_bearer_token(self, request: Request) -> Optional[str]:
        """Extrair token Bearer do header Authorization"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        if not auth_header.startswith("Bearer "):
            return None
        
        return auth_header[7:]  # Remove "Bearer "
    
    async def __call__(self, request: Request, call_next):
        """Middleware principal para validação de autenticação"""
        
        # Endpoints públicos não requerem autenticação
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Endpoints V2 requerem autenticação Bearer
        if self._is_protected_v2_endpoint(request.url.path):
            bearer_token = self._extract_bearer_token(request)
            
            if not bearer_token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "success": False,
                        "error_code": "MISSING_BEARER_TOKEN",
                        "message": "Token Bearer obrigatório para endpoints V2",
                        "details": {
                            "path": request.url.path,
                            "required_header": "Authorization: Bearer <token>",
                            "obtain_token": "POST /api/auth/login com api-key-ivo"
                        }
                    }
                )
            
            # Validar token Bearer
            try:
                token_info = await self.auth_service.validate_bearer_token(bearer_token)
                
                if not token_info:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "success": False,
                            "error_code": "INVALID_BEARER_TOKEN",
                            "message": "Token Bearer inválido ou expirado",
                            "details": {
                                "path": request.url.path,
                                "token_status": "invalid_or_expired",
                                "renew_token": "POST /api/auth/login para renovar token"
                            }
                        }
                    )
                
                # Verificar scopes se necessário
                if not self._has_required_scope(token_info, request.url.path):
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "success": False,
                            "error_code": "INSUFFICIENT_SCOPE",
                            "message": "Token não possui permissões para este endpoint",
                            "details": {
                                "path": request.url.path,
                                "token_scopes": token_info.scopes,
                                "required_scope": "v2_access"
                            }
                        }
                    )
                
                # Adicionar informações do token ao request state
                request.state.token_info = token_info
                request.state.user_id = token_info.user_id
                request.state.authenticated = True
                
            except Exception as e:
                logger.error(f"Erro na validação do token Bearer: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "error_code": "AUTH_SERVICE_ERROR",
                        "message": "Erro interno na validação do token",
                        "details": {
                            "path": request.url.path,
                            "error": "Service temporarily unavailable"
                        }
                    }
                )
        
        return await call_next(request)
    
    def _has_required_scope(self, token_info: TokenInfo, path: str) -> bool:
        """Verificar se o token possui o scope necessário"""
        # Por enquanto, todos os endpoints V2 requerem apenas "v2_access"
        required_scopes = ["v2_access"]
        
        # Verificar se token possui pelo menos um scope requerido
        return any(scope in token_info.scopes for scope in required_scopes)

# Função para aplicar o middleware na aplicação
def apply_auth_middleware(app):
    """Aplicar middleware de autenticação à aplicação FastAPI"""
    middleware = BearerTokenMiddleware()
    app.add_middleware(lambda request, call_next: middleware(request, call_next))
    logger.info("✅ Middleware de autenticação Bearer aplicado")
    return middleware