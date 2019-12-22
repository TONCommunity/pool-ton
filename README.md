# Pool TON Service

## Description

The service allows to pool user funds in the TON blockchain network for some specific purpose and the subsequent proportional distribution of the funds (if necessary).
Examples: raising funds to create a validator, raising funds to buy something, etc.

To create a pool use the telegram bot ([@pool_ton_bot](https://t.me/pool_ton_bot "@pool_ton_bot")), in which three types of pools are available:
- Public (The pool is visible in the list of public pools)
- Non-public (The pool is not visible in the list of public pools, access by link sharing)
- Private (The pool is not visible in the list of public pools, access by link sharing, administrator confirmation is necessary)

After filling in all the requested parameters, you must initialize it with transfering a certain amount of gram to the given address (it will be used to pay commission fees for successful transactions).
For the pool to work properly, it is VERY IMPORTANT to put a sufficient amount of grams on commission fees!
After successful initialization, you will receive a link to your pool and the address for participation.
In a private pool, the administrator must enter the whitelist manually.

## Principle of operation

To participate in the pool, the participant must transfer N + 1 gram to the given address (required for commission fees, the surplus will be returned to your account).
After collecting all the necessary funds, the pool administrator can transfer the funds to the destination address.
After getting a refund from the destination address (for example, a refund after validation), the pool administrator can re-transfer the funds to the destination address.
After the end of the pool’s lifetime, each participant can submit a request from 1 gram to proportional balance distribution.

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

## Description of the smart contract

Fift scripts are implemented to work with smart contracts.
To deposit funds, the participant must transfer N + 1 grams with the usual request.
To perform any service requests, it is necessary to send 1 gram in the request with the attached message body of the command.
If the request is successful, 1 gram will be returned, otherwise, the balance will be returned with commission deducted.

The smart contract contains the following functions:
- Deposit - deposit is possible only when the pool is open, the amount of funds should be in the declared min, max limits.
If a whitelist is announced, then the participant must be in it to deposit funds.
- Proportional refund - a proportional refund is only possible when the pool is closed.
- Gram transfer - transfer the gram by the pool administrator to the destination address.
- Adding to the whitelist - only a pool administrator can enter a user's address into the whitelist.
- Removing from whitelist - only a pool administrator can remove a user's address from a whitelist.

All basic settings are set during initialization (via recv_external).

The smart contract contains the following get methods:
- seqno
- config (creation timestamp, lifetime, wc destination address, a destination address, amount of fees, minimum fee, maximum fee)
- grams (number of grams collected)
- admins (list of administrators)
- whitelist (list of entries in the whitelist)
- members (list of participants and their balances)
- member_stake (balance of a specific member)
- timeleft (remaining pool lifetime)
- withdrawals (list of withdrawals)

## Developers

- [vanasprin](https://github.com/vanasprin "vanasprin") (smartcontract & scripts)
- [alexhol](https://github.com/alexhol "alexhol") (telegram bot)

## Design

Our designer [@insiua](https://t.me/insiua "@insiua") also took the initiative in implementing the interface of the web version of the pool.

![WEB](/web/design.jpeg?raw=true "WEB")

## Thanks

Special thanks to [@rulon](https://t.me/rulon "@rulon") and the [@tondev_ru](https://t.me/tondev_ru "@tondev_ru") community for their help with the brainlags.
