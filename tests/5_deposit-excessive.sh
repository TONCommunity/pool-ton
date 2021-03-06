#!/bin/bash

echo "Enter 'pool bounceable address' and press [Enter] to continue"
read addr

echo "Enter 'user1 seqno' and press [Enter] to continue"
read seqno

fift -I ./../lib/ -s ./../lib/wallet-v2.fif ./../wallets/user1 $addr $seqno 7.0
lite-client -C ./../config/ton-lite-client-test1.config.json -c "sendfile wallet-query.boc"