"""Отправка сообщений и продление «огонька» (streak).

Как это работает у TikTok: огонёк горит, пока вы переписываетесь с другом.
Значит достаточно раз в сутки отправить/переслать сообщение в каждый чат.
Бот использует только официальный веб-интерфейс tiktok.com/messages —
никаких приватных API, реверс-инжиниринга подписей запросов и обхода капчи.

ВАЖНО: селекторы TikTok меняются со временем. Они собраны в списки
(несколько вариантов) — если сайт обновится, правьте только их.
"""

from __future__ import annotations

import random

from playwright.sync_api import Page

from .browser import BrowserManager
from .config import (
    ACTION_DELAY,
    MAX_REPLIES_PER_CHAT,
    MESSAGES,
    REPLY_MODE,
    TARGETS,
    TIKTOK_INBOX_URL,
    TIKTOK_PROFILE_URL,
    TYPING_SPEED_MS,
)
from .helpers import dismiss_popups, human_pause, type_like_human
from .logger import get_logger
from .state import BotState

log = get_logger()

# --- Селекторы (несколько запасных вариантов на случай редизайна) ----------
SEL_CHAT_LIST = [
    '[data-e2e="im-message-list"] li',
    'div[class*="MessageList"] [class*="itemContainer"]',
    'div[class*="message-list"] [class*="conversation-item"]',
    'ul[class*="ChatList"] li',
]
SEL_CHAT_ITEM_TEXT = "span, div[class*='name'], div[class*='title']"
SEL_SEARCH_BOX = [
    'input[placeholder*="Search" i]',
    'input[data-e2e="im-search"]',
    'input[type="search"]',
]
SEL_COMPOSER = [
    'div[contenteditable="true"][role="textbox"]',
    'textarea[data-e2e="im-input"]',
    'div[data-placeholder*="message" i][contenteditable="true"]',
    'div[class*="InputBox"] [contenteditable="true"]',
]
SEL_SEND_BTN = [
    '[data-e2e="send-button"]',
    'button[aria-label*="Send" i]',
    'div[class*="SendButton"]',
    'button[class*="send"]',
]


