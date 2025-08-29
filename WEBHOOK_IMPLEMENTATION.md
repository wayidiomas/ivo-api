# Sistema de Webhooks para Processamento Assíncrono

## Visão Geral

Implementação completa de sistema de webhooks para endpoints de IA que demoram mais de 1 minuto. O sistema permite que o usuário escolha entre processamento síncrono ou assíncrono.

## Endpoints Suportados

Os seguintes endpoints da API v2 agora suportam processamento assíncrono via webhooks:

1. `POST /api/v2/units/{unit_id}/vocabulary` - Geração de vocabulário
2. `POST /api/v2/units/{unit_id}/sentences` - Geração de sentenças  
3. `POST /api/v2/units/{unit_id}/grammar` - Geração de estratégias gramaticais
4. `POST /api/v2/units/{unit_id}/tips` - Geração de estratégias TIPS
5. `POST /api/v2/units/{unit_id}/assessments` - Geração de atividades
6. `POST /api/v2/units/{unit_id}/qa` - Geração de perguntas e respostas

## Como Usar

### Processamento Síncrono (Comportamento Original)

Envie a requisição normalmente, sem o campo `webhook_url`:

```json
{
  "target_count": 25,
  "difficulty_level": "intermediate"
}
```

### Processamento Assíncrono (Novo)

Inclua o campo `webhook_url` no payload:

```json
{
  "webhook_url": "https://seu-endpoint.com/webhook",
  "target_count": 25,
  "difficulty_level": "intermediate"
}
```

## Resposta para Processamento Assíncrono

Quando `webhook_url` é fornecida, a API retorna imediatamente:

```json
{
  "message": "Requisição aceita para processamento assíncrono",
  "async_processing": true,
  "task_id": "vocab_1724425123456_abc12345",
  "webhook_url": "https://seu-endpoint.com/webhook",
  "endpoint": "vocabulary",
  "status": "processing",
  "estimated_completion": "1-5 minutos",
  "webhook_info": {
    "format": "POST request com JSON",
    "headers": {
      "Content-Type": "application/json",
      "X-Task-Id": "vocab_1724425123456_abc12345",
      "X-Webhook-Source": "ivo-api"
    }
  }
}
```

## Payload do Webhook

### Sucesso

Quando o processamento é concluído com sucesso:

```json
{
  "task_id": "vocab_1724425123456_abc12345",
  "status": "completed",
  "success": true,
  "result": {
    // Resultado completo do endpoint (mesmo formato da resposta síncrona)
    "data": {...},
    "message": "...",
    "hierarchy_info": {...}
  },
  "processing_time": 127.45,
  "completed_at": "2024-08-23T14:35:12Z",
  "metadata": {
    "endpoint": "vocabulary",
    "unit_id": "unit_123",
    "request_data": {
      "target_count": 25,
      "difficulty_level": "intermediate"
    }
  }
}
```

### Erro

Quando há falha no processamento:

```json
{
  "task_id": "vocab_1724425123456_abc12345",
  "status": "failed",
  "success": false,
  "error": "Descrição do erro",
  "processing_time": 45.32,
  "failed_at": "2024-08-23T14:32:45Z",
  "metadata": {
    "endpoint": "vocabulary",
    "unit_id": "unit_123",
    "request_data": {...}
  }
}
```

## Endpoints de Status

### Consultar Status de Tarefa

```http
GET /api/v2/webhooks/tasks/{task_id}/status
```

Retorna o status atual de uma tarefa específica.

### Listar Tarefas Ativas

```http
GET /api/v2/webhooks/tasks/active
```

Lista todas as tarefas atualmente em execução.

### Informações do Sistema

```http
GET /api/v2/webhooks/info
```

Retorna informações sobre o sistema de webhooks.

## Validações de webhook_url

A URL do webhook deve atender aos seguintes critérios:

- ✅ Protocolo HTTP ou HTTPS
- ✅ Hostname válido
- ✅ Máximo 2048 caracteres
- ✅ Aceita localhost e IPs privados (útil para desenvolvimento)

## Retry Policy

O sistema tentará entregar o webhook até 3 vezes com backoff exponencial:
- Tentativa 1: imediata
- Tentativa 2: após 2 segundos  
- Tentativa 3: após 4 segundos

## Arquivos Implementados

### Core
- `src/services/webhook_service.py` - Serviço principal de webhooks
- `src/core/webhook_utils.py` - Utilitários de validação e processamento
- `src/api/v2/webhook_status.py` - Endpoints de consulta de status

### Modelos Atualizados
- `src/core/unit_models.py` - Adicionado campo `webhook_url` opcional em todos os requests

### Endpoints Modificados
- `src/api/v2/vocabulary.py` - Suporte a webhook
- `src/api/v2/grammar.py` - Suporte a webhook  
- `src/api/v2/tips.py` - Suporte a webhook
- `src/main.py` - Registro do router de webhook status

## Exemplo de Uso Completo

### 1. Iniciar Processamento Assíncrono

```bash
curl -X POST "http://localhost:8000/api/v2/units/unit_123/vocabulary" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://meuapp.com/webhook",
    "target_count": 25,
    "difficulty_level": "intermediate"
  }'
```

**Resposta imediata:**
```json
{
  "message": "Requisição aceita para processamento assíncrono", 
  "task_id": "vocab_1724425123456_abc12345",
  "status": "processing"
}
```

### 2. Consultar Status (Opcional)

```bash
curl "http://localhost:8000/api/v2/webhooks/tasks/vocab_1724425123456_abc12345/status"
```

### 3. Receber Webhook

Seu endpoint receberá automaticamente o resultado quando concluído:

```json
{
  "task_id": "vocab_1724425123456_abc12345",
  "status": "completed", 
  "success": true,
  "result": {
    "data": {
      "vocabulary": {...},
      "generation_stats": {...}
    }
  }
}
```

## Benefícios

1. **Não-blocking**: Não trava a conexão durante processamento longo
2. **Confiável**: Sistema de retry para entrega de webhooks
3. **Monitorável**: Endpoints para consultar status das tarefas
4. **Compatível**: Funciona junto com o comportamento síncrono existente
5. **Seguro**: Validação de URLs de webhook para prevenir ataques

## Considerações de Performance

- Tarefas são executadas em background usando `asyncio.create_task()`
- Memory cleanup automático após 1 hora
- Timeout de 5 minutos para entrega de webhooks
- Rate limiting aplicado normalmente

## Logs

O sistema gera logs detalhados para debugging:

```
INFO: Iniciando tarefa assíncrona: vocab_1724425123456_abc12345
INFO: Executando função para tarefa: vocab_1724425123456_abc12345  
INFO: Tarefa vocab_1724425123456_abc12345 completada em 127.45s
INFO: Webhook enviado com sucesso para tarefa vocab_1724425123456_abc12345: 200
```