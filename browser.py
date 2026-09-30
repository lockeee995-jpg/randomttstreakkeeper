from __future__ import annotations

import random
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, sync_playwright
_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
window.chrome = window.chrome || { runtime: {} };
Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru', 'en-US', 'en']});
