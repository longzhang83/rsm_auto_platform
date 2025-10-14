from __future__ import annotations

import csv
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

try:
	from tqdm import tqdm
except ImportError:  # pragma: no cover
	tqdm = None

from zhipuai import ZhipuAI

DEFAULT_MODEL = "glm-4.5-flash"
SYSTEM_PROMPT = "你是一名专业的双语助理，请提供准确、简洁的翻译结果。"
API_KEY_ENV_VAR = "ZHIPUAI_API_KEY"
FALLBACK_API_KEY = "504d905384914caeac887f1c91ebf671.UtAzmxrLaLqIi3gN"
REQUESTS_PER_SECOND_ENV = "ZHIPUAI_RPS"
DEFAULT_REQUESTS_PER_SECOND = 0.6
TRANSLATION_MAP_ENV = "TRANSLATION_MAP_PATH"
DEFAULT_TRANSLATION_MAP = Path("data") / "translation_mapping.csv"


class _RateLimiter:
	def __init__(self, requests_per_second: float) -> None:
		self._lock = threading.Lock()
		self._interval = self._normalize_interval(requests_per_second)
		self._next_time = 0.0

	def _normalize_interval(self, requests_per_second: float) -> float:
		rps = max(requests_per_second, 0.05)
		return 1.0 / rps

	def set_rate(self, requests_per_second: float) -> None:
		with self._lock:
			self._interval = self._normalize_interval(requests_per_second)
			self._next_time = 0.0

	def acquire(self) -> None:
		while True:
			with self._lock:
				now = time.perf_counter()
				wait = self._next_time - now
				if wait <= 0:
					self._next_time = max(self._next_time, now) + self._interval
					return
			time.sleep(wait)


def _resolve_api_key() -> str:
	return os.getenv(API_KEY_ENV_VAR, FALLBACK_API_KEY)


def _normalise_content(content: Any) -> str:
	if isinstance(content, str):
		return content.strip()
	if isinstance(content, Sequence):
		parts = []
		for item in content:
			if isinstance(item, dict) and "text" in item:
				parts.append(str(item["text"]))
			else:
				parts.append(str(item))
		return "".join(parts).strip()
	return str(content).strip()


def chat_glm(prompt: str, model: str = DEFAULT_MODEL) -> tuple[Optional[str], Optional[str]]:
	try:
		if not prompt or not prompt.strip():
			return "Empty input", None

		client = ZhipuAI(api_key=_resolve_api_key())

		messages = [
			{"role": "system", "content": SYSTEM_PROMPT},
			{"role": "user", "content": prompt},
		]

		response = client.chat.completions.create(
			model=model,
			messages=messages,
			max_tokens=2048,
		)

		if not response or not response.choices:
			return "No response from API", None

		content = response.choices[0].message.content
		return None, _normalise_content(content)

	except Exception as exc:
		error_msg = str(exc)
		if "timeout" in error_msg.lower():
			return "Request timed out", None
		if "rate limit" in error_msg.lower():
			return "Rate limit exceeded", None
		if "api key" in error_msg.lower():
			return "Invalid API key", None
		return f"Error: {error_msg}", None


_RATE_LIMITER = _RateLimiter(float(os.getenv(REQUESTS_PER_SECOND_ENV, DEFAULT_REQUESTS_PER_SECOND)))
_MAPPING_CACHE: Dict[Path, Dict[str, str]] = {}
_MAPPING_LOCK = threading.RLock()


def configure_rate_limit(requests_per_second: float) -> None:
	if requests_per_second <= 0:
		return
	_RATE_LIMITER.set_rate(requests_per_second)


def _resolve_mapping_path(path: Optional[Union[str, Path]]) -> Path:
	if path is None:
		env_path = os.getenv(TRANSLATION_MAP_ENV)
		if env_path:
			return Path(env_path)
		return DEFAULT_TRANSLATION_MAP
	return Path(path)


