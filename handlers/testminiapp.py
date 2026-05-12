from urllib.parse import quote_plus

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes

from config import BOT_USERNAME, MINIAPP_SHORT_NAME

MINIAPP_URL = "https://alberta-utah-living-home.trycloudflare.com/miniapp/index.html"


def _miniapp_fullscreen_url(start_param: str = "") -> str:
    username = BOT_USERNAME.lstrip("@")
    app_name = MINIAPP_SHORT_NAME.strip().strip("/")
    if not app_name:
        return ""
    base = f"https://t.me/{username}/{app_name}"
    params = []
    if start_param:
        params.append(f"startapp={quote_plus(start_param)}")
    params.append("mode=fullscreen")
    return f"{base}?{'&'.join(params)}"


async def testminiapp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user

    if message is None:
        return

    first_name = user.first_name if user and user.first_name else "pirata"

    rows = []
    fullscreen_url = _miniapp_fullscreen_url()
    if fullscreen_url:
        rows.append([InlineKeyboardButton(text="📱 Abrir sem barra", url=fullscreen_url)])
    rows.append([
        InlineKeyboardButton(
            text="📱 Abrir Mini App",
            web_app=WebAppInfo(url=MINIAPP_URL),
        )
    ])
    keyboard = InlineKeyboardMarkup(rows)

    text = (
        f"🎌 <b>Baltigo Mini App</b>\n\n"
        f"Fala, {first_name}.\n"
        f"Clica no botão abaixo pra testar o Mini App dentro do Telegram."
    )

    await message.reply_text(
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )
