# src/core/unit_models.py - ATUALIZADO PARA PYDANTIC V2 COMPLETO
"""Modelos específicos para o sistema IVO V2 com hierarquia Course → Book → Unit."""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator, ValidationInfo, ValidationError, ConfigDict
from datetime import datetime
from fastapi import UploadFile
import re
import time        # Para timestamps
import json        # Para parsing JSON  
import uuid        # Para UUIDs
import logging     # Para logs
from pathlib import Path

from .enums import (
    CEFRLevel, LanguageVariant, UnitType, AimType, 
    TipStrategy, GrammarStrategy, AssessmentType, 
    UnitStatus, ContentType
)


# =============================================================================
# INPUT MODELS (Form Data) - ATUALIZADOS COM HIERARQUIA E PYDANTIC V2
# =============================================================================

class UnitCreateRequest(BaseModel):
    """Request para criação de unidade via form data - REQUER HIERARQUIA."""
    # HIERARQUIA OBRIGATÓRIA (novos campos)
    course_id: str = Field(..., description="ID do curso (obrigatório)")
    book_id: str = Field(..., description="ID do book (obrigatório)")
    
    # Dados da unidade (existentes)
    context: Optional[str] = Field(None, description="Contexto opcional da unidade")
    cefr_level: CEFRLevel = Field(..., description="Nível CEFR")
    language_variant: LanguageVariant = Field(..., description="Variante do idioma")
    unit_type: UnitType = Field(..., description="Tipo de unidade (lexical ou grammar)")
    
    @field_validator('book_id')
    @classmethod
    def validate_book_not_empty(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("book_id é obrigatório")
        return v
    
    @field_validator('course_id')
    @classmethod
    def validate_course_not_empty(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("course_id é obrigatório")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "course_id": "course_english_beginners",
                "book_id": "book_foundation_a1",
                "context": "Hotel reservation and check-in procedures",
                "cefr_level": "B1",
                "language_variant": "american_english",
                "unit_type": "lexical_unit"
            }
        }
    }


# =============================================================================
# VOCABULARY MODELS - ATUALIZADO COM VALIDAÇÃO IPA COMPLETA E PYDANTIC V2
# =============================================================================

class VocabularyItem(BaseModel):
    """Item de vocabulário com fonema IPA validado - VERSÃO COMPLETA PYDANTIC V2."""
    word: str = Field(..., min_length=1, max_length=50, description="Palavra no idioma alvo")
    phoneme: str = Field(..., description="Transcrição fonética IPA válida")
    definition: str = Field(..., min_length=1, max_length=200, description="Definition in English")
    example: str = Field(..., min_length=1, max_length=300, description="Example of usage in context")
    word_class: str = Field(..., description="Classe gramatical")
    frequency_level: str = Field("medium", description="Nível de frequência")
    
    # NOVOS CAMPOS PARA PROGRESSÃO
    context_relevance: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevância contextual")
    is_reinforcement: Optional[bool] = Field(False, description="É palavra de reforço?")
    first_introduced_unit: Optional[str] = Field(None, description="Unidade onde foi introduzida")
    
    # NOVOS CAMPOS PARA IPA E FONEMAS
    ipa_variant: str = Field("general_american", description="Variante IPA")
    stress_pattern: Optional[str] = Field(None, description="Padrão de stress")
    syllable_count: Optional[int] = Field(None, ge=1, le=8, description="Número de sílabas")
    alternative_pronunciations: List[str] = Field(default=[], description="Pronúncias alternativas")
    
    @field_validator('phoneme')
    @classmethod
    def validate_ipa_phoneme(cls, v: str) -> str:
        """Validar que o fonema usa símbolos IPA válidos - FLEXÍVEL."""
        if not v:
            raise ValueError("Fonema é obrigatório")
        
        # Verificar se está entre delimitadores IPA corretos
        if not ((v.startswith('/') and v.endswith('/')) or 
                (v.startswith('[') and v.endswith(']'))):
            raise ValueError("Fonema deve estar entre / / (fonêmico) ou [ ] (fonético)")
        
        # SÍMBOLOS IPA COMPLETOS + diacríticos + separadores para frases
        valid_ipa_chars = set(
            # Vogais básicas e avançadas (incluindo todas as vogais standard)
            'aæəɑɒɔɪɛɜɝɨɉʊʌʏyeioubcdfɡhijklmnpqrstuɥvwxyzAEIOUɪɛeɔɒɑʌʊəɜɨʏɉæ'
            # R-colored vowels (importantes para inglês americano)
            'ɚɝ'  # ɚ = r-colored schwa, ɝ = r-colored mid-central vowel
            # Consoantes especiais
            'θðʃʒʧʤŋɹɻɾɸβçʝɠʔɲɟcɕʑɖɭɽʈɳʂʐɻʋ'
            # SÍMBOLOS FALTANTES IDENTIFICADOS (inglês americano)
            'ɑ'  # Vogal /ɑ/ em "father" (já presente mas garantindo)
            # Consoantes latinas básicas (fallback para casos de emergency)
            'gptk'  # Adicionado para fallback de emergency
            # Diacríticos e modificadores
            'ʰʷʲˤ̥̩̯̰̹̜̟̘̙̞̠̃̊'
            # Suprassegmentais
            'ˈˌːˑ'
            # Articulação
            '̪̺̻̼̝̞̘̙̗̖̯̰̱̜̟̚'
            # Caracteres especiais permitidos (expandidos)
            ' .ː-'  # Adicionado hífen para palavras compostas
        )
        
        # Remover delimitadores para validação
        clean_phoneme = v.strip('/[]')
        
        # Verificar se contém apenas símbolos IPA válidos
        invalid_chars = set(clean_phoneme) - valid_ipa_chars
        if invalid_chars:
            raise ValueError(f"Símbolos IPA inválidos encontrados: {invalid_chars}")
        
        # Verificar padrões comuns de erro
        if '//' in clean_phoneme or '[[' in clean_phoneme:
            raise ValueError("Delimitadores duplicados não são permitidos")
        
        # Verificar se tem pelo menos um som válido
        if len(clean_phoneme.strip()) == 0:
            raise ValueError("Fonema não pode estar vazio")
        
        return v
    
    @field_validator('word')
    @classmethod
    def validate_word_format(cls, v: str) -> str:
        """Validar formato da palavra/expressão - FLEXÍVEL para método direto."""
        if not v:
            raise ValueError("Palavra é obrigatória")
        
        # MÉTODO DIRETO: Aceitar chunks, phrasal verbs, collocations
        # Permitir: letras, espaços, hífens, apóstrofes, pontos
        # Exemplos: "check in", "key card", "dining room", "mother-in-law", "don't"
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v.strip()):
            raise ValueError("Expressão deve conter apenas letras, espaços, hífens, apóstrofes ou pontos")
        
        # Limpar espaços extras mas manter estrutura
        cleaned = ' '.join(v.strip().split())
        return cleaned.lower()
    
    @field_validator('word_class')
    @classmethod
    def validate_word_class(cls, v: str) -> str:
        """Validar classe gramatical - EXPANDIDA para padrões nativos."""
        valid_classes = {
            # Classes básicas
            "noun", "verb", "adjective", "adverb", "preposition", 
            "conjunction", "article", "pronoun", "interjection",
            "modal", "auxiliary", "determiner", "numeral",
            # MÉTODO DIRETO: Padrões naturais do inglês
            "phrasal verb", "verb phrase", "noun phrase", "compound noun",
            "collocation", "idiom", "expression", "chunk", "phrase",
            "prepositional phrase", "adverbial phrase", "adjective phrase",
            "fixed expression", "compound adjective", "question_word"
        }
        
        if v.lower() not in valid_classes:
            raise ValueError(f"Classe gramatical deve ser uma de: {', '.join(sorted(valid_classes))}")
        
        return v.lower()
    
    @field_validator('frequency_level')
    @classmethod
    def validate_frequency_level(cls, v: str) -> str:
        """Validar nível de frequência."""
        valid_levels = {"high", "medium", "low", "very_high", "very_low"}
        
        if v.lower() not in valid_levels:
            raise ValueError(f"Nível de frequência deve ser um de: {', '.join(valid_levels)}")
        
        return v.lower()
    
    @field_validator('ipa_variant')
    @classmethod
    def validate_ipa_variant(cls, v: str) -> str:
        """Validar variante IPA."""
        valid_variants = {
            "general_american", "received_pronunciation", "australian_english",
            "canadian_english", "irish_english", "scottish_english"
        }
        
        if v.lower() not in valid_variants:
            raise ValueError(f"Variante IPA deve ser uma de: {', '.join(valid_variants)}")
        
        return v.lower()
    
    @field_validator('alternative_pronunciations')
    @classmethod
    def validate_alternative_pronunciations(cls, v: List[str]) -> List[str]:
        """Validar pronúncias alternativas."""
        # Aplicar a mesma validação IPA para cada item
        for pronunciation in v:
            if pronunciation and not ((pronunciation.startswith('/') and pronunciation.endswith('/')) or 
                                    (pronunciation.startswith('[') and pronunciation.endswith(']'))):
                raise ValueError("Pronúncia alternativa deve seguir formato IPA")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "word": "restaurant",
                "phoneme": "/ˈrɛstərɑnt/",
                "definition": "estabelecimento comercial onde se servem refeições",
                "example": "We had dinner at a lovely Italian restaurant last night.",
                "word_class": "noun",
                "frequency_level": "high",
                "context_relevance": 0.95,
                "is_reinforcement": False,
                "ipa_variant": "general_american",
                "stress_pattern": "primary_first",
                "syllable_count": 3,
                "alternative_pronunciations": ["/ˈrestərɑnt/"]
            }
        }
    }


