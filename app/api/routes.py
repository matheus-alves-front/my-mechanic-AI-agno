from fastapi import APIRouter, Header, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import create_jwt, verify_jwt
from app.api.schemas import TokenResponse, ChatRequest, ChatResponse
from app.agents.registry import get_agent_by_mode

router = APIRouter()
auth_scheme = HTTPBearer(auto_error=True)

def require_jwt(creds: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    payload = verify_jwt(creds.credentials)
    return payload

@router.post("/auth/token", response_model=TokenResponse)
def mint_token(x_admin_key: str = Header(default="")):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = create_jwt(sub="api-client", extra={"role": "client"})
    return TokenResponse(access_token=token)

@router.post("/chat/{mode}", response_model=ChatResponse)
def chat(mode: str, req: ChatRequest, _jwt=Depends(require_jwt)):
    agent = get_agent_by_mode(mode)

    # Agno sessions + memory via PostgresDb: pass user_id/session_id
    # (Agno possui suporte nativo a sessões/memórias quando db é configurado)
    result = agent.run(
        req.message,
        user_id=req.user_id,
        session_id=req.session_id,
    )

    # result pode ser string ou RunOutput; normalizamos.
    answer = getattr(result, "content", None) or getattr(result, "response", None) or str(result)

    return ChatResponse(mode=mode, user_id=req.user_id, session_id=req.session_id, answer=answer)
