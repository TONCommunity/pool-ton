#!/bin/bash

echo "Enter 'pool open timestamp (10 length)' and press [Enter] to continue"
read timestamp

# usage: <filename-base> <workchain-id> <total-amount> <min-stake> <max-stake> <pool-open> <pool-lifetime> <K> <admin-pubkey1> [<admin-pubkey2> ... <destination-addr>]
fift -I ./../lib/ -s ./../smartcont/pool-init.fif pool -1 5 1 3 $timestamp 600 1 0x1cec8575bca1f10e74277bb02df8714030f839ff8cfd7394ce7e2b0b9cd787a5

echo "Send '5 grams' to the 'non-bounceable address' and press [Enter] to continue"
read

lite-client -C ./../config/ton-lite-client-test1.config.json -c "sendfile pool-query.boc"