#!/bin/bash

echo "Enter 'pool bounceable address' and press [Enter] to continue"
read addr
echo "Enter 'admin seqno' and press [Enter] to continue"
read seqno

fift -I ./../lib/ -s ./../smartcont/whitelist-del.fif 1 0x1cec8575bca1f10e74277bb02df8714030f839ff8cfd7394ce7e2b0b9cd787a5
fift -I ./../lib/ -s ./../lib/wallet-v2.fif ./../wallets/admin $addr $seqno 1.0 -B whitelist-del-query.boc
lite-client -C ./../config/ton-lite-client-test1.config.json -c "sendfile wallet-query.boc"