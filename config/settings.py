"""Configurações centralizadas do sistema IVO V2."""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configurações principais do sistema."""
    
    # ✅ CRÍTICO: Configuração Pydantic v2 (permite campos extras + env)
    model_config = {
        "extra": "allow",
        "env_file": ".env",
        "case_sensitive": False
    }
    
    # OpenAI Configuration - Modelos 2025 (100% compatível com seu .env)
    openai_api_key: Optional[str] = None
    
    # Modelos por complexidade (Janeiro 2025)
    openai_model_simple: str = "gpt-4o-mini"       # TIER 1: RAG, validações básicas
    openai_model_vision: str = "gpt-4o-mini"       # TIER 1: Análise de imagens
    openai_model_medium: str = "gpt-5-mini"        # TIER 2: Vocabulary, Sentences
    openai_model_reasoning_lite: str = "o3-mini"   # TIER 3: Tips, Grammar
    openai_model_complex: str = "gpt-5"            # TIER 4: Unit generation
    openai_model_reasoning: str = "o3"             # TIER 5: Assessments
    
    # Modelo padrão (fallback) e configurações gerais
    openai_model: str = "gpt-5-mini"               # Modelo padrão
    openai_vision_model: str = "gpt-4o-mini"       # Mantido para compatibilidade
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7
    openai_timeout: int = 120
    openai_reasoning_effort: str = "medium"        # Para modelos o3: low, medium, high
    
    # Database Configuration
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    
    # Application Configuration (exatos do seu .env)
    app_name: str = "Curso Na Way - IVO V2 Hierárquico"
    app_version: str = "2.0.0"
    app_description: str = "Sistema hierárquico de geração de unidades educacionais com IA"
    app_environment: str = "development"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    reload: bool = True
    
    # Security
    secret_key: str = "your-super-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS Configuration (do seu .env)
    allowed_origins: str = "http://localhost:3000,http://localhost:8080,http://localhost:5173"
    allowed_methods: str = "GET,POST,PUT,DELETE,PATCH"
    allowed_headers: str = "*"
    
    # Database Connection Pool
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # LangChain Configuration (para tracing)
    langchain_tracing_v2: bool = True
    langchain_api_key: str = "your-langchain-api-key"
    langchain_project: str = "curso-na-way-ivo-v2"
    
    # MCP (Model Context Protocol) Configuration
    mcp_image_server_host: str = "localhost"
    mcp_image_server_port: int = 3002
    mcp_image_server_path: str = "./src/services/mcp_image_service.py"
    
    # IVO V2 Specific Configuration
    default_cefr_level: str = "A2"
    default_vocabulary_count: int = 25
    default_unit_type: str = "lexical_unit"
    
    # File Upload Configuration
    max_image_size: int = 10485760  # 10MB
    max_images_per_request: int = 5
    allowed_image_types: str = "jpg,jpeg,png,webp"
    supported_image_formats: str = "jpg,jpeg,png,webp,gif"
    
    # Image Processing
    image_analysis_timeout: int = 120
    enable_image_caching: bool = True
    image_cache_ttl: int = 3600  # 1 hora
    
    # Paths
    upload_dir: str = "./data/images/uploads"
    processed_dir: str = "./data/images/processed"
    pdf_dir: str = "./data/pdfs/generated"
    temp_dir: str = "./data/temp"
    cache_dir: str = "./data/cache"


# Instância global das configurações
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Obter instância singleton das configurações."""
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception as e:
            print(f"⚠️ Erro ao carregar Settings: {e}")
            # Criar instância com valores padrão em caso de erro
            _settings = Settings.model_construct()
    return _settings


# Funções de conveniência para compatibilidade
def get_openai_api_key() -> Optional[str]:
    """Obter chave da API OpenAI."""
    return get_settings().openai_api_key


def get_openai_config() -> dict:
    """Obter configurações completas do OpenAI - Modelos 2025."""
    settings = get_settings()
    return {
        "api_key": settings.openai_api_key,
        "model": settings.openai_model,
        "vision_model": settings.openai_vision_model,
        "models": {
            "simple": settings.openai_model_simple,
            "vision": settings.openai_model_vision,
            "medium": settings.openai_model_medium,
            "reasoning_lite": settings.openai_model_reasoning_lite,
            "complex": settings.openai_model_complex,
            "reasoning": settings.openai_model_reasoning
        },
        "max_tokens": settings.openai_max_tokens,
        "temperature": settings.openai_temperature,
        "timeout": settings.openai_timeout,
        "reasoning_effort": settings.openai_reasoning_effort
    }


def get_supabase_config() -> dict:
    """Obter configurações do Supabase."""
    settings = get_settings()
    return {
        "url": settings.supabase_url,
        "anon_key": settings.supabase_anon_key,
        "service_key": settings.supabase_service_key
    }


def get_database_config() -> dict:
    """Obter configurações do banco de dados."""
    settings = get_settings()
    return {
        **get_supabase_config(),
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_timeout": settings.db_pool_timeout
    }


def get_cors_config() -> dict:
    """Obter configurações de CORS."""
    settings = get_settings()
    return {
        "allow_origins": settings.allowed_origins.split(","),
        "allow_methods": settings.allowed_methods.split(","),
        "allow_headers": settings.allowed_headers.split(",") if settings.allowed_headers != "*" else ["*"],
        "allow_credentials": True
    }


