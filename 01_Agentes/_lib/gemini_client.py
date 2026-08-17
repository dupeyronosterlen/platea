"""
Cliente Gemini compartido — opcionalmente vía Cloudflare AI Gateway.

Uso:
    from gemini_client import make_client, GEMINI_MODEL
    client = make_client()

Env:
  GCP_PROJECT, GCP_LOCATION (default us-central1)
  GEMINI_MODEL (default gemini-2.5-pro)
  CF_AI_GATEWAY_BASE  — si está, reescribe la base URL a:
      https://gateway.ai.cloudflare.com/v1/{account}/{gateway}/google-vertex-ai
  CF_AIG_TOKEN        — opcional; si el gateway exige auth, se manda
      como header cf-aig-authorization
"""
from __future__ import annotations

import os
from pathlib import Path

from google import genai
from google.genai import types


def _load_shared_env() -> None:
    """Carga ~/.platea/cf.env y config compartida sin pisar vars ya seteadas."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    platea = Path.home() / ".platea" / "cf.env"
    if platea.exists():
        load_dotenv(platea, override=False)
    root = Path(__file__).resolve().parents[2]
    shared = root / "config" / "ai-gateway.env"
    if shared.exists():
        load_dotenv(shared, override=False)


def gateway_base_url() -> str | None:
    _load_shared_env()
    base = (os.getenv("CF_AI_GATEWAY_BASE") or "").strip().rstrip("/")
    return base or None


def make_client(
    *,
    project: str | None = None,
    location: str | None = None,
) -> genai.Client:
    """Client Vertex; si hay CF_AI_GATEWAY_BASE, pasa por AI Gateway."""
    _load_shared_env()
    project = project or os.environ["GCP_PROJECT"]
    location = location or os.getenv("GCP_LOCATION", "us-central1")
    gw = gateway_base_url()

    kwargs: dict = {
        "vertexai": True,
        "project": project,
        "location": location,
    }
    if gw:
        headers = {}
        aig = (os.getenv("CF_AIG_TOKEN") or "").strip()
        if aig:
            headers["cf-aig-authorization"] = f"Bearer {aig}"
        kwargs["http_options"] = types.HttpOptions(
            base_url=gw,
            headers=headers or None,
        )
    return genai.Client(**kwargs)


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-pro")


GEMINI_MODEL = gemini_model()  # conveniencia al importar
