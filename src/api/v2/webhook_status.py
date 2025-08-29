# src/api/v2/webhook_status.py
"""
Endpoints para consultar status de tarefas assíncronas.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import logging

from src.services.webhook_service import webhook_service
from src.core.unit_models import SuccessResponse

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

@router.get("/tasks/{task_id}/status", response_model=SuccessResponse)
async def get_task_status(task_id: str):
    """
    Obter status de uma tarefa assíncrona específica.
    
    Args:
        task_id: ID da tarefa
        
    Returns:
        Status da tarefa
    """
    try:
        logger.info(f"Consultando status da tarefa: {task_id}")
        
        task_info = webhook_service.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(
                status_code=404,
                detail=f"Tarefa {task_id} não encontrada"
            )
        
        # Preparar resposta com base no status
        status = task_info.get("status")
        
        response_data = {
            "task_id": task_id,
            "status": status,
            "webhook_url": task_info.get("webhook_url"),
            "started_at": task_info.get("started_at").isoformat() if task_info.get("started_at") else None,
            "metadata": task_info.get("metadata", {})
        }
        
        # Adicionar informações específicas por status
        if status == "completed":
            response_data.update({
                "success": True,
                "result": task_info.get("result"),
                "processing_time": task_info.get("processing_time"),
                "completed_at": task_info.get("completed_at").isoformat() if task_info.get("completed_at") else None
            })
        elif status == "failed":
            response_data.update({
                "success": False,
                "error": task_info.get("error"),
                "processing_time": task_info.get("processing_time"),
                "failed_at": task_info.get("failed_at").isoformat() if task_info.get("failed_at") else None
            })
        elif status in ["running", "processing"]:
            response_data.update({
                "success": None,
                "message": f"Tarefa em andamento (status: {status})"
            })
        
        message_map = {
            "running": "Tarefa em execução",
            "processing": "Tarefa sendo processada", 
            "completed": "Tarefa completada com sucesso",
            "failed": "Tarefa falhou"
        }
        
        return SuccessResponse(
            data=response_data,
            message=message_map.get(status, f"Status: {status}")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar status da tarefa {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@router.get("/tasks/active", response_model=SuccessResponse)
async def list_active_tasks():
    """
    Listar todas as tarefas ativas (em execução).
    
    Returns:
        Lista de tarefas ativas
    """
    try:
        logger.info("Listando tarefas ativas")
        
        active_tasks = webhook_service.list_active_tasks()
        
        # Formatar dados para resposta
        formatted_tasks = {}
        for task_id, task_info in active_tasks.items():
            formatted_tasks[task_id] = {
                "task_id": task_id,
                "status": task_info.get("status"),
                "webhook_url": task_info.get("webhook_url"),
                "started_at": task_info.get("started_at").isoformat() if task_info.get("started_at") else None,
                "endpoint": task_info.get("metadata", {}).get("endpoint"),
                "unit_id": task_info.get("metadata", {}).get("unit_id")
            }
        
        return SuccessResponse(
            data={
                "active_tasks": formatted_tasks,
                "total_active": len(formatted_tasks)
            },
            message=f"Encontradas {len(formatted_tasks)} tarefas ativas"
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar tarefas ativas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@router.get("/info", response_model=SuccessResponse)
async def get_webhook_info():
    """
    Obter informações sobre o sistema de webhooks.
    
    Returns:
        Informações do sistema de webhooks
    """
    try:
        return SuccessResponse(
            data={
                "webhook_system": {
                    "enabled": True,
                    "supported_endpoints": [
                        "POST /api/v2/units/{unit_id}/vocabulary",
                        "POST /api/v2/units/{unit_id}/sentences", 
                        "POST /api/v2/units/{unit_id}/grammar",
                        "POST /api/v2/units/{unit_id}/tips",
                        "POST /api/v2/units/{unit_id}/assessments",
                        "POST /api/v2/units/{unit_id}/qa"
                    ],
                    "async_parameter": "webhook_url",
                    "timeout": "5 minutos",
                    "retry_policy": "3 tentativas com backoff"
                },
                "usage": {
                    "sync_processing": "Não enviar 'webhook_url' no payload",
                    "async_processing": "Incluir 'webhook_url' no payload",
                    "webhook_url_requirements": [
                        "Deve ser uma URL HTTP/HTTPS válida",
                        "Não pode ser localhost ou IP privado",
                        "Máximo 2048 caracteres"
                    ]
                },
                "webhook_payload_format": {
                    "success_payload": {
                        "task_id": "string - ID da tarefa",
                        "status": "completed",
                        "success": True,
                        "result": "object - resultado completo do endpoint",
                        "processing_time": "number - tempo em segundos",
                        "completed_at": "string - ISO datetime",
                        "metadata": "object - metadados da requisição"
                    },
                    "error_payload": {
                        "task_id": "string - ID da tarefa",
                        "status": "failed",
                        "success": False,
                        "error": "string - descrição do erro",
                        "processing_time": "number - tempo em segundos",
                        "failed_at": "string - ISO datetime",
                        "metadata": "object - metadados da requisição"
                    }
                },
                "status_endpoints": {
                    "check_task": "GET /api/v2/webhooks/tasks/{task_id}/status",
                    "list_active": "GET /api/v2/webhooks/tasks/active",
                    "system_info": "GET /api/v2/webhooks/info"
                }
            },
            message="Informações do sistema de webhooks do IVO API v2"
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter informações de webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )