# IVO V2 - Relatório Comparativo de Geração de Conteúdo

**Data:** 2025-08-21 16:44:30
**Base URL:** http://localhost:8000

## 📊 Resumo Executivo

- **Total de Testes:** 20
- **Taxa de Sucesso Geral:** 45.0%

### 🎯 Comparação por Tipo de Unit

| Tipo | Tests | Sucessos | Taxa | Unit ID |
|------|-------|----------|------|---------|
| **SEM Imagem** | 10 | 5 | 50.0% | `unit_e7bbcdea_e580_461e_89d2_271750de7ba3` |
| **COM Imagem** | 10 | 4 | 40.0% | `unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0` |

## 🔍 Análise Comparativa

### Unit SEM Imagem (Baseada em Contexto)
- **Contexto:** "Hotel reservations and check-in procedures..."
- **Foco:** Situações e procedimentos conceituais
- **Vocabulário:** Baseado em campo semântico
- **Sentenças:** Situações de uso prático

### Unit COM Imagem (Baseada em Análise Visual)
- **Contexto:** "Restaurant dining experience..." + Imagem
- **Foco:** Objetos e ações visuais
- **Vocabulário:** Baseado em elementos da imagem
- **Sentenças:** Descrições e ações visíveis

## 📋 Resultados por Categoria

### SETUP (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/books/book_2762e908_39a5_470b_8668_3b0f4026f2c1/units` | WITH_IMAGE | 200 | 4180ms | ✅ |
### CONTEXT (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3` | NO_IMAGE | 200 | 1545ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/context` | NO_IMAGE | 200 | 2318ms | ✅ |
### CONTEXT (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0` | WITH_IMAGE | 200 | 1377ms | ✅ |
| `/api/v2/units/unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0/context` | WITH_IMAGE | 200 | 1505ms | ✅ |
### VOCABULARY (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 0 | 60016ms | ❌ |
### VOCABULARY (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0/vocabulary` | WITH_IMAGE | 0 | 60034ms | ❌ |
### SENTENCES (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 0 | 60015ms | ❌ |
### SENTENCES (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0/sentences` | WITH_IMAGE | 400 | 244ms | ❌ |
### TIPS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 200 | 5319ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 200 | 833ms | ✅ |
### TIPS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0/tips` | WITH_IMAGE | 400 | 281ms | ❌ |
### QA (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 500 | 1228ms | ❌ |
### QA (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0/qa` | WITH_IMAGE | 400 | 537ms | ❌ |
### GRAMMAR (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/grammar` | NO_IMAGE | 429 | 37ms | ❌ |
### GRAMMAR (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0/grammar` | WITH_IMAGE | 429 | 31ms | ❌ |
### ASSESSMENTS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 500 | 2345ms | ❌ |
### ASSESSMENTS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0/assessments` | WITH_IMAGE | 400 | 256ms | ❌ |
### COMPARISON (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/complete-content` | NO_IMAGE | 200 | 543ms | ✅ |
### COMPARISON (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0/complete-content` | WITH_IMAGE | 200 | 549ms | ✅ |

## 🎯 Conteúdo Gerado - Comparação

### Unit SEM Imagem
- **CONTEXT:** 2 itens gerados
- **TIPS:** 2 itens gerados
- **COMPARISON:** 1 itens gerados

### Unit COM Imagem
- **SETUP:** 1 itens gerados
- **CONTEXT:** 2 itens gerados
- **COMPARISON:** 1 itens gerados

## ⏳ Rate Limiting Aplicado

**Configurações de Tempo:**
- Operações normais: 2.0s entre requests
- Criação de unit: 3.0s
- Geração OpenAI: 8.0s (vocabulário, sentenças, tips, etc.)

**Motivos:**
1. Respeitar limites da API OpenAI
2. Evitar sobrecarga do servidor
3. Garantir processamento adequado de módulos dependentes
4. Simular uso real do sistema

## 📝 Conclusões

1. **Pipeline de Geração:** Ambas as abordagens (com e sem imagem) foram testadas
2. **Contexto vs Visual:** Comparação direta entre geração baseada em texto vs imagem
3. **Qualidade Pedagógica:** Avaliar qual abordagem produz conteúdo mais eficaz
4. **Performance com Rate Limiting:** Tempos controlados para evitar falhas
5. **Dependências Sequenciais:** Cada módulo espera o anterior completar

## 🔧 IDs para Testes Futuros

```json
{
  "course_id": "course_5e19fe18_c172_4f43_9c0a_202293325115",
  "book_id": "book_2762e908_39a5_470b_8668_3b0f4026f2c1",
  "unit_no_image": "unit_e7bbcdea_e580_461e_89d2_271750de7ba3",
  "unit_with_image": "unit_8a5978ea_02fb_42bf_946b_d29b416a6ef0"
}
```
