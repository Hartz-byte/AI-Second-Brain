"""
cache_service.py — Redis-backed caching with graceful fallback.

If REDIS_URL is not set or Redis is unreachable, all operations are no-ops.
Cache keys use SHA-256 hashing for determinism and length normalisation.
"""
import json
import hashlib
import logging
from backend.config import REDIS_URL

logger = logging.getLogger(__name__)

# Try to connect to Redis; if it fails, _redis stays None
_redis = None
if REDIS_URL:
    try:
        import redis as redis_lib
        # Auto-fix: RedisLabs gives "host:port" without scheme — add it
        _url = REDIS_URL
        if not any(_url.startswith(s) for s in ("redis://", "rediss://", "unix://")):
            _url = f"redis://{_url}"
        _redis = redis_lib.from_url(_url, decode_responses=True, socket_connect_timeout=5)
        _redis.ping()
        logger.info("Redis connected successfully.")
    except Exception as e:
        logger.warning(f"Redis unavailable — caching disabled. Reason: {e}")
        _redis = None


def _make_key(prefix: str, *parts: str) -> str:
    """Create a stable, short cache key from variable-length inputs."""
    raw = "|".join(parts)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:24]
    return f"asb:{prefix}:{digest}"


# ── Public API ──────────────────────────────────────────────────────

def get(prefix: str, *key_parts: str):
    """Return cached value (as Python obj) or None."""
    if _redis is None:
        return None
    try:
        value = _redis.get(_make_key(prefix, *key_parts))
        return json.loads(value) if value else None
    except Exception as e:
        logger.warning(f"Cache GET failed: {e}")
        return None


def set(prefix: str, value, ttl: int = 3600, *key_parts: str):
    """Store value in cache with optional TTL (seconds)."""
    if _redis is None:
        return
    try:
        _redis.setex(_make_key(prefix, *key_parts), ttl, json.dumps(value))
    except Exception as e:
        logger.warning(f"Cache SET failed: {e}")


def get_answer(question: str):
    """Retrieve a cached RAG answer for a query."""
    return get("answer", question)


def set_answer(question: str, answer: str, metadata: dict, ttl: int = 1800):
    """Cache a RAG answer + its metadata."""
    if _redis is None:
        return
    try:
        payload = json.dumps({"answer": answer, "metadata": metadata})
        _redis.setex(_make_key("answer", question), ttl, payload)
    except Exception as e:
        logger.warning(f"Cache SET answer failed: {e}")


def get_cached_answer(question: str):
    """Return (answer, metadata) tuple from cache, or (None, None)."""
    if _redis is None:
        return None, None
    try:
        raw = _redis.get(_make_key("answer", question))
        if raw:
            data = json.loads(raw)
            return data.get("answer"), data.get("metadata", {})
    except Exception as e:
        logger.warning(f"Cache GET answer failed: {e}")
    return None, None


def get_routing(question: str):
    """Return cached routing decision or None."""
    return get("route", question)


def set_routing(question: str, decision: str, ttl: int = 600):
    """Cache routing decision for a question."""
    if _redis is None:
        return
    try:
        _redis.setex(_make_key("route", question), ttl, decision)
    except Exception as e:
        logger.warning(f"Cache SET route failed: {e}")


def is_available() -> bool:
    """Check whether Redis is connected."""
    return _redis is not None