class VocabularySection(BaseModel):
    """Seção completa de vocabulário - ATUALIZADA COM RAG E VALIDAÇÃO PYDANTIC V2."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    items: List[VocabularyItem] = Field(..., description="Lista de itens de vocabulário")
    total_count: int = Field(..., description="Total de palavras")
    context_relevance: float = Field(..., ge=0.0, le=1.0, description="Relevância contextual")
    
    # NOVOS CAMPOS PARA RAG
    new_words_count: int = Field(0, description="Palavras totalmente novas")
    reinforcement_words_count: int = Field(0, description="Palavras de reforço")
    rag_context_used: Dict[str, Any] = Field(default={}, description="Contexto RAG utilizado")
    progression_level: str = Field(default="intermediate", description="Nível de progressão")
    
    # NOVOS CAMPOS PARA IPA
    phoneme_coverage: Dict[str, int] = Field(default={}, description="Cobertura de fonemas IPA")
    pronunciation_variants: List[str] = Field(default=[], description="Variantes de pronúncia utilizadas")
    phonetic_complexity: str = Field(default="medium", description="Complexidade fonética geral")
    
    generated_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('total_count')
    @classmethod
    def validate_total_count(cls, v: int, info: ValidationInfo) -> int:
        """Validar contagem total."""
        if hasattr(info, 'data') and 'items' in info.data:
            items = info.data['items']
            if v != len(items):
                return len(items)
        return v
    
    @field_validator('items')
    @classmethod
    def validate_items_not_empty(cls, v: List[VocabularyItem]) -> List[VocabularyItem]:
        """Validar que há pelo menos alguns itens."""
        if len(v) == 0:
            raise ValueError("Seção de vocabulário deve ter pelo menos 1 item")
        
        if len(v) > 50:
            raise ValueError("Seção de vocabulário não deve ter mais de 50 itens")
        
        return v
    
    @field_validator('phonetic_complexity')
    @classmethod
    def validate_phonetic_complexity(cls, v: str) -> str:
        """Validar complexidade fonética."""
        valid_complexities = {"simple", "medium", "complex", "very_complex"}
        
        if v.lower() not in valid_complexities:
            raise ValueError(f"Complexidade fonética deve ser uma de: {', '.join(valid_complexities)}")
        
        return v.lower()


# =============================================================================
# CONTENT MODELS (Tips & Grammar) - ATUALIZADOS PYDANTIC V2
# =============================================================================

class TipsContent(BaseModel):
    """Conteúdo de TIPS para unidades lexicais."""
    strategy: TipStrategy = Field(..., description="Estratégia TIPS aplicada")
    title: str = Field(..., description="Título da estratégia")
    explanation: str = Field(..., description="Explicação da estratégia")
    examples: List[str] = Field(..., description="Exemplos práticos")
    practice_suggestions: List[str] = Field(..., description="Sugestões de prática")
    memory_techniques: List[str] = Field(..., description="Técnicas de memorização")
    
    # NOVOS CAMPOS PARA RAG
    vocabulary_coverage: List[str] = Field(default=[], description="Vocabulário coberto pela estratégia")
    complementary_strategies: List[str] = Field(default=[], description="Estratégias complementares sugeridas")
    selection_rationale: str = Field(default="", description="Por que esta estratégia foi selecionada")
    
    # NOVOS CAMPOS PARA FONEMAS
    phonetic_focus: List[str] = Field(default=[], description="Fonemas ou padrões fonéticos focalizados")
    pronunciation_tips: List[str] = Field(default=[], description="Dicas específicas de pronúncia")


class GrammarContent(BaseModel):
    """Conteúdo de GRAMMAR para unidades gramaticais."""
    strategy: GrammarStrategy = Field(..., description="Estratégia GRAMMAR aplicada")
    grammar_point: str = Field(..., description="Ponto gramatical principal")
    systematic_explanation: str = Field(..., description="Explicação sistemática")
    usage_rules: List[str] = Field(..., description="Regras de uso")
    examples: List[str] = Field(..., description="Exemplos contextualizados")
    l1_interference_notes: List[str] = Field(..., description="Notas sobre interferência L1")
    common_mistakes: List[Dict[str, str]] = Field(..., description="Erros comuns e correções")
    
    # NOVOS CAMPOS PARA RAG
    vocabulary_integration: List[str] = Field(default=[], description="Como integra com o vocabulário")
    previous_grammar_connections: List[str] = Field(default=[], description="Conexões com gramática anterior")
    selection_rationale: str = Field(default="", description="Por que esta estratégia foi selecionada")


# =============================================================================
# ASSESSMENT MODELS - ATUALIZADOS COM BALANCEAMENTO PYDANTIC V2
# =============================================================================

class AssessmentActivity(BaseModel):
    """Atividade de avaliação."""
    type: AssessmentType = Field(..., description="Tipo de atividade")
    title: str = Field(..., description="Título da atividade")
    instructions: str = Field(..., description="Instruções da atividade")
    content: Dict[str, Any] = Field(..., description="Conteúdo específico da atividade")
    answer_key: Dict[str, Any] = Field(..., description="Gabarito da atividade")
    estimated_time: int = Field(..., description="Tempo estimado em minutos")
    
    # NOVOS CAMPOS PARA BALANCEAMENTO
    difficulty_level: str = Field(default="intermediate", description="Nível de dificuldade")
    skills_assessed: List[str] = Field(default=[], description="Habilidades avaliadas")
    vocabulary_focus: List[str] = Field(default=[], description="Vocabulário focado")
    
    # NOVOS CAMPOS PARA FONEMAS
    pronunciation_focus: bool = Field(False, description="Atividade foca em pronúncia")
    phonetic_elements: List[str] = Field(default=[], description="Elementos fonéticos avaliados")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "gap_fill",
                "title": "Complete the sentences",
                "instructions": "Fill in the blanks with the appropriate words from the vocabulary.",
                "content": {
                    "sentences": [
                        "I need to make a _______ for dinner.",
                        "The hotel has excellent _______."
                    ],
                    "word_bank": ["reservation", "service"]
                },
                "answer_key": {
                    "1": "reservation",
                    "2": "service"
                },
                "estimated_time": 10,
                "difficulty_level": "intermediate",
                "skills_assessed": ["vocabulary_recognition", "context_application"],
                "vocabulary_focus": ["reservation", "service"],
                "pronunciation_focus": False,
                "phonetic_elements": []
            }
        }
    }


class AssessmentSection(BaseModel):
    """Seção completa de avaliação - ATUALIZADA COM BALANCEAMENTO."""
    activities: List[AssessmentActivity] = Field(..., description="Lista de atividades (2 selecionadas)")
    selection_rationale: str = Field(..., description="Justificativa da seleção")
    total_estimated_time: int = Field(..., description="Tempo total estimado")
    skills_assessed: List[str] = Field(..., description="Habilidades avaliadas")
    
    # NOVOS CAMPOS PARA BALANCEAMENTO
    balance_analysis: Dict[str, Any] = Field(default={}, description="Análise de balanceamento")
    underused_activities: List[str] = Field(default=[], description="Atividades subutilizadas")
    complementary_pair: bool = Field(True, description="São atividades complementares?")


# =============================================================================
# COMMON MISTAKE MODEL - CLASSE FALTANTE QUE ESTAVA CAUSANDO OS ERROS
# =============================================================================

class CommonMistake(BaseModel):
    """Modelo para erros comuns identificados e suas correções - Pydantic V2 Otimizada."""
    mistake_type: str = Field(..., description="Tipo de erro comum")
    incorrect_form: str = Field(..., description="Forma incorreta")
    correct_form: str = Field(..., description="Forma correta")
    explanation: str = Field(..., description="Explicação do erro")
    examples: List[str] = Field(default=[], description="Exemplos do erro")
    frequency: str = Field(default="medium", description="Frequência do erro")
    cefr_level: str = Field(default="A2", description="Nível CEFR onde o erro ocorre")
    
    # Campos específicos para brasileiros
    l1_interference: bool = Field(False, description="É interferência do português?")
    prevention_strategy: str = Field(default="explicit_instruction", description="Estratégia de prevenção")
    related_grammar_point: Optional[str] = Field(None, description="Ponto gramatical relacionado")
    
    # ✅ MELHORIA 1: Campos adicionais úteis
    context_where_occurs: Optional[str] = Field(None, description="Contexto onde o erro é comum")
    age_group_frequency: Optional[str] = Field(None, description="Faixa etária onde é mais comum")
    remedial_exercises: List[str] = Field(default=[], description="Exercícios específicos para correção")
    
    # ✅ MELHORIA 2: Metadados de tracking
    first_observed: Optional[datetime] = Field(None, description="Quando foi observado primeiro")
    severity_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de severidade (0-1)")
    
    @field_validator('mistake_type')
    @classmethod
    def validate_mistake_type(cls, v: str) -> str:
        """Validar tipo de erro."""
        valid_types = {
            "grammatical", "lexical", "phonetic", "semantic", 
            "syntactic", "spelling", "pronunciation", "usage",
            # ✅ MELHORIA 3: Tipos adicionais específicos para brasileiros
            "article_omission", "preposition_confusion", "false_friend",
            "word_order", "verb_tense", "modal_usage"
        }
        
        if v.lower() not in valid_types:
            raise ValueError(f"Tipo de erro deve ser um de: {', '.join(sorted(valid_types))}")
        
        return v.lower()
    
    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        """Validar frequência do erro."""
        valid_frequencies = {"very_low", "low", "medium", "high", "very_high"}
        
        if v.lower() not in valid_frequencies:
            raise ValueError(f"Frequência deve ser uma de: {', '.join(sorted(valid_frequencies))}")
        
        return v.lower()
    
    @field_validator('prevention_strategy')
    @classmethod
    def validate_prevention_strategy(cls, v: str) -> str:
        """Validar estratégia de prevenção."""
        valid_strategies = {
            "explicit_instruction", "contrastive_exercises", "drilling", 
            "error_correction", "awareness_raising", "input_enhancement",
            "consciousness_raising", "form_focused_instruction",
            # ✅ MELHORIA 4: Estratégias adicionais específicas
            "pattern_recognition", "metalinguistic_awareness", 
            "controlled_practice", "communicative_practice"
        }
        
        if v.lower() not in valid_strategies:
            raise ValueError(f"Estratégia deve ser uma de: {', '.join(sorted(valid_strategies))}")
        
        return v.lower()
    
    # ✅ MELHORIA 5: Validador para CEFR
    @field_validator('cefr_level')
    @classmethod
    def validate_cefr_level(cls, v: str) -> str:
        """Validar nível CEFR."""
        valid_levels = {"A1", "A2", "B1", "B2", "C1", "C2"}
        
        if v.upper() not in valid_levels:
            raise ValueError(f"Nível CEFR deve ser um de: {', '.join(sorted(valid_levels))}")
        
        return v.upper()
    
    # ✅ MELHORIA 6: Validador para age_group_frequency
    @field_validator('age_group_frequency')
    @classmethod
    def validate_age_group(cls, v: Optional[str]) -> Optional[str]:
        """Validar faixa etária."""
        if v is None:
            return v
            
        valid_groups = {"children", "teenagers", "young_adults", "adults", "seniors", "all_ages"}
        
        if v.lower() not in valid_groups:
            raise ValueError(f"Faixa etária deve ser uma de: {', '.join(sorted(valid_groups))}")
        
        return v.lower()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "mistake_type": "grammatical",
                "incorrect_form": "I have 25 years",
                "correct_form": "I am 25 years old",
                "explanation": "Portuguese speakers often use 'have' for age due to L1 interference",
                "examples": [
                    "She has 30 years → She is 30 years old",
                    "How many years do you have? → How old are you?"
                ],
                "frequency": "very_high",
                "cefr_level": "A1",
                "l1_interference": True,
                "prevention_strategy": "contrastive_exercises",
                "related_grammar_point": "be_vs_have",
                "context_where_occurs": "Personal introductions, age discussions",
                "age_group_frequency": "all_ages",
                "remedial_exercises": [
                    "Age expression drills",
                    "Contrastive PT vs EN exercises",
                    "Controlled practice with BE + age"
                ],
                "severity_score": 0.9
            }
        }
    }


class CommonMistakeSection(BaseModel):
    """Seção de erros comuns para uma unidade - Pydantic V2."""
    mistakes: List[CommonMistake] = Field(..., description="Lista de erros comuns")
    total_mistakes: int = Field(..., description="Total de erros identificados")
    l1_interference_count: int = Field(default=0, description="Quantos são interferência L1")
    prevention_strategies: List[str] = Field(default=[], description="Estratégias de prevenção")
    difficulty_level: str = Field(default="intermediate", description="Nível de dificuldade geral")
    
    generated_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('total_mistakes')
    @classmethod
    def validate_total_mistakes(cls, v: int, info: ValidationInfo) -> int:
        """Validar contagem total."""
        if hasattr(info, 'data') and 'mistakes' in info.data:
            mistakes = info.data['mistakes']
            if v != len(mistakes):
                return len(mistakes)
        return v
    
    @field_validator('l1_interference_count')
    @classmethod
    def validate_l1_count(cls, v: int, info: ValidationInfo) -> int:
        """Validar contagem de interferência L1."""
        if hasattr(info, 'data') and 'mistakes' in info.data:
            mistakes = info.data['mistakes']
            actual_l1_count = sum(1 for mistake in mistakes if mistake.l1_interference)
            if v != actual_l1_count:
                return actual_l1_count
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "mistakes": [
                    {
                        "mistake_type": "grammatical",
                        "incorrect_form": "I have 25 years",
                        "correct_form": "I am 25 years old",
                        "explanation": "Age expression error",
                        "l1_interference": True,
                        "prevention_strategy": "contrastive_exercises"
                    }
                ],
                "total_mistakes": 1,
                "l1_interference_count": 1,
                "prevention_strategies": ["contrastive_exercises", "explicit_instruction"],
                "difficulty_level": "beginner"
            }
        }
    }


# =============================================================================
# UNIT COMPLETE MODEL - ATUALIZADO COM HIERARQUIA PYDANTIC V2
# =============================================================================

class UnitResponse(BaseModel):
    """Response completa da unidade - ATUALIZADA COM HIERARQUIA."""
    # HIERARQUIA (novos campos obrigatórios)
    id: str = Field(..., description="ID único da unidade")
    course_id: str = Field(..., description="ID do curso")
    book_id: str = Field(..., description="ID do book")
    sequence_order: int = Field(..., description="Ordem sequencial no book")
    
    # Informações básicas
    title: str = Field(..., description="Título da unidade")
    main_aim: str = Field(..., description="Objetivo principal")
    subsidiary_aims: List[str] = Field(..., description="Objetivos subsidiários")
    
    # Metadata
    unit_type: UnitType = Field(..., description="Tipo de unidade")
    cefr_level: CEFRLevel = Field(..., description="Nível CEFR")
    language_variant: LanguageVariant = Field(..., description="Variante do idioma")
    status: UnitStatus = Field(..., description="Status atual")
    
    # Content Sections
    images: List["ImageInfo"] = Field(default=[], description="Informações das imagens")
    vocabulary: Optional[VocabularySection] = Field(None, description="Seção de vocabulário")
    sentences: Optional["SentencesSection"] = Field(None, description="Seção de sentences")
    tips: Optional[TipsContent] = Field(None, description="Conteúdo TIPS (se lexical)")
    grammar: Optional[GrammarContent] = Field(None, description="Conteúdo GRAMMAR (se grammar)")
    qa: Optional["QASection"] = Field(None, description="Seção Q&A")
    assessments: Optional[AssessmentSection] = Field(None, description="Seção de avaliação")
    
    # PROGRESSÃO PEDAGÓGICA (novos campos)
    strategies_used: List[str] = Field(default=[], description="Estratégias já usadas")
    assessments_used: List[str] = Field(default=[], description="Tipos de atividades já usadas")
    vocabulary_taught: List[str] = Field(default=[], description="Vocabulário ensinado nesta unidade")
    
    # NOVOS CAMPOS PARA FONEMAS
    phonemes_introduced: List[str] = Field(default=[], description="Fonemas introduzidos nesta unidade")
    pronunciation_focus: Optional[str] = Field(None, description="Foco de pronúncia da unidade")
    
    # CONTEXTO HIERÁRQUICO (informações derivadas)
    hierarchy_info: Optional[Dict[str, Any]] = Field(None, description="Informações da hierarquia")
    progression_analysis: Optional[Dict[str, Any]] = Field(None, description="Análise de progressão")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Quality Control
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de qualidade")
    checklist_completed: List[str] = Field(default=[], description="Checklist de qualidade completado")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "unit_hotel_reservations_001",
                "course_id": "course_english_beginners",
                "book_id": "book_foundation_a1",
                "sequence_order": 5,
                "title": "Hotel Reservations",
                "main_aim": "Students will be able to make hotel reservations using appropriate vocabulary and phrases",
                "subsidiary_aims": [
                    "Use reservation-related vocabulary accurately",
                    "Apply polite language in formal situations",
                    "Understand hotel policies and procedures"
                ],
                "unit_type": "lexical_unit",
                "cefr_level": "A2",
                "language_variant": "american_english",
                "status": "completed",
                "strategies_used": ["collocations", "chunks"],
                "assessments_used": ["gap_fill", "matching"],
                "vocabulary_taught": ["reservation", "check-in", "availability", "suite"],
                "phonemes_introduced": ["/ˌrezərˈveɪʃən/", "/ˈʧɛk ɪn/"],
                "pronunciation_focus": "stress_patterns",
                "quality_score": 0.92
            }
        }
    }


# =============================================================================
# ADDITIONAL MODELS FOR SENTENCES AND QA - PYDANTIC V2
# =============================================================================

class Sentence(BaseModel):
    """Sentence conectada ao vocabulário."""
    text: str = Field(..., description="Texto da sentence")
    vocabulary_used: List[str] = Field(..., description="Palavras do vocabulário utilizadas")
    context_situation: str = Field(..., description="Situação contextual")
    complexity_level: str = Field(..., description="Nível de complexidade")
    
    # NOVOS CAMPOS PARA PROGRESSÃO
    reinforces_previous: List[str] = Field(default=[], description="Vocabulário anterior reforçado")
    introduces_new: List[str] = Field(default=[], description="Novo vocabulário introduzido")
    
    # NOVOS CAMPOS PARA FONEMAS
    phonetic_features: List[str] = Field(default=[], description="Características fonéticas destacadas")
    pronunciation_notes: Optional[str] = Field(None, description="Notas de pronúncia")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "I need to make a reservation for two people tonight.",
                "vocabulary_used": ["reservation"],
                "context_situation": "restaurant_booking",
                "complexity_level": "intermediate",
                "reinforces_previous": [],
                "introduces_new": ["reservation"],
                "phonetic_features": ["word_stress", "schwa_reduction"],
                "pronunciation_notes": "Note the stress on 'reser-VA-tion'"
            }
        }
    }


class SentencesSection(BaseModel):
    """Seção de sentences."""
    sentences: List[Sentence] = Field(..., description="Lista de sentences")
    vocabulary_coverage: float = Field(..., ge=0.0, le=1.0, description="Cobertura do vocabulário")
    
    # NOVOS CAMPOS PARA RAG
    contextual_coherence: float = Field(default=0.8, description="Coerência contextual")
    progression_appropriateness: float = Field(default=0.8, description="Adequação à progressão")
    
    # NOVOS CAMPOS PARA FONEMAS
    phonetic_progression: List[str] = Field(default=[], description="Progressão fonética nas sentences")
    pronunciation_patterns: List[str] = Field(default=[], description="Padrões de pronúncia abordados")
    
    generated_at: datetime = Field(default_factory=datetime.now)


class QASection(BaseModel):
    """Seção de perguntas e respostas."""
    questions: List[str] = Field(..., description="Perguntas para estudantes")
    answers: List[str] = Field(..., description="Respostas completas (para professores)")
    pedagogical_notes: List[str] = Field(..., description="Notas pedagógicas")
    difficulty_progression: str = Field(..., description="Progressão de dificuldade")
    
    # NOVOS CAMPOS PARA CONTEXTO
    vocabulary_integration: List[str] = Field(default=[], description="Vocabulário integrado")
    cognitive_levels: List[str] = Field(default=[], description="Níveis cognitivos das perguntas")
    
    # NOVOS CAMPOS PARA FONEMAS
    pronunciation_questions: List[str] = Field(default=[], description="Perguntas sobre pronúncia")
    phonetic_awareness: List[str] = Field(default=[], description="Consciência fonética desenvolvida")


class ImageInfo(BaseModel):
    """Informações da imagem processada."""
    filename: str = Field(..., description="Nome do arquivo")
    description: str = Field(..., description="Descrição da imagem pela IA")
    objects_detected: List[str] = Field(..., description="Objetos detectados")
    text_detected: Optional[str] = Field(None, description="Texto detectado na imagem")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Score de relevância")
    
    # NOVOS CAMPOS PARA PROGRESSÃO
    vocabulary_suggestions: List[str] = Field(default=[], description="Vocabulário sugerido pela imagem")
    context_themes: List[str] = Field(default=[], description="Temas contextuais identificados")


# =============================================================================
# PROGRESS & STATUS MODELS - ATUALIZADOS PYDANTIC V2
# =============================================================================

class GenerationProgress(BaseModel):
    """Progresso da geração de conteúdo."""
    unit_id: str = Field(..., description="ID da unidade")
    course_id: str = Field(..., description="ID do curso")
    book_id: str = Field(..., description="ID do book")
    sequence_order: int = Field(..., description="Sequência no book")
    
    current_step: str = Field(..., description="Etapa atual")
    progress_percentage: int = Field(..., ge=0, le=100, description="Porcentagem de progresso")
    message: str = Field(..., description="Mensagem de status")
    estimated_remaining_time: Optional[int] = Field(None, description="Tempo estimado restante (segundos)")
    
    # NOVOS CAMPOS PARA CONTEXTO RAG
    rag_context_loaded: bool = Field(False, description="Contexto RAG carregado?")
    precedent_units_found: int = Field(0, description="Unidades precedentes encontradas")
    vocabulary_overlap_analysis: Optional[Dict[str, Any]] = Field(None, description="Análise de sobreposição")
    
    # NOVOS CAMPOS PARA FONEMAS
    phoneme_analysis_completed: bool = Field(False, description="Análise fonética completada?")
    pronunciation_validation: Optional[Dict[str, Any]] = Field(None, description="Validação de pronúncia")
    
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais")


class ErrorResponse(BaseModel):
    """Response de erro padronizado."""
    success: bool = Field(False, description="Sempre False para erros")
    error_code: str = Field(..., description="Código do erro")
    message: str = Field(..., description="Mensagem de erro")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes do erro")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # NOVOS CAMPOS PARA DEPURAÇÃO
    hierarchy_context: Optional[Dict[str, Any]] = Field(None, description="Contexto hierárquico do erro")
    suggested_fixes: List[str] = Field(default=[], description="Sugestões de correção")


class SuccessResponse(BaseModel):
    """Response de sucesso padronizado."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    success: bool = Field(True, description="Sempre True para sucesso")
    data: Dict[str, Any] = Field(..., description="Dados da resposta")
    message: Optional[str] = Field(None, description="Mensagem opcional")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # NOVOS CAMPOS PARA CONTEXTO
    hierarchy_info: Optional[Dict[str, Any]] = Field(None, description="Informações hierárquicas")
    next_suggested_actions: List[str] = Field(default=[], description="Próximas ações sugeridas")
    
    def __init__(self, **data):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("🔍 [DEBUG] Criando SuccessResponse...")
        super().__init__(**data)
        logger.info("🔍 [DEBUG] SuccessResponse criado com sucesso")


# =============================================================================
# BATCH AND BULK OPERATION MODELS
# =============================================================================

class BulkUnitStatus(BaseModel):
    """Status de operação em lote."""
    total_units: int = Field(..., description="Total de unidades processadas")
    successful: int = Field(..., description="Unidades processadas com sucesso")
    failed: int = Field(..., description="Unidades que falharam")
    errors: List[Dict[str, str]] = Field(default=[], description="Detalhes dos erros")
    processing_time: float = Field(..., description="Tempo total de processamento")


class CourseStatistics(BaseModel):
    """Estatísticas do curso."""
    course_id: str
    course_name: str
    total_books: int
    total_units: int
    completed_units: int
    average_quality_score: float
    
    # DISTRIBUIÇÕES
    units_by_level: Dict[str, int] = Field(default={}, description="Unidades por nível CEFR")
    units_by_type: Dict[str, int] = Field(default={}, description="Unidades por tipo")
    strategy_distribution: Dict[str, int] = Field(default={}, description="Distribuição de estratégias")
    assessment_distribution: Dict[str, int] = Field(default={}, description="Distribuição de atividades")
    
    # PROGRESSÃO
    vocabulary_progression: Dict[str, Any] = Field(default={}, description="Progressão de vocabulário")
    quality_progression: List[float] = Field(default=[], description="Progressão da qualidade")
    
    # NOVOS CAMPOS PARA FONEMAS
    phoneme_distribution: Dict[str, int] = Field(default={}, description="Distribuição de fonemas IPA")
    pronunciation_variants: List[str] = Field(default=[], description="Variantes de pronúncia usadas")
    phonetic_complexity_trend: List[str] = Field(default=[], description="Tendência de complexidade fonética")
    
    last_updated: datetime = Field(default_factory=datetime.now)


