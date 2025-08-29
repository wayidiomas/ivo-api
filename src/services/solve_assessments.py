# src/services/solve_assessments.py
"""
Serviço para geração de gabaritos de assessments via IA.
Implementa resolução completa dos 7 tipos de atividades do IVO V2 usando GPT-5.
NOVO CONCEITO: Gera gabaritos com enunciado + resposta + explicação (não corrige alunos).
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, ValidationError

from src.core.unit_models import (
    SimpleSolveRequest, SolveAssessmentResult, ItemCorrection,
    ErrorAnalysis, ConstructiveFeedback, PedagogicalNotes,
    # Novos modelos para gabaritos
    SimpleGabaritoRequest, AssessmentSolution, AssessmentItem
)
from src.services.prompt_generator import PromptGeneratorService
from src.services.model_selector import get_llm_config_for_service

logger = logging.getLogger(__name__)


class SolveAssessmentsService:
    """Serviço principal para geração de gabaritos de assessments via IA."""
    
    def __init__(self):
        """Inicializar serviço com GPT-5 e prompt generator."""
        # Configurar LLM para geração de gabaritos (usar GPT-5)
        self.llm_config = get_llm_config_for_service("unit_generation")  # GPT-5 config
        self.llm = ChatOpenAI(**self.llm_config)
        
        # Prompt generator para carregar prompts YAML
        self.prompt_generator = PromptGeneratorService()
        
        logger.info("✅ SolveAssessmentsService inicializado com GPT-5 para geração de gabaritos")

    def _create_gabarito_schema(self) -> Dict[str, Any]:
        """Schema para structured output da geração de gabarito."""
        return {
            "title": "AssessmentSolution",
            "description": "Complete answer key and solution for an assessment",
            "type": "object",
            "properties": {
                "assessment_type": {"type": "string"},
                "assessment_title": {"type": "string"},
                "total_items": {"type": "integer", "minimum": 1},
                "instructions": {"type": "string"},
                "unit_context": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string"},
                            "question_text": {"type": "string"},
                            "correct_answer": {"type": "string"},
                            "explanation": {"type": "string"},
                            "difficulty_level": {
                                "type": "string", 
                                "enum": ["easy", "medium", "hard"],
                                "description": "Difficulty level of this specific item - REQUIRED field"
                            },
                            "skills_tested": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["item_id", "question_text", "correct_answer", "explanation", "difficulty_level"],
                        "additionalProperties": False
                    }
                },
                "skills_overview": {"type": "array", "items": {"type": "string"}},
                "difficulty_distribution": {
                    "type": "object",
                    "properties": {
                        "easy": {"type": "integer", "minimum": 0},
                        "medium": {"type": "integer", "minimum": 0}, 
                        "hard": {"type": "integer", "minimum": 0}
                    }
                },
                "teaching_notes": {"type": "array", "items": {"type": "string"}},
                "ai_model_used": {"type": "string", "default": "gpt-5"}
            },
            "required": [
                "assessment_type", "assessment_title", "total_items", "instructions", 
                "unit_context", "items", "skills_overview", "teaching_notes"
            ],
            "additionalProperties": False
        }

    def _create_solve_assessment_schema(self) -> Dict[str, Any]:
        """Schema para structured output da correção de assessment (LEGADO)."""
        return {
            "title": "SolveAssessmentResult",
            "description": "Schema for comprehensive assessment correction results",
            "type": "object",
            "properties": {
                "total_score": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Total score earned by student"
                },
                "total_possible": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Total possible score"
                },
                "performance_level": {
                    "type": "string",
                    "enum": ["excellent", "good", "satisfactory", "needs_improvement"],
                    "description": "Overall performance level"
                },
                "cefr_demonstration": {
                    "type": "string",
                    "enum": ["above", "at", "below"],
                    "description": "CEFR level demonstration compared to expected"
                },
                "item_corrections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string"},
                            "student_answer": {"type": "string"},
                            "correct_answer": {"type": "string"},
                            "result": {
                                "type": "string",
                                "enum": ["correct", "incorrect", "partially_correct"]
                            },
                            "score_earned": {"type": "integer", "minimum": 0},
                            "score_total": {"type": "integer", "minimum": 1},
                            "feedback": {"type": "string"},
                            "l1_interference": {"type": "string", "nullable": True}
                        },
                        "required": ["item_id", "student_answer", "correct_answer", "result", "score_earned", "score_total", "feedback"],
                        "additionalProperties": False
                    },
                    "description": "Individual item corrections"
                },
                "error_analysis": {
                    "type": "object",
                    "properties": {
                        "most_common_errors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Most frequent error types"
                        },
                        "l1_interference_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Portuguese to English interference patterns"
                        },
                        "recurring_mistakes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Mistakes that repeat across items"
                        },
                        "error_frequency": {
                            "type": "object",
                            "additionalProperties": {"type": "integer"},
                            "description": "Frequency count of each error type"
                        }
                    },
                    "required": ["most_common_errors", "l1_interference_patterns", "recurring_mistakes", "error_frequency"],
                    "additionalProperties": False
                },
                "constructive_feedback": {
                    "type": "object",
                    "properties": {
                        "strengths_demonstrated": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Positive aspects identified"
                        },
                        "areas_for_improvement": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific areas needing work"
                        },
                        "study_recommendations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Targeted study suggestions"
                        },
                        "next_steps": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Next learning steps"
                        }
                    },
                    "required": ["strengths_demonstrated", "areas_for_improvement", "study_recommendations", "next_steps"],
                    "additionalProperties": False
                },
                "pedagogical_notes": {
                    "type": "object",
                    "properties": {
                        "class_performance_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Patterns observed for class teaching"
                        },
                        "remedial_activities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Suggested remedial activities"
                        },
                        "differentiation_needed": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Necessary adaptations"
                        },
                        "followup_assessments": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Follow-up assessment ideas"
                        }
                    },
                    "required": ["class_performance_patterns", "remedial_activities", "differentiation_needed", "followup_assessments"],
                    "additionalProperties": False
                },
                "assessment_type": {"type": "string"},
                "assessment_title": {"type": "string"},
                "unit_context": {
                    "type": "object",
                    "additionalProperties": True,
                    "description": "Unit context information"
                },
                "accuracy_percentage": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 100.0,
                    "description": "Percentage of correct answers"
                },
                "ai_model_used": {"type": "string", "default": "gpt-5"}
            },
            "required": [
                "total_score", "total_possible", "performance_level", "cefr_demonstration",
                "item_corrections", "error_analysis", "constructive_feedback", "pedagogical_notes",
                "assessment_type", "assessment_title", "accuracy_percentage"
            ],
            "additionalProperties": False
        }

    async def generate_gabarito(
        self,
        unit: Any,  # Objeto Unit completo
        assessment_type: str,
        include_explanations: bool = True,
        difficulty_analysis: bool = True
    ) -> AssessmentSolution:
        """
        Gerar gabarito completo para assessment - NOVA FUNCIONALIDADE.
        
        Args:
            unit: Objeto Unit completo do banco
            assessment_type: Tipo específico de assessment 
            include_explanations: Incluir explicações detalhadas
            difficulty_analysis: Incluir análise de dificuldade
            
        Returns:
            AssessmentSolution: Gabarito completo com enunciado + resposta + explicação
        """
        start_time = time.time()
        
        logger.info(f"🎯 Gerando gabarito para {assessment_type} via GPT-5")
        
        try:
            # 1. Extrair assessment específico do JSONB
            target_assessment = self._extract_target_assessment(unit.assessments, assessment_type)
            
            # 2. Gerar prompt para gabarito
            gabarito_prompt = await self._generate_gabarito_prompt(
                unit=unit,
                target_assessment=target_assessment,
                assessment_type=assessment_type,
                include_explanations=include_explanations,
                difficulty_analysis=difficulty_analysis
            )
            
            # 3. Geração via GPT-5 com structured output
            gabarito_result = await self._generate_with_structured_output(gabarito_prompt)
            
            # 4. Construir resultado final
            processing_time = time.time() - start_time
            
            result = AssessmentSolution(
                **gabarito_result,
                solution_timestamp=datetime.now(),
                processing_time=processing_time
            )
            
            logger.info(f"✅ Gabarito gerado em {processing_time:.2f}s - {result.total_items} items resolvidos")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de gabarito: {str(e)}")
            raise

    async def _generate_gabarito_prompt(
        self,
        unit: Any,
        target_assessment: Dict[str, Any],
        assessment_type: str,
        include_explanations: bool = True,
        difficulty_analysis: bool = True
    ) -> str:
        """Gerar prompt para gabarito usando novo template."""
        try:
            # Dados da unidade para contexto
            unit_context_data = {
                "course_name": getattr(unit, 'course_id', ''),
                "book_name": getattr(unit, 'book_id', ''),
                "unit_title": getattr(unit, 'title', ''),
                "unit_id": unit.id,
                "cefr_level": unit.cefr_level.value if hasattr(unit.cefr_level, 'value') else str(unit.cefr_level),
                "unit_type": unit.unit_type.value if hasattr(unit.unit_type, 'value') else str(unit.unit_type),
                "unit_context": getattr(unit, 'context', ''),
                "main_aim": getattr(unit, 'main_aim', ''),
                "subsidiary_aims": getattr(unit, 'subsidiary_aims', []),
                "vocabulary_data": unit.vocabulary or {},
                "sentences_data": unit.sentences or {},
                "tips_data": unit.tips or {},
                "grammar_data": unit.grammar or {},
                "assessment_type": assessment_type,
                "assessment_title": target_assessment.get('title', ''),
                "assessment_instructions": target_assessment.get('instructions', ''),
                "assessment_content": target_assessment.get('content', {})
            }
            
            # Usar o prompt generator para carregar o template de gabarito
            prompt = await self.prompt_generator.generate_gabarito_prompt(**unit_context_data)
            
            return prompt
            
        except Exception as e:
            logger.error(f"Erro ao gerar prompt de gabarito: {e}")
            # Fallback simples
            return f"""
            GERAÇÃO DE GABARITO:
            - Assessment: {assessment_type}
            - Unidade: {unit.title if hasattr(unit, 'title') else 'N/A'}
            - Nível: {unit.cefr_level}
            
            Dados do Assessment: {json.dumps(target_assessment, indent=2)}
            
            Por favor, gere um gabarito completo com enunciado, respostas corretas e explicações detalhadas.
            """

    async def _generate_with_structured_output(self, prompt: str) -> Dict[str, Any]:
        """Executar geração de gabarito com structured output."""
        try:
            # Usar structured output para garantir formato JSON
            schema = self._create_gabarito_schema()
            structured_llm = self.llm.with_structured_output(schema)
            
            logger.info("🤖 Gerando gabarito via GPT-5 com structured output...")
            
            result = await structured_llm.ainvoke([
                SystemMessage(content="You are an expert assessment solver generating complete answer keys."),
                HumanMessage(content=prompt)
            ])
            
            logger.info("✅ Gabarito GPT-5 gerado com structured output")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na geração com structured output: {e}")
            raise

    async def solve_assessment_simplified(
        self, 
        unit: Any,  # Objeto Unit completo
        assessment_type: str,
        student_answers: Optional[Dict[str, Any]] = None,
        student_context: Optional[str] = None
    ) -> SolveAssessmentResult:
        """
        Corrigir assessment SIMPLIFICADO - IA processa dados crus do banco.
        
        Args:
            unit: Objeto Unit completo do banco com todos os campos
            assessment_type: Tipo específico de assessment para corrigir
            student_answers: Respostas dos alunos (opcional, do campo student_answers)
            student_context: Contexto adicional do estudante
            
        Returns:
            SolveAssessmentResult: Resultado estruturado da correção
        """
        start_time = time.time()
        
        logger.info(f"🔍 Correção SIMPLIFICADA de {assessment_type} via GPT-5 (dados crus)")
        
        try:
            # 1. Extrair assessment específico do JSONB
            target_assessment = self._extract_target_assessment(unit.assessments, assessment_type)
            
            # 2. Gerar prompt SIMPLIFICADO - IA processa dados complexos
            correction_prompt = await self._generate_simplified_prompt(
                unit=unit,
                target_assessment=target_assessment,
                assessment_type=assessment_type,
                student_answers=student_answers,
                student_context=student_context
            )
            
            # 3. Correção via GPT-5 com structured output
            correction_result = await self._correct_with_structured_output(correction_prompt)
            
            # 4. Construir resultado final
            processing_time = time.time() - start_time
            
            result = SolveAssessmentResult(
                **correction_result,
                correction_timestamp=datetime.now(),
                completion_time=processing_time
            )
            
            logger.info(f"✅ Correção concluída em {processing_time:.2f}s - Score: {result.total_score}/{result.total_possible}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na correção de assessment: {str(e)}")
            raise

    def _prepare_unit_context(self, unit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Preparar contexto da unidade para correção."""
        return {
            "course_name": unit_data.get("course_name", ""),
            "book_name": unit_data.get("book_name", ""),
            "unit_name": unit_data.get("name", ""),
            "cefr_level": unit_data.get("cefr_level", "A2"),
            "unit_type": unit_data.get("unit_type", "lexical_unit"),
            "unit_context": unit_data.get("context", ""),
            "vocabulary_items": self._extract_vocabulary_sample(unit_data.get("vocabulary", {})),
            "sentences_sample": self._extract_sentences_sample(unit_data.get("sentences", {})),
            "strategy_info": self._extract_strategy_info(unit_data),
            "learning_objectives": self._extract_learning_objectives(unit_data)
        }

    def _extract_vocabulary_sample(self, vocab_data: Dict[str, Any]) -> List[str]:
        """Extrair amostra do vocabulário para contexto."""
        if not vocab_data or "items" not in vocab_data:
            return []
        
        # Pegar top 10 palavras para contexto
        vocab_items = vocab_data.get("items", [])[:10]
        return [f"{item.get('word', '')}: {item.get('definition', '')}" for item in vocab_items]

    def _extract_sentences_sample(self, sentences_data: Dict[str, Any]) -> List[str]:
        """Extrair amostra de sentences para contexto."""
        if not sentences_data or "sentences" not in sentences_data:
            return []
        
        sentences = sentences_data.get("sentences", [])[:5]
        return [sentence.get("text", "") for sentence in sentences]

    def _extract_strategy_info(self, unit_data: Dict[str, Any]) -> str:
        """Extrair informação da estratégia aplicada."""
        if unit_data.get("tips"):
            tips = unit_data["tips"]
            return f"TIPS - {tips.get('strategy', '')}: {tips.get('title', '')}"
        elif unit_data.get("grammar"):
            grammar = unit_data["grammar"]
            return f"GRAMMAR - {grammar.get('strategy', '')}: {grammar.get('grammar_point', '')}"
        return "No strategy information available"

    def _extract_learning_objectives(self, unit_data: Dict[str, Any]) -> List[str]:
        """Extrair objetivos de aprendizagem."""
        objectives = []
        
        if unit_data.get("main_aim"):
            objectives.append(f"Main: {unit_data['main_aim']}")
            
        if unit_data.get("subsidiary_aims"):
            for aim in unit_data["subsidiary_aims"][:3]:  # Top 3
                objectives.append(f"Subsidiary: {aim}")
                
        return objectives

    def _extract_assessment_info(self, assessment_data: Dict[str, Any], assessment_type: str) -> Dict[str, Any]:
        """Extrair informações do assessment a ser corrigido."""
        # Buscar o assessment específico nas atividades
        activities = assessment_data.get("activities", [])
        target_activity = None
        
        for activity in activities:
            if activity.get("type") == assessment_type:
                target_activity = activity
                break
        
        if not target_activity:
            raise ValueError(f"Assessment type '{assessment_type}' not found in unit")
        
        return {
            "assessment_type": assessment_type,
            "assessment_title": target_activity.get("title", ""),
            "assessment_instructions": target_activity.get("instructions", ""),
            "assessment_content": target_activity.get("content", {}),
            "correct_answers": target_activity.get("answer_key", {})
        }

    async def _generate_correction_prompt(
        self,
        unit_context: Dict[str, Any],
        assessment_info: Dict[str, Any],
        solve_request: Any
    ) -> List[Any]:
        """Gerar prompt contextual para correção usando prompt generator."""
        try:
            # Usar o prompt generator para gerar prompt contextual
            prompt_messages = await self.prompt_generator.generate_professor_solving_prompt(
                **unit_context,
                **assessment_info,
                student_answers=solve_request.student_answers,
                student_name=solve_request.student_name or "Student",
                additional_context=solve_request.additional_context or ""
            )
            
            return prompt_messages
            
        except Exception as e:
            logger.error(f"Erro ao gerar prompt: {e}")
            # Fallback para prompt básico
            return self._generate_fallback_prompt(unit_context, assessment_info, solve_request)

    def _generate_fallback_prompt(
        self,
        unit_context: Dict[str, Any],
        assessment_info: Dict[str, Any],
        solve_request: Any
    ) -> List[Any]:
        """Prompt de fallback caso o prompt generator falhe."""
        system_prompt = """You are an expert English teacher correcting student assessments.
        Provide detailed, constructive feedback focusing on learning improvement."""
        
        user_prompt = f"""
        UNIT: {unit_context.get('unit_name', '')} ({unit_context.get('cefr_level', 'A2')})
        ASSESSMENT: {assessment_info.get('assessment_type', '')} - {assessment_info.get('assessment_title', '')}
        
        STUDENT ANSWERS: {json.dumps(solve_request.student_answers, indent=2)}
        CORRECT ANSWERS: {json.dumps(assessment_info.get('correct_answers', {}), indent=2)}
        
        Please provide a comprehensive correction with scoring, feedback, and recommendations.
        """
        
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

    async def _correct_with_structured_output(self, prompt_messages: List[Any]) -> Dict[str, Any]:
        """Executar correção com structured output."""
        try:
            # Usar structured output para garantir formato JSON
            schema = self._create_solve_assessment_schema()
            structured_llm = self.llm.with_structured_output(schema)
            
            logger.info("🤖 Corrigindo assessment via GPT-5 com structured output...")
            
            result = await structured_llm.ainvoke(prompt_messages)
            
            logger.info("✅ Correção GPT-5 bem-sucedida com structured output")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na correção com structured output: {e}")
            # Fallback sem structured output
            return await self._correct_fallback(prompt_messages)

    async def _correct_fallback(self, prompt_messages: List[Any]) -> Dict[str, Any]:
        """Fallback de correção sem structured output."""
        logger.info("🔄 Usando fallback sem structured output...")
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            
            # Tentar extrair JSON da resposta
            content = response.content
            
            # Buscar por JSON na resposta
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                logger.info("✅ Fallback correction successful")
                return result
            else:
                raise ValueError("No JSON found in fallback response")
                
        except Exception as fallback_error:
            logger.error(f"❌ Fallback correction failed: {fallback_error}")
            
            # Último recurso: resultado básico
            return self._create_basic_correction_result()

    def _create_basic_correction_result(self) -> Dict[str, Any]:
        """Criar resultado básico quando tudo falhar."""
        return {
            "total_score": 0,
            "total_possible": 1,
            "performance_level": "needs_improvement",
            "cefr_demonstration": "below",
            "item_corrections": [{
                "item_id": "error",
                "student_answer": "Error processing",
                "correct_answer": "Error processing", 
                "result": "incorrect",
                "score_earned": 0,
                "score_total": 1,
                "feedback": "Error occurred during correction processing"
            }],
            "error_analysis": {
                "most_common_errors": ["processing_error"],
                "l1_interference_patterns": [],
                "recurring_mistakes": [],
                "error_frequency": {"processing_error": 1}
            },
            "constructive_feedback": {
                "strengths_demonstrated": [],
                "areas_for_improvement": ["Contact support for assessment correction"],
                "study_recommendations": [],
                "next_steps": ["Try again later"]
            },
            "pedagogical_notes": {
                "class_performance_patterns": ["System error occurred"],
                "remedial_activities": [],
                "differentiation_needed": [],
                "followup_assessments": []
            },
            "assessment_type": "error",
            "assessment_title": "Error",
            "accuracy_percentage": 0.0,
            "ai_model_used": "fallback"
        }

    def _extract_target_assessment(self, assessments: Dict[str, Any], assessment_type: str) -> Dict[str, Any]:
        """Extrair assessment específico do JSONB."""
        try:
            activities = assessments.get("activities", [])
            for activity in activities:
                if activity.get("type") == assessment_type:
                    return activity
            
            logger.warning(f"Assessment '{assessment_type}' não encontrado")
            return {}
        except Exception as e:
            logger.error(f"Erro ao extrair assessment: {e}")
            return {}

    async def _generate_simplified_prompt(
        self,
        unit: Any,
        target_assessment: Dict[str, Any],
        assessment_type: str,
        student_answers: Optional[Dict[str, Any]] = None,
        student_context: Optional[str] = None
    ) -> str:
        """Gerar prompt simplificado - IA processa dados crus."""
        
        try:
            # Dados crus da unidade para a IA processar
            unit_raw_data = {
                "id": unit.id,
                "title": unit.title,
                "main_aim": unit.main_aim,
                "subsidiary_aims": unit.subsidiary_aims,
                "context": unit.context,
                "cefr_level": unit.cefr_level.value if hasattr(unit.cefr_level, 'value') else str(unit.cefr_level),
                "unit_type": unit.unit_type.value if hasattr(unit.unit_type, 'value') else str(unit.unit_type),
                "vocabulary": unit.vocabulary,
                "sentences": unit.sentences,
                "tips": unit.tips,
                "grammar": unit.grammar,
                "course_id": unit.course_id if unit.course_id else "",
                "book_id": unit.book_id if unit.book_id else ""
            }
            
            # Usar prompt generator com dados crus
            prompt = await self.prompt_generator.generate_professor_solving_prompt(
                unit_data=unit_raw_data,
                assessment_data=target_assessment,
                assessment_type=assessment_type,
                student_answers=student_answers,
                student_context=student_context or "No additional context provided"
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Erro ao gerar prompt simplificado: {e}")
            return f"""
            CORRECTION TASK:
            - Assessment Type: {assessment_type}
            - Unit: {unit.title if hasattr(unit, 'title') else 'Unknown'}
            - Level: {unit.cefr_level}
            
            Raw Assessment Data: {json.dumps(target_assessment, indent=2)}
            Student Answers: {json.dumps(student_answers or {}, indent=2)}
            
            Please provide structured correction with scores, feedback, and analysis.
            """

    def get_service_status(self) -> Dict[str, Any]:
        """Status do serviço de correção."""
        return {
            "service": "SolveAssessmentsService",
            "status": "active",
            "model_used": self.llm_config.get("model", "gpt-5"),
            "supported_assessments": [
                "cloze_test", "gap_fill", "reordering", "transformation",
                "multiple_choice", "true_false", "matching"
            ],
            "features": [
                "simplified_api_interface",
                "raw_data_processing",
                "structured_output_correction",
                "l1_interference_detection",
                "constructive_feedback",
                "pedagogical_notes"
            ]
        }

    # =============================================================================
    # NOVO MÉTODO PRINCIPAL PARA GERAÇÃO DE GABARITOS
    # =============================================================================

    async def generate_gabarito(
        self, 
        unit: Any, 
        assessment_type: str,
        include_explanations: bool = True,
        difficulty_analysis: bool = True
    ) -> AssessmentSolution:
        """
        Gerar gabarito completo para um assessment específico.
        
        Args:
            unit: Objeto Unit completo do banco
            assessment_type: Tipo do assessment 
            include_explanations: Incluir explicações detalhadas
            difficulty_analysis: Incluir análise de dificuldade
            
        Returns:
            AssessmentSolution: Gabarito estruturado completo
        """
        start_time = time.time()
        logger.info(f"🎯 Gerando gabarito para {assessment_type} via GPT-5")
        
        try:
            # 1. Extrair assessment específico
            target_assessment = self._extract_target_assessment(unit.assessments, assessment_type)
            
            # 2. Preparar contexto hierárquico
            hierarchy_context = {
                "course_name": getattr(unit, 'course_name', 'Unknown Course'),
                "book_name": getattr(unit, 'book_name', 'Unknown Book')
            }
            
            # 3. Gerar prompt usando o PromptGeneratorService
            try:
                messages = await self.prompt_generator.generate_gabarito_prompt(
                    unit_data=unit.__dict__,
                    assessment_data=target_assessment,
                    assessment_type=assessment_type,
                    hierarchy_context=hierarchy_context
                )
            except Exception as prompt_error:
                logger.error(f"Erro ao gerar prompt de gabarito: {prompt_error}")
                # Usar fallback direto
                messages = self._generate_gabarito_prompt_fallback(unit, target_assessment, assessment_type)
            
            # 4. Gerar gabarito via GPT-5 com structured output
            logger.info("🤖 Gerando gabarito via GPT-5 com structured output...")
            gabarito_result = await self._generate_with_structured_output(messages)
            
            # 5. Processar resultado
            processing_time = time.time() - start_time
            
            # Adicionar metadados
            gabarito_result['solution_timestamp'] = datetime.now().isoformat()
            gabarito_result['ai_model_used'] = 'gpt-4'
            gabarito_result['processing_time'] = processing_time
            
            # Validar com Pydantic
            result = AssessmentSolution(**gabarito_result)
            
            logger.info(f"✅ Gabarito gerado em {processing_time:.2f}s - {result.total_items} items resolvidos")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de gabarito: {str(e)}")
            raise

    def _generate_gabarito_prompt_fallback(self, unit: Any, assessment_data: Dict[str, Any], assessment_type: str) -> List[Any]:
        """Fallback para geração de prompt se o YAML falhar."""
        from langchain.schema import SystemMessage, HumanMessage
        
        system_prompt = """You are an expert English teacher creating answer keys for assessments. 
        Generate complete solutions with detailed explanations for each item.
        
        CRITICAL: Each item MUST include:
        - item_id: unique identifier (string)
        - question_text: the complete question
        - correct_answer: the accurate solution
        - explanation: detailed pedagogical explanation
        - difficulty_level: MUST be "easy", "medium", or "hard" (REQUIRED)
        - skills_tested: array of skills being evaluated
        """
        
        user_prompt = f"""Generate a complete answer key for this {assessment_type} assessment:
        
        Unit Context: {getattr(unit, 'context', '')}
        Assessment Data: {json.dumps(assessment_data, indent=2)}
        
        IMPORTANT: Every single item must have a difficulty_level field set to "easy", "medium", or "hard"."""
        
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)  
        ]

    async def _generate_with_structured_output(self, messages: List[Any]) -> Dict[str, Any]:
        """Gerar gabarito com structured output."""
        try:
            schema = self._create_gabarito_schema()
            
            response = await self.llm.with_structured_output(schema).ainvoke(messages)
            logger.info("✅ Gabarito GPT-5 gerado com structured output")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro no structured output: {str(e)}")
            raise