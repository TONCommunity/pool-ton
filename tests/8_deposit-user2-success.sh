#!/bin/bash

echo "Enter 'pool bounceable address' and press [Enter] to continue"
read addr

echo "Enter 'user2 seqno' and press [Enter] to continue"
read seqno

fift -I ./../lib/ -s ./../lib/wallet-v2.fif ./../wallets/user2 $addr $seqno 4.0
lite-client -C ./../config/ton-lite-client-test1.config.json -c "sendfile wallet-query.boc"