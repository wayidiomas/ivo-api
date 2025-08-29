# IVO V2 - Relatório Comparativo de Geração de Conteúdo

**Data:** 2025-08-21 22:03:35
**Base URL:** http://localhost:8000

## 📊 Resumo Executivo

- **Total de Testes:** 31
- **Taxa de Sucesso Geral:** 87.1%

### 🎯 Comparação por Tipo de Unit

| Tipo | Tests | Sucessos | Taxa | Unit ID |
|------|-------|----------|------|---------|
| **SEM Imagem** | 12 | 11 | 91.7% | `unit_e7bbcdea_e580_461e_89d2_271750de7ba3` |
| **COM Imagem** | 14 | 14 | 100.0% | `unit_65379abf_9658_4c9d_9f04_831afbc5b499` |

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
| `/api/v2/books/book_2762e908_39a5_470b_8668_3b0f4026f2c1/units` | WITH_IMAGE | 200 | 2481ms | ✅ |
### CONTEXT (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3` | NO_IMAGE | 200 | 1107ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/context` | NO_IMAGE | 200 | 1580ms | ✅ |
### CONTEXT (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499` | WITH_IMAGE | 200 | 1095ms | ✅ |
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/context` | WITH_IMAGE | 200 | 1600ms | ✅ |
### VOCABULARY (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 200 | 31891ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 200 | 593ms | ✅ |
### VOCABULARY (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/vocabulary` | WITH_IMAGE | 200 | 37290ms | ✅ |
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/vocabulary` | WITH_IMAGE | 200 | 504ms | ✅ |
### SENTENCES (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 200 | 39827ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 200 | 586ms | ✅ |
### SENTENCES (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/sentences` | WITH_IMAGE | 200 | 19469ms | ✅ |
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/sentences` | WITH_IMAGE | 200 | 824ms | ✅ |
### TIPS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 500 | 75910ms | ❌ |
### TIPS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/tips` | WITH_IMAGE | 200 | 82028ms | ✅ |
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/tips` | WITH_IMAGE | 200 | 735ms | ✅ |
### QA (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 200 | 17603ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 200 | 515ms | ✅ |
### QA (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/qa` | WITH_IMAGE | 200 | 21109ms | ✅ |
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/qa` | WITH_IMAGE | 200 | 575ms | ✅ |
### UNIT_CHECK (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_ccdbc42f_5325_4e63_a117_1926bd066228` | GRAMMAR_NO_IMAGE | 200 | 1064ms | ✅ |
| `/api/v2/units/unit_ccdbc42f_5325_4e63_a117_1926bd066228` | GRAMMAR_NO_IMAGE | 0 | 1065ms | ❌ |
### UNIT_CHECK (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_4dd15f48_4c94_47ad_adf2_40e6e1d25cf9` | GRAMMAR_WITH_IMAGE | 200 | 1146ms | ✅ |
| `/api/v2/units/unit_4dd15f48_4c94_47ad_adf2_40e6e1d25cf9` | GRAMMAR_WITH_IMAGE | 0 | 1147ms | ❌ |
### GRAMMAR (LEXICAL_DEMO)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/grammar` | LEXICAL_DEMO | 400 | 221ms | ❌ |
### ASSESSMENTS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 98686ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 528ms | ✅ |
### ASSESSMENTS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/assessments` | WITH_IMAGE | 200 | 126675ms | ✅ |
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/assessments` | WITH_IMAGE | 200 | 534ms | ✅ |
### COMPARISON (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/complete-content` | NO_IMAGE | 200 | 564ms | ✅ |
### COMPARISON (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_65379abf_9658_4c9d_9f04_831afbc5b499/complete-content` | WITH_IMAGE | 200 | 525ms | ✅ |

## 🎯 Conteúdo Gerado - Comparação

### Unit SEM Imagem
- **CONTEXT:** 2 itens gerados
- **VOCABULARY:** 2 itens gerados
- **SENTENCES:** 2 itens gerados
- **QA:** 2 itens gerados
- **ASSESSMENTS:** 2 itens gerados
- **COMPARISON:** 1 itens gerados

### Unit COM Imagem
- **SETUP:** 1 itens gerados
- **CONTEXT:** 2 itens gerados
- **VOCABULARY:** 2 itens gerados
- **SENTENCES:** 2 itens gerados
- **TIPS:** 2 itens gerados
- **QA:** 2 itens gerados
- **ASSESSMENTS:** 2 itens gerados
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
  "unit_with_image": "unit_65379abf_9658_4c9d_9f04_831afbc5b499",
  "unit_grammar_no_image": "unit_ccdbc42f_5325_4e63_a117_1926bd066228",
  "unit_grammar_with_image": "unit_4dd15f48_4c94_47ad_adf2_40e6e1d25cf9"
}
```
