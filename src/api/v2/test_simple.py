# src/api/v2/test_simple.py
"""Router simples para teste sem dependências pesadas."""

from fastapi import APIRouter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/test")
async def test_endpoint():
    """Endpoint de teste simples."""
    return {
        "message": "Test endpoint funcionando!",
        "success": True,
        "module": "test_simple"
    }


@router.get("/courses-simple")
async def list_courses_simple():
    """Endpoint simples para listar cursos sem dependências."""
    return {
        "success": True,
        "data": {
            "courses": [
                {
                    "id": "test-course-1", 
                    "name": "Curso de Teste",
                    "description": "Curso para testar endpoints"
                }
            ]
        },
        "message": "Cursos listados (versão simples)",
        "total": 1
    }