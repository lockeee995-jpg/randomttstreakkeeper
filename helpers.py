"""Вспомогательные функции: человеческие паузы, «человеческий» ввод текста."""

from __future__ import annotations

import random
import time

from playwright.sync_api import Page, TimeoutError as PWTimeout


def human_pause(min_s: float = 1.0, max_s: float = 3.0) -> None:
    time.sleep(random.uniform(min_s, max_s))


def type_like_human(page: Page, selector: str, text: str,
                    speed_ms: tuple[int, int] = (60, 140)) -> None:
    """Клик + посимвольный ввод с случайными задержками и редкими «задумчивыми» паузами."""
    el = page.locator(selector).first
    el.click()
    human_pause(0.2, 0.6)
    for ch in text:
        el.type(ch, delay=random.randint(*speed_ms))
        if ch in ".,!?":
            human_pause(0.15, 0.5)
        if random.random() < 0.04:
            human_pause(0.4, 1.2)


def safe_first(page: Page, selectors: list[str], timeout: int = 4000):
    """Вернёт Locator первого совпавшего селектора из списка или None."""
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            return loc
        except PWTimeout:
            continue
        except Exception:
            continue
    return None


def click_if_visible(page: Page, selectors: list[str], timeout: int = 2500) -> bool:
    loc = safe_first(page, selectors, timeout=timeout)
    if loc is None:
        return False
    try:
        loc.click()
        human_pause(0.4, 1.0)
        return True
    except Exception:
        return False


def dismiss_popups(page: Page) -> None:
    """Закрываем типовые модалки TikTok («Не сейчас», кукис-бар и т.п.)."""
    for btn in [
        'button:has-text("Не сейчас")',
        'button:has-text("Not now")',
        '[aria-label="Close"]',
        'button:has-text("Отмена")',
        'button:has-text("Cancel")',
        'div[role="dialog"] [aria-label="Close"]',
    ]:
        try:
            loc = page.locator(btn).first
            if loc.is_visible(timeout=700):
                loc.click(timeout=1500)
                human_pause(0.3, 0.8)
        except Exception:
            continue


def looks_logged_in(page: Page) -> bool:
    """Косвенная проверка авторизации: есть ли кнопка «Сообщения»/аватар."""
    try:
        if page.locator('[data-e2e="messages"], a[href*="/messages"]').first.is_visible(timeout=2500):
            return True
    except Exception:
        pass
    try:
        if page.locator('[data-e2e="user-profile-info"], [class*="UserAvatar"]').first.is_visible(timeout=1500):
            return True
    except Exception:
        pass
    return False
