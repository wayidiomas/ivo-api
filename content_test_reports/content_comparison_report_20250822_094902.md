# IVO V2 - Relatório Comparativo de Geração de Conteúdo

**Data:** 2025-08-22 09:49:02
**Base URL:** http://localhost:8000

## 📊 Resumo Executivo

- **Total de Testes:** 36
- **Taxa de Sucesso Geral:** 91.7%

### 🎯 Comparação por Tipo de Unit

| Tipo | Tests | Sucessos | Taxa | Unit ID |
|------|-------|----------|------|---------|
| **SEM Imagem** | 13 | 13 | 100.0% | `unit_e7bbcdea_e580_461e_89d2_271750de7ba3` |
| **COM Imagem** | 14 | 14 | 100.0% | `unit_0619d243_7f43_4e2a_85d1_4a671e225cf9` |

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
| `/api/v2/books/book_2762e908_39a5_470b_8668_3b0f4026f2c1/units` | WITH_IMAGE | 200 | 3460ms | ✅ |
### CONTEXT (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3` | NO_IMAGE | 200 | 1387ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/context` | NO_IMAGE | 200 | 1803ms | ✅ |
### CONTEXT (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9` | WITH_IMAGE | 200 | 1389ms | ✅ |
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/context` | WITH_IMAGE | 200 | 1646ms | ✅ |
### VOCABULARY (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 200 | 34933ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 200 | 778ms | ✅ |
### VOCABULARY (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/vocabulary` | WITH_IMAGE | 200 | 52596ms | ✅ |
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/vocabulary` | WITH_IMAGE | 200 | 1021ms | ✅ |
### SENTENCES (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 200 | 69918ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 200 | 516ms | ✅ |
### SENTENCES (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/sentences` | WITH_IMAGE | 200 | 81621ms | ✅ |
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/sentences` | WITH_IMAGE | 200 | 567ms | ✅ |
### TIPS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 200 | 86571ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 200 | 539ms | ✅ |
### TIPS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/tips` | WITH_IMAGE | 200 | 81384ms | ✅ |
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/tips` | WITH_IMAGE | 200 | 619ms | ✅ |
### QA (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 200 | 22045ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 200 | 516ms | ✅ |
### QA (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/qa` | WITH_IMAGE | 200 | 15637ms | ✅ |
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/qa` | WITH_IMAGE | 200 | 505ms | ✅ |
### UNIT_CHECK (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_bfe700db_56e6_4c2c_a726_1598de2919ec` | GRAMMAR_NO_IMAGE | 200 | 1260ms | ✅ |
### GRAMMAR_VOCAB (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_bfe700db_56e6_4c2c_a726_1598de2919ec/vocabulary` | GRAMMAR_NO_IMAGE | 200 | 51206ms | ✅ |
### GRAMMAR_SENTENCES (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_bfe700db_56e6_4c2c_a726_1598de2919ec/sentences` | GRAMMAR_NO_IMAGE | 200 | 63247ms | ✅ |
### GRAMMAR (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_bfe700db_56e6_4c2c_a726_1598de2919ec/grammar` | GRAMMAR_NO_IMAGE | 500 | 817ms | ❌ |
### UNIT_CHECK (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_7b1490c4_0505_4651_97b0_436d9f1dce85` | GRAMMAR_WITH_IMAGE | 200 | 961ms | ✅ |
### GRAMMAR_VOCAB (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_7b1490c4_0505_4651_97b0_436d9f1dce85/vocabulary` | GRAMMAR_WITH_IMAGE | 200 | 72084ms | ✅ |
### GRAMMAR_SENTENCES (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_7b1490c4_0505_4651_97b0_436d9f1dce85/sentences` | GRAMMAR_WITH_IMAGE | 200 | 70431ms | ✅ |
### GRAMMAR (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_7b1490c4_0505_4651_97b0_436d9f1dce85/grammar` | GRAMMAR_WITH_IMAGE | 500 | 919ms | ❌ |
### GRAMMAR (LEXICAL_DEMO)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/grammar` | LEXICAL_DEMO | 400 | 195ms | ❌ |
### ASSESSMENTS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 100148ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 586ms | ✅ |
### ASSESSMENTS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/assessments` | WITH_IMAGE | 200 | 136080ms | ✅ |
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/assessments` | WITH_IMAGE | 200 | 564ms | ✅ |
### COMPARISON (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/complete-content` | NO_IMAGE | 200 | 547ms | ✅ |
### COMPARISON (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0619d243_7f43_4e2a_85d1_4a671e225cf9/complete-content` | WITH_IMAGE | 200 | 517ms | ✅ |

## 🎯 Conteúdo Gerado - Comparação

### Unit SEM Imagem
- **CONTEXT:** 2 itens gerados
- **VOCABULARY:** 2 itens gerados
- **SENTENCES:** 2 itens gerados
- **TIPS:** 2 itens gerados
- **QA:** 2 itens gerados
- **UNIT_CHECK:** 1 itens gerados
- **GRAMMAR_VOCAB:** 1 itens gerados
- **GRAMMAR_SENTENCES:** 1 itens gerados
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
  "unit_with_image": "unit_0619d243_7f43_4e2a_85d1_4a671e225cf9",
  "unit_grammar_no_image": "unit_bfe700db_56e6_4c2c_a726_1598de2919ec",
  "unit_grammar_with_image": "unit_7b1490c4_0505_4651_97b0_436d9f1dce85"
}
```
