# randomttstreakkeeper
Random Tiktok streak keeper
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
