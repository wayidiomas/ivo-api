"""Configuração dos modelos de IA - Atualizado Janeiro 2025 com GPT-5 e o3."""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# Importar do sistema principal de configurações
try:
    from config.settings import get_settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    print("⚠️ config.settings não disponível, usando fallback")

try:
    from config.logger_config import get_logger
    logger = get_logger("models_config")
except ImportError:
    import logging
    logger = logging.getLogger("models_config")


class OpenAISettings(BaseSettings):
    """Configurações do OpenAI - Modelos Janeiro 2025."""
    # ✅ CORRIGIDO: Usando apenas model_config (Pydantic v2)
    model_config = ConfigDict(
        extra="allow",
        env_file=".env",
        case_sensitive=False
    )
    
    # Campos principais com novos modelos 2025
    openai_api_key: str = ""
    
    # TIER 1: Tarefas Simples (Baixo Custo)
    openai_model_simple: str = "gpt-4o-mini"      # RAG, validações básicas
    openai_model_vision: str = "gpt-4o-mini"      # Análise de imagens (multimodal)
    
    # TIER 2: Tarefas Médias (Custo-Benefício) 
    openai_model_medium: str = "gpt-5-mini"       # Vocabulary, Sentences
    
    # TIER 3: Raciocínio Pedagógico
    openai_model_reasoning_lite: str = "o3-mini"  # Tips, Grammar
    
    # TIER 4: Tarefas Complexas
    openai_model_complex: str = "gpt-5"           # Unit generation (400K context)
    
    # TIER 5: Raciocínio Profundo
    openai_model_reasoning: str = "o3"            # Assessments, Q&A complexo
    
    # Modelo padrão e configurações gerais
    openai_model: str = "gpt-5-mini"              # Padrão/fallback
    openai_vision_model: str = "gpt-4o-mini"      # Mantido para compatibilidade
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7
    openai_timeout: int = 60
    openai_reasoning_effort: str = "medium"       # low, medium, high para o3


