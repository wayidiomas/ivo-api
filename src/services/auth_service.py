from typing import Optional, Dict, Any, List
import secrets
import hashlib
from datetime import datetime, timezone
from supabase import Client
from src.models.auth import UserCreate, UserResponse, TokenInfo, AuthResponse, CreateUserRequest
from config.database import get_supabase_admin_client
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.supabase: Client = get_supabase_admin_client()
    
    def _generate_secure_token(self, prefix: str = "", length: int = 32) -> str:
        """Gera token seguro com prefixo opcional"""
        secure_token = secrets.token_urlsafe(length)
        return f"{prefix}{secure_token}" if prefix else secure_token
    
    def _hash_token(self, token: str) -> str:
        """Cria hash do token para armazenamento seguro"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def validate_api_key_ivo(self, api_key_ivo: str) -> Optional[TokenInfo]:
        """Valida token IVO e retorna informações do token se válido"""
        try:
            result = self.supabase.table("ivo_api_tokens").select(
                "id, token_ivo, token_bearer, user_id, is_active, expires_at, "
                "scopes, rate_limit_config, created_at, updated_at, last_used_at, usage_count"
            ).eq("token_ivo", api_key_ivo).eq("is_active", True).execute()
            
            if not result.data:
                logger.warning(f"🚫 INVALID_API_KEY: Token IVO inválido ou inativo: {api_key_ivo[:8]}...")
                return None
                
            token_data = result.data[0]
            
            # Verificar expiração se houver
            if token_data.get("expires_at"):
                expires_at = datetime.fromisoformat(token_data["expires_at"].replace('Z', '+00:00'))
                if expires_at < datetime.now(timezone.utc):
                    logger.warning(f"Token IVO expirado: {api_key_ivo[:10]}...")
                    return None
            
            # Atualizar last_used_at e usage_count
            await self._update_token_usage(token_data["id"])
            
            return TokenInfo(**token_data)
            
        except Exception as e:
            logger.error(f"Erro ao validar token IVO: {str(e)}")
            return None
    
    async def validate_bearer_token(self, bearer_token: str) -> Optional[TokenInfo]:
        """Valida token Bearer e retorna informações do token se válido"""
        try:
            result = self.supabase.table("ivo_api_tokens").select(
                "id, token_ivo, token_bearer, user_id, is_active, expires_at, "
                "scopes, rate_limit_config, created_at, updated_at, last_used_at, usage_count"
            ).eq("token_bearer", bearer_token).eq("is_active", True).execute()
            
            if not result.data:
                logger.warning(f"🚫 INVALID_BEARER: Token Bearer inválido ou inativo: {bearer_token[:8]}...")
                return None
                
            token_data = result.data[0]
            
            # Verificar expiração se houver
            if token_data.get("expires_at"):
                expires_at = datetime.fromisoformat(token_data["expires_at"].replace('Z', '+00:00'))
                if expires_at < datetime.now(timezone.utc):
                    logger.warning(f"Token Bearer expirado: {bearer_token[:10]}...")
                    return None
            
            # Atualizar last_used_at e usage_count
            await self._update_token_usage(token_data["id"])
            
            return TokenInfo(**token_data)
            
        except Exception as e:
            logger.error(f"Erro ao validar token Bearer: {str(e)}")
            return None
    
    async def _update_token_usage(self, token_id: str) -> None:
        """Atualiza contadores de uso do token"""
        try:
            self.supabase.table("ivo_api_tokens").update({
                "last_used_at": datetime.now(timezone.utc).isoformat(),
                "usage_count": self.supabase.table("ivo_api_tokens").select("usage_count").eq("id", token_id).execute().data[0]["usage_count"] + 1,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", token_id).execute()
        except Exception as e:
            logger.error(f"Erro ao atualizar uso do token: {str(e)}")
    
    async def authenticate_with_api_key(self, api_key_ivo: str) -> Optional[AuthResponse]:
        """Autentica com token IVO e retorna token Bearer"""
        token_info = await self.validate_api_key_ivo(api_key_ivo)
        
        if not token_info:
            return None
            
        return AuthResponse(
            access_token=token_info.token_bearer,
            token_type="bearer",
            user_id=token_info.user_id,
            scopes=token_info.scopes,
            expires_at=token_info.expires_at,
            rate_limit=token_info.rate_limit_config
        )
    
    async def authenticate_with_email_and_key(self, email: str, api_key_ivo: str) -> Optional[AuthResponse]:
        """Autentica com email + token IVO e retorna token Bearer"""
        try:
            # 1. Buscar usuário por email
            logger.info(f"🔍 Buscando usuário: '{email}'")
            user_result = self.supabase.table("ivo_users").select("id, email, is_active").eq("email", email).execute()
            
            logger.info(f"🔍 User query result: {len(user_result.data) if user_result.data else 0} results")
            if user_result.data:
                logger.info(f"🔍 Encontrou usuário: {user_result.data[0].get('email')} (ID: {user_result.data[0].get('id')})")
            
            if not user_result.data:
                logger.warning(f"🚫 LOGIN_FAILED: Usuário não encontrado para email: {email}")
                return None
                
            user = user_result.data[0]
            user_id = user["id"]
            
            # Verificar se usuário está ativo
            if not user.get("is_active", False):
                logger.warning(f"🚫 LOGIN_FAILED: Usuário inativo: {email}")
                return None
            
            # 2. Buscar token por api_key_ivo E verificar se pertence ao usuário
            logger.info(f"🔍 Buscando token com length: {len(api_key_ivo)}")
            
            token_result = self.supabase.table("ivo_api_tokens").select(
                "id, token_ivo, token_bearer, user_id, is_active, expires_at, "
                "scopes, rate_limit_config, created_at, updated_at, last_used_at, usage_count"
            ).eq("token_ivo", api_key_ivo).execute()
            
            logger.info(f"🔍 Token query result: {len(token_result.data) if token_result.data else 0} results")
            if token_result.data:
                logger.info(f"🔍 Encontrou {len(token_result.data)} token(s)")
            
            if not token_result.data:
                logger.warning(f"🚫 LOGIN_FAILED: Token IVO inválido: {api_key_ivo[:8]}... para usuário: {email}")
                return None
                
            token_data = token_result.data[0]
            
            # Verificar se token está ativo
            if not token_data.get("is_active", False):
                logger.warning(f"🚫 LOGIN_FAILED: Token inativo: {api_key_ivo[:8]}... para usuário: {email}")
                return None
            
            # 3. Verificar se o token pertence ao usuário
            if token_data["user_id"] != user_id:
                logger.warning(f"🚫 LOGIN_FAILED: Token não pertence ao usuário. Email: {email}, Token: {api_key_ivo[:8]}...")
                return None
            
            # 4. Verificar expiração se houver
            if token_data.get("expires_at"):
                expires_at = datetime.fromisoformat(token_data["expires_at"].replace('Z', '+00:00'))
                if expires_at < datetime.now(timezone.utc):
                    logger.warning(f"🚫 LOGIN_FAILED: Token expirado para usuário: {email}")
                    return None
            
            # 5. Atualizar uso do token
            await self._update_token_usage(token_data["id"])
            
            # 6. Retornar resposta de auth
            logger.info(f"✅ LOGIN_SUCCESS: {email} autenticado com sucesso | User ID: {user_id}")
            
            return AuthResponse(
                access_token=token_data["token_bearer"],
                token_type="bearer",
                user_id=user_id,
                scopes=token_data["scopes"],
                expires_at=token_data.get("expires_at"),
                rate_limit=token_data["rate_limit_config"]
            )
            
        except Exception as e:
            logger.error(f"Erro na autenticação email+key: {str(e)}")
            return None
    
    async def create_user_with_token(self, request: CreateUserRequest) -> Dict[str, Any]:
        """Cria usuário e token de acesso"""
        try:
            # Criar usuário
            user_data = {
                "email": request.email,
                "phone": request.phone,
                "is_active": True,
                "metadata": request.metadata
            }
            
            user_result = self.supabase.table("ivo_users").insert(user_data).execute()
            
            if not user_result.data:
                raise Exception("Falha ao criar usuário")
                
            user = UserResponse(**user_result.data[0])
            
            # Gerar tokens
            token_ivo = self._generate_secure_token("ivo_", 24)
            token_bearer = self._generate_secure_token("ivo_bearer_", 32)
            
            # Criar token
            token_data = {
                "token_ivo": token_ivo,
                "token_bearer": token_bearer,
                "user_id": user.id,
                "is_active": True,
                "scopes": request.scopes,
                "rate_limit_config": request.rate_limit_config
            }
            
            token_result = self.supabase.table("ivo_api_tokens").insert(token_data).execute()
            
            if not token_result.data:
                # Rollback - deletar usuário criado
                self.supabase.table("ivo_users").delete().eq("id", user.id).execute()
                raise Exception("Falha ao criar token")
            
            auth_response = AuthResponse(
                access_token=token_bearer,
                token_type="bearer",
                user_id=user.id,
                scopes=request.scopes,
                expires_at=None,
                rate_limit=request.rate_limit_config
            )
            
            return {
                "user": user,
                "token_info": auth_response,
                "api_key_ivo": token_ivo,  # Retornar também o token IVO para o usuário
                "message": "Usuário e tokens criados com sucesso"
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário e token: {str(e)}")
            raise Exception(f"Erro ao criar usuário: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Busca usuário por ID"""
        try:
            result = self.supabase.table("ivo_users").select("*").eq("id", user_id).eq("is_active", True).execute()
            
            if not result.data:
                return None
                
            return UserResponse(**result.data[0])
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {str(e)}")
            return None
    
    async def deactivate_token(self, token_id: str) -> bool:
        """Desativa token"""
        try:
            result = self.supabase.table("ivo_api_tokens").update({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", token_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Erro ao desativar token: {str(e)}")
            return False