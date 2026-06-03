import pytest
import sqlite3
import os
from engine.txn_lock import RegisterAwareTxnLock

def test_sequence_monotonic():
    db_path = "test_txn.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    lock = RegisterAwareTxnLock(db_path)

    seq1, ts1 = lock.next_seq("walmart", "01", "job1")
    seq2, ts2 = lock.next_seq("walmart", "01", "job1")

    assert seq1 == 1
    assert seq2 == 2
    assert ts2 > ts1

    os.remove(db_path)

def test_abnormal_allocation():
    db_path = "test_txn_2.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    lock = RegisterAwareTxnLock(db_path)

    lock.allocate_abnormal("target", "02", 2, "VOID", "job1")
    seq, ts = lock.next_seq("target", "02", "job1")

    assert seq == 3 # 1 and 2 were VOID

    os.remove(db_path)

def test_integrity_failure():
    db_path = "test_txn_3.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    lock = RegisterAwareTxnLock(db_path)
    lock.next_seq("cvs", "01", "j1")
    lock.next_seq("cvs", "01", "j1")
    lock.next_seq("cvs", "01", "j1")

    # manually break continuity
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM txn_registry WHERE txn_seq = 2")
        conn.commit()

    with pytest.raises(ValueError, match="Discontinuity detected"):
        lock2 = RegisterAwareTxnLock(db_path)

    os.remove(db_path)
