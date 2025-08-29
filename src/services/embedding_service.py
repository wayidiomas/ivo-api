# src/services/embedding_service.py
"""
Serviço para geração e gerenciamento de embeddings de conteúdo de unidades.
Integração com OpenAI embeddings e armazenamento vetorial.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from openai import AsyncOpenAI
from config.database import get_supabase_client
from config.models import get_openai_config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Serviço para geração e gerenciamento de embeddings vetoriais."""
    
    def __init__(self):
        """Inicializar serviço de embeddings."""
        self.supabase = get_supabase_client()
        openai_config = get_openai_config()
        self.openai_client = AsyncOpenAI(api_key=openai_config["api_key"])
        self.embedding_model = "text-embedding-3-small"  # Modelo eficiente e econômico
        self.embedding_dimensions = 1536  # Dimensões do text-embedding-3-small
        
        logger.info(f"✅ EmbeddingService inicializado com modelo {self.embedding_model}")
    
    async def generate_content_embedding(self, content: str) -> List[float]:
        """Gerar embedding para conteúdo usando OpenAI."""
        try:
            # Limitar tamanho do texto (max ~8000 tokens para text-embedding-3-small)
            if len(content) > 30000:  # ~8000 tokens aproximadamente
                content = content[:30000] + "..."
                logger.warning("Conteúdo truncado para embedding devido ao tamanho")
            
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=content,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"📊 Embedding gerado: {len(embedding)} dimensões")
            
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar embedding: {str(e)}")
            raise
    
    async def upsert_unit_content_embedding(
        self,
        course_id: str,
        book_id: str, 
        unit_id: str,
        sequence_order: int,
        content_type: str,
        content_data: Dict[str, Any]
    ) -> bool:
        """
        Fazer upsert de embedding para conteúdo de unidade.
        
        Args:
            course_id: ID do curso
            book_id: ID do livro
            unit_id: ID da unidade
            sequence_order: Ordem sequencial da unidade
            content_type: Tipo do conteúdo ('vocabulary', 'sentences', 'tips', 'grammar', 'qa', 'assessments')
            content_data: Dados do conteúdo para gerar embedding
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            # Validar content_type
            valid_types = ['vocabulary', 'sentences', 'tips', 'grammar', 'qa', 'assessments']
            if content_type not in valid_types:
                raise ValueError(f"content_type deve ser um de: {valid_types}")
            
            # Extrair texto do conteúdo para embedding
            content_text = self._extract_text_from_content(content_data, content_type)
            
            if not content_text.strip():
                logger.warning(f"⚠️ Conteúdo vazio para {content_type}, pulando embedding")
                return True
            
            # Gerar embedding
            embedding = await self.generate_content_embedding(content_text)
            
            # Preparar metadados
            metadata = {
                "content_type": content_type,
                "generated_at": datetime.utcnow().isoformat(),
                "text_length": len(content_text),
                "embedding_model": self.embedding_model,
                "content_summary": content_text[:200] + "..." if len(content_text) > 200 else content_text
            }
            
            # Dados para upsert
            upsert_data = {
                "course_id": course_id,
                "book_id": book_id,
                "unit_id": unit_id,
                "sequence_order": sequence_order,
                "content_type": content_type,
                "content": content_text,
                "embedding": embedding,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Fazer upsert (on_conflict para course_id + book_id + unit_id + content_type)
            result = self.supabase.table("ivo_unit_embeddings").upsert(
                upsert_data,
                on_conflict="course_id,book_id,unit_id,content_type"
            ).execute()
            
            if result.data:
                logger.info(f"✅ Embedding upsert para {content_type} da unidade {unit_id}: sucesso")
                return True
            else:
                logger.error(f"❌ Falha no upsert de embedding para {content_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no upsert de embedding: {str(e)}")
            return False
    
    def _extract_text_from_content(self, content_data: Dict[str, Any], content_type: str) -> str:
        """
        Extrair texto relevante do conteúdo para geração de embedding.
        
        Args:
            content_data: Dados do conteúdo
            content_type: Tipo do conteúdo
            
        Returns:
            str: Texto extraído para embedding
        """
        text_parts = []
        
        try:
            if content_type == "vocabulary":
                # Para vocabulário: extrair palavras, definições e exemplos
                if "items" in content_data:
                    for item in content_data["items"]:
                        if isinstance(item, dict):
                            word = item.get("word", "")
                            definition = item.get("definition", "")
                            example = item.get("example", "")
                            text_parts.append(f"{word}: {definition}. Example: {example}")
                        
            elif content_type == "sentences":
                # Para sentences: extrair texto das sentenças
                if "sentences" in content_data:
                    for sentence in content_data["sentences"]:
                        if isinstance(sentence, dict):
                            text = sentence.get("text", "")
                            if text:
                                text_parts.append(text)
                        elif isinstance(sentence, str):
                            text_parts.append(sentence)
                            
            elif content_type == "tips":
                # Para tips: extrair título, explicação e exemplos
                title = content_data.get("title", "")
                explanation = content_data.get("explanation", "")
                examples = content_data.get("examples", [])
                
                if title:
                    text_parts.append(f"Tips Strategy: {title}")
                if explanation:
                    text_parts.append(explanation)
                if examples:
                    text_parts.extend([str(ex) for ex in examples if ex])
                    
            elif content_type == "grammar":
                # Para grammar: ponto gramatical, explicação e exemplos
                grammar_point = content_data.get("grammar_point", "")
                explanation = content_data.get("systematic_explanation", "")
                examples = content_data.get("examples", [])
                
                if grammar_point:
                    text_parts.append(f"Grammar: {grammar_point}")
                if explanation:
                    text_parts.append(explanation)
                if examples:
                    text_parts.extend([str(ex) for ex in examples if ex])
                    
            elif content_type == "qa":
                # Para Q&A: perguntas e respostas
                questions = content_data.get("questions", [])
                answers = content_data.get("answers", [])
                
                for q in questions:
                    if q and isinstance(q, str):
                        text_parts.append(f"Q: {q}")
                        
                for a in answers:
                    if a and isinstance(a, str):
                        text_parts.append(f"A: {a}")
                        
            elif content_type == "assessments":
                # Para assessments: título, instruções e conteúdo
                if "activities" in content_data:
                    for activity in content_data["activities"]:
                        if isinstance(activity, dict):
                            title = activity.get("title", "")
                            instructions = activity.get("instructions", "")
                            
                            if title:
                                text_parts.append(f"Assessment: {title}")
                            if instructions:
                                text_parts.append(instructions)
            
            # Fallback: converter conteúdo completo para string
            if not text_parts:
                text_parts.append(str(content_data))
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao extrair texto de {content_type}: {str(e)}")
            text_parts.append(str(content_data))
        
        return " ".join(text_parts).strip()
    
    async def delete_unit_embeddings(self, unit_id: str) -> bool:
        """
        Deletar todos os embeddings de uma unidade.
        
        Args:
            unit_id: ID da unidade
            
        Returns:
            bool: True se sucesso
        """
        try:
            result = self.supabase.table("ivo_unit_embeddings").delete().eq("unit_id", unit_id).execute()
            
            if result.data is not None:  # Supabase retorna [] para delete bem-sucedido
                logger.info(f"✅ Embeddings da unidade {unit_id} deletados")
                return True
            else:
                logger.warning(f"⚠️ Nenhum embedding encontrado para unidade {unit_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao deletar embeddings da unidade {unit_id}: {str(e)}")
            return False
    
    async def bulk_upsert_unit_embeddings(
        self,
        course_id: str,
        book_id: str,
        unit_id: str,
        sequence_order: int,
        contents: Dict[str, Dict[str, Any]]
    ) -> Dict[str, bool]:
        """
        Fazer upsert em lote de múltiplos tipos de conteúdo de uma unidade.
        
        Args:
            course_id: ID do curso
            book_id: ID do livro
            unit_id: ID da unidade  
            sequence_order: Ordem sequencial
            contents: Dict com {content_type: content_data}
            
        Returns:
            Dict[str, bool]: Resultado de cada tipo de conteúdo
        """
        results = {}
        
        # Processar cada tipo de conteúdo concorrentemente
        tasks = []
        for content_type, content_data in contents.items():
            task = self.upsert_unit_content_embedding(
                course_id, book_id, unit_id, sequence_order, content_type, content_data
            )
            tasks.append((content_type, task))
        
        # Executar em paralelo com limite de concorrência
        semaphore = asyncio.Semaphore(3)  # Máximo 3 requests OpenAI paralelos
        
        async def bounded_task(content_type, task):
            async with semaphore:
                return content_type, await task
        
        bounded_tasks = [bounded_task(ct, task) for ct, task in tasks]
        completed_results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
        
        # Processar resultados
        for result in completed_results:
            if isinstance(result, Exception):
                logger.error(f"❌ Erro em bulk upsert: {str(result)}")
                continue
                
            content_type, success = result
            results[content_type] = success
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        logger.info(f"📊 Bulk upsert concluído: {successful}/{total} sucessos para unidade {unit_id}")
        
        return results


# Instância global do serviço
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Obter instância global do serviço de embeddings."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service