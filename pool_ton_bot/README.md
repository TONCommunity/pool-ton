## Installation

To run pool_ton_bot you need python version 3.6.9 or later.

Before starting the bot, you need to go to the directory, create a virtual environment and install the dependencies:
```
virtualenv venv
. venv / bin / activate
pip install -r requirements.txt
```

Next, in the config.py file, you need to configure the following values:
```
BOT_TOKEN - token for launching a tg-bot;
DB_AUTH - whether to use authentication when connecting to mongodb
the values   below are required for authentication when connecting to mongodb. if DB_AUTH = False, they are not used
DB_SERVER, DB_NAME, DB_LOGIN, DB_PASSWORD - server address, database name, username and password for connecting to mongodb;

WEBHOOK - Use webhook to receive commands from Telegram
The values   below are required to install WEBHOOK. if WEBHOOK = False, they are not used
WEBHOOK_PORT - port
WEBHOOK_IP - server ip-address
WEBHOOK_SSL_PUB - file name with public key
WEBHOOK_SSL_PRIVATE - file name with private key
WEBHOOK_URL = f "https: // {WEBHOOK_IP}: {WEBHOOK_PORT} / {BOT_TOKEN}"

ADMIN_SCRIPTS - path to the archive with contract administration scripts
USER_SCRIPTS - path to the archive with user scripts
POOLS_DIR - directory for storing .boc files
FIFT_SCRIPTS_DIR - a directory with scripts for the functioning of the bot
TON_CLIENT_CONFIG - path to the file "ton-client.config"

POOL_INIT_AMOUNT - the number of grams that the bot will ask the user when creating the pool
```

To start pool_ton_bot, you must run the command
```
python app.py
```
