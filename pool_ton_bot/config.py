BOT_TOKEN = ''

DB_AUTH = True
DB_SERVER = '127.0.0.1'
DB_NAME = ''
DB_LOGIN = ''
DB_PASSWORD = ''

WEBHOOK = True
WEBHOOK_PORT = 443
WEBHOOK_IP = ''
WEBHOOK_SSL_PUB = 'cert.pem'
WEBHOOK_SSL_PRIVATE = 'private.key'
WEBHOOK_URL = f"https://{WEBHOOK_IP}:{WEBHOOK_PORT}/{BOT_TOKEN}"

ADMIN_SCRIPTS = 'admin-fift-scripts.zip'
USER_SCRIPTS = 'user-fift-scripts.zip'
POOLS_DIR = '/root/pool_ton_bot/pools'
FIFT_SCRIPTS_DIR = '/root/pool_ton_bot/fift'
TON_CLIENT_CONFIG = "/root/ton-client.config"

POOL_INIT_AMOUNT = 10

FIFT_COMMAND = 'fift -s ' + FIFT_SCRIPTS_DIR + '/{filename}.fif {params}'
LITE_CLIENT_COMMAND = "lite-client -C " + TON_CLIENT_CONFIG + " -c 'sendfile " + POOLS_DIR + "/{pool_id}-query.boc'"


LANGUAGE_SELECTOR = {
    'ru': 'Русский 🇷🇺',
    'en': 'English 🇺🇸',
}
SUPPORTED_LANGUAGES = LANGUAGE_SELECTOR.keys()
ADMINS = (
    000000000,
    000000001,
)


BUTTONS = (
    'Create pool', 'Создать пул',
    'My pools', 'Мои пулы',
    'Settings', 'Настройки',
    'Feedback', 'Обратная связь',
)

SUPPORTED_COMMANDS = (
    'start',
    'help',
)

ADR_CHECK_API = 'https://api.ton.sh/getAddressInformation?address={adr}'
POOL_CHECK_API = 'https://api.ton.sh/getAddressState?address={adr}'

IGNORE_CALLBACK = 'ignore'
