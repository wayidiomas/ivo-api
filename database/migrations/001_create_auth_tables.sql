-- Migração: Sistema de Autenticação IVO V2
-- Data: 2025-01-24
-- Descrição: Criar tabelas para autenticação com tokens seguros

-- =====================================================================
-- TABELA DE USUÁRIOS
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.ivo_users (
    id text NOT NULL DEFAULT ('user_'::text || lower(replace((gen_random_uuid())::text, '-'::text, '_'::text))),
    email text NOT NULL,
    phone text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true,
    metadata jsonb DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT ivo_users_pkey PRIMARY KEY (id),
    CONSTRAINT ivo_users_email_unique UNIQUE (email),
    CONSTRAINT ivo_users_email_check CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT ivo_users_phone_check CHECK (phone IS NULL OR length(phone) >= 10)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_users_email ON public.ivo_users(email) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.ivo_users(created_at DESC);

-- =====================================================================
-- TABELA DE TOKENS API (NÃO ACESSÍVEL - APENAS VALIDAÇÃO INTERNA)
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.ivo_api_tokens (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    token_ivo text NOT NULL,
    token_bearer text NOT NULL,
    user_id text,
    is_active boolean DEFAULT true,
    expires_at timestamp with time zone DEFAULT NULL, -- NULL = não expira
    scopes text[] DEFAULT ARRAY['v2_access'],
    rate_limit_config jsonb DEFAULT '{"requests_per_minute": 100, "requests_per_hour": 1000}',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_used_at timestamp with time zone,
    usage_count bigint DEFAULT 0,
    
    -- Constraints
    CONSTRAINT ivo_api_tokens_pkey PRIMARY KEY (id),
    CONSTRAINT ivo_api_tokens_token_ivo_unique UNIQUE (token_ivo),
    CONSTRAINT ivo_api_tokens_token_bearer_unique UNIQUE (token_bearer),
    CONSTRAINT fk_tokens_user FOREIGN KEY (user_id) REFERENCES public.ivo_users(id) ON DELETE CASCADE,
    CONSTRAINT ivo_api_tokens_scopes_check CHECK (array_length(scopes, 1) > 0)
);

-- Índices críticos para performance e segurança
CREATE INDEX IF NOT EXISTS idx_api_tokens_token_ivo ON public.ivo_api_tokens(token_ivo) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_api_tokens_bearer ON public.ivo_api_tokens(token_bearer) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_api_tokens_user ON public.ivo_api_tokens(user_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_api_tokens_last_used ON public.ivo_api_tokens(last_used_at DESC) WHERE is_active = true;

-- =====================================================================
-- TRIGGERS PARA AUDITORIA E MANUTENÇÃO
-- =====================================================================

-- Trigger para updated_at automático em ivo_users
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_ivo_users_updated_at
    BEFORE UPDATE ON public.ivo_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para updated_at automático em ivo_api_tokens
CREATE TRIGGER trigger_ivo_api_tokens_updated_at
    BEFORE UPDATE ON public.ivo_api_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- FUNÇÃO DE LIMPEZA DE TOKENS EXPIRADOS (OPCIONAL)
-- =====================================================================

CREATE OR REPLACE FUNCTION clean_expired_tokens()
RETURNS integer AS $$
DECLARE
    deleted_count integer;
BEGIN
    -- Limpar tokens expirados (apenas se expires_at não for NULL)
    DELETE FROM public.ivo_api_tokens 
    WHERE expires_at IS NOT NULL 
    AND expires_at < now() 
    AND is_active = false;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log da limpeza (inserir registro completo válido)
    INSERT INTO public.ivo_api_tokens (token_ivo, token_bearer, is_active, scopes, usage_count)
    VALUES ('cleanup_log_' || extract(epoch from now())::text, 'cleanup_log_bearer_' || deleted_count::text, false, ARRAY['cleanup'], deleted_count);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- POLÍTICAS DE SEGURANÇA (RLS - Row Level Security)
-- =====================================================================

-- Habilitar RLS na tabela de tokens para máxima segurança
ALTER TABLE public.ivo_api_tokens ENABLE ROW LEVEL SECURITY;

-- Política: Apenas aplicação pode acessar tokens
CREATE POLICY "api_tokens_app_only" ON public.ivo_api_tokens
    FOR ALL
    TO authenticated
    USING (true);

-- Política: Usuários podem ver apenas seus próprios dados
CREATE POLICY "users_own_data" ON public.ivo_users
    FOR ALL
    TO authenticated
    USING (true);

-- =====================================================================
-- COMENTÁRIOS PARA DOCUMENTAÇÃO
-- =====================================================================

COMMENT ON TABLE public.ivo_users IS 'Tabela de usuários do sistema IVO V2';
COMMENT ON COLUMN public.ivo_users.id IS 'ID único do usuário (user_xxx format)';
COMMENT ON COLUMN public.ivo_users.email IS 'Email único do usuário (obrigatório)';
COMMENT ON COLUMN public.ivo_users.phone IS 'Telefone do usuário (opcional)';
COMMENT ON COLUMN public.ivo_users.metadata IS 'Dados adicionais do usuário em JSON';

COMMENT ON TABLE public.ivo_api_tokens IS 'TABELA CRÍTICA - Tokens de API (NÃO ACESSÍVEL via endpoints)';
COMMENT ON COLUMN public.ivo_api_tokens.token_ivo IS 'Token IVO enviado no header api-key-ivo';
COMMENT ON COLUMN public.ivo_api_tokens.token_bearer IS 'Token Bearer retornado para uso na API V2';
COMMENT ON COLUMN public.ivo_api_tokens.rate_limit_config IS 'Configuração de rate limiting por token';
COMMENT ON COLUMN public.ivo_api_tokens.usage_count IS 'Contador de uso do token';

-- =====================================================================
-- DADOS INICIAIS DE TESTE (OPCIONAL - REMOVER EM PRODUÇÃO)
-- =====================================================================

-- Token de teste para desenvolvimento (REMOVER EM PRODUÇÃO)
INSERT INTO public.ivo_api_tokens (token_ivo, token_bearer, scopes, rate_limit_config) 
VALUES (
    'ivo_test_token_dev_only_remove_in_prod', 
    'bearer_test_dev_only_remove_in_prod',
    ARRAY['v2_access', 'admin'],
    '{"requests_per_minute": 1000, "requests_per_hour": 10000}'
) ON CONFLICT (token_ivo) DO NOTHING;

-- Log de criação das tabelas
DO $$
BEGIN
    RAISE NOTICE 'Tabelas de autenticação IVO V2 criadas com sucesso!';
    RAISE NOTICE 'ATENÇÃO: Tabela ivo_api_tokens é CRÍTICA - não expor via endpoints';
    RAISE NOTICE 'Token de teste criado: ivo_test_token_dev_only_remove_in_prod';
    RAISE NOTICE 'Execute SELECT * FROM ivo_api_tokens; para verificar o token de teste';
END $$;