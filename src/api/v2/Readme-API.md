# API v2 - Sistema IVO de Geração de Conteúdo Pedagógico

Este diretório contém a implementação completa da API v2 do sistema IVO (Intelligent Vocabulary Organizer), um sistema hierárquico avançado para geração automatizada de apostilas de inglês com foco em aprendizes brasileiros.

## 🔐 Sistema de Autenticação Integrado

### 🛡️ Proteção Automática
**TODOS os endpoints `/api/v2/*` são protegidos automaticamente** pelo middleware Bearer token:
- ✅ **Middleware Transparente**: Validação automática sem modificação de código
- ✅ **Dupla Camada**: Token IVO → Login → Bearer Token → Acesso V2
- ✅ **Rate Limiting por Token**: Controle individualizado de uso
- ✅ **Audit Logging**: Rastreamento completo de ações

### 🔑 Fluxo de Autenticação
```
1. Token IVO fornecido → POST /api/auth/login
2. Recebe Bearer Token ← Resposta do login  
3. Bearer Token em Header → Authorization: Bearer <token>
4. Acesso liberado aos endpoints V2 ✅
```

## 🏗️ Arquitetura Hierárquica

O sistema segue uma estrutura hierárquica obrigatória:

```
Course → Book → Unit → Content (Vocabulary, Sentences, Strategies, Assessments)
```

### Componentes da Hierarquia

- **Course**: Curso completo com níveis CEFR e metodologia
- **Book**: Livros organizados por nível CEFR dentro do curso  
- **Unit**: Unidades sequenciais dentro do book (lexical_unit ou grammar_unit)
- **Content**: Conteúdo gerado automaticamente com IA

## 📁 Estrutura de Arquivos

### 🔐 Autenticação (Público)

#### **auth.py** - Sistema de Autenticação
**Endpoints PÚBLICOS (não requerem Bearer token):**
- `POST /api/auth/login` - Login com token IVO → Bearer token
- `POST /api/auth/create-user` - Criar usuário + tokens
- `GET /api/auth/validate-token` - Validar Bearer token atual

**Funcionalidades:**
- Sistema de dupla camada de tokens (IVO + Bearer)
- Validação de tokens com rate limiting específico
- Criação de usuários com metadados personalizáveis
- Integração com tabelas `ivo_users` e `ivo_api_tokens`
- Row Level Security (RLS) no banco de dados

**Rate Limits Específicos:**
- Login: 10 tentativas por minuto
- Criação de usuário: 3 por 5 minutos

### Endpoints Principais (🔒 Protegidos)

#### 🎯 **courses.py** - Gestão de Cursos
**Funcionalidades:**
- `POST /courses` - Criar curso com níveis CEFR e metodologia
- `GET /courses` - Listar cursos com paginação e filtros avançados
- `GET /courses/{id}` - Obter curso específico com estatísticas
- `GET /courses/{id}/hierarchy` - Visualizar hierarquia completa Course→Book→Unit
- `GET /courses/{id}/progress` - Análise pedagógica de progresso
- `PUT /courses/{id}` - Atualizar informações do curso
- `DELETE /courses/{id}` - Arquivamento seguro (não deleção física)

**🔒 Autenticação:** Todos endpoints requerem Bearer token

**Conecta-se com:**
- `hierarchical_database.py` - Operações de banco hierárquico
- `rate_limiter.py` - Controle de taxa de requisições
- `audit_logger.py` - Log de operações e auditoria
- `pagination.py` - Sistema de paginação avançada
- `auth_middleware.py` - Validação automática de tokens

#### 📚 **books.py** - Gestão de Books
**Funcionalidades:**
- `POST /courses/{course_id}/books` - Criar book em curso específico
- `GET /courses/{course_id}/books` - Listar books paginados com filtros
- `GET /books/{id}` - Obter book com unidades e estatísticas
- `GET /books/{id}/progression` - Análise de progressão pedagógica
- `PUT /books/{id}` - Atualizar informações do book
- `DELETE /books/{id}` - Arquivamento seguro

**🔒 Autenticação:** Todos endpoints requerem Bearer token

**Validações:**
- Nível CEFR do book deve estar nos níveis do curso
- Controle de sequenciamento automático
- Análise de progressão vocabular e estratégias

