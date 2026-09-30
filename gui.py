"""Окно с логами и кнопками (Tkinter). Работает в отдельном потоке, Playwright — в своём."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime


class AppWindow:
    """GUI-обёртка. Методы log()/set_status() потокобезопасны."""

    def __init__(self, on_run, on_stop, is_running_fn):
        self._q: "queue.Queue[tuple]" = queue.Queue()
        self._on_run = on_run
        self._on_stop = on_stop
        self._is_running = is_running_fn
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._build, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=10)

    # ---------- внешний API ----------
    def log(self, text: str) -> None:
        self._q.put(("log", text))

    def set_status(self, text: str, color: str = "gray") -> None:
        self._q.put(("status", (text, color)))

    # ---------- внутреннее ----------
    def _build(self) -> None:
        self.root = tk.Tk()
        self.root.title("TikTok Streak Keeper")
        self.root.geometry("640x480")
        self.root.minsize(420, 300)

        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        self.btn_run = ttk.Button(top, text="▶ Запустить", command=self._run)
        self.btn_run.pack(side="left", padx=(0, 6))
        self.btn_stop = ttk.Button(top, text="⏹ Стоп", command=self._stop, state="disabled")
        self.btn_stop.pack(side="left", padx=(0, 6))
        ttk.Button(top, text="Очистить", command=self._clear).pack(side="right")

        self.status_var = tk.StringVar(value="Готов")
        self.status_lbl = ttk.Label(top, textvariable=self.status_var, foreground="gray")
        self.status_lbl.pack(side="right", padx=8)

        self.txt = scrolledtext.ScrolledText(
            self.root, wrap="word", bg="#1e1e1e", fg="#d4d4d4",
            font=("Consolas", 9), state="disabled",
        )
        self.txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self._ready.set()
        self.root.after(100, self._pump)
        self.root.mainloop()

    def _pump(self) -> None:
        try:
            while True:
                kind, payload = self._q.get_nowait()
                if kind == "log":
                    self._append(payload)
                elif kind == "status":
                    text, color = payload
                    self.status_var.set(text)
                    try:
                        self.status_lbl.configure(foreground=color)
                    except tk.TclError:
                        pass
                    running = self._is_running()
                    self.btn_run.configure(state="disabled" if running else "normal")
                    self.btn_stop.configure(state="normal" if running else "disabled")
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.root.after(100, self._pump)

    def _append(self, line: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.txt.configure(state="normal")
        self.txt.insert("end", f"[{stamp}] {line}\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def _clear(self) -> None:
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.configure(state="disabled")

    def _run(self) -> None:
        threading.Thread(target=self._on_run, daemon=True).start()

    def _stop(self) -> None:
        self._on_stop()

    def _close(self) -> None:
        self._on_stop()
        self.root.destroy()


class LogToQueue:
    """Перенаправляет записи logging в callback окна."""

    def __init__(self, callback):
        self.callback = callback

    def write(self, message: str) -> int:
        message = message.rstrip()
        if message:
            self.callback(message)
        return len(message)

    def flush(self) -> None:
        pass
