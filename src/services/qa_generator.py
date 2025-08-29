# src/services/qa_generator.py
"""
Serviço de geração de perguntas e respostas pedagógicas.
Implementação baseada na Taxonomia de Bloom com foco em fonética e vocabulário.
Atualizado para LangChain 0.3 e Pydantic 2.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, ValidationError, Field, ConfigDict

from src.core.unit_models import QASection, QAGenerationRequest
from src.core.enums import CEFRLevel, LanguageVariant, UnitType
from config.models import get_openai_config, load_model_configs

logger = logging.getLogger(__name__)



class QAGeneratorService:
    """Serviço principal para geração de Q&A pedagógico."""
    
    def __init__(self):
        """Inicializar serviço com configurações."""
        self.openai_config = get_openai_config()
        self.model_configs = load_model_configs()
        
        # NOVO: Usar model_selector para obter o modelo correto
        from src.services.model_selector import get_llm_config_for_service
        from src.services.prompt_generator import PromptGeneratorService
        
        # Obter configuração específica para qa_generator (TIER-5: o3-mini)
        llm_config = get_llm_config_for_service("qa_generator")
        self.llm = ChatOpenAI(**llm_config)
        
        # Inicializar prompt generator para usar templates YAML
        self.prompt_generator = PromptGeneratorService()
        
        # Cache simples em memória
        self._memory_cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, float] = {}
        self._max_cache_size = 50
        
        logger.info("✅ QAGeneratorService inicializado com LangChain 0.3")
    
    async def generate_qa_for_unit(
        self,
        qa_request: QAGenerationRequest,
        unit_data: Dict[str, Any],
        content_data: Dict[str, Any],
        hierarchy_context: Dict[str, Any],
        pedagogical_context: Dict[str, Any]
    ) -> QASection:
        """
        Gerar Q&A pedagógico para uma unidade.
        
        Args:
            qa_request: Request com configurações de geração
            unit_data: Dados da unidade (título, contexto, CEFR, etc.)
            content_data: Dados de conteúdo (vocabulário, sentences, etc.)
            hierarchy_context: Contexto hierárquico (curso, book, sequência)
            pedagogical_context: Contexto pedagógico (objetivos, progressão)
            
        Returns:
            QASection completa com perguntas, respostas e notas pedagógicas
        """
        try:
            start_time = time.time()
            
            # Debug para identificar o problema
            if not isinstance(unit_data, dict):
                logger.error(f"ERROR - unit_data is not dict: type={type(unit_data)}, value={str(unit_data)[:200]}")
                raise ValueError("unit_data deve ser dict")
            
            logger.info(f"🎓 Gerando Q&A pedagógico para unidade {unit_data.get('title', 'Unknown')}")
            logger.info(f"Configurações: target_count={qa_request.target_count}, bloom_levels={qa_request.bloom_levels}")
            
            # Criar objeto request interno para compatibilidade com funções auxiliares
            request_data = {
                "unit_data": unit_data,
                "content_data": content_data,
                "hierarchy_context": hierarchy_context,
                "pedagogical_context": pedagogical_context,
                "target_question_count": qa_request.target_count
            }
            
            # 1. Construir contexto pedagógico enriquecido
            enriched_context = await self._build_pedagogical_context(
                unit_data, content_data, hierarchy_context, pedagogical_context, qa_request
            )
            
            # 2. Gerar prompt baseado na Taxonomia de Bloom
            qa_prompt = await self._build_bloom_taxonomy_prompt(enriched_context)
            
            # 3. Gerar Q&A via LLM
            raw_qa = await self._generate_qa_llm(qa_prompt)
            
            # 4. Processar e estruturar Q&A
            structured_qa = await self._process_and_structure_qa(raw_qa, enriched_context)
            
            # 5. Enriquecer com componentes fonéticos
            enriched_qa = await self._enrich_with_pronunciation_questions(
                structured_qa, content_data
            )
            
            # 6. Adicionar notas pedagógicas
            final_qa = await self._add_pedagogical_notes(enriched_qa, enriched_context)
            
            # 6.5. Garantir target_count exato
            final_qa = await self._ensure_exact_target_count(final_qa, qa_request.target_count)
            
            # 6.6. NOVO: Garantir campos obrigatórios (correção do erro 'difficulty_progression')
            final_qa = self._ensure_required_qa_fields(final_qa)
            
            # 7. Construir QASection
            qa_section = QASection(
                questions=final_qa["questions"],
                answers=final_qa["answers"],
                pedagogical_notes=final_qa["pedagogical_notes"],
                difficulty_progression=final_qa["difficulty_progression"],
                vocabulary_integration=final_qa["vocabulary_integration"],
                cognitive_levels=final_qa["cognitive_levels"],
                pronunciation_questions=final_qa["pronunciation_questions"],
                phonetic_awareness=final_qa["phonetic_awareness"]
            )
            
            generation_time = time.time() - start_time
            
            logger.info(
                f"✅ Q&A gerado: {len(qa_section.questions)} perguntas em {generation_time:.2f}s"
            )
            
            return qa_section
            
        except ValidationError as e:
            logger.error(f"❌ Erro de validação Pydantic 2: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro na geração de Q&A: {str(e)}")
            raise
    
    async def _build_pedagogical_context(
        self,
        unit_data: Dict[str, Any],
        content_data: Dict[str, Any],
        hierarchy_context: Dict[str, Any],
        pedagogical_context: Dict[str, Any],
        qa_request: QAGenerationRequest
    ) -> Dict[str, Any]:
        """Construir contexto pedagógico enriquecido."""
        
        # Usar parâmetros diretos em vez do request
        # hierarchy_context e pedagogical_context já vêm como parâmetros
        
        # Extrair vocabulário da unidade
        vocabulary_items = []
        if content_data.get("vocabulary") and content_data["vocabulary"].get("items"):
            vocabulary_items = content_data["vocabulary"]["items"]
        
        vocabulary_words = [item.get("word", "") for item in vocabulary_items]
        
        # Extrair sentences
        sentences = []
        if content_data.get("sentences") and content_data["sentences"].get("sentences"):
            sentences = [s.get("text", "") for s in content_data["sentences"]["sentences"]]
        
        # Extrair estratégias aplicadas
        strategy_info = ""
        if content_data.get("tips"):
            strategy_info = f"TIPS Strategy: {content_data['tips'].get('strategy', 'unknown')} - {content_data['tips'].get('title', '')}"
        elif content_data.get("grammar"):
            strategy_info = f"GRAMMAR Strategy: {content_data['grammar'].get('strategy', 'unknown')} - {content_data['grammar'].get('grammar_point', '')}"
        
        # Objetivos de aprendizagem
        learning_objectives = pedagogical_context.get("learning_objectives", [])
        
        enriched_context = {
            "unit_info": {
                "title": unit_data.get("title", ""),
                "context": unit_data.get("context", ""),
                "cefr_level": unit_data.get("cefr_level", "A2"),
                "unit_type": unit_data.get("unit_type", "lexical_unit"),
                "language_variant": unit_data.get("language_variant", "american_english"),
                "main_aim": unit_data.get("main_aim", ""),
                "subsidiary_aims": unit_data.get("subsidiary_aims", [])
            },
            "content_analysis": {
                "vocabulary_count": len(vocabulary_words),
                "vocabulary_words": vocabulary_words[:15],  # Top 15 para contexto
                "sentences_count": len(sentences),
                "sample_sentences": sentences[:3],  # Primeiras 3 para referência
                "strategy_applied": strategy_info,
                "has_assessments": bool(content_data.get("assessments"))
            },
            "hierarchy_info": {
                "course_name": hierarchy_context.get("course_name", ""),
                "book_name": hierarchy_context.get("book_name", ""),
                "sequence_order": hierarchy_context.get("sequence_order", 1),
                "target_level": hierarchy_context.get("target_level", unit_data.get("cefr_level"))
            },
            "pedagogical_goals": {
                "learning_objectives": learning_objectives,
                "progression_level": pedagogical_context.get("progression_level", "intermediate"),
                "phonetic_focus": pedagogical_context.get("phonetic_focus", "general_pronunciation"),
                "taught_vocabulary": pedagogical_context.get("taught_vocabulary", [])[:10],
                "target_question_count": qa_request.target_count
            },
            "bloom_taxonomy_targets": self._determine_bloom_targets(
                unit_data.get("cefr_level", "A2"),
                hierarchy_context.get("sequence_order", 1)
            )
        }
        
        return enriched_context
    
    async def _build_bloom_taxonomy_prompt(self, enriched_context: Dict[str, Any]) -> List[Any]:
        """Construir prompt baseado na Taxonomia de Bloom usando template YAML."""
        
        unit_info = enriched_context["unit_info"]
        content_analysis = enriched_context["content_analysis"]
        pedagogical_goals = enriched_context["pedagogical_goals"]
        
        # Debug logging para identificar o problema
        logger.info(f"DEBUG - unit_info type: {type(unit_info)}")
        logger.info(f"DEBUG - content_analysis type: {type(content_analysis)}")
        logger.info(f"DEBUG - pedagogical_goals type: {type(pedagogical_goals)}")
        
        if isinstance(unit_info, str):
            logger.error(f"ERROR - unit_info is string: {unit_info}")
            raise ValueError("unit_info deve ser dict, não string")
        if isinstance(content_analysis, str):
            logger.error(f"ERROR - content_analysis is string: {content_analysis}")
            raise ValueError("content_analysis deve ser dict, não string")
        if isinstance(pedagogical_goals, str):
            logger.error(f"ERROR - pedagogical_goals is string: {pedagogical_goals}")
            raise ValueError("pedagogical_goals deve ser dict, não string")
        
        # ========================================================================
        # NOVO: RESUMIR CONTEXTO VIA IA PARA REDUZIR TOKENS (mantendo AIM/SUBAIM)
        # ========================================================================
        logger.info("🔄 Resumindo contexto via IA para otimizar Q&A...")
        
        # Preparar dados para resumo (sem AIM - eles vão direto pro prompt)
        unit_data_for_summary = {
            "title": unit_info["title"],
            "context": unit_info["context"],
            "cefr_level": unit_info["cefr_level"],
            "unit_type": unit_info["unit_type"]
        }
        
        # Converter vocabulary_words para formato dict simples
        vocabulary_words = content_analysis.get("vocabulary_words", [])
        vocabulary_items = [{"word": word} for word in vocabulary_words]
        
        content_data_for_summary = {
            "vocabulary": {"items": vocabulary_items},
            "sample_sentences": content_analysis.get("sample_sentences", []),
            "strategy_applied": content_analysis.get("strategy_applied", "")
        }
        
        # RESUMIR via IA o contexto extenso (vocabulário + sentences + estratégias)
        # Criar hierarchy_context básico (sem usar enriched_context que não está disponível)
        hierarchy_context_for_summary = {
            "course_name": "Course",  # Valor padrão - será melhorado no resumo
            "book_name": "Book",      # Valor padrão - será melhorado no resumo
            "sequence_order": 1       # Valor padrão
        }
        
        try:
            summarized_context = await self.prompt_generator.summarize_context_for_qa(
                unit_data=unit_data_for_summary,
                content_data=content_data_for_summary,
                hierarchy_context=hierarchy_context_for_summary
            )
            logger.info(f"✅ Contexto resumido: {len(summarized_context)} caracteres")
        except Exception as e:
            logger.error(f"❌ Erro ao resumir contexto: {e}")
            # Fallback: contexto básico
            summarized_context = f"Unit: {unit_info['title']} | Level: {unit_info['cefr_level']} | Key vocab: {', '.join(vocabulary_words[:6])}"
        
        # Preparar dados para prompt generator (MANTENDO AIM/SUBAIM importantes)
        unit_data_for_prompt = {
            "title": unit_info["title"],
            "context": unit_info["context"],
            "cefr_level": unit_info["cefr_level"],
            "language_variant": unit_info["language_variant"],
            "unit_type": unit_info["unit_type"],
            "main_aim": unit_info.get("main_aim"),          # ✅ MANTIDO - importante
            "subsidiary_aims": unit_info.get("subsidiary_aims", [])  # ✅ MANTIDO - importante
        }
        
        # NOVA ESTRUTURA: usar resumo compacto + vocabulary essencial
        content_data_for_prompt = {
            "summarized_context": summarized_context,  # ✅ Contexto comprimido via IA
            "vocabulary": {"items": vocabulary_items[:8]},  # ✅ Só vocabulário principal
            "strategy_applied": content_analysis.get("strategy_applied", "")
        }
        
        # Usar prompt generator com dados otimizados
        qa_prompt_messages = await self.prompt_generator.generate_qa_prompt(
            unit_data=unit_data_for_prompt,
            content_data=content_data_for_prompt,
            pedagogical_context=pedagogical_goals
        )
        
        return qa_prompt_messages

    
    def _create_qa_schema(self) -> Dict[str, Any]:
        """Create precise JSON schema for QASection using LangChain 0.3 structured output."""
        return {
            "title": "QASection",
            "description": "Schema for structured Q&A generation with Bloom taxonomy cognitive levels and phonetic awareness",
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 10,
                    "description": "List of questions for students as simple strings"
                },
                "answers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 10,
                    "description": "List of complete answers for teachers as simple strings"
                },
                "pedagogical_notes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 6,
                    "description": "List of pedagogical notes as simple strings"
                },
                "difficulty_progression": {
                    "type": "string",
                    "description": "Description of difficulty progression"
                },
                "vocabulary_integration": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "List of vocabulary integrated in questions"
                },
                "cognitive_levels": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["remember", "understand", "apply", "analyze", "evaluate", "create"]
                    },
                    "default": [],
                    "description": "List of cognitive levels (Bloom Taxonomy) for each question"
                },
                "pronunciation_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "List of pronunciation questions as simple strings"
                },
                "phonetic_awareness": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "List of phonetic awareness aspects developed"
                }
            },
            "required": ["questions", "answers", "pedagogical_notes", "difficulty_progression"],
            "additionalProperties": False
        }
    
    async def _generate_qa_llm(self, prompt_messages: List[Any]) -> Dict[str, Any]:
        """Gerar Q&A usando LangChain 0.3 structured output para evitar erros de validação."""
        try:
            logger.info("🤖 Consultando LLM para geração de Q&A com structured output...")
            
            # Verificar cache
            cache_key = self._generate_cache_key(prompt_messages)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info("📦 Usando resultado do cache")
                return cached_result
            
            # Usar LangChain 0.3 with_structured_output para forçar formato correto
            qa_schema = self._create_qa_schema()
            structured_llm = self.llm.with_structured_output(qa_schema)
            
            # Gerar usando structured output
            qa_data = await structured_llm.ainvoke(prompt_messages)
            
            # Validar que retornou dict
            if not isinstance(qa_data, dict):
                logger.warning("⚠️ Structured output não retornou dict, convertendo...")
                qa_data = dict(qa_data) if hasattr(qa_data, '__dict__') else {}
            
            # Garantir campos obrigatórios com fallbacks seguros
            qa_data = self._ensure_qa_required_fields(qa_data)
            
            # Validar estrutura e sincronizar arrays
            qa_data = self._clean_qa_data(qa_data)
            
            # Salvar no cache
            self._save_to_cache(cache_key, qa_data)
            
            logger.info(
                f"✅ LLM retornou Q&A estruturado: "
                f"{len(qa_data.get('questions', []))} perguntas, "
                f"{len(qa_data.get('answers', []))} respostas, "
                f"{len(qa_data.get('cognitive_levels', []))} níveis cognitivos"
            )
            return qa_data
                
        except Exception as e:
            logger.error(f"❌ Erro na consulta ao LLM com structured output: {str(e)}")
            logger.info("🔄 Tentando fallback sem structured output...")
            return await self._generate_qa_llm_fallback(prompt_messages)
    
    def _clean_json_content(self, content: str) -> str:
        """Limpar conteúdo JSON para resolver problemas comuns causados por o3-mini."""
        
        # Remover caracteres problemáticos no início de arrays
        content = content.strip()
        
        # NOVO: Limpeza especial para o3-mini truncado
        # Remove caracteres que aparecem quando resposta é cortada pelo limite de tokens
        if content.endswith('"'):
            # Se termina com aspas incompletas, tentar fechar JSON
            if not content.endswith('}'): 
                content = content.rstrip('"') + '"}'
        
        # Fix para problemas com arrays que começam incorretamente
        # Ex: "questions": ["[", "pergunta1", "pergunta2"] -> "questions": ["pergunta1", "pergunta2"]
        import re
        
        # Padrão para encontrar arrays que começam com "[" como primeiro elemento
        pattern = r'("questions":\s*\[)\s*"?\["?\s*,\s*'
        content = re.sub(pattern, r'\1', content)
        
        # Mesmo padrão para outros arrays
        for field in ["answers", "cognitive_levels", "pedagogical_notes", "pronunciation_questions", "phonetic_awareness", "vocabulary_integration"]:
            pattern = f'("{field}":\\s*\\[)\\s*"?\\["?\\s*,\\s*'
            content = re.sub(pattern, r'\1', content)
        
        # NOVO: Limpeza especial para conteúdo truncado de o3-mini
        # Remove elementos incompletos no final de arrays
        truncated_patterns = [
            r',\s*"[^"]*$',      # Remove elementos incompletos no final
            r'"[^"]*$',          # Remove strings incompletas no final
            r',\s*$',             # Remove vírgulas pendentes
        ]
        
        for pattern in truncated_patterns:
            content = re.sub(pattern, '', content)
        
        # Remover elementos inválidos que são apenas "[" ou "]"
        patterns_to_clean = [
            r'"?\["?(?:\s*,)?',  # Remove "[" elements
            r'"?\]"?(?:\s*,)?',  # Remove "]" elements  
            r',\s*,',            # Remove double commas
            r',\s*\]',           # Remove trailing commas in arrays
            r'\[\s*,',           # Remove leading commas in arrays
        ]
        
        for pattern in patterns_to_clean:
            content = re.sub(pattern, '', content)
            
        # Fix final para garantir JSON válido
        content = re.sub(r',(\s*[}\]])', r'\1', content)  # Remove trailing commas
        
        # NOVO: Fechar JSON incompleto causado por truncamento
        if not content.strip().endswith('}'):
            # Contar chaves abertas vs fechadas
            open_braces = content.count('{')
            close_braces = content.count('}')
            
            # Fechar arrays abertos
            open_brackets = content.count('[') - content.count(']')
            content += ']' * max(0, open_brackets)
            
            # Fechar objetos abertos
            missing_braces = open_braces - close_braces
            content += '}' * max(0, missing_braces)
        
        return content
    
    def _ensure_qa_required_fields(self, qa_data: Dict[str, Any]) -> Dict[str, Any]:
        """Garantir campos obrigatórios na seção de Q&A."""
        # Garantir listas obrigatórias
        if "questions" not in qa_data or not isinstance(qa_data["questions"], list):
            qa_data["questions"] = []
        if "answers" not in qa_data or not isinstance(qa_data["answers"], list):
            qa_data["answers"] = []
        if "pedagogical_notes" not in qa_data or not isinstance(qa_data["pedagogical_notes"], list):
            qa_data["pedagogical_notes"] = []
        
        # Garantir campo obrigatório string
        if "difficulty_progression" not in qa_data:
            qa_data["difficulty_progression"] = "Progressiva do simples ao complexo"
        
        # Garantir campos opcionais com valores padrão
        defaults = {
            "vocabulary_integration": [],
            "cognitive_levels": [],
            "pronunciation_questions": [],
            "phonetic_awareness": []
        }
        
        for field, default_value in defaults.items():
            if field not in qa_data:
                qa_data[field] = default_value
        
        return qa_data
    
    def _clean_qa_data(self, qa_data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpar e sincronizar arrays de Q&A."""
        # Limpar e validar arrays de strings
        string_arrays = ["questions", "answers", "pedagogical_notes", "vocabulary_integration", "cognitive_levels", "pronunciation_questions", "phonetic_awareness"]
        
        for field in string_arrays:
            if field in qa_data:
                qa_data[field] = self._ensure_string_list(qa_data[field])
        
        # Sincronizar questions, answers e cognitive_levels (devem ter mesmo tamanho)
        questions = qa_data.get("questions", [])
        answers = qa_data.get("answers", [])
        cognitive_levels = qa_data.get("cognitive_levels", [])
        
        # Encontrar tamanho mínimo
        min_length = min(len(questions), len(answers)) if questions and answers else 0
        
        if min_length > 0:
            qa_data["questions"] = questions[:min_length]
            qa_data["answers"] = answers[:min_length]
            
            # Ajustar cognitive_levels para corresponder
            if len(cognitive_levels) < min_length:
                # Preencher com níveis padrão
                default_levels = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
                while len(cognitive_levels) < min_length:
                    cognitive_levels.append(default_levels[len(cognitive_levels) % len(default_levels)])
            qa_data["cognitive_levels"] = cognitive_levels[:min_length]
        else:
            # Se não há perguntas/respostas válidas, criar conjunto mínimo baseado no conteúdo da unidade
            # OTIMIZADO: Reduzir fallback para economizar tokens
            qa_data["questions"] = ["What did you learn from this unit?", "How would you use this knowledge?"]
            qa_data["answers"] = ["Key concepts and vocabulary for practical use.", "Apply in real communication situations."]
            qa_data["cognitive_levels"] = ["remember", "apply"]
        
        # Garantir que pedagogical_notes tenha pelo menos 2 itens (OTIMIZADO)
        if len(qa_data.get("pedagogical_notes", [])) < 2:
            qa_data["pedagogical_notes"] = [
                "Check vocabulary usage in answers",
                "Encourage practical application"
            ]
        
        return qa_data
    
    def _ensure_string_list(self, value: Any) -> List[str]:
        """Garantir que valor seja lista de strings válidas."""
        if not isinstance(value, list):
            return []
        
        result = []
        for item in value:
            if item and str(item).strip():
                item_str = str(item).strip()
                
                # Filtrar elementos problemáticos
                if self._is_valid_content_item(item_str):
                    result.append(item_str)
        
        return result
    
    def _is_valid_content_item(self, item: str) -> bool:
        """Verificar se item é conteúdo válido (não template/placeholder)."""
        
        # Filtrar elementos claramente inválidos
        invalid_patterns = [
            r'^[\[\]]+$',                    # Apenas colchetes
            r'^Question \d+',                # "Question 1", "Question 2", etc
            r'^\.\.\.$',                     # Apenas "..."
            r'^Answer to question \d+',      # "Answer to question 1", etc
            r'^Teaching note \d+',           # "Teaching note 1", etc
            r'^Pronunciation-focused question \d+',  # Templates de exemplo
            r'^Phonetic awareness development note \d+',  # Templates de exemplo
            r'^word\d+$',                    # "word1", "word2", etc - templates
            r'^Complete answer.*with',       # Templates de resposta
            r'^\(.+level\)$',               # "(Remember level)" etc
        ]
        
        import re
        for pattern in invalid_patterns:
            if re.match(pattern, item, re.IGNORECASE):
                return False
        
        # Item deve ter pelo menos 5 caracteres para ser considerado válido
        if len(item) < 5:
            return False
            
        return True
    
    async def _generate_qa_llm_fallback(self, prompt_messages: List[Any]) -> Dict[str, Any]:
        """Fallback para geração sem structured output quando structured falha."""
        try:
            logger.info("🔄 Tentando geração fallback sem structured output...")
            
            # Gerar usando LangChain tradicional
            response = await self.llm.ainvoke(prompt_messages)
            content = response.content
            
            # Tentar parsear JSON
            try:
                # Limpar response se necessário
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                
                # Limpar problemas comuns de JSON
                content = self._clean_json_content(content)
                
                qa_data = json.loads(content)
                
                if not isinstance(qa_data, dict):
                    raise ValueError("Response não é um objeto")
                
                # Aplicar limpeza rigorosa no fallback
                qa_data = self._ensure_qa_required_fields(qa_data)
                qa_data = self._clean_qa_data(qa_data)
                
                logger.info(f"✅ Fallback gerou Q&A com {len(qa_data.get('questions', []))} perguntas")
                return qa_data
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"⚠️ Erro ao parsear JSON no fallback: {str(e)}")
                return self._extract_qa_from_text(content)
                
        except Exception as e:
            logger.error(f"❌ Erro no fallback: {str(e)}")
            # Retornar Q&A de fallback final
            return await self._generate_fallback_qa()
    
    async def _process_and_structure_qa(
        self, 
        raw_qa: Dict[str, Any], 
        enriched_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Processar e estruturar dados de Q&A."""
        
        # Extrair e validar campos obrigatórios
        questions = raw_qa.get("questions", [])
        answers = raw_qa.get("answers", [])
        cognitive_levels = raw_qa.get("cognitive_levels", [])
        
        # Garantir que há o mesmo número de perguntas, respostas e níveis cognitivos
        min_length = min(len(questions), len(answers), len(cognitive_levels))
        if min_length == 0:
            return await self._generate_fallback_qa()
        
        # Truncar para o menor comprimento para manter consistência
        questions = questions[:min_length]
        answers = answers[:min_length]
        cognitive_levels = cognitive_levels[:min_length]
        
        # Processar campos opcionais
        pedagogical_notes = raw_qa.get("pedagogical_notes", [])
        pronunciation_questions = raw_qa.get("pronunciation_questions", [])
        phonetic_awareness = raw_qa.get("phonetic_awareness", [])
        vocabulary_integration = raw_qa.get("vocabulary_integration", [])
        
        # Validar e expandir notas pedagógicas se necessário
        if len(pedagogical_notes) < len(questions) // 2:
            # Adicionar notas pedagógicas básicas
            unit_info = enriched_context["unit_info"]
            # Usar notas pedagógicas variadas em vez de template repetitivo
            pedagogical_templates = [
                f"This question helps students apply {unit_info['unit_type']} knowledge in practical contexts.",
                f"Use this to encourage critical thinking about {unit_info['unit_type']} concepts.",
                f"This question develops students' ability to analyze and use {unit_info['unit_type']} effectively.",
                f"Focus on helping students connect {unit_info['unit_type']} to their personal experiences.",
                f"This question promotes active learning and application of {unit_info['unit_type']} skills.",
                f"Use this to assess students' comprehension and encourage deeper exploration.",
                f"This question helps students reflect on their learning process and progress.",
                f"Focus on practical application and real-world use of learned concepts."
            ]
            
            for i in range(len(questions) - len(pedagogical_notes)):
                template_index = i % len(pedagogical_templates)
                pedagogical_notes.append(pedagogical_templates[template_index])
        
        # Determinar progressão de dificuldade
        difficulty_progression = self._analyze_difficulty_progression(cognitive_levels)
        
        return {
            "questions": questions,
            "answers": answers,
            "cognitive_levels": cognitive_levels,
            "pedagogical_notes": pedagogical_notes,
            "pronunciation_questions": pronunciation_questions,
            "phonetic_awareness": phonetic_awareness,
            "vocabulary_integration": vocabulary_integration,
            "difficulty_progression": difficulty_progression
        }
    
    async def _enrich_with_pronunciation_questions(
        self, 
        structured_qa: Dict[str, Any], 
        content_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enriquecer Q&A com perguntas específicas de pronúncia."""
        
        pronunciation_questions = structured_qa.get("pronunciation_questions", [])
        phonetic_awareness = structured_qa.get("phonetic_awareness", [])
        
        # Se já tem perguntas de pronúncia suficientes, manter
        if len(pronunciation_questions) >= 2:
            return structured_qa
        
        # Extrair vocabulário para criar perguntas de pronúncia
        vocabulary_items = []
        if content_data.get("vocabulary") and content_data["vocabulary"].get("items"):
            vocabulary_items = content_data["vocabulary"]["items"][:5]  # Top 5 palavras
        
        # Gerar perguntas de pronúncia adicionais
        additional_pronunciation = []
        additional_awareness = []
        
        for item in vocabulary_items:
            word = item.get("word", "")
            phoneme = item.get("phoneme", "")
            
            if word and phoneme:
                # Pergunta sobre fonema
                additional_pronunciation.append(
                    f"How do you pronounce '{word}'? What sounds do you hear?"
                )
                
                # Consciência fonética
                additional_awareness.append(
                    f"Students should identify the individual sounds in '{word}' {phoneme} and practice stress patterns."
                )
        
        # Adicionar perguntas de pronúncia gerais se necessário
        if len(additional_pronunciation) < 2:
            additional_pronunciation.extend([
                "Which words from this unit have similar stress patterns?",
                "How does connected speech change the pronunciation of these words?"
            ])
            
            additional_awareness.extend([
                "Focus on word stress patterns and rhythm in connected speech.",
                "Encourage students to notice pronunciation differences in different contexts."
            ])
        
        # Combinar com existentes
        structured_qa["pronunciation_questions"] = pronunciation_questions + additional_pronunciation[:2]
        structured_qa["phonetic_awareness"] = phonetic_awareness + additional_awareness[:2]
        
        return structured_qa
    
    def _ensure_required_qa_fields(self, qa_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Garantir que todos os campos obrigatórios existam no qa_data.
        Correção para o erro 'difficulty_progression' e outros campos missing.
        """
        # Garantir campos obrigatórios como listas
        required_lists = {
            "questions": [],
            "answers": [],
            "pedagogical_notes": [],
            "vocabulary_integration": [],
            "cognitive_levels": [],
            "pronunciation_questions": [],
            "phonetic_awareness": []
        }
        
        for field, default_value in required_lists.items():
            if field not in qa_data or not isinstance(qa_data[field], list):
                qa_data[field] = default_value
        
        # Garantir campo difficulty_progression (string obrigatória)
        if "difficulty_progression" not in qa_data or not isinstance(qa_data["difficulty_progression"], str):
            # Analisar progressão baseada nos cognitive_levels existentes
            cognitive_levels = qa_data.get("cognitive_levels", [])
            if cognitive_levels:
                qa_data["difficulty_progression"] = self._analyze_difficulty_progression(cognitive_levels)
            else:
                qa_data["difficulty_progression"] = "Progressive difficulty from simple recall to complex application"
        
        logger.debug(f"✅ Campos obrigatórios garantidos: {list(qa_data.keys())}")
        return qa_data
    
    async def _add_pedagogical_notes(
        self, 
        enriched_qa: Dict[str, Any], 
        enriched_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adicionar notas pedagógicas detalhadas."""
        
        pedagogical_notes = enriched_qa.get("pedagogical_notes", [])
        questions = enriched_qa.get("questions", [])
        cognitive_levels = enriched_qa.get("cognitive_levels", [])
        
        unit_info = enriched_context["unit_info"]
        cefr_level = unit_info["cefr_level"]
        
        # Expandir notas pedagógicas
        enhanced_notes = []
        
        for i, (question, level) in enumerate(zip(questions, cognitive_levels)):
            if i < len(pedagogical_notes):
                base_note = pedagogical_notes[i]
            else:
                base_note = f"Teaching guidance for question {i+1}"
            
            # Adicionar orientações específicas por nível cognitivo
            level_guidance = self._get_level_specific_guidance(level, cefr_level)
            
            enhanced_note = f"{base_note} | {level_guidance}"
            enhanced_notes.append(enhanced_note)
        
        # Adicionar notas gerais sobre o uso do Q&A
        general_notes = [
            f"Use these questions progressively to build {cefr_level} level comprehension.",
            f"Encourage students to use unit vocabulary: {', '.join(enriched_qa.get('vocabulary_integration', [])[:5])}.",
            "Monitor pronunciation during oral responses and provide feedback.",
            f"Adapt questions to {unit_info['unit_type']} learning objectives."
        ]
        
        enhanced_notes.extend(general_notes)
        
        enriched_qa["pedagogical_notes"] = enhanced_notes
        return enriched_qa
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _determine_bloom_targets(self, cefr_level: str, sequence_order: int) -> Dict[str, int]:
        """Determinar distribuição alvo de níveis de Bloom."""
        
        # Base distribution adaptada por nível CEFR
        base_distributions = {
            "A1": {"remember": 4, "understand": 3, "apply": 2, "analyze": 1, "evaluate": 0, "create": 0},
            "A2": {"remember": 3, "understand": 3, "apply": 3, "analyze": 1, "evaluate": 0, "create": 0},
            "B1": {"remember": 2, "understand": 3, "apply": 3, "analyze": 2, "evaluate": 1, "create": 0},
            "B2": {"remember": 2, "understand": 2, "apply": 3, "analyze": 2, "evaluate": 2, "create": 1},
            "C1": {"remember": 1, "understand": 2, "apply": 2, "analyze": 3, "evaluate": 2, "create": 2},
            "C2": {"remember": 1, "understand": 2, "apply": 2, "analyze": 2, "evaluate": 3, "create": 2}
        }
        
        distribution = base_distributions.get(cefr_level, base_distributions["A2"]).copy()
        
        # Ajustar baseado na sequência (unidades mais avançadas = mais análise)
        if sequence_order > 5:
            if distribution.get("analyze", 0) > 0:
                distribution["analyze"] += 1
            if distribution.get("remember", 0) > 1:
                distribution["remember"] -= 1
        
        return distribution
    
    def _analyze_difficulty_progression(self, cognitive_levels: List[str]) -> str:
        """Analisar progressão de dificuldade."""
        
        level_order = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
        level_scores = {level: i for i, level in enumerate(level_order)}
        
        if not cognitive_levels:
            return "unknown"
        
        scores = [level_scores.get(level, 2) for level in cognitive_levels]
        
        # Verificar se há progressão geral
        if len(scores) > 1:
            avg_first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
            avg_second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            
            if avg_second_half > avg_first_half + 0.5:
                return "progressive"
            elif abs(avg_second_half - avg_first_half) <= 0.5:
                return "balanced"
            else:
                return "needs_reordering"
        
        return "single_level"
    
    def _get_level_specific_guidance(self, cognitive_level: str, cefr_level: str) -> str:
        """Obter orientações específicas por nível cognitivo."""
        
        guidance_map = {
            "remember": f"Help students recall vocabulary and basic concepts. For {cefr_level}: focus on recognition and simple recall.",
            "understand": f"Encourage explanation and description. For {cefr_level}: students should demonstrate comprehension through paraphrasing.",
            "apply": f"Guide students to use knowledge in new situations. For {cefr_level}: practical application in different contexts.",
            "analyze": f"Help students break down information and see relationships. For {cefr_level}: compare and contrast elements.",
            "evaluate": f"Encourage critical thinking and judgment. For {cefr_level}: assess and give reasoned opinions.",
            "create": f"Support students in producing original work. For {cefr_level}: combine elements to form something new."
        }
        
        return guidance_map.get(cognitive_level, "Guide students appropriately for their level.")
    
    def _extract_qa_from_text(self, text: str) -> Dict[str, Any]:
        """Extrair Q&A de texto quando JSON parsing falha."""
        
        qa_data = {
            "questions": [],
            "answers": [],
            "cognitive_levels": [],
            "pedagogical_notes": [],
            "pronunciation_questions": [],
            "phonetic_awareness": [],
            "vocabulary_integration": []
        }
        
        lines = text.split('\n')
        current_section = None
        current_list = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detectar seções
            if 'question' in line.lower():
                if current_section and current_list:
                    qa_data[current_section].extend(current_list)
                current_section = 'questions'
                current_list = []
                if ':' in line:
                    current_list.append(line.split(':', 1)[-1].strip())
            elif 'answer' in line.lower():
                if current_section and current_list:
                    qa_data[current_section].extend(current_list)
                current_section = 'answers'
                current_list = []
                if ':' in line:
                    current_list.append(line.split(':', 1)[-1].strip())
            elif 'pronunciation' in line.lower():
                if current_section and current_list:
                    qa_data[current_section].extend(current_list)
                current_section = 'pronunciation_questions'
                current_list = []
            elif any(marker in line for marker in ['1.', '2.', '3.', '-', '•']):
                if current_section:
                    cleaned_line = line.lstrip('123456789.-•').strip()
                    if cleaned_line:
                        current_list.append(cleaned_line)
        
        # Adicionar última seção
        if current_section and current_list:
            qa_data[current_section].extend(current_list)
        
        # Preencher campos faltantes
        num_questions = len(qa_data['questions'])
        
        if len(qa_data['answers']) < num_questions:
            # Usar respostas genéricas mais pedagógicas
            generic_answers = [
                "Students should provide a detailed response based on unit content and personal understanding.",
                "Encourage students to use vocabulary from the unit and explain their reasoning.",
                "This question allows for creative application of learned concepts in practical contexts.",
                "Students should demonstrate comprehension by connecting concepts to real-world situations.",
                "Focus on encouraging students to express their ideas using appropriate language structures.",
                "This question develops analytical thinking and application of unit vocabulary.",
                "Students should provide examples and explanations to support their answers.",
                "Encourage reflection on learning and practical application of new knowledge."
            ]
            
            for i in range(len(qa_data['answers']), num_questions):
                answer_index = i % len(generic_answers)
                qa_data['answers'].append(generic_answers[answer_index])
        
        if len(qa_data['cognitive_levels']) < num_questions:
            default_levels = ['remember', 'understand', 'apply', 'analyze'] * (num_questions // 4 + 1)
            qa_data['cognitive_levels'] = default_levels[:num_questions]
        
        return qa_data
    
    async def _generate_fallback_qa(self, unit_context: str = "general English", cefr_level: str = "A2", vocabulary_words: list = None) -> Dict[str, Any]:
        """Gerar Q&A de fallback via IA usando YAML quando geração principal falha."""
        try:
            # Usar novo prompt YAML para Q&A fallback
            qa_fallback_prompt = await self.prompt_generator.generate_qa_prompt(
                unit_context=unit_context,
                cefr_level=cefr_level,
                vocabulary_words=vocabulary_words or [],
                target_count=5,
                language_variant="american_english"
            )
            
            response = await self.llm.ainvoke(qa_fallback_prompt)
            
            # Parse JSON response
            try:
                response_content = response.content
                if "```json" in response_content:
                    response_content = response_content.split("```json")[1].split("```")[0]
                
                fallback_data = json.loads(response_content)
                logger.info("✅ Q&A fallback gerado via IA")
                return fallback_data
                
            except json.JSONDecodeError:
                logger.warning("Erro no parsing do Q&A fallback via IA, usando fallback técnico")
                return self._technical_fallback_qa()
                
        except Exception as e:
            logger.warning(f"Erro ao gerar Q&A fallback via IA: {str(e)}, usando fallback técnico")
            return self._technical_fallback_qa()
    
    def _technical_fallback_qa(self) -> Dict[str, Any]:
        """Q&A fallback técnico apenas quando IA falha completamente."""
        
        fallback_qa = {
            "questions": [
                "What new vocabulary did you learn in this unit?",
                "How would you use these words in a real conversation?",
                "Can you explain the main topic of this unit?",
                "What pronunciation patterns did you notice?",
                "How can you practice these words at home?"
            ],
            "answers": [
                "Students should list and define the key vocabulary from the unit, explaining meanings in their own words.",
                "Students should create example sentences or dialogues using the new vocabulary in realistic contexts.",
                "Students should summarize the unit's main theme and connect it to their personal experiences.",
                "Students should identify stress patterns, difficult sounds, and pronunciation rules from the unit.",
                "Students should suggest practical ways to review and use the vocabulary outside of class."
            ],
            "cognitive_levels": ["remember", "apply", "understand", "analyze", "create"],
            "pedagogical_notes": [
                "Use this question to assess vocabulary retention and understanding.",
                "Encourage creative use of vocabulary in meaningful contexts.",
                "Help students connect new learning to prior knowledge.",
                "Develop phonetic awareness and pronunciation skills.",
                "Promote autonomous learning and self-study strategies."
            ],
            "pronunciation_questions": [
                "Which words in this unit have stress on the first syllable?",
                "How do you pronounce the most difficult word from this unit?"
            ],
            "phonetic_awareness": [
                "Students should develop awareness of English stress patterns.",
                "Focus on clear articulation of challenging sounds."
            ],
            "vocabulary_integration": ["vocabulary", "pronunciation", "conversation", "practice"]
        }
        
        logger.warning("⚠️ Usando Q&A de fallback")
        return fallback_qa
    
    def _generate_cache_key(self, prompt_messages: List[Any]) -> str:
        """Gerar chave para cache baseada no prompt."""
        content = "".join([msg.content for msg in prompt_messages])
        return f"qa_{hash(content)}"
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Obter item do cache em memória."""
        current_time = time.time()
        
        # Verificar se existe e não expirou (2 horas = 7200s)
        if (key in self._memory_cache and 
            key in self._cache_expiry and 
            current_time - self._cache_expiry[key] < 7200):
            return self._memory_cache[key]
        
        # Remover se expirado
        if key in self._memory_cache:
            del self._memory_cache[key]
        if key in self._cache_expiry:
            del self._cache_expiry[key]
        
        return None
    
    def _save_to_cache(self, key: str, value: Dict[str, Any]) -> None:
        """Salvar item no cache em memória."""
        # Limpar cache se muito grande
        if len(self._memory_cache) >= self._max_cache_size:
            # Remover item mais antigo
            oldest_key = min(self._cache_expiry.keys(), key=self._cache_expiry.get)
            del self._memory_cache[oldest_key]
            del self._cache_expiry[oldest_key]
        
        self._memory_cache[key] = value
        self._cache_expiry[key] = time.time()
    
    async def _ensure_exact_target_count(self, qa_data: Dict[str, Any], target_count: int) -> Dict[str, Any]:
        """
        Garantir que o número exato de perguntas seja respeitado.
        Similar ao sistema implementado para vocabulário e sentences.
        """
        current_questions = qa_data.get("questions", [])
        current_answers = qa_data.get("answers", [])
        current_count = len(current_questions)
        
        logger.info(f"🎯 Garantindo target_count QA: {current_count} → {target_count} perguntas")
        
        if current_count == target_count:
            logger.info(f"✅ Target count já correto: {target_count} perguntas")
            return qa_data
        
        elif current_count > target_count:
            # Remover perguntas extras, mantendo as melhores
            logger.info(f"📉 Removendo {current_count - target_count} perguntas extras")
            
            # Manter as primeiras que são geralmente as melhores
            qa_data["questions"] = current_questions[:target_count]
            qa_data["answers"] = current_answers[:target_count]
            
            # Ajustar outros arrays se existirem
            for key in ["pedagogical_notes", "cognitive_levels", "pronunciation_questions", "phonetic_awareness"]:
                if key in qa_data and isinstance(qa_data[key], list):
                    qa_data[key] = qa_data[key][:target_count]
            
            logger.info(f"✅ Reduzido para {target_count} perguntas")
            
        else:
            # Gerar perguntas adicionais simples
            needed = target_count - current_count
            logger.info(f"📈 Gerando {needed} perguntas adicionais")
            
            try:
                # Gerar perguntas simples adicionais
                extra_questions = []
                extra_answers = []
                
                # Gerar perguntas variadas em vez de repetitivas
                question_templates = [
                    "What new vocabulary from this unit would you use in daily conversation?",
                    "How would you explain this unit's topic to someone who doesn't speak English?",
                    "Which pronunciation rule from this unit do you find most useful?",
                    "What cultural aspect did you learn from this unit's content?",
                    "How does this unit's vocabulary connect to your personal experiences?",
                    "What would you teach first from this unit to a beginner student?",
                    "Which sentence structure from this unit is most practical for you?",
                    "How would you practice this unit's content outside of class?"
                ]
                
                answer_templates = [
                    "Students should select vocabulary items they find most relevant and explain their practical applications.",
                    "Students should demonstrate understanding by creating simple explanations or translations.",
                    "Students should identify and apply pronunciation patterns they've learned.",
                    "Students should discuss cultural insights gained from the unit's context and vocabulary.",
                    "Students should make personal connections between unit content and their own experiences.",
                    "Students should prioritize and sequence learning objectives for effective teaching.",
                    "Students should analyze grammatical patterns and choose those most useful for communication.",
                    "Students should propose realistic study strategies and practice methods."
                ]
                
                for i in range(needed):
                    template_index = i % len(question_templates)
                    extra_questions.append(question_templates[template_index])
                    extra_answers.append(answer_templates[template_index])
                
                qa_data["questions"] = current_questions + extra_questions
                qa_data["answers"] = current_answers + extra_answers
                
                # Estender outros arrays se existirem
                if "pedagogical_notes" in qa_data:
                    pedagogical_templates = [
                        "Encourage students to reflect on their learning and make personal connections.",
                        "This question develops critical thinking about the unit content.",
                        "Use this to assess comprehension and encourage vocabulary application.",
                        "Focus on practical application of learned concepts in real situations.",
                        "This question promotes active recall and deeper understanding.",
                        "Encourage students to explain their reasoning and provide examples.",
                        "Use this to connect unit content to students' prior knowledge and experiences.",
                        "This question develops analytical skills and language awareness."
                    ]
                    qa_data["pedagogical_notes"] = qa_data["pedagogical_notes"] + [pedagogical_templates[i % len(pedagogical_templates)] for i in range(needed)]
                if "cognitive_levels" in qa_data:
                    qa_data["cognitive_levels"] = qa_data["cognitive_levels"] + ["remember" for _ in range(needed)]
                
                logger.info(f"✅ Adicionadas {needed} perguntas para atingir target_count: {target_count}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao gerar perguntas adicionais: {str(e)}")
        
        return qa_data


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def validate_qa_structure(qa_data: Dict[str, Any]) -> bool:
    """Validar estrutura básica de Q&A."""
    required_fields = ["questions", "answers"]
    
    for field in required_fields:
        if field not in qa_data:
            return False
        if not isinstance(qa_data[field], list):
            return False
    
    # Verificar se há pelo menos uma pergunta e resposta
    if len(qa_data["questions"]) == 0 or len(qa_data["answers"]) == 0:
        return False
    
    # Verificar se o número de perguntas e respostas é compatível
    if len(qa_data["questions"]) != len(qa_data["answers"]):
        return False
    
    return True


def analyze_cognitive_complexity(cognitive_levels: List[str]) -> Dict[str, Any]:
    """Analisar complexidade cognitiva das perguntas."""
    
    level_weights = {
        "remember": 1,
        "understand": 2,
        "apply": 3,
        "analyze": 4,
        "evaluate": 5,
        "create": 6
    }
    
    if not cognitive_levels:
        return {"complexity_score": 0, "distribution": {}}
    
    # Calcular score médio de complexidade
    total_weight = sum(level_weights.get(level, 3) for level in cognitive_levels)
    complexity_score = total_weight / len(cognitive_levels)
    
    # Distribuição por níveis
    distribution = {}
    for level in cognitive_levels:
        distribution[level] = distribution.get(level, 0) + 1
    
    return {
        "complexity_score": complexity_score,
        "distribution": distribution,
        "highest_level": max(cognitive_levels, key=lambda x: level_weights.get(x, 0)) if cognitive_levels else None,
        "variety_score": len(set(cognitive_levels)) / 6  # 6 níveis possíveis
    }


def generate_pronunciation_questions(vocabulary_items: List[Dict[str, Any]]) -> List[str]:
    """Gerar perguntas de pronúncia baseadas no vocabulário."""
    
    pronunciation_questions = []
    
    for item in vocabulary_items[:3]:  # Top 3 palavras
        word = item.get("word", "")
        phoneme = item.get("phoneme", "")
        syllable_count = item.get("syllable_count", 1)
        
        if word:
            # Pergunta sobre stress
            if syllable_count > 1:
                pronunciation_questions.append(
                    f"Where is the main stress in the word '{word}'?"
                )
            
            # Pergunta sobre sons específicos
            if phoneme:
                pronunciation_questions.append(
                    f"What sounds do you hear in '{word}'? Practice saying it clearly."
                )
    
    # Perguntas gerais se não há vocabulário suficiente
    if len(pronunciation_questions) < 2:
        pronunciation_questions.extend([
            "Which words from this unit rhyme with each other?",
            "How does the pronunciation change in connected speech?"
        ])
    
    return pronunciation_questions[:3]  # Máximo 3 perguntas


# =============================================================================
# ASYNC UTILITY FUNCTIONS - VERSÕES MODERNAS
# =============================================================================

async def generate_qa_for_unit_async(
    unit_data: Dict[str, Any],
    content_data: Dict[str, Any],
    hierarchy_context: Dict[str, Any] = None,
    pedagogical_context: Dict[str, Any] = None
) -> QASection:
    """
    Função utilitária moderna para gerar Q&A.
    
    Args:
        unit_data: Dados da unidade
        content_data: Conteúdo da unidade (vocabulário, sentences, etc.)
        hierarchy_context: Contexto hierárquico opcional
        pedagogical_context: Contexto pedagógico opcional
        
    Returns:
        QASection completa
    """
    generator = QAGeneratorService()
    
    qa_params = {
        "unit_data": unit_data,
        "content_data": content_data,
        "hierarchy_context": hierarchy_context or {},
        "pedagogical_context": pedagogical_context or {}
    }
    
    return await generator.generate_qa_for_unit(qa_params)


async def enhance_existing_qa(
    existing_qa: QASection,
    additional_vocabulary: List[Dict[str, Any]] = None,
    pronunciation_focus: str = None
) -> QASection:
    """
    Enriquecer Q&A existente com novo conteúdo.
    
    Args:
        existing_qa: Q&A section existente
        additional_vocabulary: Vocabulário adicional
        pronunciation_focus: Foco específico de pronúncia
        
    Returns:
        QASection enriquecida
    """
    # Adicionar perguntas de pronúncia se especificado
    if pronunciation_focus and additional_vocabulary:
        additional_pronunciation = generate_pronunciation_questions(additional_vocabulary)
        
        enhanced_qa = QASection(
            questions=existing_qa.questions + [f"Pronunciation focus ({pronunciation_focus}): {q}" for q in additional_pronunciation],
            answers=existing_qa.answers + [f"Answer focusing on {pronunciation_focus} aspects." for _ in additional_pronunciation],
            pedagogical_notes=existing_qa.pedagogical_notes + [f"Emphasize {pronunciation_focus} in pronunciation practice."],
            difficulty_progression=existing_qa.difficulty_progression,
            vocabulary_integration=existing_qa.vocabulary_integration + [item.get("word", "") for item in additional_vocabulary[:3]],
            cognitive_levels=existing_qa.cognitive_levels + ["apply"] * len(additional_pronunciation),
            pronunciation_questions=existing_qa.pronunciation_questions + additional_pronunciation,
            phonetic_awareness=existing_qa.phonetic_awareness + [f"Focus on {pronunciation_focus} awareness."]
        )
        
        return enhanced_qa
    
    return existing_qa


def create_qa_quality_report(qa_section: QASection) -> Dict[str, Any]:
    """
    Criar relatório de qualidade do Q&A.
    
    Args:
        qa_section: Seção de Q&A para analisar
        
    Returns:
        Dict com métricas de qualidade
    """
    # Análise básica
    total_questions = len(qa_section.questions)
    total_answers = len(qa_section.answers)
    pronunciation_ratio = len(qa_section.pronunciation_questions) / max(total_questions, 1)
    
    # Análise cognitiva
    cognitive_analysis = analyze_cognitive_complexity(qa_section.cognitive_levels)
    
    # Análise de vocabulário
    vocabulary_integration_score = len(qa_section.vocabulary_integration) / max(total_questions, 1)
    
    # Score geral de qualidade
    quality_components = {
        "structure_completeness": min(total_answers / max(total_questions, 1), 1.0),
        "cognitive_diversity": cognitive_analysis.get("variety_score", 0),
        "pronunciation_focus": min(pronunciation_ratio * 2, 1.0),  # Ideal: 50% das perguntas
        "vocabulary_integration": min(vocabulary_integration_score, 1.0),
        "pedagogical_depth": min(len(qa_section.pedagogical_notes) / max(total_questions, 1), 1.0)
    }
    
    overall_quality = sum(quality_components.values()) / len(quality_components)
    
    return {
        "overall_quality_score": round(overall_quality, 2),
        "quality_components": quality_components,
        "statistics": {
            "total_questions": total_questions,
            "total_answers": total_answers,
            "pronunciation_questions": len(qa_section.pronunciation_questions),
            "pronunciation_ratio": round(pronunciation_ratio, 2),
            "vocabulary_words_integrated": len(qa_section.vocabulary_integration),
            "pedagogical_notes": len(qa_section.pedagogical_notes)
        },
        "cognitive_analysis": cognitive_analysis,
        "difficulty_progression": qa_section.difficulty_progression,
        "recommendations": _generate_qa_improvement_recommendations(quality_components, qa_section)
    }


def _generate_qa_improvement_recommendations(
    quality_components: Dict[str, float], 
    qa_section: QASection
) -> List[str]:
    """Gerar recomendações de melhoria para Q&A."""
    
    recommendations = []
    
    if quality_components["structure_completeness"] < 0.9:
        recommendations.append("Verificar se todas as perguntas têm respostas correspondentes.")
    
    if quality_components["cognitive_diversity"] < 0.5:
        recommendations.append("Aumentar diversidade cognitiva - incluir mais níveis da Taxonomia de Bloom.")
    
    if quality_components["pronunciation_focus"] < 0.3:
        recommendations.append("Adicionar mais perguntas focadas em pronúncia e consciência fonética.")
    
    if quality_components["vocabulary_integration"] < 0.6:
        recommendations.append("Integrar mais vocabulário da unidade nas perguntas e respostas.")
    
    if quality_components["pedagogical_depth"] < 0.7:
        recommendations.append("Expandir notas pedagógicas para orientar melhor o uso das perguntas.")
    
    if len(qa_section.questions) < 8:
        recommendations.append("Considerar adicionar mais perguntas para cobertura completa (ideal: 8-12).")
    
    if qa_section.difficulty_progression == "needs_reordering":
        recommendations.append("Reordenar perguntas para progressão logical de dificuldade.")
    
    return recommendations


# =============================================================================
# EXEMPLO DE USO E TESTE
# =============================================================================

async def test_qa_generator():
    """Função de teste para o QA Generator."""
    
    # Dados de exemplo
    unit_data = {
        "title": "Hotel Reservations",
        "context": "Making hotel reservations and check-in procedures",
        "cefr_level": "A2",
        "unit_type": "lexical_unit",
        "language_variant": "american_english",
        "main_aim": "Students will be able to make hotel reservations",
        "subsidiary_aims": ["Use polite language", "Understand hotel procedures"]
    }
    
    content_data = {
        "vocabulary": {
            "items": [
                {"word": "reservation", "phoneme": "/ˌrezərˈveɪʃən/", "definition": "reserva"},
                {"word": "reception", "phoneme": "/rɪˈsepʃən/", "definition": "recepção"},
                {"word": "available", "phoneme": "/əˈveɪləbəl/", "definition": "disponível"}
            ]
        },
        "sentences": {
            "sentences": [
                {"text": "I'd like to make a reservation for tonight."},
                {"text": "Is there a room available?"},
                {"text": "Please check at the reception desk."}
            ]
        },
        "tips": {
            "strategy": "chunks",
            "title": "Useful Chunks for Hotel Communication"
        }
    }
    
    hierarchy_context = {
        "course_name": "English for Travel",
        "book_name": "Basic Travel English",
        "sequence_order": 3,
        "target_level": "A2"
    }
    
    pedagogical_context = {
        "learning_objectives": ["Make reservations politely", "Understand hotel vocabulary"],
        "progression_level": "intermediate",
        "phonetic_focus": "word_stress",
        "taught_vocabulary": ["hotel", "room", "night"]
    }
    
    try:
        # Gerar Q&A
        qa_section = await generate_qa_for_unit_async(
            unit_data, content_data, hierarchy_context, pedagogical_context
        )
        
        print("✅ Q&A Gerado com sucesso!")
        print(f"Perguntas: {len(qa_section.questions)}")
        print(f"Respostas: {len(qa_section.answers)}")
        print(f"Perguntas de pronúncia: {len(qa_section.pronunciation_questions)}")
        
        # Gerar relatório de qualidade
        quality_report = create_qa_quality_report(qa_section)
        print(f"Qualidade geral: {quality_report['overall_quality_score']}")
        
        return qa_section
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return None


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_qa_generator())