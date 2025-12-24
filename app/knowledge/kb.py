from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.db.postgres import PostgresDb

from app.core.config import settings

def build_knowledge() -> Knowledge:
    # Embedder Gemini com batch para reduzir chamadas (importante em datasets grandes)
    embedder = GeminiEmbedder(
        id=settings.EMBED_MODEL,
        dimensions=settings.EMBED_DIMENSIONS,
        enable_batch=bool(settings.EMBED_BATCH),
        batch_size=int(settings.EMBED_BATCH_SIZE),
    )

    vector_db = PgVector(
        db_url=settings.DB_URL,
        table_name=settings.KB_TABLE,
        embedder=embedder,
    )

    # Contents DB (metadados) recomendado em produção via Postgres. :contentReference[oaicite:2]{index=2}
    contents_db = PostgresDb(db_url=settings.DB_URL)

    return Knowledge(
        name="mechanic-knowledge-base",
        description="Knowledge base de mecânica automotiva (motor, elétrica, manutenção, OBD, troubleshooting).",
        vector_db=vector_db,
        contents_db=contents_db,
        max_results=int(settings.KB_MAX_RESULTS),
    )
