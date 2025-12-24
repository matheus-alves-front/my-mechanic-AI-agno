from app.agents.common import build_base_agent

NORMAL_INSTRUCTIONS = """
Objetivo: Q&A geral sobre carros, mecânica, elétrica, manutenção e conceitos.

Comportamento:
- Respostas diretas, com exemplos.
- Se a pergunta envolver diagnóstico real, colete dados mínimos do veículo e sintomas.
"""

def build_agent():
    return build_base_agent(
        agent_id="normal",
        name="CarKnowledgeAssistant",
        instructions=NORMAL_INSTRUCTIONS,
        mode_label="IA Normal",
    )
