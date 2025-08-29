# src/services/pdf_generation.py
"""
Serviço para geração de dados PDF - Professor e Student versions.
Filtragem inteligente de JSONB com omissão de campos vazios.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.core.pdf_models import (
    PDFUnitResponse, PDFHierarchyInfo, PDFVocabularyItem, 
    PDFSentenceItem, PDFQAItem, PDFAssessmentActivity, 
    PDFSolveAssessment, PDFServiceStatus
)
from src.core.enums import UnitType

logger = logging.getLogger(__name__)


class PDFGenerationService:
    """Serviço principal para geração de dados PDF."""
    
    def __init__(self):
        logger.info("✅ PDFGenerationService inicializado")
    
    async def generate_pdf_data(
        self,
        unit: Any,  # Objeto Unit completo
        version: str,  # "professor" ou "student"
        content_sections: Optional[List[str]] = None,
        include_hierarchy: bool = True,
        format_options: Dict[str, Any] = {}
    ) -> PDFUnitResponse:
        """
        Gerar dados para PDF com filtragem inteligente.
        
        Args:
            unit: Objeto Unit completo do banco
            version: "professor" ou "student"
            content_sections: Seções específicas ou None para todas
            include_hierarchy: Incluir info de curso/book
            format_options: Opções adicionais de formatação
        """
        logger.info(f"📄 Gerando dados PDF versão {version} para unidade {unit.id}")
        
        try:
            # 1. Informações básicas da unidade
            unit_info = self._extract_unit_info(unit, version)
            
            # 2. Informações hierárquicas (se solicitado)
            hierarchy_info = None
            if include_hierarchy:
                hierarchy_info = self._extract_hierarchy_info(unit)
            
            # 3. Filtrar conteúdo por versão e tipo de unidade
            filtered_content = await self._filter_content_by_version(
                unit, version, content_sections, format_options
            )
            
            # 4. Montar resposta final
            total_sections = len([k for k, v in filtered_content.items() if v is not None])
            omitted_sections = [k for k, v in filtered_content.items() if v is None]
            
            response = PDFUnitResponse(
                unit_info=unit_info,
                hierarchy_info=hierarchy_info,
                **filtered_content,
                generated_for=version,
                total_sections=total_sections,
                omitted_sections=omitted_sections
            )
            
            logger.info(f"✅ PDF data gerado: {total_sections} seções, {len(omitted_sections)} omitidas")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar PDF data: {str(e)}")
            raise
    
    def _extract_unit_info(self, unit: Any, version: str) -> Dict[str, Any]:
        """Extrair informações básicas da unidade por versão."""
        base_info = {
            "id": unit.id,
            "title": unit.title,
            "context": unit.context,
            "cefr_level": unit.cefr_level.value if hasattr(unit.cefr_level, 'value') else str(unit.cefr_level),
            "sequence_order": unit.sequence_order,
            "unit_type": unit.unit_type.value if hasattr(unit.unit_type, 'value') else str(unit.unit_type)
        }
        
        # Professor version inclui mais campos pedagógicos
        if version == "professor":
            base_info.update({
                "main_aim": unit.main_aim,
                "subsidiary_aims": unit.subsidiary_aims or []
            })
        
        return base_info
    
    def _extract_hierarchy_info(self, unit: Any) -> Optional[PDFHierarchyInfo]:
        """Extrair informações hierárquicas."""
        try:
            return PDFHierarchyInfo(
                unit_id=unit.id,
                unit_title=unit.title or "Untitled Unit",
                sequence_order=unit.sequence_order,
                course_name=unit.course.name if hasattr(unit, 'course') and unit.course else None,
                book_name=unit.book.name if hasattr(unit, 'book') and unit.book else None
            )
        except Exception as e:
            logger.warning(f"Erro ao extrair hierarchy info: {e}")
            return None
    
    async def _filter_content_by_version(
        self,
        unit: Any,
        version: str,
        content_sections: Optional[List[str]],
        format_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filtrar conteúdo por versão com omissão de campos vazios."""
        
        filtered = {}
        
        # Definir seções a processar
        available_sections = ["vocabulary", "sentences", "tips", "grammar", "qa", "assessments", "solve_assessments"]
        sections_to_process = content_sections or available_sections
        
        for section in sections_to_process:
            if section == "vocabulary" and unit.vocabulary:
                filtered["vocabulary"] = self._filter_vocabulary(unit.vocabulary, version, format_options)
            
            elif section == "sentences" and unit.sentences:
                filtered["sentences"] = self._filter_sentences(unit.sentences, version)
            
            elif section == "tips" and unit.tips and self._is_lexical_unit(unit):
                filtered["tips"] = unit.tips  # Completo para unidades lexicais
            
            elif section == "grammar" and unit.grammar and self._is_grammar_unit(unit):
                filtered["grammar"] = unit.grammar  # Completo para unidades gramaticais
            
            elif section == "qa" and unit.qa:
                filtered["qa"] = self._filter_qa(unit.qa, version)
            
            elif section == "assessments" and unit.assessments:
                filtered["assessments"] = self._filter_assessments(unit.assessments, version)
            
            elif section == "solve_assessments" and unit.solve_assessments:
                filtered["solve_assessments"] = self._filter_solve_assessments(unit.solve_assessments, version)
            
            else:
                # Campo vazio ou não aplicável - será omitido (None)
                filtered[section] = None
        
        return filtered
    
    def _filter_vocabulary(self, vocab_data: Dict[str, Any], version: str, format_options: Dict[str, Any]) -> List[PDFVocabularyItem]:
        """Filtrar vocabulário por versão."""
        try:
            items = vocab_data.get("items", [])
            filtered_items = []
            
            for item in items:
                # Campos básicos para ambas versões
                vocab_item_data = {
                    "word": item.get("word", ""),
                    "definition": item.get("definition", ""),
                    "example": item.get("example")
                }
                
                # Fonética importante para ambas versões (ajuste conforme feedback)
                vocab_item_data.update({
                    "phoneme": item.get("phoneme"),
                    "ipa_transcription": item.get("ipa_transcription"),
                    "syllable_count": item.get("syllable_count")
                })
                
                # Campos pedagógicos apenas para professor
                if version == "professor":
                    vocab_item_data.update({
                        "part_of_speech": item.get("part_of_speech"),
                        "difficulty_level": item.get("difficulty_level"),
                        "frequency": item.get("frequency")
                    })
                
                filtered_items.append(PDFVocabularyItem(**vocab_item_data))
            
            return filtered_items if filtered_items else None
            
        except Exception as e:
            logger.warning(f"Erro ao filtrar vocabulary: {e}")
            return None
    
    def _filter_sentences(self, sentences_data: Dict[str, Any], version: str) -> List[PDFSentenceItem]:
        """Filtrar sentences por versão."""
        try:
            items = sentences_data.get("items", [])
            filtered_items = []
            
            for item in items:
                sentence_data = {
                    "text": item.get("text", ""),
                    "context_situation": item.get("context_situation")
                }
                
                # Dados pedagógicos apenas para professor
                if version == "professor":
                    sentence_data.update({
                        "vocabulary_used": item.get("vocabulary_used"),
                        "complexity_level": item.get("complexity_level"),
                        "reinforces_previous": item.get("reinforces_previous")
                    })
                
                filtered_items.append(PDFSentenceItem(**sentence_data))
            
            return filtered_items if filtered_items else None
            
        except Exception as e:
            logger.warning(f"Erro ao filtrar sentences: {e}")
            return None
    
    def _filter_qa(self, qa_data: Dict[str, Any], version: str) -> List[PDFQAItem]:
        """Filtrar Q&A com foco na taxonomia de Bloom."""
        try:
            # Verificar se qa_data é um dicionário válido
            if not isinstance(qa_data, dict):
                logger.warning(f"QA data inválido - esperado dict, recebido {type(qa_data)}")
                return None
            
            questions = qa_data.get("questions", [])
            
            # Verificar se questions é uma lista válida
            if not isinstance(questions, list):
                logger.warning(f"QA questions inválido - esperado list, recebido {type(questions)}")
                return None
            
            filtered_questions = []
            
            for question in questions:
                # Verificar se question é um dicionário
                if not isinstance(question, dict):
                    logger.warning(f"Question item inválido - esperado dict, recebido {type(question)}")
                    continue
                
                qa_item_data = {
                    "question": question.get("question", ""),
                    "answer": question.get("answer", ""),
                    "bloom_level": question.get("bloom_level", "understand")
                }
                
                # Dados pedagógicos apenas para professor
                if version == "professor":
                    qa_item_data.update({
                        "pedagogical_purpose": question.get("pedagogical_purpose"),
                        "follow_up_suggestions": question.get("follow_up_suggestions")
                    })
                
                filtered_questions.append(PDFQAItem(**qa_item_data))
            
            return filtered_questions if filtered_questions else None
            
        except Exception as e:
            logger.warning(f"Erro ao filtrar Q&A: {e}")
            return None
    
    def _filter_assessments(self, assessments_data: Dict[str, Any], version: str) -> List[PDFAssessmentActivity]:
        """Filtrar assessments por versão."""
        try:
            activities = assessments_data.get("activities", [])
            filtered_activities = []
            
            for activity in activities:
                activity_data = {
                    "type": activity.get("type", ""),
                    "title": activity.get("title", ""),
                    "instructions": activity.get("instructions", ""),
                    "questions": activity.get("questions", [])
                }
                
                # Answers apenas para professor
                if version == "professor":
                    activity_data.update({
                        "answers": activity.get("answers"),
                        "pedagogical_rationale": activity.get("pedagogical_rationale")
                    })
                
                filtered_activities.append(PDFAssessmentActivity(**activity_data))
            
            return filtered_activities if filtered_activities else None
            
        except Exception as e:
            logger.warning(f"Erro ao filtrar assessments: {e}")
            return None
    
    def _filter_solve_assessments(self, solve_data: Dict[str, Any], version: str) -> Dict[str, PDFSolveAssessment]:
        """Filtrar correções IA por versão."""
        try:
            filtered_corrections = {}
            
            for assessment_type, correction in solve_data.items():
                correction_data = {
                    "assessment_type": assessment_type,
                    "total_score": correction.get("total_score"),
                    "accuracy_percentage": correction.get("accuracy_percentage"),
                    "performance_level": correction.get("performance_level"),
                    "constructive_feedback": correction.get("constructive_feedback", {})
                }
                
                # Análise completa apenas para professor
                if version == "professor":
                    correction_data.update({
                        "error_analysis": correction.get("error_analysis"),
                        "pedagogical_notes": correction.get("pedagogical_notes")
                    })
                
                filtered_corrections[assessment_type] = PDFSolveAssessment(**correction_data)
            
            return filtered_corrections if filtered_corrections else None
            
        except Exception as e:
            logger.warning(f"Erro ao filtrar solve_assessments: {e}")
            return None
    
    def _is_lexical_unit(self, unit: Any) -> bool:
        """Verificar se é unidade lexical."""
        unit_type = unit.unit_type
        if hasattr(unit_type, 'value'):
            return unit_type.value == "lexical_unit"
        return str(unit_type) == "lexical_unit"
    
    def _is_grammar_unit(self, unit: Any) -> bool:
        """Verificar se é unidade gramatical."""
        unit_type = unit.unit_type  
        if hasattr(unit_type, 'value'):
            return unit_type.value == "grammar_unit"
        return str(unit_type) == "grammar_unit"
    
    def get_service_status(self) -> PDFServiceStatus:
        """Status do serviço PDF."""
        return PDFServiceStatus()