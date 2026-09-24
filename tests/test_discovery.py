import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from agent_kaizen.hermes import discover, discover_profile_homes
from agent_kaizen.search import search_profiles


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


if __name__ == "__main__":
    unittest.main()
