## Build

- build.sh - compiles pool-code.fc to pool-code.fif.

- build-storage.sh - compiles pool-init-storage.fc to pool-init-storage.fif.

## Func scripts

- pool-code.fc - smart contract code.
- pool-init-storage.fc - init storage code.

## Fift scripts

- grams-send.fif - creates the message body to be sent from a wallet to send funds to destination address.
- stake-recover.fif - creates the message body to be sent from a wallet to recover its stakes or bonuses.
- whitelist-add.fif - creates the message body to be sent from a wallet to add pubkeys into pool whitelist.
- whitelist-del.fif - creates the message body to be sent from a wallet to delete pubkeys from pool whitelist.
- pool-init.fif - creates a new pool in specified workchain id.
