## Py-Tracker
A tracker for cryptocurrencies

Py-tracker is a python-based tracker for cryptocurrencies where you are in control of all keys and connections to your accounts. Moreover it gives the possibility to plot single token balance or single account balance and have pretty candle-graphs to track balance. I still have a lot of improvement to do but would be very glad to collaborate and make it better!

*Instructions for first use:* You will need to put in the file system/scantokens.csv your own API token for Ethscan (if you are going to track any ethereum wallet) --> https://etherscan.io/apis and/or your own API for BSCScan (for BSC wallets) --> https://docs.bscscan.com/getting-started/viewing-api-usage-statisticsb

When you run Py-tracker for the first time you will be prompted to add your account informations. You will need to input an Account name (eg. Metamask), flag custodial if it is an exchange account or leave it unflagged if it is a non-custodial wallet, input the network (see below), for Cardano only flag Delegate if the wallet you are tracking has been used to delegate to staking pools (otherwise the balance will be seen as zero), input Public address of non-custodial wallet (NEVER SHARE YOUR PRIVATE KEYS, INPUT PUBLIC ADDRESS ONLY), for exchange accounts you will be required to insert your API key and private token (leaving network empty). Follow instructions to generate your API keys for exchanges (READ-ONLY PERMISSIONS) --> Binance: https://www.binance.com/en/support/faq/360002502072 Crypto.com Exchange: https://help.crypto.com/en/articles/3511424-api Coinbase: https://developers.coinbase.com/docs/wallet/api-key-authentication



## *ATTENTION* I will *NEVER* ask for your private keys or recovery sentence of non-custodial wallets. In case of exchange accounts *ONLY* use read-only APIs to use Py-Tracker. Be safe, the crypto world is teeming with scammers.



