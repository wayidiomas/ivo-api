#!/usr/bin/env python3
"""
Script de Teste para Pipeline Completo com Webhooks - IVO V2
Testa pipelines de geração com DUAS abordagens:
1. Pipeline SÍNCRONO (comportamento original)
2. Pipeline ASSÍNCRONO (usando webhooks)
"""

import requests
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
BASE_URL = "http://localhost:8000"
WEBHOOK_URL = "http://localhost:3001/webhook"
REPORTS_DIR = "webhook_test_reports"

# IDs base para teste
BASE_TEST_IDS = {
    "course_id": "course_5e19fe18_c172_4f43_9c0a_202293325115",
    "book_id": "book_2762e908_39a5_470b_8668_3b0f4026f2c1",
    "unit_sync": None,   # Unit para teste síncrono (será criada)
    "unit_async": None   # Unit para teste assíncrono (será criada)
}

class WebhookHandler(BaseHTTPRequestHandler):
    """Handler para receber webhooks durante os testes."""
    
    received_webhooks = []
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            webhook_data = json.loads(post_data.decode('utf-8'))
            
            # Armazenar webhook recebido
            webhook_entry = {
                "timestamp": datetime.now().isoformat(),
                "path": self.path,
                "headers": dict(self.headers),
                "data": webhook_data
            }
            
            WebhookHandler.received_webhooks.append(webhook_entry)
            
            # Log do webhook recebido
            task_id = webhook_data.get("task_id", "unknown")
            status = webhook_data.get("status", "unknown")
            success = webhook_data.get("success", False)
            
            print(f"    🔔 Webhook recebido: {task_id} - Status: {status} - Success: {success}")
            
            # Responder com 200 OK
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "received"}')
            
        except Exception as e:
            print(f"    ❌ Erro ao processar webhook: {str(e)}")
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suprimir logs do servidor HTTP
        pass

