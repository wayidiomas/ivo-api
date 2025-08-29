# IVO V2 - Relatório Comparativo de Geração de Conteúdo

**Data:** 2025-08-19 07:34:33
**Base URL:** http://localhost:8000

## 📊 Resumo Executivo

- **Total de Testes:** 27
- **Taxa de Sucesso Geral:** 18.5%

### 🎯 Comparação por Tipo de Unit

| Tipo | Tests | Sucessos | Taxa | Unit ID |
|------|-------|----------|------|---------|
| **SEM Imagem** | 13 | 2 | 15.4% | `unit_e7bbcdea_e580_461e_89d2_271750de7ba3` |
| **COM Imagem** | 14 | 3 | 21.4% | `unit_0d2ae96c_762d_436e_897d_f38e56ca532f` |

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
| `/api/v2/books/book_2762e908_39a5_470b_8668_3b0f4026f2c1/units` | WITH_IMAGE | 200 | 3985ms | ✅ |
### CONTEXT (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3` | NO_IMAGE | 200 | 1512ms | ✅ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/context` | NO_IMAGE | 200 | 1011ms | ✅ |
### CONTEXT (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f` | WITH_IMAGE | 200 | 1523ms | ✅ |
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/context` | WITH_IMAGE | 200 | 1230ms | ✅ |
### VOCABULARY (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 404 | 11ms | ❌ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/vocabulary` | NO_IMAGE | 404 | 16ms | ❌ |
### VOCABULARY (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/vocabulary` | WITH_IMAGE | 404 | 15ms | ❌ |
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/vocabulary` | WITH_IMAGE | 404 | 21ms | ❌ |
### SENTENCES (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 404 | 124ms | ❌ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/sentences` | NO_IMAGE | 404 | 11ms | ❌ |
### SENTENCES (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/sentences` | WITH_IMAGE | 404 | 12ms | ❌ |
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/sentences` | WITH_IMAGE | 404 | 13ms | ❌ |
### TIPS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 404 | 16ms | ❌ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/tips` | NO_IMAGE | 429 | 77ms | ❌ |
### TIPS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/tips` | WITH_IMAGE | 429 | 9ms | ❌ |
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/tips` | WITH_IMAGE | 429 | 11ms | ❌ |
### QA (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 429 | 12ms | ❌ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/qa` | NO_IMAGE | 429 | 10ms | ❌ |
### QA (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/qa` | WITH_IMAGE | 429 | 12ms | ❌ |
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/qa` | WITH_IMAGE | 429 | 12ms | ❌ |
### ASSESSMENTS (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 429 | 10ms | ❌ |
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/assessments` | NO_IMAGE | 429 | 53ms | ❌ |
### ASSESSMENTS (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/assessments` | WITH_IMAGE | 429 | 14ms | ❌ |
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/assessments` | WITH_IMAGE | 429 | 14ms | ❌ |
### COMPARISON (NO_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_e7bbcdea_e580_461e_89d2_271750de7ba3/complete-content` | NO_IMAGE | 404 | 98ms | ❌ |
### COMPARISON (WITH_IMAGE)

| Endpoint | Tipo | Status | Tempo | Resultado |
|----------|------|--------|-------|-----------|
| `/api/v2/units/unit_0d2ae96c_762d_436e_897d_f38e56ca532f/complete-content` | WITH_IMAGE | 404 | 10ms | ❌ |

## 🎯 Conteúdo Gerado - Comparação

### Unit SEM Imagem
- **CONTEXT:** 2 itens gerados

### Unit COM Imagem
- **SETUP:** 1 itens gerados
- **CONTEXT:** 2 itens gerados

## 📝 Conclusões

1. **Pipeline de Geração:** Ambas as abordagens (com e sem imagem) foram testadas
2. **Contexto vs Visual:** Comparação direta entre geração baseada em texto vs imagem
3. **Qualidade Pedagógica:** Avaliar qual abordagem produz conteúdo mais eficaz
4. **Performance:** Comparar tempos de processamento entre os dois métodos

## 🔧 IDs para Testes Futuros

```json
{
  "course_id": "course_5e19fe18_c172_4f43_9c0a_202293325115",
  "book_id": "book_2762e908_39a5_470b_8668_3b0f4026f2c1",
  "unit_no_image": "unit_e7bbcdea_e580_461e_89d2_271750de7ba3",
  "unit_with_image": "unit_0d2ae96c_762d_436e_897d_f38e56ca532f"
}
```
