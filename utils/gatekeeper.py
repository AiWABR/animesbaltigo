import html
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import REQUIRED_CHANNELS, REQUIRED_CHANNEL_URL

_MEMBERSHIP_CACHE_KEY = "membership_cache"
_ACCESS_NOTICE_TTL = 120
_MEMBERSHIP_CACHE_TTL = 300


def _cache_get(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool | None:
    cache = context.application.bot_data.setdefault(_MEMBERSHIP_CACHE_KEY, {})
    item = cache.get(user_id)
    if not item:
        return None
    allowed, expires_at = item
    if time.time() >= expires_at:
        cache.pop(user_id, None)
        return None
    return allowed


def _cache_set(context: ContextTypes.DEFAULT_TYPE, user_id: int, allowed: bool) -> None:
    cache = context.application.bot_data.setdefault(_MEMBERSHIP_CACHE_KEY, {})
    ttl = _MEMBERSHIP_CACHE_TTL if allowed else 60
    cache[user_id] = (allowed, time.time() + ttl)


def _is_member_allowed(member) -> bool:
    status = str(getattr(member, "status", "") or "").strip().lower()
    if status in {"member", "administrator", "creator"}:
        return True
    return status == "restricted" and bool(getattr(member, "is_member", False))


async def ensure_channel_membership(update, context: ContextTypes.DEFAULT_TYPE):
    if not REQUIRED_CHANNELS:
        return True

    if not update.effective_user or not update.effective_message:
        return False

    user = update.effective_user
    user_id = user.id
    cached = _cache_get(context, user_id)
    if cached is True:
        return True

    allowed = True
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
        except Exception:
            allowed = False
            break
        if not _is_member_allowed(member):
            allowed = False
            break

    _cache_set(context, user_id, allowed)
    if allowed:
        return True

    user_key = f"access_notice:{user_id}"
    now = time.monotonic()
    last_notice = context.user_data.get(user_key, 0.0)
    if now - last_notice < _ACCESS_NOTICE_TTL:
        return False
    context.user_data[user_key] = now

    name = html.escape(user.first_name or "amigo")
    text = (
        f"🛑 <b>Calma aí, {name}</b>\n\n"
        "Para usar este comando, você precisa entrar nos meus canais primeiro.\n\n"
        "Assim você fica por dentro das novidades, avisos e atualizações.\n\n"
        "Clique abaixo, entre nos canais da pasta e volte para tentar novamente."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Entrar nos canais", url=REQUIRED_CHANNEL_URL)]
    ])

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    return False
