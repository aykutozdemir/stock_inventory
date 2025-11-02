"""
Root application helpers for tests and external callers.

Exposes:
- load_hardware_config(): read hardware_config.json and summarize
- get_llm(): return initialized LlamaCpp instance via AIService
"""

import json
import os
from typing import Any, Dict

from backend.services.ai_service import AIService


_ai_service: AIService | None = None


def _get_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def load_hardware_config() -> Dict[str, Any]:
    """Load hardware_config.json and return a summary dict expected by tests."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(project_root, "hardware_config.json")

    # Defaults if file missing
    config: Dict[str, Any] = {
        "n_threads": 4,
        "n_ctx": 2048,
        "gpu_layers": 0,
        "detected_vram_mb": 0,
        "detected_cpu_threads": 4,
    }

    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                config.update(loaded)
        except Exception:
            # Keep defaults if unreadable
            pass

    use_gpu = bool(config.get("gpu_layers", 0) != 0)
    vram = int(config.get("detected_vram_mb", 0) or 0)
    threads = int(config.get("detected_cpu_threads", config.get("n_threads", 4)))
    description = f"CPU {threads} threads, VRAM {vram} MB"

    config["use_gpu"] = use_gpu
    config["description"] = description
    return config


def get_llm():
    """Return the initialized LLM instance from AIService (may be None if no model)."""
    service = _get_service()
    if service.llm is None:
        raise RuntimeError("LLM is not initialized. Ensure models exist under 'models/'.")
    return service.llm


