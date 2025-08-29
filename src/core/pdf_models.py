# src/core/pdf_models.py
"""
Modelos para PDF generation - Professor e Student versions.
Sistema inteligente que omite campos vazios e filtra por tipo de unidade.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from src.core.enums import UnitType, CEFRLevel


class SimplePDFRequest(BaseModel):
    """Request simplificado para PDF generation."""
    
    # Configurações básicas
    version: str = Field(..., description="professor ou student")
    include_hierarchy: bool = Field(default=True, description="Incluir info de curso/book")
    
    # Seções opcionais (se não especificado, inclui todas disponíveis)
    content_sections: Optional[List[str]] = Field(
        default=None, 
        description="Seções específicas: vocabulary, sentences, tips, grammar, qa, assessments, solve_assessments"
    )
    
    # Opções de formato
    format_options: Optional[Dict[str, Any]] = Field(
        default={}, 
        description="Opções como language, include_advanced_phonetics, etc"
    )


class PDFHierarchyInfo(BaseModel):
    """Informações hierárquicas para PDF."""
    unit_id: str
    unit_title: str
    sequence_order: int
    course_name: Optional[str] = None
    book_name: Optional[str] = None


class PDFVocabularyItem(BaseModel):
    """Item de vocabulário otimizado para PDF."""
    word: str
    definition: str
    example: Optional[str] = None
    
    # Fonética (importante para ambas as versões)
    phoneme: Optional[str] = None
    ipa_transcription: Optional[str] = None
    syllable_count: Optional[int] = None
    
    # Campos pedagógicos (apenas professor)
    part_of_speech: Optional[str] = None
    difficulty_level: Optional[str] = None
    frequency: Optional[str] = None


class PDFSentenceItem(BaseModel):
    """Sentence otimizada para PDF."""
    text: str
    
    # Contexto básico (ambas versões)
    context_situation: Optional[str] = None
    
    # Dados pedagógicos (apenas professor)  
    vocabulary_used: Optional[List[str]] = None
    complexity_level: Optional[str] = None
    reinforces_previous: Optional[List[str]] = None


class PDFQAItem(BaseModel):
    """Q&A otimizado - taxonomia de Bloom essencial."""
    question: str
    answer: str
    bloom_level: str  # remember, understand, apply, analyze, evaluate, create
    
    # Apenas para professor
    pedagogical_purpose: Optional[str] = None
    follow_up_suggestions: Optional[List[str]] = None


class PDFAssessmentActivity(BaseModel):
    """Assessment activity para PDF."""
    type: str  # cloze_test, gap_fill, etc
    title: str
    instructions: str
    
    # Content adaptado por versão
    questions: List[Dict[str, Any]]  # Estrutura varia por tipo
    
    # Answers apenas para professor
    answers: Optional[Dict[str, Any]] = None
    pedagogical_rationale: Optional[str] = None


class PDFSolveAssessment(BaseModel):
    """Resultado de correção IA para PDF."""
    assessment_type: str
    total_score: Optional[int] = None
    accuracy_percentage: Optional[float] = None
    performance_level: Optional[str] = None
    
    # Feedback (adaptado por versão)
    constructive_feedback: Dict[str, Any]
    
    # Dados completos apenas para professor
    error_analysis: Optional[Dict[str, Any]] = None
    pedagogical_notes: Optional[Dict[str, Any]] = None


class PDFUnitResponse(BaseModel):
    """Response completa para PDF generation."""
    
    # Informações básicas
    unit_info: Dict[str, Any]
    hierarchy_info: Optional[PDFHierarchyInfo] = None
    
    # Conteúdo filtrado (campos omitidos se vazios)
    vocabulary: Optional[List[PDFVocabularyItem]] = None
    sentences: Optional[List[PDFSentenceItem]] = None
    tips: Optional[Dict[str, Any]] = None         # Completo se lexical_unit
    grammar: Optional[Dict[str, Any]] = None      # Completo se grammar_unit  
    qa: Optional[List[PDFQAItem]] = None
    assessments: Optional[List[PDFAssessmentActivity]] = None
    solve_assessments: Optional[Dict[str, PDFSolveAssessment]] = None
    
    # Metadata
    generated_for: str  # "professor" ou "student"  
    generated_at: datetime = Field(default_factory=datetime.now)
    total_sections: int  # Quantas seções foram incluídas
    omitted_sections: List[str] = Field(default=[])  # Seções omitidas por estarem vazias


class PDFServiceStatus(BaseModel):
    """Status do serviço PDF."""
    service: str = "PDFGenerationService"
    status: str = "active"
    supported_versions: List[str] = ["professor", "student"]
    supported_unit_types: List[str] = ["lexical_unit", "grammar_unit"]
    features: List[str] = [
        "intelligent_field_omission",
        "unit_type_aware_filtering", 
        "bloom_taxonomy_optimization",
        "phonetic_preservation",
        "hierarchical_context"
    ]