# src/services/hierarchical_database.py - ATUALIZADO COM PAGINAÇÃO
"""Serviço para operações de banco com hierarquia Course → Book → Unit e paginação."""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging

from config.database import get_supabase_client
from src.core.hierarchical_models import (
    Course, CourseCreateRequest, Book, BookCreateRequest,
    UnitWithHierarchy, HierarchicalUnitRequest, RAGVocabularyContext,
    RAGStrategyContext, RAGAssessmentContext, ProgressionAnalysis,
    HierarchyValidationResult
)
from src.core.pagination import (
    PaginationParams, SortParams, CourseFilterParams, BookFilterParams, 
    UnitFilterParams, QueryBuilder
)
from src.core.enums import UnitStatus, CEFRLevel
from src.services.embedding_service import get_embedding_service
from src.services.aim_detector import AimDetectorService


logger = logging.getLogger(__name__)


class HierarchicalDatabaseService:
    """Serviço para operações hierárquicas no banco de dados com paginação."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.embedding_service = get_embedding_service()
    
    # =============================================================================
    # COURSE OPERATIONS COM PAGINAÇÃO
    # =============================================================================
    
    async def create_course(self, course_data: CourseCreateRequest) -> Course:
        """Criar novo curso."""
        try:
            # Preparar dados para inserção
            insert_data = {
                "name": course_data.name,
                "description": course_data.description,
                "target_levels": [level.value for level in course_data.target_levels],
                "language_variant": course_data.language_variant.value,
                "methodology": course_data.methodology
            }
            
            # Inserir no banco
            result = self.supabase.table("ivo_courses").insert(insert_data).execute()
            
            if not result.data:
                raise Exception("Falha ao criar curso")
            
            # Retornar modelo Course
            course_record = result.data[0]
            return Course(**course_record)
            
        except Exception as e:
            logger.error(f"Erro ao criar curso: {str(e)}")
            raise
    
    async def get_course(self, course_id: str) -> Optional[Course]:
        """Buscar curso por ID."""
        try:
            result = self.supabase.table("ivo_courses").select("*").eq("id", course_id).execute()
            
            if not result.data:
                return None
                
            return Course(**result.data[0])
            
        except Exception as e:
            logger.error(f"Erro ao buscar curso {course_id}: {str(e)}")
            raise
    
    async def list_courses(self) -> List[Course]:
        """Listar todos os cursos (método original mantido para compatibilidade)."""
        try:
            result = self.supabase.table("ivo_courses").select("*").order("created_at", desc=True).execute()
            
            return [Course(**record) for record in result.data]
            
        except Exception as e:
            logger.error(f"Erro ao listar cursos: {str(e)}")
            raise
    
    async def list_courses_paginated(
        self,
        pagination: PaginationParams,
        sorting: SortParams,
        filters: Optional[CourseFilterParams] = None
    ) -> Tuple[List[Course], int]:
        """
        Listar cursos com paginação, ordenação e filtros.
        
        Returns:
            Tuple[List[Course], int]: (cursos_da_pagina, total_count)
        """
        try:
            # Construir query base
            query = self.supabase.table("ivo_courses").select("*", count="exact")
            count_query = self.supabase.table("ivo_courses").select("*", count="exact", head=True)
            
            # Aplicar filtros
            if filters:
                filter_dict = filters.to_dict()
                
                # Busca por texto
                if filter_dict.get('search'):
                    search_term = f"%{filter_dict['search']}%"
                    query = query.or_(f"name.ilike.{search_term},description.ilike.{search_term}")
                    count_query = count_query.or_(f"name.ilike.{search_term},description.ilike.{search_term}")
                
                # Filtros específicos
                if filter_dict.get('language_variant'):
                    query = query.eq("language_variant", filter_dict['language_variant'])
                    count_query = count_query.eq("language_variant", filter_dict['language_variant'])
                
                if filter_dict.get('target_level'):
                    query = query.contains("target_levels", [filter_dict['target_level']])
                    count_query = count_query.contains("target_levels", [filter_dict['target_level']])
                
                if filter_dict.get('methodology'):
                    query = query.contains("methodology", [filter_dict['methodology']])
                    count_query = count_query.contains("methodology", [filter_dict['methodology']])
                
                # Filtros de data
                if filter_dict.get('created_after'):
                    query = query.gte("created_at", filter_dict['created_after'])
                    count_query = count_query.gte("created_at", filter_dict['created_after'])
                
                if filter_dict.get('created_before'):
                    query = query.lte("created_at", filter_dict['created_before'])
                    count_query = count_query.lte("created_at", filter_dict['created_before'])
            
            # Obter contagem total
            count_result = count_query.execute()
            total_count = count_result.count
            
            # Aplicar ordenação
            allowed_sort_fields = ["name", "created_at", "updated_at"]
            sort_field = sorting.sort_by if sorting.sort_by in allowed_sort_fields else "created_at"
            
            query = query.order(sort_field, desc=sorting.is_descending)
            
            # Aplicar paginação
            query = query.range(pagination.offset, pagination.offset + pagination.size - 1)
            
            # Executar query
            result = query.execute()
            
            courses = [Course(**record) for record in result.data]
            
            logger.info(f"Cursos paginados: {len(courses)} de {total_count} total")
            
            return courses, total_count
            
        except Exception as e:
            logger.error(f"Erro ao listar cursos paginados: {str(e)}")
            raise
    
    async def update_course(self, course_id: str, course_data: CourseCreateRequest) -> Course:
        """Atualizar curso."""
        try:
            update_data = {
                "name": course_data.name,
                "description": course_data.description,
                "target_levels": [level.value for level in course_data.target_levels],
                "language_variant": course_data.language_variant.value,
                "methodology": course_data.methodology,
                "updated_at": "now()"
            }
            
            result = (
                self.supabase.table("ivo_courses")
                .update(update_data)
                .eq("id", course_id)
                .execute()
            )
            
            if not result.data:
                raise Exception("Falha ao atualizar curso")
            
            return Course(**result.data[0])
            
        except Exception as e:
            logger.error(f"Erro ao atualizar curso {course_id}: {str(e)}")
            raise
    
    async def delete_course(self, course_id: str) -> bool:
        """Deletar curso e todos os recursos relacionados."""
        try:
            # Em uma implementação real, isso seria uma transação
            # Por enquanto, simular deleção bem-sucedida
            
            # 1. Deletar units relacionadas
            self.supabase.table("ivo_units").delete().eq("course_id", course_id).execute()
            
            # 2. Deletar books relacionados
            self.supabase.table("ivo_books").delete().eq("course_id", course_id).execute()
            
            # 3. Deletar curso
            result = self.supabase.table("ivo_courses").delete().eq("id", course_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Erro ao deletar curso {course_id}: {str(e)}")
            raise
    
    # =============================================================================
    # BOOK OPERATIONS COM PAGINAÇÃO
    # =============================================================================
    
    async def create_book(self, course_id: str, book_data: BookCreateRequest) -> Book:
        """Criar novo book dentro de um curso."""
        try:
            # Verificar se o curso existe
            course = await self.get_course(course_id)
            if not course:
                raise ValueError(f"Curso {course_id} não encontrado")
            
            # Determinar próximo sequence_order
            next_sequence = await self._get_next_book_sequence(course_id)
            
            # Preparar dados para inserção
            insert_data = {
                "course_id": course_id,
                "name": book_data.name,
                "description": book_data.description,
                "target_level": book_data.target_level.value,
                "sequence_order": next_sequence
            }
            
            # Inserir no banco
            result = self.supabase.table("ivo_books").insert(insert_data).execute()
            
            if not result.data:
                raise Exception("Falha ao criar book")
            
            return Book(**result.data[0])
            
        except Exception as e:
            logger.error(f"Erro ao criar book: {str(e)}")
            raise
    
    async def get_book(self, book_id: str) -> Optional[Book]:
        """Buscar book por ID."""
        try:
            result = self.supabase.table("ivo_books").select("*").eq("id", book_id).execute()
            
            if not result.data:
                return None
                
            return Book(**result.data[0])
            
        except Exception as e:
            logger.error(f"Erro ao buscar book {book_id}: {str(e)}")
            raise
    
    async def list_books_by_course(self, course_id: str) -> List[Book]:
        """Listar books de um curso (método original mantido)."""
        try:
            result = (
                self.supabase.table("ivo_books")
                .select("*")
                .eq("course_id", course_id)
                .order("sequence_order")
                .execute()
            )
            
            return [Book(**record) for record in result.data]
            
        except Exception as e:
            logger.error(f"Erro ao listar books do curso {course_id}: {str(e)}")
            raise
    
    async def list_books_paginated(
        self,
        course_id: str,
        pagination: PaginationParams,
        sorting: SortParams,
        filters: Optional[BookFilterParams] = None
    ) -> Tuple[List[Book], int]:
        """Listar books com paginação."""
        try:
            # Query base
            query = (
                self.supabase.table("ivo_books")
                .select("*", count="exact")
                .eq("course_id", course_id)
            )
            count_query = (
                self.supabase.table("ivo_books")
                .select("*", count="exact", head=True)
                .eq("course_id", course_id)
            )
            
            # Aplicar filtros
            if filters:
                filter_dict = filters.to_dict()
                
                if filter_dict.get('search'):
                    search_term = f"%{filter_dict['search']}%"
                    query = query.or_(f"name.ilike.{search_term},description.ilike.{search_term}")
                    count_query = count_query.or_(f"name.ilike.{search_term},description.ilike.{search_term}")
                
                if filter_dict.get('target_level'):
                    query = query.eq("target_level", filter_dict['target_level'])
                    count_query = count_query.eq("target_level", filter_dict['target_level'])
            
            # Contagem total
            count_result = count_query.execute()
            total_count = count_result.count
            
            # Ordenação
            allowed_sort_fields = ["name", "target_level", "sequence_order", "created_at"]
            sort_field = sorting.sort_by if sorting.sort_by in allowed_sort_fields else "sequence_order"
            
            query = query.order(sort_field, desc=sorting.is_descending)
            
            # Paginação
            query = query.range(pagination.offset, pagination.offset + pagination.size - 1)
            
            # Executar
            result = query.execute()
            books = [Book(**record) for record in result.data]
            
            return books, total_count
            
        except Exception as e:
            logger.error(f"Erro ao listar books paginados: {str(e)}")
            raise

    async def list_all_books_paginated(
        self,
        pagination: PaginationParams,
        sorting: SortParams,
        filters: Optional[BookFilterParams] = None
    ) -> Tuple[List[dict], int]:
        """Listar TODOS os books (todos os cursos) com paginação."""
        try:
            # Query base - TODOS os books
            query = (
                self.supabase.table("ivo_books")
                .select("*, ivo_courses!inner(id, name, language_variant)", count="exact")
            )
            count_query = (
                self.supabase.table("ivo_books")
                .select("*", count="exact", head=True)
            )
            
            # Aplicar filtros
            if filters:
                filter_dict = filters.to_dict()
                
                # Busca por nome/descrição
                if filter_dict.get('search'):
                    search_term = f"%{filter_dict['search']}%"
                    query = query.or_(f"name.ilike.{search_term},description.ilike.{search_term}")
                    count_query = count_query.or_(f"name.ilike.{search_term},description.ilike.{search_term}")
                
                # Filtro por nível CEFR
                if filter_dict.get('target_level'):
                    query = query.eq("target_level", filter_dict['target_level'])
                    count_query = count_query.eq("target_level", filter_dict['target_level'])
                
                # Filtro por curso
                if filter_dict.get('course_id'):
                    query = query.eq("course_id", filter_dict['course_id'])
                    count_query = count_query.eq("course_id", filter_dict['course_id'])
                
                # Filtro por variante do idioma (via join com courses)
                if filter_dict.get('language_variant'):
                    query = query.eq("ivo_courses.language_variant", filter_dict['language_variant'])
                    count_query = count_query.eq("ivo_courses.language_variant", filter_dict['language_variant'])
            
            # Contar total
            count_result = count_query.execute()
            total_count = count_result.count if count_result.count else 0
            
            # Ordenação
            allowed_sort_fields = ["name", "created_at", "updated_at", "sequence_order", "target_level"]
            sort_field = sorting.sort_by if sorting.sort_by in allowed_sort_fields else "updated_at"
            
            query = query.order(sort_field, desc=sorting.is_descending)
            
            # Paginação
            query = query.range(pagination.offset, pagination.offset + pagination.size - 1)
            
            # Executar
            result = query.execute()
            
            # Transformar dados para incluir informações do curso
            books_data = []
            for record in result.data:
                # Calcular vocabulary count real agregando das units
                vocabulary_count = await self._calculate_real_vocabulary_count(record["id"])
                
                book_data = {
                    "id": record["id"],
                    "name": record["name"],
                    "description": record.get("description"),
                    "target_level": record["target_level"],
                    "sequence_order": record["sequence_order"],
                    "unit_count": record["unit_count"],
                    "vocabulary_count": vocabulary_count,  # NOVO CAMPO
                    "vocabulary_coverage": record.get("vocabulary_coverage", []),
                    "created_at": record["created_at"],
                    "updated_at": record["updated_at"],
                    "course_id": record["course_id"],
                    "course_name": record["ivo_courses"]["name"],
                    "course_language_variant": record["ivo_courses"]["language_variant"],
                    # Status simulável baseado em unit_count
                    "status": "completed" if record["unit_count"] > 0 else "draft"
                }
                books_data.append(book_data)
            
            return books_data, total_count
            
        except Exception as e:
            logger.error(f"Erro ao listar todos os books paginados: {str(e)}")
            raise

    async def _calculate_real_vocabulary_count(self, book_id: str) -> int:
        """Calcular contagem real de vocabulário agregando das units do book."""
        try:
            # Consultar todas as units do book e somar os itens de vocabulary
            result = self.supabase.table("ivo_units")\
                .select("vocabulary")\
                .eq("book_id", book_id)\
                .execute()
            
            total_vocabulary_count = 0
            
            for unit in result.data:
                vocabulary_data = unit.get("vocabulary")
                if vocabulary_data and isinstance(vocabulary_data, dict):
                    # Contar itens no vocabulary JSONB
                    vocabulary_items = vocabulary_data.get("items", [])
                    if isinstance(vocabulary_items, list):
                        total_vocabulary_count += len(vocabulary_items)
            
            return total_vocabulary_count
            
        except Exception as e:
            logger.warning(f"Erro ao calcular vocabulary count para book {book_id}: {str(e)}")
            return 0

    async def update_book(self, book_id: str, book_data: BookCreateRequest) -> Book:
        """Atualizar book existente."""
        try:
            # Verificar se book existe
            existing_book = await self.get_book(book_id)
            if not existing_book:
                raise ValueError(f"Book {book_id} não encontrado")
            
            # Preparar dados para atualização
            update_data = {
                "name": book_data.name,
                "description": book_data.description,
                "target_level": book_data.target_level.value,
                "updated_at": datetime.now().isoformat()
            }
            
            # Atualizar no banco
            result = self.supabase.table("ivo_books").update(update_data).eq("id", book_id).execute()
            
            if not result.data:
                raise Exception("Falha ao atualizar book")
            
            return Book(**result.data[0])
            
        except Exception as e:
            logger.error(f"Erro ao atualizar book {book_id}: {str(e)}")
            raise

    async def delete_book(self, book_id: str) -> bool:
        """Deletar book e todas as unidades relacionadas."""
        try:
            # 1. Deletar units relacionadas
            self.supabase.table("ivo_units").delete().eq("book_id", book_id).execute()
            
            # 2. Deletar book
            result = self.supabase.table("ivo_books").delete().eq("id", book_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Erro ao deletar book {book_id}: {str(e)}")
            raise
    
    # =============================================================================
    # UNIT OPERATIONS COM PAGINAÇÃO
    # =============================================================================
    
    async def create_unit(self, unit_data: HierarchicalUnitRequest) -> UnitWithHierarchy:
        """Criar unidade com validação hierárquica."""
        try:
            # Validar hierarquia
            validation = await self.validate_hierarchy(unit_data.course_id, unit_data.book_id)
            if not validation.is_valid:
                raise ValueError(f"Hierarquia inválida: {validation.errors}")
            
            # Determinar próximo sequence_order
            next_sequence = await self._get_next_unit_sequence(unit_data.book_id)
            
            # Preparar dados para inserção
            insert_data = {
                "course_id": unit_data.course_id,
                "book_id": unit_data.book_id,
                "sequence_order": next_sequence,
                "title": unit_data.title,
                "context": unit_data.context,
                "cefr_level": unit_data.cefr_level.value,
                "language_variant": unit_data.language_variant.value,
                "unit_type": unit_data.unit_type.value,
                "status": UnitStatus.CREATING.value
            }
            
            # Inserir no banco
            result = self.supabase.table("ivo_units").insert(insert_data).execute()
            
            if not result.data:
                raise Exception("Falha ao criar unidade")
            
            unit = UnitWithHierarchy(**result.data[0])
            
            # Gerar aims automaticamente após criação da unit
            try:
                await self._generate_and_save_unit_aims(unit, unit_data)
                logger.info(f"✅ Aims gerados para unit {unit.id}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao gerar aims para unit {unit.id}: {str(e)}")
                # Não falha a criação da unit se aims falharem
            
            # Recarregar unit com aims atualizados
            updated_unit = await self.get_unit(unit.id)
            return updated_unit if updated_unit else unit
            
        except Exception as e:
            logger.error(f"Erro ao criar unidade: {str(e)}")
            raise
    
    async def get_unit(self, unit_id: str) -> Optional[UnitWithHierarchy]:
        """Buscar unidade por ID."""
        try:
            result = self.supabase.table("ivo_units").select("*").eq("id", unit_id).execute()
            
            if not result.data:
                return None
                
            return UnitWithHierarchy(**result.data[0])
            
        except Exception as e:
            logger.error(f"Erro ao buscar unidade {unit_id}: {str(e)}")
            raise
    
    async def get_unit_with_hierarchy(self, unit_id: str) -> Optional[UnitWithHierarchy]:
        """Alias para get_unit - compatibilidade com métodos de embedding."""
        return await self.get_unit(unit_id)
    
    async def list_units_by_book(self, book_id: str) -> List[UnitWithHierarchy]:
        """Listar unidades de um book (método original mantido)."""
        try:
            result = (
                self.supabase.table("ivo_units")
                .select("*")
                .eq("book_id", book_id)
                .order("sequence_order")
                .execute()
            )
            
            return [UnitWithHierarchy(**record) for record in result.data]
            
        except Exception as e:
            logger.error(f"Erro ao listar unidades do book {book_id}: {str(e)}")
            raise
    
    async def list_units_paginated(
        self,
        book_id: str,
        pagination: PaginationParams,
        sorting: SortParams,
        filters: Optional[UnitFilterParams] = None
    ) -> Tuple[List[UnitWithHierarchy], int]:
        """Listar unidades com paginação."""
        try:
            # Query base
            query = (
                self.supabase.table("ivo_units")
                .select("*", count="exact")
                .eq("book_id", book_id)
            )
            count_query = (
                self.supabase.table("ivo_units")
                .select("*", count="exact", head=True)
                .eq("book_id", book_id)
            )
            
            # Aplicar filtros
            if filters:
                filter_dict = filters.to_dict()
                
                if filter_dict.get('search'):
                    search_term = f"%{filter_dict['search']}%"
                    query = query.or_(f"title.ilike.{search_term},context.ilike.{search_term}")
                    count_query = count_query.or_(f"title.ilike.{search_term},context.ilike.{search_term}")
                
                if filter_dict.get('status'):
                    query = query.eq("status", filter_dict['status'])
                    count_query = count_query.eq("status", filter_dict['status'])
                
                if filter_dict.get('unit_type'):
                    query = query.eq("unit_type", filter_dict['unit_type'])
                    count_query = count_query.eq("unit_type", filter_dict['unit_type'])
                
                if filter_dict.get('cefr_level'):
                    query = query.eq("cefr_level", filter_dict['cefr_level'])
                    count_query = count_query.eq("cefr_level", filter_dict['cefr_level'])
                
                if filter_dict.get('quality_score_min'):
                    query = query.gte("quality_score", filter_dict['quality_score_min'])
                    count_query = count_query.gte("quality_score", filter_dict['quality_score_min'])
            
            # Contagem total
            count_result = count_query.execute()
            total_count = count_result.count
            
            # Ordenação
            allowed_sort_fields = ["title", "sequence_order", "status", "cefr_level", "created_at", "quality_score"]
            sort_field = sorting.sort_by if sorting.sort_by in allowed_sort_fields else "sequence_order"
            
            query = query.order(sort_field, desc=sorting.is_descending)
            
            # Paginação
            query = query.range(pagination.offset, pagination.offset + pagination.size - 1)
            
            # Executar
            result = query.execute()
            units = [UnitWithHierarchy(**record) for record in result.data]
            
            return units, total_count
            
        except Exception as e:
            logger.error(f"Erro ao listar unidades paginadas: {str(e)}")
            raise
    
    async def update_unit_status(self, unit_id: str, status: UnitStatus) -> bool:
        """Atualizar status da unidade."""
        try:
            # Handle both string and enum
            status_value = status.value if hasattr(status, 'value') else status
            
            result = (
                self.supabase.table("ivo_units")
                .update({"status": status_value, "updated_at": "now()"})
                .eq("id", unit_id)
                .execute()
            )
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status da unidade {unit_id}: {str(e)}")
            raise
    
    async def update_unit_content(self, unit_id: str, content_type: str, content: Dict[str, Any]) -> bool:
        """Atualizar conteúdo específico da unidade."""
        try:
            update_data = {
                content_type: content,
                "updated_at": "now()"
            }
            
            result = (
                self.supabase.table("ivo_units")
                .update(update_data)
                .eq("id", unit_id)
                .execute()
            )
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar conteúdo {content_type} da unidade {unit_id}: {str(e)}")
            raise
    
    # =============================================================================
    # RAG FUNCTIONS (mantidas do original)
    # =============================================================================
    
    async def get_taught_vocabulary(
        self, 
        course_id: str, 
        book_id: Optional[str] = None, 
        sequence_order: Optional[int] = None
    ) -> List[str]:
        """Buscar vocabulário já ensinado usando função SQL."""
        try:
            result = self.supabase.rpc(
                "get_taught_vocabulary",
                {
                    "target_course_id": course_id,
                    "target_book_id": book_id,
                    "target_sequence": sequence_order
                }
            ).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Erro ao buscar vocabulário ensinado: {str(e)}")
            return []
    
    async def get_used_strategies(
        self, 
        course_id: str, 
        book_id: str, 
        sequence_order: int
    ) -> List[str]:
        """Buscar estratégias já usadas usando função SQL."""
        try:
            result = self.supabase.rpc(
                "get_used_strategies",
                {
                    "target_course_id": course_id,
                    "target_book_id": book_id,
                    "target_sequence": sequence_order
                }
            ).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Erro ao buscar estratégias usadas: {str(e)}")
            return []
    
    async def get_used_assessments(
        self, 
        course_id: str, 
        book_id: str, 
        sequence_order: int
    ) -> Dict[str, Any]:
        """Buscar atividades já usadas usando função SQL."""
        try:
            result = self.supabase.rpc(
                "get_used_assessments",
                {
                    "target_course_id": course_id,
                    "target_book_id": book_id,
                    "target_sequence": sequence_order
                }
            ).execute()
            
            return result.data or {}
            
        except Exception as e:
            logger.error(f"Erro ao buscar atividades usadas: {str(e)}")
            return {}
    
    async def match_precedent_units(
        self,
        query_embedding: List[float],
        course_id: str,
        book_id: str,
        sequence_order: int,
        match_threshold: float = 0.7,
        match_count: int = 5,
        is_revision_unit: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Buscar unidades precedentes para RAG com prioridade híbrida."""
        try:
            result = self.supabase.rpc(
                "match_precedent_units_enhanced",
                {
                    "query_embedding": query_embedding,
                    "target_course_id": course_id,
                    "target_book_id": book_id,
                    "target_sequence": sequence_order,
                    "match_threshold": match_threshold,
                    "match_count": match_count,
                    "is_revision_unit": is_revision_unit or False
                }
            ).execute()
            
            results = result.data or []
            
            # Log para debug
            if results:
                recent_count = len([r for r in results if r.get('context_type') == 'recent'])
                semantic_count = len([r for r in results if r.get('context_type') == 'semantic'])
                logger.info(f"RAG Context: {recent_count} recent + {semantic_count} semantic units")
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao buscar unidades precedentes: {str(e)}")
            # Fallback para função original se nova não existir
            try:
                result = self.supabase.rpc(
                    "match_precedent_units",
                    {
                        "query_embedding": query_embedding,
                        "target_course_id": course_id,
                        "target_book_id": book_id,
                        "target_sequence": sequence_order,
                        "match_threshold": match_threshold,
                        "match_count": match_count
                    }
                ).execute()
                return result.data or []
            except:
                return []
    
    # =============================================================================
    # VALIDATION & HELPER METHODS
    # =============================================================================
    
    async def validate_hierarchy(self, course_id: str, book_id: str) -> HierarchyValidationResult:
        """Validar se book pertence ao curso."""
        try:
            # Verificar se course existe
            course = await self.get_course(course_id)
            if not course:
                return HierarchyValidationResult(
                    is_valid=False,
                    errors=[f"Curso {course_id} não encontrado"]
                )
            
            # Verificar se book existe e pertence ao curso
            result = (
                self.supabase.table("ivo_books")
                .select("id, course_id")
                .eq("id", book_id)
                .eq("course_id", course_id)
                .execute()
            )
            
            if not result.data:
                return HierarchyValidationResult(
                    is_valid=False,
                    errors=[f"Book {book_id} não pertence ao curso {course_id}"]
                )
            
            return HierarchyValidationResult(is_valid=True)
            
        except Exception as e:
            logger.error(f"Erro na validação hierárquica: {str(e)}")
            return HierarchyValidationResult(
                is_valid=False,
                errors=[f"Erro de validação: {str(e)}"]
            )
    
    async def validate_hierarchy_complete(
        self, 
        book_id: str, 
        unit_data: Dict[str, Any]
    ) -> HierarchyValidationResult:
        """
        Validação hierárquica simples para criação de units.
        Foca apenas em validações básicas, sem restrições pedagógicas.
        """
        try:
            errors = []
            
            # 1. Validar que book existe
            book = await self.get_book(book_id)
            if not book:
                return HierarchyValidationResult(
                    is_valid=False,
                    errors=[f"Book {book_id} não encontrado"]
                )
            
            # 2. Validar que course existe
            course = await self.get_course(book.course_id)
            if not course:
                return HierarchyValidationResult(
                    is_valid=False,
                    errors=[f"Course {book.course_id} não encontrado"]
                )
            
            # 3. Validar que CEFR level é válido (apenas formato)
            unit_cefr = unit_data.get("cefr_level")
            valid_cefr = ["A1", "A2", "B1", "B2", "C1", "C2"]
            if unit_cefr not in valid_cefr:
                errors.append(f"CEFR level inválido: '{unit_cefr}'. Use: {', '.join(valid_cefr)}")
            
            # 4. Validar que language_variant é válido (apenas formato)
            unit_variant = unit_data.get("language_variant")
            valid_variants = [
                "american_english", "british_english", "australian_english", 
                "indian_english", "canadian_english", "mexican_spanish",
                "argentinian_spanish", "colombian_spanish", "spanish_spain",
                "brazilian_portuguese", "european_portuguese", 
                "french_france", "canadian_french"
            ]
            if unit_variant not in valid_variants:
                errors.append(f"Language variant inválido: '{unit_variant}'")
            
            # 5. Validar que unit_type é válido
            unit_type = unit_data.get("unit_type")
            valid_types = ["lexical_unit", "grammar_unit"]
            if unit_type not in valid_types:
                errors.append(f"Unit type inválido: '{unit_type}'. Use: {', '.join(valid_types)}")
            
            # Resultado - só valida dados básicos, sem restrições pedagógicas
            is_valid = len(errors) == 0
            
            return HierarchyValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=[],
                suggestions=[]
            )
            
        except Exception as e:
            logger.error(f"Erro na validação hierárquica: {str(e)}")
            return HierarchyValidationResult(
                is_valid=False,
                errors=[f"Erro interno de validação: {str(e)}"]
            )
    
    async def get_progression_analysis(
        self, 
        course_id: str, 
        book_id: str, 
        current_sequence: int
    ) -> ProgressionAnalysis:
        """Analisar progressão pedagógica."""
        try:
            # Buscar vocabulário ensinado
            taught_vocab = await self.get_taught_vocabulary(course_id, book_id, current_sequence)
            
            # Buscar estratégias usadas
            used_strategies = await self.get_used_strategies(course_id, book_id, current_sequence)
            
            # Buscar atividades usadas
            used_assessments = await self.get_used_assessments(course_id, book_id, current_sequence)
            
            # Contar estratégias
            strategy_distribution = {}
            for strategy in used_strategies:
                strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
            
            # Análise de balanceamento
            assessment_balance = {}
            if isinstance(used_assessments, dict):
                assessment_balance = used_assessments
            
            # Gerar recomendações
            recommendations = []
            if len(taught_vocab) > 100:
                recommendations.append("Considerar revisão de vocabulário aprendido")
            
            if len(set(used_strategies)) < 3:
                recommendations.append("Diversificar estratégias pedagógicas")
            
            return ProgressionAnalysis(
                course_id=course_id,
                book_id=book_id,
                current_sequence=current_sequence,
                vocabulary_progression={"total_words": len(taught_vocab), "words": taught_vocab[:10]},
                strategy_distribution=strategy_distribution,
                assessment_balance=assessment_balance,
                recommendations=recommendations,
                quality_metrics={
                    "vocabulary_diversity": len(set(taught_vocab)) / max(len(taught_vocab), 1),
                    "strategy_diversity": len(set(used_strategies)) / max(len(used_strategies), 1)
                }
            )
            
        except Exception as e:
            logger.error(f"Erro na análise de progressão: {str(e)}")
            return ProgressionAnalysis(
                course_id=course_id,
                book_id=book_id,
                current_sequence=current_sequence
            )
    
    async def _get_next_book_sequence(self, course_id: str) -> int:
        """Determinar próximo sequence_order para book."""
        try:
            result = (
                self.supabase.table("ivo_books")
                .select("sequence_order")
                .eq("course_id", course_id)
                .order("sequence_order", desc=True)
                .limit(1)
                .execute()
            )
            
            if result.data:
                return result.data[0]["sequence_order"] + 1
            return 1
            
        except Exception as e:
            logger.error(f"Erro ao determinar próximo sequence para course {course_id}: {str(e)}")
            return 1
    
    async def _get_next_unit_sequence(self, book_id: str) -> int:
        """Determinar próximo sequence_order para unit."""
        try:
            result = (
                self.supabase.table("ivo_units")
                .select("sequence_order")
                .eq("book_id", book_id)
                .order("sequence_order", desc=True)
                .limit(1)
                .execute()
            )
            
            if result.data:
                return result.data[0]["sequence_order"] + 1
            return 1
            
        except Exception as e:
            logger.error(f"Erro ao determinar próximo sequence para book {book_id}: {str(e)}")
            return 1
    
    # =============================================================================
    # BULK OPERATIONS
    # =============================================================================
    
    async def get_course_hierarchy(self, course_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Buscar hierarquia completa do curso com controle de profundidade."""
        try:
            # Buscar curso
            course = await self.get_course(course_id)
            if not course:
                return {}
            
            hierarchy = {
                "course": course.dict(),
                "books": []
            }
            
            # Se max_depth >= 2, incluir books
            if max_depth >= 2:
                books = await self.list_books_by_course(course_id)
                
                for book in books:
                    book_data = book.dict()
                    
                    # Se max_depth >= 3, incluir units
                    if max_depth >= 3:
                        units = await self.list_units_by_book(book.id)
                        book_data["units"] = [unit.dict() for unit in units]
                    else:
                        book_data["units"] = []
                    
                    hierarchy["books"].append(book_data)
            
            return hierarchy
            
        except Exception as e:
            logger.error(f"Erro ao buscar hierarquia do curso {course_id}: {str(e)}")
            return {}
    
    # =============================================================================
    # SEARCH AND ANALYTICS
    # =============================================================================
    
    async def search_across_hierarchy(
        self,
        search_term: str,
        course_id: Optional[str] = None,
        search_types: List[str] = ["courses", "books", "units"]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Buscar em toda a hierarquia."""
        results = {
            "courses": [],
            "books": [],
            "units": []
        }
        
        try:
            search_pattern = f"%{search_term}%"
            
            # Buscar courses
            if "courses" in search_types:
                query = self.supabase.table("ivo_courses").select("*")
                if course_id:
                    query = query.eq("id", course_id)
                
                course_results = query.or_(
                    f"name.ilike.{search_pattern},description.ilike.{search_pattern}"
                ).execute()
                
                results["courses"] = [Course(**record).dict() for record in course_results.data]
            
            # Buscar books
            if "books" in search_types:
                query = self.supabase.table("ivo_books").select("*")
                if course_id:
                    query = query.eq("course_id", course_id)
                
                book_results = query.or_(
                    f"name.ilike.{search_pattern},description.ilike.{search_pattern}"
                ).execute()
                
                results["books"] = [Book(**record).dict() for record in book_results.data]
            
            # Buscar units
            if "units" in search_types:
                query = self.supabase.table("ivo_units").select("*")
                if course_id:
                    query = query.eq("course_id", course_id)
                
                unit_results = query.or_(
                    f"title.ilike.{search_pattern},context.ilike.{search_pattern}"
                ).execute()
                
                results["units"] = [UnitWithHierarchy(**record).dict() for record in unit_results.data]
            
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca hierárquica: {str(e)}")
            return results
    
    async def get_system_analytics(self) -> Dict[str, Any]:
        """Obter analytics do sistema."""
        try:
            # Contar recursos
            courses_count = self.supabase.table("ivo_courses").select("*", count="exact", head=True).execute().count
            books_count = self.supabase.table("ivo_books").select("*", count="exact", head=True).execute().count
            units_count = self.supabase.table("ivo_units").select("*", count="exact", head=True).execute().count
            
            # Distribuição por status
            status_distribution = {}
            units_by_status = self.supabase.table("ivo_units").select("status", count="exact").execute()
            
            for unit in units_by_status.data:
                status = unit.get("status", "unknown")
                status_distribution[status] = status_distribution.get(status, 0) + 1
            
            # Distribuição por nível CEFR
            cefr_distribution = {}
            units_by_cefr = self.supabase.table("ivo_units").select("cefr_level", count="exact").execute()
            
            for unit in units_by_cefr.data:
                level = unit.get("cefr_level", "unknown")
                cefr_distribution[level] = cefr_distribution.get(level, 0) + 1
            
            return {
                "system_totals": {
                    "courses": courses_count,
                    "books": books_count,
                    "units": units_count
                },
                "status_distribution": status_distribution,
                "cefr_distribution": cefr_distribution,
                "completion_rate": (
                    status_distribution.get("completed", 0) / max(units_count, 1)
                ) * 100,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter analytics: {str(e)}")
            return {}
    
    # =============================================================================
    # EMBEDDING OPERATIONS
    # =============================================================================
    
    async def upsert_unit_content_embeddings(
        self,
        unit_id: str,
        contents: Dict[str, Dict[str, Any]]
    ) -> Dict[str, bool]:
        """
        Fazer upsert de embeddings para todos os conteúdos de uma unidade.
        
        Args:
            unit_id: ID da unidade
            contents: Dict com {content_type: content_data}
            
        Returns:
            Dict[str, bool]: Resultado de cada tipo de conteúdo
        """
        try:
            # Obter dados hierárquicos da unidade
            unit = await self.get_unit_with_hierarchy(unit_id)
            if not unit:
                logger.error(f"❌ Unidade {unit_id} não encontrada para embedding")
                return {}
            
            # Fazer bulk upsert usando embedding service
            results = await self.embedding_service.bulk_upsert_unit_embeddings(
                course_id=unit.course_id,
                book_id=unit.book_id,
                unit_id=unit.id,
                sequence_order=unit.sequence_order,
                contents=contents
            )
            
            logger.info(f"📊 Embeddings da unidade {unit_id} atualizados: {results}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer upsert de embeddings da unidade {unit_id}: {str(e)}")
            return {}
    
    async def upsert_single_content_embedding(
        self,
        unit_id: str,
        content_type: str,
        content_data: Dict[str, Any]
    ) -> bool:
        """
        Fazer upsert de embedding para um tipo específico de conteúdo.
        
        Args:
            unit_id: ID da unidade
            content_type: Tipo do conteúdo ('vocabulary', 'sentences', etc.)
            content_data: Dados do conteúdo
            
        Returns:
            bool: True se sucesso
        """
        try:
            # Obter dados hierárquicos da unidade
            unit = await self.get_unit_with_hierarchy(unit_id)
            if not unit:
                logger.error(f"❌ Unidade {unit_id} não encontrada para embedding")
                return False
            
            # Fazer upsert usando embedding service
            success = await self.embedding_service.upsert_unit_content_embedding(
                course_id=unit.course_id,
                book_id=unit.book_id,
                unit_id=unit.id,
                sequence_order=unit.sequence_order,
                content_type=content_type,
                content_data=content_data
            )
            
            if success:
                logger.info(f"✅ Embedding {content_type} da unidade {unit_id} atualizado")
            else:
                logger.error(f"❌ Falha ao atualizar embedding {content_type} da unidade {unit_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer upsert de embedding {content_type}: {str(e)}")
            return False
    
    async def delete_unit_embeddings(self, unit_id: str) -> bool:
        """
        Deletar todos os embeddings de uma unidade.
        
        Args:
            unit_id: ID da unidade
            
        Returns:
            bool: True se sucesso
        """
        try:
            success = await self.embedding_service.delete_unit_embeddings(unit_id)
            
            if success:
                logger.info(f"✅ Embeddings da unidade {unit_id} deletados")
            else:
                logger.error(f"❌ Falha ao deletar embeddings da unidade {unit_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao deletar embeddings da unidade {unit_id}: {str(e)}")
            return False

    async def _generate_and_save_unit_aims(self, unit: UnitWithHierarchy, unit_data: HierarchicalUnitRequest):
        """Gerar aims automaticamente para a unit criada e salvar no banco."""
        try:
            # Buscar contexto hierárquico
            course = await self.get_course(unit.course_id)
            book = await self.get_book(unit.book_id)
            
            if not course or not book:
                logger.warning(f"Contexto hierárquico incompleto para unit {unit.id}")
                return
            
            # Preparar parâmetros para detecção de aims
            detection_params = {
                "unit_data": {
                    "title": unit.title or f"Unit {unit.sequence_order}",
                    "context": unit.context or "General English learning unit",
                    "cefr_level": unit.cefr_level,
                    "unit_type": unit.unit_type,
                    "language_variant": unit.language_variant,
                    "main_aim": unit.main_aim,
                    "subsidiary_aims": unit.subsidiary_aims or []
                },
                "content_data": {
                    # Vazio inicialmente - aims são gerados primeiro
                    "vocabulary": {"items": []},
                    "sentences": {"sentences": []},
                    "tips": None,
                    "grammar": None,
                    "assessments": None
                },
                "hierarchy_context": {
                    "course_name": course.name,
                    "book_name": book.name,
                    "sequence_order": unit.sequence_order,
                    "target_level": unit.cefr_level
                },
                "rag_context": {
                    # Contexto RAG básico - pode ser expandido
                    "taught_vocabulary": [],
                    "used_strategies": [],
                    "progression_level": "initial"
                },
                "images_analysis": {
                    "success": False,
                    "individual_analyses": []
                }
            }
            
            # Gerar aims usando AimDetectorService
            aim_detector = AimDetectorService()
            unit_aims = await aim_detector.detect_and_generate_aims(detection_params)
            
            # Salvar no banco
            update_data = {
                "main_aim": unit_aims.main_aim,
                "subsidiary_aims": unit_aims.subsidiary_aims
            }
            
            result = (
                self.supabase.table("ivo_units")
                .update(update_data)
                .eq("id", unit.id)
                .execute()
            )
            
            if result.data:
                logger.info(f"✅ Aims salvos no banco para unit {unit.id}: main_aim + {len(unit_aims.subsidiary_aims)} subsidiary")
            else:
                logger.error(f"❌ Falha ao salvar aims para unit {unit.id}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar aims para unit {unit.id}: {str(e)}")
            raise


    # =============================================================================
    # DASHBOARD METHODS - CONSULTAS POR DATA RANGE
    # =============================================================================
    
    async def get_courses_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Course]:
        """Buscar cursos criados em um período específico."""
        try:
            result = (
                self.supabase.table("ivo_courses")
                .select("*")
                .gte("created_at", start_date.isoformat())
                .lt("created_at", end_date.isoformat())
                .execute()
            )
            
            if result.data:
                courses = []
                for course_dict in result.data:
                    try:
                        course = Course.parse_obj(course_dict)
                        courses.append(course)
                    except Exception as e:
                        logger.warning(f"Erro ao parsear curso {course_dict.get('id')}: {str(e)}")
                        continue
                
                return courses
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar cursos por data: {str(e)}")
            return []
    
    async def get_books_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Book]:
        """Buscar books criados em um período específico."""
        try:
            result = (
                self.supabase.table("ivo_books")
                .select("*")
                .gte("created_at", start_date.isoformat())
                .lt("created_at", end_date.isoformat())
                .execute()
            )
            
            if result.data:
                books = []
                for book_dict in result.data:
                    try:
                        book = Book.parse_obj(book_dict)
                        books.append(book)
                    except Exception as e:
                        logger.warning(f"Erro ao parsear book {book_dict.get('id')}: {str(e)}")
                        continue
                
                return books
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar books por data: {str(e)}")
            return []
    
    async def get_units_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[UnitWithHierarchy]:
        """Buscar units criadas em um período específico."""
        try:
            result = (
                self.supabase.table("ivo_units")
                .select("*")
                .gte("created_at", start_date.isoformat())
                .lt("created_at", end_date.isoformat())
                .execute()
            )
            
            if result.data:
                units = []
                for unit_dict in result.data:
                    try:
                        unit = UnitWithHierarchy.parse_obj(unit_dict)
                        units.append(unit)
                    except Exception as e:
                        logger.warning(f"Erro ao parsear unit {unit_dict.get('id')}: {str(e)}")
                        continue
                
                return units
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar units por data: {str(e)}")
            return []


# Instância global do serviço
hierarchical_db = HierarchicalDatabaseService()