#### 🎓 **units.py** - Gestão de Unidades
**Funcionalidades:**
- `POST /books/{book_id}/units` - Criar unidade com imagens obrigatórias
- `GET /books/{book_id}/units` - Listar unidades paginadas
- `GET /units/{id}` - Obter unidade completa com contexto RAG
- `GET /units/{id}/context` - Contexto RAG detalhado para geração
- `GET /units/{id}/aims` - **NOVO:** Objetivos detectados automaticamente (AIM Detector)
- `PUT /units/{id}/status` - Controle de estado da unidade
- `PUT /units/{id}` - Atualizar metadados da unidade
- `DELETE /units/{id}` - Arquivamento com análise de impacto

**🔒 Autenticação:** Todos endpoints requerem Bearer token

**Estados da Unidade (Status Flow):**
```
creating → vocab_pending → sentences_pending → content_pending → assessments_pending → completed
```

**Validações:**
- Upload obrigatório de 1-2 imagens (máx 10MB cada)
- Validação hierárquica completa
- Análise de qualidade e progressão
- **AIM Detector automático** na criação (detecta objetivos pedagógicos)

### Geração de Conteúdo com IA (🔒 Protegidos)

#### 📝 **vocabulary.py** - Geração de Vocabulário
**Sistema RAG Inteligente:**
- Análise de imagens via OpenAI Vision (integrado)
- Prevenção de repetições com contexto histórico
- Geração de fonemas IPA automática
- 20-45 palavras por nível CEFR
- **Structured Output com LangChain 0.3** - Eliminação de falhas JSON

**Endpoints:**
- `POST /units/{id}/vocabulary` - Gerar vocabulário com RAG + Vision
- `GET /units/{id}/vocabulary` - Obter vocabulário com análises
- `PUT /units/{id}/vocabulary` - Edição manual validada
- `DELETE /units/{id}/vocabulary` - Remoção com atualização de status
- `GET /units/{id}/vocabulary/analysis` - Análise qualitativa completa

**🔒 Autenticação:** Todos endpoints requerem Bearer token

**Conecta-se com:**
- `VocabularyGeneratorService` - Service de geração IA
- `image_analysis_service.py` - Análise integrada (SEM MCP)
- Base RAG hierárquica para contexto

#### 📖 **sentences.py** - Geração de Sentences
**Funcionalidades:**
- Sentences conectadas ao vocabulário gerado
- Integração com palavras de reforço de unidades anteriores
- Análise de complexidade e adequação ao nível
- Coerência contextual baseada no tema da unidade
- **Structured Output** - Prevenção de falhas de parsing

**Endpoints:**
- `POST /units/{id}/sentences` - Gerar sentences conectadas
- `GET /units/{id}/sentences` - Obter sentences com análise
- `PUT /units/{id}/sentences` - Edição manual
- `DELETE /units/{id}/sentences` - Remoção com regressão de status
- `GET /units/{id}/sentences/analysis` - Análise qualitativa

**🔒 Autenticação:** Todos endpoints requerem Bearer token

#### 💡 **tips.py** - Estratégias TIPS (Unidades Lexicais)
**6 Estratégias Inteligentes:**
1. **Afixação** - Prefixos e sufixos
2. **Substantivos Compostos** - Agrupamento temático
3. **Colocações** - Combinações naturais
4. **Expressões Fixas** - Fórmulas cristalizadas
5. **Idiomas** - Expressões figurativas
6. **Chunks** - Blocos funcionais

**Seleção RAG:**
- Análise do vocabulário para detectar padrões
- Balanceamento baseado em estratégias já usadas
- Adequação ao nível CEFR
- Foco fonético e pronunciação
- **Structured Output com Enums** - Validação estrita de estratégias

**Endpoints:**
- `POST /units/{id}/tips` - Gerar estratégia TIPS inteligente
- `GET /units/{id}/tips` - Obter estratégia aplicada
- `PUT /units/{id}/tips` - Edição manual com validação
- `DELETE /units/{id}/tips` - Remoção com ajuste de status
- `GET /units/{id}/tips/analysis` - Análise pedagógica
- `GET /tips/strategies` - Informações sobre as 6 estratégias

**🔒 Autenticação:** Todos endpoints requerem Bearer token

#### 📐 **grammar.py** - Estratégias GRAMMAR (Unidades Gramaticais)
**2 Estratégias Especializadas:**
1. **Explicação Sistemática** - Apresentação organizada e dedutiva
2. **Prevenção de Erros L1→L2** - Análise contrastiva português-inglês

**Foco Brasileiro:**
- Interferência L1 (português) → L2 (inglês)
- Erros comuns de brasileiros
- Exercícios contrastivos específicos
- Análise de false friends e estruturas

