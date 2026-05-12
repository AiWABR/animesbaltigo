from urllib.parse import quote_plus

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes

from config import BOT_USERNAME, MINIAPP_SHORT_NAME

MINIAPP_URL = "https://alberta-utah-living-home.trycloudflare.com/miniapp/index.html"


def _miniapp_fullscreen_url(start_param: str = "") -> str:
    username = BOT_USERNAME.lstrip("@")
    app_name = MINIAPP_SHORT_NAME.strip().strip("/")
    base = f"https://t.me/{username}/{app_name}" if app_name else f"https://t.me/{username}"
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

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="📱 Abrir sem barra",
                    url=_miniapp_fullscreen_url(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Abrir compatível",
                    web_app=WebAppInfo(url=MINIAPP_URL),
                )
            ]
        ]
    )

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