# =============================================================================
# VOCABULARY GENERATION MODELS - NOVOS PARA PROMPT 6 PYDANTIC V2
# =============================================================================

# =============================================================================
# SOLVE ASSESSMENTS MODELS - CORREÇÃO IA DE ATIVIDADES
# =============================================================================

class ItemCorrection(BaseModel):
    """Correção individual de item de assessment."""
    item_id: str = Field(..., description="ID do item/questão")
    student_answer: str = Field(..., description="Resposta do aluno")
    correct_answer: str = Field(..., description="Resposta esperada")
    result: str = Field(..., description="Resultado: correct, incorrect, partially_correct")
    score_earned: int = Field(..., ge=0, description="Pontos obtidos")
    score_total: int = Field(..., ge=1, description="Pontos possíveis")
    feedback: str = Field(..., description="Feedback específico para este item")
    l1_interference: Optional[str] = Field(None, description="Padrão de interferência PT→EN identificado")

class ErrorAnalysis(BaseModel):
    """Análise detalhada de erros."""
    most_common_errors: List[str] = Field(default=[], description="Tipos de erro mais frequentes")
    l1_interference_patterns: List[str] = Field(default=[], description="Padrões específicos PT→EN")
    recurring_mistakes: List[str] = Field(default=[], description="Erros que se repetem")
    error_frequency: Dict[str, int] = Field(default={}, description="Frequência de cada tipo de erro")

class ConstructiveFeedback(BaseModel):
    """Feedback construtivo para o aluno."""
    strengths_demonstrated: List[str] = Field(default=[], description="Aspectos positivos identificados")
    areas_for_improvement: List[str] = Field(default=[], description="Áreas específicas para melhoria")
    study_recommendations: List[str] = Field(default=[], description="Sugestões de estudo direcionadas")
    next_steps: List[str] = Field(default=[], description="Próximos passos no aprendizado")

class PedagogicalNotes(BaseModel):
    """Notas pedagógicas para professores."""
    class_performance_patterns: List[str] = Field(default=[], description="Padrões observados na turma")
    remedial_activities: List[str] = Field(default=[], description="Atividades remediais sugeridas")
    differentiation_needed: List[str] = Field(default=[], description="Adaptações necessárias")
    followup_assessments: List[str] = Field(default=[], description="Avaliações de acompanhamento")

class SolveAssessmentResult(BaseModel):
    """Resultado completo da correção de assessment pela IA."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    # === AVALIAÇÃO GERAL ===
    total_score: int = Field(..., description="Pontuação total obtida")
    total_possible: int = Field(..., description="Pontuação total possível")
    performance_level: str = Field(..., description="Nível de desempenho: excellent, good, satisfactory, needs_improvement")
    cefr_demonstration: str = Field(..., description="Nível CEFR demonstrado: above, at, below")
    
    # === CORREÇÃO ITEM POR ITEM ===
    item_corrections: List[ItemCorrection] = Field(..., description="Correções individuais")
    
    # === ANÁLISES ===
    error_analysis: ErrorAnalysis = Field(..., description="Análise detalhada de erros")
    constructive_feedback: ConstructiveFeedback = Field(..., description="Feedback construtivo")
    pedagogical_notes: PedagogicalNotes = Field(..., description="Notas para professores")
    
    # === METADADOS ===
    assessment_type: str = Field(..., description="Tipo de assessment corrigido")
    assessment_title: str = Field(..., description="Título da atividade")
    unit_context: Dict[str, Any] = Field(default={}, description="Contexto da unidade")
    correction_timestamp: datetime = Field(default_factory=datetime.now)
    
    # === ESTATÍSTICAS ===
    accuracy_percentage: float = Field(..., ge=0.0, le=100.0, description="Porcentagem de acerto")
    completion_time: Optional[float] = Field(None, description="Tempo de correção em segundos")
    ai_model_used: str = Field(default="gpt-5", description="Modelo IA usado na correção")

class SimpleSolveRequest(BaseModel):
    """Request SIMPLIFICADO para correção de assessment - só o essencial."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    # === APENAS O ESSENCIAL ===
    assessment_type: str = Field(..., description="Tipo de assessment para corrigir")
    include_student_answers: bool = Field(default=False, description="Se True, usa respostas salvas no banco")
    student_context: Optional[str] = Field(None, description="Contexto adicional do estudante")


# =============================================================================
# ASSESSMENT SOLUTION MODELS - GERADOR DE GABARITOS
# =============================================================================

class AssessmentItem(BaseModel):
    """Item individual de um assessment com solução."""
    item_id: str = Field(..., description="ID único do item")
    question_text: str = Field(..., description="Enunciado completo da questão")
    correct_answer: str = Field(..., description="Resposta correta/gabarito")
    explanation: str = Field(..., description="Explicação detalhada da solução")
    difficulty_level: str = Field(..., description="Nível de dificuldade: easy, medium, hard")
    skills_tested: List[str] = Field(default=[], description="Habilidades testadas")
    
class AssessmentSolution(BaseModel):
    """Solução completa de um assessment - NOVO MODELO PARA GABARITOS."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    # === IDENTIFICAÇÃO ===
    assessment_type: str = Field(..., description="Tipo de assessment")
    assessment_title: str = Field(..., description="Título da atividade")
    total_items: int = Field(..., description="Total de questões")
    
    # === INSTRUÇÕES E CONTEXTO ===
    instructions: str = Field(..., description="Instruções completas do assessment")
    unit_context: str = Field(..., description="Contexto da unidade para referência")
    
    # === SOLUÇÕES ITEM POR ITEM ===
    items: List[AssessmentItem] = Field(..., description="Soluções detalhadas de cada item")
    
    # === RESUMO PEDAGÓGICO ===
    skills_overview: List[str] = Field(default=[], description="Visão geral das habilidades testadas")
    difficulty_distribution: Dict[str, int] = Field(default={}, description="Distribuição por dificuldade")
    teaching_notes: List[str] = Field(default=[], description="Notas para professores")
    
    # === METADADOS ===
    solution_timestamp: datetime = Field(default_factory=datetime.now)
    ai_model_used: str = Field(default="gpt-5", description="Modelo usado para gerar gabarito")
    processing_time: Optional[float] = Field(None, description="Tempo de processamento")

class SimpleGabaritoRequest(BaseModel):
    """Request para geração de gabarito."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    assessment_type: str = Field(..., description="Tipo de assessment para resolver")
    include_explanations: bool = Field(default=True, description="Incluir explicações detalhadas")
    difficulty_analysis: bool = Field(default=True, description="Incluir análise de dificuldade")

# =============================================================================
# CONTENT GENERATION REQUEST MODELS - PRODUÇÃO-READY COM VALIDAÇÃO ESPECÍFICA
# =============================================================================

class VocabularyGenerationRequest(BaseModel):
    """Request específico para geração de vocabulário."""
    # Webhook para processamento assíncrono (OPCIONAL)
    webhook_url: Optional[str] = Field(None, description="URL para webhook - se fornecida, processará assíncronamente")
    
    # Configurações básicas - OBRIGATÓRIAS
    target_count: int = Field(..., ge=5, le=50, description="Número EXATO de palavras a gerar (obrigatório)")
    difficulty_level: Optional[str] = Field("intermediate", description="Nível: beginner, intermediate, advanced")
    focus_areas: Optional[List[str]] = Field(None, description="Áreas de foco: verbs, nouns, adjectives, etc")
    
    # Compatibilidade (deprecated)
    word_count: Optional[int] = Field(None, description="DEPRECATED: Use target_count")
    
    # Configurações IPA
    ipa_variant: Optional[str] = Field("general_american", description="Variante IPA")
    include_alternative_pronunciations: Optional[bool] = Field(False, description="Incluir pronúncias alternativas")
    phonetic_complexity: Optional[str] = Field("medium", description="Complexidade fonética: simple, medium, complex")
    
    # Contexto RAG
    avoid_repetition: Optional[bool] = Field(True, description="Evitar repetições")
    is_revision_unit: bool = Field(False, description="Unidade de revisão (permite busca RAG ampla em outros books)")
    avoid_vocabulary: Optional[List[str]] = Field(None, description="Palavras a evitar")
    reinforce_vocabulary: Optional[List[str]] = Field(None, description="Palavras para reforçar")
    use_rag_context: Optional[bool] = Field(True, description="Usar contexto RAG")


class SentenceGenerationRequest(BaseModel):
    """Request específico para geração de sentences."""
    # Webhook para processamento assíncrono (OPCIONAL)
    webhook_url: Optional[str] = Field(None, description="URL para webhook - se fornecida, processará assíncronamente")
    
    # Configurações básicas - OBRIGATÓRIAS
    target_count: int = Field(..., ge=3, le=20, description="Número EXATO de sentenças a gerar (obrigatório)")
    complexity_level: Optional[str] = Field("simple", description="Complexidade: simple, intermediate, complex")
    
    # Compatibilidade (deprecated)
    sentence_count: Optional[int] = Field(None, description="DEPRECATED: Use target_count")
    
    # Conexão com vocabulário
    connect_to_vocabulary: Optional[bool] = Field(True, description="Conectar ao vocabulário da unit")
    vocabulary_coverage: Optional[float] = Field(0.7, ge=0.1, le=1.0, description="% do vocabulário a usar")
    
    # Contexto e variedade
    sentence_types: Optional[List[str]] = Field(None, description="Tipos: declarative, interrogative, imperative")
    avoid_repetition: Optional[bool] = Field(True, description="Evitar repetições")
    use_rag_context: Optional[bool] = Field(True, description="Usar contexto RAG")
    is_revision_unit: bool = Field(False, description="Unidade de revisão (permite busca RAG ampla em outros books)")


class TipsGenerationRequest(BaseModel):
    """Request específico para geração de TIPS strategies."""
    # Webhook para processamento assíncrono (OPCIONAL)
    webhook_url: Optional[str] = Field(None, description="URL para webhook - se fornecida, processará assíncronamente")
    
    # Configurações básicas
    strategy_count: Optional[int] = Field(3, ge=1, le=6, description="Número de estratégias")
    focus_type: Optional[str] = Field("vocabulary", description="Foco: vocabulary, pronunciation, usage")
    
    # Estratégias específicas
    preferred_strategies: Optional[List[str]] = Field(None, description="Estratégias preferidas")
    avoid_strategies: Optional[List[str]] = Field(None, description="Estratégias a evitar")
    
    # Contexto
    difficulty_adaptation: Optional[bool] = Field(True, description="Adaptar à dificuldade da unit")
    use_rag_context: Optional[bool] = Field(True, description="Usar contexto RAG")
    include_l1_warnings: Optional[bool] = Field(True, description="Incluir avisos sobre interferência L1")


