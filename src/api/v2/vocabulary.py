# src/api/v2/vocabulary.py - MIGRAÇÃO MCP→SERVICE COMPLETA
"""Endpoints para geração de vocabulário com contexto RAG hierárquico."""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional, Dict, Any
import logging
import time
import json
from datetime import datetime

from src.services.hierarchical_database import hierarchical_db
from src.services.vocabulary_generator import VocabularyGeneratorService
from src.core.unit_models import (
    SuccessResponse, ErrorResponse, VocabularySection, VocabularyItem,
    VocabularyGenerationRequest
)
from src.core.enums import CEFRLevel, LanguageVariant, UnitType, UnitStatus
from src.core.audit_logger import (
    audit_logger_instance, AuditEventType, audit_endpoint, extract_unit_info
)
from src.core.rate_limiter import rate_limit_dependency
from src.core.webhook_utils import create_async_wrapper, should_process_async, WebhookResponse
from src.services.webhook_service import webhook_service

router = APIRouter()
logger = logging.getLogger(__name__)


async def rate_limit_vocabulary_generation(request: Request):
    """Rate limiting específico para geração de vocabulário."""
    await rate_limit_dependency(request, "generate_vocabulary")


def serialize_datetime(obj):
    """Serializa datetime para string ISO."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj


async def _generate_vocabulary_for_unit_sync(
    unit_id: str,
    vocabulary_request: VocabularyGenerationRequest,
    request: Request,
    _: None = None
):
    """
    Gerar vocabulário contextual para a unidade usando RAG e análise de imagens.
    
    Flow do IVO V2:
    1. Buscar unidade e validar hierarquia
    2. Analisar imagens via Image Analysis Service (migrado de MCP)
    3. Usar RAG para contexto de progressão
    4. Evitar repetições de vocabulário já ensinado
    5. Gerar vocabulário adequado ao nível CEFR
    6. Salvar e atualizar status da unidade
    """
    try:
        logger.info(f"Iniciando geração de vocabulário para unidade: {unit_id}")
        
        # 1. Buscar e validar unidade
        unit = await hierarchical_db.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # 2. Verificar status adequado
        if unit.status.value not in ["creating", "vocab_pending"]:
            if unit.vocabulary:
                logger.info(f"Unidade {unit_id} já possui vocabulário - regenerando")
        
        # 3. Buscar contexto da hierarquia
        course = await hierarchical_db.get_course(unit.course_id)
        book = await hierarchical_db.get_book(unit.book_id)
        
        if not course or not book:
            raise HTTPException(
                status_code=400,
                detail="Hierarquia inválida: curso ou book não encontrado"
            )
        
        # 4. Buscar contexto RAG para evitar repetições
        logger.info("Coletando contexto RAG para prevenção de repetições...")
        
        taught_vocabulary = await hierarchical_db.get_taught_vocabulary(
            unit.course_id, unit.book_id, unit.sequence_order
        )
        
        used_strategies = await hierarchical_db.get_used_strategies(
            unit.course_id, unit.book_id, unit.sequence_order
        )
        
        # 5. Analisar imagens se existirem (usando Image Analysis Service - migrado de MCP)
        images_analysis = {}
        if unit.images and len(unit.images) > 0:
            try:
                logger.info("Analisando imagens via Image Analysis Service para contexto de vocabulário...")
                
                # ✅ MIGRAÇÃO COMPLETA: MCP → Service integrado
                from src.services.image_analysis_service import analyze_images_for_unit_creation
                
                # Extrair dados base64 das imagens
                images_b64 = []
                for img in unit.images:
                    if img.get("base64"):
                        images_b64.append(img["base64"])
                
                if images_b64:
                    images_analysis = await analyze_images_for_unit_creation(
                        image_files_b64=images_b64,
                        context=unit.context or "",
                        cefr_level=unit.cefr_level.value,
                        unit_type=unit.unit_type.value
                    )
                    
                    if images_analysis.get("success"):
                        logger.info(f"✅ Análise de imagens bem-sucedida (service integrado): {len(images_analysis.get('consolidated_vocabulary', {}).get('vocabulary', []))} palavras sugeridas")
                    else:
                        logger.warning(f"⚠️ Falha na análise de imagens: {images_analysis.get('error', 'Erro desconhecido')}")
                        
            except Exception as e:
                logger.warning(f"⚠️ Erro na análise de imagens via Service: {str(e)}")
                images_analysis = {"error": str(e)}
        
        # 6. Preparar dados para geração
        unit_data = {
            "title": unit.title,
            "context": unit.context,
            "cefr_level": unit.cefr_level.value,
            "language_variant": unit.language_variant.value,
            "unit_type": unit.unit_type.value
        }
        
        hierarchy_context = {
            "course_name": course.name,
            "book_name": book.name,
            "sequence_order": unit.sequence_order,
            "target_level": book.target_level.value
        }
        
        rag_context = {
            "taught_vocabulary": taught_vocabulary,
            "used_strategies": used_strategies,
            "progression_level": _determine_progression_level(unit.sequence_order),
            "vocabulary_density": len(taught_vocabulary) / max(unit.sequence_order, 1)
        }
        
        # 7. Gerar vocabulário usando service
        start_time = time.time()
        vocabulary_generator = VocabularyGeneratorService()
        
        logger.info("🔍 [DEBUG] Chamando VocabularyGeneratorService...")
        vocabulary_section = await vocabulary_generator.generate_vocabulary_for_unit(
            vocabulary_request,
            unit_data,
            hierarchy_context,
            rag_context,
            images_analysis
        )
        logger.info("🔍 [DEBUG] VocabularyGeneratorService retornou dados")
        
        generation_time = time.time() - start_time
        
        # 8. Salvar vocabulário na unidade
        logger.info("🔍 [DEBUG] Salvando no banco...")
        vocab_for_db = serialize_datetime(vocabulary_section.model_dump())
        await hierarchical_db.update_unit_content(
            unit_id, 
            "vocabulary", 
            vocab_for_db
        )
        logger.info("🔍 [DEBUG] Salvo no banco OK")
        
        # 9. Atualizar lista de vocabulário ensinado na unidade
        vocabulary_words = [item.word for item in vocabulary_section.items]
        await hierarchical_db.update_unit_content(
            unit_id,
            "vocabulary_taught",
            vocabulary_words
        )
        
        # 10. Fazer upsert de embedding do vocabulário gerado
        logger.info("🔍 [DEBUG] Criando embedding do vocabulário...")
        try:
            embedding_success = await hierarchical_db.upsert_single_content_embedding(
                unit_id=unit_id,
                content_type="vocabulary",
                content_data=vocab_for_db
            )
            if embedding_success:
                logger.info("✅ Embedding do vocabulário criado com sucesso")
            else:
                logger.warning("⚠️ Falha ao criar embedding do vocabulário (não afeta resultado)")
        except Exception as embedding_error:
            logger.warning(f"⚠️ Erro ao criar embedding do vocabulário: {str(embedding_error)}")
        
        # 11. Atualizar status da unidade
        await hierarchical_db.update_unit_status(unit_id, UnitStatus.SENTENCES_PENDING)
        
        # 11. Log de auditoria
        await audit_logger_instance.log_content_generation(
            request=request,
            generation_type="vocabulary",
            unit_id=unit_id,
            book_id=unit.book_id,
            course_id=unit.course_id,
            content_stats={
                "vocabulary_count": len(vocabulary_section.items),
                "new_words": vocabulary_section.new_words_count,
                "reinforcement_words": vocabulary_section.reinforcement_words_count,
                "context_relevance": vocabulary_section.context_relevance,
                "progression_level": rag_context["progression_level"]
            },
            ai_usage={
                "model": "gpt-4o-mini",
                "generation_time": generation_time,
                "images_analyzed": len(unit.images) if unit.images else 0,
                "service_used": "ImageAnalysisService (migrado de MCP)"
            },
            processing_time=generation_time,
            success=True
        )
        
        # DEBUG: Rastrear serialização
        logger.info("🔍 [DEBUG] Preparando resposta - vocabulary_section criado")
        
        try:
            vocab_data = vocabulary_section.model_dump()
            logger.info("🔍 [DEBUG] vocabulary_section.model_dump() OK")
        except Exception as e:
            logger.error(f"🔍 [DEBUG] ERRO vocabulary_section.model_dump(): {e}")
            raise
        
        try:
            vocab_serialized = serialize_datetime(vocab_data)
            logger.info("🔍 [DEBUG] serialize_datetime(vocab_data) OK")
        except Exception as e:
            logger.error(f"🔍 [DEBUG] ERRO serialize_datetime(): {e}")
            raise
        
        logger.info("🔍 [DEBUG] Criando SuccessResponse...")
        
        return SuccessResponse(
            data={
                "vocabulary": vocab_serialized,
                "generation_stats": {
                    "total_words": len(vocabulary_section.items),
                    "new_words": vocabulary_section.new_words_count,
                    "reinforcement_words": vocabulary_section.reinforcement_words_count,
                    "context_relevance": f"{vocabulary_section.context_relevance:.1%}",
                    "processing_time": f"{generation_time:.2f}s"
                },
                "unit_progression": {
                    "unit_id": unit_id,
                    "previous_status": unit.status.value,
                    "new_status": "sentences_pending",
                    "next_step": "Gerar sentences conectadas ao vocabulário"
                },
                "rag_context_used": {
                    "taught_vocabulary_count": len(taught_vocabulary),
                    "avoided_repetitions": len([w for w in vocabulary_words if w.lower() not in [tv.lower() for tv in taught_vocabulary]]),
                    "progression_level": rag_context["progression_level"],
                    "images_analyzed": len(unit.images) if unit.images else 0
                },
                "migration_info": {
                    "images_analyzed": len(unit.images) if unit.images else 0,
                    "service_analysis_success": images_analysis.get("success", False),
                    "vocabulary_from_images": len(images_analysis.get("consolidated_vocabulary", {}).get("vocabulary", [])) if images_analysis.get("success") else 0,
                    "migration_status": "✅ MCP → Service migration completed successfully"
                }
            },
            message=f"Vocabulário gerado com sucesso para unidade '{unit.title}' (service integrado)",
            hierarchy_info={
                "course_id": unit.course_id,
                "book_id": unit.book_id,
                "unit_id": unit_id,
                "sequence": unit.sequence_order
            },
            next_suggested_actions=[
                "Gerar sentences conectadas",
                f"POST /api/v2/units/{unit_id}/sentences",
                "Verificar contexto RAG atualizado",
                f"GET /api/v2/units/{unit_id}/context"
            ]
        )
        
        logger.info("🔍 [DEBUG] SuccessResponse criado, saindo da função")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar vocabulário para unidade {unit_id}: {str(e)}")
        
        # Log de erro
        await audit_logger_instance.log_content_generation(
            request=request,
            generation_type="vocabulary",
            unit_id=unit_id,
            book_id=getattr(unit, 'book_id', ''),
            course_id=getattr(unit, 'course_id', ''),
            success=False,
            error_details=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na geração de vocabulário: {str(e)}"
        )


@router.post("/units/{unit_id}/vocabulary")
@audit_endpoint(AuditEventType.UNIT_CONTENT_GENERATED, extract_unit_info)
async def generate_vocabulary_for_unit(
    unit_id: str,
    vocabulary_request: VocabularyGenerationRequest,
    request: Request,
    _: None = Depends(rate_limit_vocabulary_generation)
):
    """
    Gerar vocabulário contextual para a unidade.
    
    Suporta processamento síncrono e assíncrono:
    - Se webhook_url não for fornecida: processamento síncrono (comportamento original)
    - Se webhook_url for fornecida: processamento assíncrono com notificação via webhook
    
    Para processamento assíncrono, inclua 'webhook_url' no payload:
    {
        "webhook_url": "https://your-endpoint.com/webhook",
        "target_count": 25,
        "difficulty_level": "intermediate"
    }
    
    O webhook receberá o resultado completo quando o processamento for concluído.
    """
    try:
        # Verificar se deve processar assíncronamente
        if hasattr(vocabulary_request, 'webhook_url') and vocabulary_request.webhook_url:
            from src.core.webhook_utils import validate_webhook_url, extract_webhook_metadata
            
            # Validar webhook_url
            is_valid, error = validate_webhook_url(vocabulary_request.webhook_url)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"webhook_url inválida: {error}"
                )
            
            # Gerar task ID
            task_id = webhook_service.generate_task_id("vocab")
            
            # Extrair metadados
            metadata = extract_webhook_metadata(
                "vocabulary",
                unit_id, 
                vocabulary_request.model_dump(),
                {"cefr_level": "unknown", "endpoint": "vocabulary"}
            )
            
            # Criar cópia do request sem webhook_url
            clean_request = vocabulary_request.model_copy()
            clean_request.webhook_url = None
            
            # Executar assíncronamente
            await webhook_service.execute_async_task(
                task_id=task_id,
                webhook_url=vocabulary_request.webhook_url,
                task_func=_generate_vocabulary_for_unit_sync,
                task_args=(unit_id, clean_request, request),
                task_kwargs={},
                metadata=metadata
            )
            
            # Retornar resposta de aceitação
            return WebhookResponse.async_accepted(task_id, vocabulary_request.webhook_url, "vocabulary")
        
        else:
            # Processamento síncrono (comportamento original)
            return await _generate_vocabulary_for_unit_sync(unit_id, vocabulary_request, request)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no endpoint de vocabulário {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/units/{unit_id}/vocabulary", response_model=SuccessResponse)
async def get_unit_vocabulary(unit_id: str, request: Request):
    """Obter vocabulário da unidade."""
    try:
        logger.info(f"Buscando vocabulário da unidade: {unit_id}")
        
        # Buscar unidade
        unit = await hierarchical_db.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # Verificar se possui vocabulário
        if not unit.vocabulary:
            return SuccessResponse(
                data={
                    "has_vocabulary": False,
                    "unit_status": unit.status.value,
                    "message": "Unidade ainda não possui vocabulário gerado"
                },
                message="Vocabulário não encontrado",
                hierarchy_info={
                    "course_id": unit.course_id,
                    "book_id": unit.book_id,
                    "unit_id": unit_id,
                    "sequence": unit.sequence_order
                },
                next_suggested_actions=[
                    "Gerar vocabulário",
                    f"POST /api/v2/units/{unit_id}/vocabulary"
                ]
            )
        
        # Buscar contexto adicional
        course = await hierarchical_db.get_course(unit.course_id)
        book = await hierarchical_db.get_book(unit.book_id)
        
        # Análise do vocabulário
        vocabulary_data = unit.vocabulary
        vocabulary_items = vocabulary_data.get("items", [])
        
        # Estatísticas por classe de palavra
        word_class_distribution = {}
        frequency_distribution = {}
        
        for item in vocabulary_items:
            word_class = item.get("word_class", "unknown")
            frequency = item.get("frequency_level", "unknown")
            
            word_class_distribution[word_class] = word_class_distribution.get(word_class, 0) + 1
            frequency_distribution[frequency] = frequency_distribution.get(frequency, 0) + 1
        
        return SuccessResponse(
            data={
                "vocabulary": vocabulary_data,
                "analysis": {
                    "total_words": len(vocabulary_items),
                    "word_class_distribution": word_class_distribution,
                    "frequency_distribution": frequency_distribution,
                    "context_relevance": vocabulary_data.get("context_relevance", 0),
                    "new_words_count": vocabulary_data.get("new_words_count", 0),
                    "reinforcement_words_count": vocabulary_data.get("reinforcement_words_count", 0),
                    "progression_level": vocabulary_data.get("progression_level", "unknown")
                },
                "unit_context": {
                    "unit_title": unit.title,
                    "unit_type": unit.unit_type.value,
                    "cefr_level": unit.cefr_level.value,
                    "course_name": course.name if course else None,
                    "book_name": book.name if book else None,
                    "sequence_order": unit.sequence_order
                },
                "has_vocabulary": True
            },
            message=f"Vocabulário da unidade '{unit.title}'",
            hierarchy_info={
                "course_id": unit.course_id,
                "book_id": unit.book_id,
                "unit_id": unit_id,
                "sequence": unit.sequence_order
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar vocabulário da unidade {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.put("/units/{unit_id}/vocabulary", response_model=SuccessResponse)
async def update_unit_vocabulary(
    unit_id: str,
    vocabulary_data: Dict[str, Any],
    request: Request,
    _: None = Depends(rate_limit_vocabulary_generation)
):
    """Atualizar vocabulário da unidade (edição manual)."""
    try:
        logger.info(f"Atualizando vocabulário da unidade: {unit_id}")
        
        # Verificar se unidade existe
        unit = await hierarchical_db.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # Validar estrutura básica dos dados
        if not isinstance(vocabulary_data, dict):
            raise HTTPException(
                status_code=400,
                detail="Dados de vocabulário devem ser um objeto JSON"
            )
        
        required_fields = ["items"]
        for field in required_fields:
            if field not in vocabulary_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Campo obrigatório ausente: {field}"
                )
        
        # Validar estrutura dos items
        items = vocabulary_data["items"]
        if not isinstance(items, list):
            raise HTTPException(
                status_code=400,
                detail="Campo 'items' deve ser uma lista"
            )
        
        # Validar cada item
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=400,
                    detail=f"Item {i+1} deve ser um objeto"
                )
            
            required_item_fields = ["word", "phoneme", "definition", "example"]
            for field in required_item_fields:
                if field not in item:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Campo obrigatório ausente no item {i+1}: {field}"
                    )
        
        # Atualizar total_count automaticamente
        vocabulary_data["total_count"] = len(items)
        vocabulary_data["updated_at"] = time.time()
        
        # Extrair palavras para atualizar vocabulary_taught
        vocabulary_words = [item["word"] for item in items]
        
        # Salvar no banco
        await hierarchical_db.update_unit_content(unit_id, "vocabulary", vocabulary_data)
        await hierarchical_db.update_unit_content(unit_id, "vocabulary_taught", vocabulary_words)
        
        # Log da atualização
        await audit_logger_instance.log_event(
            event_type=AuditEventType.UNIT_UPDATED,
            request=request,
            additional_data={
                "update_type": "vocabulary_manual_edit",
                "vocabulary_count": len(items),
                "unit_id": unit_id
            }
        )
        
        return SuccessResponse(
            data={
                "updated": True,
                "vocabulary": vocabulary_data,
                "update_stats": {
                    "total_words": len(items),
                    "update_timestamp": vocabulary_data["updated_at"]
                }
            },
            message=f"Vocabulário atualizado com sucesso",
            hierarchy_info={
                "course_id": unit.course_id,
                "book_id": unit.book_id,
                "unit_id": unit_id,
                "sequence": unit.sequence_order
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar vocabulário da unidade {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.delete("/units/{unit_id}/vocabulary", response_model=SuccessResponse)
async def delete_unit_vocabulary(unit_id: str, request: Request):
    """Deletar vocabulário da unidade."""
    try:
        logger.warning(f"Deletando vocabulário da unidade: {unit_id}")
        
        # Verificar se unidade existe
        unit = await hierarchical_db.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # Verificar se possui vocabulário
        if not unit.vocabulary:
            return SuccessResponse(
                data={
                    "deleted": False,
                    "message": "Unidade não possui vocabulário para deletar"
                },
                message="Nenhum vocabulário encontrado para deletar"
            )
        
        # Deletar vocabulário (setar como None)
        await hierarchical_db.update_unit_content(unit_id, "vocabulary", None)
        await hierarchical_db.update_unit_content(unit_id, "vocabulary_taught", [])
        
        # Ajustar status se necessário (voltar para vocab_pending)
        if unit.status.value in ["sentences_pending", "content_pending", "assessments_pending", "completed"]:
            await hierarchical_db.update_unit_status(unit_id, "vocab_pending")
        
        # Log da deleção
        await audit_logger_instance.log_event(
            event_type=AuditEventType.UNIT_UPDATED,
            request=request,
            additional_data={
                "update_type": "vocabulary_deleted",
                "unit_id": unit_id,
                "previous_vocabulary_count": len(unit.vocabulary.get("items", []))
            }
        )
        
        return SuccessResponse(
            data={
                "deleted": True,
                "previous_vocabulary_count": len(unit.vocabulary.get("items", [])),
                "new_status": "vocab_pending"
            },
            message="Vocabulário deletado com sucesso",
            hierarchy_info={
                "course_id": unit.course_id,
                "book_id": unit.book_id,
                "unit_id": unit_id,
                "sequence": unit.sequence_order
            },
            next_suggested_actions=[
                "Regenerar vocabulário",
                f"POST /api/v2/units/{unit_id}/vocabulary"
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar vocabulário da unidade {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/units/{unit_id}/vocabulary/analysis", response_model=SuccessResponse)
async def analyze_unit_vocabulary(unit_id: str, request: Request):
    """Analisar qualidade e adequação do vocabulário da unidade."""
    try:
        logger.info(f"Analisando vocabulário da unidade: {unit_id}")
        
        # Buscar unidade
        unit = await hierarchical_db.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # Verificar se possui vocabulário
        if not unit.vocabulary:
            raise HTTPException(
                status_code=400,
                detail="Unidade não possui vocabulário para analisar"
            )
        
        # Buscar vocabulário já ensinado para comparação
        taught_vocabulary = await hierarchical_db.get_taught_vocabulary(
            unit.course_id, unit.book_id, unit.sequence_order
        )
        
        # Analisar vocabulário
        vocabulary_data = unit.vocabulary
        items = vocabulary_data.get("items", [])
        
        analysis = {
            "basic_statistics": _analyze_vocabulary_statistics(items),
            "cefr_adequacy": _analyze_cefr_adequacy(items, unit.cefr_level.value),
            "repetition_analysis": _analyze_vocabulary_repetitions(items, taught_vocabulary),
            "phoneme_analysis": _analyze_phoneme_quality(items),
            "contextual_relevance": vocabulary_data.get("context_relevance", 0),
            "progression_metrics": {
                "new_words_count": vocabulary_data.get("new_words_count", 0),
                "reinforcement_words_count": vocabulary_data.get("reinforcement_words_count", 0),
                "progression_level": vocabulary_data.get("progression_level", "unknown")
            }
        }
        
        # Gerar recomendações
        recommendations = _generate_vocabulary_recommendations(analysis, unit)
        
        return SuccessResponse(
            data={
                "analysis": analysis,
                "recommendations": recommendations,
                "summary": {
                    "total_words": len(items),
                    "taught_vocabulary_count": len(taught_vocabulary),
                    "overall_quality": _calculate_vocabulary_overall_quality(analysis),
                    "needs_improvement": len(recommendations) > 0
                }
            },
            message=f"Análise do vocabulário da unidade '{unit.title}'",
            hierarchy_info={
                "course_id": unit.course_id,
                "book_id": unit.book_id,
                "unit_id": unit_id,
                "sequence": unit.sequence_order
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao analisar vocabulário da unidade {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _determine_progression_level(sequence_order: int) -> str:
    """Determinar nível de progressão baseado na sequência."""
    if sequence_order <= 3:
        return "high_frequency_basic"
    elif sequence_order <= 7:
        return "functional_vocabulary"
    else:
        return "contextual_expansion"


def _calculate_target_vocabulary_count(cefr_level: str, sequence_order: int) -> int:
    """Calcular número alvo de vocabulário baseado no nível e sequência."""
    base_counts = {
        "A1": 20,
        "A2": 25,
        "B1": 30,
        "B2": 35,
        "C1": 40,
        "C2": 45
    }
    
    base = base_counts.get(cefr_level, 25)
    
    # Ajustar baseado na sequência (primeiras unidades podem ter menos)
    if sequence_order <= 2:
        return max(15, base - 5)
    elif sequence_order <= 5:
        return base
    else:
        return min(50, base + 5)


def _analyze_vocabulary_statistics(items: List[Dict]) -> Dict[str, Any]:
    """Analisar estatísticas básicas do vocabulário."""
    if not items:
        return {"error": "No vocabulary items to analyze"}
    
    word_classes = {}
    frequency_levels = {}
    word_lengths = []
    
    for item in items:
        # Classe de palavra
        word_class = item.get("word_class", "unknown")
        word_classes[word_class] = word_classes.get(word_class, 0) + 1
        
        # Nível de frequência
        frequency = item.get("frequency_level", "unknown")
        frequency_levels[frequency] = frequency_levels.get(frequency, 0) + 1
        
        # Comprimento da palavra
        word = item.get("word", "")
        word_lengths.append(len(word))
    
    return {
        "total_words": len(items),
        "word_class_distribution": word_classes,
        "frequency_distribution": frequency_levels,
        "average_word_length": sum(word_lengths) / len(word_lengths) if word_lengths else 0,
        "word_length_range": {"min": min(word_lengths), "max": max(word_lengths)} if word_lengths else {}
    }


def _analyze_cefr_adequacy(items: List[Dict], cefr_level: str) -> Dict[str, Any]:
    """Analisar adequação ao nível CEFR."""
    expected_frequency = {
        "A1": "high",
        "A2": "high", 
        "B1": "medium",
        "B2": "medium",
        "C1": "low",
        "C2": "low"
    }
    
    expected = expected_frequency.get(cefr_level, "medium")
    appropriate_count = 0
    
    for item in items:
        frequency = item.get("frequency_level", "medium")
        if frequency == expected:
            appropriate_count += 1
    
    adequacy_percentage = (appropriate_count / len(items)) * 100 if items else 0
    
    return {
        "expected_frequency": expected,
        "appropriate_words": appropriate_count,
        "total_words": len(items),
        "adequacy_percentage": adequacy_percentage,
        "needs_adjustment": adequacy_percentage < 70
    }


def _analyze_vocabulary_repetitions(items: List[Dict], taught_vocabulary: List[str]) -> Dict[str, Any]:
    """Analisar repetições com vocabulário já ensinado."""
    current_words = [item.get("word", "").lower() for item in items]
    taught_words_lower = [word.lower() for word in taught_vocabulary]
    
    repetitions = [word for word in current_words if word in taught_words_lower]
    new_words = [word for word in current_words if word not in taught_words_lower]
    
    return {
        "repeated_words": repetitions,
        "new_words": new_words,
        "repetition_count": len(repetitions),
        "new_words_count": len(new_words),
        "repetition_percentage": (len(repetitions) / len(current_words)) * 100 if current_words else 0,
        "is_appropriate_repetition": 5 <= len(repetitions) <= 15  # 5-15% de repetição é bom
    }


def _analyze_phoneme_quality(items: List[Dict]) -> Dict[str, Any]:
    """Analisar qualidade dos fonemas IPA."""
    phonemes_present = 0
    phonemes_missing = 0
    
    for item in items:
        phoneme = item.get("phoneme", "")
        if phoneme and phoneme.startswith("/") and phoneme.endswith("/"):
            phonemes_present += 1
        else:
            phonemes_missing += 1
    
    completeness = (phonemes_present / len(items)) * 100 if items else 0
    
    return {
        "phonemes_present": phonemes_present,
        "phonemes_missing": phonemes_missing,
        "completeness_percentage": completeness,
        "quality_good": completeness >= 95
    }


def _generate_vocabulary_recommendations(analysis: Dict[str, Any], unit) -> List[str]:
    """Gerar recomendações para melhorar vocabulário."""
    recommendations = []
    
    # Análise básica
    basic_stats = analysis["basic_statistics"]
    if basic_stats["total_words"] < 20:
        recommendations.append(f"Vocabulário insuficiente ({basic_stats['total_words']} palavras). Recomendado: 20-30 palavras.")
    
    # Análise CEFR
    cefr_analysis = analysis["cefr_adequacy"]
    if cefr_analysis["needs_adjustment"]:
        recommendations.append(
            f"Apenas {cefr_analysis['adequacy_percentage']:.1f}% das palavras são adequadas ao nível {unit.cefr_level.value}. "
            f"Foque em palavras de frequência '{cefr_analysis['expected_frequency']}'."
        )
    
    # Análise de repetições
    repetition_analysis = analysis["repetition_analysis"]
    if repetition_analysis["repetition_percentage"] > 20:
        recommendations.append(
            f"Muitas repetições ({repetition_analysis['repetition_percentage']:.1f}%). "
            f"Reduza palavras já ensinadas: {', '.join(repetition_analysis['repeated_words'][:3])}"
        )
    elif repetition_analysis["repetition_percentage"] < 5:
        recommendations.append(
            "Muito poucas repetições. Considere reforçar vocabulário anterior (5-15% ideal)."
        )
    
    # Análise de fonemas
    phoneme_analysis = analysis["phoneme_analysis"]
    if not phoneme_analysis["quality_good"]:
        recommendations.append(
            f"Fonemas IPA incompletos ({phoneme_analysis['completeness_percentage']:.1f}% presente). "
            f"Adicione transcrições para {phoneme_analysis['phonemes_missing']} palavras."
        )
    
    # Análise de distribuição
    word_classes = basic_stats["word_class_distribution"]
    if word_classes.get("noun", 0) > len(basic_stats) * 0.6:
        recommendations.append("Muitos substantivos. Diversifique com verbos e adjetivos.")
    
    # Contextual relevance
    context_relevance = analysis.get("contextual_relevance", 0)
    if context_relevance < 0.7:
        recommendations.append(
            f"Baixa relevância contextual ({context_relevance:.1%}). "
            f"Alinhe melhor o vocabulário com o tema da unidade."
        )
    
    return recommendations


def _calculate_vocabulary_overall_quality(analysis: Dict[str, Any]) -> float:
    """Calcular qualidade geral do vocabulário."""
    try:
        cefr_score = analysis["cefr_adequacy"]["adequacy_percentage"] / 100
        phoneme_score = analysis["phoneme_analysis"]["completeness_percentage"] / 100
        context_score = analysis.get("contextual_relevance", 0.7)
        
        # Repetition score (inverso - muita repetição é ruim)
        repetition_pct = analysis["repetition_analysis"]["repetition_percentage"]
        if 5 <= repetition_pct <= 15:
            repetition_score = 1.0
        elif repetition_pct < 5:
            repetition_score = 0.8
        else:
            repetition_score = max(0.3, 1.0 - (repetition_pct - 15) / 100)
        
        # Média ponderada
        overall = (cefr_score * 0.3 + phoneme_score * 0.2 + context_score * 0.3 + repetition_score * 0.2)
        return round(overall, 2)
        
    except Exception as e:
        logger.warning(f"Erro ao calcular qualidade geral: {str(e)}")
        return 0.7  # Score padrão