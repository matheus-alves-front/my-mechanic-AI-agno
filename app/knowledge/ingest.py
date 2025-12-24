import os
import json
import asyncio
import logging
from typing import Dict, Any
from pathlib import Path

from app.knowledge.kb import build_knowledge
from app.core.config import settings

log = logging.getLogger("ingest")

def _derive_metadata(entry: Dict[str, Any]) -> Dict[str, Any]:
    url = (entry.get("url") or "").strip()
    title = (entry.get("title") or "").strip()
    scraped_at = (entry.get("scraped_at") or "").strip()

    domain = ""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
    except Exception:
        domain = ""

    # Heurísticas simples (você pode sofisticar depois)
    content = (entry.get("content") or "").lower()
    category = "general"
    if "obd" in url.lower() or "trouble" in url.lower() or "dtc" in content:
        category = "obd_dtc"
    elif "wiring" in content or "voltage" in content or "sensor" in content:
        category = "electrical"
    elif "maintenance" in url.lower() or "manutenc" in content:
        category = "maintenance"

    lang = "pt"
    if any(w in content for w in ["the", "and", "engine", "vehicle", "diagnostic"]):
        lang = "en"

    return {
        "url": url,
        "title": title,
        "domain": domain,
        "category": category,
        "lang": lang,
        "scraped_at": scraped_at,
    }

async def ingest_jsonl_dir(dataset_dir: str, skip_if_exists: bool = True, concurrency: int = 8) -> None:
    kb = build_knowledge()

    root = Path(dataset_dir)
    if not root.exists():
        raise RuntimeError(f"Dataset dir not found: {dataset_dir}")

    jsonl_files = sorted([p for p in root.rglob("*.jsonl") if p.is_file()])
    log.info("found_jsonl_files", extra={"count": len(jsonl_files), "dir": str(root)})

    sem = asyncio.Semaphore(concurrency)

    async def upsert_entry(entry: Dict[str, Any]) -> None:
        text = (entry.get("content") or "").strip()
        if len(text) < 300:
            return

        meta = _derive_metadata(entry)
        # Nome único de content: usa URL + hash leve
        uid = meta["url"] or meta["title"] or "unknown"
        name = f"mec::{uid}"

        # Evita reinsert se solicitado (quando contents_db tem registro)
        if skip_if_exists and meta.get("url"):
            try:
                # search por url em metadata (depende do ContentsDB)
                # Se não existir método pronto, o add_content_async irá deduplicar por name/url
                pass
            except Exception:
                pass

        # add_content_async suporta text_content (conteúdo direto), evitando Reader custom.
        # Isso mantém tudo dentro do sistema de Knowledge/ContentsDB/VectorDB do Agno.
        await kb.add_content_async(
            name=name,
            text_content=text,
            metadata=meta,
        )

    async def process_file(path: Path) -> None:
        async with sem:
            log.info("ingesting_file", extra={"file": str(path)})
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    await upsert_entry(entry)

    # Processa sequencial por arquivo, concorrência por semáforo de arquivo
    tasks = [asyncio.create_task(process_file(p)) for p in jsonl_files]
    await asyncio.gather(*tasks)

def run_ingest() -> None:
    asyncio.run(
        ingest_jsonl_dir(
            dataset_dir=settings.DATASET_DIR,
            skip_if_exists=bool(settings.INGEST_SKIP_IF_EXISTS),
            concurrency=int(settings.INGEST_CONCURRENCY),
        )
    )

if __name__ == "__main__":
    run_ingest()
