# src/services/vocabulary_generator.py
"""
Serviço de geração de vocabulário com RAG e análise de imagens.
Implementação completa do PROMPT 6 do IVO V2 Guide.
CORRIGIDO: IA contextual para análises complexas, constantes técnicas mantidas.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from pydantic import BaseModel, ValidationError

from src.core.unit_models import (
    VocabularyItem, VocabularySection, VocabularyGenerationRequest,
    VocabularyGenerationResponse
)
from src.core.enums import CEFRLevel, LanguageVariant, UnitType
from config.models import get_openai_config, load_model_configs

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES TÉCNICAS (MANTIDAS - SÃO PADRÕES ESTABELECIDOS)
# =============================================================================

IPA_VARIANT_MAPPING = {
    "american_english": "general_american",
    "british_english": "received_pronunciation",
    "australian_english": "australian_english",
    "canadian_english": "canadian_english",
    "indian_english": "indian_english"
}

VOWEL_SOUNDS = "aeiouy"

STRESS_PATTERNS = {
    "primary_first": "ˈ",
    "secondary_first": "ˌ",
    "unstressed": ""
}


class VocabularyGeneratorService:
    """Serviço principal para geração de vocabulário contextual."""
    
    def __init__(self):
        """Inicializar serviço com configurações."""
        self.openai_config = get_openai_config()
        self.model_configs = load_model_configs()
        
        # NOVO: Usar model_selector para obter o modelo correto
        from src.services.model_selector import get_llm_config_for_service
        
        # Obter configuração específica para vocabulary_generator (TIER-2: gpt-5-mini)
        llm_config = get_llm_config_for_service("vocabulary_generator")
        self.llm = ChatOpenAI(**llm_config)
        
        # Adicionar prompt_generator para usar os YAMLs de fallback
        from src.services.prompt_generator import PromptGeneratorService
        self.prompt_generator = PromptGeneratorService()
        
        logger.info("✅ VocabularyGeneratorService inicializado com IA contextual e LangChain 0.3 structured output")
    
    async def generate_vocabulary_for_unit(
        self, 
        vocabulary_request: VocabularyGenerationRequest,
        unit_data: Dict[str, Any],
        hierarchy_context: Dict[str, Any],
        rag_context: Dict[str, Any],
        images_analysis: Dict[str, Any]
    ) -> VocabularySection:
        """
        Gerar vocabulário para uma unidade usando RAG e análise de imagens.
        
        Args:
            vocabulary_request: Request com configurações de geração
            unit_data: Dados da unidade (título, contexto, CEFR, etc.)
            hierarchy_context: Contexto hierárquico (curso, book, sequência)
            rag_context: Contexto RAG (palavras já ensinadas, progressão)
            images_analysis: Análise das imagens da unidade
            
        Returns:
            VocabularySection completa com itens validados
        """
        try:
            start_time = time.time()
            
            # Usar target_count do request
            target_count = vocabulary_request.target_count if vocabulary_request.target_count else 15
            
            logger.info(f"🔤 Gerando {target_count} palavras de vocabulário para unidade")
            
            # 1. Construir contexto enriquecido
            enriched_context = await self._build_enriched_context(
                unit_data, hierarchy_context, rag_context, images_analysis
            )
            
            # 2. ANÁLISE VIA IA: Guidelines CEFR contextuais
            cefr_guidelines = await self._analyze_cefr_guidelines_ai(
                cefr_level=unit_data.get("cefr_level", "A2"),
                unit_context=unit_data.get("context", ""),
                unit_type=unit_data.get("unit_type", "lexical_unit"),
                hierarchy_context=hierarchy_context
            )
            
            # 3. Gerar prompt contextualizado
            vocabulary_prompt = await self._build_vocabulary_prompt(
                enriched_context, target_count, cefr_guidelines
            )
            
            # 4. Gerar vocabulário via LLM
            raw_vocabulary = await self._generate_vocabulary_llm(vocabulary_prompt)
            
            # 5. Processar e validar vocabulário
            validated_items = await self._process_and_validate_vocabulary(
                raw_vocabulary, enriched_context
            )
            
            # 6. Aplicar RAG para evitar repetições
            filtered_items = await self._apply_rag_filtering(
                validated_items, rag_context
            )
            
            # 7. Enriquecer com fonemas IPA
            enriched_items = await self._enrich_with_phonemes_ai(
                filtered_items, unit_data.get("language_variant", "american_english"),
                unit_data.get("context", "")
            )
            
            # 8. ANÁLISE VIA IA: Métricas de qualidade
            quality_metrics = await self._calculate_quality_metrics_ai(
                enriched_items, enriched_context, rag_context
            )
            
            # 9. ANÁLISE VIA IA: Complexidade fonética
            phonetic_complexity = await self._analyze_phonetic_complexity_ai(
                enriched_items, unit_data.get("cefr_level", "A2")
            )
            
            # 10. Garantir target_count exato
            final_items = await self._ensure_exact_target_count(
                enriched_items, target_count, enriched_context, rag_context
            )
            
            # 11. Construir resposta final
            vocabulary_section = VocabularySection(
                items=final_items,
                total_count=len(final_items),
                context_relevance=quality_metrics.get("context_relevance", 0.8),
                new_words_count=quality_metrics.get("new_words_count", len(enriched_items)),
                reinforcement_words_count=quality_metrics.get("reinforcement_count", 0),
                rag_context_used=rag_context,
                progression_level=rag_context.get("progression_level", "intermediate"),
                phoneme_coverage=quality_metrics.get("phoneme_coverage", {}),
                pronunciation_variants=[unit_data.get("language_variant", "american_english")],
                phonetic_complexity=phonetic_complexity,
                generated_at=datetime.now()
            )
            
            generation_time = time.time() - start_time
            
            logger.info(
                f"✅ Vocabulário gerado: {len(enriched_items)} palavras em {generation_time:.2f}s"
            )
            
            return vocabulary_section
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de vocabulário: {str(e)}")
            raise
    
    async def _build_enriched_context(
        self,
        unit_data: Dict[str, Any],
        hierarchy_context: Dict[str, Any],
        rag_context: Dict[str, Any],
        images_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Construir contexto enriquecido para geração."""
        
        # Extrair vocabulário das imagens se disponível
        image_vocabulary = []
        if images_analysis.get("success") and images_analysis.get("consolidated_vocabulary"):
            vocab_data = images_analysis["consolidated_vocabulary"].get("vocabulary", [])
            image_vocabulary = [item.get("word", "") for item in vocab_data if item.get("word")]
        
        # Contexto base da unidade
        base_context = unit_data.get("context", "")
        unit_title = unit_data.get("title", "")
        
        # Contexto da hierarquia
        course_name = hierarchy_context.get("course_name", "")
        book_name = hierarchy_context.get("book_name", "")
        sequence_order = hierarchy_context.get("sequence_order", 1)
        
        # Análise de progressão
        taught_vocabulary = rag_context.get("taught_vocabulary", [])
        progression_level = rag_context.get("progression_level", "intermediate")
        
        # Temas contextuais das imagens
        image_themes = []
        if images_analysis.get("success"):
            for analysis in images_analysis.get("individual_analyses", []):
                if "structured_data" in analysis.get("analysis", {}):
                    themes = analysis["analysis"]["structured_data"].get("contextual_themes", [])
                    image_themes.extend(themes)
        
        enriched_context = {
            "unit_context": {
                "title": unit_title,
                "context": base_context,
                "cefr_level": unit_data.get("cefr_level", "A2"),
                "language_variant": unit_data.get("language_variant", "american_english"),
                "unit_type": unit_data.get("unit_type", "lexical_unit")
            },
            "hierarchy_context": {
                "course_name": course_name,
                "book_name": book_name,
                "sequence_order": sequence_order,
                "target_level": hierarchy_context.get("target_level", unit_data.get("cefr_level"))
            },
            "rag_context": {
                "taught_vocabulary": taught_vocabulary[:20],  # Últimas 20 para contexto sutil
                "progression_level": progression_level,
                "vocabulary_density": rag_context.get("vocabulary_density", 0),
                "words_to_avoid": taught_vocabulary[-12:],  # Evitar apenas últimas 12 palavras
                "reinforcement_candidates": self._select_reinforcement_words(taught_vocabulary)
            },
            "images_context": {
                "vocabulary_suggestions": image_vocabulary[:15],  # Top 15 das imagens
                "themes": list(set(image_themes))[:10],  # Top 10 temas únicos
                "has_images": bool(image_vocabulary),
                "images_analyzed": len(images_analysis.get("individual_analyses", []))
            },
            "generation_preferences": {
                "target_count": 25,
                "allow_reinforcement": True,
                "focus_on_images": bool(image_vocabulary),
                "progression_appropriate": True
            }
        }
        
        return enriched_context
    
    # =============================================================================
    # ANÁLISES VIA IA (SUBSTITUEM DADOS HARD-CODED)
    # =============================================================================
    
    async def _analyze_cefr_guidelines_ai(
        self, 
        cefr_level: str, 
        unit_context: str, 
        unit_type: str,
        hierarchy_context: Dict[str, Any]
    ) -> str:
        """Análise contextual via IA para guidelines CEFR específicas."""
        
        system_prompt = """Você é um especialista em níveis CEFR e desenvolvimento de vocabulário contextual.
        
        Analise o nível CEFR fornecido considerando o contexto específico da unidade e tipo de ensino.
        Forneça guidelines específicas e contextuais para seleção de vocabulário apropriado."""
        
        human_prompt = f"""Analise este contexto educacional específico:
        
        NÍVEL CEFR: {cefr_level}
        CONTEXTO DA UNIDADE: {unit_context}
        TIPO DE UNIDADE: {unit_type}
        CURSO: {hierarchy_context.get('course_name', '')}
        LIVRO: {hierarchy_context.get('book_name', '')}
        SEQUÊNCIA: Unidade {hierarchy_context.get('sequence_order', 1)}
        
        Forneça guidelines específicas para seleção de vocabulário considerando:
        - Complexidade apropriada para o nível {cefr_level}
        - Relevância específica ao contexto "{unit_context}"
        - Progressão pedagógica adequada
        - Aplicabilidade comunicativa no contexto específico
        - Adequação ao tipo de unidade {unit_type}
        
        Responda com guidelines diretas e específicas para este contexto exato, não genéricas."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.warning(f"Erro na análise CEFR via IA: {str(e)}")
            return self._minimal_cefr_fallback(cefr_level)
    
    async def _analyze_phonetic_complexity_ai(
        self, 
        vocabulary_items: List[VocabularyItem], 
        cefr_level: str
    ) -> str:
        """Análise contextual via IA da complexidade fonética."""
        
        system_prompt = """Você é um especialista em análise fonética e complexidade de pronúncia para brasileiros.
        
        Analise a complexidade fonética do vocabulário considerando:
        - Padrões de sílabas e stress
        - Sons desafiadores para brasileiros
        - Adequação ao nível CEFR
        - Distribuição de dificuldades"""
        
        # Preparar dados do vocabulário
        vocab_analysis = []
        for item in vocabulary_items[:10]:  # Limitar para análise
            word_info = f"{item.word}"
            if item.phoneme:
                word_info += f" [{item.phoneme}]"
            if item.syllable_count:
                word_info += f" ({item.syllable_count} sílabas)"
            vocab_analysis.append(word_info)
        
        human_prompt = f"""Analise a complexidade fonética deste vocabulário:
        
        VOCABULÁRIO: {'; '.join(vocab_analysis)}
        NÍVEL CEFR: {cefr_level}
        TOTAL DE PALAVRAS: {len(vocabulary_items)}
        
        Analise:
        - Nível geral de complexidade fonética
        - Padrões de stress predominantes
        - Sons específicos desafiadores para brasileiros
        - Distribuição de complexidade silábica
        - Adequação ao nível {cefr_level}
        
        Retorne classificação: "simple", "medium", "complex", ou "very_complex" com justificativa."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Extrair classificação da resposta
            content = response.content.lower()
            if "very_complex" in content:
                return "very_complex"
            elif "complex" in content:
                return "complex"
            elif "simple" in content:
                return "simple"
            else:
                return "medium"
                
        except Exception as e:
            logger.warning(f"Erro na análise fonética via IA: {str(e)}")
            return "medium"
    
    async def _calculate_quality_metrics_ai(
        self, 
        vocabulary_items: List[VocabularyItem], 
        enriched_context: Dict[str, Any],
        rag_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calcular métricas de qualidade usando análise IA."""
        
        if not vocabulary_items:
            return {"context_relevance": 0.0, "new_words_count": 0, "reinforcement_count": 0}
        
        # Contagens básicas (mantidas - são contadores simples)
        new_words = [item for item in vocabulary_items if not item.is_reinforcement]
        reinforcement_words = [item for item in vocabulary_items if item.is_reinforcement]
        
        # ANÁLISE VIA IA: Relevância contextual
        context_relevance = await self._analyze_context_relevance_ai(
            vocabulary_items, enriched_context
        )
        
        # Cobertura de fonemas (mantida - é análise técnica)
        phonemes_used = set()
        for item in vocabulary_items:
            if item.phoneme:
                clean_phoneme = item.phoneme.strip('/[]')
                phonemes_used.update(clean_phoneme.replace(' ', ''))
        
        phoneme_coverage = {
            "total_unique_phonemes": len(phonemes_used),
            "coverage_score": int(min(len(phonemes_used) / 30, 1.0) * 100)  # Convert to percentage int
        }
        
        # Distribuição por classe de palavra (mantida - é contagem)
        word_classes = {}
        for item in vocabulary_items:
            word_class = item.word_class
            word_classes[word_class] = word_classes.get(word_class, 0) + 1
        
        return {
            "context_relevance": context_relevance,
            "new_words_count": len(new_words),
            "reinforcement_count": len(reinforcement_words),
            "phoneme_coverage": phoneme_coverage,
            "word_class_distribution": word_classes,
            "quality_score": (context_relevance + phoneme_coverage["coverage_score"]) / 2
        }
    
    async def _analyze_context_relevance_ai(
        self, 
        vocabulary_items: List[VocabularyItem], 
        enriched_context: Dict[str, Any]
    ) -> float:
        """Análise contextual via IA da relevância do vocabulário."""
        
        system_prompt = """Você é um especialista em avaliação de relevância contextual de vocabulário.
        
        Analise quão relevante o vocabulário é para o contexto específico da unidade."""
        
        # Preparar vocabulário para análise
        vocab_summary = [f"{item.word} ({item.word_class})" for item in vocabulary_items[:15]]
        unit_ctx = enriched_context.get("unit_context", {})
        
        human_prompt = f"""Avalie a relevância contextual deste vocabulário:
        
        VOCABULÁRIO: {', '.join(vocab_summary)}
        CONTEXTO DA UNIDADE: {unit_ctx.get('context', '')}
        TÍTULO: {unit_ctx.get('title', '')}
        NÍVEL: {unit_ctx.get('cefr_level', 'A2')}
        TIPO: {unit_ctx.get('unit_type', 'lexical_unit')}
        
        Avalie numa escala de 0.0 a 1.0:
        - Quão relevante este vocabulário é para o contexto específico
        - Se as palavras são apropriadas para o cenário
        - Se contribuem para objetivos comunicativos do contexto
        
        Retorne APENAS um número decimal entre 0.0 e 1.0 representando a relevância."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Extrair score numérico
            import re
            score_match = re.search(r'0\.\d+|1\.0', response.content)
            if score_match:
                return float(score_match.group())
            else:
                return 0.7  # Fallback padrão
                
        except Exception as e:
            logger.warning(f"Erro na análise de relevância via IA: {str(e)}")
            return 0.7
    
    async def _enrich_with_phonemes_ai(
        self, 
        vocabulary_items: List[VocabularyItem], 
        language_variant: str,
        unit_context: str
    ) -> List[VocabularyItem]:
        """Enriquecer itens com fonemas IPA usando análise IA quando necessário."""
        
        items_needing_phonemes = []
        complete_items = []
        
        # Separar itens que precisam de melhoria fonética
        for item in vocabulary_items:
            if not item.phoneme or item.phoneme.startswith("/placeholder_"):
                items_needing_phonemes.append(item)
            else:
                # Aplicar variante IPA (constante técnica mantida)
                item.ipa_variant = self._get_ipa_variant(language_variant)
                item.stress_pattern = self._estimate_stress_pattern(item.phoneme)
                complete_items.append(item)
        
        # ANÁLISE VIA IA: Gerar fonemas para itens que precisam
        if items_needing_phonemes:
            improved_items = await self._improve_phonemes_ai(
                items_needing_phonemes, language_variant, unit_context
            )
            complete_items.extend(improved_items)
        
        return complete_items
    
    async def _improve_phonemes_ai(
        self, 
        vocabulary_items: List[VocabularyItem], 
        language_variant: str,
        unit_context: str
    ) -> List[VocabularyItem]:
        """Melhorar fonemas usando IA contextual."""
        
        system_prompt = f"""Você é um especialista em fonética inglesa e transcrição IPA.
        
        Forneça transcrições IPA precisas para as palavras, considerando a variante {language_variant} e o contexto específico."""
        
        words_to_improve = [item.word for item in vocabulary_items[:10]]  # Limitar para performance
        
        human_prompt = f"""Forneça transcrições IPA para estas palavras:
        
        PALAVRAS: {', '.join(words_to_improve)}
        VARIANTE: {language_variant}
        CONTEXTO: {unit_context}
        
        Para cada palavra, retorne no formato: palavra: /transcrição/
        Use IPA padrão para {language_variant}.
        Considere o contexto para possíveis variações de pronúncia.
        
        Exemplo formato:
        hotel: /hoʊˈtɛl/
        reception: /rɪˈsɛpʃən/"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse da resposta
            phoneme_mapping = self._parse_phoneme_response(response.content)
            
            # Aplicar melhorias
            for item in vocabulary_items:
                if item.word in phoneme_mapping:
                    item.phoneme = phoneme_mapping[item.word]
                    item.ipa_variant = self._get_ipa_variant(language_variant)
                    item.stress_pattern = self._estimate_stress_pattern(item.phoneme)
                else:
                    # Fallback técnico para palavras não encontradas
                    item.phoneme = self._generate_basic_phoneme(item.word)
                    item.ipa_variant = self._get_ipa_variant(language_variant)
            
            return vocabulary_items
            
        except Exception as e:
            logger.warning(f"Erro na melhoria de fonemas via IA: {str(e)}")
            # Aplicar fallbacks técnicos
            for item in vocabulary_items:
                item.phoneme = self._generate_basic_phoneme(item.word)
                item.ipa_variant = self._get_ipa_variant(language_variant)
            return vocabulary_items
    
    async def _build_vocabulary_prompt(
        self, 
        enriched_context: Dict[str, Any], 
        target_count: int,
        cefr_guidelines: str
    ) -> List[Any]:
        """Construir prompt contextualizado para geração de vocabulário."""
        
        unit_ctx = enriched_context["unit_context"]
        hierarchy_ctx = enriched_context["hierarchy_context"]
        rag_ctx = enriched_context["rag_context"]
        images_ctx = enriched_context["images_context"]
        
        system_prompt = f"""You are an expert English vocabulary teacher creating contextualized vocabulary for {unit_ctx['cefr_level']} level students.

EDUCATIONAL CONTEXT:
- Course: {hierarchy_ctx['course_name']}
- Book: {hierarchy_ctx['book_name']}
- Unit: {unit_ctx['title']}
- Sequence: Unit {hierarchy_ctx['sequence_order']} of the book
- Context: {unit_ctx['context']}
- Level: {unit_ctx['cefr_level']}
- Language Variant: {unit_ctx['language_variant']}
- Unit Type: {unit_ctx['unit_type']}

CONTEXTUAL CEFR GUIDELINES: {cefr_guidelines}

RAG CONTEXT (Important for coherence):
- Words already taught: {', '.join(rag_ctx['taught_vocabulary'])}
- Progression level: {rag_ctx['progression_level']}
- Reinforcement candidates: {', '.join(rag_ctx['reinforcement_candidates'][:5])}

IMAGES ANALYSIS:
{"- Image vocabulary suggestions: " + ', '.join(images_ctx['vocabulary_suggestions']) if images_ctx['vocabulary_suggestions'] else "- No images analyzed"}
{"- Image themes: " + ', '.join(images_ctx['themes']) if images_ctx['themes'] else ""}

GENERATION REQUIREMENTS - STRICTLY ENFORCE:
1. Generate EXACTLY {target_count} vocabulary items - NO MORE, NO LESS
2. Avoid repeating words from "already taught" list unless for reinforcement (max 20%)
3. Focus on words visible/suggested in images when available
4. Ensure vocabulary follows the contextual guidelines above
5. CRITICAL: The response MUST contain exactly {target_count} items
5. Include 10-20% reinforcement words for review
6. Each word must include: word, IPA phoneme, Portuguese definition, contextual example
7. Prioritize practical, communicative vocabulary for this specific context
8. Use {unit_ctx['language_variant']} pronunciations

OUTPUT FORMAT: Return valid JSON array with this exact structure:
[
  {{
    "word": "example",
    "phoneme": "/ɪɡˈzæmpəl/",
    "definition": "exemplo, modelo",
    "example": "This is a good example of modern architecture.",
    "word_class": "noun",
    "frequency_level": "high",
    "context_relevance": 0.9,
    "is_reinforcement": false
  }}
]"""

        human_prompt = f"""MANDATORY: Generate EXACTLY {target_count} vocabulary items for the unit "{unit_ctx['title']}" in the context: "{unit_ctx['context']}"

⚠️  CRITICAL REQUIREMENT: Your response MUST contain exactly {target_count} vocabulary items.

Level: {unit_ctx['cefr_level']}
Type: {unit_ctx['unit_type']}

{"Image suggestions to prioritize: " + ', '.join(images_ctx['vocabulary_suggestions'][:10]) if images_ctx['vocabulary_suggestions'] else "No image context available."}

Remember:
- Avoid: {', '.join(rag_ctx['words_to_avoid'][:10])}
- Consider for reinforcement: {', '.join(rag_ctx['reinforcement_candidates'][:5])}
- Follow the contextual guidelines provided
- Make examples relevant to the specific context
- Ensure {unit_ctx['language_variant']} pronunciation

Generate the JSON array now:"""

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
    
    def _create_vocabulary_schema(self) -> Dict[str, Any]:
        """Create precise JSON schema for VocabularyItem list using LangChain 0.3 structured output."""
        return {
            "title": "VocabularyList",
            "description": "Schema for structured vocabulary items generation with phonetic and contextual data",
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "word": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 50,
                                "description": "Word in target language"
                            },
                            "phoneme": {
                                "type": "string",
                                "description": "Valid IPA phonetic transcription between / / or [ ]"
                            },
                            "definition": {
                                "type": "string",
                                "minLength": 5,
                                "maxLength": 200,
                                "description": "Definition in Portuguese"
                            },
                            "example": {
                                "type": "string",
                                "minLength": 10,
                                "maxLength": 300,
                                "description": "Usage example in context"
                            },
                            "word_class": {
                                "type": "string",
                                "enum": [
                                    "noun", "verb", "adjective", "adverb", "preposition", 
                                    "conjunction", "article", "pronoun", "interjection",
                                    "modal", "auxiliary", "determiner", "numeral",
                                    "phrasal verb", "verb phrase", "noun phrase", "compound noun",
                                    "collocation", "idiom", "expression", "chunk", "phrase",
                                    "prepositional phrase", "adverbial phrase", "adjective phrase",
                                    "fixed expression", "compound adjective", "question_word"
                                ],
                                "description": "Grammatical class - must be one of the valid options"
                            },
                            "frequency_level": {
                                "type": "string",
                                "enum": ["high", "medium", "low", "very_high", "very_low"],
                                "default": "medium",
                                "description": "Frequency level"
                            },
                            "context_relevance": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Contextual relevance (0.0 to 1.0)"
                            },
                            "is_reinforcement": {
                                "type": "boolean",
                                "default": False,
                                "description": "Is reinforcement word?"
                            },
                            "ipa_variant": {
                                "type": "string",
                                "enum": ["general_american", "received_pronunciation", "australian_english", "canadian_english", "irish_english", "scottish_english"],
                                "default": "general_american",
                                "description": "IPA variant"
                            },
                            "stress_pattern": {
                                "type": "string",
                                "description": "Stress pattern (optional)"
                            },
                            "syllable_count": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 8,
                                "description": "Number of syllables (optional)"
                            },
                            "alternative_pronunciations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "default": [],
                                "description": "Alternative pronunciations"
                            }
                        },
                        "required": ["word", "phoneme", "definition", "example", "word_class"],
                        "additionalProperties": False
                    },
                    "minItems": 1,
                    "maxItems": 50,
                    "description": "List of vocabulary items"
                }
            },
            "required": ["items"],
            "additionalProperties": False
        }
    
    async def _generate_vocabulary_llm(self, prompt_messages: List[Any]) -> List[Dict[str, Any]]:
        """Gerar vocabulário usando LangChain 0.3 structured output para evitar erros de validação."""
        try:
            logger.info("🤖 Consultando LLM para geração de vocabulário com structured output...")
            
            # Usar LangChain 0.3 with_structured_output para forçar formato correto
            vocabulary_schema = self._create_vocabulary_schema()
            structured_llm = self.llm.with_structured_output(vocabulary_schema)
            
            # Gerar usando structured output
            vocabulary_response = await structured_llm.ainvoke(prompt_messages)
            
            # Extrair lista de items do objeto estruturado
            if isinstance(vocabulary_response, dict) and "items" in vocabulary_response:
                vocabulary_list = vocabulary_response["items"]
            elif isinstance(vocabulary_response, list):
                vocabulary_list = vocabulary_response
            else:
                logger.warning("⚠️ Structured output formato inesperado, convertendo...")
                vocabulary_list = list(vocabulary_response) if hasattr(vocabulary_response, '__iter__') else []
            
            # Garantir campos obrigatórios com fallbacks seguros
            vocabulary_list = self._ensure_vocabulary_required_fields(vocabulary_list)
            
            # Validar estrutura de cada item
            vocabulary_list = self._clean_vocabulary_items(vocabulary_list)
            
            logger.info(
                f"✅ LLM retornou {len(vocabulary_list)} itens de vocabulário estruturados: "
                f"palavras validadas e IPA formatado"
            )
            return vocabulary_list
            
        except Exception as e:
            logger.error(f"❌ Erro na consulta ao LLM com structured output: {str(e)}")
            logger.info("🔄 Tentando fallback sem structured output...")
            return await self._generate_vocabulary_llm_fallback(prompt_messages)
    
    def _ensure_vocabulary_required_fields(self, vocabulary_list: List[Any]) -> List[Dict[str, Any]]:
        """Garantir campos obrigatórios em cada item de vocabulário."""
        cleaned_list = []
        
        for i, item in enumerate(vocabulary_list):
            if isinstance(item, dict):
                # Garantir campos obrigatórios
                cleaned_item = {
                    "word": str(item.get("word", f"word_{i+1}")).strip(),
                    "phoneme": str(item.get("phoneme", "/wɚd/")).strip(),
                    "definition": str(item.get("definition", "Definição em português")).strip(),
                    "example": str(item.get("example", "Exemplo de uso em contexto")).strip(),
                    "word_class": str(item.get("word_class", "noun")).lower().strip(),
                    "frequency_level": str(item.get("frequency_level", "medium")).lower().strip(),
                    "context_relevance": float(item.get("context_relevance", 0.8)),
                    "is_reinforcement": bool(item.get("is_reinforcement", False)),
                    "ipa_variant": str(item.get("ipa_variant", "general_american")).lower().strip(),
                    "stress_pattern": item.get("stress_pattern"),
                    "syllable_count": item.get("syllable_count"),
                    "alternative_pronunciations": item.get("alternative_pronunciations", [])
                }
                
                # Validar tamanhos mínimos
                if len(cleaned_item["word"]) >= 1 and len(cleaned_item["definition"]) >= 5:
                    cleaned_list.append(cleaned_item)
            
        return cleaned_list
    
    def _clean_vocabulary_items(self, vocabulary_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Limpar e validar estrutura de cada item de vocabulário."""
        cleaned_list = []
        
        for item in vocabulary_list:
            try:
                # Validar phoneme IPA
                phoneme = item.get("phoneme", "")
                if not phoneme.startswith(("/", "[")) and not phoneme.endswith(("/", "]")):
                    # Se não tem delimitadores, adicionar / /
                    if "/" not in phoneme and "[" not in phoneme:
                        item["phoneme"] = f"/{phoneme}/"
                elif phoneme.startswith(("/", "[")) and not phoneme.endswith(("/", "]")):
                    # Se tem início mas não fim, adicionar fim correspondente
                    if phoneme.startswith("/"):
                        item["phoneme"] = phoneme + "/"
                    elif phoneme.startswith("["):
                        item["phoneme"] = phoneme + "]"
                elif not phoneme.startswith(("/", "[")) and phoneme.endswith(("/", "]")):
                    # Se tem fim mas não início, adicionar início correspondente
                    if phoneme.endswith("/"):
                        item["phoneme"] = "/" + phoneme
                    elif phoneme.endswith("]"):
                        item["phoneme"] = "[" + phoneme
                
                # Limpar alternative_pronunciations
                if "alternative_pronunciations" in item:
                    if isinstance(item["alternative_pronunciations"], list):
                        item["alternative_pronunciations"] = [
                            str(pron).strip() for pron in item["alternative_pronunciations"] 
                            if pron and str(pron).strip()
                        ]
                    else:
                        item["alternative_pronunciations"] = []
                
                # Validar context_relevance
                if "context_relevance" in item:
                    try:
                        relevance = float(item["context_relevance"])
                        item["context_relevance"] = max(0.0, min(1.0, relevance))
                    except (ValueError, TypeError):
                        item["context_relevance"] = 0.8
                
                cleaned_list.append(item)
                
            except Exception as e:
                logger.warning(f"⚠️ Erro ao limpar item de vocabulário: {str(e)}, item ignorado")
                continue
        
        return cleaned_list
    
    async def _process_and_validate_vocabulary(
        self, 
        raw_vocabulary: List[Dict[str, Any]], 
        enriched_context: Dict[str, Any]
    ) -> List[VocabularyItem]:
        """Processar e validar itens de vocabulário."""
        validated_items = []
        
        unit_ctx = enriched_context["unit_context"]
        
        for i, raw_item in enumerate(raw_vocabulary):
            try:
                # Aplicar valores padrão se necessário
                processed_item = {
                    "word": raw_item.get("word", f"word_{i}").lower().strip(),
                    "phoneme": raw_item.get("phoneme", f"/word_{i}/"),
                    "definition": raw_item.get("definition", "definição não disponível"),
                    "example": raw_item.get("example", f"Example with {raw_item.get('word', 'word')}."),
                    "word_class": raw_item.get("word_class", "noun"),
                    "frequency_level": raw_item.get("frequency_level", "medium"),
                    "context_relevance": raw_item.get("context_relevance", 0.7),
                    "is_reinforcement": raw_item.get("is_reinforcement", False),
                    "ipa_variant": self._get_ipa_variant(unit_ctx["language_variant"]),
                    "syllable_count": self._estimate_syllable_count(raw_item.get("word", "")),
                }
                
                # Validar usando Pydantic
                vocabulary_item = VocabularyItem(**processed_item)
                validated_items.append(vocabulary_item)
                
            except ValidationError as e:
                logger.warning(f"⚠️ Item {i+1} inválido, pulando: {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"⚠️ Erro ao processar item {i+1}: {str(e)}")
                continue
        
        logger.info(f"✅ {len(validated_items)} itens validados de {len(raw_vocabulary)} originais")
        if len(validated_items) < len(raw_vocabulary):
            logger.warning(f"⚠️ {len(raw_vocabulary) - len(validated_items)} itens foram rejeitados na validação")
        return validated_items
    
    async def _apply_rag_filtering(
        self, 
        vocabulary_items: List[VocabularyItem], 
        rag_context: Dict[str, Any]
    ) -> List[VocabularyItem]:
        """Aplicar filtros RAG para evitar repetições e melhorar progressão."""
        
        taught_words = set(word.lower() for word in rag_context.get("taught_vocabulary", []))
        reinforcement_candidates = set(word.lower() for word in rag_context.get("reinforcement_candidates", []))
        
        filtered_items = []
        new_words_count = 0
        reinforcement_count = 0
        max_reinforcement = min(max(1, len(vocabulary_items) // 5), 10)  # Máximo 20% reforço, mínimo 1, máximo 10
        
        # Primeiro, adicionar palavras novas
        for item in vocabulary_items:
            word_lower = item.word.lower()
            
            if word_lower not in taught_words:
                # Palavra nova - adicionar
                item.is_reinforcement = False
                filtered_items.append(item)
                new_words_count += 1
                
            elif (word_lower in reinforcement_candidates and 
                  reinforcement_count < max_reinforcement):
                # Palavra para reforço - adicionar com limite
                item.is_reinforcement = True
                filtered_items.append(item)
                reinforcement_count += 1
            
            # Parar se atingiu o número desejado
            if len(filtered_items) >= 30:  # Gerar um pouco mais para ter opções
                break
        
        logger.info(
            f"🎯 RAG filtering: {new_words_count} novas, {reinforcement_count} reforço (de {len(vocabulary_items)} originais)"
        )
        
        return filtered_items
    
    async def _ensure_exact_target_count(
        self,
        items: List[VocabularyItem],
        target_count: int,
        enriched_context: Dict[str, Any],
        rag_context: Dict[str, Any]
    ) -> List[VocabularyItem]:
        """Garantir que tenhamos exatamente target_count palavras."""
        
        if len(items) == target_count:
            logger.info(f"✅ Target count perfeito: {target_count} palavras")
            return items
        
        if len(items) > target_count:
            # Se temos mais, cortar para o target_count
            logger.info(f"🔪 Cortando de {len(items)} para {target_count} palavras")
            return items[:target_count]
        
        if len(items) < target_count:
            # Se temos menos, tentar gerar mais
            missing_count = target_count - len(items)
            logger.warning(f"⚠️ Faltam {missing_count} palavras. LLM gerou apenas {len(items)} de {target_count}")
            
            # Por agora, repetir algumas das melhores palavras
            # TODO: Implementar geração adicional se necessário
            existing_words = set(item.word.lower() for item in items)
            
            # Gerar palavras básicas via IA se necessário
            if len(items) < target_count:
                words_needed = target_count - len(items)
                try:
                    logger.info(f"🤖 Gerando {words_needed} palavras básicas via IA...")
                    
                    # Carregar prompt para fallback de vocabulário
                    unit_context = enriched_context.get("unit_context", {}).get("context", "general English vocabulary")
                    cefr_level = enriched_context.get("unit_context", {}).get("cefr_level", "A2")
                    language_variant = enriched_context.get("unit_context", {}).get("language_variant", "american_english")
                    ipa_variant = self._get_ipa_variant(language_variant)
                    
                    # Construir unit_data no formato correto
                    unit_data_fallback = {
                        "context": unit_context,
                        "cefr_level": cefr_level,
                        "language_variant": language_variant,
                        "unit_type": "lexical_unit",
                        "title": "Vocabulary Fallback Generation"
                    }
                    
                    # Construir hierarchy_context básico
                    hierarchy_context_fallback = {
                        "course_name": "Fallback Course",
                        "book_name": "Fallback Book", 
                        "sequence_order": 1
                    }
                    
                    # Construir rag_context com palavras existentes
                    rag_context_fallback = {
                        "taught_vocabulary": [item.word for item in items],
                        "progression_level": "intermediate",
                        "vocabulary_density": 0
                    }
                    
                    # Images analysis vazio para fallback
                    images_analysis_fallback = {
                        "success": False,
                        "consolidated_vocabulary": {"vocabulary": []},
                        "individual_analyses": []
                    }
                    
                    fallback_prompt = await self.prompt_generator.generate_vocabulary_prompt(
                        unit_data=unit_data_fallback,
                        hierarchy_context=hierarchy_context_fallback,
                        rag_context=rag_context_fallback,
                        images_analysis=images_analysis_fallback,
                        target_count=words_needed
                    )
                    
                    # Gerar palavras básicas via LLM
                    response = await self.llm.ainvoke(fallback_prompt)
                    
                    # Parse da resposta
                    import json
                    response_content = response.content
                    if "```json" in response_content:
                        response_content = response_content.split("```json")[1].split("```")[0]
                    
                    basic_words_data = json.loads(response_content)
                    
                    # Converter para VocabularyItems
                    for word_data in basic_words_data[:words_needed]:
                        try:
                            vocab_item = VocabularyItem(
                                word=word_data["word"],
                                phoneme=word_data["phoneme"],
                                definition=word_data["definition"],
                                example=word_data["example"],
                                word_class=word_data["word_class"],
                                frequency_level=word_data.get("frequency_level", "high"),
                                context_relevance=word_data.get("context_relevance", 0.8),
                                is_reinforcement=word_data.get("is_reinforcement", False),
                                ipa_variant=ipa_variant,
                                syllable_count=len(word_data["word"].split()) # Estimativa simples
                            )
                            items.append(vocab_item)
                            logger.info(f"➕ Adicionada palavra básica via IA: {word_data['word']}")
                        except Exception as e:
                            logger.warning(f"Erro ao processar palavra básica {word_data.get('word', 'unknown')}: {e}")
                            
                except Exception as e:
                    logger.error(f"❌ Erro na geração de palavras básicas via IA: {e}")
                    # Fallback de emergência via AI (último recurso)
                    logger.info("🔄 Usando fallback de emergência com AI...")
                    try:
                        # Construir dados para emergência
                        emergency_unit_data = {
                            "context": "emergency basic words",
                            "cefr_level": "A1",
                            "language_variant": "american_english",
                            "unit_type": "lexical_unit",
                            "title": "Emergency Vocabulary"
                        }
                        
                        emergency_hierarchy_context = {
                            "course_name": "Emergency Course",
                            "book_name": "Emergency Book",
                            "sequence_order": 1
                        }
                        
                        emergency_rag_context = {
                            "taught_vocabulary": [],
                            "progression_level": "beginner",
                            "vocabulary_density": 0
                        }
                        
                        emergency_images_analysis = {
                            "success": False,
                            "consolidated_vocabulary": {"vocabulary": []},
                            "individual_analyses": []
                        }
                        
                        emergency_prompt = await self.prompt_generator.generate_vocabulary_prompt(
                            unit_data=emergency_unit_data,
                            hierarchy_context=emergency_hierarchy_context,
                            rag_context=emergency_rag_context,
                            images_analysis=emergency_images_analysis,
                            target_count=words_needed
                        )
                        emergency_response = await self.llm.ainvoke(emergency_prompt)
                        emergency_data = self._extract_vocabulary_from_text(emergency_response.content)
                        simple_fallback = [item.get("word", "").lower() for item in emergency_data if item.get("word")]
                        if not simple_fallback:
                            raise Exception("Emergency AI também falhou")
                    except Exception as emergency_error:
                        logger.error(f"❌ AI de emergência falhou: {emergency_error}")
                        # Fallback técnico final apenas se tudo falhar
                        # Fallback words com IPA correto
                        simple_fallback_with_ipa = [
                            ("good", "/ɡʊd/", "adjective"),
                            ("help", "/hɛlp/", "verb"),
                            ("time", "/taɪm/", "noun"),
                            ("person", "/ˈpɜrsən/", "noun"),
                            ("important", "/ɪmˈpɔrtənt/", "adjective"),
                            ("work", "/wɜrk/", "verb"),
                            ("home", "/hoʊm/", "noun"),
                            ("water", "/ˈwɔtər/", "noun")
                        ]
                        
                    for word, phoneme, word_class in simple_fallback_with_ipa[:words_needed]:
                        if word not in existing_words:
                            try:
                                vocab_item = VocabularyItem(
                                    word=word,
                                    phoneme=phoneme,
                                    definition=f"{word} - basic English word",
                                    example=f"This is an example with {word}.",
                                    word_class=word_class,
                                    frequency_level="high",
                                    context_relevance=0.7,
                                    is_reinforcement=False,
                                    ipa_variant=ipa_variant,
                                    syllable_count=len([c for c in phoneme if c in 'aeiouæɑɒɔɪɛɜɝʊʌ'])
                                )
                                # Note: Este fallback pode falhar na validação IPA, que é intencional
                                items.append(vocab_item)
                                logger.warning(f"⚠️ Adicionada palavra fallback simples: {word}")
                            except Exception as validation_error:
                                logger.error(f"❌ Fallback simples também falhou para {word}: {validation_error}")
            
            logger.info(f"✅ Target count ajustado: {len(items)} palavras")
            return items[:target_count]
        
        return items
    
    # =============================================================================
    # FALLBACKS MÍNIMOS (APENAS PARA ERROS DE IA)
    # =============================================================================
    
    def _minimal_cefr_fallback(self, cefr_level: str) -> str:
        """Fallback mínimo para guidelines CEFR em caso de erro de IA."""
        return f"Vocabulário apropriado para {cefr_level} com foco comunicativo no contexto específico"
    
    async def _generate_vocabulary_llm_fallback(self, prompt_messages: List[Any]) -> List[Dict[str, Any]]:
        """Fallback para geração sem structured output quando structured falha."""
        try:
            logger.info("🔄 Tentando geração fallback sem structured output...")
            
            response = await self.llm.ainvoke(prompt_messages)
            content = response.content
            
            # Tentar parsear JSON
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                
                # CORREÇÃO: Limpar JSON malformado com aspas extras
                content_cleaned = self._clean_malformed_json(content)
                vocabulary_list = json.loads(content_cleaned)
                
                if not isinstance(vocabulary_list, list):
                    raise ValueError("Response não é uma lista")
                
                # Aplicar limpeza rigorosa no fallback
                vocabulary_list = self._ensure_vocabulary_required_fields(vocabulary_list)
                vocabulary_list = self._clean_vocabulary_items(vocabulary_list)
                
                logger.info(f"✅ Fallback JSON parseou {len(vocabulary_list)} itens de vocabulário")
                return vocabulary_list
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"⚠️ Erro ao parsear JSON no fallback: {str(e)}")
                # Tentar adicionar ]} no final se estiver truncado
                if '"is_reinforce' in content and not content.strip().endswith(']'):
                    logger.info("🔧 Tentando corrigir JSON truncado...")
                    content_fixed = content.rstrip() + '": false}]'
                    try:
                        vocabulary_list = json.loads(content_fixed)
                        vocabulary_list = self._ensure_vocabulary_required_fields(vocabulary_list)
                        vocabulary_list = self._clean_vocabulary_items(vocabulary_list)
                        logger.info(f"✅ JSON corrigido com sucesso! {len(vocabulary_list)} itens")
                        return vocabulary_list
                    except:
                        pass
                return self._extract_vocabulary_from_text(content)
                
        except Exception as e:
            logger.error(f"❌ Erro no fallback: {str(e)}")
            return await self._generate_fallback_vocabulary_ai()
    
    async def _generate_fallback_vocabulary_ai(self) -> List[Dict[str, Any]]:
        """Gerar vocabulário de fallback usando IA quando LLM principal falha."""
        
        system_prompt = """Você é um professor de inglês gerando vocabulário básico de emergência.
        
        Gere vocabulário simples e útil para estudantes."""
        
        human_prompt = """Gere 5 palavras básicas de vocabulário em inglês no formato JSON:
        
        [
          {
            "word": "palavra",
            "phoneme": "/fonema/",
            "definition": "definição em português",
            "example": "Example sentence.",
            "word_class": "noun",
            "frequency_level": "high",
            "context_relevance": 0.8,
            "is_reinforcement": false
          }
        ]"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Tentar parsear resposta
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            vocabulary_list = json.loads(content)
            
            if isinstance(vocabulary_list, list) and len(vocabulary_list) > 0:
                logger.info("✅ Fallback IA gerou vocabulário de emergência")
                return vocabulary_list
            else:
                raise ValueError("Fallback IA não retornou lista válida")
                
        except Exception as e:
            logger.warning(f"⚠️ Fallback IA também falhou: {str(e)}")
            return self._minimal_hardcoded_fallback()
    
    def _minimal_hardcoded_fallback(self) -> List[Dict[str, Any]]:
        """Fallback mínimo com dados hard-coded apenas para emergências críticas."""
        logger.warning("⚠️ Usando fallback hard-coded mínimo - apenas para emergências")
        
        return [
            {
                "word": "vocabulary",
                "phoneme": "/voʊˈkæbjəˌlɛri/",
                "definition": "vocabulário",
                "example": "Learning vocabulary is important.",
                "word_class": "noun",
                "frequency_level": "high",
                "context_relevance": 0.7,
                "is_reinforcement": False
            },
            {
                "word": "learning",
                "phoneme": "/ˈlɜrnɪŋ/",
                "definition": "aprendizagem",
                "example": "Learning English takes practice.",
                "word_class": "noun",
                "frequency_level": "high",
                "context_relevance": 0.7,
                "is_reinforcement": False
            }
        ]
    
    # =============================================================================
    # HELPER METHODS (CONSTANTES TÉCNICAS E UTILITÁRIOS)
    # =============================================================================
    
    def _select_reinforcement_words(self, taught_vocabulary: List[str]) -> List[str]:
        """Selecionar palavras candidatas para reforço estratégico."""
        # Algoritmo: 8 palavras estratégicas (5-15 posições atrás) para conexão sutil
        if len(taught_vocabulary) < 15:
            return taught_vocabulary[-8:] if taught_vocabulary else []
        return taught_vocabulary[-15:-5] if len(taught_vocabulary) >= 15 else []
    
    def _get_ipa_variant(self, language_variant: str) -> str:
        """Mapear variante de idioma para variante IPA (constante técnica)."""
        return IPA_VARIANT_MAPPING.get(language_variant, "general_american")
    
    def _estimate_syllable_count(self, word: str) -> int:
        """Estimar número de sílabas (algoritmo técnico simples)."""
        if not word:
            return 1
            
        word = word.lower()
        syllables = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in VOWEL_SOUNDS
            if is_vowel and not prev_was_vowel:
                syllables += 1
            prev_was_vowel = is_vowel
        
        # Ajustes técnicos
        if word.endswith('e'):
            syllables -= 1
        if syllables == 0:
            syllables = 1
            
        return syllables
    
    def _generate_basic_phoneme(self, word: str) -> str:
        """Gerar fonema básico para palavra (fallback técnico)."""
        # Implementação técnica básica - para casos de emergência
        return f"/{word.replace('e', 'ə').replace('a', 'æ')}/"
    
    def _estimate_stress_pattern(self, phoneme: str) -> str:
        """Estimar padrão de stress do fonema (análise técnica)."""
        if 'ˈ' in phoneme:
            return "primary_first"
        elif 'ˌ' in phoneme:
            return "secondary_first"
        else:
            return "unstressed"
    
    def _clean_malformed_json(self, content: str) -> str:
        """Limpar JSON malformado que vem do OpenAI com aspas extras."""
        import re
        
        # Log inicial para debug
        logger.info(f"🧹 Limpando JSON malformado...")
        
        # Padrão 1: Remover aspas extras no final de valores de string
        # Exemplo: "menu"" -> "menu"
        content = re.sub(r'(["\w\s\-\'\.]+)""', r'\1"', content)
        
        # Padrão 2: Corrigir aspas extras em valores específicos
        # Exemplo: "word": "menu"", -> "word": "menu",
        content = re.sub(r'":\s*"([^"]+)""', r'": "\1"', content)
        
        # Padrão 3: Corrigir aspas duplas no final de phonemes
        # Exemplo: "/ˈmɛn.juː/"" -> "/ˈmɛn.juː/"
        content = re.sub(r'(/[^/]+/)""', r'\1"', content)
        
        # Padrão 4: Limpar aspas extras gerais
        content = re.sub(r'""', r'"', content)
        
        # Padrão 5: Garantir que não há vírgulas duplicadas ou espaços extras
        content = re.sub(r',\s*,', r',', content)
        content = re.sub(r'\s+', ' ', content)
        
        logger.info(f"✅ JSON limpo aplicado")
        
        return content
    
    def _extract_vocabulary_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extrair vocabulário de texto quando JSON parsing falha (parser técnico)."""
        vocabulary = []
        lines = text.split('\n')
        
        current_item = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parser técnico para extrair informações básicas
            if 'word:' in line.lower() or '"word"' in line:
                if current_item:
                    vocabulary.append(current_item)
                    current_item = {}
                word = line.split(':')[-1].strip().strip('"').strip(',')
                current_item['word'] = word
            elif 'phoneme:' in line.lower() or '"phoneme"' in line:
                phoneme = line.split(':')[-1].strip().strip('"').strip(',')
                current_item['phoneme'] = phoneme
            elif 'definition:' in line.lower() or '"definition"' in line:
                definition = line.split(':')[-1].strip().strip('"').strip(',')
                current_item['definition'] = definition
            elif 'example:' in line.lower() or '"example"' in line:
                example = line.split(':')[-1].strip().strip('"').strip(',')
                current_item['example'] = example
        
        if current_item:
            vocabulary.append(current_item)
        
        # Preencher campos faltantes com padrões técnicos
        for item in vocabulary:
            item.setdefault('word_class', 'noun')
            item.setdefault('frequency_level', 'medium')
            item.setdefault('context_relevance', 0.7)
            item.setdefault('is_reinforcement', False)
        
        return vocabulary
    
    def _parse_phoneme_response(self, response_content: str) -> Dict[str, str]:
        """Parser técnico para extrair fonemas da resposta IA."""
        phoneme_mapping = {}
        lines = response_content.split('\n')
        
        for line in lines:
            if ':' in line and '/' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    word = parts[0].strip()
                    phoneme_part = parts[1].strip()
                    
                    # Extrair fonema entre /.../ 
                    import re
                    phoneme_match = re.search(r'/[^/]+/', phoneme_part)
                    if phoneme_match:
                        phoneme_mapping[word] = phoneme_match.group()
        
        return phoneme_mapping
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Obter status do serviço."""
        return {
            "service": "VocabularyGeneratorService",
            "status": "active",
            "ai_integration": "100% contextual analysis",
            "cache_system": "disabled_as_requested",
            "storage": "supabase_integration",
            "llm_model": self.openai_config["model"],
            "constants_maintained": list(IPA_VARIANT_MAPPING.keys()),
            "ai_analysis_methods": [
                "_analyze_cefr_guidelines_ai",
                "_analyze_phonetic_complexity_ai", 
                "_calculate_quality_metrics_ai",
                "_analyze_context_relevance_ai",
                "_enrich_with_phonemes_ai",
                "_improve_phonemes_ai"
            ]
        }
    
    async def validate_generation_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parâmetros de geração."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validações básicas
        required_fields = ["unit_data", "hierarchy_context", "rag_context"]
        for field in required_fields:
            if field not in params:
                validation_result["errors"].append(f"Campo obrigatório ausente: {field}")
                validation_result["valid"] = False
        
        # Validações específicas
        unit_data = params.get("unit_data", {})
        if not unit_data.get("context"):
            validation_result["warnings"].append("Contexto da unidade vazio - pode afetar qualidade")
        
        if not params.get("images_analysis", {}).get("success"):
            validation_result["warnings"].append("Análise de imagens não disponível")
        
        target_count = params.get("target_vocabulary_count", 25)
        if target_count < 10 or target_count > 50:
            validation_result["warnings"].append(f"Target count {target_count} fora do range recomendado (10-50)")
        
        return validation_result