**Endpoints:**
- `POST /units/{id}/grammar` - Gerar estratégia GRAMMAR
- `GET /units/{id}/grammar` - Obter estratégia aplicada
- `PUT /units/{id}/grammar` - Edição manual
- `DELETE /units/{id}/grammar` - Remoção
- `GET /units/{id}/grammar/analysis` - Análise L1→L2
- `GET /grammar/strategies` - Info sobre estratégias GRAMMAR

**🔒 Autenticação:** Todos endpoints requerem Bearer token

#### 🎯 **assessments.py** - Geração de Atividades
**7 Tipos de Assessment:**
1. **Cloze Test** - Compreensão geral
2. **Gap Fill** - Lacunas específicas  
3. **Reordenação** - Ordem de frases
4. **Transformação** - Estruturas gramaticais
5. **Múltipla Escolha** - Questões objetivas
6. **Verdadeiro/Falso** - Compreensão textual
7. **Matching** - Associação de elementos

**Seleção Inteligente:**
- Algoritmo RAG para balanceamento
- Máximo 2 atividades por unidade
- Evita repetição excessiva (máx 2x por 7 unidades)
- Atividades complementares entre si

**Endpoints:**
- `POST /units/{id}/assessments` - Gerar 2 atividades balanceadas
- `GET /units/{id}/assessments` - Obter atividades com análise
- `PUT /units/{id}/assessments` - Edição manual
- `DELETE /units/{id}/assessments` - Remoção
- `GET /units/{id}/assessments/analysis` - Análise de qualidade
- `GET /assessments/types` - Info sobre os 7 tipos

**🔒 Autenticação:** Todos endpoints requerem Bearer token

#### ❓ **qa.py** - Perguntas e Respostas Pedagógicas
**Sistema Q&A Inteligente:**
- Baseado na Taxonomia de Bloom (6 níveis cognitivos)
- Perguntas de pronúncia e consciência fonética
- Integração com vocabulário e estratégias da unidade
- Progressão de dificuldade estruturada

**Níveis Cognitivos:**
1. **Remember** - Recordar fatos básicos
2. **Understand** - Explicar conceitos
3. **Apply** - Usar em situações novas
4. **Analyze** - Quebrar em partes
5. **Evaluate** - Fazer julgamentos
6. **Create** - Produzir conteúdo original

**Endpoints:**
- `POST /units/{id}/qa` - Gerar Q&A pedagógico
- `GET /units/{id}/qa` - Obter perguntas e respostas
- `PUT /units/{id}/qa` - Edição manual
- `DELETE /units/{id}/qa` - Remoção
- `GET /units/{id}/qa/analysis` - Análise pedagógica
- `GET /qa/pedagogical-guidelines` - Diretrizes pedagógicas

**🔒 Autenticação:** Todos endpoints requerem Bearer token

### Sistema de Saúde e Monitoramento

#### 🏥 **health.py** - Health Check Avançado (Público)
**Monitoramento Completo:**
- Status de conexões (Supabase, OpenAI API)
- Validação de componentes IVO V2
- Verificação de serviços hierárquicos
- Análise de rate limiting e auditoria
- **Validação do sistema de autenticação**
- Diagnósticos específicos do sistema

**Endpoints:**
- `GET /health` - Health check básico
- `GET /health/detailed` - Diagnóstico completo com recomendações

**⚠️ Nota:** Endpoints de health são PÚBLICOS (não requerem Bearer token)

**Monitora:**
- Conexão Supabase e tabelas hierárquicas
- **Tabelas de autenticação** (`ivo_users`, `ivo_api_tokens`)
- OpenAI API para geração de conteúdo
- VocabularyGeneratorService e outros services
- **AuthService e middleware de autenticação**
- Image Analysis Service (integrado)
- Rate Limiter em memória
- Audit Logger
- Variáveis de ambiente críticas
- Paths do sistema de arquivos

#### 📋 **__init__.py** - Informações da API
**Metadados Completos:**
- **Versão 2.1.0 da API** (atualizada com autenticação)
- Arquitetura hierárquica Course→Book→Unit
- **Sistema de autenticação completo** integrado
- Status de implementação (85% completo)
- Endpoints implementados vs pendentes
- Fluxo recomendado de uso com autenticação
- Rate limits por endpoint + autenticação
- Sistema de validação de imports

**Informações de Estado:**
- **Implementados**: auth, courses, books, units, vocabulary, assessments, tips, grammar, qa, sentences
- **Novos**: auth system, AIM detector, structured output
- **Pendentes**: exportação, relatórios avançados
- Configurações de rate limiting específicas
- Tags para documentação automática

