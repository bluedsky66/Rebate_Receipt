import sqlite3
import time
import random
import os
from typing import Literal, Tuple

class RegisterAwareTxnLock:
    def __init__(self, db_path: str = "us_rebate_receipts/jobs/txn_registry.db"):
        self.db_path = db_path
        self.last_timestamps = {}  # store_id_register_id -> last_timestamp_ms
        self._init_db()
        self.verify_integrity()

    def _init_db(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            if self.db_path != ":memory:":
                conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS txn_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_id TEXT,
                    register_id TEXT,
                    txn_seq INTEGER,
                    job_id TEXT,
                    status TEXT,
                    timestamp REAL,
                    total_amount REAL,
                    hex_dump_hash TEXT,
                    UNIQUE(store_id, register_id, txn_seq)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_store_reg_seq ON txn_registry(store_id, register_id, txn_seq)")
            conn.commit()

    def verify_integrity(self):
        """Checks for sequence continuity and any missing/duplicate sequences per register."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT store_id, register_id, MIN(txn_seq), MAX(txn_seq), COUNT(*) FROM txn_registry GROUP BY store_id, register_id")
            for row in cursor.fetchall():
                store_id, register_id, min_seq, max_seq, count = row
                if max_seq - min_seq + 1 != count:
                    raise ValueError(f"Integrity check failed: Discontinuity detected for {store_id} register {register_id}.")

                # Verify exact continuity via querying individual rows
                cursor.execute("SELECT txn_seq FROM txn_registry WHERE store_id=? AND register_id=? ORDER BY txn_seq", (store_id, register_id))
                seqs = [r[0] for r in cursor.fetchall()]
                for i in range(len(seqs) - 1):
                    if seqs[i+1] - seqs[i] != 1:
                        raise ValueError(f"Integrity check failed: Discontinuity detected for {store_id} register {register_id}.")

                # Load the last timestamp to maintain monotonicity
                cursor.execute("SELECT MAX(timestamp) FROM txn_registry WHERE store_id=? AND register_id=?", (store_id, register_id))
                last_ts = cursor.fetchone()[0]
                if last_ts:
                    self.last_timestamps[f"{store_id}_{register_id}"] = last_ts

    def _get_monotonic_timestamp(self, store_id: str, register_id: str, increment_seconds: float = 0.0) -> float:
        key = f"{store_id}_{register_id}"
        current_time = time.time()

        last_ts = self.last_timestamps.get(key, 0)

        # Ensure new timestamp is strictly greater than the last one, plus any specific increment
        new_ts = max(current_time, last_ts + increment_seconds + 0.001)
        self.last_timestamps[key] = new_ts
        return new_ts

    def allocate_abnormal(self, store_id: str, register_id: str, count: int, status: Literal["VOID", "RETURN"], job_id: str = "SYSTEM"):
        """Allocates placeholder sequences for VOIDs and RETURNs"""
        if count <= 0:
            return

        with sqlite3.connect(self.db_path, isolation_level="IMMEDIATE") as conn:
            cursor = conn.cursor()
            for _ in range(count):
                cursor.execute("SELECT IFNULL(MAX(txn_seq), 0) FROM txn_registry WHERE store_id=? AND register_id=?", (store_id, register_id))
                current_max = cursor.fetchone()[0]
                next_seq = current_max + 1

                # Increment timestamp by a few seconds for realistic gap
                ts = self._get_monotonic_timestamp(store_id, register_id, increment_seconds=random.uniform(5.0, 30.0))

                cursor.execute(
                    "INSERT INTO txn_registry (store_id, register_id, txn_seq, job_id, status, timestamp, total_amount, hex_dump_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (store_id, register_id, next_seq, job_id, status, ts, 0.0, None)
                )
            conn.commit()

    def next_seq(self, store_id: str, register_id: str, job_id: str) -> Tuple[int, float]:
        """Atomically gets the next sequence number for a register and records a NORMAL transaction start."""
        with sqlite3.connect(self.db_path, isolation_level="IMMEDIATE") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT IFNULL(MAX(txn_seq), 0) FROM txn_registry WHERE store_id=? AND register_id=?", (store_id, register_id))
            current_max = cursor.fetchone()[0]
            next_seq = current_max + 1

            ts = self._get_monotonic_timestamp(store_id, register_id, increment_seconds=random.uniform(30.0, 120.0))

            cursor.execute(
                "INSERT INTO txn_registry (store_id, register_id, txn_seq, job_id, status, timestamp) VALUES (?, ?, ?, ?, 'NORMAL', ?)",
                (store_id, register_id, next_seq, job_id, ts)
            )
            conn.commit()
            return next_seq, ts

    def update_transaction(self, store_id: str, register_id: str, txn_seq: int, total_amount: float, hex_dump_hash: str):
        """Updates the transaction with total amount and hash after generation."""
        with sqlite3.connect(self.db_path, isolation_level="IMMEDIATE") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE txn_registry SET total_amount=?, hex_dump_hash=? WHERE store_id=? AND register_id=? AND txn_seq=?",
                (total_amount, hex_dump_hash, store_id, register_id, txn_seq)
            )
            conn.commit()
