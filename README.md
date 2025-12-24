# Car Mechanic RAG (Agno + Gemini + PgVector) — Produção

Este serviço expõe 4 modos de agente:
1) Investigativo (triagem guiada por perguntas)
2) Mecânico (explica e orienta manutenção preventiva/diagnóstico)
3) Mecânico PRO (apoio técnico para mecânicos)
4) IA Normal (Q&A geral sobre carros)

Stack:
- Agno Agents + Knowledge (RAG)
- Gemini (LLM)
- GeminiEmbedder (Embeddings)
- PgVector (Postgres + pgvector)
- Persistência de sessões/memórias via PostgresDb (Agno)

## Pré-requisitos
- Docker e Docker Compose
- Uma chave `GOOGLE_API_KEY` (Google AI Studio) ou credenciais Vertex AI

## Setup rápido (produção via Docker)
1) Copie `.env.example` para `.env` e preencha:
   - GOOGLE_API_KEY
   - ADMIN_API_KEY
   - JWT_SECRET
2) Suba:
   - `make docker-up`
3) Ingestão do dataset (JSONL):
   - Monte sua pasta `./dataset_mecanica_full` com seus `.jsonl`
   - `make ingest`

## API
### Auth
- `POST /auth/token` com header `x-admin-key: <ADMIN_API_KEY>`
  Retorna JWT.

### Chat
- `POST /chat/{mode}` onde `{mode}` ∈ `investigative | mechanic | pro | normal`
  Header: `Authorization: Bearer <JWT>`
  Body:
  {
    "user_id": "u123",
    "session_id": "s456",
    "message": "meu carro está falhando..."
  }

### Health
- `GET /health`

## Segurança (importante)
Este sistema nunca deve instruir procedimentos perigosos sem alertas.
Quando o problema envolver freios, direção, airbags, alta-voltagem (híbridos/EV), combustível/vazamentos,
o agente deve recomendar interromper o uso e procurar um profissional.
