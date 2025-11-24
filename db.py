# db.py
import sqlite3
from pathlib import Path
import hashlib
from typing import List, Tuple, Optional

DATA_DIR = "./data"
DB_PATH = "./data/pkm.sqlite3"


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                created TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS note_tags (
                note_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY(note_id, tag_id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                remind_at TEXT,
                mail_sent INTEGER DEFAULT 0
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )

        self.conn.commit()

    def execute(self, sql: str, params: Tuple = ()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def get_password(self):
        row = self.execute("SELECT value FROM app_settings "
                           "WHERE key='password'").fetchone()
        return row[0] if row else None

    def set_password(self, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        self.execute("INSERT OR REPLACE INTO app_settings(key, value) "
                     "VALUES('password', ?)",
                     (hashed,))

    def verify(self, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        row = self.execute("SELECT value FROM app_settings "
                           "WHERE key='password'").fetchone()
        return bool(row and row[0] == hashed)

    def add_tag(self, name):
        name = name.strip()
        if not name:
            raise ValueError("Tag name is empty")
        try:
            cur = self.execute("INSERT INTO tags(name) "
                               "VALUES(?)",
                               (name,))
            return cur.lastrowid
        except sqlite3.IntegrityError:
            cur = self.execute("SELECT id FROM tags "
                               "WHERE name = ?",
                               (name,))
            row = cur.fetchone()
            return row[0]

    def set_tags(self, note_id: int, tags):
        self.execute("DELETE FROM note_tags "
                     "WHERE note_id = ?",
                     (note_id,))
        for tag in tags:
            tag = tag.strip()
            if not tag:
                continue
            tag_id = self.add_tag(tag)
            self.execute("INSERT OR IGNORE INTO note_tags(note_id, tag_id) "
                         "VALUES(?, ?)",
                         (note_id, tag_id))

    def get_tags(self, note_id: int) -> List[str]:
        cur = self.execute(
            "SELECT t.name FROM tags t "
            "JOIN note_tags nt ON t.id=nt.tag_id "
            "WHERE nt.note_id = ?",
            (note_id,)
        )
        return [r[0] for r in cur.fetchall()]

    def add_rem(self, note_id: int, remind_at: str) -> int:
        cur = self.execute("INSERT INTO reminders(note_id, remind_at, mail_sent) "
                           "VALUES(?, ?, 0)",
                           (note_id, remind_at))
        return cur.lastrowid

    def get_rem(self, note_id: int) -> List[Tuple[int, str, int]]:
        cur = self.execute("SELECT id, remind_at, mail_sent FROM reminders "
                           "WHERE note_id = ? "
                           "ORDER BY remind_at ASC", (note_id,))
        return cur.fetchall()

    def del_rem(self, reminder_id: int) -> None:
        self.execute("DELETE FROM reminders "
                     "WHERE id = ?",
                     (reminder_id,))

    def get_rems(self, current_datetime: str) -> List[Tuple[int, int, str, str]]:
        cur = self.execute(
            "SELECT r.id, r.note_id, r.remind_at, n.title FROM reminders r "
            "JOIN notes n ON n.id = r.note_id "
            "WHERE r.remind_at <= ? AND r.mail_sent = 0",
            (current_datetime,)
        )
        return cur.fetchall()

    def mark_rem(self, reminder_id: int) -> None:
        self.execute("UPDATE reminders SET mail_sent = 1 "
                     "WHERE id = ?",
                     (reminder_id,))

    def get_note(self, note_id: int):
        return self.execute("SELECT id, title, content, created FROM notes "
                            "WHERE id = ?",
                            (note_id,)).fetchone()

    def close(self):
        self.conn.close()
