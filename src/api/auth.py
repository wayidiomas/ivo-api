from fastapi import APIRouter, HTTPException, Header, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from src.models.auth import AuthRequest, AuthResponse, CreateUserRequest, CreateUserResponse
from src.services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

def get_auth_service() -> AuthService:
    return AuthService()

@router.post("/login", response_model=AuthResponse)
async def login(
    request: AuthRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Autentica com email + chave de acesso e retorna token Bearer para acesso à API V2
    
    - **email**: Email do usuário registrado
    - **api_key_ivo**: Chave de acesso IVO (funciona como senha)
    - Retorna token Bearer válido para uso na API V2
    """
    try:
        auth_response = await auth_service.authenticate_with_email_and_key(request.email, request.api_key_ivo)
        
        if not auth_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou chave de acesso inválidos"
            )
        
        # Log de sucesso no login (sem dados sensíveis)
        logger.info(f"🔐 LOGIN_SUCCESS: {request.email} autenticado | User: {auth_response.user_id}")
        return auth_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no processo de autenticação"
        )

@router.post("/create-user", response_model=CreateUserResponse)
async def create_user(
    request: CreateUserRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Cria novo usuário com tokens de acesso
    
    - **email**: Email único do usuário
    - **phone**: Telefone opcional
    - **metadata**: Dados adicionais em JSON
    - **scopes**: Permissões do token (padrão: ["v2_access"])
    - **rate_limit_config**: Configuração de rate limiting
    
    Retorna usuário criado e informações dos tokens
    """
    try:
        result = await auth_service.create_user_with_token(request)
        
        # Incluir o token IVO na resposta (apenas uma vez na criação)
        response_data = CreateUserResponse(
            user=result["user"],
            token_info=result["token_info"],
            message=result["message"]
        )
        
        # Log importante para administradores (sem token completo)
        logger.info(f"👤 USER_CREATED: {result['user'].email} | ID: {result['user'].id}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        
        # Verificar se é erro de email duplicado
        if "duplicate key value violates unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email já está em uso"
            )
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar usuário"
        )

@router.get("/validate-token")
async def validate_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Valida token Bearer atual
    
    Endpoint para verificar se o token Bearer ainda é válido
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Bearer não fornecido"
        )
    
    try:
        token_info = await auth_service.validate_bearer_token(credentials.credentials)
        
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Bearer inválido ou expirado"
            )
        
        return {
            "valid": True,
            "user_id": token_info.user_id,
            "scopes": token_info.scopes,
            "expires_at": token_info.expires_at,
            "usage_count": token_info.usage_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na validação do token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na validação do token"
        )