def get_image_config() -> dict:
    """Obter configurações de processamento de imagens."""
    settings = get_settings()
    return {
        "max_size": settings.max_image_size,
        "max_images": settings.max_images_per_request,
        "allowed_types": settings.allowed_image_types.split(","),
        "supported_formats": settings.supported_image_formats.split(","),
        "analysis_timeout": settings.image_analysis_timeout,
        "enable_caching": settings.enable_image_caching,
        "cache_ttl": settings.image_cache_ttl
    }


def get_ivo_defaults() -> dict:
    """Obter configurações padrão do IVO V2."""
    settings = get_settings()
    return {
        "cefr_level": settings.default_cefr_level,
        "vocabulary_count": settings.default_vocabulary_count,
        "unit_type": settings.default_unit_type
    }


def get_langchain_config() -> dict:
    """Obter configurações do LangChain."""
    settings = get_settings()
    return {
        "tracing_v2": settings.langchain_tracing_v2,
        "api_key": settings.langchain_api_key,
        "project": settings.langchain_project
    }


def get_mcp_config() -> dict:
    """Obter configurações do MCP (Model Context Protocol)."""
    settings = get_settings()
    return {
        "host": settings.mcp_image_server_host,
        "port": settings.mcp_image_server_port,
        "path": settings.mcp_image_server_path
    }


def is_development() -> bool:
    """Verificar se está em modo desenvolvimento."""
    return get_settings().app_environment.lower() == "development"


def is_production() -> bool:
    """Verificar se está em modo produção."""
    return get_settings().app_environment.lower() == "production"


# Validações de configuração
def validate_required_settings() -> dict:
    """Validar configurações obrigatórias."""
    try:
        settings = get_settings()
        missing = []
        warnings = []
        
        # Verificar configurações críticas
        if not settings.openai_api_key:
            missing.append("OPENAI_API_KEY")
        elif not settings.openai_api_key.startswith("sk-"):
            warnings.append("OPENAI_API_KEY não parece válida (deve começar com 'sk-')")
        
        if not settings.supabase_url:
            missing.append("SUPABASE_URL")
        
        if not settings.supabase_anon_key:
            missing.append("SUPABASE_ANON_KEY")
        
        # Verificar configurações recomendadas
        if settings.secret_key == "your-super-secret-key-here-change-in-production":
            warnings.append("SECRET_KEY usando valor padrão - altere em produção")
        
        if is_production() and settings.debug:
            warnings.append("DEBUG=True em ambiente de produção")
        
        if settings.langchain_api_key == "your-langchain-api-key":
            warnings.append("LANGCHAIN_API_KEY usando valor padrão")
        
        # Verificar valores numéricos
        if settings.openai_max_tokens <= 0:
            missing.append("OPENAI_MAX_TOKENS deve ser maior que 0")
        
        if not (0.0 <= settings.openai_temperature <= 2.0):
            warnings.append("OPENAI_TEMPERATURE recomendado entre 0.0 e 2.0")
        
        return {
            "valid": len(missing) == 0,
            "missing": missing,
            "warnings": warnings,
            "environment": settings.app_environment,
            "total_settings": len(settings.model_dump()),
            "openai_configured": bool(settings.openai_api_key),
            "database_configured": bool(settings.supabase_url and settings.supabase_anon_key)
        }
        
    except Exception as e:
        return {
            "valid": False,
            "missing": ["Erro ao carregar configurações"],
            "warnings": [],
            "environment": "unknown",
            "error": str(e)
        }


def get_all_settings() -> dict:
    """Obter todas as configurações (para debug)."""
    try:
        settings = get_settings()
        all_settings = settings.model_dump()
        
        # Mascarar informações sensíveis
        sensitive_fields = ["openai_api_key", "supabase_anon_key", "supabase_service_key", "secret_key", "langchain_api_key"]
        for field in sensitive_fields:
            if field in all_settings and all_settings[field]:
                if len(str(all_settings[field])) > 8:
                    all_settings[field] = "***" + str(all_settings[field])[-4:]
                else:
                    all_settings[field] = "***"
        
        return all_settings
    except Exception as e:
        return {"error": f"Erro ao obter configurações: {str(e)}"}


# Para compatibilidade com código existente
def get_config():
    """Alias para get_settings() para compatibilidade."""
    return get_settings()


# Teste das configurações
if __name__ == "__main__":
    print("🔧 Testando configurações do sistema...")
    
    try:
        # Testar carregamento básico
        settings = get_settings()
        print(f"✅ Settings carregado: {settings.app_name} v{settings.app_version}")
        
        # Testar configurações do OpenAI
        openai_config = get_openai_config()
        print(f"✅ OpenAI configurado: {openai_config['model']}")
        
        # Testar validação
        validation = validate_required_settings()
        print(f"✅ Validação: {'VÁLIDO' if validation['valid'] else 'INVÁLIDO'}")
        print(f"   Total configurações: {validation.get('total_settings', 'N/A')}")
        print(f"   OpenAI: {'✅' if validation.get('openai_configured') else '❌'}")
        print(f"   Database: {'✅' if validation.get('database_configured') else '❌'}")
        
        if validation['missing']:
            print(f"   ❌ Faltando: {validation['missing']}")
        if validation['warnings']:
            print(f"   ⚠️ Avisos: {validation['warnings']}")
        
        # Testar outras configurações
        cors_config = get_cors_config()
        print(f"✅ CORS: {len(cors_config['allow_origins'])} origens permitidas")
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()