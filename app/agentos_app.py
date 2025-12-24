from agno.os import AgentOS
from app.agents.registry import get_all_agents

def build_agent_os() -> AgentOS:
    return AgentOS(
        id="car-mechanic-agentos",
        agents=get_all_agents(),
        run_hooks_in_background=True,
        telemetry=False,
        cors_allowed_origins=[
            "https://os.agno.com",
            "http://localhost:3000",
        ],
        description="AgentOS para agentes de mecânica automotiva.",
    )

agent_os = build_agent_os()
