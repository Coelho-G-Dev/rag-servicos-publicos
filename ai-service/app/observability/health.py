from typing import Dict, Any
from app.db.postgres import check_db_health


def get_health_status() -> Dict[str, Any]:
    db_ok = check_db_health()
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": "rag-ai-service",
        "checks": {
            "database": "connected" if db_ok else "unavailable",
            "model": "all-MiniLM-L6-v2"
        }
    }
