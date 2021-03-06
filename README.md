## Py-Tracker
A tracker for cryptocurrencies

Py-tracker is a python-based tracker for cryptocurrencies where you are in control of all keys and connections to your accounts. Moreover it gives the possibility to plot single token balance or single account balance and have pretty candle-graphs to track balance. I still have a lot of improvement to do but would be very glad to collaborate and make it better! 

*Instructions for first use:* Download all files to a folder. 
Before running main.exe you will need to put into the file system/scantokens.csv your own API token for Ethscan (if you are going to track any ethereum wallet) --> https://etherscan.io/apis and/or your own API for BSCScan (for BSC wallets) --> https://docs.bscscan.com/getting-started/viewing-api-usage-statisticsb if you do not plan on tracking ETH or BSC wallets you can skip this step.

When you run Py-tracker for the first time you will be prompted to add your account informations. You will need to input an Account name (eg. Metamask), flag custodial if it is an exchange account or leave it unflagged if it is a non-custodial wallet, input the network* (see below), for Cardano only flag Delegate if the wallet you are tracking has been used to delegate to staking pools (otherwise the balance will be seen as zero), input Public address of non-custodial wallet (NEVER SHARE YOUR PRIVATE KEYS, INPUT PUBLIC ADDRESS ONLY), for exchange accounts you will be required to insert your API key and private token (leaving network empty). Follow instructions to generate your API keys for exchanges (READ-ONLY PERMISSIONS) --> Binance: https://www.binance.com/en/support/faq/360002502072 Crypto.com Exchange: https://help.crypto.com/en/articles/3511424-api Coinbase: https://developers.coinbase.com/docs/wallet/api-key-authentication

* Enter the abbreviation in parenthesis in the following list: For now supported networks are ethereum (ETH), Binance Smart Chain (BSC), Cardano (ADA), Tron (TRX). I am working to increase support. If you have coins in other networks that are not supported add them to othertokens.csv file (either by modifying it directly or via interface).
            
*Google Drive backup:* with Py-Tracker you can create a backup of your files with your google drive account. This way it is possible to use Py-tracker in different devices and keep you data always updated. However, for maximum security you will have to create your own Google Drive API keys, you can find the instruction in this link: https://pythonhosted.org/PyDrive/quickstart.html#authentication put the file client-secrets.json inside the main folder of Py-Tracker (not inside system folder). There is no need to do this if you do not intend to use google drive.

*Ignore file:* Due to the fact that nowadays scammers started doing scam tokens airdrops and dust attacks you can ignore these tokens when using Py-Tracker. You can do that by inserting the name of the tokens and the account name where they are in the ignore file (either directly modifying the ignore.csv file or via interface).


*Updating Crypto.com App balance:* Crypto.com App does not have to this date an API for getting updated balances. Unfortunately users will have to do it by hand. You can follow the instructions here https://help.crypto.com/en/articles/3438579-how-do-i-export-my-transaction-history-app the resulting file will follow the nomenclature: crypto_transactions_record_DATE_NNNNNN.csv put this file as is in the main folder of Py-Tracker and it will be processed accordingly. After processing the file will be moved to the folder ./crypto.com-obs

*Binance locked staking:* Binance to this date does not transmit the data regarding locked staking under "Earn wallet". For a correct calculation make sure to manually add all tokens you are currently locked staking in Binance to the binancestaking.csv file.

## *ATTENTION* I will *NEVER* ask for your private keys or recovery sentence of non-custodial wallets. In case of exchange accounts *ONLY* use read-only APIs to use Py-Tracker. Be safe, the crypto world is teeming with scammers.