## 🔧 Integrações e Dependências

### Services Externos
- **OpenAI GPT-4o-mini** - Geração de conteúdo IA
- **Supabase** - Banco de dados PostgreSQL + tabelas de auth
- **OpenAI Vision** - Análise de imagens (integrado, sem MCP)
- **IPA (International Phonetic Alphabet)** - Transcrições fonéticas

### Components Internos
- **auth_middleware.py** - Middleware automático Bearer token
- **auth_service.py** - Serviço de autenticação completo
- **hierarchical_database.py** - ORM hierárquico personalizado
- **rate_limiter.py** - Rate limiting em memória + por token
- **audit_logger.py** - Sistema de auditoria completo
- **pagination.py** - Paginação avançada com filtros
- **enums.py** - Enums do sistema (CEFR, UnitType, etc.)

### Services de Geração (Atualizados)
- **VocabularyGeneratorService** - Geração com structured output
- **SentencesGeneratorService** - Sentences com fallback robusto
- **TipsGeneratorService** - Estratégias TIPS com enum validation
- **GrammarGeneratorService** - Estratégias GRAMMAR para gramática
- **AssessmentSelectorService** - Seleção inteligente de atividades
- **QAGeneratorService** - Geração de Q&A pedagógico
- **AuthService** - **NOVO:** Validação e gestão de tokens
- **AimDetectorService** - **NOVO:** Detecção automática de objetivos

## 🎯 Sistema RAG (Retrieval-Augmented Generation)

### Contexto Hierárquico Inteligente
O sistema utiliza RAG para:

1. **Prevenção de Repetições**
   - Análise de vocabulário já ensinado
   - Evita duplicação desnecessária
   - Permite reforço estratégico (5-15%)

2. **Balanceamento de Estratégias**
   - Distribui estratégias TIPS/GRAMMAR uniformemente
   - Evita overuse de estratégias específicas
   - Mantém diversidade pedagógica

3. **Seleção de Assessments**
   - Balanceia os 7 tipos de atividades
   - Evita repetição excessiva
   - Garante complementaridade

4. **Progressão Pedagógica**
   - Adapta complexidade à sequência
   - Considera histórico de aprendizagem
   - Mantém coerência curricular

5. **Detecção de Objetivos (AIM Detector)**
   - **NOVO:** Analisa automaticamente objetivos de aprendizagem
   - Detecta main_aim e subsidiary_aims
   - Integração automática na criação de units

### Análise de Contexto
- **Taught Vocabulary**: Lista de palavras já ensinadas
- **Used Strategies**: Estratégias pedagógicas aplicadas
- **Assessment Balance**: Distribuição de tipos de atividades
- **Progression Level**: Nível de progressão na sequência
- **Quality Metrics**: Métricas de qualidade do conteúdo
- **Learning Objectives**: **NOVO:** Objetivos detectados automaticamente

## 🚀 Fluxo de Uso Recomendado

### 🔐 Passo 0: Autenticação
```bash
# 1. Obter token IVO (fornecido pelo sistema)
# 2. Fazer login
curl -X POST "/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"api_key_ivo": "ivo_your_token_here"}'

# 3. Usar Bearer token retornado em todos endpoints V2
export BEARER_TOKEN="ivo_bearer_abc123..."
```

### 📚 Fluxo Principal
1. **Criar Course** com níveis CEFR e metodologia
2. **Criar Books** organizados por nível
3. **Criar Units** sequenciais com imagens (AIM Detector automático)
4. **Gerar Vocabulary** usando RAG + Vision
5. **Gerar Sentences** conectadas ao vocabulário
6. **Gerar Strategies** (TIPS para léxico, GRAMMAR para gramática)
7. **Gerar Assessments** (2 atividades balanceadas)
8. **Gerar Q&A** (opcional - complemento pedagógico)
9. **Unit completed!** - Pronta para uso

**Todos os passos 1-9 requerem Bearer token no header!**

## 📊 Features Avançadas

### 🔐 Autenticação e Segurança
- **Middleware Transparente**: Proteção automática de endpoints V2
- **Rate Limiting por Token**: Controle individualizado
- **Dual Token System**: Token IVO + Bearer token
- **Row Level Security**: Proteção no banco de dados
- **Audit Trail Completo**: Rastreamento de ações

