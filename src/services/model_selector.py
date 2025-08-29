"""
Model Selector - Sistema centralizado para seleção de modelos 2025.
Garante que cada serviço use o modelo correto baseado na complexidade da tarefa.
"""

from typing import Dict, Any, Optional
from config.models import get_content_config, get_openai_config
import logging

logger = logging.getLogger(__name__)

# Mapeamento de serviços para tipos de conteúdo
SERVICE_TO_CONTENT_TYPE = {
    # TIER 1 - Simples (gpt-4o-mini)
    "image_analysis": "image_analysis",
    "rag_context": "rag_context",
    "prompt_generator": "rag_context",  # Usa gpt-4o para melhor qualidade de prompts
    "l1_interference": "ivo_grammar_generation",   # Análise linguística contrastiva complexa
    
    # TIER 2 - Médio (gpt-5-mini)
    "vocabulary_generator": "ivo_vocab_generation",
    "sentences_generator": "ivo_sentences_generation",
    
    # TIER 3 - Raciocínio Pedagógico (o3-mini)
    "tips_generator": "ivo_tips_generation",
    "grammar_generator": "ivo_grammar_generation",
    
    # TIER 4 - Complexo (gpt-5)
    "unit_generator": "unit_generation",
    "aim_detector": "unit_generation",  # Análise complexa de objetivos
    
    # TIER 5 - Raciocínio Profundo (o3/o3-mini)
    "assessment_selector": "ivo_assessments_generation",
    
    # TIER 3 - Q&A movido para o3-mini (reasoning controlado para Q&A)
    "qa_generator": "ivo_qa_generation"
}


def get_model_for_service(service_name: str) -> Dict[str, Any]:
    """
    Obter configuração completa do modelo para um serviço específico.
    
    Args:
        service_name: Nome do serviço (ex: "grammar_generator", "vocabulary_generator")
        
    Returns:
        Dict com model, temperature, max_tokens, etc.
    """
    try:
        # Identificar o tipo de conteúdo baseado no serviço
        content_type = SERVICE_TO_CONTENT_TYPE.get(service_name)
        
        if not content_type:
            logger.warning(f"⚠️ Serviço '{service_name}' não mapeado, usando configuração padrão")
            # Fallback para configuração padrão
            return get_openai_config()
        
        # Obter configuração específica do content_type
        config = get_content_config(content_type)
        
        # Log informativo
        model = config.get("model", "unknown")
        logger.info(f"✅ Serviço '{service_name}' usando modelo '{model}' (content_type: {content_type})")
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter modelo para '{service_name}': {e}")
        # Fallback seguro
        return get_openai_config()


def get_llm_config_for_service(service_name: str) -> Dict[str, Any]:
    """
    Obter configuração pronta para ChatOpenAI baseada no serviço.
    
    Args:
        service_name: Nome do serviço
        
    Returns:
        Dict com parâmetros prontos para ChatOpenAI
    """
    config = get_model_for_service(service_name)
    
    # Preparar configuração para LangChain ChatOpenAI
    llm_config = {
        "model": config.get("model", "gpt-4o"),
        "temperature": config.get("temperature", 0.7),
        "max_tokens": config.get("max_tokens", 2048),
        "api_key": config.get("api_key"),
        "timeout": config.get("timeout", 300),  # 5 minutos para modelos 2025
        "max_retries": config.get("max_retries", 3)
    }
    
    # Adicionar configurações especiais para modelos o3 (detecção precisa)
    model_name = llm_config.get("model", "").lower()
    if model_name in ["o3", "o3-mini"]:  # ✅ Detecção exata, não substring
        reasoning_effort = config.get("reasoning_effort", "medium")
        # TODO: reasoning_effort será reativado quando LangChain suportar nativamente
        # llm_config["reasoning_effort"] = reasoning_effort  # Parâmetro direto quando suportado
        
        # Remover temperature para modelos o3 (não suportado)
        llm_config.pop("temperature", None)
        logger.info(f"🧠 Modelo o3 detectado: {model_name}, reasoning_effort temporariamente desabilitado (aguardando suporte LangChain)")
    
    return llm_config


def log_model_selection(service_name: str, model: str, tier: Optional[str] = None):
    """
    Logar a seleção de modelo para auditoria.
    
    Args:
        service_name: Nome do serviço
        model: Modelo selecionado
        tier: Tier do modelo (opcional)
    """
    tier_info = f" (Tier: {tier})" if tier else ""
    logger.info(f"🎯 Model Selection: {service_name} → {model}{tier_info}")


# Função helper para identificar o tier de um modelo
def get_model_tier(model: str) -> str:
    """
    Identificar o tier de complexidade de um modelo.
    
    Args:
        model: Nome do modelo
        
    Returns:
        str: Tier do modelo (1-5)
    """
    model_lower = model.lower()
    
    if "gpt-4o-mini" in model_lower:
        return "TIER-1 (Simples)"
    elif "gpt-5-mini" in model_lower or "gpt-5-nano" in model_lower:
        return "TIER-2 (Médio)"
    elif "o3-mini" in model_lower:
        return "TIER-3 (Raciocínio Pedagógico)"
    elif "gpt-5" in model_lower and "mini" not in model_lower:
        return "TIER-4 (Complexo)"
    elif "o3" in model_lower and "mini" not in model_lower:
        return "TIER-5 (Raciocínio Profundo)"
    else:
        return "TIER-? (Desconhecido)"


# Exemplo de uso
if __name__ == "__main__":
    print("🔍 Testando Model Selector para todos os serviços...")
    print("=" * 60)
    
    # Testar todos os serviços mapeados
    for service_name in SERVICE_TO_CONTENT_TYPE.keys():
        config = get_model_for_service(service_name)
        model = config.get("model", "unknown")
        tier = get_model_tier(model)
        
        print(f"\n📦 Serviço: {service_name}")
        print(f"   • Modelo: {model}")
        print(f"   • Tier: {tier}")
        print(f"   • Temperature: {config.get('temperature', 'N/A')}")
        print(f"   • Max Tokens: {config.get('max_tokens', 'N/A')}")
        
        if "o3" in model:
            print(f"   • Reasoning Effort: {config.get('reasoning_effort', 'medium')}")
    
    print("\n" + "=" * 60)
    print("✅ Model Selector configurado com modelos 2025!")