import logging
import os

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.google import Gemini
from google.auth import default as google_auth_default
from google.auth.exceptions import DefaultCredentialsError

from app.core.config import settings
from app.knowledge.kb import build_knowledge
from app.tools.safety import SafetyTools
from app.tools.vehicle_intake import VehicleIntakeTools

logger = logging.getLogger(__name__)

try:
    from agno.tools.eleven_labs import ElevenLabsTools
except Exception:  # pragma: no cover
    ElevenLabsTools = None


def _select_genai_backend():
    """Pick Vertex AI only when credentials are available, otherwise fall back to API key."""
    use_vertex = settings.GOOGLE_GENAI_USE_VERTEXAI
    project = settings.GOOGLE_CLOUD_PROJECT
    location = settings.GOOGLE_CLOUD_LOCATION

    if not use_vertex:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"
        return False, None, None

    missing = [
        name
        for name, value in {
            "GOOGLE_CLOUD_PROJECT": project,
            "GOOGLE_CLOUD_LOCATION": location,
        }.items()
        if not value
    ]
    if missing:
        logger.warning(
            "Vertex AI requested but missing %s. Falling back to Google AI Studio API key.",
            ", ".join(missing),
        )
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"
        return False, None, None

    try:
        google_auth_default()
    except DefaultCredentialsError as exc:
        logger.warning(
            "Vertex AI requested but Application Default Credentials not found (%s). "
            "Run `gcloud auth application-default login` or set GOOGLE_APPLICATION_CREDENTIALS. "
            "Falling back to Google AI Studio API key.",
            exc,
        )
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"
        return False, None, None

    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", location)
    logger.info("Using Vertex AI (project=%s, location=%s)", project, location)
    return True, project, location


def _build_tools():
    tools = [
        VehicleIntakeTools(),
        SafetyTools(),
    ]

    eleven_key = getattr(settings, "ELEVEN_LABS_API_KEY", None) or os.getenv("ELEVEN_LABS_API_KEY")
    if ElevenLabsTools and eleven_key:
        tools.append(
            ElevenLabsTools(
                api_key=eleven_key,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                model_id="eleven_multilingual_v2",
                target_directory="audio_generations",
            )
        )
    else:
        if not eleven_key:
            logger.warning("ELEVEN_LABS_API_KEY not set; ElevenLabsTools disabled.")
        if ElevenLabsTools is None:
            logger.warning("agno.tools.eleven_labs import failed; ElevenLabsTools disabled.")

    return tools


def build_base_agent(
    agent_id: str,
    name: str,
    instructions: str,
    mode_label: str,
) -> Agent:
    use_vertex, project, location = _select_genai_backend()

    model = Gemini(
        id="gemini-2.0-flash",
        vertexai=use_vertex,
        project_id=project,
        location=location,
        api_key=settings.GOOGLE_API_KEY if not use_vertex else None,
    )

    db = PostgresDb(db_url=settings.DB_URL)
    knowledge = build_knowledge()

    tools = _build_tools()

    # Bloco global de "gatilho de áudio" (isso é o que faltava no comportamento do agente).
    audio_policy = """
Política de resposta por voz (obrigatório):
- Se o usuário solicitar áudio/voz (ex.: "áudio", "por voz", "fale", "responda com áudio"),
  você DEVE chamar a ferramenta ElevenLabs `text_to_speech` usando como input o texto final da sua resposta.
- O texto para narração deve ser curto, direto, sem markdown e sem listas longas.
""".strip()

    return Agent(
        id=agent_id,
        name=name,
        model=model,
        db=db,
        knowledge=knowledge,
        search_knowledge=True,
        add_history_to_context=True,
        enable_user_memories=True,
        markdown=True,
        tools=tools,
        instructions=f"""
Você é um assistente especializado em mecânica automotiva.
Modo: {mode_label}

Regras obrigatórias:
- Sempre priorize segurança: se houver risco (freios, direção, airbags, vazamento de combustível, cheiro forte, fumaça,
  superaquecimento severo, alta-voltagem em híbridos/EV), oriente parar e tratar segurança.
- Nunca invente especificações do veículo: se faltar dado, pergunte.
- Quando usar conhecimento (RAG), cite as fontes com base em URLs/metadados quando estiverem disponíveis no contexto.
- Seja objetivo: primeiro triagem, depois hipótese, depois verificação, depois próximos passos.
- Respostas curtas por padrão.

{audio_policy}

{instructions}
""".strip(),
    )
