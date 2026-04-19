"""Application settings: env + ``.env``, validated at import/instantiation."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration (environment variables and optional ``.env``)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="gita-backend", validation_alias="APP_NAME")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    data_dir: Path = Field(default=Path("./data"), validation_alias="DATA_DIR")
    database_path: Path | None = Field(default=None, validation_alias="DATABASE_PATH")

    fts_candidate_limit: int = Field(default=24, ge=1, validation_alias="FTS_CANDIDATE_LIMIT")
    final_verse_count: int = Field(default=3, ge=1, le=10, validation_alias="FINAL_VERSE_COUNT")
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        validation_alias="EMBEDDING_MODEL",
    )
    embeddings_artifact_path: Path | None = Field(
        default=None,
        validation_alias="EMBEDDINGS_ARTIFACT_PATH",
        description="Path to verses_embeddings.npz; default DATA_DIR/verses_embeddings.npz",
    )
    semantic_rerank_enabled: bool = Field(default=True, validation_alias="SEMANTIC_RERANK_ENABLED")

    ollama_base_url: str = Field(default="http://127.0.0.1:11434", validation_alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:14b", validation_alias="OLLAMA_MODEL")
    ollama_connect_timeout_s: float = Field(
        default=5.0,
        ge=0.5,
        le=120.0,
        validation_alias="OLLAMA_CONNECT_TIMEOUT_S",
    )
    ollama_read_timeout_s: float = Field(
        default=120.0,
        ge=5.0,
        le=900.0,
        validation_alias="OLLAMA_READ_TIMEOUT_S",
    )
    ollama_write_timeout_s: float = Field(
        default=60.0,
        ge=2.0,
        le=300.0,
        validation_alias="OLLAMA_WRITE_TIMEOUT_S",
    )
    ollama_generation_deadline_s: float = Field(
        default=64.0,
        ge=5.0,
        le=900.0,
        validation_alias="OLLAMA_GENERATION_DEADLINE_S",
        description="Wall-clock cap for one streamed explanation (asyncio timeout around Ollama).",
    )
    ollama_temperature: float = Field(
        default=0.12,
        ge=0.0,
        le=1.5,
        validation_alias="OLLAMA_TEMPERATURE",
        description="Low temperature for stable, concise decoding (latency-friendly).",
    )
    ollama_top_p: float = Field(
        default=0.82,
        ge=0.1,
        le=1.0,
        validation_alias="OLLAMA_TOP_P",
    )
    ollama_repeat_penalty: float = Field(
        default=1.15,
        ge=1.0,
        le=2.0,
        validation_alias="OLLAMA_REPEAT_PENALTY",
    )
    ollama_num_predict: int = Field(
        default=120,
        ge=32,
        le=512,
        validation_alias="OLLAMA_NUM_PREDICT",
        description="Decode cap (tokens); keep aligned with validation max words for lower latency.",
    )
    ollama_keep_alive: str = Field(
        default="30m",
        validation_alias="OLLAMA_KEEP_ALIVE",
        description=(
            "Ollama ``keep_alive`` directive (e.g. ``30m``, ``2h``, ``-1`` for always). Sent with each "
            "/api/chat request so the model stays resident between calls and the first-token latency "
            "does not include model reload time. Set to empty string to omit."
        ),
    )

    guidance_generation_max_verses: int = Field(
        default=1,
        ge=1,
        le=2,
        validation_alias="GUIDANCE_GENERATION_MAX_VERSES",
        description="Verses embedded in the Ollama prompt (retrieval may still return more cards to the client).",
    )
    guidance_burnout_generation_max_verses: int = Field(
        default=1,
        ge=1,
        le=2,
        validation_alias="GUIDANCE_BURNOUT_GENERATION_MAX_VERSES",
        description=(
            "Burnout-specific override for verses in the generation prompt. Keeps the burnout "
            "path narrow without affecting other intents, and supports A/B investigation of "
            "the burnout latency outlier (1 = primary only, 2 = primary + support)."
        ),
    )
    guidance_burnout_debug_log: bool = Field(
        default=True,
        validation_alias="GUIDANCE_BURNOUT_DEBUG_LOG",
        description=(
            "When true, emits a dedicated ``guidance_burnout_debug`` log record with full prompt "
            "telemetry for the burnout path so cold-start and context-size effects can be "
            "diagnosed without affecting other intents."
        ),
    )
    guidance_validation_max_retries: int = Field(
        default=1,
        ge=1,
        le=8,
        validation_alias="GUIDANCE_VALIDATION_MAX_RETRIES",
        description="Ollama regeneration attempts when post-generation validation fails (1 = no retry).",
    )
    guidance_validation_min_words: int = Field(
        default=20,
        ge=12,
        le=120,
        validation_alias="GUIDANCE_VALIDATION_MIN_WORDS",
        description="Minimum word count for an accepted explanation (after polish); paired with max caps.",
    )
    guidance_validation_max_words: int = Field(
        default=72,
        ge=50,
        le=200,
        validation_alias="GUIDANCE_VALIDATION_MAX_WORDS",
        description="Hard maximum words for an accepted explanation.",
    )
    guidance_validation_max_sentences: int = Field(
        default=3,
        ge=2,
        le=8,
        validation_alias="GUIDANCE_VALIDATION_MAX_SENTENCES",
        description="Maximum sentences for an accepted explanation.",
    )

    guidance_rate_limit_per_minute: int = Field(
        default=60,
        ge=0,
        validation_alias="GUIDANCE_RATE_LIMIT_PER_MINUTE",
        description="Per client IP sliding window; 0 disables.",
    )
    guidance_stream_chunk_delay_s: float = Field(
        default=0.0,
        ge=0.0,
        le=3.0,
        validation_alias="GUIDANCE_STREAM_CHUNK_DELAY_S",
        description="Pause after each streamed chunk; keep 0 for lowest user-visible latency.",
    )
    guidance_eval_debug: bool = Field(
        default=False,
        validation_alias="GUIDANCE_EVAL_DEBUG",
        description=(
            "When true, all guidance streams behave like request.eval_debug=true (diagnostics + no generic "
            "fallback masking). Prefer per-request eval_debug for captures."
        ),
    )
    guidance_feedback_log_path: Path | None = Field(
        default=None,
        validation_alias="GUIDANCE_FEEDBACK_LOG_PATH",
        description=(
            "If set, POST /api/v1/guidance/feedback appends one JSON object per line (NDJSON). "
            "Relative paths resolve under DATA_DIR."
        ),
    )
    retrieve_cache_max_entries: int = Field(
        default=128,
        ge=0,
        validation_alias="RETRIEVE_CACHE_MAX_ENTRIES",
    )
    retrieve_cache_ttl_s: float = Field(
        default=60.0,
        ge=0.0,
        le=3600.0,
        validation_alias="RETRIEVE_CACHE_TTL_S",
    )

    # Comma-separated browser origins (e.g. http://localhost:3000). Empty + ENVIRONMENT=development
    # uses a small localhost allowlist so NEXT_PUBLIC_API_BASE_URL dev setups work without a proxy.
    cors_allowed_origins: str = Field(default="", validation_alias="CORS_ALLOWED_ORIGINS")

    @field_validator("data_dir", mode="before")
    @classmethod
    def expand_data_dir(cls, v: str | Path) -> Path:
        return Path(v).expanduser().resolve(strict=False)

    @field_validator("database_path", "guidance_feedback_log_path", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: str | Path | None) -> Path | str | None:
        if v == "" or v is None:
            return None
        return v

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        u = (v or "INFO").strip().upper()
        if u not in logging._nameToLevel:
            return "INFO"
        return u

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_base_url(cls, v: str) -> str:
        s = (v or "").strip().rstrip("/")
        if not s.startswith(("http://", "https://")):
            raise ValueError("OLLAMA_BASE_URL must be an absolute http(s) URL")
        return s

    @field_validator("fts_candidate_limit")
    @classmethod
    def cap_fts_candidate_limit(cls, v: int) -> int:
        if v > 256:
            raise ValueError("FTS_CANDIDATE_LIMIT must be <= 256")
        return v

    @field_validator("environment")
    @classmethod
    def normalize_environment(cls, v: str) -> str:
        return (v or "development").strip().lower()

    def resolved_database_path(self) -> Path:
        if self.database_path is not None:
            return Path(self.database_path).expanduser().resolve(strict=False)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return (self.data_dir / "gita.db").resolve(strict=False)

    def resolved_embeddings_npz_path(self) -> Path:
        if self.embeddings_artifact_path is not None:
            return Path(self.embeddings_artifact_path).expanduser().resolve(strict=False)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return (self.data_dir / "verses_embeddings.npz").resolve(strict=False)

    def resolved_guidance_feedback_log_path(self) -> Path | None:
        if self.guidance_feedback_log_path is None:
            return None
        p = Path(self.guidance_feedback_log_path).expanduser()
        if not p.is_absolute():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            return (self.data_dir / p).resolve(strict=False)
        return p.resolve(strict=False)

    def cors_origins(self) -> list[str]:
        raw = (self.cors_allowed_origins or "").strip()
        if raw:
            return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
        if self.environment == "development":
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ]
        return []


@lru_cache
def get_settings() -> Settings:
    return Settings()
