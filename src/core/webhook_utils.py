# src/core/webhook_utils.py
"""
Utilitários para validação e processamento de webhooks.
"""

import re
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def validate_webhook_url(webhook_url: str) -> Tuple[bool, Optional[str]]:
    """
    Valida se a URL do webhook é válida e segura.
    
    Args:
        webhook_url: URL do webhook a ser validada
        
    Returns:
        Tuple[bool, Optional[str]]: (é_válida, mensagem_de_erro)
    """
    if not webhook_url or not isinstance(webhook_url, str):
        return False, "webhook_url deve ser uma string não vazia"
    
    # Validar formato básico da URL
    try:
        parsed_url = urlparse(webhook_url)
    except Exception as e:
        return False, f"URL inválida: {str(e)}"
    
    # Verificar esquema
    if parsed_url.scheme not in ['http', 'https']:
        return False, "webhook_url deve usar protocolo HTTP ou HTTPS"
    
    # Verificar se tem hostname
    if not parsed_url.netloc:
        return False, "webhook_url deve ter um hostname válido"
    
    # Verificações básicas de segurança (removido bloqueio de localhost)
    hostname = parsed_url.hostname
    if hostname:
        # Apenas verificar se não é um hostname obviamente inválido
        if hostname.strip() == "":
            return False, "hostname não pode estar vazio"
    
    # Verificar comprimento razoável
    if len(webhook_url) > 2048:
        return False, "webhook_url muito longa (máximo 2048 caracteres)"
    
    return True, None

def should_process_async(payload: Dict[str, Any]) -> bool:
    """
    Determina se uma requisição deve ser processada assíncronamente.
    
    Args:
        payload: Payload da requisição
        
    Returns:
        bool: True se deve processar assíncronamente
    """
    # Verificar se tem webhook_url no payload
    webhook_url = payload.get("webhook_url")
    
    if not webhook_url:
        return False
    
    # Validar webhook_url
    is_valid, error = validate_webhook_url(webhook_url)
    if not is_valid:
        logger.warning(f"webhook_url inválida: {error}")
        return False
    
    return True

def extract_webhook_metadata(
    endpoint_name: str,
    unit_id: str, 
    payload: Dict[str, Any],
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extrai metadados para incluir no webhook.
    
    Args:
        endpoint_name: Nome do endpoint sendo processado
        unit_id: ID da unidade
        payload: Payload original da requisição
        additional_data: Dados adicionais
        
    Returns:
        Dict com metadados
    """
    metadata = {
        "endpoint": endpoint_name,
        "unit_id": unit_id,
        "request_data": {
            key: value for key, value in payload.items() 
            if key != "webhook_url"  # Não incluir webhook_url no metadata
        }
    }
    
    if additional_data:
        metadata.update(additional_data)
    
    return metadata

class WebhookResponse:
    """Classe para padronizar respostas de webhook."""
    
    @staticmethod
    def async_accepted(task_id: str, webhook_url: str, endpoint_name: str) -> Dict[str, Any]:
        """Resposta para processamento assíncrono aceito."""
        return {
            "message": f"Requisição aceita para processamento assíncrono",
            "async_processing": True,
            "task_id": task_id,
            "webhook_url": webhook_url,
            "endpoint": endpoint_name,
            "status": "processing",
            "estimated_completion": "1-5 minutos",
            "webhook_info": {
                "format": "POST request com JSON",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Task-Id": task_id,
                    "X-Webhook-Source": "ivo-api"
                },
                "payload_structure": {
                    "task_id": "string",
                    "status": "completed | failed",
                    "success": "boolean",
                    "result": "object (se success=true)",
                    "error": "string (se success=false)",
                    "processing_time": "number (segundos)",
                    "completed_at": "ISO datetime",
                    "metadata": "object"
                }
            }
        }

def create_async_wrapper(sync_func, endpoint_name: str):
    """
    Cria um wrapper que pode processar síncronamente ou assíncronamente.
    
    Args:
        sync_func: Função original do endpoint
        endpoint_name: Nome do endpoint para logging
        
    Returns:
        Função wrapper
    """
    async def wrapper(
        unit_id: str,
        request_payload,
        request,
        *args,
        **kwargs
    ):
        from src.services.webhook_service import webhook_service
        
        # Extrair dados do payload
        if hasattr(request_payload, 'model_dump'):
            payload_dict = request_payload.model_dump()
        elif hasattr(request_payload, 'dict'):
            payload_dict = request_payload.dict()
        else:
            payload_dict = dict(request_payload) if request_payload else {}
        
        # Verificar se deve processar assíncronamente
        if should_process_async(payload_dict):
            webhook_url = payload_dict["webhook_url"]
            
            # Gerar task ID
            task_id = webhook_service.generate_task_id(f"{endpoint_name}")
            
            # Extrair metadados
            metadata = extract_webhook_metadata(endpoint_name, unit_id, payload_dict)
            
            # Preparar argumentos para função original (sem webhook_url)
            clean_payload_dict = {k: v for k, v in payload_dict.items() if k != "webhook_url"}
            
            # Recriar objeto de request sem webhook_url se necessário
            if hasattr(request_payload, 'model_copy') or hasattr(request_payload, 'copy'):
                try:
                    # Para Pydantic v2
                    if hasattr(request_payload, 'model_copy'):
                        clean_request_payload = request_payload.model_copy(update={"webhook_url": None}, exclude={"webhook_url"})
                    else:
                        # Para Pydantic v1
                        clean_request_payload = request_payload.copy(update={"webhook_url": None}, exclude={"webhook_url"})
                except:
                    # Se falhar, usar payload original
                    clean_request_payload = request_payload
            else:
                clean_request_payload = request_payload
            
            # Executar tarefa assíncronamente
            await webhook_service.execute_async_task(
                task_id=task_id,
                webhook_url=webhook_url,
                task_func=sync_func,
                task_args=(unit_id, clean_request_payload, request) + args,
                task_kwargs=kwargs,
                metadata=metadata
            )
            
            # Retornar resposta de aceitação
            return WebhookResponse.async_accepted(task_id, webhook_url, endpoint_name)
        
        else:
            # Processar síncronamente (comportamento original)
            return await sync_func(unit_id, request_payload, request, *args, **kwargs)
    
    return wrapper