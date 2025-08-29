"""
Gerador de conteúdo gramatical usando IA - LangChain 0.3.
Implementa estratégias GRAMMAR 1 (Sistemática) e GRAMMAR 2 (Prevenção L1→L2).
CORRIGIDO: Prompts contextuais via IA, integração com sistema IVO V2.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import asyncio
from dataclasses import dataclass

# YAML import
import yaml

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Pydantic 2 nativo - sem necessidade de compatibilidade
from pydantic import BaseModel, ValidationError, Field, ConfigDict

# Imports internos
from config.logger_config import get_logger
from config.models import get_openai_config, load_model_configs
from src.core.unit_models import GrammarContent
from src.core.enums import GrammarStrategy

# Logger configurado
logger = get_logger("grammar_generator")
logger.info("🚀 Usando LangChain 0.3 com Pydantic 2 nativo, IA contextual e structured output")


# =============================================================================
# CONSTANTES TÉCNICAS (MANTIDAS - PADRÕES ESTABELECIDOS)
# =============================================================================

GRAMMAR_STRATEGIES = {
    "systematic": "explicacao_sistematica",
    "l1_prevention": "prevencao_erros_l1"
}

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

LANGUAGE_VARIANTS = ["american", "british", "australian", "canadian"]


# Removi @dataclass GrammarContent - agora usando o modelo Pydantic de src.core.unit_models


class GrammarRequest(BaseModel):
    """Modelo de requisição para geração de gramática - Pydantic 2."""
    input_text: str = Field(..., description="Texto base para análise gramatical")
    vocabulary_list: List[str] = Field(..., description="Lista de vocabulário disponível") 
    level: str = Field(..., description="Nível CEFR (A1, A2, B1, B2, C1, C2)")
    variant: str = Field(default="american", description="Variante do inglês")
    unit_context: str = Field(default="", description="Contexto específico da unidade")
    strategy: str = Field(default="systematic", description="Estratégia: systematic ou l1_prevention")
    rag_context: Dict[str, Any] = Field(default_factory=dict, description="Contexto RAG da hierarquia")

    # 🔥 Pydantic 2 - Nova sintaxe de configuração
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )


class GrammarGenerator:
    """Gerador de conteúdo gramatical contextual - LangChain 0.3 + IA."""
    
    def __init__(self):
        """Inicializar gerador com LangChain 0.3 e IA contextual."""
        self.llm = None
        self._load_config()
        
    def _load_config(self):
        """Carregar configurações para LangChain 0.3 com modelo correto."""
        try:
            # NOVO: Usar model_selector para obter o modelo correto
            from src.services.model_selector import get_llm_config_for_service
            
            # Obter configuração específica para grammar_generator
            llm_config = get_llm_config_for_service("grammar_generator")
            
            # 🔧 Parâmetros para LangChain 0.3 com modelo correto (o3-mini)
            self.llm = ChatOpenAI(**llm_config)
            
            logger.info(f"✅ ChatOpenAI v0.3 configurado com modelo: {llm_config.get('model')} (TIER-3: Raciocínio Pedagógico)")
                
        except Exception as e:
            logger.error(f"❌ Erro na configuração: {e}")
            raise

    async def generate_grammar_content(self, request: GrammarRequest) -> GrammarContent:
        """
        Gerar conteúdo gramatical contextual - LangChain 0.3 + IA.
        
        Args:
            request: Dados da requisição validados pelo Pydantic 2
            
        Returns:
            GrammarContent: Conteúdo estruturado por estratégia
        """
        try:
            logger.info(f"🎯 Gerando gramática {request.level} - Estratégia: {request.strategy}")
            
            # Validação automática pelo Pydantic 2
            if not request.input_text.strip():
                raise ValueError("Texto de entrada vazio")
            
            # ANÁLISE VIA IA: Identificar ponto gramatical principal
            grammar_point = await self._identify_grammar_point_ai(
                text=request.input_text,
                vocabulary=request.vocabulary_list,
                context=request.unit_context,
                level=request.level
            )
            
            # ANÁLISE VIA IA: Gerar prompt contextual baseado na estratégia
            contextual_messages = await self._generate_contextual_prompt_ai(
                request=request,
                grammar_point=grammar_point
            )
            
            # 🚀 LangChain 0.3 - Método ainvoke moderno
            logger.debug("🔄 Invocando LLM com prompt contextual (LangChain 0.3)")
            response = await self.llm.ainvoke(contextual_messages)
            
            # Extrair conteúdo da resposta
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 🔄 Usar structured output para garantir formato correto
            grammar_content = await self._generate_grammar_with_structured_output(
                contextual_messages=contextual_messages,
                request=request,
                grammar_point=grammar_point
            )
            
            logger.info(f"✅ Gramática gerada: {grammar_point} ({request.strategy})")
            return grammar_content
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de gramática: {str(e)}")
            raise
    
    def _create_grammar_schema(self) -> Dict[str, Any]:
        """Create precise JSON schema for GrammarContent using LangChain 0.3 structured output."""
        return {
            "title": "GrammarContent",
            "description": "Schema for structured grammar content generation with L1 interference analysis and systematic explanations",
            "type": "object",
            "properties": {
                "grammar_point": {
                    "type": "string",
                    "description": "Main grammar point"
                },
                "systematic_explanation": {
                    "type": "string",
                    "description": "Clear and detailed systematic explanation"
                },
                "usage_rules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "description": "List of usage rules as simple strings"
                },
                "examples": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "description": "List of contextualized examples as simple strings"
                },
                "l1_interference_notes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of L1 interference notes as simple strings"
                },
                "common_mistakes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "mistake": {"type": "string", "description": "Common mistake"},
                            "correction": {"type": "string", "description": "Correction"},
                            "explanation": {"type": "string", "description": "Error explanation"}
                        },
                        "required": ["mistake", "correction", "explanation"],
                        "additionalProperties": False
                    },
                    "description": "List of common mistakes and their corrections"
                },
                "vocabulary_integration": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "How it integrates with vocabulary"
                },
                "previous_grammar_connections": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Connections to previous grammar"
                },
                "selection_rationale": {
                    "type": "string",
                    "default": "",
                    "description": "Why this strategy was selected"
                }
            },
            "required": ["grammar_point", "systematic_explanation", "usage_rules", "examples", "l1_interference_notes", "common_mistakes"],
            "additionalProperties": False
        }
    
    async def _generate_grammar_with_structured_output(
        self, 
        contextual_messages: List[Any],
        request: GrammarRequest,
        grammar_point: str
    ) -> GrammarContent:
        """Gerar conteúdo gramatical usando LangChain 0.3 structured output."""
        try:
            logger.info("🤖 Gerando conteúdo gramatical com structured output...")
            
            # Usar LangChain 0.3 with_structured_output para forçar formato correto
            grammar_schema = self._create_grammar_schema()
            structured_llm = self.llm.with_structured_output(grammar_schema)
            
            # Gerar usando structured output
            grammar_data = await structured_llm.ainvoke(contextual_messages)
            
            # Validar que retornou dict
            if not isinstance(grammar_data, dict):
                logger.warning("⚠️ Structured output não retornou dict, convertendo...")
                grammar_data = dict(grammar_data) if hasattr(grammar_data, '__dict__') else {}
            
            # Garantir campos obrigatórios com fallbacks seguros
            grammar_data = self._ensure_grammar_required_fields(grammar_data, grammar_point, request)
            
            # Validar estrutura dos dados
            grammar_data = self._clean_grammar_data(grammar_data)
            
            # Determinar estratégia baseada no request
            strategy = GrammarStrategy.EXPLICACAO_SISTEMATICA
            if request.strategy == "l1_prevention":
                strategy = GrammarStrategy.PREVENCAO_ERROS_L1
            
            # Criar objeto GrammarContent
            grammar_content = GrammarContent(
                strategy=strategy,
                grammar_point=grammar_data["grammar_point"],
                systematic_explanation=grammar_data["systematic_explanation"],
                usage_rules=grammar_data["usage_rules"],
                examples=grammar_data["examples"],
                l1_interference_notes=grammar_data["l1_interference_notes"],
                common_mistakes=grammar_data["common_mistakes"],
                vocabulary_integration=grammar_data.get("vocabulary_integration", []),
                previous_grammar_connections=grammar_data.get("previous_grammar_connections", []),
                selection_rationale=grammar_data.get("selection_rationale", "")
            )
            
            logger.info(
                f"✅ LLM retornou conteúdo gramatical estruturado: "
                f"{len(grammar_data.get('usage_rules', []))} regras, "
                f"{len(grammar_data.get('examples', []))} exemplos, "
                f"{len(grammar_data.get('common_mistakes', []))} erros comuns"
            )
            return grammar_content
            
        except Exception as e:
            logger.error(f"❌ Erro na geração com structured output: {str(e)}")
            logger.info("🔄 Tentando fallback sem structured output...")
            return await self._generate_grammar_fallback(contextual_messages, request, grammar_point)
    
    def _ensure_grammar_required_fields(
        self, 
        grammar_data: Dict[str, Any], 
        grammar_point: str, 
        request: GrammarRequest
    ) -> Dict[str, Any]:
        """Garantir campos obrigatórios no conteúdo gramatical."""
        # Garantir campo principal
        if "grammar_point" not in grammar_data:
            grammar_data["grammar_point"] = grammar_point
        
        # Garantir explicação
        if "systematic_explanation" not in grammar_data:
            grammar_data["systematic_explanation"] = f"Explicação sistemática de {grammar_point}"
        
        # Garantir listas obrigatórias
        required_lists = {
            "usage_rules": [f"Regra principal de {grammar_point}", "Aplicação em contexto específico"],
            "examples": [f"Example using {grammar_point}", "Practical application example", "Contextual usage example"],
            "l1_interference_notes": [f"Possível interferência L1 em {grammar_point}"],
            "common_mistakes": [
                {"mistake": f"Common error with {grammar_point}", "correction": "Correct form", "explanation": "Why this is incorrect"}
            ]
        }
        
        for field, default_value in required_lists.items():
            if field not in grammar_data or not isinstance(grammar_data[field], list):
                grammar_data[field] = default_value
        
        # Garantir campos opcionais
        optional_fields = {
            "vocabulary_integration": [],
            "previous_grammar_connections": [],
            "selection_rationale": f"Estratégia {request.strategy} selecionada para {grammar_point}"
        }
        
        for field, default_value in optional_fields.items():
            if field not in grammar_data:
                grammar_data[field] = default_value
        
        return grammar_data
    
    def _clean_grammar_data(self, grammar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpar e validar estrutura dos dados gramaticais."""
        # Limpar arrays de strings
        string_arrays = ["usage_rules", "examples", "l1_interference_notes", "vocabulary_integration", "previous_grammar_connections"]
        
        for field in string_arrays:
            if field in grammar_data:
                grammar_data[field] = self._ensure_string_list(grammar_data[field])
        
        # Validar e limpar common_mistakes
        if "common_mistakes" in grammar_data and isinstance(grammar_data["common_mistakes"], list):
            cleaned_mistakes = []
            for mistake in grammar_data["common_mistakes"]:
                if isinstance(mistake, dict):
                    cleaned_mistake = {
                        "mistake": str(mistake.get("mistake", "Common error")).strip(),
                        "correction": str(mistake.get("correction", "Correct form")).strip(),
                        "explanation": str(mistake.get("explanation", "Explanation of error")).strip()
                    }
                    cleaned_mistakes.append(cleaned_mistake)
            grammar_data["common_mistakes"] = cleaned_mistakes
        
        return grammar_data
    
    def _ensure_string_list(self, value: Any) -> List[str]:
        """Garantir que valor seja lista de strings válidas."""
        if not isinstance(value, list):
            return []
        
        result = []
        for item in value:
            if item and str(item).strip():
                result.append(str(item).strip())
        
        return result
    
    async def _generate_grammar_fallback(
        self, 
        contextual_messages: List[Any],
        request: GrammarRequest,
        grammar_point: str
    ) -> GrammarContent:
        """Fallback para geração sem structured output quando structured falha."""
        try:
            logger.info("🔄 Tentando geração fallback sem structured output...")
            
            # Gerar usando LangChain tradicional
            response = await self.llm.ainvoke(contextual_messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Usar parser IA original como fallback
            grammar_content = await self._parse_grammar_response_ai(
                content=content,
                request=request,
                grammar_point=grammar_point
            )
            
            logger.info(f"✅ Fallback gerou conteúdo gramatical para {grammar_point}")
            return grammar_content
                
        except Exception as e:
            logger.error(f"❌ Erro no fallback: {str(e)}")
            # Criar conteúdo mínimo de emergência
            return self._create_minimal_grammar_content(grammar_point, request)
    
    def _create_minimal_grammar_content(self, grammar_point: str, request: GrammarRequest) -> GrammarContent:
        """Criar conteúdo gramatical mínimo de emergência."""
        strategy = GrammarStrategy.EXPLICACAO_SISTEMATICA
        if request.strategy == "l1_prevention":
            strategy = GrammarStrategy.PREVENCAO_ERROS_L1
        
        return GrammarContent(
            strategy=strategy,
            grammar_point=grammar_point,
            systematic_explanation=f"Explicação básica de {grammar_point}",
            usage_rules=[f"Regra principal de {grammar_point}", "Aplicação em contexto"],
            examples=[f"Example with {grammar_point}", "Practical usage example"],
            l1_interference_notes=[f"Possível interferência L1 com {grammar_point}"],
            common_mistakes=[{
                "mistake": f"Common error with {grammar_point}",
                "correction": "Correct form",
                "explanation": "Explanation of the error"
            }],
            vocabulary_integration=[],
            previous_grammar_connections=[],
            selection_rationale=f"Estratégia {request.strategy} aplicada"
        )

    # =============================================================================
    # ANÁLISES VIA IA (SUBSTITUEM PROMPTS HARD-CODED)
    # =============================================================================

    async def _identify_grammar_point_ai(
        self, 
        text: str, 
        vocabulary: List[str], 
        context: str, 
        level: str
    ) -> str:
        """Identificar ponto gramatical principal via análise IA."""
        
        system_prompt = """Você é um especialista em análise gramatical contextual.
        
        Identifique o ponto gramatical mais relevante e produtivo considerando o texto, vocabulário e contexto específicos."""
        
        human_prompt = f"""Identifique o ponto gramatical principal:
        
        TEXTO: {text}
        VOCABULÁRIO: {', '.join(vocabulary[:10])}
        CONTEXTO DA UNIDADE: {context}
        NÍVEL CEFR: {level}
        
        Analise e determine qual ponto gramatical seria mais relevante e pedagogicamente produtivo para esta situação específica.
        
        Considere:
        - Estruturas presentes no texto
        - Vocabulário disponível para exemplos
        - Adequação ao nível {level}
        - Relevância para o contexto "{context}"
        
        Retorne APENAS o nome do ponto gramatical (ex: "Present Perfect", "Modal Verbs", "Conditional Sentences")."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            grammar_point = response.content.strip()
            
            # Validação básica
            if len(grammar_point) > 100:
                grammar_point = grammar_point[:100]
            
            return grammar_point if grammar_point else "Grammar Structures"
            
        except Exception as e:
            logger.warning(f"Erro na identificação gramatical via IA: {str(e)}")
            return "Grammar Structures"

    async def _generate_contextual_prompt_ai(
        self, 
        request: GrammarRequest, 
        grammar_point: str
    ) -> List[Any]:
        """Gerar prompt contextual específico via IA baseado na estratégia."""
        
        # Determinar tipo de estratégia
        if request.strategy == "l1_prevention":
            return await self._generate_l1_prevention_prompt(request, grammar_point)
        else:
            return await self._generate_systematic_prompt(request, grammar_point)

    async def _generate_systematic_prompt(
        self, 
        request: GrammarRequest, 
        grammar_point: str
    ) -> List[Any]:
        """Gerar prompt para GRAMMAR 1: Explicação Sistemática."""
        
        # ANÁLISE VIA IA: Abordagem sistemática específica
        systematic_approach = await self._analyze_systematic_approach_ai(
            grammar_point=grammar_point,
            level=request.level,
            context=request.unit_context,
            vocabulary=request.vocabulary_list
        )
        
        system_prompt = f"""Você é um especialista em ensino sistemático de gramática inglesa.
        
        Sua tarefa é criar explicação sistemática e estruturada do ponto gramatical, adaptada ao contexto específico.
        
        ESTRATÉGIA: GRAMMAR 1 - Explicação Sistemática
        ABORDAGEM CONTEXTUAL: {systematic_approach}"""
        
        human_prompt = f"""Crie explicação sistemática para:
        
        PONTO GRAMATICAL: {grammar_point}
        TEXTO BASE: {request.input_text}
        VOCABULÁRIO: {', '.join(request.vocabulary_list[:10])}
        NÍVEL: {request.level}
        CONTEXTO: {request.unit_context}
        VARIANTE: {request.variant}
        
        FORMATO ESTRUTURADO:
        1. EXPLICAÇÃO CLARA: Regra gramatical adaptada ao nível {request.level}
        2. ESTRUTURA/PADRÃO: Como formar e usar
        3. EXEMPLOS CONTEXTUAIS: 4-5 exemplos usando o vocabulário disponível
        4. PADRÕES DE USO: Quando e como aplicar
        5. NOTAS VARIANTE: Diferenças {request.variant} se relevante
        
        Mantenha foco pedagógico sistemático e use vocabulário disponível nos exemplos."""
        
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

    async def _generate_l1_prevention_prompt(
        self, 
        request: GrammarRequest, 
        grammar_point: str
    ) -> List[Any]:
        """Gerar prompt para GRAMMAR 2: Prevenção L1→L2."""
        
        # ANÁLISE VIA IA: Padrões de interferência L1
        l1_analysis = await self._analyze_l1_interference_ai(
            grammar_point=grammar_point,
            context=request.unit_context,
            vocabulary=request.vocabulary_list,
            level=request.level
        )
        
        system_prompt = f"""Você é um especialista em interferência linguística português→inglês.
        
        Sua tarefa é focar na prevenção de erros específicos que brasileiros cometem com este ponto gramatical.
        
        ESTRATÉGIA: GRAMMAR 2 - Prevenção de Erros L1→L2
        ANÁLISE L1: {l1_analysis}"""
        
        human_prompt = f"""Crie conteúdo focado em prevenção L1→L2:
        
        PONTO GRAMATICAL: {grammar_point}
        TEXTO BASE: {request.input_text}
        VOCABULÁRIO: {', '.join(request.vocabulary_list[:10])}
        NÍVEL: {request.level}
        CONTEXTO: {request.unit_context}
        
        FOCO EM INTERFERÊNCIA PORTUGUÊS→INGLÊS:
        1. ERRO COMUM: Principal erro que brasileiros cometem
        2. PADRÃO PORTUGUÊS: Como seria em português
        3. FORMA INCORRETA: Como brasileiros falam/escrevem erroneamente
        4. FORMA CORRETA: Como deve ser em inglês
        5. EXEMPLOS CONTRASTIVOS: Português vs Inglês correto
        6. ESTRATÉGIAS DE PREVENÇÃO: Como evitar o erro
        
        Use vocabulário disponível e contexto "{request.unit_context}" nos exemplos."""
        
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

    async def _analyze_systematic_approach_ai(
        self, 
        grammar_point: str, 
        level: str, 
        context: str, 
        vocabulary: List[str]
    ) -> str:
        """Análise via IA da melhor abordagem sistemática."""
        
        system_prompt = """Você é um especialista em metodologia de ensino de gramática.
        
        Determine a melhor abordagem sistemática para ensinar este ponto gramatical considerando o contexto específico."""
        
        human_prompt = f"""Determine abordagem sistemática para:
        
        PONTO GRAMATICAL: {grammar_point}
        NÍVEL: {level}
        CONTEXTO: {context}
        VOCABULÁRIO DISPONÍVEL: {', '.join(vocabulary[:8])}
        
        Recomende a abordagem pedagógica mais eficaz:
        - Sequência de apresentação
        - Foco principal para este nível
        - Como usar o vocabulário disponível
        - Progressão lógica de conceitos
        
        Retorne estratégia sistemática específica para este contexto."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.warning(f"Erro na análise sistemática via IA: {str(e)}")
            return f"Abordagem sistemática adaptada para {level} no contexto {context}"

    async def _analyze_l1_interference_ai(
        self, 
        grammar_point: str, 
        context: str, 
        vocabulary: List[str], 
        level: str
    ) -> str:
        """Análise via IA de padrões de interferência L1 (português→inglês)."""
        
        system_prompt = """Você é um especialista em interferência linguística português-inglês.
        
        Analise os principais erros que brasileiros cometem com este ponto gramatical específico."""
        
        human_prompt = f"""Analise interferência L1→L2 para:
        
        PONTO GRAMATICAL: {grammar_point}
        CONTEXTO: {context}
        VOCABULÁRIO: {', '.join(vocabulary[:8])}
        NÍVEL: {level}
        
        Identifique:
        - Principal erro que brasileiros cometem com {grammar_point}
        - Por que este erro acontece (influência do português)
        - Padrões específicos de interferência neste contexto
        - Exemplos típicos de erro português→inglês
        
        Foque nos erros mais comuns para {level} no contexto "{context}".
        
        Retorne análise específica de interferência L1."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.warning(f"Erro na análise L1 via IA: {str(e)}")
            return f"Análise de interferência L1 para {grammar_point} no contexto {context}"

    async def _parse_grammar_response_ai(
        self, 
        content: str, 
        request: GrammarRequest,
        grammar_point: str
    ) -> GrammarContent:
        """Parser inteligente via IA para estruturar resposta."""
        
        system_prompt = """Você é um especialista em estruturação de conteúdo educacional.
        
        Extraia e organize as informações da resposta em categorias estruturadas."""
        
        human_prompt = f"""Estruture este conteúdo gramatical:
        
        CONTEÚDO: {content}
        ESTRATÉGIA: {request.strategy}
        PONTO GRAMATICAL: {grammar_point}
        
        Extraia e organize em formato JSON:
        {{
            "explanation": "explicação principal clara",
            "examples": ["exemplo 1", "exemplo 2", "exemplo 3"],
            "patterns": ["padrão 1", "padrão 2"],
            "variant_notes": "notas sobre variante se houver",
            "l1_focus": "aspectos de interferência L1 se aplicável"
        }}
        
        Mantenha foco na estratégia {request.strategy}."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Tentar parsear JSON
            try:
                if "```json" in response.content:
                    json_content = response.content.split("```json")[1].split("```")[0].strip()
                else:
                    json_content = response.content
                
                parsed_data = json.loads(json_content)
                
                # Determinar estratégia
                strategy = GrammarStrategy.EXPLICACAO_SISTEMATICA
                if request.strategy == "l1_prevention":
                    strategy = GrammarStrategy.PREVENCAO_ERROS_L1
                
                return GrammarContent(
                    strategy=strategy,
                    grammar_point=grammar_point,
                    systematic_explanation=parsed_data.get("explanation", "Explicação via IA"),
                    usage_rules=parsed_data.get("patterns", [f"Regra principal de {grammar_point}"]),
                    examples=parsed_data.get("examples", [f"Example with {grammar_point}"]),
                    l1_interference_notes=[parsed_data.get("l1_focus", f"Possível interferência L1 com {grammar_point}")],
                    common_mistakes=[{
                        "mistake": f"Common error with {grammar_point}",
                        "correction": "Correct form",
                        "explanation": "Explanation of error"
                    }],
                    vocabulary_integration=[],
                    previous_grammar_connections=[],
                    selection_rationale=f"Estratégia {request.strategy} via fallback"
                )
                
            except (json.JSONDecodeError, KeyError):
                logger.warning("Erro no parsing JSON, usando parser técnico fallback")
                return self._technical_parser_fallback(content, request, grammar_point)
                
        except Exception as e:
            logger.warning(f"Erro no parser IA: {str(e)}")
            return self._technical_parser_fallback(content, request, grammar_point)

    # =============================================================================
    # PARSER TÉCNICO (MANTIDO - UTILITÁRIO TÉCNICO)
    # =============================================================================

    def _technical_parser_fallback(
        self, 
        content: str, 
        request: GrammarRequest, 
        grammar_point: str
    ) -> GrammarContent:
        """Parser técnico fallback quando IA parsing falha."""
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Inicializar campos
        explanation = ""
        examples = []
        patterns = []
        variant_notes = None
        l1_interference_focus = None
        
        current_section = None
        
        # Parsing contextual técnico
        for line in lines:
            line_lower = line.lower()
            
            # Detectar seções por palavras-chave técnicas
            if any(kw in line_lower for kw in ["explicação", "explanation", "regra"]):
                current_section = "explanation"
                if ":" in line:
                    explanation += line.split(":", 1)[-1].strip() + " "
                    
            elif any(kw in line_lower for kw in ["exemplos", "examples"]):
                current_section = "examples"
                
            elif any(kw in line_lower for kw in ["padrões", "patterns", "uso"]):
                current_section = "patterns"
                
            elif any(kw in line_lower for kw in ["variante", "variant", "diferenças"]):
                current_section = "variant"
                
            elif any(kw in line_lower for kw in ["erro", "interferência", "l1", "português"]):
                current_section = "l1"
                
            else:
                # Adicionar conteúdo à seção atual (lógica técnica)
                if current_section == "explanation":
                    explanation += line + " "
                elif current_section == "examples":
                    if line.startswith(("•", "-", "1.", "2.", "3.", "*")) or len(line) > 20:
                        examples.append(line.lstrip("•-123456789.*• "))
                elif current_section == "patterns":
                    if line.startswith(("•", "-", "1.", "2.", "3.", "*")):
                        patterns.append(line.lstrip("•-123456789.*• "))
                elif current_section == "variant":
                    variant_notes = (variant_notes or "") + line + " "
                elif current_section == "l1":
                    l1_interference_focus = {"focus": line}
        
        # Fallbacks técnicos
        if not explanation:
            explanation = content[:300].strip()
        if not examples:
            sentences = [s.strip() for s in content.replace('\n', ' ').split('.') 
                        if 15 < len(s.strip()) < 100]
            examples = sentences[:3] if sentences else ["Exemplo contextual"]
        if not patterns:
            patterns = ["Padrão gramatical identificado"]
        
        # Determinar estratégia
        strategy = GrammarStrategy.EXPLICACAO_SISTEMATICA
        if request.strategy == "l1_prevention":
            strategy = GrammarStrategy.PREVENCAO_ERROS_L1
        
        return GrammarContent(
            strategy=strategy,
            grammar_point=grammar_point,
            systematic_explanation=explanation.strip(),
            usage_rules=patterns[:3] if patterns else [f"Regra principal de {grammar_point}"],
            examples=examples[:5] if examples else [f"Example with {grammar_point}"],
            l1_interference_notes=[l1_interference_focus.get("focus", f"Interferência L1 com {grammar_point}") if l1_interference_focus else f"Interferência L1 com {grammar_point}"],
            common_mistakes=[{
                "mistake": f"Common error with {grammar_point}",
                "correction": "Correct form", 
                "explanation": "Technical fallback error"
            }],
            vocabulary_integration=[],
            previous_grammar_connections=[],
            selection_rationale=f"Estratégia {request.strategy} via parser técnico"
        )

    # =============================================================================
    # UTILITÁRIOS TÉCNICOS (MANTIDOS)
    # =============================================================================

    def format_for_output(self, grammar_content: GrammarContent) -> Dict[str, Any]:
        """Formatar para saída estruturada (utilitário técnico)."""
        return {
            "type": "grammar",
            "grammar_point": grammar_content.grammar_point,
            "explanation": grammar_content.systematic_explanation,
            "examples": grammar_content.examples,
            "usage_rules": grammar_content.usage_rules,
            "strategy": str(grammar_content.strategy),
            "l1_interference_notes": grammar_content.l1_interference_notes,
            "metadata": {
                "generated_at": "timestamp",
                "section": "grammar",
                "langchain_version": "0.3.x",
                "pydantic_version": "2.x",
                "ai_contextual": True
            }
        }

    async def get_service_status(self) -> Dict[str, Any]:
        """Status do serviço (utilitário técnico)."""
        return {
            "service": "GrammarGenerator",
            "status": "active",
            "strategies": list(GRAMMAR_STRATEGIES.values()),
            "ai_integration": "100% contextual analysis",
            "langchain_version": "0.3.x",
            "supported_levels": CEFR_LEVELS,
            "supported_variants": LANGUAGE_VARIANTS,
            "ai_methods": [
                "_identify_grammar_point_ai",
                "_analyze_systematic_approach_ai",
                "_analyze_l1_interference_ai", 
                "_parse_grammar_response_ai"
            ]
        }


# 🚀 Função utilitária moderna (MANTIDA - INTERFACE TÉCNICA)
async def generate_grammar(
    text: str, 
    vocabulary: List[str], 
    level: str = "B1", 
    variant: str = "american",
    unit_context: str = "",
    strategy: str = "systematic"
) -> Dict[str, Any]:
    """
    Função simplificada para gerar gramática com LangChain 0.3 + IA contextual.
    
    Args:
        text: Texto base
        vocabulary: Lista de vocabulário
        level: Nível CEFR
        variant: Variante do inglês
        unit_context: Contexto específico da unidade
        strategy: "systematic" ou "l1_prevention"
        
    Returns:
        Dict: Conteúdo gramatical formatado
    """
    generator = GrammarGenerator()
    
    # Pydantic 2 - validação automática
    request = GrammarRequest(
        input_text=text,
        vocabulary_list=vocabulary,
        level=level,
        variant=variant,
        unit_context=unit_context,
        strategy=strategy
    )
    
    grammar_content = await generator.generate_grammar_content(request)
    return generator.format_for_output(grammar_content)

# =============================================================================
# GRAMMAR GENERATOR SERVICE - CLASSE FALTANTE
# =============================================================================

class GrammarGeneratorService:
    """
    Service wrapper para GrammarGenerator - compatibilidade com sistema IVO V2.
    Esta classe fornece interface compatível esperada pelo sistema.
    """
    
    def __init__(self):
        """Inicializar service com generator interno."""
        self.generator = GrammarGenerator()
        logger.info("✅ GrammarGeneratorService inicializado")
    
    async def generate_grammar_content(
        self, 
        request: GrammarRequest
    ) -> GrammarContent:
        """
        Interface principal para geração de gramática.
        
        Args:
            request: Dados da requisição validados pelo Pydantic 2
            
        Returns:
            GrammarContent: Conteúdo estruturado por estratégia
        """
        return await self.generator.generate_grammar_content(request)
    
    async def generate_grammar_for_unit(
        self,
        unit_data: Dict[str, Any],
        vocabulary_items: List[str],
        context: str = "",
        strategy: str = "systematic"
    ) -> GrammarContent:
        """
        Gerar gramática para uma unidade específica.
        Interface compatível com sistema hierárquico IVO V2.
        
        Args:
            unit_data: Dados da unidade
            vocabulary_items: Vocabulário da unidade
            context: Contexto da unidade
            strategy: Estratégia gramatical
            
        Returns:
            GrammarContent: Objeto Pydantic com conteúdo gramatical para unidade
        """
        try:
            # Extrair informações da unidade
            level = unit_data.get("cefr_level", "B1")
            variant = unit_data.get("language_variant", "american_english").replace("_english", "")
            unit_context = context or unit_data.get("context", "")
            
            # Texto base da unidade
            text_sources = []
            if unit_data.get("main_aim"):
                text_sources.append(unit_data["main_aim"])
            if unit_data.get("subsidiary_aims"):
                text_sources.extend(unit_data["subsidiary_aims"])
            if unit_context:
                text_sources.append(unit_context)
            
            input_text = ". ".join(text_sources) or "Grammar practice with available vocabulary."
            
            # Criar request
            request = GrammarRequest(
                input_text=input_text,
                vocabulary_list=vocabulary_items,
                level=level,
                variant=variant,
                unit_context=unit_context,
                strategy=strategy
            )
            
            # Gerar conteúdo
            grammar_content = await self.generator.generate_grammar_content(request)
            
            # Adicionar metadados diretamente no objeto (se necessário)
            # Os metadados de unidade podem ser adicionados depois na API
            
            logger.info(f"✅ Gramática gerada para unidade: {grammar_content.grammar_point}")
            return grammar_content
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de gramática para unidade: {str(e)}")
            raise
    
    def get_available_strategies(self) -> List[str]:
        """Retornar estratégias disponíveis."""
        return list(GRAMMAR_STRATEGIES.keys())
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Status do service."""
        generator_status = await self.generator.get_service_status()
        return {
            **generator_status,
            "service_name": "GrammarGeneratorService",
            "wrapper_status": "active",
            "ivo_v2_compatible": True
        }
    
    async def validate_grammar_request(self, request_data: Dict[str, Any]) -> bool:
        """Validar dados de requisição."""
        try:
            GrammarRequest(**request_data)
            return True
        except ValidationError:
            return False


# =============================================================================
# INSTÂNCIA GLOBAL PARA COMPATIBILIDADE
# =============================================================================

# Instância global que será importada pelo sistema
grammar_service = GrammarGeneratorService()


# =============================================================================
# FUNÇÃO DE CONVENIÊNCIA PARA INTEGRAÇÃO
# =============================================================================

async def create_grammar_for_unit(
    unit_data: Dict[str, Any],
    vocabulary_items: List[str] = None,
    context: str = "",
    strategy: str = "systematic"
) -> Dict[str, Any]:
    """
    Função de conveniência para integração com sistema IVO V2.
    
    Args:
        unit_data: Dados completos da unidade
        vocabulary_items: Lista de vocabulário (opcional)
        context: Contexto adicional
        strategy: "systematic" ou "l1_prevention"
        
    Returns:
        Dict: Conteúdo gramatical pronto para uso
    """
    service = GrammarGeneratorService()
    
    # Usar vocabulário da unidade se não fornecido
    if vocabulary_items is None:
        vocabulary_section = unit_data.get("vocabulary", {})
        if isinstance(vocabulary_section, dict):
            items = vocabulary_section.get("items", [])
            vocabulary_items = [item.get("word", "") for item in items if isinstance(item, dict)]
        else:
            vocabulary_items = []
    
    return await service.generate_grammar_for_unit(
        unit_data=unit_data,
        vocabulary_items=vocabulary_items,
        context=context,
        strategy=strategy
    )

# Exemplo e teste para LangChain 0.3 + IA Contextual
if __name__ == "__main__":
    async def test_langchain_v03_ai():
        """Testar LangChain 0.3 + IA contextual."""
        try:
            print("🧪 Testando LangChain 0.3 + IA Contextual...")
            
            # Testar GRAMMAR 1: Sistemática
            result1 = await generate_grammar(
                text="The students have been learning English for two years.",
                vocabulary=["learn", "student", "year", "English", "study"],
                level="B2",
                variant="american",
                unit_context="academic environment",
                strategy="systematic"
            )
            
            print("🎯 GRAMMAR 1 (Sistemática):")
            print(f"   Ponto: {result1['grammar_point']}")
            print(f"   Estratégia: {result1['strategy_type']}")
            
            # Testar GRAMMAR 2: L1 Prevention
            result2 = await generate_grammar(
                text="I am working here since 2020.",
                vocabulary=["work", "since", "here", "year"],
                level="A2", 
                variant="american",
                unit_context="workplace",
                strategy="l1_prevention"
            )
            
            print("🎯 GRAMMAR 2 (L1 Prevention):")
            print(f"   Ponto: {result2['grammar_point']}")
            print(f"   Estratégia: {result2['strategy_type']}")
            print(f"   L1 Focus: {result2['l1_interference_focus']}")
            
            print("🎉 LangChain 0.3 + IA Contextual funcionando!")
            
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
    
    # Executar teste
    asyncio.run(test_langchain_v03_ai())