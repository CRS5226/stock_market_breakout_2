# --- services/telegram_alert.py ---
import logging
import os
import asyncio
from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Welcome to the AlgoBot!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Use /start to initiate or just chat with me.")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)


async def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials missing.")
        return
    try:
        from telegram import Bot

        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Telegram error: {e}")


def send_trade_alert(symbol: str, action: str, price: float, date: str):
    message = f"\n*ALERT: {action} Signal*\nSymbol: `{symbol}`\nPrice: `{price}`\nDate: `{date}`"
    asyncio.run(send_telegram_message(message))


def send_pipeline_status(status: str, symbol: str):
    message = f"\n*Pipeline {status}* for `{symbol}`"
    asyncio.run(send_telegram_message(message))


def send_error_alert(error: str):
    message = f"\n*ERROR Occurred:*\n```{error}```"
    asyncio.run(send_telegram_message(message))


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logger.info("Telegram bot polling started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
