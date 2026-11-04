import time
import logging
import colorama
from colorama import Fore, Style
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import lxml
except ModuleNotFoundError:
    pass

import Utils.cardinal_tools
import Utils.config_loader as cfg_loader
from first_setup import first_setup
from Utils.logger import configure_logging
from studio import Cardinal
import Utils.exceptions as excs
from locales.localizer import Localizer

# FunPay Studio (FPS) Logo & Metadata
VERSION = "1.0.0"

logo = f"""{Fore.CYAN}{Style.BRIGHT}
  ______            _____             _____ _             _ _       
 |  ____|          |  __ \\           / ____| |           | (_)      
 | |__ _   _ _ __  | |__) |_ _ _   _| (___ | |_ _   _  __| |_  ___  
 |  __| | | | '_ \\ |  ___/ _` | | | |\\___ \\| __| | | |/ _` | |/ _ \\ 
 | |  | |_| | | | || |  | (_| | |_| |____) | |_| |_| | (_| | | (_) |
 |_|   \\__,_|_| |_||_|   \\__,_|\\__, |_____/ \\__|\\__,_|\\__,_|_|\\___/ 
                                __/ |                               
                               |___/                                
{Style.RESET_ALL}"""

Utils.cardinal_tools.set_console_title(f"FunPay Studio v{VERSION}")

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(__file__))

folders = ["configs", "logs", "storage", "storage/cache", "storage/plugins", "storage/products", "plugins", "core"]
for i in folders:
    if not os.path.exists(i):
        os.makedirs(i)

files = ["configs/auto_delivery.cfg", "configs/auto_response.cfg"]
for i in files:
    if not os.path.exists(i):
        with open(i, "w", encoding="utf-8") as f:
            pass

colorama.init()
configure_logging()
logging.raiseExceptions = False
logger = logging.getLogger("main")
logger.debug("------------------------------------------------------------------")

print(f"{logo}")
print(f"{Fore.GREEN}{Style.BRIGHT}  [*] FunPay Studio v{VERSION} — Официальная экосистема для продавцов{Style.RESET_ALL}\n")
print(f"{Fore.YELLOW}{Style.BRIGHT}  * Создатель ядра:      {Fore.WHITE}yuepi-FPS")
print(f"{Fore.YELLOW}{Style.BRIGHT}  * Официальный канал:  {Fore.WHITE}https://t.me/funpaystudio")
print(f"{Fore.YELLOW}{Style.BRIGHT}  * Каталог плагинов:    {Fore.WHITE}https://t.me/fps_plugins1")
print(f"{Fore.YELLOW}{Style.BRIGHT}  * Наш FunPay магазин:  {Fore.WHITE}https://funpay.com/users/11535828/{Style.RESET_ALL}")
print(f"{Fore.CYAN}  * Модули студии:       [SMM Engine] [Anti-Ban Guard] [License Manager] [Sales Analytics]{Style.RESET_ALL}\n")

if not os.path.exists("configs/_main.cfg"):
    first_setup()
    sys.exit()

try:
    logger.info("$MAGENTAЗагружаю конфиг _main.cfg...")
    MAIN_CFG = cfg_loader.load_main_config("configs/_main.cfg")
    localizer = Localizer(MAIN_CFG["Other"]["language"])
    _ = localizer.translate

    logger.info("$MAGENTAЗагружаю конфиг auto_response.cfg...")
    AR_CFG = cfg_loader.load_auto_response_config("configs/auto_response.cfg")
    RAW_AR_CFG = cfg_loader.load_raw_auto_response_config("configs/auto_response.cfg")

    logger.info("$MAGENTAЗагружаю конфиг auto_delivery.cfg...")
    AD_CFG = cfg_loader.load_auto_delivery_config("configs/auto_delivery.cfg")
except excs.ConfigParseError as e:
    logger.error(e)
    logger.error("Завершаю программу...")
    time.sleep(5)
    sys.exit()
except UnicodeDecodeError:
    logger.error("Произошла ошибка при расшифровке UTF-8. Убедитесь, что кодировка файла = UTF-8, а формат конца строк = LF.")
    logger.error("Завершаю программу...")
    time.sleep(5)
    sys.exit()
except Exception as e:
    logger.critical(f"Произошла непредвиденная ошибка: {e}")
    logger.warning("TRACEBACK", exc_info=True)
    logger.error("Завершаю программу...")
    time.sleep(5)
    sys.exit()

localizer = Localizer(MAIN_CFG["Other"]["language"])

try:
    Cardinal(MAIN_CFG, AD_CFG, AR_CFG, RAW_AR_CFG, VERSION).init().run()
except KeyboardInterrupt:
    logger.info("Завершаю программу FunPay Studio...")
    sys.exit()
except Exception as e:
    logger.critical(f"При работе FunPay Studio произошла ошибка: {e}")
    logger.warning("TRACEBACK", exc_info=True)
    time.sleep(5)
    sys.exit()
