# CryptominersAnalysisTools
A collection of tools for cryptominers analysis. Part of the Cryptominers Anatomy blog series by Maor Dahan.


## Candidate table (Part I)
In the first blog there is a candidate table that was generated using this tool. The table holds
the most relevant crypto coins that attacker could use for its cryptomining malware. They are sorted
by the profitability of mining them using a formula that considered its reward per block mining and
the network hashrate which predict the chances of wining the block mining race respective to the botnet
size and computing power.

Here is an example of it's output where the most relevant coins are both privacy and ASIC resistant ones.
```
Name                     | Algorithm    | Privacy Coin | ASIC resistant | KHR Profit
------------------------------------------------------------------------------------
SUMO                     | CryptoNightR |      No      |      Yes       | 0.00029647
FNNC                     | YescryptR16  |      No      |      Yes       | 0.00021125
Yerbas                   | GhostRider   |      No      |      Yes       | 0.00020158
RTM                      | GhostRider   |     Yes      |      Yes       | 0.00013138
FSC                      | GhostRider   |      No      |      Yes       | 0.00009290
Kylacoin                 | Flex         |      No      |      Yes       | 0.00007729
LCN                      | Flex         |      No      |      Yes       | 0.00007559
SPRX                     | YesPoWer     |      No      |      Yes       | 0.00004781
Monero                   | RandomX      |     Yes      |      Yes       | 0.00003965
Quantum Resistant Ledger | RandomX      |      No      |      Yes       | 0.00002945
Pascal                   | RandomHash2  |      No      |      Yes       | 0.00001978
XMC                      | CryptoNight  |      No      |       No       | 0.00001740
XELIS                    | XelisHash    |      No      |      Yes       | 0.00000289
Babacoin                 | GhostRider   |      No      |      Yes       | 0.00000096
GBX                      | NeoScrypt    |     Yes      |      Yes       | 0.00000091
Litecoin                 | Scrypt       |     Yes      |       No       | 0.00000076
GSPC                     | GhostRider   |      No      |      Yes       | 0.00000069
Frog Coin                | BMW512       |      No      |      Yes       | 0.00000044
PLUS1                    | HMQ1725      |      No      |      Yes       | 0.00000038
ZOC                      | NeoScrypt    |      No      |      Yes       | 0.00000015
VGC                      | X16Rv2       |      No      |      Yes       | 0.00000012
Zephyr                   | RandomX      |     Yes      |      Yes       | 0.00000003
Avian                    | X16RT        |      No      |      Yes       | 0.00000002
DIME                     | Quark        |      No      |       No       | 0.00000002
Actinium                 | Lyra2z       |      No      |      Yes       | 0.00000001
Verus                    | VerusHash    |     Yes      |      Yes       | 0.00000001
EFL                      | Scrypt       |      No      |       No       | 0.00000000
Dogecoin                 | Scrypt       |      No      |       No       | 0.00000000
Arion                    | X11          |      No      |       No       | 0.00000000
Dash                     | X11          |     Yes      |       No       | 0.00000000
BOLI                     | X11          |      No      |       No       | 0.00000000
BTB                      | Scrypt       |      No      |       No       | 0.00000000
HAL                      | NeoScrypt    |      No      |      Yes       | 0.00000000
NOVO                     | SHA256DT     |      No      |       No       | 0.00000000
Sumokoin - exchanges: 1 - markets: 1
Raptoreum - exchanges: 6 - markets: 9
Monero - exchanges: 31 - markets: 59
XMC - exchanges: 3 - markets: 4
Zephyr - exchanges: 9 - markets: 15
Verus - exchanges: 3 - markets: 6
```

## Acknowledgments
Akamai data science department for insighhtful data.

## License
This repository is under [Apache License 2.0](https://github.com/akamai/CryptominersAnalysisTools/blob/main/LICENSE)