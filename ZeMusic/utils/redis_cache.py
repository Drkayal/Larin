import os
import json
import hashlib
from typing import Optional, Dict, Any

try:
	import redis  # type: ignore
except Exception:
	redis = None  # Redis client may be unavailable at runtime

import config

_redis_client: Optional["redis.Redis"] = None


def _build_redis() -> Optional["redis.Redis"]:
	if redis is None:
		return None
	url = os.getenv("REDIS_URL", "").strip()
	try:
		if url:
			return redis.from_url(url, decode_responses=True)
		# Fallback to host/port/db
		host = os.getenv("REDIS_HOST", "localhost")
		port = int(os.getenv("REDIS_PORT", "6379"))
		db = int(os.getenv("REDIS_DB", "0"))
		password = os.getenv("REDIS_PASSWORD")
		return redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
	except Exception:
		return None


def get_client() -> Optional["redis.Redis"]:
	global _redis_client
	if _redis_client is None:
		_redis_client = _build_redis()
	return _redis_client


def normalize_query(query: str) -> str:
	return " ".join((query or "").strip().lower().split())


def _qkey(query: str) -> str:
	q = normalize_query(query)
	h = hashlib.sha256(q.encode()).hexdigest()[:24]
	return f"yt:search:{h}"


def _afile_key(video_id: str) -> str:
	return f"yt:audio:{(video_id or '').strip()}"


def _flag_key() -> str:
	return "bot:music_replies_enabled"


def is_music_replies_enabled() -> bool:
	client = get_client()
	if not client:
		return True
	try:
		val = client.get(_flag_key())
		if val is None:
			return True
		return val == "1"
	except Exception:
		return True


def set_music_replies_enabled(enabled: bool) -> bool:
	client = get_client()
	if not client:
		return False
	try:
		client.set(_flag_key(), "1" if enabled else "0")
		return True
	except Exception:
		return False


def get_cached_search(query: str) -> Optional[Dict[str, Any]]:
	client = get_client()
	if not client:
		return None
	try:
		val = client.get(_qkey(query))
		return json.loads(val) if val else None
	except Exception:
		return None


def set_cached_search(query: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
	client = get_client()
	if not client:
		return False
	try:
		j = json.dumps(data, ensure_ascii=False)
		key = _qkey(query)
		ttl = ttl_seconds or int(getattr(config, "CACHE_EXPIRATION_HOURS", 168)) * 3600
		client.setex(key, ttl, j)
		return True
	except Exception:
		return False


def get_cached_audio(video_id: str) -> Optional[Dict[str, Any]]:
	client = get_client()
	if not client:
		return None
	try:
		val = client.get(_afile_key(video_id))
		if not val:
			return None
		data = json.loads(val)
		path = data.get("path")
		if path and os.path.exists(path):
			return data
		# إن كان المسار غير موجود، احذف الإدخال
		client.delete(_afile_key(video_id))
		return None
	except Exception:
		return None


def set_cached_audio(video_id: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
	client = get_client()
	if not client:
		return False
	try:
		j = json.dumps(data, ensure_ascii=False)
		key = _afile_key(video_id)
		ttl = ttl_seconds or int(getattr(config, "CACHE_EXPIRATION_HOURS", 168)) * 3600
		client.setex(key, ttl, j)
		return True
	except Exception:
		return False


def ban_audio(video_id: str) -> None:
	client = get_client()
	if not client:
		return
	try:
		client.delete(_afile_key(video_id))
	except Exception:
		pass