class AssessmentGenerationRequest(BaseModel):
    """Request específico para geração de assessments."""
    # Webhook para processamento assíncrono (OPCIONAL)
    webhook_url: Optional[str] = Field(None, description="URL para webhook - se fornecida, processará assíncronamente")
    
    # Configurações básicas
    assessment_count: Optional[int] = Field(2, ge=1, le=5, description="Número de atividades")
    difficulty_distribution: Optional[str] = Field("balanced", description="Distribuição: easy, balanced, challenging")
    
    # Tipos de assessment
    preferred_types: Optional[List[str]] = Field(None, description="Tipos preferidos de atividade")
    avoid_types: Optional[List[str]] = Field(None, description="Tipos a evitar")
    
    # Balanceamento
    ensure_variety: Optional[bool] = Field(True, description="Garantir variedade de tipos")
    connect_to_content: Optional[bool] = Field(True, description="Conectar ao conteúdo da unit")
    use_rag_context: Optional[bool] = Field(True, description="Usar contexto RAG")


class QAGenerationRequest(BaseModel):
    """Request específico para geração de Q&A."""
    # Webhook para processamento assíncrono (OPCIONAL)
    webhook_url: Optional[str] = Field(None, description="URL para webhook - se fornecida, processará assíncronamente")
    
    # Configurações básicas - OBRIGATÓRIAS
    target_count: int = Field(..., ge=2, le=15, description="Número EXATO de perguntas a gerar (obrigatório)")
    bloom_levels: Optional[List[str]] = Field(["remember", "understand"], description="Níveis da Taxonomia de Bloom")
    
    # Compatibilidade (deprecated)
    question_count: Optional[int] = Field(None, description="DEPRECATED: Use target_count")
    
    # Tipos de pergunta
    question_types: Optional[List[str]] = Field(None, description="Tipos: multiple_choice, open_ended, true_false")
    difficulty_progression: Optional[bool] = Field(True, description="Progressão de dificuldade")
    
    # Contexto
    connect_to_content: Optional[bool] = Field(True, description="Conectar ao conteúdo da unit")
    use_rag_context: Optional[bool] = Field(True, description="Usar contexto RAG")


class GrammarGenerationRequest(BaseModel):
    """Request específico para geração de grammar strategies."""
    # Webhook para processamento assíncrono (OPCIONAL)
    webhook_url: Optional[str] = Field(None, description="URL para webhook - se fornecida, processará assíncronamente")
    
    # Configurações básicas
    strategy_count: Optional[int] = Field(3, ge=1, le=6, description="Número de estratégias gramaticais")
    grammar_focus: Optional[str] = Field("unit_based", description="Foco: unit_based, specific_point, mixed")
    
    # Estratégias específicas
    preferred_strategies: Optional[List[str]] = Field(None, description="Estratégias preferidas")
    complexity_level: Optional[str] = Field("intermediate", description="Complexidade: beginner, intermediate, advanced")
    
    # Contexto
    connect_to_vocabulary: Optional[bool] = Field(True, description="Conectar ao vocabulário")
    use_rag_context: Optional[bool] = Field(True, description="Usar contexto RAG")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "images_context": [
                    {
                        "description": "Hotel reception with people checking in",
                        "objects": ["desk", "receptionist", "guests", "luggage"],
                        "themes": ["hospitality", "travel", "accommodation"]
                    }
                ],
                "target_count": 25,
                "cefr_level": "A2",
                "language_variant": "american_english",
                "unit_type": "lexical_unit",
                "ipa_variant": "general_american",
                "include_alternative_pronunciations": False,
                "phonetic_complexity": "medium",
                "avoid_vocabulary": ["hello", "goodbye"],
                "reinforce_vocabulary": ["hotel", "room"]
            }
        }
    }


class VocabularyGenerationResponse(BaseModel):
    """Response da geração de vocabulário."""
    vocabulary_section: VocabularySection = Field(..., description="Seção de vocabulário gerada")
    generation_metadata: Dict[str, Any] = Field(..., description="Metadados da geração")
    rag_analysis: Dict[str, Any] = Field(..., description="Análise RAG aplicada")
    quality_metrics: Dict[str, float] = Field(..., description="Métricas de qualidade")
    
    # MÉTRICAS DE IPA
    phoneme_analysis: Dict[str, Any] = Field(..., description="Análise dos fonemas incluídos")
    pronunciation_coverage: Dict[str, float] = Field(..., description="Cobertura de padrões de pronúncia")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "generation_metadata": {
                    "generation_time_ms": 1500,
                    "ai_model_used": "gpt-4o-mini",
                    "mcp_analysis_included": True,
                    "rag_context_applied": True
                },
                "rag_analysis": {
                    "words_avoided": 3,
                    "words_reinforced": 2,
                    "new_words_generated": 20,
                    "progression_appropriate": True
                },
                "quality_metrics": {
                    "context_relevance": 0.92,
                    "cefr_appropriateness": 0.95,
                    "vocabulary_diversity": 0.88,
                    "phonetic_accuracy": 0.97
                },
                "phoneme_analysis": {
                    "total_unique_phonemes": 35,
                    "most_common_phonemes": ["/ə/", "/ɪ/", "/eɪ/"],
                    "stress_patterns": ["primary_first", "primary_second"],
                    "syllable_distribution": {"1": 5, "2": 12, "3": 6, "4+": 2}
                },
                "pronunciation_coverage": {
                    "vowel_sounds": 0.85,
                    "consonant_clusters": 0.70,
                    "stress_patterns": 0.90
                }
            }
        }
    }


# =============================================================================
# PHONETIC VALIDATION MODELS - NOVOS PYDANTIC V2
# =============================================================================

class PhoneticValidationResult(BaseModel):
    """Resultado da validação fonética de um item de vocabulário."""
    word: str = Field(..., description="Palavra validada")
    phoneme: str = Field(..., description="Fonema validado")
    is_valid: bool = Field(..., description="Se a validação passou")
    
    validation_details: Dict[str, Any] = Field(..., description="Detalhes da validação")
    suggestions: List[str] = Field(default=[], description="Sugestões de correção")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confiança na validação")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "word": "restaurant",
                "phoneme": "/ˈrɛstərɑnt/",
                "is_valid": True,
                "validation_details": {
                    "ipa_symbols_valid": True,
                    "stress_marking_correct": True,
                    "syllable_count_matches": True,
                    "variant_appropriate": True
                },
                "suggestions": [],
                "confidence_score": 0.98
            }
        }
    }


class BulkPhoneticValidation(BaseModel):
    """Validação fonética em lote."""
    total_items: int = Field(..., description="Total de itens validados")
    valid_items: int = Field(..., description="Itens válidos")
    invalid_items: int = Field(..., description="Itens inválidos")
    
    validation_results: List[PhoneticValidationResult] = Field(..., description="Resultados individuais")
    overall_quality: float = Field(..., ge=0.0, le=1.0, description="Qualidade geral")
    
    common_errors: List[str] = Field(default=[], description="Erros comuns encontrados")
    improvement_suggestions: List[str] = Field(default=[], description="Sugestões de melhoria")


# =============================================================================
# MIGRATION HELPERS (Para compatibilidade) - ATUALIZADO PYDANTIC V2
# =============================================================================

class LegacyUnitAdapter(BaseModel):
    """Adaptador para unidades do sistema antigo."""
    
    @classmethod
    def from_legacy_unit(cls, legacy_data: Dict[str, Any]) -> UnitResponse:
        """Converte unidade do formato antigo para o novo com hierarquia."""
        # Implementar lógica de migração
        # Por enquanto, valores padrão para hierarquia
        return UnitResponse(
            id=legacy_data.get("id", "legacy_unit"),
            course_id=legacy_data.get("course_id", "course_default"),
            book_id=legacy_data.get("book_id", "book_default"),
            sequence_order=legacy_data.get("sequence_order", 1),
            title=legacy_data.get("title", "Legacy Unit"),
            main_aim=legacy_data.get("main_aim", "Legacy main aim"),
            subsidiary_aims=legacy_data.get("subsidiary_aims", []),
            unit_type=UnitType(legacy_data.get("unit_type", "lexical_unit")),
            cefr_level=CEFRLevel(legacy_data.get("cefr_level", "A1")),
            language_variant=LanguageVariant(legacy_data.get("language_variant", "american_english")),
            status=UnitStatus(legacy_data.get("status", "creating")),
            vocabulary=legacy_data.get("vocabulary"),
            sentences=legacy_data.get("sentences"),
            tips=legacy_data.get("tips"),
            grammar=legacy_data.get("grammar"),
            qa=legacy_data.get("qa"),
            assessments=legacy_data.get("assessments"),
            # NOVOS CAMPOS PARA COMPATIBILIDADE
            phonemes_introduced=legacy_data.get("phonemes_introduced", []),
            pronunciation_focus=legacy_data.get("pronunciation_focus"),
            created_at=legacy_data.get("created_at", datetime.now()),
            updated_at=legacy_data.get("updated_at", datetime.now())
        )
    
    @classmethod
    def migrate_vocabulary_to_ipa(cls, legacy_vocabulary: List[Dict[str, Any]]) -> List[VocabularyItem]:
        """Migrar vocabulário antigo para formato com IPA."""
        migrated_items = []
        
        for item in legacy_vocabulary:
            # Gerar fonema básico se não existir
            phoneme = item.get("phoneme")
            if not phoneme:
                # Fonema placeholder - deveria ser gerado por IA
                word = item.get("word", "")
                phoneme = f"/placeholder_{word}/"
            
            try:
                vocabulary_item = VocabularyItem(
                    word=item.get("word", ""),
                    phoneme=phoneme,
                    definition=item.get("definition", ""),
                    example=item.get("example", ""),
                    word_class=item.get("word_class", "noun"),
                    frequency_level=item.get("frequency_level", "medium"),
                    context_relevance=item.get("context_relevance", 0.5),
                    is_reinforcement=item.get("is_reinforcement", False),
                    ipa_variant="general_american",
                    syllable_count=item.get("syllable_count", 1)
                )
                migrated_items.append(vocabulary_item)
            except Exception as e:
                # Log erro e pular item inválido
                print(f"Erro ao migrar item {item.get('word', 'unknown')}: {str(e)}")
                continue
        
        return migrated_items


# =============================================================================
# L1 INTERFERENCE PATTERN MODEL - PYDANTIC V2
# =============================================================================

class L1InterferencePattern(BaseModel):
    """Modelo para padrões de interferência L1→L2 (português→inglês)."""
    pattern_type: str = Field(..., description="Tipo de padrão de interferência")
    portuguese_structure: str = Field(..., description="Estrutura em português")
    incorrect_english: str = Field(..., description="Inglês incorreto (interferência)")
    correct_english: str = Field(..., description="Inglês correto")
    explanation: str = Field(..., description="Explicação da interferência")
    prevention_strategy: str = Field(..., description="Estratégia de prevenção")
    examples: List[str] = Field(default=[], description="Exemplos adicionais")
    difficulty_level: str = Field(default="intermediate", description="Nível de dificuldade")
    
    # Validações específicas
    @field_validator('pattern_type')
    @classmethod
    def validate_pattern_type(cls, v: str) -> str:
        """Validar tipo de padrão."""
        valid_types = {
            "grammatical", "lexical", "phonetic", "semantic", 
            "syntactic", "cultural", "pragmatic"
        }
        
        if v.lower() not in valid_types:
            raise ValueError(f"Tipo de padrão deve ser um de: {', '.join(valid_types)}")
        
        return v.lower()
    
    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty_level(cls, v: str) -> str:
        """Validar nível de dificuldade."""
        valid_levels = {"beginner", "elementary", "intermediate", "upper_intermediate", "advanced"}
        
        if v.lower() not in valid_levels:
            raise ValueError(f"Nível de dificuldade deve ser um de: {', '.join(valid_levels)}")
        
        return v.lower()
    
    @field_validator('prevention_strategy')
    @classmethod
    def validate_prevention_strategy(cls, v: str) -> str:
        """Validar estratégia de prevenção."""
        valid_strategies = {
            "contrastive_exercises", "awareness_raising", "drilling", 
            "error_correction", "explicit_instruction", "input_enhancement",
            "consciousness_raising", "form_focused_instruction"
        }
        
        if v.lower() not in valid_strategies:
            raise ValueError(f"Estratégia deve ser uma de: {', '.join(valid_strategies)}")
        
        return v.lower()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "pattern_type": "grammatical",
                "portuguese_structure": "Eu tenho 25 anos",
                "incorrect_english": "I have 25 years",
                "correct_english": "I am 25 years old",
                "explanation": "Portuguese uses 'ter' (have) for age, English uses 'be'",
                "prevention_strategy": "contrastive_exercises",
                "examples": [
                    "I am 30 years old",
                    "She is 25 years old",
                    "How old are you? (not: How many years do you have?)"
                ],
                "difficulty_level": "beginner"
            }
        }
    }


