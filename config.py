"""
config.py — Merkezi Uygulama Ayarları
Dinamik yapılandırma (60s TTL): Firebase Firestore `aimunazara` ->
`system_config/llm` ve `system_config/firecrawl`.
Ortam değişkenleri yalnızca offline/fallback varsayılanlarıdır.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Gemini Model Yapılandırması (Fallback Varsayılanları)
# ──────────────────────────────────────────────

DEFAULT_MODEL = "gemini-4-hydrogen"
DEFAULT_THINKING_LEVEL = "high"

FALLBACK_MODELS = [
    "gemini-4-carbon",
    "gemini-4-argon",
]

ALLOWED_MODELS = [DEFAULT_MODEL] + FALLBACK_MODELS

DEFAULT_ALLOWED_ORIGINS = [
    "https://firecrawl-mcp.web.app",
    "https://firecrawl-mcp.firebaseapp.com",
    "https://firecrawl-ai-summarizer-gj6zwiml4a-ez.a.run.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
DEFAULT_RATE_LIMIT_PER_MINUTE = 10

# ──────────────────────────────────────────────
# Zaman Aşımı & Sunucu Ayarları
# ──────────────────────────────────────────────

LLM_TIMEOUT_MS = 120_000  # 120 saniye
PIPELINE_TIMEOUT_S = 120.0
DEFAULT_PORT = 8000

FIRESTORE_CONFIG_PROJECT = os.getenv("FIRESTORE_CONFIG_PROJECT", "aimunazara")
_CONFIG_TTL_SECONDS = 60

_config_lock = threading.Lock()
_last_loaded_at = 0.0
_cached_config: dict[str, Any] = {}


def is_firestore_config_enabled() -> bool:
    return os.getenv("FIRESTORE_CONFIG_ENABLED", "true").strip().lower() not in {"false", "0", "no", "off"}


def _decode_firestore_value(raw: Any) -> Any:
    if not isinstance(raw, dict):
        return raw
    if "stringValue" in raw:
        return raw["stringValue"]
    if "booleanValue" in raw:
        return bool(raw["booleanValue"])
    if "integerValue" in raw:
        return int(raw["integerValue"])
    if "doubleValue" in raw:
        return float(raw["doubleValue"])
    if "nullValue" in raw:
        return None
    if "arrayValue" in raw:
        return [_decode_firestore_value(v) for v in raw["arrayValue"].get("values", [])]
    if "mapValue" in raw:
        return {k: _decode_firestore_value(v) for k, v in raw["mapValue"].get("fields", {}).items()}
    return raw


def _parse_firestore_doc(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: _decode_firestore_value(v) for k, v in payload.get("fields", {}).items()}


def _env_gemini_keys() -> list[str]:
    keys: list[str] = []
    for var in ("GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.getenv(var, "").strip()
        if val and val not in keys:
            keys.append(val)
    return keys


def _fallback_runtime_config() -> dict[str, Any]:
    return {
        "gemini_keys": _env_gemini_keys(),
        "firecrawl_api_key": os.getenv("FIRECRAWL_API_KEY", "").strip(),
        "active_model": os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL,
        "thinking_level": os.getenv("THINKING_LEVEL", "").strip().lower() or DEFAULT_THINKING_LEVEL,
        "fallback_models": list(FALLBACK_MODELS),
        "allowed_models": list(ALLOWED_MODELS),
        "allowed_origins": list(DEFAULT_ALLOWED_ORIGINS),
        "rate_limit_per_minute": DEFAULT_RATE_LIMIT_PER_MINUTE,
        "loaded_from_firestore": False,
    }


def _fetch_firestore_docs(project_id: str, doc_ids: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    import google.auth
    import google.auth.transport.requests

    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/datastore"])
    creds.refresh(google.auth.transport.requests.Request())
    headers = {"Authorization": f"Bearer {creds.token}"}
    out: dict[str, dict[str, Any]] = {}
    with httpx.Client(timeout=8.0) as client:
        for doc_id in doc_ids:
            url = (
                f"https://firestore.googleapis.com/v1/projects/{project_id}"
                f"/databases/(default)/documents/system_config/{doc_id}"
            )
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                out[doc_id] = _parse_firestore_doc(resp.json())
            elif resp.status_code != 404:
                logger.warning("Firestore system_config/%s HTTP %s", doc_id, resp.status_code)
    return out


def _clean_str_list(raw: Any, fallback: list[str]) -> list[str]:
    if isinstance(raw, list):
        cleaned = [str(x).strip() for x in raw if str(x).strip()]
        if cleaned:
            return cleaned
    if isinstance(raw, str) and raw.strip():
        cleaned = [x.strip() for x in raw.split(",") if x.strip()]
        if cleaned:
            return cleaned
    return list(fallback)


def get_runtime_config(force: bool = False) -> dict[str, Any]:
    """Return dynamic config from Firestore (60s TTL) with env/default fallback."""
    global _last_loaded_at, _cached_config

    if not is_firestore_config_enabled():
        return _fallback_runtime_config()

    now = time.monotonic()
    if not force and _cached_config and _last_loaded_at > 0 and (now - _last_loaded_at) < _CONFIG_TTL_SECONDS:
        return _cached_config

    with _config_lock:
        now = time.monotonic()
        if not force and _cached_config and _last_loaded_at > 0 and (now - _last_loaded_at) < _CONFIG_TTL_SECONDS:
            return _cached_config

        base = _fallback_runtime_config()
        try:
            docs = _fetch_firestore_docs(FIRESTORE_CONFIG_PROJECT, ("llm", "firecrawl"))
            llm_doc = docs.get("llm", {})
            fc_doc = docs.get("firecrawl", {})

            fs_keys: list[str] = []
            for kname in ("gemini_api_key_primary", "gemini_api_key_secondary"):
                val = str(llm_doc.get(kname) or "").strip()
                if val and val not in fs_keys:
                    fs_keys.append(val)

            active_model = str(fc_doc.get("active_model") or llm_doc.get("active_model") or "").strip() or base["active_model"]
            thinking_level = str(fc_doc.get("thinking_level") or llm_doc.get("active_thinking_level") or "").strip().lower() or base["thinking_level"]
            fallback_models = _clean_str_list(fc_doc.get("fallback_models") or llm_doc.get("fallback_models"), FALLBACK_MODELS)
            allowed_models = _clean_str_list(fc_doc.get("allowed_models"), [active_model, *fallback_models])
            if active_model not in allowed_models:
                allowed_models.insert(0, active_model)
            allowed_origins = _clean_str_list(fc_doc.get("allowed_origins"), DEFAULT_ALLOWED_ORIGINS)
            fc_key = str(fc_doc.get("firecrawl_api_key") or "").strip() or base["firecrawl_api_key"]
            rate_raw = fc_doc.get("rate_limit_per_minute")
            rate_limit = int(rate_raw) if isinstance(rate_raw, (int, float)) and int(rate_raw) > 0 else DEFAULT_RATE_LIMIT_PER_MINUTE

            _cached_config = {
                "gemini_keys": fs_keys if fs_keys else base["gemini_keys"],
                "firecrawl_api_key": fc_key,
                "active_model": active_model,
                "thinking_level": thinking_level,
                "fallback_models": fallback_models,
                "allowed_models": allowed_models,
                "allowed_origins": allowed_origins,
                "rate_limit_per_minute": rate_limit,
                "loaded_from_firestore": bool(llm_doc or fc_doc),
            }
            _last_loaded_at = time.monotonic()
            return _cached_config
        except Exception as exc:
            logger.warning("Firestore firecrawl config okunamadi (fallback kullaniliyor): %s", exc)
            if not _cached_config:
                _cached_config = base
            _last_loaded_at = time.monotonic() - (_CONFIG_TTL_SECONDS - 10)
            return _cached_config


def normalize_thinking_level(model_name: str, level: str | None) -> str | None:
    """Clamp thinking levels for Gemini 4 models strictly to LOW, MEDIUM, or HIGH."""
    if not level or not str(model_name).startswith("gemini-4"):
        return None
    raw = str(level).strip().upper()
    if raw in {"XHIGH", "MAX"}:
        return "HIGH"
    if raw in {"MINIMAL", "OFF", "NONE"}:
        return "LOW"
    if raw in {"LOW", "MEDIUM", "HIGH"}:
        return raw
    return "HIGH"
