# src/api/v2/sentences.py
"""Endpoints para geração de sentences conectadas ao vocabulário."""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional, Dict, Any
import logging
import time
import json
from datetime import datetime

from src.services.hierarchical_database import hierarchical_db
from src.core.unit_models import (
    SuccessResponse, ErrorResponse, SentencesSection, Sentence,
    SentenceGenerationRequest
)
from src.core.enums import CEFRLevel, LanguageVariant, UnitType, UnitStatus
from src.core.audit_logger import (
    audit_logger_instance, AuditEventType, audit_endpoint, extract_unit_info
)
from src.core.rate_limiter import rate_limit_dependency
from src.services.sentences_generator import SentencesGeneratorService
from src.core.webhook_utils import validate_webhook_url, extract_webhook_metadata, WebhookResponse
from src.services.webhook_service import webhook_service

router = APIRouter()
logger = logging.getLogger(__name__)


def serialize_datetime(obj):
    """Serializa datetime para string ISO."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj


async def rate_limit_sentences_generation(request: Request):
    """Rate limiting específico para geração de sentences."""
    await rate_limit_dependency(request, "generate_sentences")


async def _generate_sentences_for_unit_sync(
    unit_id: str,
    sentences_request: SentenceGenerationRequest,
    request: Request,
    _: None = None
):
    """
    Gerar sentences conectadas ao vocabulário da unidade.
    
    Flow do IVO V2:
    1. Buscar unidade e validar hierarquia
    2. Verificar se vocabulário existe
    3. Usar RAG para contexto de progressão
    4. Gerar sentences usando vocabulário atual + reforço
    5. Salvar e atualizar status da unidade
    """
    try:
        logger.info(f"Iniciando geração de sentences para unidade: {unit_id}")
        
        # 1. Buscar e validar unidade
        unit = await hierarchical_db.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # 2. Verificar status adequado
        if unit.status.value not in ["vocab_pending", "sentences_pending"]:
            if unit.status.value == "creating":
                raise HTTPException(
                    status_code=400,
                    detail="Unidade ainda não possui vocabulário. Gere o vocabulário primeiro."
                )
            elif unit.sentences:
                logger.info(f"Unidade {unit_id} já possui sentences - regenerando")
        
        # 3. Verificar se possui vocabulário válido
        if not unit.vocabulary or not unit.vocabulary.get("items"):
            # Verificar se houve falha na geração de vocabulário
            vocab_status = getattr(unit.vocabulary, 'generation_status', 'missing') if unit.vocabulary else 'missing'
            
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Vocabulário insuficiente para gerar sentences",
                    "status": vocab_status,
                    "vocabulary_items_count": len(unit.vocabulary.get("items", [])) if unit.vocabulary else 0,
                    "required_action": f"POST /api/v2/units/{unit_id}/vocabulary",
                    "suggestion": "A geração de vocabulário pode ter falhado. Tente regenerar o vocabulário primeiro."
                }
            )
        
        # 4. Buscar contexto RAG para progressão
        logger.info("Coletando contexto RAG para geração contextualizada...")
        
        taught_vocabulary = await hierarchical_db.get_taught_vocabulary(
            unit.course_id, unit.book_id, unit.sequence_order
        )
        
        # 5. Buscar contexto de course e book
        course = await hierarchical_db.get_course(unit.course_id)
        book = await hierarchical_db.get_book(unit.book_id)
        
        # 6. Preparar dados para geração
        unit_data = {
            "title": unit.title,
            "context": unit.context,
            "cefr_level": unit.cefr_level.value,
            "language_variant": unit.language_variant.value,
            "unit_type": unit.unit_type.value
        }
        
        hierarchy_context = {
            "course_name": course.name if course else "",
            "book_name": book.name if book else "",
            "sequence_order": unit.sequence_order,
            "target_level": book.target_level.value if book else unit.cefr_level.value
        }
        
        rag_context = {
            "taught_vocabulary": taught_vocabulary,
            "vocabulary_for_reinforcement": _select_reinforcement_vocabulary(
                taught_vocabulary, unit.vocabulary["items"]
            ),
            "progression_level": _determine_progression_level(unit.sequence_order)
        }
        
        images_context = unit.images or []
        
        # 7. Gerar sentences usando service
        start_time = time.time()
        sentences_generator = SentencesGeneratorService()
        
        sentences_section = await sentences_generator.generate_sentences_for_unit(
            sentences_request,
            unit_data,
            unit.vocabulary,
            hierarchy_context,
            rag_context,
            images_context
        )
        
        generation_time = time.time() - start_time
        
        # 8. Salvar sentences na unidade
        sentences_for_db = serialize_datetime(sentences_section.model_dump())
        await hierarchical_db.update_unit_content(
            unit_id, 
            "sentences", 
            sentences_for_db
        )
        
        # 9. Fazer upsert de embedding das sentences geradas
        logger.info("📊 Criando embedding das sentences...")
        try:
            embedding_success = await hierarchical_db.upsert_single_content_embedding(
                unit_id=unit_id,
                content_type="sentences",
                content_data=sentences_for_db
            )
            if embedding_success:
                logger.info("✅ Embedding das sentences criado com sucesso")
            else:
                logger.warning("⚠️ Falha ao criar embedding das sentences (não afeta resultado)")
        except Exception as embedding_error:
            logger.warning(f"⚠️ Erro ao criar embedding das sentences: {str(embedding_error)}")
        
        # 10. Atualizar status da unidade
        if unit.unit_type.value == "lexical_unit":
            next_status = "content_pending"  # Próximo: TIPS
        else:  # grammar_unit
            next_status = "content_pending"  # Próximo: GRAMMAR
        
        await hierarchical_db.update_unit_status(unit_id, UnitStatus.CONTENT_PENDING)
        
        # 10. Log de auditoria
        await audit_logger_instance.log_content_generation(
            request=None,  # Será preenchido pelo decorador
            generation_type="sentences",
            unit_id=unit_id,
            book_id=unit.book_id,
            course_id=unit.course_id,
            content_stats={
                "sentences_count": len(sentences_section.sentences),
                "vocabulary_coverage": sentences_section.vocabulary_coverage,
                "contextual_coherence": sentences_section.contextual_coherence,
                "progression_appropriateness": sentences_section.progression_appropriateness
            },
            ai_usage={
                "model": "gpt-4o-mini",
                "generation_time": generation_time
            },
            processing_time=generation_time,
            success=True
        )
        
        return SuccessResponse(
            data={
                "sentences": sentences_section.model_dump(mode='json'),
                "generation_stats": {
                    "total_sentences": len(sentences_section.sentences),
                    "vocabulary_coverage": f"{sentences_section.vocabulary_coverage:.1%}",
                    "contextual_coherence": f"{sentences_section.contextual_coherence:.1%}",
                    "processing_time": f"{generation_time:.2f}s"
                },
                "unit_progression": {
                    "unit_id": unit_id,
                    "previous_status": unit.status.value,
                    "new_status": next_status,
                    "next_step": "Gerar estratégias (TIPS ou GRAMMAR)"
                },
                "rag_context_used": {
                    "taught_vocabulary_count": len(taught_vocabulary),
                    "reinforcement_words": len(rag_context["vocabulary_for_reinforcement"]),
                    "progression_level": rag_context["progression_level"]
                }
            },
            message=f"Sentences geradas com sucesso para unidade '{unit.title}'",
            hierarchy_info={
                "course_id": unit.course_id,
                "book_id": unit.book_id,
                "unit_id": unit_id,
                "sequence": unit.sequence_order
            },
            next_suggested_actions=[
                f"Gerar {'TIPS' if unit.unit_type.value == 'lexical_unit' else 'GRAMMAR'}",
                f"POST /api/v2/units/{unit_id}/{'tips' if unit.unit_type.value == 'lexical_unit' else 'grammar'}",
                "Verificar contexto RAG atualizado",
                f"GET /api/v2/units/{unit_id}/context"
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar sentences para unidade {unit_id}: {str(e)}")
        
        # Log de erro
        await audit_logger_instance.log_content_generation(
            request=None,
            generation_type="sentences",
            unit_id=unit_id,
            book_id=getattr(unit, 'book_id', ''),
            course_id=getattr(unit, 'course_id', ''),
            success=False,
            error_details=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na geração de sentences: {str(e)}"
        )


@router.post("/units/{unit_id}/sentences")
@audit_endpoint(AuditEventType.UNIT_CONTENT_GENERATED, extract_unit_info)
async def generate_sentences_for_unit(
    unit_id: str,
    sentences_request: SentenceGenerationRequest,
    request: Request,
    _: None = Depends(rate_limit_sentences_generation)
):
    """Gerar sentences para unidade com suporte a webhooks."""
    try:
        # Verificar se deve processar assíncronamente
        if hasattr(sentences_request, 'webhook_url') and sentences_request.webhook_url:
            # Validar webhook_url
            is_valid, error = validate_webhook_url(sentences_request.webhook_url)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"webhook_url inválida: {error}")
            
            # Executar assíncronamente
            task_id = webhook_service.generate_task_id("sentences")
            metadata = extract_webhook_metadata("sentences", unit_id, sentences_request.model_dump(), {"endpoint": "sentences"})
            clean_request = sentences_request.model_copy()
            clean_request.webhook_url = None
            
            await webhook_service.execute_async_task(
                task_id=task_id,
                webhook_url=sentences_request.webhook_url,
                task_func=_generate_sentences_for_unit_sync,
                task_args=(unit_id, clean_request, request),
                task_kwargs={},
                metadata=metadata
            )
            
            return WebhookResponse.async_accepted(task_id, sentences_request.webhook_url, "sentences")
        
        else:
            # Processamento síncrono
            return await _generate_sentences_for_unit_sync(unit_id, sentences_request, request)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no endpoint de sentences {unit_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/units/{unit_id}/sentences", response_model=SuccessResponse)
async def get_unit_sentences(unit_id: str):
    """Obter sentences da unidade."""
    try:
        logger.info(f"Buscando sentences da unidade: {unit_id}")
        
        # Buscar unidade
        unit = await hierarchical_db.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # Verificar se possui sentences
        if not unit.sentences:
            return SuccessResponse(
                data={
                    "has_sentences": False,
                    "unit_status": unit.status.value,
                    "message": "Unidade ainda não possui sentences geradas"
                },
                message="Sentences não encontradas",
                hierarchy_info={
                    "course_id": unit.course_id,
                    "book_id": unit.book_id,
                    "unit_id": unit_id,
                    "sequence": unit.sequence_order
                },
                next_suggested_actions=[
                    "Gerar sentences",
                    f"POST /api/v2/units/{unit_id}/sentences"
                ]
            )
        
        # Buscar contexto adicional
        course = await hierarchical_db.get_course(unit.course_id)
        book = await hierarchical_db.get_book(unit.book_id)
        
        # Análise das sentences
        sentences_data = unit.sentences
        vocabulary_used = set()
        complexity_distribution = {}
        
        for sentence in sentences_data.get("sentences", []):
            # Vocabulário usado
            vocab_in_sentence = sentence.get("vocabulary_used", [])
            vocabulary_used.update(vocab_in_sentence)
            
            # Distribuição de complexidade
            complexity = sentence.get("complexity_level", "unknown")
            complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1
        
        return SuccessResponse(
            data={
                "sentences": sentences_data,
                "analysis": {
                    "total_sentences": len(sentences_data.get("sentences", [])),
                    "unique_vocabulary_used": len(vocabulary_used),
                    "vocabulary_coverage": sentences_data.get("vocabulary_coverage", 0),
                    "complexity_distribution": complexity_distribution,
                    "contextual_coherence": sentences_data.get("contextual_coherence", 0),
                    "progression_appropriateness": sentences_data.get("progression_appropriateness", 0)
                },
                "unit_context": {
                    "unit_title": unit.title,
                    "unit_type": unit.unit_type.value,
                    "cefr_level": unit.cefr_level.value,
                    "course_name": course.name if course else None,
                    "book_name": book.name if book else None,
                    "sequence_order": unit.sequence_order
                },
                "has_sentences": True
            },
            message=f"Sentences da unidade '{unit.title}'",
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
        logger.error(f"Erro ao buscar sentences da unidade {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.put("/units/{unit_id}/sentences", response_model=SuccessResponse)
async def update_unit_sentences(
    unit_id: str,
    sentences_data: Dict[str, Any],
    _: None = Depends(rate_limit_sentences_generation)
):
    """Atualizar sentences da unidade (edição manual)."""
    try:
        logger.info(f"Atualizando sentences da unidade: {unit_id}")
        
        # Verificar se unidade existe
        unit = await hierarchical_db.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # Validar estrutura básica dos dados
        if not isinstance(sentences_data, dict):
            raise HTTPException(
                status_code=400,
                detail="Dados de sentences devem ser um objeto JSON"
            )
        
        required_fields = ["sentences"]
        for field in required_fields:
            if field not in sentences_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Campo obrigatório ausente: {field}"
                )
        
        # Validar estrutura das sentences
        sentences = sentences_data["sentences"]
        if not isinstance(sentences, list):
            raise HTTPException(
                status_code=400,
                detail="Campo 'sentences' deve ser uma lista"
            )
        
        # Validar cada sentence
        for i, sentence in enumerate(sentences):
            if not isinstance(sentence, dict):
                raise HTTPException(
                    status_code=400,
                    detail=f"Sentence {i+1} deve ser um objeto"
                )
            
            required_sentence_fields = ["text", "vocabulary_used", "context_situation"]
            for field in required_sentence_fields:
                if field not in sentence:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Campo obrigatório ausente na sentence {i+1}: {field}"
                    )
        
        # Atualizar timestamps
        sentences_data["updated_at"] = time.time()
        
        # Salvar no banco
        await hierarchical_db.update_unit_content(unit_id, "sentences", sentences_data)
        
        # Log da atualização
        await audit_logger_instance.log_event(
            event_type=AuditEventType.UNIT_UPDATED,
            additional_data={
                "update_type": "sentences_manual_edit",
                "sentences_count": len(sentences),
                "unit_id": unit_id
            }
        )
        
        return SuccessResponse(
            data={
                "updated": True,
                "sentences": sentences_data,
                "update_stats": {
                    "total_sentences": len(sentences),
                    "update_timestamp": sentences_data["updated_at"]
                }
            },
            message=f"Sentences atualizadas com sucesso",
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
        logger.error(f"Erro ao atualizar sentences da unidade {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.delete("/units/{unit_id}/sentences", response_model=SuccessResponse)
async def delete_unit_sentences(unit_id: str):
    """Deletar sentences da unidade."""
    try:
        logger.warning(f"Deletando sentences da unidade: {unit_id}")
        
        # Verificar se unidade existe
        unit = await hierarchical_db.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # Verificar se possui sentences
        if not unit.sentences:
            return SuccessResponse(
                data={
                    "deleted": False,
                    "message": "Unidade não possui sentences para deletar"
                },
                message="Nenhuma sentence encontrada para deletar"
            )
        
        # Deletar sentences (setar como None)
        await hierarchical_db.update_unit_content(unit_id, "sentences", None)
        
        # Ajustar status se necessário
        if unit.status.value in ["content_pending", "assessments_pending", "completed"]:
            await hierarchical_db.update_unit_status(unit_id, UnitStatus.SENTENCES_PENDING)
        
        # Log da deleção
        await audit_logger_instance.log_event(
            event_type=AuditEventType.UNIT_UPDATED,
            additional_data={
                "update_type": "sentences_deleted",
                "unit_id": unit_id,
                "previous_sentences_count": len(unit.sentences.get("sentences", []))
            }
        )
        
        return SuccessResponse(
            data={
                "deleted": True,
                "previous_sentences_count": len(unit.sentences.get("sentences", [])),
                "new_status": "sentences_pending"
            },
            message="Sentences deletadas com sucesso",
            hierarchy_info={
                "course_id": unit.course_id,
                "book_id": unit.book_id,
                "unit_id": unit_id,
                "sequence": unit.sequence_order
            },
            next_suggested_actions=[
                "Regenerar sentences",
                f"POST /api/v2/units/{unit_id}/sentences"
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar sentences da unidade {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/units/{unit_id}/sentences/analysis", response_model=SuccessResponse)
async def analyze_unit_sentences(unit_id: str):
    """Analisar qualidade e adequação das sentences da unidade."""
    try:
        logger.info(f"Analisando sentences da unidade: {unit_id}")
        
        # Buscar unidade
        unit = await hierarchical_db.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # Verificar se possui sentences
        if not unit.sentences:
            raise HTTPException(
                status_code=400,
                detail="Unidade não possui sentences para analisar"
            )
        
        # Buscar vocabulário da unidade para comparação
        vocabulary_words = []
        if unit.vocabulary and unit.vocabulary.get("items"):
            vocabulary_words = [item["word"] for item in unit.vocabulary["items"]]
        
        # Analisar sentences
        sentences_data = unit.sentences
        sentences = sentences_data.get("sentences", [])
        
        analysis = {
            "vocabulary_analysis": _analyze_vocabulary_usage(sentences, vocabulary_words),
            "complexity_analysis": _analyze_complexity_distribution(sentences),
            "contextual_analysis": _analyze_contextual_coherence(sentences),
            "progression_analysis": _analyze_progression_appropriateness(sentences, unit.cefr_level.value),
            "quality_metrics": {
                "vocabulary_coverage": sentences_data.get("vocabulary_coverage", 0),
                "contextual_coherence": sentences_data.get("contextual_coherence", 0),
                "progression_appropriateness": sentences_data.get("progression_appropriateness", 0)
            }
        }
        
        # Gerar recomendações
        recommendations = _generate_sentences_recommendations(analysis, unit)
        
        return SuccessResponse(
            data={
                "analysis": analysis,
                "recommendations": recommendations,
                "summary": {
                    "total_sentences": len(sentences),
                    "vocabulary_words_available": len(vocabulary_words),
                    "overall_quality": _calculate_overall_quality(analysis),
                    "needs_improvement": len(recommendations) > 0
                }
            },
            message=f"Análise das sentences da unidade '{unit.title}'",
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
        logger.error(f"Erro ao analisar sentences da unidade {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _select_reinforcement_vocabulary(taught_vocabulary: List[str], current_vocabulary: List[Dict]) -> List[str]:
    """Selecionar palavras para reforço nas sentences."""
    current_words = {item["word"].lower() for item in current_vocabulary}
    taught_words = {word.lower() for word in taught_vocabulary}
    
    # Palavras já ensinadas que podem ser reforçadas (não estão no vocabulário atual)
    reinforcement_candidates = taught_words - current_words
    
    # Selecionar até 5 palavras para reforço
    return list(reinforcement_candidates)[:5]


def _determine_progression_level(sequence_order: int) -> str:
    """Determinar nível de progressão baseado na sequência."""
    if sequence_order <= 3:
        return "basic_introduction"
    elif sequence_order <= 7:
        return "building_foundation"
    elif sequence_order <= 12:
        return "expanding_context"
    else:
        return "advanced_application"


def _analyze_vocabulary_usage(sentences: List[Dict], vocabulary_words: List[str]) -> Dict[str, Any]:
    """Analisar uso do vocabulário nas sentences."""
    vocab_set = set(word.lower() for word in vocabulary_words)
    vocab_usage = {}
    total_vocab_instances = 0
    
    for sentence in sentences:
        vocab_used = sentence.get("vocabulary_used", [])
        for word in vocab_used:
            word_lower = word.lower()
            if word_lower in vocab_set:
                vocab_usage[word_lower] = vocab_usage.get(word_lower, 0) + 1
                total_vocab_instances += 1
    
    coverage = len(vocab_usage) / max(len(vocabulary_words), 1)
    
    return {
        "words_used": len(vocab_usage),
        "words_available": len(vocabulary_words),
        "coverage_percentage": coverage * 100,
        "usage_distribution": vocab_usage,
        "unused_words": [word for word in vocabulary_words if word.lower() not in vocab_usage],
        "average_usage_per_word": total_vocab_instances / max(len(vocab_usage), 1)
    }


def _analyze_complexity_distribution(sentences: List[Dict]) -> Dict[str, Any]:
    """Analisar distribuição de complexidade."""
    complexity_counts = {}
    
    for sentence in sentences:
        complexity = sentence.get("complexity_level", "unknown")
        complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
    
    total = len(sentences)
    complexity_percentages = {
        level: (count / total) * 100 
        for level, count in complexity_counts.items()
    }
    
    return {
        "distribution_counts": complexity_counts,
        "distribution_percentages": complexity_percentages,
        "most_common_level": max(complexity_counts, key=complexity_counts.get) if complexity_counts else "unknown",
        "total_sentences": total
    }


def _analyze_contextual_coherence(sentences: List[Dict]) -> Dict[str, Any]:
    """Analisar coerência contextual das sentences."""
    contexts = {}
    
    for sentence in sentences:
        context = sentence.get("context_situation", "unknown")
        contexts[context] = contexts.get(context, 0) + 1
    
    context_diversity = len(contexts)
    
    return {
        "context_situations": list(contexts.keys()),
        "context_distribution": contexts,
        "context_diversity": context_diversity,
        "most_common_context": max(contexts, key=contexts.get) if contexts else "unknown",
        "diversity_score": context_diversity / max(len(sentences), 1)
    }


def _analyze_progression_appropriateness(sentences: List[Dict], cefr_level: str) -> Dict[str, Any]:
    """Analisar adequação à progressão pedagógica."""
    # Análise simplificada baseada na complexidade esperada por nível
    expected_complexity = {
        "A1": "basic",
        "A2": "basic",
        "B1": "intermediate", 
        "B2": "intermediate",
        "C1": "advanced",
        "C2": "advanced"
    }
    
    expected = expected_complexity.get(cefr_level, "intermediate")
    appropriate_count = 0
    
    for sentence in sentences:
        complexity = sentence.get("complexity_level", "intermediate")
        if complexity == expected:
            appropriate_count += 1
    
    appropriateness = appropriate_count / max(len(sentences), 1)
    
    return {
        "expected_complexity": expected,
        "appropriate_sentences": appropriate_count,
        "total_sentences": len(sentences),
        "appropriateness_percentage": appropriateness * 100,
        "needs_adjustment": appropriateness < 0.7
    }


def _generate_sentences_recommendations(analysis: Dict[str, Any], unit) -> List[str]:
    """Gerar recomendações para melhorar sentences."""
    recommendations = []
    
    # Análise de vocabulário
    vocab_analysis = analysis["vocabulary_analysis"]
    if vocab_analysis["coverage_percentage"] < 70:
        recommendations.append(
            f"Baixa cobertura de vocabulário ({vocab_analysis['coverage_percentage']:.1f}%). "
            f"Considere usar mais palavras do vocabulário da unidade."
        )
    
    if vocab_analysis["unused_words"]:
        unused_sample = vocab_analysis["unused_words"][:3]
        recommendations.append(
            f"Palavras não utilizadas: {', '.join(unused_sample)}. "
            f"Considere criar sentences com essas palavras."
        )
    
    # Análise de complexidade
    complexity_analysis = analysis["complexity_analysis"]
    if "unknown" in complexity_analysis["distribution_counts"]:
        recommendations.append("Algumas sentences não têm nível de complexidade definido.")
    
    # Análise de progressão
    progression_analysis = analysis["progression_analysis"]
    if progression_analysis["needs_adjustment"]:
        recommendations.append(
            f"Apenas {progression_analysis['appropriateness_percentage']:.1f}% das sentences "
            f"são adequadas ao nível {unit.cefr_level.value}. Ajuste a complexidade."
        )
    
    # Análise contextual
    contextual_analysis = analysis["contextual_analysis"]
    if contextual_analysis["diversity_score"] < 0.5:
        recommendations.append(
            "Baixa diversidade contextual. Considere variar as situações das sentences."
        )
    
    return recommendations


def _calculate_overall_quality(analysis: Dict[str, Any]) -> float:
    """Calcular qualidade geral das sentences."""
    vocab_score = min(analysis["vocabulary_analysis"]["coverage_percentage"] / 100, 1.0)
    progression_score = analysis["progression_analysis"]["appropriateness_percentage"] / 100
    context_score = analysis["contextual_analysis"]["diversity_score"]
    
    # Média ponderada
    overall = (vocab_score * 0.4 + progression_score * 0.4 + context_score * 0.2)
    return round(overall, 2)


def _calculate_target_sentence_count(cefr_level: str, sequence_order: int) -> int:
    """Calcular número alvo de sentenças baseado no nível e sequência."""
    base_counts = {
        "A1": 8,
        "A2": 10,
        "B1": 12,
        "B2": 14,
        "C1": 16,
        "C2": 18
    }
    
    base = base_counts.get(cefr_level, 10)
    
    # Ajustar baseado na sequência (primeiras unidades podem ter menos)
    if sequence_order <= 2:
        return max(6, base - 2)
    elif sequence_order <= 5:
        return base
    else:
        return min(20, base + 2)