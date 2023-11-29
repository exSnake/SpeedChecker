import asyncio
import speedtest
import logging
import logging.handlers
import random
from telegram import Bot
from dotenv import load_dotenv
import os

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Inserisci il tuo token bot di Telegram
TOKEN = os.getenv('TOKEN')

# Inizializza il bot di Telegram
bot = Bot(TOKEN)
PAPERTRAIL_HOST = os.getenv('PAPERTRAIL_HOST')
PAPERTRAIL_PORT = int(os.getenv('PAPERTRAIL_PORT'))

# Configura il logger per inviare i log a Papertrail
logger = logging.getLogger('speedtest')
logger.setLevel(logging.INFO)

# Handler per i livelli di log INFO
handler = logging.handlers.SysLogHandler(address=(PAPERTRAIL_HOST , PAPERTRAIL_PORT))
formatter = logging.Formatter('[\x1b[34m%(levelname)s\x1b[0m] %(message)s')  # Info in blu
handler.setFormatter(formatter)
logger.addHandler(handler)

# Handler per i livelli di log WARN
handler_warn_error = logging.handlers.SysLogHandler(address=(PAPERTRAIL_HOST , PAPERTRAIL_PORT))
formatter_warn_error = logging.Formatter('[\x1b[33m%(levelname)s\x1b[0m] %(message)s')  # Warn in giallo
handler_warn_error.setFormatter(formatter_warn_error)
handler_warn_error.setLevel(logging.WARNING)
logger.addHandler(handler_warn_error)

# Handler per i livelli di log ERROR
handler_error = logging.handlers.SysLogHandler(address=(PAPERTRAIL_HOST , PAPERTRAIL_PORT))
formatter_error = logging.Formatter('[\x1b[31m%(levelname)s\x1b[0m] %(message)s')  # Error in rosso
handler_error.setFormatter(formatter_error)
handler_error.setLevel(logging.ERROR)
logger.addHandler(handler_error)

logger.propagate = False

async def run_speed_test():
    try:
        logger.info("Inizio speed test...")
        st = speedtest.Speedtest(secure=1)
        speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000  # Converti in Mbps
        return download_speed
    except Exception as e:
        logger.error(f"Errore durante lo speed test: {e}")
        return None

async def send_telegram_notification(message):
    try:
        await bot.send_message(chat_id='-848735007', text=message)
    except Exception as e:
        logger.error(f"Errore nell'invio della notifica Telegram: {e}")

async def main():
    retry = 0
    download_speed = await run_speed_test()
    # retry in while loop max 3 times speed test if download speed is None
    while download_speed is None and retry < 3:
        retry += 1
        logger.warning(f"Errore durante lo speed test. Ritento {retry}...")
        await asyncio.sleep(random.randint(65, 125)
        download_speed = await run_speed_test()
    if download_speed is None:
        logger.error("Errore durante lo speed test. Controlla la connessione.")
        await send_telegram_notification("Errore durante lo speed test. Controlla la connessione.")
    elif download_speed <= 100:
        logger.info(f"La velocità di download è inferiore o uguale a 100 Mbps: {download_speed:.2f} Mbps, controllare il cavo di rete sullo switch.")
        await send_telegram_notification(f"La velocità di download è inferiore o uguale a 100 Mbps: {download_speed:.2f} Mbps")
    else:
        logger.info(f"Velocità di download: {download_speed:.2f} Mbps")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
