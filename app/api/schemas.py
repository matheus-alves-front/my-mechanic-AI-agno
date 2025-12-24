from pydantic import BaseModel, Field

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Identificador do usuário no seu sistema")
    session_id: str = Field(..., description="Identificador da sessão de conversa")
    message: str = Field(..., min_length=1)

class ChatResponse(BaseModel):
    mode: str
    user_id: str
    session_id: str
    answer: str