def _find_first(page: Page, selectors: list[str], timeout: int = 5000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            return loc
        except Exception:
            continue
    return None


def send_message(page: Page, text: str) -> bool:
    """Вводит текст в поле чата и отправляет (Enter или кнопка Send)."""
    composer = _find_first(page, SEL_COMPOSER)
    if composer is None:
        log.error("Не нашёл поле ввода сообщения — возможно, изменился интерфейс.")
        return False
    try:
        composer.click()
        human_pause(0.3, 0.8)
        # посимвольный ввод через клавиатуру — выглядит естественно
        page.keyboard.type(text, delay=random.randint(*TYPING_SPEED_MS))
        human_pause(0.6, 1.6)
        page.keyboard.press("Enter")
        human_pause(0.5, 1.0)
        # если после Enter текст остался — жмём кнопку отправки
        try:
            if composer.inner_text().strip():
                btn = _find_first(page, SEL_SEND_BTN, timeout=2000)
                if btn is not None:
                    btn.click()
        except Exception:
            pass
        return True
    except Exception as exc:
        log.error(f"Ошибка отправки: {exc}")
        return False


def open_chat_by_username(page: Page, username: str) -> bool:
    """Заходит в переписку с пользователем через его профиль → Message."""
    page.goto(f"{TIKTOK_PROFILE_URL}{username}", wait_until="domcontentloaded")
    human_pause(*ACTION_DELAY)
    dismiss_popups(page)
    msg_btn = _find_first(page, [
        'button:has-text("Message")',
        'button:has-text("Сообщение")',
        '[data-e2e="user-message"]',
        'div[role="button"]:has-text("Message")',
    ], timeout=6000)
    if msg_btn is None:
        log.warning(f"[{username}] не нашёл кнопку Message (нет переписки/подписки?)")
        return False
    try:
        msg_btn.click()
        human_pause(*ACTION_DELAY)
        return True
    except Exception as exc:
        log.error(f"[{username}] клик по Message не сработал: {exc}")
        return False


def open_chat_via_search(page: Page, name: str) -> bool:
    """Ищет чат по имени в мессенджере TikTok."""
    box = _find_first(page, SEL_SEARCH_BOX, timeout=4000)
    if box is None:
        return False
    try:
        box.click()
        human_pause(0.3, 0.7)
        box.fill("")
        page.keyboard.type(name, delay=random.randint(50, 120))
        human_pause(1.2, 2.2)
        item = page.locator(
            f'[class*="result" i]:has-text("{name}"), '
            f'li:has-text("{name}"), [class*="item"]:has-text("{name}")'
        ).first
        item.click(timeout=5000)
        human_pause(*ACTION_DELAY)
        return True
    except Exception:
        return False


def list_inbox_chats(page: Page, limit: int = 20) -> list[tuple[int, str]]:
    """Возвращает [(индекс, имя_чата)] для всех видимых чатов во входящих."""
    chats: list[tuple[int, str]] = []
    items = None
    for sel in SEL_CHAT_LIST:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                items = loc
                break
        except Exception:
            continue
    if items is None:
        return chats
    n = min(items.count(), limit)
    for i in range(n):
        try:
            raw = items.nth(i).inner_text(timeout=2500) or ""
            name = raw.strip().splitlines()[0][:40] if raw.strip() else f"chat#{i}"
            chats.append((i, name))
        except Exception:
            chats.append((i, f"chat#{i}"))
    return chats


def click_chat(page: Page, selector_used: str, index: int) -> bool:
    try:
        page.locator(selector_used).nth(index).click(timeout=5000)
        human_pause(*ACTION_DELAY)
        return True
    except Exception:
        return False


def pick_message(state: BotState) -> str:
    idx = state.next_message_index(len(MESSAGES))
    return MESSAGES[idx]


def keep_streak(mgr: BrowserManager, state: BotState, stop_flag=None) -> dict:
    """Основной проход: заходит в чаты и отправляет по сообщению.

    Возвращает статистику {'sent': N, 'skipped': N, 'failed': N}.
    """
    def stopped():
        return bool(stop_flag and stop_flag())

    page = mgr.page
    assert page is not None
    stats = {"sent": 0, "skipped": 0, "failed": 0}

    page.goto(TIKTOK_INBOX_URL, wait_until="domcontentloaded")
    human_pause(3.0, 5.5)
    dismiss_popups(page)

    # ---- режим 1: конкретные ники из TARGETS ----
    if TARGETS:
        for username in TARGETS:
            if stopped():
                break
            if not open_chat_by_username(page, username):
                if not open_chat_via_search(page, username):
                    stats["failed"] += 1
                    continue
            _send_to_open_chat(page, username, state, stats, stopped)
        state.save()
        return stats

    # ---- режим 2: все чаты во входящих ----
    chats = list_inbox_chats(page)
    if not chats:
        log.warning("Список чатов пуст или не найден. Проверьте вход или "
                    "допишите никнеймы в config.TARGETS.")
        return {"sent": 0, "skipped": 0, "failed": 0}

    log.info(f"Найдено чатов: {len(chats)}")
    # сначала самые давние — они ближе к потере огонька
    chats.sort(key=lambda c: state.last_seen(c[1]))

    sel = None
    for s in SEL_CHAT_LIST:
        try:
            if page.locator(s).count() > 0:
                sel = s
                break
        except Exception:
            continue

    for idx, name in chats:
        if stopped():
            break
        if sel is None or not click_chat(page, sel, idx):
            stats["failed"] += 1
            continue
        _send_to_open_chat(page, name, state, stats, stopped)

    state.bump_run()
    state.save()
    return stats


def _send_to_open_chat(page: Page, name: str, state: BotState,
                       stats: dict, stopped) -> None:
    sent_here = 0
    for _ in range(MAX_REPLIES_PER_CHAT):
        if stopped() or sent_here >= MAX_REPLIES_PER_CHAT:
            break
        text = pick_message(state)
        if send_message(page, text):
            state.mark_sent(name, text)
            state.mark_day(name)
            stats["sent"] += 1
            sent_here += 1
            log.info(f"✉ [{name}] «{text}»")
            human_pause(1.0, 2.5)
        else:
            stats["failed"] += 1
            break
    state.save()
