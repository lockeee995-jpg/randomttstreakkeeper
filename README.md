--- tiktok_streak/README.md (原始)


+++ tiktok_streak/README.md (修改后)
# TikTok Streak Keeper 🔥

Бот, который раз в сутки заходит в ваши переписки TikTok и отправляет
сообщения, чтобы «огонёк» (streak) с друзьями не погас. Работает через
**официальный веб-интерфейс** `tiktok.com/messages` (Playwright + Chromium) —
без реверс-инжиниринга приватных API и без обхода капчи.

> ⚠️ **Дисклеймер.** Автоматизация нарушает [Условия использования TikTok](https://www.tiktok.com/legal/page/ru/terms-of-service),
> и аккаунт могут ограничить или заблокировать. Используйте на свой страх и риск,
> только на своём аккаунте и с большими паузами. Не отправляйте спам незнакомым людям.

## Установка

```bash
pip install -r tiktok_streak/requirements.txt
python -m playwright install chromium
```

## Первый запуск

```bash
# 1. Один раз войти вручную (капча/2FA — вводите сами, профиль сохранится)
python -m tiktok_streak --login

# 2. Настроить tiktok_streak/config.py: TARGETS, MESSAGES, паузы

# 3. Продлить огонёк один раз
python -m tiktok_streak

# или постоянно (интервал случайный, из config.INTERVAL_HOURS)
python -m tiktok_streak --loop

# окно с кнопками «Запустить / Стоп» и живым логом
python -m tiktok_streak --gui

# статистика: кому и когда писали
python -m tiktok_streak --status
```

Удобно ставить на ежедневный расписанием (Windows Планировщик / cron):

```cron
0 12 * * * cd /path/to/project && python -m tiktok_streak >> streak_cron.log 2>&1
```

## Настройка (`config.py`)

| Параметр | Что делает |
|---|---|
| `TARGETS` | Ники друзей без `@`. Пусто = пройтись по всем чатам во «Входящих» |
| `MESSAGES` | Список фраз — бот чередует их по кругу |
| `MIN/MAX_DELAY_BETWEEN_MESSAGES` | Пауза между сообщениями (сек). Меньше 30 не ставьте |
| `HEADLESS` | `True` — без окна браузера (с окном надёжнее для детекта) |
| `RUN_LOOP`, `INTERVAL_HOURS` | Постоянный режим со случайным интервалом |

## Как устроено

```
tiktok_streak/
├── config.py      # все настройки
├── browser.py     # Chromium с персистентным профилем (логин 1 раз)
├── auth.py        # проверка сессии, ручной и авто-вход
├── messenger.py   # заход в чаты + отправка сообщений (селекторы тут)
├── state.py       # state.json: кому/когда писали, очередь фраз
├── gui.py         # tkinter-окно (по желанию)
└── __main__.py    # CLI: --login / --loop / --gui / --status
```

Если TikTok изменит вёрстку — обновите списки селекторов в начале
`messenger.py` (`SEL_CHAT_LIST`, `SEL_COMPOSER`, `SEL_SEND_BTN`).

## Частые проблемы

- **«Не нашёл поле ввода»** → вы не залогинены или редизайн: `--login`, затем правьте селекторы.
- **Капча при входе** → это нормально и правильно: решите её руками один раз,
  дальше профиль сохранён в папке `browser_profile/`.
- **Нужны ли ответы собеседника?** Для огонька достаточно вашего сообщения раз в сутки;
  бот пишет по одному сообщению в каждый чат за проход (`MAX_REPLIES_PER_CHAT`).
