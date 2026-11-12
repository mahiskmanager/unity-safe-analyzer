import sqlite3
import json
import csv
import io
import threading
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo
from . import config

_lock = threading.RLock()

@contextmanager
def _connect():
    config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(config.DATABASE_PATH, timeout=20)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def init_db():
    with _lock, _connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            asset TEXT NOT NULL,
            ticker TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            direction TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            entry REAL,
            stop REAL,
            target REAL,
            risk TEXT,
            result TEXT NOT NULL DEFAULT 'PENDING',
            result_at TEXT,
            snapshot_json TEXT NOT NULL,
            analysis_json TEXT NOT NULL
        )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_signals_asset ON signals(asset)")

def add_signal(asset, ticker, timeframe, snapshot, analysis):
    sid = __import__("uuid").uuid4().hex[:12]
    now = datetime.now(ZoneInfo(config.TIMEZONE)).isoformat()
    with _lock, _connect() as con:
        con.execute("""
        INSERT INTO signals
        (id,created_at,asset,ticker,timeframe,direction,confidence,entry,stop,target,risk,
         snapshot_json,analysis_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            sid, now, asset, ticker, timeframe, analysis["direction"],
            analysis["confidence"], analysis.get("entry"), analysis.get("stop"),
            analysis.get("target"), analysis.get("risk"),
            json.dumps(snapshot), json.dumps(analysis)
        ))
    return sid

def set_result(signal_id, result):
    if result not in {"WIN", "LOSS", "VOID"}:
        raise ValueError("Resultado inválido")
    now = datetime.now(ZoneInfo(config.TIMEZONE)).isoformat()
    with _lock, _connect() as con:
        cur = con.execute("""
        UPDATE signals SET result=?, result_at=?
        WHERE id=? AND result='PENDING'
        """, (result, now, signal_id))
        return cur.rowcount == 1

def recent_signals(limit=10, today=False):
    query = "SELECT * FROM signals"
    params = []
    if today:
        local_date = datetime.now(ZoneInfo(config.TIMEZONE)).date().isoformat()
        query += " WHERE created_at LIKE ?"
        params.append(local_date + "%")
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(max(1, min(int(limit), 100)))
    with _lock, _connect() as con:
        return [dict(row) for row in con.execute(query, params).fetchall()]

def statistics(today=False):
    query = "SELECT result, COUNT(*) AS n FROM signals"
    params = []
    if today:
        local_date = datetime.now(ZoneInfo(config.TIMEZONE)).date().isoformat()
        query += " WHERE created_at LIKE ?"
        params.append(local_date + "%")
    query += " GROUP BY result"
    with _lock, _connect() as con:
        rows = con.execute(query, params).fetchall()
    counts = {r["result"]: r["n"] for r in rows}
    wins, losses = counts.get("WIN", 0), counts.get("LOSS", 0)
    closed = wins + losses
    return {
        "total": sum(counts.values()), "wins": wins, "losses": losses,
        "pending": counts.get("PENDING", 0), "void": counts.get("VOID", 0),
        "closed": closed, "accuracy": (wins / closed * 100) if closed else 0.0
    }

def export_csv() -> str:
    with _lock, _connect() as con:
        rows = con.execute("SELECT * FROM signals ORDER BY created_at DESC").fetchall()
    output = io.StringIO()
    if rows:
        writer = csv.writer(output)
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow([row[k] for k in row.keys()])
    return output.getvalue()