class L1InterferenceAnalysis(BaseModel):
    """Análise completa de interferência L1→L2."""
    grammar_point: str = Field(..., description="Ponto gramatical analisado")
    vocabulary_items: List[str] = Field(..., description="Itens de vocabulário analisados")
    cefr_level: str = Field(..., description="Nível CEFR do conteúdo")
    
    identified_patterns: List[L1InterferencePattern] = Field(..., description="Padrões identificados")
    prevention_strategies: List[str] = Field(..., description="Estratégias de prevenção gerais")
    common_mistakes: List[str] = Field(..., description="Erros comuns identificados")
    preventive_exercises: List[Dict[str, Any]] = Field(..., description="Exercícios preventivos sugeridos")
    
    # Métricas de análise
    interference_risk_score: float = Field(..., ge=0.0, le=1.0, description="Score de risco de interferência")
    patterns_count: int = Field(..., ge=0, description="Número de padrões identificados")
    coverage_areas: List[str] = Field(..., description="Áreas de interferência cobertas")
    
    generated_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('interference_risk_score')
    @classmethod
    def validate_risk_score(cls, v: float) -> float:
        """Validar score de risco."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score de risco deve estar entre 0.0 e 1.0")
        return v
    
    @field_validator('patterns_count')
    @classmethod
    def validate_patterns_count(cls, v: int, info: ValidationInfo) -> int:
        """Validar contagem de padrões."""
        if hasattr(info, 'data') and 'identified_patterns' in info.data:
            patterns = info.data['identified_patterns']
            if v != len(patterns):
                return len(patterns)
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "grammar_point": "Age expressions",
                "vocabulary_items": ["age", "years", "old", "young"],
                "cefr_level": "A1",
                "identified_patterns": [
                    {
                        "pattern_type": "grammatical",
                        "portuguese_structure": "Eu tenho X anos",
                        "incorrect_english": "I have X years",
                        "correct_english": "I am X years old",
                        "explanation": "Age structure difference PT vs EN",
                        "prevention_strategy": "contrastive_exercises"
                    }
                ],
                "prevention_strategies": [
                    "Contrast exercises Portuguese vs English",
                    "Explicit instruction on BE vs HAVE",
                    "Drilling with age expressions"
                ],
                "common_mistakes": [
                    "Using HAVE instead of BE for age",
                    "Literal translation from Portuguese",
                    "Missing 'old' in age expressions"
                ],
                "preventive_exercises": [
                    {
                        "type": "contrast_exercise",
                        "description": "Compare PT and EN age expressions",
                        "examples": ["PT: Tenho 20 anos → EN: I am 20 years old"]
                    }
                ],
                "interference_risk_score": 0.8,
                "patterns_count": 1,
                "coverage_areas": ["grammatical_structure", "verb_usage"]
            }
        }
    }


# =============================================================================
# UTILITY FUNCTIONS PARA IPA - NOVAS
# =============================================================================

def extract_phonemes_from_vocabulary(vocabulary_section: VocabularySection) -> List[str]:
    """Extrair lista única de fonemas de uma seção de vocabulário."""
    phonemes = set()
    
    for item in vocabulary_section.items:
        # Extrair fonemas individuais do campo phoneme
        clean_phoneme = item.phoneme.strip('/[]')
        # Separar por espaços e pontos para obter fonemas individuais
        individual_phonemes = clean_phoneme.replace('.', ' ').split()
        
        for phoneme in individual_phonemes:
            if phoneme and len(phoneme) > 0:
                phonemes.add(phoneme)
    
    return sorted(list(phonemes))


def analyze_phonetic_complexity(vocabulary_items: List[VocabularyItem]) -> Dict[str, Any]:
    """Analisar complexidade fonética de uma lista de itens de vocabulário."""
    if not vocabulary_items:
        return {"complexity": "unknown", "details": {}}
    
    syllable_counts = [item.syllable_count for item in vocabulary_items if item.syllable_count]
    phoneme_lengths = [len(item.phoneme.strip('/[]').replace(' ', '')) for item in vocabulary_items]
    
    avg_syllables = sum(syllable_counts) / len(syllable_counts) if syllable_counts else 1
    avg_phoneme_length = sum(phoneme_lengths) / len(phoneme_lengths) if phoneme_lengths else 5
    
    # Determinar complexidade baseada em métricas
    if avg_syllables <= 1.5 and avg_phoneme_length <= 6:
        complexity = "simple"
    elif avg_syllables <= 2.5 and avg_phoneme_length <= 10:
        complexity = "medium"
    elif avg_syllables <= 3.5 and avg_phoneme_length <= 15:
        complexity = "complex"
    else:
        complexity = "very_complex"
    
    return {
        "complexity": complexity,
        "details": {
            "average_syllables": round(avg_syllables, 2),
            "average_phoneme_length": round(avg_phoneme_length, 2),
            "total_items": len(vocabulary_items),
            "syllable_distribution": {
                "1": len([s for s in syllable_counts if s == 1]),
                "2": len([s for s in syllable_counts if s == 2]),
                "3": len([s for s in syllable_counts if s == 3]),
                "4+": len([s for s in syllable_counts if s >= 4])
            }
        }
    }


def validate_ipa_consistency(vocabulary_items: List[VocabularyItem]) -> Dict[str, Any]:
    """Validar consistência IPA entre itens de vocabulário."""
    variants = set(item.ipa_variant for item in vocabulary_items)
    inconsistencies = []
    
    if len(variants) > 1:
        inconsistencies.append(f"Múltiplas variantes IPA encontradas: {variants}")
    
    # Verificar padrões de stress inconsistentes
    stress_patterns = [item.stress_pattern for item in vocabulary_items if item.stress_pattern]
    unique_patterns = set(stress_patterns)
    
    if len(unique_patterns) > 3:
        inconsistencies.append(f"Muitos padrões de stress diferentes: {unique_patterns}")
    
    return {
        "is_consistent": len(inconsistencies) == 0,
        "inconsistencies": inconsistencies,
        "variants_used": list(variants),
        "stress_patterns_used": list(unique_patterns)
    }


# =============================================================================
# UTILIDADES PARA L1 INTERFERENCE
# =============================================================================

def create_l1_interference_pattern(
    pattern_type: str,
    portuguese_structure: str,
    incorrect_english: str,
    correct_english: str,
    explanation: str,
    prevention_strategy: str = "contrastive_exercises",
    examples: List[str] = None,
    difficulty_level: str = "intermediate"
) -> L1InterferencePattern:
    """Criar um padrão de interferência L1→L2."""
    return L1InterferencePattern(
        pattern_type=pattern_type,
        portuguese_structure=portuguese_structure,
        incorrect_english=incorrect_english,
        correct_english=correct_english,
        explanation=explanation,
        prevention_strategy=prevention_strategy,
        examples=examples or [],
        difficulty_level=difficulty_level
    )


def get_common_l1_interference_patterns() -> List[L1InterferencePattern]:
    """Retornar padrões comuns de interferência para brasileiros."""
    return [
        L1InterferencePattern(
            pattern_type="grammatical",
            portuguese_structure="Eu tenho 25 anos",
            incorrect_english="I have 25 years",
            correct_english="I am 25 years old",
            explanation="Portuguese uses 'ter' (have) for age, English uses 'be'",
            prevention_strategy="contrastive_exercises",
            examples=["I am 30 years old", "She is 25 years old"],
            difficulty_level="beginner"
        ),
        L1InterferencePattern(
            pattern_type="lexical",
            portuguese_structure="Eu estou com fome",
            incorrect_english="I am with hunger",
            correct_english="I am hungry",
            explanation="Portuguese uses 'estar com + noun', English uses 'be + adjective'",
            prevention_strategy="explicit_instruction",
            examples=["I am thirsty", "I am tired", "I am cold"],
            difficulty_level="beginner"
        ),
        L1InterferencePattern(
            pattern_type="grammatical",
            portuguese_structure="A Maria é mais alta que a Ana",
            incorrect_english="Maria is more tall than Ana",
            correct_english="Maria is taller than Ana",
            explanation="Portuguese always uses 'mais + adjective', English has irregular comparatives",
            prevention_strategy="drilling",
        ),
        L1InterferencePattern(
            pattern_type="grammatical",
            portuguese_structure="A Maria é mais alta que a Ana",
            incorrect_english="Maria is more tall than Ana",
            correct_english="Maria is taller than Ana",
            explanation="Portuguese always uses 'mais + adjective', English has irregular comparatives",
            prevention_strategy="drilling",
            examples=["bigger (not more big)", "better (not more good)"],
            difficulty_level="elementary"
        ),
        L1InterferencePattern(
            pattern_type="phonetic",
            portuguese_structure="Hospital [hos-pi-TAL]",
            incorrect_english="Hospital [hos-pi-TAL]",
            correct_english="Hospital [HOS-pi-tal]",
            explanation="Portuguese stress on final syllable, English on first",
            prevention_strategy="awareness_raising",
            examples=["Hotel [ho-TEL] vs [ho-TEL]", "Animal [a-ni-MAL] vs [AN-i-mal]"],
            difficulty_level="intermediate"
        ),
        L1InterferencePattern(
            pattern_type="semantic",
            portuguese_structure="Pretender fazer algo",
            incorrect_english="I pretend to do something",
            correct_english="I intend to do something",
            explanation="Portuguese 'pretender' = English 'intend', not 'pretend'",
            prevention_strategy="consciousness_raising",
            examples=["I intend to study", "I plan to travel"],
            difficulty_level="intermediate"
        )
        ]


def analyze_text_for_l1_interference(text: str, cefr_level: str) -> List[str]:
    """Analisar texto para possíveis interferências L1."""
    common_patterns = get_common_l1_interference_patterns()
    potential_issues = []
    
    text_lower = text.lower()
    
    # Verificar padrões conhecidos
    interference_indicators = {
        "have + number + years": "Age expression with HAVE instead of BE",
        "more + adjective": "Comparative with MORE instead of -ER",
        "with + emotion noun": "Emotion expression with WITH instead of adjective",
        "pretend + to": "False friend: pretend vs intend"
    }
    
    for pattern, issue in interference_indicators.items():
        # Verificação simplificada - na prática seria mais sofisticada
        if any(word in text_lower for word in pattern.split(" + ")):
            potential_issues.append(issue)
    
    return potential_issues


# =============================================================================
# UTILIDADES PARA COMMON MISTAKES
# =============================================================================

def create_common_mistake(
    mistake_type: str,
    incorrect_form: str,
    correct_form: str,
    explanation: str,
    examples: List[str] = None,
    l1_interference: bool = False,
    prevention_strategy: str = "explicit_instruction",
    frequency: str = "medium",
    cefr_level: str = "A2",
    # ✅ NOVOS PARÂMETROS
    context_where_occurs: Optional[str] = None,
    severity_score: Optional[float] = None,
    remedial_exercises: List[str] = None
) -> CommonMistake:
    """Criar um erro comum com parâmetros expandidos."""
    return CommonMistake(
        mistake_type=mistake_type,
        incorrect_form=incorrect_form,
        correct_form=correct_form,
        explanation=explanation,
        examples=examples or [],
        l1_interference=l1_interference,
        prevention_strategy=prevention_strategy,
        frequency=frequency,
        cefr_level=cefr_level,
        context_where_occurs=context_where_occurs,
        severity_score=severity_score,
        remedial_exercises=remedial_exercises or []
    )


def get_common_brazilian_mistakes() -> List[CommonMistake]:
    """Retornar erros comuns para brasileiros - VERSÃO EXPANDIDA."""
    return [
        CommonMistake(
            mistake_type="grammatical",
            incorrect_form="I have 25 years",
            correct_form="I am 25 years old",
            explanation="Portuguese uses 'ter' (have) for age, English uses 'be'",
            examples=[
                "She has 30 years → She is 30 years old",
                "My brother has 18 years → My brother is 18 years old"
            ],
            l1_interference=True,
            prevention_strategy="contrastive_exercises",
            frequency="very_high",
            cefr_level="A1",
            context_where_occurs="Personal introductions, biographical information",
            age_group_frequency="all_ages",
            severity_score=0.95,
            remedial_exercises=[
                "BE + age drills",
                "How old questions practice",
                "Contrastive Portuguese vs English"
            ]
        ),
        CommonMistake(
            mistake_type="lexical", 
            incorrect_form="I am with hunger",
            correct_form="I am hungry",
            explanation="Portuguese 'estar com fome' vs English adjective",
            examples=[
                "I am with thirst → I am thirsty",
                "She is with cold → She is cold"
            ],
            l1_interference=True,
            prevention_strategy="pattern_recognition",
            frequency="high",
            cefr_level="A1",
            context_where_occurs="Daily activities, basic needs expression",
            age_group_frequency="all_ages",
            severity_score=0.8,
            remedial_exercises=[
                "BE + adjective practice",
                "Physical state expressions",
                "Contrast exercises: COM vs adjective"
            ]
        ),
        CommonMistake(
            mistake_type="article_omission",
            incorrect_form="The life is beautiful",
            correct_form="Life is beautiful", 
            explanation="Portuguese uses definite article with abstract nouns",
            examples=[
                "The love is important → Love is important",
                "The music helps relaxation → Music helps relaxation"
            ],
            l1_interference=True,
            prevention_strategy="awareness_raising",
            frequency="high",
            cefr_level="A2",
            context_where_occurs="Abstract concepts, generalizations",
            age_group_frequency="teenagers",
            severity_score=0.7,
            remedial_exercises=[
                "Abstract noun practice",
                "Article omission drills",
                "Generalization statements"
            ]
        ),
        CommonMistake(
            mistake_type="false_friend",
            incorrect_form="I will assist the conference",
            correct_form="I will attend the conference",
            explanation="Portuguese 'assistir' = English 'attend', not 'assist'",
            examples=[
                "I assisted the movie → I watched the movie",
                "Did you assist the class? → Did you attend the class?"
            ],
            l1_interference=True,
            prevention_strategy="explicit_instruction",
            frequency="medium",
            cefr_level="B1",
            context_where_occurs="Academic and professional contexts",
            age_group_frequency="adults",
            severity_score=0.6,
            remedial_exercises=[
                "False friends identification",
                "Context-based vocabulary practice",
                "Attend vs assist contrast"
            ]
        ),
        CommonMistake(
            mistake_type="pronunciation",
            incorrect_form="/ˈhospɪtal/ (stress on final)",
            correct_form="/ˈhɒspɪtl/ (stress on first)",
            explanation="Portuguese stress on final syllable vs English initial stress",
            examples=[
                "hotel: /hoˈtɛw/ → /hoʊˈtel/",
                "animal: /aniˈmaw/ → /ˈænɪməl/"
            ],
            l1_interference=True,
            prevention_strategy="drilling",
            frequency="medium",
            cefr_level="A2",
            context_where_occurs="Cognate words, formal vocabulary",
            age_group_frequency="all_ages",
            severity_score=0.5,
            remedial_exercises=[
                "Stress pattern recognition",
                "Cognate pronunciation drills",
                "Minimal pair practice"
            ]
        )
    ]


# ✅ MELHORIA 7: Função de análise mais robusta
def analyze_text_for_common_mistakes(
    text: str, 
    cefr_level: str = "A2",
    focus_l1_interference: bool = True
) -> Dict[str, Any]:
    """Analisar texto para identificar erros comuns - VERSÃO MELHORADA."""
    common_mistakes = get_common_brazilian_mistakes()
    identified_mistakes = []
    
    text_lower = text.lower()
    
    # Filtrar por nível CEFR se especificado
    if cefr_level:
        common_mistakes = [
            mistake for mistake in common_mistakes 
            if mistake.cefr_level <= cefr_level
        ]
    
    # Filtrar por interferência L1 se especificado
    if focus_l1_interference:
        common_mistakes = [
            mistake for mistake in common_mistakes 
            if mistake.l1_interference
        ]
    
    # Verificar padrões de erro conhecidos
    for mistake in common_mistakes:
        # Análise mais sofisticada
        incorrect_parts = mistake.incorrect_form.lower().split()
        
        # Verificar se padrão existe no texto
        pattern_found = False
        
        # Verificação por palavras-chave
        if len(incorrect_parts) <= 3:
            pattern_found = all(part in text_lower for part in incorrect_parts)
        else:
            # Para padrões mais complexos, verificar proximidade
            positions = []
            for part in incorrect_parts:
                if part in text_lower:
                    positions.append(text_lower.find(part))
                else:
                    break
            
            if len(positions) == len(incorrect_parts):
                # Verificar se palavras estão próximas (dentro de 10 caracteres)
                max_distance = max(positions) - min(positions)
                pattern_found = max_distance <= 20
        
        if pattern_found:
            identified_mistakes.append(mistake)
    
    # Análise estatística
    total_words = len(text.split())
    error_density = len(identified_mistakes) / max(total_words, 1)
    
    # Categorizar erros
    error_categories = {}
    severity_scores = []
    
    for mistake in identified_mistakes:
        category = mistake.mistake_type
        error_categories[category] = error_categories.get(category, 0) + 1
        
        if mistake.severity_score:
            severity_scores.append(mistake.severity_score)
    
    return {
        "identified_mistakes": identified_mistakes,
        "analysis_summary": {
            "total_errors_found": len(identified_mistakes),
            "error_density": round(error_density, 3),
            "average_severity": round(sum(severity_scores) / len(severity_scores), 2) if severity_scores else 0,
            "error_categories": error_categories,
            "l1_interference_errors": len([m for m in identified_mistakes if m.l1_interference]),
            "most_common_error_type": max(error_categories.keys(), key=error_categories.get) if error_categories else None
        },
        "recommendations": [
            f"Focus on {mistake.prevention_strategy} for {mistake.mistake_type} errors"
            for mistake in identified_mistakes[:3]
        ],
        "text_analysis": {
            "word_count": total_words,
            "cefr_level_analyzed": cefr_level,
            "l1_interference_focus": focus_l1_interference
        }
    }


# =============================================================================
# FUNÇÕES UTILITÁRIAS ADICIONAIS
# =============================================================================

def get_mistakes_by_cefr_level(cefr_level: str) -> List[CommonMistake]:
    """Obter erros comuns para um nível CEFR específico."""
    all_mistakes = get_common_brazilian_mistakes()
    return [mistake for mistake in all_mistakes if mistake.cefr_level == cefr_level.upper()]


def get_mistakes_by_type(mistake_type: str) -> List[CommonMistake]:
    """Obter erros comuns por tipo."""
    all_mistakes = get_common_brazilian_mistakes()
    return [mistake for mistake in all_mistakes if mistake.mistake_type == mistake_type.lower()]


def get_high_priority_mistakes() -> List[CommonMistake]:
    """Obter erros de alta prioridade (frequency=high/very_high, severity>0.7)."""
    all_mistakes = get_common_brazilian_mistakes()
    return [
        mistake for mistake in all_mistakes 
        if mistake.frequency in ["high", "very_high"] and 
           (mistake.severity_score or 0) > 0.7
    ]


# =============================================================================
# VALIDAÇÃO E STATUS
# =============================================================================

def validate_common_mistake_structure(mistake_data: dict) -> Dict[str, Any]:
    """Validar estrutura de dados de erro comum."""
    try:
        mistake = CommonMistake(**mistake_data)
        return {
            "valid": True,
            "validated_mistake": mistake,
            "validation_errors": []
        }
    except ValidationError as e:
        return {
            "valid": False,
            "validated_mistake": None,
            "validation_errors": [str(error) for error in e.errors()]
        }


# Constrastive example
class ContrastiveExample(BaseModel):
    """
    Exemplo contrastivo para análise estrutural português↔inglês.
    Diferente de CommonMistake - foca em PREVENÇÃO via contraste estrutural.
    
    Usado pelo L1InterferenceAnalyzer para análise preventiva.
    """
    
    # Estruturas contrastivas
    portuguese: str = Field(..., description="Versão/estrutura em português")
    english_wrong: str = Field(..., description="Inglês incorreto (transferência literal)")
    english_correct: str = Field(..., description="Inglês correto")
    
    # Análise pedagógica
    teaching_point: str = Field(..., description="Ponto de ensino principal")
    structural_difference: str = Field(..., description="Diferença estrutural específica")
    interference_type: str = Field(..., description="Tipo de interferência")
    
    # Contexto pedagógico
    cefr_level: str = Field(default="A2", description="Nível CEFR relevante")
    difficulty_level: str = Field(default="medium", description="Nível de dificuldade")
    prevention_strategy: str = Field(default="contrastive_awareness", description="Estratégia de prevenção")
    
    # Exemplos práticos
    additional_examples: List[str] = Field(default=[], description="Exemplos adicionais")
    practice_sentences: List[str] = Field(default=[], description="Frases para prática")
    
    # Metadados
    linguistic_explanation: Optional[str] = Field(None, description="Explicação linguística detalhada")
    common_in_context: Optional[str] = Field(None, description="Contexto onde é comum")
    
    @field_validator('interference_type')
    @classmethod
    def validate_interference_type(cls, v: str) -> str:
        """Validar tipo de interferência."""
        valid_types = {
            "grammatical_structure",     # Diferenças gramaticais
            "word_order",               # Ordem das palavras
            "article_usage",            # Uso de artigos
            "verb_construction",        # Construção verbal
            "preposition_pattern",      # Padrões de preposição
            "pronoun_usage",           # Uso de pronomes
            "tense_aspect",            # Tempo e aspecto
            "modality_expression",     # Expressão de modalidade
            "negation_pattern",        # Padrões de negação
            "question_formation",      # Formação de perguntas
            "comparative_structure",   # Estruturas comparativas
            "possession_expression"    # Expressão de posse
        }
        
        if v not in valid_types:
            raise ValueError(f"Tipo de interferência deve ser um de: {', '.join(valid_types)}")
        
        return v
    
    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty_level(cls, v: str) -> str:
        """Validar nível de dificuldade."""
        valid_levels = {"very_easy", "easy", "medium", "hard", "very_hard"}
        
        if v not in valid_levels:
            raise ValueError(f"Nível de dificuldade deve ser um de: {', '.join(valid_levels)}")
        
        return v
    
    @field_validator('prevention_strategy')
    @classmethod
    def validate_prevention_strategy(cls, v: str) -> str:
        """Validar estratégia de prevenção."""
        valid_strategies = {
            "contrastive_awareness",     # Conscientização contrastiva
            "explicit_instruction",     # Instrução explícita
            "pattern_recognition",      # Reconhecimento de padrões
            "controlled_practice",      # Prática controlada
            "error_anticipation",       # Antecipação de erros
            "structural_comparison",    # Comparação estrutural
            "metalinguistic_awareness", # Consciência metalinguística
            "form_focused_instruction"  # Instrução focada na forma
        }
        
        if v not in valid_strategies:
            raise ValueError(f"Estratégia deve ser uma de: {', '.join(valid_strategies)}")
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "portuguese": "Eu tenho 25 anos",
                "english_wrong": "I have 25 years",
                "english_correct": "I am 25 years old",
                "teaching_point": "Age expression uses BE + years old, not HAVE + years",
                "structural_difference": "Portuguese uses HAVE + age, English uses BE + age + 'years old'",
                "interference_type": "verb_construction",
                "cefr_level": "A1",
                "difficulty_level": "medium",
                "prevention_strategy": "contrastive_awareness",
                "additional_examples": [
                    "She is 30 years old (not: She has 30 years)",
                    "How old are you? (not: How many years do you have?)"
                ],
                "practice_sentences": [
                    "My brother ___ 22 years old. (is)",
                    "How old ___ your sister? (is)"
                ],
                "linguistic_explanation": "Portuguese 'ter idade' vs English 'be age years old' represents different conceptualization of age as possession vs state",
                "common_in_context": "Basic personal information, introductions"
            }
        }
    }


class ContrastiveExampleSection(BaseModel):
    """Seção de exemplos contrastivos para uma unidade - ANÁLISE ESTRUTURAL."""
    examples: List[ContrastiveExample] = Field(..., description="Lista de exemplos contrastivos")
    total_examples: int = Field(..., description="Total de exemplos")
    
    # Análise da seção
    main_interference_types: List[str] = Field(default=[], description="Principais tipos de interferência")
    prevention_focus: str = Field(..., description="Foco principal de prevenção")
    difficulty_assessment: str = Field(default="medium", description="Avaliação de dificuldade geral")
    
    # Recomendações pedagógicas
    teaching_sequence: List[str] = Field(default=[], description="Sequência recomendada de ensino")
    practice_activities: List[str] = Field(default=[], description="Atividades de prática sugeridas")
    
    # Metadados
    target_cefr_level: str = Field(..., description="Nível CEFR alvo")
    brazilian_learner_focus: bool = Field(True, description="Foco em aprendizes brasileiros")
    
    generated_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('total_examples')
    @classmethod
    def validate_total_examples(cls, v: int, info: ValidationInfo) -> int:
        """Validar contagem total."""
        if hasattr(info, 'data') and 'examples' in info.data:
            examples = info.data['examples']
            if v != len(examples):
                return len(examples)
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "examples": [
                    {
                        "portuguese": "Eu tenho 25 anos",
                        "english_wrong": "I have 25 years", 
                        "english_correct": "I am 25 years old",
                        "teaching_point": "Age expression difference",
                        "structural_difference": "Portuguese TER vs English BE",
                        "interference_type": "verb_construction"
                    }
                ],
                "total_examples": 1,
                "main_interference_types": ["verb_construction"],
                "prevention_focus": "Structural awareness of PT vs EN verb usage",
                "difficulty_assessment": "medium",
                "teaching_sequence": [
                    "Present Portuguese structure",
                    "Show English equivalent", 
                    "Highlight difference",
                    "Practice correct form"
                ],
                "practice_activities": [
                    "Contrastive comparison exercises",
                    "Error identification tasks",
                    "Controlled production practice"
                ],
                "target_cefr_level": "A1",
                "brazilian_learner_focus": True
            }
        }
    }


# =============================================================================
# UTILITY FUNCTIONS PARA CONTRASTIVE EXAMPLES
# =============================================================================

def create_contrastive_example(
    portuguese: str,
    english_wrong: str,
    english_correct: str,
    teaching_point: str,
    structural_difference: str = "",
    interference_type: str = "grammatical_structure",
    cefr_level: str = "A2",
    difficulty_level: str = "medium",
    prevention_strategy: str = "contrastive_awareness",
    additional_examples: List[str] = None,
    practice_sentences: List[str] = None
) -> ContrastiveExample:
    """Criar um exemplo contrastivo estruturado."""
    return ContrastiveExample(
        portuguese=portuguese,
        english_wrong=english_wrong,
        english_correct=english_correct,
        teaching_point=teaching_point,
        structural_difference=structural_difference or f"Portuguese vs English structural difference",
        interference_type=interference_type,
        cefr_level=cefr_level,
        difficulty_level=difficulty_level,
        prevention_strategy=prevention_strategy,
        additional_examples=additional_examples or [],
        practice_sentences=practice_sentences or []
    )


def get_common_contrastive_examples_for_brazilians() -> List[ContrastiveExample]:
    """Retornar exemplos contrastivos comuns para brasileiros."""
    return [
        ContrastiveExample(
            portuguese="Eu tenho 25 anos",
            english_wrong="I have 25 years",
            english_correct="I am 25 years old",
            teaching_point="Age expression uses BE + years old, not HAVE + years",
            structural_difference="Portuguese: TER + idade | English: BE + idade + years old",
            interference_type="verb_construction",
            cefr_level="A1",
            difficulty_level="medium",
            prevention_strategy="contrastive_awareness",
            additional_examples=[
                "She is 30 years old (not: She has 30 years)",
                "How old are you? (not: How many years do you have?)"
            ],
            practice_sentences=[
                "My brother ___ 22 years old. (is)",
                "How old ___ your sister? (is)"
            ]
        ),
        ContrastiveExample(
            portuguese="Eu estou com fome",
            english_wrong="I am with hunger",
            english_correct="I am hungry",
            teaching_point="Emotions/states use adjectives, not 'with + noun'",
            structural_difference="Portuguese: ESTAR COM + substantivo | English: BE + adjetivo",
            interference_type="grammatical_structure",
            cefr_level="A1",
            difficulty_level="easy",
            prevention_strategy="pattern_recognition",
            additional_examples=[
                "I am thirsty (not: I am with thirst)",
                "I am tired (not: I am with tiredness)"
            ],
            practice_sentences=[
                "She is ___ after the long walk. (tired)",
                "Are you ___? There's food in the kitchen. (hungry)"
            ]
        ),
        ContrastiveExample(
            portuguese="A vida é bela",
            english_wrong="The life is beautiful",
            english_correct="Life is beautiful",
            teaching_point="Abstract nouns don't need definite article in generalizations",
            structural_difference="Portuguese: artigo + substantivo abstrato | English: substantivo abstrato (sem artigo)",
            interference_type="article_usage",
            cefr_level="A2",
            difficulty_level="hard",
            prevention_strategy="explicit_instruction",
            additional_examples=[
                "Love is important (not: The love is important)",
                "Music is universal (not: The music is universal)"
            ],
            practice_sentences=[
                "___ is the key to happiness. (Love)",
                "___ helps us relax. (Music)"
            ]
        ),
        ContrastiveExample(
            portuguese="Ela é mais alta que eu",
            english_wrong="She is more tall than me",
            english_correct="She is taller than me",
            teaching_point="Short adjectives use -er, not 'more + adjective'",
            structural_difference="Portuguese: MAIS + adjetivo | English: adjetivo-ER (para adj. curtos)",
            interference_type="comparative_structure",
            cefr_level="A2",
            difficulty_level="medium",
            prevention_strategy="pattern_recognition",
            additional_examples=[
                "He is faster than his brother (not: more fast)",
                "This book is better than that one (not: more good)"
            ],
            practice_sentences=[
                "This car is ___ than mine. (faster)",
                "My house is ___ than yours. (bigger)"
            ]
        )
    ]


def analyze_contrastive_pattern(
    portuguese_structure: str,
    english_structure: str,
    examples: List[str] = None
) -> Dict[str, Any]:
    """Analisar padrão contrastivo entre português e inglês."""
    return {
        "portuguese_pattern": portuguese_structure,
        "english_pattern": english_structure,
        "structural_differences": [
            "Analyze word order differences",
            "Analyze verb construction differences", 
            "Analyze article usage differences",
            "Analyze preposition usage differences"
        ],
        "interference_likelihood": "high" if "ter" in portuguese_structure.lower() else "medium",
        "teaching_recommendations": [
            "Use explicit contrastive explanation",
            "Provide controlled practice",
            "Create awareness activities",
            "Use error anticipation exercises"
        ],
        "examples_provided": examples or [],
        "analysis_confidence": 0.85
    }
# =============================================================================
# FORWARD REFERENCES FIX - PYDANTIC V2 COMPATIBLE
# =============================================================================

# Resolver referências circulares para Pydantic V2
UnitResponse.model_rebuild()
VocabularySection.model_rebuild()
SentencesSection.model_rebuild()
QASection.model_rebuild()


# =============================================================================
# EXPORTS E VERSIONING
# =============================================================================

__all__ = [
    # Input Models
    "UnitCreateRequest",
    
    # Vocabulary Models
    "VocabularyItem",
    "VocabularySection",
    "VocabularyGenerationRequest", 
    "VocabularyGenerationResponse",
    
    # Content Generation Request Models
    "SentenceGenerationRequest",
    "TipsGenerationRequest", 
    "AssessmentGenerationRequest",
    "QAGenerationRequest",
    "GrammarGenerationRequest",
    
    # Content Models
    "TipsContent",
    "GrammarContent",
    
    # Assessment Models
    "AssessmentActivity",
    "AssessmentSection",
    
    # Common Mistake Models - NOVO
    "CommonMistake",
    "CommonMistakeSection",
    
    # Unit Models
    "UnitResponse",
    
    # Additional Content Models
    "Sentence",
    "SentencesSection",
    "QASection",
    "ImageInfo",
    
    # Progress Models
    "GenerationProgress",
    "ErrorResponse",
    "SuccessResponse",
    
    # Bulk Models
    "BulkUnitStatus",
    "CourseStatistics",
    
    # Phonetic Models
    "PhoneticValidationResult",
    "BulkPhoneticValidation",
    
    # L1 Interference Models
    "L1InterferencePattern",
    "L1InterferenceAnalysis",
    
    # Legacy Models
    "LegacyUnitAdapter",
    
    # Utility Functions
    "extract_phonemes_from_vocabulary",
    "analyze_phonetic_complexity",
    "validate_ipa_consistency",
    "create_l1_interference_pattern",
    "get_common_l1_interference_patterns",
    "analyze_text_for_l1_interference",
    "create_common_mistake",
    "get_common_brazilian_mistakes",
    "analyze_text_for_common_mistakes",

    #Constrative Example Models
    "ContrastiveExample",
    "ContrastiveExampleSection", 
    "create_contrastive_example",
    "get_common_contrastive_examples_for_brazilians",
    "analyze_contrastive_pattern"
]

# Versioning para Pydantic V2
__pydantic_version__ = "2.x"
__compatibility__ = "Pydantic V2 Compatible"
__migration_date__ = "2025-01-28"
__breaking_changes__ = [
    "@validator → @field_validator",
    "class Config → model_config", 
    "schema_extra → json_schema_extra",
    "values → info.data in validators"
]