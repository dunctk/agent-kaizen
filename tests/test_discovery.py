import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from agent_kaizen.hermes import discover, discover_profile_homes
from agent_kaizen.search import search_profiles
from agent_kaizen.inspect import inspect_profiles


def make_state(path: Path):
    conn = sqlite3.connect(path)
    conn.executescript("""
    CREATE TABLE sessions(id TEXT PRIMARY KEY, source TEXT, title TEXT);
    CREATE TABLE messages(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT, tool_name TEXT, tool_calls TEXT, timestamp REAL);
    CREATE VIRTUAL TABLE messages_fts USING fts5(content, tool_name, tool_calls, content='messages', content_rowid='id');
    CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
      INSERT INTO messages_fts(rowid, content, tool_name, tool_calls) VALUES(new.id, new.content, new.tool_name, new.tool_calls);
    END;
    """)
    conn.execute("INSERT INTO sessions VALUES (?, ?, ?)", ("s1", "cron", "Daily researcher"))
    conn.execute(
        "INSERT INTO messages(session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        ("s1", "assistant", "Recovered from an API timeout manually", 100.0),
    )
    conn.commit()
    conn.close()


def make_inspection_state(path: Path, now: float):
    conn = sqlite3.connect(path)
    conn.executescript("""
    CREATE TABLE sessions(
      id TEXT PRIMARY KEY,
      source TEXT,
      title TEXT,
      started_at REAL,
      last_activity_at REAL,
      message_count INTEGER,
      tool_call_count INTEGER,
      api_call_count INTEGER,
      estimated_cost_usd REAL,
      actual_cost_usd REAL,
      model TEXT
    );
    CREATE TABLE messages(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT,
      role TEXT,
      content TEXT,
      tool_name TEXT,
      tool_calls TEXT,
      timestamp REAL
    );
    CREATE VIRTUAL TABLE messages_fts USING fts5(
      content, tool_name, tool_calls, content='messages', content_rowid='id'
    );
    CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
      INSERT INTO messages_fts(rowid, content, tool_name, tool_calls)
      VALUES(new.id, new.content, new.tool_name, new.tool_calls);
    END;
    """)
    conn.execute(
        "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("cron-1", "cron", "Daily researcher", now - 120, now - 30, 2, 1, 1, 0.05, None, "test-model"),
    )
    conn.execute(
        "INSERT INTO messages(session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        ("cron-1", "assistant", "API timeout; had to retry manually after failure", now - 60),
    )
    conn.commit()
    conn.close()


class DiscoveryTests(unittest.TestCase):
    def test_discover_profiles_cron_and_search(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / ".hermes"
            root.mkdir()
            (root / "config.yaml").write_text("model: test\n")
            (root / "logs").mkdir()
            (root / "logs" / "agent.log").write_text("INFO started\nWARNING API timeout\n")
            (root / "cron" / "output" / "job1").mkdir(parents=True)
            (root / "cron" / "jobs.json").write_text(json.dumps({"jobs": [{
                "id": "job1",
                "name": "Daily researcher",
                "schedule_display": "every 1d",
                "enabled": True,
                "next_run_at": "2026-09-25T08:00:00+00:00",
            }]}))
            (root / "cron" / "output" / "job1" / "run.md").write_text(
                "Investigated API timeout and retried.\n"
            )
            make_state(root / "state.db")

            pdir = root / "profiles" / "coder"
            pdir.mkdir(parents=True)
            (pdir / "config.yaml").write_text("model: coder\n")

            profiles = discover(root)
            self.assertEqual([p.name for p in profiles], ["default", "coder"])
            self.assertEqual(profiles[0].cron_jobs[0].name, "Daily researcher")
            self.assertEqual(discover_profile_homes(pdir), [("coder", pdir.resolve())])

            hits = search_profiles(profiles, "API timeout", {"sessions", "logs", "cron"}, 20)
            sources = {h.source for h in hits}
            self.assertTrue({"sessions", "logs", "cron-output"}.issubset(sources))


    def test_inspect_summarizes_recent_hermes_activity(self):
        with tempfile.TemporaryDirectory() as td:
            now = time.time()
            root = Path(td) / ".hermes"
            root.mkdir()
            (root / "config.yaml").write_text("model: test\n")
            (root / "logs").mkdir()
            (root / "logs" / "agent.log").write_text("WARNING rate limit retrying\n")
            (root / "cron" / "output" / "job1").mkdir(parents=True)
            (root / "cron" / "jobs.json").write_text(json.dumps({"jobs": [{
                "id": "job1",
                "name": "Daily researcher",
                "schedule_display": "every 1h",
                "enabled": True,
            }]}))
            (root / "cron" / "output" / "job1" / "20260924_080000.md").write_text(
                "ERROR timeout\nmanual intervention used workaround\n"
            )
            make_inspection_state(root / "state.db", now)

            report = inspect_profiles(discover(root), days=7, evidence_limit=10, now=now)
            profile = report.profiles[0]

            self.assertEqual(profile.sessions.sessions, 1)
            self.assertEqual(profile.sessions.cron_sessions, 1)
            self.assertEqual(profile.sessions.api_calls, 1)
            self.assertAlmostEqual(profile.sessions.estimated_cost_usd, 0.05)
            self.assertGreaterEqual(profile.sessions.failure_signals, 1)
            self.assertGreaterEqual(profile.sessions.intervention_signals, 1)
            self.assertEqual(profile.log_failure_signals, 1)
            self.assertEqual(profile.cron[0].output_artifacts, 1)
            self.assertEqual(profile.cron[0].failure_signals, 1)
            self.assertEqual(profile.cron[0].intervention_signals, 1)
            self.assertTrue(profile.attention)


if __name__ == "__main__":
    unittest.main()
