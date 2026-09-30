"""Состояние бота: кому, когда и что отправляли. Нужен для «очередности» сообщений."""

from __future__ import annotations

import json
import time
from pathlib import Path


class BotState:
    def __init__(self, path: str | Path = "state.json"):
        self.path = Path(path)
        self.data: dict = {"chats": {}, "msg_index": 0, "runs": 0}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        self.data.setdefault("chats", {})
        self.data.setdefault("msg_index", 0)
        self.data.setdefault("runs", 0)

    def save(self) -> None:
        try:
            self.path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass

    # -- счётчик сообщений -------------------------------------------------
    def next_message_index(self, total: int) -> int:
        idx = self.data.get("msg_index", 0) % max(total, 1)
        self.data["msg_index"] = (idx + 1) % max(total, 1)
        return idx

    # -- информация о чатах ------------------------------------------------
    def chat_info(self, name: str) -> dict:
        return self.data["chats"].get(name, {})

    def last_seen(self, name: str) -> float:
        return float(self.chat_info(name).get("last_ts", 0))

    def mark_sent(self, name: str, text: str) -> None:
        chat = self.data["chats"].setdefault(name, {})
        chat["last_ts"] = time.time()
        chat["last_text"] = text
        chat["sent_total"] = int(chat.get("sent_total", 0)) + 1

    def bump_run(self) -> None:
        self.data["runs"] = int(self.data.get("runs", 0)) + 1

    def streak_days(self, name: str) -> int:
        """Грубая прикидка: сколько последних дней подряд в этот чат писали."""
        days = set(self.chat_info(name).get("days", []))
        day = int(time.time() // 86400)
        count = 0
        while day - count in days or (day - count) == day:
            count += 1
        return count

    def mark_day(self, name: str) -> None:
        chat = self.data["chats"].setdefault(name, {})
        days = set(chat.get("days", []))
        days.add(int(time.time() // 86400))
        chat["days"] = sorted(days)[-365:]
