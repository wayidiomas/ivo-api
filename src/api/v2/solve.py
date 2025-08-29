# src/api/v2/solve.py
"""
Endpoints para geração de gabaritos (answer keys) para assessments via IA.
Sistema inteligente de geração de gabaritos usando GPT-5 com explicações pedagógicas.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional, Dict, Any
import logging
import time

from src.services.hierarchical_database import hierarchical_db
from src.services.solve_assessments import SolveAssessmentsService
from src.core.unit_models import (
    SuccessResponse, ErrorResponse, SimpleGabaritoRequest, AssessmentSolution
)
from src.core.audit_logger import (
    audit_logger_instance, AuditEventType, audit_endpoint, extract_unit_info
)
from src.core.rate_limiter import rate_limit_dependency

router = APIRouter(
    tags=["Gabarito Generation"],
    responses={
        404: {"description": "Unit or assessment not found"},
        400: {"description": "Invalid assessment type or missing data"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "AI gabarito generation service error"}
    }
)
logger = logging.getLogger(__name__)

# Instância global do serviço de geração de gabaritos
solve_service = SolveAssessmentsService()


async def rate_limit_gabarito_generation(request: Request):
    """Rate limiting específico para geração de gabaritos."""
    await rate_limit_dependency(request, "gabarito_generation")


@router.post(
    "/{unit_id}/generate_gabarito", 
    response_model=SuccessResponse,
    summary="Generate Assessment Answer Key (Gabarito) with AI",
    description="Generate comprehensive answer keys (gabaritos) for assessments using GPT-5 AI with detailed explanations and teaching notes.",
    operation_id="generate_unit_gabarito"
)
async def generate_unit_gabarito(
    unit_id: str,
    gabarito_request: SimpleGabaritoRequest,
    request: Request,
    _: None = Depends(rate_limit_gabarito_generation)
):
    """
    **Generate Assessment Answer Key (Gabarito) with AI**
    
    This endpoint uses GPT-5 to generate complete answer keys with:
    - Complete solutions for every assessment item
    - Detailed explanations for correct answers
    - Pedagogical reasoning for teachers
    - Skills analysis and CEFR alignment
    - Teaching notes and follow-up suggestions
    
    **Process:**
    1. Fetches unit data and target assessment from database
    2. AI analyzes assessment structure and context
    3. Generates comprehensive answer key with explanations
    4. Results saved to `solve_assessments` JSONB field
    
    **Assessment Types:** `cloze_test`, `gap_fill`, `reordering`, `transformation`, 
    `multiple_choice`, `true_false`, `matching`
    """
    logger.info(f"📝 Iniciando geração de gabarito para {gabarito_request.assessment_type} na unidade {unit_id}")
    
    try:
        # 1. Buscar unidade com TODOS os dados
        unit = await hierarchical_db.get_unit_with_hierarchy(unit_id)
        
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # 2. Verificar se tem assessments
        if not unit.assessments:
            raise HTTPException(
                status_code=400,
                detail="Unidade não possui assessments para geração de gabarito"
            )
        
        # 3. Validar assessment_type
        assessment_types = [activity.get("type") for activity in unit.assessments.get("activities", [])]
        if gabarito_request.assessment_type not in assessment_types:
            raise HTTPException(
                status_code=400,
                detail=f"Assessment '{gabarito_request.assessment_type}' não encontrado. Disponíveis: {assessment_types}"
            )
        
        # 4. Executar geração de gabarito via IA
        start_time = time.time()
        
        gabarito_result = await solve_service.generate_gabarito(
            unit=unit,  # Objeto completo da unidade
            assessment_type=gabarito_request.assessment_type,
            include_explanations=gabarito_request.include_explanations,
            difficulty_analysis=gabarito_request.difficulty_analysis
        )
        
        processing_time = time.time() - start_time
        
        # 5. Salvar resultado no banco
        await _save_gabarito_result_to_unit(unit_id, gabarito_request.assessment_type, gabarito_result)
        
        # 6. Log de auditoria
        await audit_logger_instance.log_content_generation(
            request=request,
            generation_type="gabarito_generation",
            unit_id=unit_id,
            book_id=unit.book_id,
            course_id=unit.course_id,
            content_stats={
                "assessment_type": gabarito_request.assessment_type,
                "total_items": gabarito_result.total_items,
                "included_explanations": gabarito_request.include_explanations,
                "difficulty_analysis": gabarito_request.difficulty_analysis,
                "processing_time": processing_time,
                "ai_model": gabarito_result.ai_model_used if hasattr(gabarito_result, 'ai_model_used') else 'gpt-5'
            },
            success=True
        )
        
        return SuccessResponse(
            data={
                "gabarito_result": gabarito_result.model_dump(),
                "processing_stats": {
                    "assessment_type": gabarito_request.assessment_type,
                    "total_items": gabarito_result.total_items,
                    "processing_time": f"{processing_time:.2f}s",
                    "ai_model_used": gabarito_result.ai_model_used if hasattr(gabarito_result, 'ai_model_used') else 'gpt-5',
                    "included_explanations": gabarito_request.include_explanations,
                    "difficulty_analysis": gabarito_request.difficulty_analysis
                }
            },
            message=f"Gabarito para '{gabarito_request.assessment_type}' gerado com sucesso - {gabarito_result.total_items} itens processados",
            hierarchy_info={
                "course_id": unit.course_id,
                "book_id": unit.book_id,
                "unit_id": unit_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar gabarito para unidade {unit_id}: {str(e)}")
        
        # Log de erro
        await audit_logger_instance.log_content_generation(
            request=request,
            generation_type="gabarito_generation",
            unit_id=unit_id,
            book_id="unknown",
            course_id="unknown",
            content_stats={
                "assessment_type": gabarito_request.assessment_type,
                "error": str(e)
            },
            success=False
        )
        
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao gerar gabarito"
        )


@router.get(
    "/{unit_id}/gabaritos", 
    response_model=SuccessResponse,
    summary="Get Assessment Answer Keys (Gabaritos)",
    description="Retrieve generated assessment answer keys from the database.",
    operation_id="get_unit_gabaritos"
)
async def get_unit_gabaritos(
    unit_id: str,
    assessment_type: Optional[str] = None,
    request: Request = None
):
    """
    Obter gabaritos gerados para assessments da unidade.
    
    Args:
        unit_id: ID da unidade
        assessment_type: Tipo específico de assessment (opcional)
        
    Returns:
        SuccessResponse com gabaritos disponíveis
    """
    logger.info(f"📋 Buscando gabaritos para unidade {unit_id}")
    
    try:
        # Buscar unidade
        unit = await hierarchical_db.get_unit(unit_id)
        
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # Obter solve_assessments do banco (campo usado para gabaritos também)
        gabarito_results = unit.solve_assessments or {}
        
        if not gabarito_results:
            return SuccessResponse(
                data={
                    "gabarito_results": {},
                    "available_gabaritos": [],
                    "message": "Nenhum gabarito encontrado para esta unidade"
                },
                message="Unidade sem gabaritos gerados",
                hierarchy_info={
                    "unit_id": unit_id,
                    "course_id": unit.course_id,
                    "book_id": unit.book_id
                }
            )
        
        # Filtrar por assessment_type se especificado
        filtered_results = gabarito_results
        if assessment_type:
            filtered_results = {
                k: v for k, v in gabarito_results.items() 
                if k == assessment_type
            }
            
            if not filtered_results:
                raise HTTPException(
                    status_code=404,
                    detail=f"Gabarito para assessment '{assessment_type}' não encontrado"
                )
        
        return SuccessResponse(
            data={
                "gabarito_results": filtered_results,
                "available_gabaritos": list(gabarito_results.keys()),
                "gabarito_count": len(filtered_results),
                "unit_info": {
                    "unit_title": unit.title,
                    "cefr_level": unit.cefr_level.value,
                    "unit_type": unit.unit_type.value
                }
            },
            message=f"Gabaritos obtidos com sucesso",
            hierarchy_info={
                "unit_id": unit_id,
                "course_id": unit.course_id,
                "book_id": unit.book_id
            },
            next_suggested_actions=[
                "Analisar soluções completas",
                "Revisar explicações pedagógicas",
                f"POST /api/v2/units/{unit_id}/generate_gabarito para novo gabarito"
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar gabaritos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao buscar gabaritos"
        )


@router.put("/{unit_id}/gabarito/{assessment_type}", response_model=SuccessResponse)
async def update_gabarito_result(
    unit_id: str,
    assessment_type: str,
    gabarito_request: SimpleGabaritoRequest,
    request: Request,
    _: None = Depends(rate_limit_gabarito_generation)
):
    """
    Atualizar/regenerar gabarito de assessment específico.
    
    Args:
        unit_id: ID da unidade
        assessment_type: Tipo de assessment a regenerar
        gabarito_request: Flags opcionais (include_explanations, etc)
        
    Returns:
        SuccessResponse com gabarito atualizado
    """
    logger.info(f"🔄 Regenerando gabarito de {assessment_type} para unidade {unit_id}")
    
    # Forçar o assessment_type no request
    gabarito_request.assessment_type = assessment_type
    
    # Reutilizar a lógica do POST
    return await generate_unit_gabarito(unit_id, gabarito_request, request)


@router.delete("/{unit_id}/gabarito/{assessment_type}", response_model=SuccessResponse)
async def delete_gabarito_result(
    unit_id: str,
    assessment_type: str,
    request: Request = None
):
    """
    Remover gabarito específico.
    
    Args:
        unit_id: ID da unidade
        assessment_type: Tipo de assessment a remover
        
    Returns:
        SuccessResponse confirmando remoção
    """
    logger.info(f"🗑️ Removendo gabarito de {assessment_type} para unidade {unit_id}")
    
    try:
        # Buscar unidade
        unit = await hierarchical_db.get_unit(unit_id)
        
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # Obter solve_assessments atual (onde gabaritos são armazenados)
        gabarito_results = unit.solve_assessments or {}
        
        if assessment_type not in gabarito_results:
            raise HTTPException(
                status_code=404,
                detail=f"Gabarito para '{assessment_type}' não encontrado"
            )
        
        # Remover o gabarito específico
        del gabarito_results[assessment_type]
        
        # Atualizar no banco
        await hierarchical_db.update_unit_content(unit_id, "solve_assessments", gabarito_results)
        
        return SuccessResponse(
            data={
                "removed_assessment": assessment_type,
                "remaining_gabaritos": list(gabarito_results.keys()),
                "unit_id": unit_id
            },
            message=f"Gabarito de '{assessment_type}' removido com sucesso",
            hierarchy_info={
                "unit_id": unit_id,
                "course_id": unit.course_id,
                "book_id": unit.book_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover gabarito: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao remover gabarito"
        )


async def _save_gabarito_result_to_unit(
    unit_id: str, 
    assessment_type: str, 
    gabarito_result: AssessmentSolution
):
    """Salvar resultado do gabarito no campo solve_assessments da unidade."""
    try:
        # Buscar solve_assessments atual
        unit = await hierarchical_db.get_unit(unit_id)
        current_gabarito_results = unit.solve_assessments or {}
        
        # Adicionar novo gabarito (com serialização JSON apropriada)
        current_gabarito_results[assessment_type] = gabarito_result.model_dump(mode='json')
        
        # Atualizar no banco
        await hierarchical_db.update_unit_content(unit_id, "solve_assessments", current_gabarito_results)
        
        logger.info(f"✅ Gabarito salvo para {assessment_type} na unidade {unit_id}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar gabarito: {str(e)}")
        raise


@router.get("/health", response_model=SuccessResponse)
async def get_gabarito_service_health():
    """Health check do serviço de geração de gabaritos."""
    service_status = solve_service.get_service_status()
    
    return SuccessResponse(
        data=service_status,
        message="Serviço de geração de gabaritos ativo e funcionando"
    )


# =============================================================================
# DEPRECATED ENDPOINTS - MANTER PARA BACKWARD COMPATIBILITY
# =============================================================================

@router.post(
    "/{unit_id}/solve_assessments", 
    response_model=SuccessResponse,
    summary="[DEPRECATED] Use /generate_gabarito instead",
    description="DEPRECATED: This endpoint generates gabaritos, not student corrections. Use /generate_gabarito for clarity.",
    operation_id="solve_unit_assessments_deprecated",
    deprecated=True
)
async def solve_unit_assessments_deprecated(
    unit_id: str,
    solve_request: SimpleGabaritoRequest,  # Changed to match new model
    request: Request,
    _: None = Depends(rate_limit_gabarito_generation)
):
    """
    DEPRECATED: Mantido apenas para compatibilidade.
    Redireciona para generate_unit_gabarito internamente.
    """
    logger.warning(f"⚠️ Uso de endpoint DEPRECATED: /solve_assessments. Use /generate_gabarito")
    return await generate_unit_gabarito(unit_id, solve_request, request)


@router.get(
    "/{unit_id}/solve_assessments", 
    response_model=SuccessResponse,
    summary="[DEPRECATED] Use /gabaritos instead",
    description="DEPRECATED: This endpoint returns gabaritos, not correction results. Use /gabaritos for clarity.",
    operation_id="get_solve_assessments_results_deprecated",
    deprecated=True
)
async def get_solve_assessments_results_deprecated(
    unit_id: str,
    assessment_type: Optional[str] = None,
    request: Request = None
):
    """
    DEPRECATED: Mantido apenas para compatibilidade.
    Redireciona para get_unit_gabaritos internamente.
    """
    logger.warning(f"⚠️ Uso de endpoint DEPRECATED: GET /solve_assessments. Use /gabaritos")
    return await get_unit_gabaritos(unit_id, assessment_type, request)