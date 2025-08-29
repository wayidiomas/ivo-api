# IVO V2 - Relatório Comparativo de Geração de Conteúdo

**Data:** 2025-08-22 12:43:24
**Base URL:** http://localhost:8000

## 📊 Resumo Executivo

- **Total de Testes:** 36
- **Taxa de Sucesso Geral:** 91.7%

### 🎯 Comparação por Tipo de Unit

| Tipo | Tests | Sucessos | Taxa | Unit ID |
|------|-------|----------|------|---------|
| **SEM Imagem** | 13 | 13 | 100.0% | `unit_e7bbcdea_e580_461e_89d2_271750de7ba3` |
| **COM Imagem** | 14 | 14 | 100.0% | `unit_20b4a370_e444_4754_b961_165efebc7c8c` |

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
| `/api/v2/books/book_2762e908_39a5_470b_8668_3b0f4026f2c1/units` | WITH_IMAGE | 200 | 3654ms | ✅ |
### CONTEXT (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3` | NO_IMAGE | 200 | 1091ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/context` | NO_IMAGE | 200 | 1703ms | ✅ |
### CONTEXT (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c` | WITH_IMAGE | 200 | 1077ms | ✅ |
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/context` | WITH_IMAGE | 200 | 1659ms | ✅ |
### VOCABULARY (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 200 | 43561ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 200 | 773ms | ✅ |
### VOCABULARY (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/vocabulary` | WITH_IMAGE | 200 | 46229ms | ✅ |
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/vocabulary` | WITH_IMAGE | 200 | 838ms | ✅ |
### SENTENCES (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 200 | 60857ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 200 | 707ms | ✅ |
### SENTENCES (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/sentences` | WITH_IMAGE | 200 | 62777ms | ✅ |
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/sentences` | WITH_IMAGE | 200 | 1042ms | ✅ |
### TIPS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 200 | 66226ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 200 | 510ms | ✅ |
### TIPS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/tips` | WITH_IMAGE | 200 | 87016ms | ✅ |
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/tips` | WITH_IMAGE | 200 | 555ms | ✅ |
### QA (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 200 | 21770ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 200 | 538ms | ✅ |
### QA (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/qa` | WITH_IMAGE | 200 | 26577ms | ✅ |
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/qa` | WITH_IMAGE | 200 | 552ms | ✅ |
### UNIT_CHECK (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_61633152_00a6_4a44_af28_c4e9ca1dfa2d` | GRAMMAR_NO_IMAGE | 200 | 1319ms | ✅ |
### GRAMMAR_VOCAB (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_61633152_00a6_4a44_af28_c4e9ca1dfa2d/vocabulary` | GRAMMAR_NO_IMAGE | 200 | 51109ms | ✅ |
### GRAMMAR_SENTENCES (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_61633152_00a6_4a44_af28_c4e9ca1dfa2d/sentences` | GRAMMAR_NO_IMAGE | 200 | 60577ms | ✅ |
### GRAMMAR (GRAMMAR_NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_61633152_00a6_4a44_af28_c4e9ca1dfa2d/grammar` | GRAMMAR_NO_IMAGE | 500 | 1072ms | ❌ |
### UNIT_CHECK (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_f2de5f34_801c_490f_95d6_8d967e6a839c` | GRAMMAR_WITH_IMAGE | 200 | 1477ms | ✅ |
### GRAMMAR_VOCAB (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_f2de5f34_801c_490f_95d6_8d967e6a839c/vocabulary` | GRAMMAR_WITH_IMAGE | 200 | 91173ms | ✅ |
### GRAMMAR_SENTENCES (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_f2de5f34_801c_490f_95d6_8d967e6a839c/sentences` | GRAMMAR_WITH_IMAGE | 200 | 52061ms | ✅ |
### GRAMMAR (GRAMMAR_WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_f2de5f34_801c_490f_95d6_8d967e6a839c/grammar` | GRAMMAR_WITH_IMAGE | 500 | 861ms | ❌ |
### GRAMMAR (LEXICAL_DEMO)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/grammar` | LEXICAL_DEMO | 400 | 181ms | ❌ |
### ASSESSMENTS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 102107ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 200 | 548ms | ✅ |
### ASSESSMENTS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/assessments` | WITH_IMAGE | 200 | 161773ms | ✅ |
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/assessments` | WITH_IMAGE | 200 | 534ms | ✅ |
### COMPARISON (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/complete-content` | NO_IMAGE | 200 | 565ms | ✅ |
### COMPARISON (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_20b4a370_e444_4754_b961_165efebc7c8c/complete-content` | WITH_IMAGE | 200 | 607ms | ✅ |

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
  "unit_with_image": "unit_20b4a370_e444_4754_b961_165efebc7c8c",
  "unit_grammar_no_image": "unit_61633152_00a6_4a44_af28_c4e9ca1dfa2d",
  "unit_grammar_with_image": "unit_f2de5f34_801c_490f_95d6_8d967e6a839c"
}
```
