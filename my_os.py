import os
import sys
from app.agentos_app import agent_os

# Permite: make dev-os / make run-os
# Ex.: AGENTOS_PORT=7777 python -m my_os --reload
if __name__ == "__main__":
    reload = "--reload" in sys.argv
    port = int(os.getenv("AGENTOS_PORT", "7777"))

    # O AgentOS internamente usa uvicorn e vai importar "my_os:app"
    agent_os.serve(app="my_os:app", port=port, reload=reload)

# Importável por uvicorn (via agent_os.serve(app="my_os:app", ...))
app = agent_os.get_app()
