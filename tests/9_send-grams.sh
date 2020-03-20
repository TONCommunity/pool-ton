#!/bin/bash

echo "Enter 'pool bounceable address' and press [Enter] to continue"
read addr
echo "Enter 'admin seqno' and press [Enter] to continue"
read seqno
echo "Enter 'dest bounceable address' and press [Enter] to continue"
read dest

fift -I ./../lib/ -s ./../smartcont/grams-send.fif $dest
fift -I ./../lib/ -s ./../lib/wallet-v2.fif ./../wallets/admin $addr $seqno 1.0 -B grams-send-query.boc
lite-client -C ./../config/ton-lite-client-test1.config.json -c "sendfile wallet-query.boc"