def _ensure_mapping_loaded(path: Path) -> Dict[str, str]:
	with _MAPPING_LOCK:
		if path in _MAPPING_CACHE:
			return _MAPPING_CACHE[path]

		mapping: Dict[str, str] = {}
		if path.exists():
			with path.open("r", newline="", encoding="utf-8-sig") as handle:
				reader = csv.reader(handle)
				for row in reader:
					if not row:
						continue
					if row[0] == "source" and len(row) > 1 and row[1] == "target":
						continue
					source = row[0].strip()
					target = row[1].strip() if len(row) > 1 else ""
					if source:
						mapping[source] = target
		_MAPPING_CACHE[path] = mapping
		return mapping


def _lookup_mapping(path: Path, source: str) -> Optional[str]:
	with _MAPPING_LOCK:
		mapping = _ensure_mapping_loaded(path)
		return mapping.get(source)


def _write_mapping(path: Path, mapping: Dict[str, str]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", newline="", encoding="utf-8-sig") as handle:
		writer = csv.writer(handle)
		writer.writerow(["source", "target"])
		for source, target in mapping.items():
			writer.writerow([source, target])


def _store_mapping(path: Path, source: str, target: str) -> None:
	if not source or not target:
		return
	with _MAPPING_LOCK:
		mapping = _ensure_mapping_loaded(path)
		existing = mapping.get(source)
		if existing == target:
			return
		mapping[source] = target
		_write_mapping(path, mapping)


@lru_cache(maxsize=512)
def _translate_cached(text: str) -> str:
	_RATE_LIMITER.acquire()
	prompt = (
		"请将以下中文词语或短语翻译成自然、简洁的英文。"
		"只输出英文译文，不要添加说明或引号。\n"
		f"中文：{text}\n英文："
	)
	err, result = chat_glm(prompt)
	if err or not result:
		raise RuntimeError(err or "empty response")
	translated = result.strip()
	if not translated or translated == text:
		raise RuntimeError("translation identical to source")
	return translated


def translate_text(text: str, *, mapping_path: Optional[Union[str, Path]] = None) -> str:
	clean_text = (text or "").strip()
	if not clean_text:
		return ""

	path = _resolve_mapping_path(mapping_path)
	existing = _lookup_mapping(path, clean_text)
	if existing:
		return existing

	for attempt in range(3):
		try:
			translated = _translate_cached(clean_text)
			_store_mapping(path, clean_text, translated)
			return translated
		except Exception:  # pragma: no cover - depends on external API
			_translate_cached.cache_clear()
			time.sleep(min(0.5 * (attempt + 1), 2.0))

	return clean_text


def clear_translation_cache(*, drop_mapping_cache: bool = False) -> None:
	_translate_cached.cache_clear()
	if drop_mapping_cache:
		with _MAPPING_LOCK:
			_MAPPING_CACHE.clear()


def batch_translate_texts(
	texts: Iterable[str],
	*,
	max_workers: int = 3,
	requests_per_second: Optional[float] = None,
	progress_description: str = "翻译摘要",
	mapping_path: Optional[Union[str, Path]] = None,
) -> Dict[str, str]:
	cleaned: List[str] = []
	seen: set[str] = set()
	for text in texts:
		candidate = (text or "").strip()
		if not candidate or candidate in seen:
			continue
		seen.add(candidate)
		cleaned.append(candidate)

	if not cleaned:
		return {}

	if requests_per_second:
		configure_rate_limit(requests_per_second)

	results: Dict[str, str] = {}

	def _worker(value: str) -> Tuple[str, str]:
		return value, translate_text(value, mapping_path=mapping_path)

	progress_bar = None
	if tqdm and cleaned:
		progress_bar = tqdm(total=len(cleaned), desc=progress_description, unit="项", leave=False)

	with ThreadPoolExecutor(max_workers=max_workers or 1) as executor:
		future_to_text = {executor.submit(_worker, value): value for value in cleaned}
		for future in as_completed(future_to_text):
			try:
				original, translated = future.result()
			except Exception:
				original, translated = future_to_text[future], future_to_text[future]
			results[original] = translated or original
			if progress_bar:
				progress_bar.update(1)

	if progress_bar:
		progress_bar.close()

	return results


if __name__ == "__main__":
	error, reply = chat_glm("你好，请简单自我介绍。")
	print(error or reply)
