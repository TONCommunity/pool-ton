# Pool TON Service

## Links

- [promo website](https://ton.ms/ "promo website")
- [promo video](https://www.youtube.com/watch?v=j1TLFYJzGoM "promo video")

## Description

The service allows to pool user funds in the TON blockchain network for some specific purpose and the subsequent proportional distribution of the funds (if necessary).
Examples: raising funds to create a validator, raising funds to buy something, etc.

To create a pool use the telegram bot ([@pool_ton_bot](https://t.me/pool_ton_bot "@pool_ton_bot")), in which three types of pools are available:
- Public (The pool is visible in the list of public pools)
- Non-public (The pool is not visible in the list of public pools, access by link sharing)
- Private (The pool is not visible in the list of public pools, access by link sharing, administrator confirmation is necessary)

After filling in all the requested parameters, you must initialize it with transfering a certain amount of gram to the given address.
After successful initialization, you will receive a link to your pool and the address for participation.
In a private pool, the administrator must enter the whitelist manually.

## Principle of operation

To participate in the pool, the participant must transfer N + 1 gram to the given address (required for commission fees, the surplus will be returned to your account).
After collecting all the necessary funds, the pool administrator can transfer the funds to the destination address.
After the return the funds from the destination address or the end of the pool’s lifetime, each participant can submit a request from 1 gram to proportional balance distribution.

## Description of the smart contract

Fift scripts are implemented to work with smart contracts.
To deposit funds, the participant must transfer N + 1 grams with the usual request.
To withdrawal funds, the participant must transfer 1 grams with the usual request after the return the funds from the destination address or the end of the pool’s lifetime.
To perform any service requests, it is necessary to send 1 gram in the request with the attached message body of the command.

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
- config (creation timestamp, lifetime, wc destination address, a destination address, amount of fees, minimum fee, maximum fee, fulfilled)
- grams (number of grams collected)
- admins (list of administrators)
- whitelist (list of entries in the whitelist)
- members (list of participants and their balances)
- member_stake (balance of a specific member)
- timeleft (remaining pool lifetime)
- withdrawals (list of withdrawals)