class WebhookPipelineTester:
    """Tester para pipeline com webhooks vs síncrono."""
    
    def __init__(self, base_url: str = BASE_URL, webhook_url: str = WEBHOOK_URL):
        self.base_url = base_url
        self.webhook_url = webhook_url
        self.results = {
            "sync": [],
            "async": []
        }
        self.webhook_tasks = {}
        self.test_ids = BASE_TEST_IDS.copy()
        
        # Criar diretório de reports
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        # Inicializar servidor webhook
        self.webhook_server = None
        self.webhook_thread = None
        
        # Autenticação
        self.session = requests.Session()
        self.bearer_token = None
        self.auth_setup_completed = False
        
        # Configurar autenticação automaticamente
        self._setup_authentication()
    
    def start_webhook_server(self):
        """Iniciar servidor webhook para receber callbacks."""
        print(f"🔔 Iniciando servidor webhook em {self.webhook_url}")
        
        parsed_url = urlparse(self.webhook_url)
        server_address = (parsed_url.hostname or 'localhost', parsed_url.port or 3001)
        
        try:
            self.webhook_server = HTTPServer(server_address, WebhookHandler)
            self.webhook_thread = threading.Thread(target=self.webhook_server.serve_forever, daemon=True)
            self.webhook_thread.start()
            
            # Aguardar um pouco para o servidor inicializar
            time.sleep(1)
            
            # Testar se o servidor está funcionando
            test_response = requests.get(f"http://{server_address[0]}:{server_address[1]}/test", timeout=2)
            print(f"    ✅ Servidor webhook ativo em {server_address[0]}:{server_address[1]}")
            return True
            
        except Exception as e:
            print(f"    ❌ Erro ao iniciar servidor webhook: {str(e)}")
            print(f"    ⚠️  Continuando sem servidor webhook local")
            return False
    
    def _setup_authentication(self):
        """Configurar autenticação usando token de desenvolvimento"""
        try:
            test_token = os.getenv("TEST_API_KEY_IVO", "ivo_test_token_dev_only_remove_in_prod")
            auth_data = {
                "api_key_ivo": test_token
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/login", json=auth_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.bearer_token = data.get('access_token')
                if self.bearer_token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.bearer_token}'
                    })
                    self.auth_setup_completed = True
                    print(f"🔐 Autenticação configurada: {self.bearer_token[:20]}...")
                    return True
            
            print(f"❌ Falha na autenticação: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Erro na configuração de auth: {str(e)}")
            return False
    
    def stop_webhook_server(self):
        """Parar servidor webhook."""
        if self.webhook_server:
            self.webhook_server.shutdown()
            print("    🔔 Servidor webhook finalizado")
    
    def create_test_units(self):
        """Criar units de teste para pipelines síncrono e assíncrono."""
        print(f"\n🏗️  CRIANDO UNITS DE TESTE")
        print("=" * 60)
        
        book_id = self.test_ids["book_id"]
        
        # Unit para pipeline SÍNCRONO
        sync_unit_data = {
            'context': 'Airport check-in and boarding procedures for international flights',
            'cefr_level': 'A2', 
            'language_variant': 'american_english',
            'unit_type': 'lexical_unit'
        }
        
        print("    📝 Criando unit para pipeline SÍNCRONO...")
        sync_result = self._create_unit(sync_unit_data, "SYNC")
        if sync_result:
            self.test_ids["unit_sync"] = sync_result
            print(f"    ✅ Unit síncrona criada: {sync_result}")
        else:
            print(f"    ❌ Falha ao criar unit síncrona")
            return False
        
        # Unit para pipeline ASSÍNCRONO
        async_unit_data = {
            'context': 'Shopping mall navigation and retail purchasing experience',
            'cefr_level': 'A2', 
            'language_variant': 'american_english',
            'unit_type': 'lexical_unit'
        }
        
        print("    🔄 Criando unit para pipeline ASSÍNCRONO...")
        async_result = self._create_unit(async_unit_data, "ASYNC")
        if async_result:
            self.test_ids["unit_async"] = async_result
            print(f"    ✅ Unit assíncrona criada: {async_result}")
        else:
            print(f"    ❌ Falha ao criar unit assíncrona")
            return False
        
        return True
    
    def _create_unit(self, unit_data: Dict, unit_type: str) -> Optional[str]:
        """Criar uma unit e retornar o ID."""
        book_id = self.test_ids["book_id"]
        
        try:
            url = f"{self.base_url}/api/v2/books/{book_id}/units"
            response = self.session.post(url, data=unit_data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result and result.get('success') and result.get('data', {}).get('unit', {}).get('id'):
                    return result['data']['unit']['id']
            
            print(f"    ❌ Erro ao criar unit {unit_type}: {response.status_code} - {response.text[:100]}")
            return None
            
        except Exception as e:
            print(f"    ❌ Exceção ao criar unit {unit_type}: {str(e)}")
            return None
    
    def run_sync_pipeline(self):
        """Executar pipeline completo SÍNCRONO."""
        print(f"\n⚡ PIPELINE SÍNCRONO")
        print("=" * 60)
        
        unit_id = self.test_ids["unit_sync"]
        if not unit_id:
            print("❌ Unit síncrona não disponível")
            return False
        
        print(f"    📝 Processando unit: {unit_id}")
        print(f"    🔄 Modo: SÍNCRONO (sem webhook_url)")
        
        # 1. Vocabulário
        vocab_data = {
            "target_count": 10,
            "difficulty_level": "intermediate"
        }
        
        vocab_start = time.time()
        vocab_result = self._test_sync_endpoint("vocabulary", unit_id, vocab_data)
        vocab_time = time.time() - vocab_start
        
        if not vocab_result:
            print("    ❌ Falha na geração de vocabulário síncrono")
            return False
        
        print(f"    ✅ Vocabulário gerado síncronamente em {vocab_time:.2f}s")
        
        # 2. Sentences
        sentences_data = {
            "target_count": 8,
            "complexity_level": "simple",
            "connect_to_vocabulary": True
        }
        
        sentences_start = time.time()
        sentences_result = self._test_sync_endpoint("sentences", unit_id, sentences_data)
        sentences_time = time.time() - sentences_start
        
        if not sentences_result:
            print("    ❌ Falha na geração de sentenças síncrono")
            return False
        
        print(f"    ✅ Sentenças geradas síncronamente em {sentences_time:.2f}s")
        
        # 3. Tips
        tips_data = {
            "strategy_count": 1,
            "focus_type": "vocabulary"
        }
        
        tips_start = time.time()
        tips_result = self._test_sync_endpoint("tips", unit_id, tips_data)
        tips_time = time.time() - tips_start
        
        if not tips_result:
            print("    ❌ Falha na geração de tips síncrono")
            return False
        
        print(f"    ✅ Tips gerados síncronamente em {tips_time:.2f}s")
        
        # 4. Q&A
        qa_data = {
            "target_count": 6,
            "bloom_levels": ["remember", "understand", "apply"]
        }
        
        qa_start = time.time()
        qa_result = self._test_sync_endpoint("qa", unit_id, qa_data)
        qa_time = time.time() - qa_start
        
        if not qa_result:
            print("    ❌ Falha na geração de Q&A síncrono")
            return False
        
        print(f"    ✅ Q&A gerado síncronamente em {qa_time:.2f}s")
        
        # 5. Assessments
        assessments_data = {
            "assessment_count": 2,
            "difficulty_distribution": "balanced"
        }
        
        assessments_start = time.time()
        assessments_result = self._test_sync_endpoint("assessments", unit_id, assessments_data)
        assessments_time = time.time() - assessments_start
        
        if not assessments_result:
            print("    ❌ Falha na geração de assessments síncrono")
            return False
        
        print(f"    ✅ Assessments gerados síncronamente em {assessments_time:.2f}s")
        
        total_time = vocab_time + sentences_time + tips_time + qa_time + assessments_time
        
        self.results["sync"] = {
            "unit_id": unit_id,
            "total_time": total_time,
            "steps": {
                "vocabulary": {"time": vocab_time, "success": True},
                "sentences": {"time": sentences_time, "success": True},
                "tips": {"time": tips_time, "success": True},
                "qa": {"time": qa_time, "success": True},
                "assessments": {"time": assessments_time, "success": True}
            },
            "completed": True
        }
        
        print(f"    🏁 Pipeline síncrono concluído em {total_time:.2f}s")
        return True
    
    def run_async_pipeline(self):
        """Executar pipeline completo ASSÍNCRONO com webhooks."""
        print(f"\n🔄 PIPELINE ASSÍNCRONO COM WEBHOOKS")
        print("=" * 60)
        
        unit_id = self.test_ids["unit_async"]
        if not unit_id:
            print("❌ Unit assíncrona não disponível")
            return False
        
        print(f"    📝 Processando unit: {unit_id}")
        print(f"    🔔 Modo: ASSÍNCRONO (com webhook_url: {self.webhook_url})")
        
        # Limpar webhooks recebidos
        WebhookHandler.received_webhooks = []
        
        # Dados base para todos os endpoints
        endpoints_data = {
            "vocabulary": {
                "webhook_url": self.webhook_url,
                "target_count": 10,
                "difficulty_level": "intermediate"
            },
            "sentences": {
                "webhook_url": self.webhook_url,
                "target_count": 8,
                "complexity_level": "simple",
                "connect_to_vocabulary": True
            },
            "tips": {
                "webhook_url": self.webhook_url,
                "strategy_count": 1,
                "focus_type": "vocabulary"
            },
            "qa": {
                "webhook_url": self.webhook_url,
                "target_count": 6,
                "bloom_levels": ["remember", "understand", "apply"]
            },
            "assessments": {
                "webhook_url": self.webhook_url,
                "assessment_count": 2,
                "difficulty_distribution": "balanced"
            }
        }
        
        # 1. Disparar todas as requisições assíncronas
        async_tasks = {}
        
        for endpoint, data in endpoints_data.items():
            task_result = self._test_async_endpoint(endpoint, unit_id, data)
            if task_result:
                task_id = task_result.get("task_id")
                async_tasks[endpoint] = {
                    "task_id": task_id,
                    "started_at": datetime.now(),
                    "completed": False
                }
                print(f"    🚀 {endpoint.upper()} disparado assíncronamente - Task ID: {task_id}")
            else:
                print(f"    ❌ Falha ao disparar {endpoint} assíncrono")
                return False
        
        print(f"\n    ⏳ Aguardando {len(async_tasks)} webhooks...")
        
        # 2. Aguardar todos os webhooks
        max_wait_time = 300  # 5 minutos
        wait_start = time.time()
        
        while time.time() - wait_start < max_wait_time:
            # Verificar webhooks recebidos
            completed_tasks = 0
            
            for webhook in WebhookHandler.received_webhooks:
                task_id = webhook["data"].get("task_id")
                
                # Encontrar endpoint correspondente
                for endpoint, task_info in async_tasks.items():
                    if task_info["task_id"] == task_id and not task_info["completed"]:
                        task_info["completed"] = True
                        task_info["completed_at"] = datetime.now()
                        task_info["webhook_data"] = webhook["data"]
                        
                        status = webhook["data"].get("status")
                        success = webhook["data"].get("success")
                        processing_time = webhook["data"].get("processing_time", 0)
                        
                        if success:
                            print(f"    ✅ {endpoint.upper()} concluído via webhook em {processing_time:.2f}s")
                        else:
                            print(f"    ❌ {endpoint.upper()} falhou via webhook: {webhook['data'].get('error', 'Erro desconhecido')}")
                        
                        break
            
            # Contar tarefas completadas
            completed_tasks = len([t for t in async_tasks.values() if t["completed"]])
            
            if completed_tasks == len(async_tasks):
                print(f"    🏁 Todos os {completed_tasks} webhooks recebidos!")
                break
            
            print(f"    ⏳ {completed_tasks}/{len(async_tasks)} webhooks recebidos... (aguardando {max_wait_time - (time.time() - wait_start):.0f}s)")
            time.sleep(5)
        
        # 3. Verificar resultados
        total_async_time = time.time() - wait_start
        all_completed = all(task["completed"] for task in async_tasks.values())
        
        if not all_completed:
            pending_tasks = [endpoint for endpoint, task in async_tasks.items() if not task["completed"]]
            print(f"    ⚠️  Timeout atingido. Tarefas pendentes: {pending_tasks}")
        
        self.results["async"] = {
            "unit_id": unit_id,
            "total_time": total_async_time,
            "steps": async_tasks,
            "completed": all_completed,
            "webhooks_received": len(WebhookHandler.received_webhooks),
            "webhook_data": WebhookHandler.received_webhooks.copy()
        }
        
        print(f"    🏁 Pipeline assíncrono {'concluído' if all_completed else 'parcialmente concluído'} em {total_async_time:.2f}s")
        return all_completed
    
    def _test_sync_endpoint(self, endpoint: str, unit_id: str, data: Dict) -> bool:
        """Testar endpoint de forma síncrona."""
        try:
            url = f"{self.base_url}/api/v2/units/{unit_id}/{endpoint}"
            response = self.session.post(url, json=data, timeout=300)  # 5 minutos timeout
            
            if response.status_code == 200:
                return True
            else:
                print(f"      ❌ Erro HTTP {response.status_code}: {response.text[:100]}")
                return False
                
        except Exception as e:
            print(f"      ❌ Exceção: {str(e)}")
            return False
    
    def _test_async_endpoint(self, endpoint: str, unit_id: str, data: Dict) -> Optional[Dict]:
        """Testar endpoint de forma assíncrona (com webhook_url)."""
        try:
            url = f"{self.base_url}/api/v2/units/{unit_id}/{endpoint}"
            response = self.session.post(url, json=data, timeout=30)  # Request rápida
            
            if response.status_code == 200:
                result = response.json()
                if result.get("async_processing") and result.get("task_id"):
                    return result
                else:
                    print(f"      ❌ Resposta não indica processamento assíncrono")
                    return None
            else:
                print(f"      ❌ Erro HTTP {response.status_code}: {response.text[:100]}")
                return None
                
        except Exception as e:
            print(f"      ❌ Exceção: {str(e)}")
            return None
    
    def compare_results(self):
        """Comparar resultados dos dois pipelines."""
        print(f"\n📊 COMPARAÇÃO DE RESULTADOS")
        print("=" * 60)
        
        sync_results = self.results["sync"]
        async_results = self.results["async"]
        
        if not sync_results or not async_results:
            print("❌ Não foi possível comparar - dados insuficientes")
            return
        
        sync_time = sync_results["total_time"]
        async_time = async_results["total_time"]
        
        print(f"📝 PIPELINE SÍNCRONO:")
        print(f"   • Tempo total: {sync_time:.2f}s")
        print(f"   • Passos executados: {len(sync_results['steps'])}")
        print(f"   • Status: {'✅ Completo' if sync_results['completed'] else '❌ Incompleto'}")
        
        for step, info in sync_results['steps'].items():
            print(f"     - {step}: {info['time']:.2f}s {'✅' if info['success'] else '❌'}")
        
        print(f"\n🔄 PIPELINE ASSÍNCRONO:")
        print(f"   • Tempo total de espera: {async_time:.2f}s")
        print(f"   • Passos disparados: {len(async_results['steps'])}")
        print(f"   • Webhooks recebidos: {async_results['webhooks_received']}")
        print(f"   • Status: {'✅ Completo' if async_results['completed'] else '❌ Incompleto'}")
        
        for step, info in async_results['steps'].items():
            if info['completed']:
                webhook_data = info['webhook_data']
                processing_time = webhook_data.get('processing_time', 0)
                success = webhook_data.get('success', False)
                print(f"     - {step}: {processing_time:.2f}s {'✅' if success else '❌'}")
            else:
                print(f"     - {step}: ⏳ Pendente")
        
        print(f"\n🎯 COMPARAÇÃO:")
        if async_results['completed'] and sync_results['completed']:
            if async_time < sync_time:
                improvement = sync_time - async_time
                print(f"   • Assíncrono foi {improvement:.2f}s mais rápido")
                print(f"   • Melhoria: {(improvement/sync_time)*100:.1f}%")
            else:
                slower = async_time - sync_time
                print(f"   • Assíncrono foi {slower:.2f}s mais lento (overhead de webhook)")
                print(f"   • Diferença: {(slower/sync_time)*100:.1f}%")
            
            print(f"   • Vantagem assíncrona: Não bloqueia a aplicação")
            print(f"   • Vantagem assíncrona: Permite processamento paralelo")
        else:
            print("   • Comparação não possível - pipelines incompletos")
    
    def generate_report(self):
        """Gerar relatório detalhado."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "webhook_url": self.webhook_url,
                "test_ids": self.test_ids
            },
            "sync_results": self.results["sync"],
            "async_results": self.results["async"]
        }
        
        # Salvar relatório JSON
        json_file = f"{REPORTS_DIR}/webhook_pipeline_test_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Relatório salvo: {json_file}")
        return json_file
    
    def run_complete_test(self):
        """Executar teste completo comparativo."""
        print("🧪 IVO V2 - Teste Comparativo Pipeline Webhook vs Síncrono")
        print("=" * 80)
        print(f"📍 Base URL: {self.base_url}")
        print(f"🔔 Webhook URL: {self.webhook_url}")
        print(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔐 Autenticação: {'Configurada' if self.auth_setup_completed else 'Falha'}")
        if self.bearer_token:
            print(f"🔑 Token: {self.bearer_token[:20]}...")
        print("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # 1. Iniciar servidor webhook
            webhook_ok = self.start_webhook_server()
            if not webhook_ok:
                print("⚠️  Continuando sem servidor webhook local")
            
            # 2. Criar units de teste
            if not self.create_test_units():
                print("❌ Erro crítico: Não foi possível criar units de teste")
                return
            
            # 3. Executar pipeline síncrono
            sync_success = self.run_sync_pipeline()
            
            # 4. Executar pipeline assíncrono
            async_success = self.run_async_pipeline()
            
            # 5. Comparar resultados
            self.compare_results()
            
            # 6. Gerar relatório
            self.generate_report()
            
            # Resumo final
            duration = datetime.now() - start_time
            
            print("=" * 80)
            print("🏁 TESTE COMPLETO FINALIZADO")
            print(f"⏱️  Duração: {duration}")
            print(f"📝 Pipeline Síncrono: {'✅ Sucesso' if sync_success else '❌ Falha'}")
            print(f"🔄 Pipeline Assíncrono: {'✅ Sucesso' if async_success else '❌ Falha'}")
            print("=" * 80)
            
        finally:
            # Limpar recursos
            self.stop_webhook_server()

def main():
    """Função principal."""
    print("🎆 IVO V2 - Webhook Pipeline Tester")
    print("=" * 50)
    
    # Verificar conectividade da API
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"❌ API não acessível em {BASE_URL}")
            return
        print(f"✅ API acessível em {BASE_URL}")
    except Exception as e:
        print(f"❌ Não foi possível conectar em {BASE_URL}: {str(e)}")
        return
    
    # Executar teste
    tester = WebhookPipelineTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main()