#!/usr/bin/env python3
"""
Teste Interativo Completo de Unidade - IVO V2
Permite configurar e gerar uma unidade completa com todos os componentes.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
BASE_URL = "http://localhost:8000"
RESULTS_DIR = "interactive_unit_results"

class InteractiveUnitTester:
    """Tester interativo para criação completa de unidade."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.unit_config = {}
        self.generated_content = {}
        self.errors = []
        
        # Criar diretório de resultados
        os.makedirs(RESULTS_DIR, exist_ok=True)
        
        # Autenticação
        self.session = requests.Session()
        self.bearer_token = None
        self.auth_setup_completed = False
        
        # A autenticação será configurada interativamente
    
    def collect_user_input(self):
        """Coletar configurações da unidade do usuário."""
        print("🎯 IVO V2 - Gerador Interativo de Unidade Completa")
        print("=" * 60)
        print("Vamos configurar sua unidade passo a passo...\n")
        
        # 0. CONFIGURAÇÃO DE AUTENTICAÇÃO INTERATIVA
        if not self._interactive_auth_setup():
            return False
        
        print("\n" + "=" * 60)
        print("📝 CONFIGURAÇÃO DA UNIDADE")
        print("=" * 60)
        
        # 1. Informações básicas da unidade
        print("📝 INFORMAÇÕES BÁSICAS DA UNIDADE:")
        self.unit_config['unit_name'] = input("Nome da unidade: ")
        self.unit_config['context'] = input("Contexto da unidade (ex: Airport check-in procedures): ")
        
        # 2. Nível e variante
        print(f"\n📊 CONFIGURAÇÕES PEDAGÓGICAS:")
        print("Níveis CEFR disponíveis: A1, A2, B1, B2, C1, C2")
        self.unit_config['cefr_level'] = input("Nível CEFR: ").upper()
        
        print("Variantes disponíveis: american_english, british_english")
        self.unit_config['language_variant'] = input("Variante do idioma: ").lower()
        
        print("Tipos de unidade: lexical_unit, grammar_unit")
        self.unit_config['unit_type'] = input("Tipo de unidade: ").lower()
        
        # 3. IDs de hierarquia
        print(f"\n🏗️ CONFIGURAÇÕES DE HIERARQUIA:")
        self.unit_config['course_id'] = input("ID do Course (deixe vazio para usar padrão): ") or "course_5e19fe18_c172_4f43_9c0a_202293325115"
        self.unit_config['book_id'] = input("ID do Book (deixe vazio para usar padrão): ") or "book_2762e908_39a5_470b_8668_3b0f4026f2c1"
        
        # 4. Configurações de conteúdo
        print(f"\n⚙️ CONFIGURAÇÕES DE GERAÇÃO:")
        
        # Vocabulário
        print("VOCABULÁRIO:")
        vocab_count = input("  Quantidade de palavras (5-50, padrão: 15): ")
        self.unit_config['vocab_count'] = int(vocab_count) if vocab_count else 15
        
        vocab_difficulty = input("  Dificuldade (beginner/intermediate/advanced, padrão: intermediate): ")
        self.unit_config['vocab_difficulty'] = vocab_difficulty or "intermediate"
        
        # Sentences
        print("SENTENÇAS:")
        sentences_count = input("  Quantidade de sentenças (3-20, padrão: 10): ")
        self.unit_config['sentences_count'] = int(sentences_count) if sentences_count else 10
        
        sentences_complexity = input("  Complexidade (simple/intermediate/complex, padrão: simple): ")
        self.unit_config['sentences_complexity'] = sentences_complexity or "simple"
        
        # Tips
        print("TIPS:")
        tips_count = input("  Quantidade de estratégias (1-6, padrão: 2): ")
        self.unit_config['tips_count'] = int(tips_count) if tips_count else 2
        
        # Q&A
        print("Q&A:")
        qa_count = input("  Quantidade de perguntas (2-15, padrão: 8): ")
        self.unit_config['qa_count'] = int(qa_count) if qa_count else 8
        
        # Assessments
        print("ASSESSMENTS:")
        assessments_count = input("  Quantidade de atividades (1-5, padrão: 3): ")
        self.unit_config['assessments_count'] = int(assessments_count) if assessments_count else 3
        
        # 5. Opções avançadas
        print(f"\n🔧 OPÇÕES AVANÇADAS:")
        
        use_image = input("Incluir imagem fake para teste? (s/n, padrão: n): ").lower() == 's'
        self.unit_config['use_image'] = use_image
        
        use_webhooks = input("Usar processamento assíncrono com webhooks? (s/n, padrão: n): ").lower() == 's'
        self.unit_config['use_webhooks'] = use_webhooks
        
        if use_webhooks:
            webhook_url = input("  URL do webhook (padrão: http://localhost:3001/webhook): ")
            self.unit_config['webhook_url'] = webhook_url or "http://localhost:3001/webhook"
        
        include_aim_detector = input("Incluir análise de AIM Detector? (s/n, padrão: s): ").lower() != 'n'
        self.unit_config['include_aim_detector'] = include_aim_detector
        
        include_l1_interference = input("Incluir análise de L1 Interference? (s/n, padrão: s): ").lower() != 'n'
        self.unit_config['include_l1_interference'] = include_l1_interference
        
        # Confirmação
        print(f"\n📋 CONFIGURAÇÃO FINAL:")
        print(f"Unidade: {self.unit_config['unit_name']}")
        print(f"Contexto: {self.unit_config['context']}")
        print(f"Nível: {self.unit_config['cefr_level']} | Variante: {self.unit_config['language_variant']}")
        print(f"Tipo: {self.unit_config['unit_type']}")
        print(f"Conteúdo: {self.unit_config['vocab_count']} palavras, {self.unit_config['sentences_count']} sentenças")
        print(f"Com imagem: {'Sim' if self.unit_config['use_image'] else 'Não'}")
        print(f"Webhooks: {'Sim' if self.unit_config['use_webhooks'] else 'Não'}")
        print(f"AIM Detector: {'Sim' if self.unit_config['include_aim_detector'] else 'Não'}")
        print(f"L1 Interference: {'Sim' if self.unit_config['include_l1_interference'] else 'Não'}")
        
        confirm = input(f"\n✅ Confirma a criação da unidade? (s/n): ").lower()
        if confirm != 's':
            print("❌ Operação cancelada pelo usuário.")
            return False
        
        return True
    
    def _setup_authentication(self):
        """Configuração inicial automática - será substituída pela interativa"""
        # Esta será chamada pela versão interativa
        return False
    
    def _interactive_auth_setup(self):
        """Configuração de autenticação INTERATIVA"""
        print("🔐 CONFIGURAÇÃO DE AUTENTICAÇÃO")
        print("=" * 50)
        print("Escolha como você quer se autenticar:")
        print("1. 🔧 Usar token de desenvolvimento (padrão)")
        print("2. 🔑 Fazer login com seu token IVO existente") 
        print("3. 👤 Criar novo usuário + token")
        print("4. ⚠️  Pular autenticação (só endpoints públicos)")
        
        escolha = input("\nEscolha (1-4, padrão: 1): ").strip() or "1"
        
        if escolha == "1":
            return self._auth_with_dev_token()
        elif escolha == "2":
            return self._auth_with_custom_token()
        elif escolha == "3":
            return self._auth_with_new_user()
        elif escolha == "4":
            print("⚠️  Pulando autenticação - apenas endpoints públicos funcionarão")
            return True
        else:
            print("❌ Opção inválida, usando token de desenvolvimento")
            return self._auth_with_dev_token()
    
    def _auth_with_dev_token(self):
        """Autenticar com token de desenvolvimento"""
        print("\n🔧 Usando token de desenvolvimento...")
        test_token = os.getenv("TEST_API_KEY_IVO", "ivo_test_token_dev_only_remove_in_prod")
        return self._do_login(test_token, "desenvolvimento")
    
    def _auth_with_custom_token(self):
        """Autenticar com token IVO fornecido pelo usuário"""
        print("\n🔑 Login com token IVO existente:")
        token_ivo = input("Digite seu token IVO: ").strip()
        
        if not token_ivo:
            print("❌ Token não fornecido, usando token de desenvolvimento")
            return self._auth_with_dev_token()
        
        return self._do_login(token_ivo, "customizado")
    
    def _auth_with_new_user(self):
        """Criar novo usuário e usar token gerado"""
        print("\n👤 Criação de novo usuário:")
        email = input("Email para o novo usuário: ").strip()
        
        if not email:
            print("❌ Email não fornecido, usando token de desenvolvimento")
            return self._auth_with_dev_token()
        
        phone = input("Telefone (opcional): ").strip() or None
        
        try:
            # Criar usuário
            user_data = {
                "email": email,
                "phone": phone,
                "metadata": {"source": "interactive_test", "created_by": "test_script"}
            }
            
            print("  🔄 Criando usuário...")
            response = self.session.post(f"{self.base_url}/api/auth/create-user", json=user_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                bearer_token = result.get("token_info", {}).get("access_token")
                user_id = result.get("user", {}).get("id")
                
                if bearer_token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {bearer_token}'
                    })
                    self.auth_setup_completed = True
                    self.bearer_token = bearer_token
                    
                    print(f"  ✅ Usuário criado com sucesso!")
                    print(f"  👤 User ID: {user_id}")
                    print(f"  🔑 Token Bearer: {bearer_token[:20]}...")
                    return True
            
            print(f"  ❌ Falha ao criar usuário: {response.status_code}")
            print(f"  📝 Response: {response.text[:200]}...")
            print("  🔧 Fallback: usando token de desenvolvimento")
            return self._auth_with_dev_token()
            
        except Exception as e:
            print(f"  ❌ Erro ao criar usuário: {str(e)}")
            print("  🔧 Fallback: usando token de desenvolvimento")
            return self._auth_with_dev_token()
    
    def _do_login(self, token_ivo: str, token_type: str):
        """Executar login com token IVO"""
        try:
            auth_data = {"api_key_ivo": token_ivo}
            
            print(f"  🔄 Fazendo login com token {token_type}...")
            response = self.session.post(f"{self.base_url}/api/auth/login", json=auth_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.bearer_token = data.get('access_token')
                if self.bearer_token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.bearer_token}'
                    })
                    self.auth_setup_completed = True
                    print(f"  ✅ Login realizado com sucesso!")
                    print(f"  🔑 Token Bearer: {self.bearer_token[:20]}...")
                    return True
            
            print(f"  ❌ Falha no login: {response.status_code}")
            print(f"  📝 Response: {response.text[:200]}...")
            return False
            
        except Exception as e:
            print(f"  ❌ Erro no login: {str(e)}")
            return False
    
    def create_unit(self) -> Optional[str]:
        """Criar a unidade com as configurações especificadas."""
        print(f"\n🏗️ CRIANDO UNIDADE...")
        
        book_id = self.unit_config['book_id']
        
        # Dados da unidade
        unit_data = {
            'context': self.unit_config['context'],
            'cefr_level': self.unit_config['cefr_level'],
            'language_variant': self.unit_config['language_variant'],
            'unit_type': self.unit_config['unit_type']
        }
        
        try:
            url = f"{self.base_url}/api/v2/books/{book_id}/units"
            
            # Criar imagem fake se solicitado
            files = None
            if self.unit_config['use_image']:
                print("  📸 Adicionando imagem fake...")
                fake_image_data = b'\\x89PNG\\r\\n\\x1a\\n\\x00\\x00\\x00\\rIHDR\\x00\\x00\\x00\\x20\\x00\\x00\\x00\\x20\\x08\\x02\\x00\\x00\\x00\\xfc\\x18\\xed\\xa3\\x00\\x00\\x00\\x12IDATx\\x9cc\\xf8\\x0f\\x00\\x00\\x00\\x00\\x01\\x00\\x01IEND\\xaeB`\\x82'
                files = {'image_1': ('unit_image.png', fake_image_data, 'image/png')}
            
            # Fazer requisição usando sessão autenticada
            if files:
                response = self.session.post(url, data=unit_data, files=files, timeout=120)
            else:
                response = self.session.post(url, data=unit_data, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('data', {}).get('unit', {}).get('id'):
                    unit_id = result['data']['unit']['id']
                    print(f"  ✅ Unidade criada: {unit_id}")
                    return unit_id
                else:
                    print(f"  ❌ Resposta inválida: {result}")
                    return None
            else:
                print(f"  ❌ Erro HTTP {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"  ❌ Erro na criação: {str(e)}")
            return None
    
    def generate_content(self, unit_id: str):
        """Gerar todo o conteúdo da unidade."""
        print(f"\n🔄 GERANDO CONTEÚDO COMPLETO...")
        
        # 1. Vocabulário
        print("  📚 Gerando vocabulário...")
        vocab_data = {
            "target_count": self.unit_config['vocab_count'],
            "difficulty_level": self.unit_config['vocab_difficulty'],
            "ipa_variant": "general_american",
            "include_alternative_pronunciations": False
        }
        
        if self.unit_config['use_webhooks']:
            vocab_data["webhook_url"] = self.unit_config['webhook_url']
        
        vocab_result = self._make_request("POST", f"/api/v2/units/{unit_id}/vocabulary", vocab_data)
        self.generated_content['vocabulary'] = vocab_result
        
        # Aguardar processamento se síncrono
        if not self.unit_config['use_webhooks']:
            time.sleep(2)
        
        # 2. Sentences
        print("  📝 Gerando sentenças...")
        sentences_data = {
            "target_count": self.unit_config['sentences_count'],
            "complexity_level": self.unit_config['sentences_complexity'],
            "connect_to_vocabulary": True
        }
        
        if self.unit_config['use_webhooks']:
            sentences_data["webhook_url"] = self.unit_config['webhook_url']
        
        sentences_result = self._make_request("POST", f"/api/v2/units/{unit_id}/sentences", sentences_data)
        self.generated_content['sentences'] = sentences_result
        
        if not self.unit_config['use_webhooks']:
            time.sleep(2)
        
        # 3. Tips (apenas para lexical_unit)
        if self.unit_config['unit_type'] == 'lexical_unit':
            print("  💡 Gerando estratégias TIPS...")
            tips_data = {
                "strategy_count": self.unit_config['tips_count'],
                "focus_type": "vocabulary",
                "include_l1_warnings": True
            }
            
            if self.unit_config['use_webhooks']:
                tips_data["webhook_url"] = self.unit_config['webhook_url']
            
            tips_result = self._make_request("POST", f"/api/v2/units/{unit_id}/tips", tips_data)
            self.generated_content['tips'] = tips_result
            
            if not self.unit_config['use_webhooks']:
                time.sleep(2)
        
        # 4. Grammar (apenas para grammar_unit)
        if self.unit_config['unit_type'] == 'grammar_unit':
            print("  📚 Gerando estratégias GRAMMAR...")
            grammar_data = {
                "strategy_count": 2,
                "grammar_focus": "unit_based",
                "connect_to_vocabulary": True
            }
            
            if self.unit_config['use_webhooks']:
                grammar_data["webhook_url"] = self.unit_config['webhook_url']
            
            grammar_result = self._make_request("POST", f"/api/v2/units/{unit_id}/grammar", grammar_data)
            self.generated_content['grammar'] = grammar_result
            
            if not self.unit_config['use_webhooks']:
                time.sleep(2)
        
        # 5. Q&A
        print("  ❓ Gerando perguntas e respostas...")
        qa_data = {
            "target_count": self.unit_config['qa_count'],
            "bloom_levels": ["remember", "understand", "apply"],
            "difficulty_progression": True
        }
        
        if self.unit_config['use_webhooks']:
            qa_data["webhook_url"] = self.unit_config['webhook_url']
        
        qa_result = self._make_request("POST", f"/api/v2/units/{unit_id}/qa", qa_data)
        self.generated_content['qa'] = qa_result
        
        if not self.unit_config['use_webhooks']:
            time.sleep(2)
        
        # 6. Assessments
        print("  📝 Gerando atividades de avaliação...")
        assessments_data = {
            "assessment_count": self.unit_config['assessments_count'],
            "difficulty_distribution": "balanced",
            "connect_to_content": True
        }
        
        if self.unit_config['use_webhooks']:
            assessments_data["webhook_url"] = self.unit_config['webhook_url']
        
        assessments_result = self._make_request("POST", f"/api/v2/units/{unit_id}/assessments", assessments_data)
        self.generated_content['assessments'] = assessments_result
        
        # 7. AIM Detector (se solicitado)
        if self.unit_config['include_aim_detector']:
            print("  🎯 Executando AIM Detector...")
            aim_result = self._make_request("GET", f"/api/v2/units/{unit_id}/aims")
            self.generated_content['aim_detector'] = aim_result
        
        # 8. L1 Interference (se solicitado)  
        if self.unit_config['include_l1_interference']:
            print("  🔍 Analisando L1 Interference...")
            l1_result = self._make_request("GET", f"/api/v2/units/{unit_id}/l1-interference")
            self.generated_content['l1_interference'] = l1_result
        
        # 9. Conteúdo completo final
        print("  📋 Coletando conteúdo completo...")
        complete_result = self._make_request("GET", f"/api/v2/units/{unit_id}/complete-content")
        self.generated_content['complete_content'] = complete_result
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Fazer requisição HTTP com tratamento de erro."""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = self.session.get(url, timeout=300)  # 5 minutos
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=300)
            else:
                print(f"    ❌ Método {method} não suportado")
                return None
            
            if response.status_code == 200:
                result = response.json()
                print(f"    ✅ {endpoint.split('/')[-1]} - OK")
                return result
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"    ❌ {endpoint.split('/')[-1]} - {error_msg}")
                self.errors.append(f"{endpoint}: {error_msg}")
                return None
                
        except Exception as e:
            error_msg = str(e)
            print(f"    ❌ {endpoint.split('/')[-1]} - Exceção: {error_msg}")
            self.errors.append(f"{endpoint}: {error_msg}")
            return None
    
    def generate_document(self, unit_id: str):
        """Gerar documento final com todo o conteúdo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unit_name_safe = "".join(c for c in self.unit_config['unit_name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Arquivo Markdown
        md_filename = f"{RESULTS_DIR}/unit_{unit_name_safe}_{timestamp}.md"
        
        # Arquivo JSON
        json_filename = f"{RESULTS_DIR}/unit_{unit_name_safe}_{timestamp}.json"
        
        # Gerar conteúdo Markdown
        md_content = self._generate_markdown_content(unit_id)
        
        # Gerar conteúdo JSON
        json_content = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "unit_id": unit_id,
                "configuration": self.unit_config,
                "errors": self.errors
            },
            "generated_content": self.generated_content
        }
        
        # Salvar arquivos
        try:
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=2, ensure_ascii=False)
            
            print(f"\n📁 DOCUMENTOS GERADOS:")
            print(f"  📄 Markdown: {md_filename}")
            print(f"  📄 JSON: {json_filename}")
            
            return md_filename, json_filename
            
        except Exception as e:
            print(f"  ❌ Erro ao salvar arquivos: {str(e)}")
            return None, None
    
    def _generate_markdown_content(self, unit_id: str) -> str:
        """Gerar conteúdo em Markdown."""
        md = f"""# {self.unit_config['unit_name']}

**Data de Geração:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Unit ID:** `{unit_id}`

## 📋 Configuração da Unidade

| Campo | Valor |
|-------|--------|
| **Nome** | {self.unit_config['unit_name']} |
| **Contexto** | {self.unit_config['context']} |
| **Nível CEFR** | {self.unit_config['cefr_level']} |
| **Variante** | {self.unit_config['language_variant']} |
| **Tipo** | {self.unit_config['unit_type']} |
| **Course ID** | `{self.unit_config['course_id']}` |
| **Book ID** | `{self.unit_config['book_id']}` |

## ⚙️ Configurações de Geração

| Componente | Configuração |
|------------|--------------|
| **Vocabulário** | {self.unit_config['vocab_count']} palavras ({self.unit_config['vocab_difficulty']}) |
| **Sentenças** | {self.unit_config['sentences_count']} sentenças ({self.unit_config['sentences_complexity']}) |
| **Tips** | {self.unit_config['tips_count']} estratégias |
| **Q&A** | {self.unit_config['qa_count']} perguntas |
| **Assessments** | {self.unit_config['assessments_count']} atividades |
| **Com Imagem** | {'Sim' if self.unit_config['use_image'] else 'Não'} |
| **Webhooks** | {'Sim' if self.unit_config['use_webhooks'] else 'Não'} |
| **AIM Detector** | {'Sim' if self.unit_config['include_aim_detector'] else 'Não'} |
| **L1 Interference** | {'Sim' if self.unit_config['include_l1_interference'] else 'Não'} |

---

"""

        # Adicionar cada seção de conteúdo
        for content_type, content_data in self.generated_content.items():
            if content_data and content_data.get('success'):
                md += self._format_content_section(content_type, content_data)
        
        # Adicionar erros se houver
        if self.errors:
            md += f"""## ❌ Erros Encontrados

{len(self.errors)} erro(s) durante a geração:

"""
            for i, error in enumerate(self.errors, 1):
                md += f"{i}. {error}\n"
        
        md += f"""

---

**Gerado por:** IVO V2 - Interactive Unit Tester  
**Timestamp:** {datetime.now().isoformat()}  
**Base URL:** {self.base_url}
"""
        
        return md
    
    def _format_content_section(self, content_type: str, content_data: Dict) -> str:
        """Formatar uma seção de conteúdo para Markdown."""
        
        # Títulos das seções
        titles = {
            'vocabulary': '📚 Vocabulário',
            'sentences': '📝 Sentenças',
            'tips': '💡 Estratégias TIPS',
            'grammar': '📚 Estratégias GRAMMAR',
            'qa': '❓ Perguntas e Respostas',
            'assessments': '📝 Atividades de Avaliação',
            'aim_detector': '🎯 AIM Detector',
            'l1_interference': '🔍 L1 Interference',
            'complete_content': '📋 Conteúdo Completo'
        }
        
        title = titles.get(content_type, content_type.title())
        md = f"## {title}\n\n"
        
        try:
            data = content_data.get('data', {})
            
            if content_type == 'vocabulary':
                vocab_data = data.get('vocabulary', {})
                items = vocab_data.get('items', [])
                
                md += f"**Total de palavras:** {len(items)}\n\n"
                
                if items:
                    md += "| Palavra | Fonema | Definição | Exemplo |\n"
                    md += "|---------|--------|-----------|----------|\n"
                    
                    for item in items[:10]:  # Limitar a 10 para não ficar muito longo
                        word = item.get('word', 'N/A')
                        phoneme = item.get('phoneme', 'N/A')
                        definition = item.get('definition', 'N/A')[:50] + '...' if len(item.get('definition', '')) > 50 else item.get('definition', 'N/A')
                        example = item.get('example', 'N/A')[:80] + '...' if len(item.get('example', '')) > 80 else item.get('example', 'N/A')
                        
                        md += f"| {word} | {phoneme} | {definition} | {example} |\n"
            
            elif content_type == 'sentences':
                sentences_data = data.get('sentences', {})
                sentences = sentences_data.get('sentences', [])
                
                md += f"**Total de sentenças:** {len(sentences)}\n\n"
                
                for i, sentence in enumerate(sentences, 1):
                    if isinstance(sentence, dict):
                        text = sentence.get('sentence', sentence.get('text', 'N/A'))
                        translation = sentence.get('translation', '')
                        md += f"{i}. **{text}**\n"
                        if translation:
                            md += f"   *Tradução: {translation}*\n"
                    else:
                        md += f"{i}. {sentence}\n"
                    md += "\n"
            
            elif content_type in ['tips', 'grammar']:
                strategy_data = data.get('tips' if content_type == 'tips' else 'grammar', {})
                
                md += f"**Estratégia:** {strategy_data.get('strategy', 'N/A')}\n"
                md += f"**Título:** {strategy_data.get('title', 'N/A')}\n\n"
                
                explanation = strategy_data.get('explanation', 'N/A')
                md += f"**Explicação:**\n{explanation}\n\n"
                
                examples = strategy_data.get('examples', [])
                if examples:
                    md += "**Exemplos:**\n"
                    for i, example in enumerate(examples, 1):
                        md += f"{i}. {example}\n"
                    md += "\n"
            
            elif content_type == 'qa':
                qa_data = data.get('qa', {})
                questions = qa_data.get('questions', [])
                
                md += f"**Total de perguntas:** {len(questions)}\n\n"
                
                for i, qa_item in enumerate(questions, 1):
                    question = qa_item.get('question', 'N/A')
                    answer = qa_item.get('answer', 'N/A')
                    
                    md += f"### Pergunta {i}\n"
                    md += f"**P:** {question}\n"
                    md += f"**R:** {answer}\n\n"
            
            elif content_type == 'assessments':
                assessments_data = data.get('assessments', {})
                activities = assessments_data.get('activities', [])
                
                md += f"**Total de atividades:** {len(activities)}\n\n"
                
                for i, activity in enumerate(activities, 1):
                    title = activity.get('title', f'Atividade {i}')
                    activity_type = activity.get('type', 'N/A')
                    instructions = activity.get('instructions', 'N/A')
                    
                    md += f"### {title}\n"
                    md += f"**Tipo:** {activity_type}\n"
                    md += f"**Instruções:** {instructions}\n\n"
            
            elif content_type == 'aim_detector':
                aims = data.get('detected_aims', [])
                md += f"**Objetivos detectados:** {len(aims)}\n\n"
                
                for aim in aims:
                    if isinstance(aim, dict):
                        aim_type = aim.get('type', 'N/A')
                        description = aim.get('description', 'N/A')
                        confidence = aim.get('confidence', 0)
                        md += f"- **{aim_type}** (confiança: {confidence:.2f}): {description}\n"
                    else:
                        md += f"- {aim}\n"
            
            elif content_type == 'l1_interference':
                interferences = data.get('interferences', [])
                md += f"**Interferências L1 detectadas:** {len(interferences)}\n\n"
                
                for interference in interferences:
                    if isinstance(interference, dict):
                        area = interference.get('area', 'N/A')
                        description = interference.get('description', 'N/A')
                        severity = interference.get('severity', 'N/A')
                        md += f"- **{area}** (severidade: {severity}): {description}\n"
                    else:
                        md += f"- {interference}\n"
            
            else:
                # Formato genérico para outros tipos
                md += f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```\n"
            
        except Exception as e:
            md += f"❌ Erro ao formatar seção: {str(e)}\n"
            md += f"```json\n{json.dumps(content_data, indent=2, ensure_ascii=False)}\n```\n"
        
        md += "\n---\n\n"
        return md
    
    def run_interactive_test(self):
        """Executar teste interativo completo."""
        try:
            # 1. Coletar configurações do usuário
            if not self.collect_user_input():
                return
            
            print(f"\n🚀 INICIANDO GERAÇÃO DA UNIDADE COMPLETA...")
            print(f"🔐 Autenticação: {'Configurada' if self.auth_setup_completed else 'Falha'}")
            if self.bearer_token:
                print(f"🔑 Token: {self.bearer_token[:20]}...")
            start_time = datetime.now()
            
            # 2. Criar unidade
            unit_id = self.create_unit()
            if not unit_id:
                print("❌ Falha na criação da unidade. Abortando.")
                return
            
            # 3. Gerar todo o conteúdo
            self.generate_content(unit_id)
            
            # 4. Gerar documento final
            md_file, json_file = self.generate_document(unit_id)
            
            # 5. Relatório final
            duration = datetime.now() - start_time
            success_count = len([c for c in self.generated_content.values() if c and c.get('success')])
            total_count = len(self.generated_content)
            
            print(f"\n🏁 GERAÇÃO COMPLETA FINALIZADA!")
            print(f"⏱️  Duração: {duration}")
            print(f"📊 Sucessos: {success_count}/{total_count}")
            print(f"🆔 Unit ID: {unit_id}")
            
            if self.errors:
                print(f"❌ Erros: {len(self.errors)}")
                for error in self.errors[:3]:  # Mostrar apenas os primeiros 3
                    print(f"  • {error}")
            
            if md_file:
                print(f"\n📄 Documento gerado: {md_file}")
                print(f"💾 Dados salvos: {json_file}")
            
            print(f"\n✨ Unidade '{self.unit_config['unit_name']}' criada com sucesso!")
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Operação interrompida pelo usuário.")
        except Exception as e:
            print(f"\n❌ Erro inesperado: {str(e)}")

def main():
    """Função principal."""
    print("🎆 IVO V2 - Interactive Unit Generator")
    print("=" * 50)
    
    # Verificar conectividade da API
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"❌ API não acessível em {BASE_URL}")
            return
        print(f"✅ API acessível em {BASE_URL}")
        print("🔐 Configurando autenticação...\n")
    except Exception as e:
        print(f"❌ Não foi possível conectar em {BASE_URL}: {str(e)}")
        return
    
    # Executar teste interativo
    tester = InteractiveUnitTester()
    tester.run_interactive_test()

if __name__ == "__main__":
    main()