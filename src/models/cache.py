"""
Disk-backed cache for model responses (SQLite).

Every model call is keyed by a hash of:
  (model_name, messages, temperature, seed, sample_index)

This makes the full inference run resumable and idempotent: re-running
the inference script never re-calls a model for a prompt already cached.
"""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional


DEFAULT_CACHE_PATH = Path("results/inference_cache.sqlite")


def _make_key(
    model_name: str,
    messages: list[dict],
    temperature: float,
    seed: Optional[int],
    sample_index: int,
) -> str:
    """Deterministic hash key for one model call."""
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": round(float(temperature), 4),
        "seed": seed,
        "sample_index": sample_index,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ResponseCache:
    def __init__(self, path: Path = DEFAULT_CACHE_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS responses (
                    key            TEXT PRIMARY KEY,
                    model_name     TEXT NOT NULL,
                    case_id        TEXT,
                    sample_index   INTEGER,
                    temperature    REAL,
                    seed           INTEGER,
                    provider       TEXT,
                    text           TEXT,
                    finish_reason  TEXT,
                    created_at     TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_model ON responses(model_name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_case ON responses(case_id)"
            )

    def get(
        self,
        model_name: str,
        messages: list[dict],
        temperature: float,
        seed: Optional[int],
        sample_index: int,
    ) -> Optional[dict]:
        key = _make_key(model_name, messages, temperature, seed, sample_index)
        with self._conn() as conn:
            row = conn.execute(
                "SELECT text, finish_reason, provider FROM responses "
                "WHERE key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        return {"text": row[0], "finish_reason": row[1], "provider": row[2]}

    def put(
        self,
        model_name: str,
        messages: list[dict],
        temperature: float,
        seed: Optional[int],
        sample_index: int,
        case_id: str,
        text: str,
        finish_reason: Optional[str],
        provider: str,
    ):
        key = _make_key(model_name, messages, temperature, seed, sample_index)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO responses
                (key, model_name, case_id, sample_index, temperature, seed,
                 provider, text, finish_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (key, model_name, case_id, sample_index, temperature, seed,
                 provider, text, finish_reason),
            )

    def count(self, model_name: Optional[str] = None) -> int:
        with self._conn() as conn:
            if model_name:
                row = conn.execute(
                    "SELECT COUNT(*) FROM responses WHERE model_name = ?",
                    (model_name,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) FROM responses"
                ).fetchone()
        return row[0]

    def stats(self) -> dict:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT model_name, COUNT(*) FROM responses "
                "GROUP BY model_name"
            ).fetchall()
        return {model: n for model, n in rows}