class ModelConfigs:
    """Gerenciador de configurações dos modelos com suporte a tiers."""
    
    def __init__(self):
        self.configs = {}
        self._load_configs()
    
    def _load_configs(self):
        """Carregar configurações do arquivo YAML."""
        try:
            config_path = Path("config/models.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.configs = yaml.safe_load(f)
                logger.info("✅ Configurações dos modelos carregadas do YAML (2025)")
            else:
                # Configurações padrão se arquivo não existir
                self.configs = self._get_default_configs()
                logger.info("⚙️ Usando configurações padrão 2025 (models.yaml não encontrado)")
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar YAML: {e}")
            self.configs = self._get_default_configs()
    
    def _get_default_configs(self) -> Dict[str, Any]:
        """Configurações padrão dos modelos - Janeiro 2025."""
        return {
            "openai": {
                "models": {
                    "simple": "gpt-4o-mini",
                    "vision": "gpt-4o-mini",
                    "medium": "gpt-5-mini",
                    "reasoning_lite": "o3-mini",
                    "complex": "gpt-5",
                    "reasoning": "o3"
                },
                "default_model": "gpt-5-mini",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 60,
                "max_retries": 3,
                "reasoning_config": {
                    "effort": "medium",
                    "streaming": True
                }
            },
            "content_configs": {
                # TIER 1 - Simples
                "rag_context": {
                    "model": "gpt-4o",  # Melhorado de gpt-4o-mini para prompt generation
                    "max_tokens": 2048,  # Aumentado para prompts mais complexos
                    "temperature": 0.3
                },
                "image_analysis": {
                    "model": "gpt-4o-mini",
                    "max_tokens": 1536,
                    "temperature": 0.5
                },
                
                # TIER 2 - Médio
                "ivo_vocab_generation": {
                    "model": "gpt-5-mini",
                    "max_tokens": 2048,
                    "temperature": 0.5
                },
                "ivo_sentences_generation": {
                    "model": "gpt-4o",  # Modelo eficiente e estável
                    "max_tokens": 1200,  # Reduzido para evitar truncamento
                    "temperature": 0.6
                },
                
                # TIER 3 - Raciocínio Pedagógico
                "ivo_tips_generation": {
                    "model": "o3-mini",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "reasoning_effort": "medium"
                },
                "ivo_grammar_generation": {
                    "model": "o3-mini",
                    "max_tokens": 2048,
                    "temperature": 0.5,
                    "reasoning_effort": "medium"
                },
                
                # TIER 4 - Complexo
                "unit_generation": {
                    "model": "gpt-5",
                    "max_tokens": 4096,
                    "temperature": 0.7,
                    "context_window": 400000
                },
                
                # TIER 5 - Raciocínio Profundo
                "ivo_assessments_generation": {
                    "model": "o3",
                    "max_tokens": 3072,
                    "temperature": 0.6,
                    "reasoning_effort": "high"
                },
                "ivo_qa_generation": {
                    "model": "gpt-5-mini",  # Mudado de o3-mini para gpt-5-mini (400K context, 128K output)
                    "max_tokens": 4096,  # Aumentado significativamente - gpt-5-mini suporta 128K output
                    "temperature": 0.6
                    # reasoning_effort removido - não aplicável ao gpt-5-mini
                },
                
                # Legacy (compatibilidade)
                "vocab_generation": {
                    "model": "gpt-5-mini",
                    "max_tokens": 2048,
                    "temperature": 0.5
                },
                "teoria_generation": {
                    "model": "gpt-5-mini",
                    "max_tokens": 3072,
                    "temperature": 0.6
                },
                "frases_generation": {
                    "model": "gpt-5-mini",
                    "max_tokens": 2048,
                    "temperature": 0.7
                },
                "gramatica_generation": {
                    "model": "o3-mini",
                    "max_tokens": 3072,
                    "temperature": 0.5
                },
                "tips_generation": {
                    "model": "o3-mini",
                    "max_tokens": 2048,
                    "temperature": 0.8
                },
                "exercicios_generation": {
                    "model": "o3",
                    "max_tokens": 4096,
                    "temperature": 0.6
                }
            }
        }
    
    def get_model_for_task(self, task_type: str) -> str:
        """Obter o modelo apropriado para um tipo de tarefa."""
        task_model_mapping = {
            # TIER 1
            "rag": "simple",
            "context": "simple",
            "image": "vision",
            
            # TIER 2
            "vocabulary": "medium",
            "sentences": "medium",
            
            # TIER 3
            "tips": "reasoning_lite",
            "grammar": "reasoning_lite",
            
            # TIER 4
            "unit": "complex",
            
            # TIER 5
            "assessments": "reasoning",
            
            # TIER 2 - Q&A movido para gpt-5-mini (melhor para structured output)
            "qa": "medium"  # Q&A usa gpt-5-mini para evitar reasoning_tokens
        }
        
        model_tier = task_model_mapping.get(task_type, "medium")
        models = self.configs.get("openai", {}).get("models", {})
        return models.get(model_tier, "gpt-5-mini")
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Obter configurações do OpenAI com modelos 2025."""
        openai_config = self.configs.get("openai", {})
        models = openai_config.get("models", {})
        
        # ✅ PRIORIDADE 1: Usar settings.py se disponível
        if SETTINGS_AVAILABLE:
            try:
                settings = get_settings()
                return {
                    "api_key": settings.openai_api_key or "",
                    "model": getattr(settings, 'openai_model', models.get("medium", "gpt-5-mini")),
                    "vision_model": getattr(settings, 'openai_model_vision', models.get("vision", "gpt-4o-mini")),
                    "models": {
                        "simple": getattr(settings, 'openai_model_simple', models.get("simple", "gpt-4o-mini")),
                        "vision": getattr(settings, 'openai_model_vision', models.get("vision", "gpt-4o-mini")),
                        "medium": getattr(settings, 'openai_model_medium', models.get("medium", "gpt-5-mini")),
                        "reasoning_lite": getattr(settings, 'openai_model_reasoning_lite', models.get("reasoning_lite", "o3-mini")),
                        "complex": getattr(settings, 'openai_model_complex', models.get("complex", "gpt-5")),
                        "reasoning": getattr(settings, 'openai_model_reasoning', models.get("reasoning", "o3"))
                    },
                    "max_tokens": settings.openai_max_tokens,
                    "temperature": settings.openai_temperature,
                    "timeout": openai_config.get("timeout", 60),
                    "max_retries": openai_config.get("max_retries", 3),
                    "reasoning_config": openai_config.get("reasoning_config", {}),
                    "content_configs": self.configs.get("content_configs", {})
                }
            except Exception as e:
                logger.warning(f"⚠️ Erro ao usar settings.py: {e}, usando fallback")
        
        # ✅ PRIORIDADE 2: Usar OpenAISettings diretamente
        try:
            env_settings = OpenAISettings()
            return {
                "api_key": env_settings.openai_api_key,
                "model": env_settings.openai_model,
                "vision_model": env_settings.openai_vision_model,
                "models": {
                    "simple": env_settings.openai_model_simple,
                    "vision": env_settings.openai_model_vision,
                    "medium": env_settings.openai_model_medium,
                    "reasoning_lite": env_settings.openai_model_reasoning_lite,
                    "complex": env_settings.openai_model_complex,
                    "reasoning": env_settings.openai_model_reasoning
                },
                "max_tokens": env_settings.openai_max_tokens,
                "temperature": env_settings.openai_temperature,
                "timeout": env_settings.openai_timeout,
                "reasoning_effort": env_settings.openai_reasoning_effort,
                "max_retries": openai_config.get("max_retries", 3),
                "reasoning_config": openai_config.get("reasoning_config", {}),
                "content_configs": self.configs.get("content_configs", {})
            }
        except Exception as e:
            logger.warning(f"⚠️ Erro ao usar OpenAISettings: {e}, usando fallback final")
        
        # ✅ PRIORIDADE 3: Fallback direto do .env + YAML
        return {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "model": os.getenv("OPENAI_MODEL", models.get("medium", "gpt-5-mini")),
            "vision_model": os.getenv("OPENAI_MODEL_VISION", models.get("vision", "gpt-4o-mini")),
            "models": {
                "simple": os.getenv("OPENAI_MODEL_SIMPLE", models.get("simple", "gpt-4o-mini")),
                "vision": os.getenv("OPENAI_MODEL_VISION", models.get("vision", "gpt-4o-mini")),
                "medium": os.getenv("OPENAI_MODEL_MEDIUM", models.get("medium", "gpt-5-mini")),
                "reasoning_lite": os.getenv("OPENAI_MODEL_REASONING_LITE", models.get("reasoning_lite", "o3-mini")),
                "complex": os.getenv("OPENAI_MODEL_COMPLEX", models.get("complex", "gpt-5")),
                "reasoning": os.getenv("OPENAI_MODEL_REASONING", models.get("reasoning", "o3"))
            },
            "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", openai_config.get("max_tokens", 4096))),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", openai_config.get("temperature", 0.7))),
            "timeout": int(os.getenv("OPENAI_TIMEOUT", openai_config.get("timeout", 60))),
            "reasoning_effort": os.getenv("OPENAI_REASONING_EFFORT", "medium"),
            "max_retries": openai_config.get("max_retries", 3),
            "reasoning_config": openai_config.get("reasoning_config", {}),
            "content_configs": self.configs.get("content_configs", {})
        }
    
    def get_content_config(self, content_type: str) -> Dict[str, Any]:
        """Obter configuração específica para tipo de conteúdo."""
        content_configs = self.configs.get("content_configs", {})
        base_config = content_configs.get(content_type, {})
        
        # Mesclar com configurações globais do OpenAI
        openai_config = self.get_openai_config()
        
        # Se o content_type tem um modelo específico no YAML, usar
        specific_model = base_config.get("model")
        if not specific_model:
            # Mapear content_type para task_type e obter modelo apropriado
            task_mapping = {
                "ivo_vocab_generation": "vocabulary",
                "ivo_sentences_generation": "sentences",
                "ivo_tips_generation": "tips",
                "ivo_grammar_generation": "grammar",
                "ivo_assessments_generation": "assessments",
                "ivo_qa_generation": "qa",
                "image_analysis": "image",
                "rag_context": "rag"
            }
            task_type = task_mapping.get(content_type, "medium")
            specific_model = self.get_model_for_task(task_type)
        
        # Retornar configuração completa
        return {
            "model": specific_model,
            "max_tokens": base_config.get("max_tokens", openai_config.get("max_tokens")),
            "temperature": base_config.get("temperature", openai_config.get("temperature")),
            "api_key": openai_config.get("api_key"),
            "timeout": base_config.get("timeout", openai_config.get("timeout")),
            "reasoning_effort": base_config.get("reasoning_effort", openai_config.get("reasoning_effort", "medium")),
            **base_config  # Incluir configurações específicas
        }


# ✅ Instância global segura
try:
    _model_configs = ModelConfigs()
    logger.info("✅ ModelConfigs inicializado com modelos 2025")
except Exception as e:
    logger.error(f"❌ Erro ao inicializar ModelConfigs: {e}")
    _model_configs = None


def get_openai_config() -> Dict[str, Any]:
    """
    Função para obter configurações do OpenAI com modelos 2025.
    
    Returns:
        Dict: Configurações completas do OpenAI
    """
    if _model_configs:
        return _model_configs.get_openai_config()
    
    # Fallback extremo se tudo falhar
    logger.warning("⚠️ Usando fallback extremo para OpenAI config")
    return {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        "vision_model": os.getenv("OPENAI_MODEL_VISION", "gpt-4o-mini"),
        "models": {
            "simple": "gpt-4o-mini",
            "vision": "gpt-4o-mini",
            "medium": "gpt-5-mini",
            "reasoning_lite": "o3-mini",
            "complex": "gpt-5",
            "reasoning": "o3"
        },
        "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        "timeout": int(os.getenv("OPENAI_TIMEOUT", "60")),
        "reasoning_effort": "medium",
        "max_retries": 3,
        "content_configs": {}
    }


def get_model_for_task(task_type: str) -> str:
    """
    Obter o modelo apropriado para um tipo de tarefa.
    
    Args:
        task_type: Tipo de tarefa (rag, vocabulary, assessments, etc.)
        
    Returns:
        str: Nome do modelo apropriado
    """
    if _model_configs:
        return _model_configs.get_model_for_task(task_type)
    
    # Fallback
    default_mapping = {
        "rag": "gpt-4o-mini",
        "image": "gpt-4o-mini",
        "vocabulary": "gpt-5-mini",
        "sentences": "gpt-5-mini",
        "tips": "o3-mini",
        "grammar": "o3-mini",
        "unit": "gpt-5",
        "assessments": "o3",
        "qa": "gpt-5-mini"  # Mudado de o3-mini para gpt-5-mini
    }
    return default_mapping.get(task_type, "gpt-5-mini")


def load_model_configs() -> Dict[str, Any]:
    """
    Função para carregar todas as configurações dos modelos.
    
    Returns:
        Dict: Todas as configurações
    """
    if _model_configs:
        return _model_configs.configs
    return {}


def get_content_config(content_type: str) -> Dict[str, Any]:
    """
    Obter configuração para um tipo específico de conteúdo.
    
    Args:
        content_type: Tipo de conteúdo (ivo_vocab_generation, ivo_tips_generation, etc.)
        
    Returns:
        Dict: Configurações específicas do tipo
    """
    if _model_configs:
        return _model_configs.get_content_config(content_type)
    
    # Fallback
    base_config = get_openai_config()
    return {
        "model": base_config.get("model"),
        "api_key": base_config.get("api_key"),
        "max_tokens": 2048,  # Default conservador
        "temperature": 0.7,
        "timeout": base_config.get("timeout", 60)
    }


def reload_configs():
    """Recarregar configurações dos modelos."""
    global _model_configs
    try:
        _model_configs = ModelConfigs()
        logger.info("🔄 Configurações dos modelos 2025 recarregadas")
    except Exception as e:
        logger.error(f"❌ Erro ao recarregar configurações: {e}")


def validate_openai_config() -> Dict[str, Any]:
    """
    Validar se as configurações do OpenAI estão corretas.
    
    Returns:
        Dict: Resultado da validação
    """
    try:
        config = get_openai_config()
        issues = []
        warnings = []
        
        # Verificar API key
        if not config.get("api_key"):
            issues.append("OPENAI_API_KEY não configurada")
        elif not config.get("api_key").startswith("sk-"):
            warnings.append("OPENAI_API_KEY não parece válida (não inicia com 'sk-')")
        
        # Verificar modelos 2025
        models = config.get("models", {})
        expected_models = ["simple", "vision", "medium", "reasoning_lite", "complex", "reasoning"]
        for model_tier in expected_models:
            if model_tier not in models:
                warnings.append(f"Modelo '{model_tier}' não configurado")
        
        # Verificar configurações básicas
        required_fields = ["model", "max_tokens", "temperature"]
        for field in required_fields:
            if field not in config:
                issues.append(f"Campo obrigatório '{field}' não encontrado")
        
        # Verificar valores numéricos
        if config.get("max_tokens", 0) <= 0:
            issues.append("max_tokens deve ser maior que 0")
        
        if not (0.0 <= config.get("temperature", -1) <= 2.0):
            issues.append("temperature deve estar entre 0.0 e 2.0")
        
        is_valid = len(issues) == 0
        
        if is_valid:
            logger.info("✅ Configurações do OpenAI 2025 válidas")
        else:
            logger.error(f"❌ Problemas encontrados: {issues}")
        
        return {
            "valid": is_valid,
            "issues": issues,
            "warnings": warnings,
            "config": config,
            "models_configured": models
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao validar configurações: {e}")
        return {
            "valid": False,
            "issues": [f"Erro de validação: {str(e)}"],
            "warnings": [],
            "config": {}
        }


# Exemplo de uso e teste
if __name__ == "__main__":
    print("🔧 Testando configurações dos modelos 2025...")
    
    try:
        # Testar configuração do OpenAI
        config = get_openai_config()
        print(f"✅ API Key: {'***' + config['api_key'][-4:] if config['api_key'] else 'NÃO CONFIGURADA'}")
        print(f"✅ Modelo Padrão: {config['model']}")
        print(f"✅ Vision Model: {config['vision_model']}")
        print("\n📊 Modelos por Tier:")
        for tier, model in config.get('models', {}).items():
            print(f"   • {tier}: {model}")
        print(f"\n⚙️ Max Tokens: {config['max_tokens']}")
        print(f"⚙️ Temperature: {config['temperature']}")
        print(f"⚙️ Timeout: {config['timeout']}")
        print(f"⚙️ Reasoning Effort: {config.get('reasoning_effort', 'medium')}")
        
        # Testar mapeamento de tarefas
        print("\n🎯 Modelos por Tarefa:")
        tasks = ["rag", "vocabulary", "tips", "assessments", "unit"]
        for task in tasks:
            model = get_model_for_task(task)
            print(f"   • {task}: {model}")
        
        # Testar configuração de conteúdo específico
        vocab_config = get_content_config("ivo_vocab_generation")
        print(f"\n📝 Vocab Config: Model={vocab_config.get('model')}, Tokens={vocab_config.get('max_tokens')}")
        
        # Validar configurações
        validation = validate_openai_config()
        print(f"\n🔍 Validação: {'✅ VÁLIDO' if validation['valid'] else '❌ INVÁLIDO'}")
        if validation['issues']:
            print(f"   Problemas: {validation['issues']}")
        if validation['warnings']:
            print(f"   Avisos: {validation['warnings']}")
            
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()