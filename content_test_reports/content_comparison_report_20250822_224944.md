# IVO V2 - Relatório Comparativo de Geração de Conteúdo

**Data:** 2025-08-22 22:49:44
**Base URL:** http://localhost:8000

## 📊 Resumo Executivo

- **Total de Testes:** 37
- **Taxa de Sucesso Geral:** 94.6%

### 🎯 Comparação por Tipo de Unit

| Tipo | Tests | Sucessos | Taxa | Unit ID |
|------|-------|----------|------|---------|
| **SEM Imagem** | 12 | 11 | 91.7% | `unit_e7bbcdea_e580_461e_89d2_271750de7ba3` |
| **COM Imagem** | 14 | 14 | 100.0% | `unit_a8bfa5b9_3e06_4592_805a_99107461e789` |

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
| `/api/v2/books/book_2762e908_39a5_470b_8668_3b0f4026f2c1/units` | WITH_IMAGE | 200 | 3868ms | ✅ |
### CONTEXT (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3` | NO_IMAGE | 200 | 1432ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/context` | NO_IMAGE | 200 | 2117ms | ✅ |
### CONTEXT (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789` | WITH_IMAGE | 200 | 1255ms | ✅ |
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/context` | WITH_IMAGE | 200 | 2015ms | ✅ |
### VOCABULARY (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 200 | 28582ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 200 | 611ms | ✅ |
### VOCABULARY (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/vocabulary` | WITH_IMAGE | 200 | 28930ms | ✅ |
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/vocabulary` | WITH_IMAGE | 200 | 655ms | ✅ |
### SENTENCES (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 200 | 12979ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 200 | 561ms | ✅ |
### SENTENCES (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/sentences` | WITH_IMAGE | 200 | 13975ms | ✅ |
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/sentences` | WITH_IMAGE | 200 | 557ms | ✅ |
### TIPS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 500 | 62266ms | ❌ |
### TIPS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/tips` | WITH_IMAGE | 200 | 80264ms | ✅ |
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/tips` | WITH_IMAGE | 200 | 1037ms | ✅ |
### QA (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 200 | 40251ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 200 | 571ms | ✅ |
### QA (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/qa` | WITH_IMAGE | 200 | 37657ms | ✅ |
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/qa` | WITH_IMAGE | 200 | 810ms | ✅ |
### UNIT_CHECK (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_b5b1ad9a_595f_4cc0_b519_7a190d913dd8` | GRAMMAR_NO_IMAGE | 200 | 1129ms | ✅ |
### GRAMMAR_VOCAB (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_b5b1ad9a_595f_4cc0_b519_7a190d913dd8/vocabulary` | GRAMMAR_NO_IMAGE | 200 | 46416ms | ✅ |
### GRAMMAR_SENTENCES (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_b5b1ad9a_595f_4cc0_b519_7a190d913dd8/sentences` | GRAMMAR_NO_IMAGE | 200 | 11880ms | ✅ |
### GRAMMAR (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_b5b1ad9a_595f_4cc0_b519_7a190d913dd8/grammar` | GRAMMAR_NO_IMAGE | 200 | 35281ms | ✅ |
| `/api/v2/units/unit_b5b1ad9a_595f_4cc0_b519_7a190d913dd8/grammar` | GRAMMAR_NO_IMAGE | 200 | 503ms | ✅ |
### UNIT_CHECK (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_2491ce7d_8d72_44e4_9c91_a01caa7dddce` | GRAMMAR_WITH_IMAGE | 200 | 1047ms | ✅ |
### GRAMMAR_VOCAB (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_2491ce7d_8d72_44e4_9c91_a01caa7dddce/vocabulary` | GRAMMAR_WITH_IMAGE | 200 | 21700ms | ✅ |
### GRAMMAR_SENTENCES (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_2491ce7d_8d72_44e4_9c91_a01caa7dddce/sentences` | GRAMMAR_WITH_IMAGE | 200 | 10969ms | ✅ |
### GRAMMAR (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_2491ce7d_8d72_44e4_9c91_a01caa7dddce/grammar` | GRAMMAR_WITH_IMAGE | 200 | 33323ms | ✅ |
| `/api/v2/units/unit_2491ce7d_8d72_44e4_9c91_a01caa7dddce/grammar` | GRAMMAR_WITH_IMAGE | 200 | 516ms | ✅ |
### GRAMMAR (LEXICAL_DEMO)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/grammar` | LEXICAL_DEMO | 400 | 203ms | ❌ |
### ASSESSMENTS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 71068ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 566ms | ✅ |
### ASSESSMENTS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/assessments` | WITH_IMAGE | 200 | 102799ms | ✅ |
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/assessments` | WITH_IMAGE | 200 | 564ms | ✅ |
### COMPARISON (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/complete-content` | NO_IMAGE | 200 | 560ms | ✅ |
### COMPARISON (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_a8bfa5b9_3e06_4592_805a_99107461e789/complete-content` | WITH_IMAGE | 200 | 543ms | ✅ |

## 🎯 Conteúdo Gerado - Comparação

### Unit SEM Imagem
- **CONTEXT:** 2 itens gerados
- **VOCABULARY:** 2 itens gerados
- **SENTENCES:** 2 itens gerados
- **QA:** 2 itens gerados
- **UNIT_CHECK:** 1 itens gerados
- **GRAMMAR_VOCAB:** 1 itens gerados
- **GRAMMAR_SENTENCES:** 1 itens gerados
- **GRAMMAR:** 2 itens gerados
- **ASSESSMENTS:** 2 itens gerados
- **COMPARISON:** 1 itens gerados

### Unit COM Imagem
- **SETUP:** 1 itens gerados
- **CONTEXT:** 2 itens gerados
- **VOCABULARY:** 2 itens gerados
- **SENTENCES:** 2 itens gerados
- **TIPS:** 2 itens gerados
- **QA:** 2 itens gerados
- **UNIT_CHECK:** 1 itens gerados
- **GRAMMAR_VOCAB:** 1 itens gerados
- **GRAMMAR_SENTENCES:** 1 itens gerados
- **GRAMMAR:** 2 itens gerados
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
  "unit_with_image": "unit_a8bfa5b9_3e06_4592_805a_99107461e789",
  "unit_grammar_no_image": "unit_b5b1ad9a_595f_4cc0_b519_7a190d913dd8",
  "unit_grammar_with_image": "unit_2491ce7d_8d72_44e4_9c91_a01caa7dddce"
}
```
