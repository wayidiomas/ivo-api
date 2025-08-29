# src/services/webhook_service.py
"""
Serviço de webhooks para processamento assíncrono de endpoints de IA.
Permite que operações demoradas sejam executadas em background.
"""

import asyncio
import logging
import time
import httpx
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json
import uuid

logger = logging.getLogger(__name__)

class WebhookService:
    """Serviço para gerenciar webhooks e processamento assíncrono."""
    
    def __init__(self):
        self._background_tasks: Dict[str, Dict[str, Any]] = {}
        self.timeout = 300  # 5 minutos timeout para webhooks
        
    async def execute_async_task(
        self,
        task_id: str,
        webhook_url: str,
        task_func: Callable,
        task_args: tuple,
        task_kwargs: dict,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Executa uma tarefa de forma assíncrona e envia resultado via webhook.
        
        Args:
            task_id: ID único da tarefa
            webhook_url: URL para enviar o resultado
            task_func: Função a ser executada
            task_args: Argumentos posicionais para a função
            task_kwargs: Argumentos nomeados para a função
            metadata: Metadados adicionais
            
        Returns:
            task_id da tarefa em execução
        """
        logger.info(f"Iniciando tarefa assíncrona: {task_id}")
        
        # Registrar tarefa
        self._background_tasks[task_id] = {
            "status": "running",
            "webhook_url": webhook_url,
            "started_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        # Executar tarefa em background
        asyncio.create_task(self._run_background_task(
            task_id, webhook_url, task_func, task_args, task_kwargs, metadata
        ))
        
        return task_id
    
    async def _run_background_task(
        self,
        task_id: str,
        webhook_url: str,
        task_func: Callable,
        task_args: tuple,
        task_kwargs: dict,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Executa a tarefa em background e envia resultado via webhook."""
        start_time = time.time()
        
        try:
            # Atualizar status
            self._background_tasks[task_id]["status"] = "processing"
            
            # Executar função
            logger.info(f"Executando função para tarefa: {task_id}")
            result = await task_func(*task_args, **task_kwargs)
            
            processing_time = time.time() - start_time
            logger.info(f"Tarefa {task_id} completada em {processing_time:.2f}s")
            
            # Preparar payload de sucesso
            webhook_payload = {
                "task_id": task_id,
                "status": "completed",
                "success": True,
                "result": result,
                "processing_time": processing_time,
                "completed_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Atualizar status local
            self._background_tasks[task_id].update({
                "status": "completed",
                "result": result,
                "processing_time": processing_time,
                "completed_at": datetime.utcnow()
            })
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Erro na tarefa {task_id}: {str(e)}")
            
            # Preparar payload de erro
            webhook_payload = {
                "task_id": task_id,
                "status": "failed",
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
                "failed_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Atualizar status local
            self._background_tasks[task_id].update({
                "status": "failed",
                "error": str(e),
                "processing_time": processing_time,
                "failed_at": datetime.utcnow()
            })
        
        # Enviar webhook
        await self._send_webhook(webhook_url, webhook_payload, task_id)
        
        # Limpar tarefa após um tempo (evitar memory leak)
        asyncio.create_task(self._cleanup_task(task_id, delay=3600))  # 1 hora
    
    async def _send_webhook(self, webhook_url: str, payload: Dict[str, Any], task_id: str):
        """Envia o resultado via webhook com retry."""
        max_retries = 3
        retry_delay = 2  # segundos
        
        headers = {
            "Content-Type": "application/json",
            "X-Task-Id": task_id,
            "X-Webhook-Source": "ivo-api"
        }
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers=headers
                    )
                    
                    if response.status_code >= 200 and response.status_code < 300:
                        logger.info(f"Webhook enviado com sucesso para tarefa {task_id}: {response.status_code}")
                        return
                    else:
                        logger.warning(f"Webhook retornou status {response.status_code} para tarefa {task_id}")
                        
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} de envio do webhook falhou para tarefa {task_id}: {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
        
        logger.error(f"Falha ao enviar webhook após {max_retries} tentativas para tarefa {task_id}")
    
    async def _cleanup_task(self, task_id: str, delay: int = 3600):
        """Remove tarefa da memória após delay."""
        await asyncio.sleep(delay)
        if task_id in self._background_tasks:
            del self._background_tasks[task_id]
            logger.info(f"Tarefa {task_id} removida da memória")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtém status de uma tarefa."""
        return self._background_tasks.get(task_id)
    
    def list_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Lista todas as tarefas ativas."""
        return {
            task_id: task_info 
            for task_id, task_info in self._background_tasks.items()
            if task_info.get("status") in ["running", "processing"]
        }
    
    @staticmethod
    def generate_task_id(prefix: str = "task") -> str:
        """Gera um ID único para tarefa."""
        timestamp = int(time.time() * 1000)
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{timestamp}_{unique_id}"

# Instância global do serviço
webhook_service = WebhookService()