from functools import lru_cache
from fastapi import HTTPException

from app.agents.investigative import build_agent as build_investigative
from app.agents.mechanic import build_agent as build_mechanic
from app.agents.pro import build_agent as build_pro
from app.agents.normal import build_agent as build_normal

VALID_MODES = {"investigative", "mechanic", "pro", "normal"}

@lru_cache(maxsize=8)
def _cached(mode: str):
    if mode == "investigative":
        return build_investigative()
    if mode == "mechanic":
        return build_mechanic()
    if mode == "pro":
        return build_pro()
    if mode == "normal":
        return build_normal()
    raise ValueError(mode)

def get_agent_by_mode(mode: str):
    mode = (mode or "").strip().lower()
    if mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Use one of: {sorted(VALID_MODES)}")
    return _cached(mode)

def get_all_agents():
    # Importante: usar os mesmos objetos cacheados para evitar duplicar conexões/estado
    return [
        _cached("investigative"),
        _cached("mechanic"),
        _cached("pro"),
        _cached("normal"),
    ]