### Rate Limiting Inteligente
- Limits específicos por tipo de operação
- **Rate limiting específico para auth** (login, create-user)
- Proteção contra abuse de geração IA
- Configuração flexível por endpoint

### Auditoria Completa
- Log de todas operações hierárquicas
- **Tracking de autenticação e tokens**
- Tracking de geração de conteúdo IA
- Métricas de performance e uso
- Análise de erros e recuperação

### Paginação Avançada
- Filtros dinâmicos por múltiplos campos
- Ordenação flexível
- Metadados estatísticos
- Otimização de performance

### Análise de Qualidade
- Scores automáticos de qualidade
- Recomendações de melhoria
- Análise de adequação CEFR
- Métricas pedagógicas detalhadas
- **AIM Detection automático**

### Structured Output (LangChain 0.3)
- **Eliminação de falhas JSON** em todos os services
- Validação com Pydantic 2.x
- Fallback robusto em caso de erros
- **Enum validation** para estratégias

## 🎨 Especificidades para Brasileiros

### Análise L1→L2 (Português→Inglês)
- **False Friends**: library ≠ livraria
- **Estruturas**: auxiliares, artigos, ordem
- **Pronúncia**: sons /th/, vogais, consoantes finais
- **Gramática**: interferência sistemática

### Estratégias Culturais
- Contextos brasileiros em exemplos
- Situações familiares aos aprendizes
- Metodologia adaptada ao perfil brasileiro
- Foco em erros comuns de brasileiros

## 📈 Métricas e Analytics

### Quality Scores
- Vocabulário: relevância, adequação CEFR, fonemas
- Sentences: complexidade, coerência, integração
- Strategies: eficácia pedagógica, adequação ao nível
- Assessments: balanceamento, complementaridade
- Q&A: profundidade cognitiva, progressão
- **Auth Security**: Taxa de autenticações válidas

### Progression Analytics
- Densidade vocabular por unidade
- Diversidade de estratégias aplicadas
- Variedade de tipos de assessment
- Taxa de conclusão de unidades
- Qualidade média do conteúdo gerado
- **Token usage analytics** por usuário

### Security Analytics (Novo)
- Taxa de autenticações bem-sucedidas
- Distribuição de uso por token
- Análise de rate limiting por endpoint
- Audit trail de ações críticas

## 🛡️ Segurança e Compliance

### Proteção de Dados
- **RLS (Row Level Security)** no banco
- Tokens com hash seguro
- Rate limiting por token individual
- Audit logging completo
- Validação de entrada em todos endpoints

### Token Management
- **Expiração configurável** de tokens
- **Scopes personalizáveis** por token
- **Rate limiting individual** por token
- **Revogação instantânea** de tokens
- **Rotação automática** (futura)

---

## 🚨 Limitações Atuais

- **Export/PDF**: Sistema de exportação não implementado
- **Reports**: Relatórios avançados pendentes
- **Real-time**: Sistema de geração em tempo real básico
- **Caching**: Cache em memória apenas (sem Redis)
- **OAuth2**: Apenas Bearer token (OAuth2 planejado)

## 🔮 Próximos Passos

1. Implementar sistema de exportação para PDF
2. Adicionar relatórios pedagógicos avançados
3. Melhorar cache com Redis/persistent storage
4. **Sistema de OAuth2** (Google, Facebook)
5. Dashboard de analytics em tempo real
6. API para integração com LMS
7. Sistema de revisão e correção automática
8. Geração de exercícios adaptativos
9. **Token refresh automático**
10. **Multi-tenancy** com organizações

---

## 📋 Checklist de Segurança

### ✅ Implementado
- [x] Bearer token authentication
- [x] Rate limiting por token
- [x] Row Level Security (RLS)
- [x] Middleware automático de proteção
- [x] Audit logging completo
- [x] Validação de entrada
- [x] Token hashing seguro
- [x] Scopes configuráveis

### 🚧 Em Desenvolvimento
- [ ] Token refresh automático
- [ ] OAuth2 integration
- [ ] Multi-tenancy
- [ ] Token rotation policies

---

*Esta API representa um sistema completo de geração automatizada de conteúdo pedagógico para ensino de inglês, com foco especial em aprendizes brasileiros, metodologia baseada em evidências pedagógicas e sistema de autenticação empresarial robusto.*

**Versão**: 2.1.0  
**Segurança**: Bearer Token + RLS + Audit Logging  
**Arquitetura**: Course → Book → Unit (Protegida)  
**IA Integration**: LangChain 0.3 + OpenAI GPT-4o-mini + Structured Output