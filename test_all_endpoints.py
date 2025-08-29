#!/usr/bin/env python3
"""
Script de teste completo para todos os endpoints do IVO V2
Executa testes na ordem hierárquica: Course → Book → Unit → Content
Gera relatório detalhado de erros e acertos
"""

import requests
import json
import time
from datetime import datetime
import os
import sys
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
BASE_URL = "http://localhost:8000"
OUTPUT_DIR = "test_reports"
TIMEOUT = 30

class EndpointTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.start_time = datetime.now()
        
        # IDs criados durante os testes para usar em endpoints dependentes
        self.test_ids = {
            'course_id': None,
            'book_id': None,
            'unit_id': None
        }
        
        # Autenticação
        self.bearer_token = None
        self.auth_setup_completed = False
        
        # Criar diretório de relatórios se não existir
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    def log_result(self, category: str, endpoint: str, method: str, 
                   status_code: int, response_data: Any, error: str = None,
                   execution_time: float = 0, notes: str = ""):
        """Registrar resultado do teste"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'success': 200 <= status_code < 300,
            'response_size': len(str(response_data)) if response_data else 0,
            'execution_time_ms': round(execution_time * 1000, 2),
            'error': error,
            'notes': notes,
            'response_preview': str(response_data)[:200] if response_data else None
        }
        self.results.append(result)
        
        # Log em tempo real
        status = "✅" if result['success'] else "❌"
        print(f"{status} [{category}] {method} {endpoint} - {status_code} ({execution_time*1000:.0f}ms)")
        if error:
            print(f"    Error: {error}")
        if notes:
            print(f"    Notes: {notes}")
    
    def test_endpoint(self, category: str, method: str, endpoint: str, 
                     data: Dict = None, files: Dict = None, 
                     expected_status: int = 200, notes: str = "") -> Optional[Dict]:
        """Testar um endpoint específico"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=TIMEOUT)
            elif method.upper() == 'POST':
                if files:
                    response = self.session.post(url, data=data, files=files, timeout=TIMEOUT)
                else:
                    response = self.session.post(url, json=data, timeout=TIMEOUT)
            elif method.upper() == 'PUT':
                if files:
                    response = self.session.put(url, data=data, files=files, timeout=TIMEOUT)
                else:
                    response = self.session.put(url, json=data, timeout=TIMEOUT)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=TIMEOUT)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            execution_time = time.time() - start_time
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            self.log_result(
                category=category,
                endpoint=endpoint,
                method=method.upper(),
                status_code=response.status_code,
                response_data=response_data,
                execution_time=execution_time,
                notes=notes
            )
            
            return response_data if response.status_code == expected_status else None
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_result(
                category=category,
                endpoint=endpoint,
                method=method.upper(),
                status_code=0,
                response_data=None,
                error=str(e),
                execution_time=execution_time,
                notes=notes
            )
            return None
    
    def setup_authentication(self):
        """Configurar autenticação com fallback inteligente"""
        print("\n🔐 CONFIGURANDO AUTENTICAÇÃO")
        
        # Estratégia 1: Token de desenvolvimento
        test_token = os.getenv("TEST_API_KEY_IVO", "ivo_test_token_dev_only_remove_in_prod")
        if self._try_login(test_token, "desenvolvimento"):
            return True
        
        # Estratégia 2: Criar usuário temporário para teste
        print("    🔄 Tentando criar usuário temporário de teste...")
        if self._try_create_temp_user():
            return True
        
        # Estratégia 3: Continuar sem autenticação (mostra quais endpoints falham)
        print("    ⚠️  Continuando sem autenticação - endpoints V2 mostrarão falhas esperadas")
        return False
    
    def _try_login(self, token_ivo: str, token_type: str) -> bool:
        """Tentar login com token específico"""
        try:
            auth_data = {"api_key_ivo": token_ivo}
            response = self.session.post(f"{BASE_URL}/api/auth/login", json=auth_data, timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                self.bearer_token = data.get('access_token')
                if self.bearer_token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.bearer_token}'
                    })
                    self.auth_setup_completed = True
                    print(f"    ✅ Login com token {token_type} realizado com sucesso")
                    print(f"    🔑 Token Bearer: {self.bearer_token[:20]}...")
                    return True
            
            print(f"    ❌ Falha no login {token_type}: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"    ❌ Erro no login {token_type}: {str(e)}")
            return False
    
    def _try_create_temp_user(self) -> bool:
        """Tentar criar usuário temporário para teste"""
        try:
            import time
            temp_email = f"test_auto_{int(time.time())}@ivo-test.com"
            
            user_data = {
                "email": temp_email,
                "metadata": {"source": "automated_test", "temporary": True}
            }
            
            response = self.session.post(f"{BASE_URL}/api/auth/create-user", json=user_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                bearer_token = result.get("token_info", {}).get("access_token")
                
                if bearer_token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {bearer_token}'
                    })
                    self.auth_setup_completed = True
                    self.bearer_token = bearer_token
                    
                    print(f"    ✅ Usuário temporário criado: {temp_email}")
                    print(f"    🔑 Token Bearer: {bearer_token[:20]}...")
                    return True
            
            print(f"    ❌ Falha ao criar usuário temporário: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"    ❌ Erro ao criar usuário temporário: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Executar todos os testes na ordem hierárquica"""
        print("🚀 Iniciando testes completos do IVO V2...")
        print(f"📍 Base URL: {BASE_URL}")
        print(f"⏰ Início: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 0. CONFIGURAR AUTENTICAÇÃO
        auth_success = self.setup_authentication()
        if not auth_success:
            print("⚠️ Prosseguindo sem autenticação - alguns testes podem falhar")
        
        # 1. TESTES DE SISTEMA
        self.test_system_endpoints()
        
        # 2. TESTES DE AUTENTICAÇÃO
        self.test_auth_endpoints()
        
        # 3. TESTES DE DEBUG
        self.test_debug_endpoints()
        
        # 4. TESTES HIERÁRQUICOS - ORDEM OBRIGATÓRIA
        self.test_course_operations()
        self.test_book_operations()
        self.test_unit_operations()
        self.test_content_generation()
        
        # 5. TESTES DE ENDPOINTS INFORMATIVOS
        self.test_info_endpoints()
        
        print("=" * 80)
        print("🏁 Testes concluídos!")
        self.generate_report()
    
    def test_system_endpoints(self):
        """Testar endpoints de sistema"""
        print("\n📊 TESTANDO ENDPOINTS DE SISTEMA")
        
        self.test_endpoint("SYSTEM", "GET", "/", notes="Página inicial da API")
        self.test_endpoint("SYSTEM", "GET", "/docs", notes="Documentação Swagger")
        self.test_endpoint("SYSTEM", "GET", "/redoc", notes="Documentação ReDoc")
        self.test_endpoint("SYSTEM", "GET", "/openapi.json", notes="Schema OpenAPI")
        self.test_endpoint("SYSTEM", "GET", "/system/health", notes="Health check detalhado")
        self.test_endpoint("SYSTEM", "GET", "/system/stats", notes="Estatísticas do sistema")
        self.test_endpoint("SYSTEM", "GET", "/system/rate-limits", notes="Info de rate limiting")
        self.test_endpoint("SYSTEM", "GET", "/system/redis-migration", notes="Info migração Redis")
    
    def test_auth_endpoints(self):
        """Testar endpoints de autenticação"""
        print("\n🔐 TESTANDO ENDPOINTS DE AUTENTICAÇÃO")
        
        # Testar login com token válido
        test_token = os.getenv("TEST_API_KEY_IVO", "ivo_test_token_dev_only_remove_in_prod")
        login_data = {
            "api_key_ivo": test_token
        }
        self.test_endpoint("AUTH", "POST", "/api/auth/login", data=login_data, 
                         notes="Login com token IVO")
        
        # Testar validação do token (com autenticação)
        self.test_endpoint("AUTH", "GET", "/api/auth/validate-token", 
                         notes="Validar token Bearer atual")
        
        # Testar criação de usuário
        user_data = {
            "email": f"test_{int(time.time())}@example.com",
            "metadata": {"source": "automated_test"}
        }
        self.test_endpoint("AUTH", "POST", "/api/auth/create-user", data=user_data,
                         notes="Criar novo usuário")
    
    def test_debug_endpoints(self):
        """Testar endpoints de debug"""
        print("\n🔍 TESTANDO ENDPOINTS DE DEBUG")
        
        self.test_endpoint("DEBUG", "GET", "/debug/routes", notes="Lista de rotas registradas")
        self.test_endpoint("DEBUG", "GET", "/debug/storage", notes="Info de storage/cache")
        self.test_endpoint("DEBUG", "GET", "/debug/router-registration", notes="Debug registro de routers")
        self.test_endpoint("DEBUG", "GET", "/debug/api-status", notes="Status da API")
    
    def test_course_operations(self):
        """Testar operações de Course (hierarquia nível 1)"""
        print("\n📚 TESTANDO OPERAÇÕES DE COURSES")
        
        # Criar course
        course_data = {
            "name": "Curso de Teste Automático",
            "description": "Curso criado pelo script de testes",
            "target_levels": ["A1", "A2", "B1"],
            "language_variant": "american_english"
        }
        
        if self.auth_setup_completed:
            response = self.test_endpoint("COURSE", "POST", "/api/v2/courses", 
                                        data=course_data, notes="Criar novo curso")
        else:
            response = self.test_endpoint("COURSE", "POST", "/api/v2/courses", 
                             data=course_data, notes="Criar novo curso (sem auth - deve falhar)", 
                             expected_status=401)
        
        if response and response.get('success'):
            course_id = response.get('data', {}).get('course', {}).get('id')
            if course_id:
                self.test_ids['course_id'] = course_id
                print(f"    📝 Course ID obtido: {course_id}")
        
        # Listar courses (também protegido)
        expected_status = 200 if self.auth_setup_completed else 401
        self.test_endpoint("COURSE", "GET", "/api/v2/courses", notes="Listar todos os courses",
                         expected_status=expected_status)
        
        # Testar course específico se temos ID
        if self.test_ids['course_id'] and self.auth_setup_completed:
            course_id = self.test_ids['course_id']
            self.test_endpoint("COURSE", "GET", f"/api/v2/courses/{course_id}", 
                             notes="Obter course específico")
            self.test_endpoint("COURSE", "GET", f"/api/v2/courses/{course_id}/hierarchy", 
                             notes="Hierarquia do course")
            self.test_endpoint("COURSE", "GET", f"/api/v2/courses/{course_id}/progress", 
                             notes="Progresso do course")
        
        # Endpoints simples de teste (também protegidos)
        expected_status = 200 if self.auth_setup_completed else 401
        self.test_endpoint("COURSE", "GET", "/api/v2/test", notes="Endpoint de teste simples",
                         expected_status=expected_status)
    
    def test_book_operations(self):
        """Testar operações de Book (hierarquia nível 2)"""
        print("\n📖 TESTANDO OPERAÇÕES DE BOOKS")
        
        if not self.test_ids['course_id']:
            print("    ⚠️ Pulando testes de books - nenhum course_id disponível")
            return
        
        course_id = self.test_ids['course_id']
        
        # Criar book
        book_data = {
            "name": "Book de Teste A1",
            "description": "Book criado pelo script de testes",
            "target_level": "A1"
        }
        
        response = self.test_endpoint("BOOK", "POST", f"/api/v2/courses/{course_id}/books", 
                                    data=book_data, notes="Criar novo book")
        
        if response and response.get('success'):
            book_id = response.get('data', {}).get('book', {}).get('id')
            if book_id:
                self.test_ids['book_id'] = book_id
                print(f"    📝 Book ID obtido: {book_id}")
        
        # Listar books do course
        self.test_endpoint("BOOK", "GET", f"/api/v2/courses/{course_id}/books", 
                         notes="Listar books do course")
        
        # Testar book específico se temos ID
        if self.test_ids['book_id']:
            book_id = self.test_ids['book_id']
            self.test_endpoint("BOOK", "GET", f"/api/v2/books/{book_id}", 
                             notes="Obter book específico")
            self.test_endpoint("BOOK", "GET", f"/api/v2/books/{book_id}/progression", 
                             notes="Progressão pedagógica do book")
    
    def test_unit_operations(self):
        """Testar operações de Unit (hierarquia nível 3)"""
        print("\n📑 TESTANDO OPERAÇÕES DE UNITS")
        
        if not self.test_ids['book_id']:
            print("    ⚠️ Pulando testes de units - nenhum book_id disponível")
            return
        
        book_id = self.test_ids['book_id']
        
        # Criar arquivo de imagem fake para teste
        fake_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        
        # Criar unit
        unit_data = {
            'context': 'Unidade de teste criada automaticamente',
            'cefr_level': 'A1',
            'language_variant': 'american_english',
            'unit_type': 'lexical_unit'
        }
        
        files = {
            'image_1': ('test_image.png', fake_image, 'image/png')
        }
        
        response = self.test_endpoint("UNIT", "POST", f"/api/v2/books/{book_id}/units", 
                                    data=unit_data, files=files, notes="Criar nova unit")
        
        if response and response.get('success'):
            unit_id = response.get('data', {}).get('unit', {}).get('id')
            if unit_id:
                self.test_ids['unit_id'] = unit_id
                print(f"    📝 Unit ID obtido: {unit_id}")
        
        # Listar units do book
        self.test_endpoint("UNIT", "GET", f"/api/v2/books/{book_id}/units", 
                         notes="Listar units do book")
        
        # Testar unit específica se temos ID
        if self.test_ids['unit_id']:
            unit_id = self.test_ids['unit_id']
            self.test_endpoint("UNIT", "GET", f"/api/v2/units/{unit_id}", 
                             notes="Obter unit específica")
            self.test_endpoint("UNIT", "GET", f"/api/v2/units/{unit_id}/context", 
                             notes="Contexto RAG da unit")
    
    def test_content_generation(self):
        """Testar geração de conteúdo (hierarquia nível 4)"""
        print("\n🔤 TESTANDO GERAÇÃO DE CONTEÚDO")
        
        if not self.test_ids['unit_id']:
            print("    ⚠️ Pulando testes de conteúdo - nenhum unit_id disponível")
            return
        
        unit_id = self.test_ids['unit_id']
        
        # Vocabulário
        vocab_data = {
            "target_word_count": 10,
            "difficulty_level": "beginner",
            "include_ipa": True
        }
        self.test_endpoint("CONTENT", "POST", f"/api/v2/units/{unit_id}/vocabulary", 
                         data=vocab_data, notes="Gerar vocabulário")
        self.test_endpoint("CONTENT", "GET", f"/api/v2/units/{unit_id}/vocabulary", 
                         notes="Obter vocabulário da unit")
        
        # Sentences
        sentences_data = {
            "target_sentence_count": 5,
            "connection_style": "contextual"
        }
        self.test_endpoint("CONTENT", "POST", f"/api/v2/units/{unit_id}/sentences", 
                         notes="Obter sentences da unit")
        
        # Tips (estratégias lexicais)
        tips_data = {
            "strategy_count": 2,
            "focus_areas": ["pronunciation", "usage"]
        }
        self.test_endpoint("CONTENT", "POST", f"/api/v2/units/{unit_id}/tips", 
                         data=tips_data, notes="Gerar tips")
        self.test_endpoint("CONTENT", "GET", f"/api/v2/units/{unit_id}/tips", 
                         notes="Obter tips da unit")
        
        # Grammar (estratégias gramaticais)
        grammar_data = {
            "grammar_points": ["present_simple"],
            "include_l1_interference": True
        }
        self.test_endpoint("CONTENT", "POST", f"/api/v2/units/{unit_id}/grammar", 
                         data=grammar_data, notes="Gerar grammar")
        self.test_endpoint("CONTENT", "GET", f"/api/v2/units/{unit_id}/grammar", 
                         notes="Obter grammar da unit")
        
        # Assessments
        assessment_data = {
            "assessment_count": 2,
            "assessment_types": ["fill_blank", "multiple_choice"]
        }
        self.test_endpoint("CONTENT", "POST", f"/api/v2/units/{unit_id}/assessments", 
                         data=assessment_data, notes="Gerar assessments")
        self.test_endpoint("CONTENT", "GET", f"/api/v2/units/{unit_id}/assessments", 
                         notes="Obter assessments da unit")
        
        # Q&A
        qa_data = {
            "question_count": 3,
            "bloom_levels": ["knowledge", "comprehension"]
        }
        self.test_endpoint("CONTENT", "POST", f"/api/v2/units/{unit_id}/qa", 
                         data=qa_data, notes="Gerar Q&A")
        self.test_endpoint("CONTENT", "GET", f"/api/v2/units/{unit_id}/qa", 
                         notes="Obter Q&A da unit")
        
        # Endpoints informativos de estratégias
        self.test_endpoint("CONTENT", "GET", "/api/v2/tips/strategies", 
                         notes="Info sobre estratégias TIPS")
        self.test_endpoint("CONTENT", "GET", "/api/v2/grammar/strategies", 
                         notes="Info sobre estratégias GRAMMAR")
        self.test_endpoint("CONTENT", "GET", "/api/v2/assessments/types", 
                         notes="Tipos de assessments")
        self.test_endpoint("CONTENT", "GET", "/api/v2/qa/pedagogical-guidelines", 
                         notes="Guidelines pedagógicas Q&A")
    
    def test_info_endpoints(self):
        """Testar endpoints informativos"""
        print("\n📋 TESTANDO ENDPOINTS INFORMATIVOS")
        
        self.test_endpoint("INFO", "GET", "/api/overview", notes="Visão geral da API")
    
    def generate_report(self):
        """Gerar relatório completo dos testes"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Estatísticas
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r['success']])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Agrupar por categoria
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'success': 0, 'failed': 0, 'tests': []}
            categories[cat]['total'] += 1
            categories[cat]['tests'].append(result)
            if result['success']:
                categories[cat]['success'] += 1
            else:
                categories[cat]['failed'] += 1
        
        # Criar relatório detalhado
        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        report_file = f"{OUTPUT_DIR}/ivo_v2_test_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# IVO V2 - Relatório de Testes Completo\n\n")
            f.write(f"**Data:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Duração:** {duration}\n")
            f.write(f"**Base URL:** {BASE_URL}\n\n")
            
            f.write("## 📊 Resumo Executivo\n\n")
            f.write(f"- **Total de Testes:** {total_tests}\n")
            f.write(f"- **Sucessos:** {successful_tests} (✅ {success_rate:.1f}%)\n")
            f.write(f"- **Falhas:** {failed_tests} (❌ {100-success_rate:.1f}%)\n\n")
            
            f.write("## 📈 Por Categoria\n\n")
            for cat, stats in categories.items():
                rate = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
                f.write(f"### {cat}\n")
                f.write(f"- Total: {stats['total']} | Sucessos: {stats['success']} | Falhas: {stats['failed']} | Taxa: {rate:.1f}%\n\n")
            
            f.write("## 📋 Detalhes dos Testes\n\n")
            for cat, stats in categories.items():
                f.write(f"### {cat}\n\n")
                f.write("| Endpoint | Método | Status | Tempo | Resultado | Erro |\n")
                f.write("|----------|--------|--------|-------|-----------|------|\n")
                
                for test in stats['tests']:
                    status_icon = "✅" if test['success'] else "❌"
                    endpoint = test['endpoint']
                    method = test['method']
                    status_code = test['status_code']
                    time_ms = test['execution_time_ms']
                    error = test['error'] or '-'
                    
                    f.write(f"| `{endpoint}` | {method} | {status_code} | {time_ms}ms | {status_icon} | {error} |\n")
                
                f.write("\n")
            
            f.write("## 🔍 IDs Gerados\n\n")
            f.write("Durante os testes, os seguintes IDs foram criados:\n\n")
            for key, value in self.test_ids.items():
                f.write(f"- **{key}:** `{value}`\n")
            
            f.write("\n## 📝 Observações\n\n")
            f.write("- Testes executados na ordem hierárquica: Course → Book → Unit → Content\n")
            f.write("- IDs criados são reutilizados em testes dependentes\n")
            f.write("- Falhas podem ser devido a dependências não atendidas\n")
            f.write(f"- Autenticação configurada: {'✅ Sim' if self.auth_setup_completed else '❌ Não'}\n")
            f.write(f"- Token Bearer usado: {self.bearer_token[:20] + '...' if self.bearer_token else 'Nenhum'}\n")
            f.write("- Todos endpoints /api/v2/* requerem autenticação Bearer\n")
        
        # Relatório JSON para processamento programático
        json_file = f"{OUTPUT_DIR}/ivo_v2_test_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': self.start_time.isoformat(),
                    'duration_seconds': duration.total_seconds(),
                    'base_url': BASE_URL,
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'failed_tests': failed_tests,
                    'success_rate': success_rate
                },
                'test_ids': self.test_ids,
                'categories': categories,
                'results': self.results
            }, f, indent=2, ensure_ascii=False)
        
        # Relatório resumido no console
        print(f"\n📊 RELATÓRIO FINAL")
        print(f"Total: {total_tests} | Sucessos: {successful_tests} | Falhas: {failed_tests}")
        print(f"Taxa de Sucesso: {success_rate:.1f}%")
        print(f"Duração: {duration}")
        print(f"\n📁 Relatórios salvos:")
        print(f"  - Markdown: {report_file}")
        print(f"  - JSON: {json_file}")
        
        if failed_tests > 0:
            print(f"\n❌ FALHAS DETECTADAS:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['method']} {result['endpoint']} ({result['status_code']}) - {result['error']}")

def main():
    """Função principal"""
    print("🧪 IVO V2 - Script de Testes Completo")
    print("=====================================")
    
    # Verificar se a API está rodando
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ API acessível em {BASE_URL}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Erro: API não está acessível em {BASE_URL}")
        print("Certifique-se que o container Docker está rodando:")
        print("  docker-compose up")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)
    
    # Executar testes
    tester = EndpointTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()