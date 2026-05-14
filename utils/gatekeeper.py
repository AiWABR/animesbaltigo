import html
import re
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import REQUIRED_CHANNELS

_MEMBERSHIP_CACHE_KEY = "membership_cache"
_MEMBERSHIP_CACHE_TTL = 300

_CHANNEL_LABELS = {
    "@AtualizacoesOn": "📢 Atualizações",
    "@Centraldeanimes_Baltigo": "🍥 Anime Baltigo",
    "@QG_BALTIGO": "🏠 QG Baltigo",
}


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
    ttl = _MEMBERSHIP_CACHE_TTL if allowed else 60
    cache = context.application.bot_data.setdefault(_MEMBERSHIP_CACHE_KEY, {})
    cache[user_id] = (allowed, time.time() + ttl)


def _is_member_allowed(member) -> bool:
    status = str(getattr(member, "status", "") or "").strip().lower()
    if status in {"member", "administrator", "creator"}:
        return True
    return status == "restricted" and bool(getattr(member, "is_member", False))


def _channel_url(channel: str) -> str:
    channel = str(channel or "").strip()
    if channel.startswith("@"):
        return f"https://t.me/{channel[1:]}"
    if channel.startswith("http://") or channel.startswith("https://"):
        return channel
    return f"https://t.me/{channel.lstrip('@')}"


def _channel_label(channel: str) -> str:
    channel = str(channel or "").strip()
    if channel in _CHANNEL_LABELS:
        return _CHANNEL_LABELS[channel]
    clean = re.sub(r"[_-]+", " ", channel.lstrip("@")).strip().title()
    return f"📢 {clean or 'Canal'}"


def _channel_keyboard(channels: list[str]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(_channel_label(channel), url=_channel_url(channel))
        for channel in channels
    ]
    rows = [buttons[index : index + 2] for index in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


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

    missing_channels: list[str] = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
        except Exception:
            missing_channels.append(channel)
            continue
        if not _is_member_allowed(member):
            missing_channels.append(channel)

    allowed = not missing_channels
    _cache_set(context, user_id, allowed)
    if allowed:
        return True

    name = html.escape(user.first_name or "amigo")
    text = (
        f"🛑 <b>Calma aí, {name}</b>\n\n"
        "Para usar este comando, você precisa entrar nos canais oficiais primeiro.\n\n"
        "É por lá que eu aviso novidades, lançamentos e atualizações importantes.\n\n"
        "Entre nos canais abaixo e envie o comando novamente."
    )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=_channel_keyboard(missing_channels),
    )
    return False
