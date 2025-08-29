# IVO V2 - Relatório Comparativo de Geração de Conteúdo

**Data:** 2025-08-22 18:18:00
**Base URL:** http://localhost:8000

## 📊 Resumo Executivo

- **Total de Testes:** 24
- **Taxa de Sucesso Geral:** 54.2%

### 🎯 Comparação por Tipo de Unit

| Tipo | Tests | Sucessos | Taxa | Unit ID |
|------|-------|----------|------|---------|
| **SEM Imagem** | 10 | 7 | 70.0% | `unit_e7bbcdea_e580_461e_89d2_271750de7ba3` |
| **COM Imagem** | 9 | 4 | 44.4% | `unit_d82e16ee_0f26_4d6e_8b14_f60053b2523d` |

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
| `/api/v2/books/book_2762e908_39a5_470b_8668_3b0f4026f2c1/units` | WITH_IMAGE | 200 | 2472ms | ✅ |
### CONTEXT (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3` | NO_IMAGE | 200 | 1289ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/context` | NO_IMAGE | 200 | 2060ms | ✅ |
### CONTEXT (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_d82e16ee_0f26_4d6e_8b14_f60053b2523d` | WITH_IMAGE | 200 | 1591ms | ✅ |
| `/api/v2/units/unit_d82e16ee_0f26_4d6e_8b14_f60053b2523d/context` | WITH_IMAGE | 200 | 1874ms | ✅ |
### VOCABULARY (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 422 | 15ms | ❌ |
### VOCABULARY (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_d82e16ee_0f26_4d6e_8b14_f60053b2523d/vocabulary` | WITH_IMAGE | 422 | 15ms | ❌ |
### SENTENCES (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 422 | 42ms | ❌ |
### SENTENCES (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_d82e16ee_0f26_4d6e_8b14_f60053b2523d/sentences` | WITH_IMAGE | 422 | 13ms | ❌ |
### TIPS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 200 | 72335ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 200 | 604ms | ✅ |
### TIPS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_d82e16ee_0f26_4d6e_8b14_f60053b2523d/tips` | WITH_IMAGE | 400 | 269ms | ❌ |
### QA (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 422 | 31ms | ❌ |
### QA (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_d82e16ee_0f26_4d6e_8b14_f60053b2523d/qa` | WITH_IMAGE | 429 | 13ms | ❌ |
### UNIT_CHECK (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_6610ea7d_8faf_4fa2_b239_b0f0c3ae9d39` | GRAMMAR_NO_IMAGE | 200 | 1145ms | ✅ |
### GRAMMAR_VOCAB (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_6610ea7d_8faf_4fa2_b239_b0f0c3ae9d39/vocabulary` | GRAMMAR_NO_IMAGE | 422 | 11ms | ❌ |
### UNIT_CHECK (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_dc634ad1_c967_48fa_a8f6_cc0e3d91546d` | GRAMMAR_WITH_IMAGE | 200 | 1094ms | ✅ |
### GRAMMAR_VOCAB (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_dc634ad1_c967_48fa_a8f6_cc0e3d91546d/vocabulary` | GRAMMAR_WITH_IMAGE | 422 | 14ms | ❌ |
### GRAMMAR (LEXICAL_DEMO)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/grammar` | LEXICAL_DEMO | 400 | 507ms | ❌ |
### ASSESSMENTS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 98533ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 599ms | ✅ |
### ASSESSMENTS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_d82e16ee_0f26_4d6e_8b14_f60053b2523d/assessments` | WITH_IMAGE | 400 | 239ms | ❌ |
### COMPARISON (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/complete-content` | NO_IMAGE | 200 | 506ms | ✅ |
### COMPARISON (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_d82e16ee_0f26_4d6e_8b14_f60053b2523d/complete-content` | WITH_IMAGE | 200 | 688ms | ✅ |

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
  "unit_with_image": "unit_d82e16ee_0f26_4d6e_8b14_f60053b2523d",
  "unit_grammar_no_image": "unit_6610ea7d_8faf_4fa2_b239_b0f0c3ae9d39",
  "unit_grammar_with_image": "unit_dc634ad1_c967_48fa_a8f6_cc0e3d91546d"
}
```
