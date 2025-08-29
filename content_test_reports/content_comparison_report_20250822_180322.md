# IVO V2 - Relatório Comparativo de Geração de Conteúdo

**Data:** 2025-08-22 18:03:22
**Base URL:** http://localhost:8000

## 📊 Resumo Executivo

- **Total de Testes:** 24
- **Taxa de Sucesso Geral:** 54.2%

### 🎯 Comparação por Tipo de Unit

| Tipo | Tests | Sucessos | Taxa | Unit ID |
|------|-------|----------|------|---------|
| **SEM Imagem** | 10 | 7 | 70.0% | `unit_e7bbcdea_e580_461e_89d2_271750de7ba3` |
| **COM Imagem** | 9 | 4 | 44.4% | `unit_dc893e62_3460_42d3_a7f1_ed5717f67c2f` |

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
| `/api/v2/books/book_2762e908_39a5_470b_8668_3b0f4026f2c1/units` | WITH_IMAGE | 200 | 2522ms | ✅ |
### CONTEXT (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3` | NO_IMAGE | 200 | 1138ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/context` | NO_IMAGE | 200 | 2007ms | ✅ |
### CONTEXT (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_dc893e62_3460_42d3_a7f1_ed5717f67c2f` | WITH_IMAGE | 200 | 1254ms | ✅ |
| `/api/v2/units/unit_dc893e62_3460_42d3_a7f1_ed5717f67c2f/context` | WITH_IMAGE | 200 | 2014ms | ✅ |
### VOCABULARY (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 422 | 17ms | ❌ |
### VOCABULARY (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_dc893e62_3460_42d3_a7f1_ed5717f67c2f/vocabulary` | WITH_IMAGE | 422 | 13ms | ❌ |
### SENTENCES (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 422 | 158ms | ❌ |
### SENTENCES (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_dc893e62_3460_42d3_a7f1_ed5717f67c2f/sentences` | WITH_IMAGE | 422 | 31ms | ❌ |
### TIPS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 200 | 70846ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 200 | 1334ms | ✅ |
### TIPS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_dc893e62_3460_42d3_a7f1_ed5717f67c2f/tips` | WITH_IMAGE | 400 | 228ms | ❌ |
### QA (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 422 | 16ms | ❌ |
### QA (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_dc893e62_3460_42d3_a7f1_ed5717f67c2f/qa` | WITH_IMAGE | 429 | 17ms | ❌ |
### UNIT_CHECK (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_31bef8d7_6264_4c82_90be_75042a734bd0` | GRAMMAR_NO_IMAGE | 200 | 1105ms | ✅ |
### GRAMMAR_VOCAB (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_31bef8d7_6264_4c82_90be_75042a734bd0/vocabulary` | GRAMMAR_NO_IMAGE | 422 | 13ms | ❌ |
### UNIT_CHECK (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_d2cbd07f_07b2_4c88_9918_a3109405ab4a` | GRAMMAR_WITH_IMAGE | 200 | 1815ms | ✅ |
### GRAMMAR_VOCAB (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_d2cbd07f_07b2_4c88_9918_a3109405ab4a/vocabulary` | GRAMMAR_WITH_IMAGE | 422 | 14ms | ❌ |
### GRAMMAR (LEXICAL_DEMO)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/grammar` | LEXICAL_DEMO | 429 | 14ms | ❌ |
### ASSESSMENTS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 76674ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 571ms | ✅ |
### ASSESSMENTS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_dc893e62_3460_42d3_a7f1_ed5717f67c2f/assessments` | WITH_IMAGE | 400 | 322ms | ❌ |
### COMPARISON (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/complete-content` | NO_IMAGE | 200 | 772ms | ✅ |
### COMPARISON (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_dc893e62_3460_42d3_a7f1_ed5717f67c2f/complete-content` | WITH_IMAGE | 200 | 603ms | ✅ |

## 🎯 Conteúdo Gerado - Comparação

### Unit SEM Imagem
- **CONTEXT:** 2 itens gerados
- **TIPS:** 2 itens gerados
- **UNIT_CHECK:** 1 itens gerados
- **ASSESSMENTS:** 2 itens gerados
- **COMPARISON:** 1 itens gerados

### Unit COM Imagem
- **SETUP:** 1 itens gerados
- **CONTEXT:** 2 itens gerados
- **UNIT_CHECK:** 1 itens gerados
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
  "unit_with_image": "unit_dc893e62_3460_42d3_a7f1_ed5717f67c2f",
  "unit_grammar_no_image": "unit_31bef8d7_6264_4c82_90be_75042a734bd0",
  "unit_grammar_with_image": "unit_d2cbd07f_07b2_4c88_9918_a3109405ab4a"
}
```
