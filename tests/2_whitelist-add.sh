#!/bin/bash

echo "Enter 'pool bounceable address' and press [Enter] to continue"
read addr
echo "Enter 'admin seqno' and press [Enter] to continue"
read seqno

fift -I ./../lib/ -s ./../smartcont/whitelist-add.fif 3 0x830d1d8b701eeebbcb1b020578e789f9540ad5db961c1d650bd0a908dc9b9987 0xa35869e0bd7ad83c83df83b61747dcd09fb1a39ad829d7c6c6fb1ca50dc4579c 0x1cec8575bca1f10e74277bb02df8714030f839ff8cfd7394ce7e2b0b9cd787a5
fift -I ./../lib/ -s ./../lib/wallet-v2.fif ./../wallets/admin $addr $seqno 1.0 -B whitelist-add-query.boc
lite-client -C ./../config/ton-lite-client-test1.config.json -c "sendfile wallet-query.boc"