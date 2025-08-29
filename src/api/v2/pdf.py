# src/api/v2/pdf.py
"""
Endpoints para geração de dados PDF - Professor e Student versions.
Sistema inteligente com filtragem JSONB e omissão de campos vazios.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional
import logging
import time

from src.services.hierarchical_database import hierarchical_db
from src.services.pdf_generation import PDFGenerationService
from src.core.unit_models import SuccessResponse
from src.core.pdf_models import SimplePDFRequest, PDFUnitResponse
from src.core.audit_logger import (
    audit_logger_instance, AuditEventType, audit_endpoint, extract_unit_info
)
from src.core.rate_limiter import rate_limit_dependency

router = APIRouter(
    prefix="/units",
    tags=["PDF Generation"],
    responses={
        404: {"description": "Unit not found"},
        400: {"description": "Invalid PDF generation parameters"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "PDF generation service error"}
    }
)
logger = logging.getLogger(__name__)

# Instância global do serviço PDF
pdf_service = PDFGenerationService()


async def rate_limit_pdf_generation(request: Request):
    """Rate limiting específico para PDF generation."""
    await rate_limit_dependency(request, "pdf_generation")


@router.post(
    "/{unit_id}/pdf/professor", 
    response_model=SuccessResponse,
    summary="Generate Professor PDF Data",
    description="Generate complete PDF data for teachers with all pedagogical information and analysis.",
    operation_id="generate_professor_pdf_data"
)
async def generate_professor_pdf_data(
    unit_id: str,
    pdf_request: SimplePDFRequest,
    request: Request,
    _: None = Depends(rate_limit_pdf_generation)
):
    """
    **Generate Professor PDF Data - Complete Pedagogical Version**
    
    This endpoint generates comprehensive PDF data for teachers including:
    - Complete vocabulary with phonetics and pedagogical notes
    - Full sentences with context and teaching suggestions
    - Complete tips (lexical units) or grammar (grammar units)
    - Q&A with full Bloom's taxonomy and pedagogical purpose
    - Assessments with answers and rationale
    - AI correction results with detailed analysis
    
    **Key Features:**
    - Unit-type aware (lexical vs grammar)
    - Omits empty fields automatically
    - Includes all pedagogical metadata
    - Hierarchical context (course/book info)
    """
    logger.info(f"📄 Gerando PDF data PROFESSOR para unidade {unit_id}")
    
    try:
        # 1. Buscar unidade completa
        unit = await hierarchical_db.get_unit_with_hierarchy(unit_id)
        
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # 2. Forçar versão professor
        pdf_request.version = "professor"
        
        # 3. Gerar dados PDF
        start_time = time.time()
        
        pdf_data = await pdf_service.generate_pdf_data(
            unit=unit,
            version="professor",
            content_sections=pdf_request.content_sections,
            include_hierarchy=pdf_request.include_hierarchy,
            format_options=pdf_request.format_options or {}
        )
        
        processing_time = time.time() - start_time
        
        # 4. Log de auditoria
        await audit_logger_instance.log_content_generation(
            request=request,
            generation_type="pdf_professor",
            unit_id=unit_id,
            book_id=unit.book_id,
            course_id=unit.course_id,
            content_stats={
                "sections_included": pdf_data.total_sections,
                "sections_omitted": len(pdf_data.omitted_sections),
                "unit_type": pdf_data.unit_info.get("unit_type"),
                "include_hierarchy": pdf_request.include_hierarchy
            },
            processing_time=processing_time,
            success=True
        )
        
        return SuccessResponse(
            data={
                "pdf_data": pdf_data.model_dump(),
                "generation_stats": {
                    "version": "professor",
                    "unit_type": pdf_data.unit_info.get("unit_type"),
                    "sections_included": pdf_data.total_sections,
                    "sections_omitted": pdf_data.omitted_sections,
                    "processing_time": f"{processing_time:.2f}s",
                    "has_hierarchy": pdf_data.hierarchy_info is not None
                }
            },
            message=f"PDF data para professor gerado - {pdf_data.total_sections} seções incluídas",
            hierarchy_info={
                "course_id": unit.course_id,
                "book_id": unit.book_id,
                "unit_id": unit_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar PDF data professor para unidade {unit_id}: {str(e)}")
        
        # Log de erro
        await audit_logger_instance.log_content_generation(
            request=request,
            generation_type="pdf_professor",
            unit_id=unit_id,
            book_id="unknown",
            course_id="unknown",
            content_stats={
                "error": str(e)
            },
            success=False
        )
        
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao gerar PDF data para professor"
        )


@router.post(
    "/{unit_id}/pdf/student", 
    response_model=SuccessResponse,
    summary="Generate Student PDF Data",
    description="Generate student-focused PDF data with essential content and phonetics, excluding pedagogical analysis.",
    operation_id="generate_student_pdf_data"
)
async def generate_student_pdf_data(
    unit_id: str,
    pdf_request: SimplePDFRequest,
    request: Request,
    _: None = Depends(rate_limit_pdf_generation)
):
    """
    **Generate Student PDF Data - Essential Learning Version**
    
    This endpoint generates student-focused PDF data including:
    - Vocabulary with phonetics (important for students)
    - Sentences with basic context
    - Complete tips (lexical) or grammar (grammar units)
    - Q&A with essential Bloom's taxonomy levels
    - Assessment questions (without answers)
    - AI feedback (constructive only)
    
    **Key Features:**
    - Student-safe content filtering
    - Phonetics included for pronunciation
    - Unit-type aware filtering
    - Omits empty fields automatically
    - No pedagogical metadata
    """
    logger.info(f"🎓 Gerando PDF data STUDENT para unidade {unit_id}")
    
    try:
        # 1. Buscar unidade completa
        unit = await hierarchical_db.get_unit_with_hierarchy(unit_id)
        
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unit_id} não encontrada"
            )
        
        # 2. Forçar versão student
        pdf_request.version = "student"
        
        # 3. Gerar dados PDF
        start_time = time.time()
        
        pdf_data = await pdf_service.generate_pdf_data(
            unit=unit,
            version="student",
            content_sections=pdf_request.content_sections,
            include_hierarchy=pdf_request.include_hierarchy,
            format_options=pdf_request.format_options or {}
        )
        
        processing_time = time.time() - start_time
        
        # 4. Log de auditoria
        await audit_logger_instance.log_content_generation(
            request=request,
            generation_type="pdf_student",
            unit_id=unit_id,
            book_id=unit.book_id,
            course_id=unit.course_id,
            content_stats={
                "sections_included": pdf_data.total_sections,
                "sections_omitted": len(pdf_data.omitted_sections),
                "unit_type": pdf_data.unit_info.get("unit_type"),
                "include_hierarchy": pdf_request.include_hierarchy
            },
            processing_time=processing_time,
            success=True
        )
        
        return SuccessResponse(
            data={
                "pdf_data": pdf_data.model_dump(),
                "generation_stats": {
                    "version": "student",
                    "unit_type": pdf_data.unit_info.get("unit_type"),
                    "sections_included": pdf_data.total_sections,
                    "sections_omitted": pdf_data.omitted_sections,
                    "processing_time": f"{processing_time:.2f}s",
                    "has_hierarchy": pdf_data.hierarchy_info is not None
                }
            },
            message=f"PDF data para aluno gerado - {pdf_data.total_sections} seções incluídas",
            hierarchy_info={
                "course_id": unit.course_id,
                "book_id": unit.book_id,
                "unit_id": unit_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar PDF data student para unidade {unit_id}: {str(e)}")
        
        # Log de erro
        await audit_logger_instance.log_content_generation(
            request=request,
            generation_type="pdf_student",
            unit_id=unit_id,
            book_id="unknown",
            course_id="unknown",
            content_stats={
                "error": str(e)
            },
            success=False
        )
        
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao gerar PDF data para aluno"
        )


@router.get("/health/pdf", response_model=SuccessResponse)
async def get_pdf_service_health():
    """Health check do serviço PDF."""
    service_status = pdf_service.get_service_status()
    
    return SuccessResponse(
        data=service_status.model_dump(),
        message="Serviço PDF ativo e funcionando"
    )