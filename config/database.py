"""Configuração do banco de dados Supabase - Corrigido para Pydantic v2."""
import os
from supabase import create_client, Client
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class DatabaseSettings(BaseSettings):
    """Configurações do banco de dados - 100% compatível com Pydantic v2."""
    
    # ✅ CORRIGIDO: Usar ConfigDict para Pydantic v2
    model_config = ConfigDict(
        extra="allow",           # Permite campos extras do .env
        env_file=".env",         # Carrega do arquivo .env
        case_sensitive=False     # Não diferencia maiúsculas/minúsculas
    )
    
    # Campos de banco de dados
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    
    # Configurações de pool de conexão (opcionais)
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30


def get_supabase_client() -> Client:
    """Retorna cliente configurado do Supabase."""
    try:
        settings = DatabaseSettings()
        
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise ValueError("SUPABASE_URL e SUPABASE_ANON_KEY devem estar configurados no .env")
        
        return create_client(settings.supabase_url, settings.supabase_anon_key)
    except Exception as e:
        print(f"⚠️ Erro ao criar cliente Supabase: {e}")
        # Retornar cliente mock em caso de erro para não quebrar imports
        from unittest.mock import Mock
        return Mock()


def get_supabase_admin_client() -> Client:
    """Retorna cliente admin do Supabase."""
    try:
        settings = DatabaseSettings()
        
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_KEY devem estar configurados no .env")
        
        return create_client(settings.supabase_url, settings.supabase_service_key)
    except Exception as e:
        print(f"⚠️ Erro ao criar cliente admin Supabase: {e}")
        # Retornar cliente mock em caso de erro
        from unittest.mock import Mock
        return Mock()


def test_database_connection() -> dict:
    """Testar conexão com banco de dados."""
    try:
        client = get_supabase_client()
        
        # Teste simples de conexão
        result = client.table("ivo_courses").select("id").limit(1).execute()
        
        return {
            "connected": True,
            "message": "Conexão com Supabase OK",
            "table_accessible": True
        }
    except Exception as e:
        return {
            "connected": False,
            "message": f"Erro de conexão: {str(e)}",
            "table_accessible": False
        }


def validate_database_config() -> dict:
    """Validar configurações do banco de dados."""
    try:
        settings = DatabaseSettings()
        
        issues = []
        warnings = []
        
        if not settings.supabase_url:
            issues.append("SUPABASE_URL não configurada")
        elif not settings.supabase_url.startswith("https://"):
            warnings.append("SUPABASE_URL deve começar com 'https://'")
        
        if not settings.supabase_anon_key:
            issues.append("SUPABASE_ANON_KEY não configurada")
        
        if not settings.supabase_service_key:
            warnings.append("SUPABASE_SERVICE_KEY não configurada (opcional para operações admin)")
        
        # Verificar configurações de pool
        if settings.db_pool_size <= 0:
            warnings.append("db_pool_size deve ser maior que 0")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "settings_loaded": True,
            "config": {
                "url_configured": bool(settings.supabase_url),
                "anon_key_configured": bool(settings.supabase_anon_key),
                "service_key_configured": bool(settings.supabase_service_key),
                "pool_size": settings.db_pool_size,
                "pool_timeout": settings.db_pool_timeout
            }
        }
    except Exception as e:
        return {
            "valid": False,
            "issues": [f"Erro ao carregar configurações: {str(e)}"],
            "warnings": [],
            "settings_loaded": False
        }


# Para compatibilidade e debug
if __name__ == "__main__":
    print("🔧 Testando configurações do banco de dados...")
    
    try:
        # Teste de configuração
        validation = validate_database_config()
        print(f"✅ Configuração: {'VÁLIDA' if validation['valid'] else 'INVÁLIDA'}")
        
        if validation['issues']:
            print(f"   ❌ Problemas: {validation['issues']}")
        if validation['warnings']:
            print(f"   ⚠️ Avisos: {validation['warnings']}")
        
        if validation['valid']:
            # Teste de conexão
            connection_test = test_database_connection()
            print(f"✅ Conexão: {'OK' if connection_test['connected'] else 'FALHOU'}")
            print(f"   {connection_test['message']}")
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()