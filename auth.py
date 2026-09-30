from __future__ import annotations

import os

from playwright.sync_api import Page

from .browser import BrowserManager
from .helpers import dismiss_popups, human_pause, looks_logged_in, type_like_human
from .logger import get_logger

log = get_logger()
