Streamlit UI  ──HTTP──▶  FastAPI  ──▶  start_jupyter.sh / stop_jupyter.sh
                              │
                              └── reads /var/run/jupyter_instances.json
systemd
 ├── jupyter-backend (FastAPI :8000)
 └── jupyter-frontend (Streamlit :8501)
         ↓
        Nginx (443)
         ↓
  /api/    /ui/    /jupyter/<port>/
