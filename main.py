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
# Definizione di una classe di gestore personalizzato
class ColoredFormatterHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Crea i formatter per i diversi livelli di log
        self.formatter_info = logging.Formatter('[\x1b[34m%(levelname)s\x1b[0m] %(message)s')  # Info in blu
        self.formatter_warn = logging.Formatter('[\x1b[33m%(levelname)s\x1b[0m] %(message)s')  # Warn in giallo
        self.formatter_error = logging.Formatter('[\x1b[31m%(levelname)s\x1b[0m] %(message)s')  # Error in rosso

    def emit(self, record):
        if record.levelno == logging.INFO:
            self.setFormatter(self.formatter_info)
        elif record.levelno == logging.WARNING:
            self.setFormatter(self.formatter_warn)
        elif record.levelno >= logging.ERROR:
            self.setFormatter(self.formatter_error)

        return super().emit(record)

# Configura il logger principale
logger = logging.getLogger('speedtest')
logger.setLevel(logging.INFO)

# Crea un'istanza del gestore personalizzato
handler = ColoredFormatterHandler()

# Aggiungi il gestore al logger principale
logger.addHandler(handler)

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
        await asyncio.sleep(random.randint(125, 300))
        download_speed = await run_speed_test()
    if download_speed is None:
        logger.error("Errore durante lo speed test. Controlla la connessione.")
    elif download_speed <= 100:
        logger.info(f"La velocità di download è inferiore o uguale a 100 Mbps: {download_speed:.2f} Mbps, controllare il cavo di rete sullo switch.")
        await send_telegram_notification(f"La velocità di download è inferiore o uguale a 100 Mbps: {download_speed:.2f} Mbps")
    else:
        logger.info(f"Velocità di download: {download_speed:.2f} Mbps")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
