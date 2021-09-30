import json
import logging
import binance.exceptions
import pandas as pd
from forex_python.converter import CurrencyRates
from binance.client import Client
import hmac
import hashlib
import requests
import time
import os
import numpy as np
import copy
import datetime as dt
import sys
import shutil
from coinbase.wallet.client import Client as CoinbaseClient
import pickle as pk
from currency_converter import CurrencyConverter

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='executionlog.log')

# ------------------------------------------------------------ #
version = "Version 2021-09-30"
# ------------------------------------------------------------ #

# ------------------------------------------------------------ #
#          Starting path, setup and scan tokens                #
# ------------------------------------------------------------ #

wdir = os.getcwd() + "\\system"
if wdir not in sys.path:
    sys.path.insert(0, wdir)

scantokens = pd.read_csv(wdir + "\\scantokens.csv")

etherscan_token = scantokens.loc[scantokens['Scan'] == "EthScan", "Token"].tolist()[0]
bscscantoken = scantokens.loc[scantokens['Scan'] == "BSCScan", "Token"].tolist()[0]


def get_setup():
    if "setup.json" not in os.listdir():
        return []
    else:
        with open("setup.json") as ol:
            loaded_setup = json.load(ol)
        return loaded_setup

# Load Setup
setup = get_setup()


# ------------------------------------------------------------ #
#                      Utility functions                       #
# ------------------------------------------------------------ #

def str_to_datetime(date: str):
    try:
        if len(date) > 11:
            new_date = dt.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        else:
            new_date = dt.datetime.strptime(date, '%Y-%m-%d')

        return new_date

    except ValueError:
        print("Invalid format. Allowed formats are: YYYY-MM-DD and YYYY-MM-DD HH:MM:SS")

def create_new_balance_dict():
    new_dict = dict({'byAccount': dict(), 'total': {'open': pd.DataFrame(), 'close': pd.DataFrame(),
                                                                'high': pd.DataFrame(), 'low': pd.DataFrame(),
                                                                'totalbalance': pd.DataFrame(),
                                                                'pltotale': pd.DataFrame()}})
    return new_dict

def get_currency_rate(currency='USD'):
    try:
        if currency != "USD":
            currency_rates = CurrencyRates()
            conversion_rate = currency_rates.get_rate('USD', currency)
        else:
            conversion_rate = 1
    except requests.exceptions.ConnectionError:
        if currency != "USD":
            currency_rates = CurrencyConverter()
            conversion_rate = currency_rates.convert(1, 'USD', currency)
        else:
            conversion_rate = 1
    return conversion_rate


def datetime_to_str(date, houroutput=True):
    if houroutput:
        new_date = date.strftime('%Y-%m-%d %H:%M:%S')
    else:
        new_date = date.strftime('%Y-%m-%d')
    return str(new_date)


def ignore_tokens(tokensdf, loc) -> pd.DataFrame:
    ignore = pd.read_csv(wdir + "\\ignore.csv")
    if ignore.shape[0] > 0:
        ignore_temp = ignore[ignore['Location'] == loc]
        if ignore_temp.shape[0] > 0:
            vout = tokensdf.loc[[k for k in list(tokensdf.index) if k not in list(ignore_temp['Token'])]]
            return vout
        else:
            return tokensdf
    else:
        return tokensdf


def get_coingecko_networks(chain):
    from difflib import SequenceMatcher
    vout = requests.get(f'http://api.coingecko.com/api/v3/asset_platforms')
    vout = vout.json()
    vout = [e.get('id') for e in vout if
            SequenceMatcher(None, chain.upper(), e.get('name').upper()).ratio() >= 0.6 or chain.upper() in e.get(
                'name').upper()]
    return vout


if 'networklist.pickle' not in os.listdir():
    netlist = requests.get(f'http://api.coingecko.com/api/v3/asset_platforms')
    netlist = netlist.json()
    with open('networklist.pickle', 'wb') as handle1:
        pk.dump(netlist, handle1, protocol=pk.HIGHEST_PROTOCOL)
else:
    if dt.datetime.now().timestamp() - os.path.getmtime('networklist.pickle') >= 604800:
        netlist = requests.get(f'http://api.coingecko.com/api/v3/asset_platforms')
        netlist = netlist.json()
        with open('networklist.pickle', 'wb') as handle1:
            pk.dump(netlist, handle1, protocol=pk.HIGHEST_PROTOCOL)
    else:
        with open('networklist.pickle', 'rb') as handle1:
            netlist = pk.load(handle1)

netlistfinal = [a.get('id') for a in netlist if a.get('id') != '']


# ------------------------------------------------------------ #
#                  Get balances functions                      #
# ------------------------------------------------------------ #

def other_tokens() -> pd.DataFrame:
    other = [wdir + "\\" + x for x in os.listdir(wdir) if x == 'othertoken.csv']
    if len(other) != 0:
        vout = pd.read_csv(other[0])
        vout.index = vout['Token'].tolist()
        vout.drop('Token', axis=1, inplace=True)
        for k in range(vout.shape[0]):
            if vout.loc[list(vout.index)[k], 'Contract'] == '0':
                vout.loc[list(vout.index)[k], 'Contract'] = 0

        if isinstance(vout, pd.Series):
            vout = pd.DataFrame(vout).T

        return vout
    else:
        return pd.DataFrame()


def get_eth_erc20_balance(ethaddress, etherscantoken, locname):
    resp = requests.get(f"https://api.etherscan.io/api?module=account&action=balance&address={ethaddress}"
                        f"&tag=latest&apikey={etherscantoken}")

    eth_balance = int(json.loads(resp.content).get('result')) / (10 ** 18)
    total_value = [eth_balance]
    total_amount = ["ETH"]
    contract_list = [0]
    in_or_out = [1]

    erc20 = requests.get(f"https://api.etherscan.io/api?module=account&action=tokentx&address={ethaddress}"
                         f"&startblock=0&endblock=9999999999&sort=asc&apikey={etherscantoken}")
    erc20 = erc20.json()

    [total_amount.append(s.get('tokenSymbol')) for s in erc20.get('result')]
    [total_value.append(int(s.get('value')) / (10 ** 18)) for s in erc20.get('result')]
    [contract_list.append(s.get('contractAddress')) for s in erc20.get('result')]

    contract_df = pd.Series(data=contract_list, index=total_amount)

    for erc20_token in erc20.get('result'):
        if erc20_token.get('to').upper() == ethaddress.upper():
            in_or_out.append(1)
        elif erc20_token.get('from').upper() == ethaddress.upper():
            in_or_out.append(-1)

    total_pl = [total_value[k] * in_or_out[k] for k in range(len(total_value))]

    all_tokens = pd.DataFrame(dict({'tokens': total_amount, 'amount': total_pl})).groupby(['tokens']).sum()

    vout = pd.Series(all_tokens.iloc[:, 0], all_tokens.index)
    vout.index = [x.upper() for x in vout.index]
    vout = vout[vout > 0]
    vout = pd.merge(vout, pd.DataFrame(contract_df), left_index=True, right_index=True)
    vout.columns = ['Amount', 'Contract']
    vout['Network'] = 'ethereum'

    return ignore_tokens(vout, locname)


def get_tron_wallet_balance(address, locname):
    trx_tokens, trx_amounts, trx_contracts = ([], [], [])

    trx_response = requests.get(f"https://apilist.tronscan.org/api/account?address={address}")
    trx_response = trx_response.json()

    trx_frozen = (trx_response.get('frozenForEnergy') + trx_response.get('frozenForBandWidth')) / 1000000
    [trx_amounts.append(s.get('amount')) for s in trx_response.get('tokens')]
    [trx_tokens.append(s.get('tokenAbbr').upper()) for s in trx_response.get('tokens')]
    [trx_contracts.append(trx_response.get('tokens')[n].get('tokenId')) for n in range(len(trx_response.get('tokens')))]
    for i in range(len(trx_contracts)):
        if trx_contracts[i] == "_":
            trx_contracts[i] = 0

    contract_df = pd.Series(data=trx_contracts, index=trx_tokens)

    trx_amounts.append(trx_frozen)
    trx_tokens.append("TRX")
    trx_amounts = [float(k) for k in trx_amounts]

    token_df = pd.DataFrame(dict({'tokens': trx_tokens, 'amount': trx_amounts})).groupby(['tokens']).sum()

    vout = pd.Series(token_df.iloc[:, 0], token_df.index)
    vout.index = [x.upper() for x in vout.index]
    vout = vout[vout > 0]
    vout = pd.merge(vout, pd.DataFrame(contract_df), left_index=True, right_index=True)
    vout.columns = ['Amount', 'Contract']
    vout['Network'] = 'tron'

    return ignore_tokens(vout, locname)


def get_bsc_bep20_balance(bscaddress, bsctoken, locname):
    url = f'https://api.bscscan.com/api?module=account&action=balance&address={bscaddress}&tag=latest&apikey={bsctoken}'

    response = requests.get(url)
    bnb_balance = int(response.json().get('result')) / 10 ** 18
    total_tokens = ["BNB"]
    token_decimals = [10 ** 18]
    contracts_list = [0]

    # Get current BEP20
    bep20 = requests.get(f'https://api.bscscan.com/api?module=account&action=tokentx&address={bscaddress}&'
                         f'startblock=0&endblock=999999999999999&sort=asc&apikey={bsctoken}')

    bep20 = bep20.json()

    [total_tokens.append(s.get('tokenSymbol')) for s in bep20.get('result')]
    [contracts_list.append(s.get('contractAddress')) for s in bep20.get('result')]
    [token_decimals.append(10 ** int(s.get('tokenDecimal'))) for s in bep20.get('result')]

    vout = pd.DataFrame({'Tokens': total_tokens, 'Contract': contracts_list, 'Dec': token_decimals})
    vout.drop_duplicates(inplace=True)
    vout.reset_index(inplace=True, drop=True)
    vout['Amount'] = 0

    for line_index in range(vout.shape[0]):
        if vout.loc[line_index, 'Tokens'] == 'BNB':
            vout.loc[line_index, 'Amount'] = bnb_balance
        else:
            tokenbalance = requests.get(f'https://api.bscscan.com/api?module=account&action=tokenbalance'
                                        f'&contractaddress={vout.loc[line_index, "Contract"]}&address={bscaddress}&'
                                        f'tag=latest&apikey={bsctoken}')
            vout.loc[line_index, 'Amount'] = int(tokenbalance.json().get('result')) / vout.loc[line_index, 'Dec']

    duplicated_tokens = [(x, k) for x, k in enumerate(list(vout['Tokens'])) if list(vout['Tokens']).count(k) > 1]
    if len(duplicated_tokens) > 0:
        for ind, name in duplicated_tokens:
            vout.loc[ind, 'Tokens'] = name + "-" + vout.loc[ind, 'Contract'][-5:len(vout.loc[ind, 'Contract'])]

    vout.index = [i.upper() for i in vout['Tokens']]
    vout.drop(['Dec', 'Tokens'], axis=1, inplace=True)
    vout = vout[vout['Amount'] > 0]
    vout = ignore_tokens(vout, locname)
    vout['Network'] = 'binance-smart-chain'
    return vout


def get_cardano_balance(address, delegate=False) -> pd.DataFrame:
    req_response = requests.get(f"https://api.blockchair.com/cardano/raw/address/{address}")
    req_response = req_response.json()

    amount_in = int(req_response.get('data').get(address).get('address').get('caTotalInput').get('getCoin')) / 10 ** 6
    amount_out = int(req_response.get('data').get(address).get('address').get('caTotalOutput').get('getCoin')) / 10 ** 6
    fee = int(req_response.get('data').get(address).get('address').get('caTotalFee').get('getCoin')) / 10 ** 6

    if delegate:
        delegation_transaction = req_response.get('data').get(address).get('address').get('caTxList')
        fee -= int(delegation_transaction[len(delegation_transaction) - 1].get('ctbFees').get('getCoin')) / 10 ** 6
        amount_out = pd.DataFrame(dict({'Amount': [amount_in - fee - 2],
                                        'Contract': 0, 'Network': 'cardano'}))  # 2 is the KeyDeposit
        amount_out.index = ["ADA"]
        return amount_out
    else:
        if amount_in - amount_out - fee < 0:
            total_amount = 0
        else:
            total_amount = amount_in - amount_out - fee

    amount_out = pd.DataFrame(
        dict({'Amount': [total_amount], 'Contract': 0, 'Network': 'cardano'}))  # 2 is the KeyDeposit
    amount_out.index = ["ADA"]

    return amount_out


def get_binance_balance(binancetoken, binancesecret, locname) -> pd.DataFrame:
    client = Client(binancetoken, binancesecret)
    account = client.get_account()

    tokens = [account.get('balances')[x].get('asset') for x in range(len(account.get('balances')))
              if
              float(account.get('balances')[x].get('free')) + float(account.get('balances')[x].get('locked')) > 0]
    token_amounts = [float(account.get('balances')[x].get('free')) + float(account.get('balances')[x].get('locked')) for
                     x
                     in range(len(account.get('balances')))
                     if
                     float(account.get('balances')[x].get('free')) + float(
                         account.get('balances')[x].get('locked')) > 0]
    tokens = [tokens[x].replace("LD", "") if tokens[x].startswith("LD") else tokens[x] for x in
              range(len(tokens))]
    tokens = ["ETH" if tokens[x] == "BETH" else tokens[x] for x in range(len(tokens))]

    binance_staking_df = pd.read_csv(wdir + "\\binancestaking.csv")
    if binance_staking_df.shape[0] > 0:
        tokens.extend(list(binance_staking_df.loc[:, 'Token']))
        token_amounts.extend(list(binance_staking_df.loc[:, 'Amount']))

    vout = pd.Series(token_amounts, tokens)
    vout = vout.groupby(vout.index).sum()
    fiat = ["AUD", "BRL", "EUR", "GBP", "GHS", "HKD", "KES", "KZT", "NGN", "NOK", "PHP", "PEN", "RUB", "TRY", "UGX",
            "UAH"]
    is_not_fiat = [x for x in vout.index if x not in fiat]
    vout = vout.loc[is_not_fiat]

    vout = pd.DataFrame(vout)
    vout.columns = ['Amount']

    return ignore_tokens(vout[vout > 0], locname)


def get_crypto_exchange_balance(cryptotoken, cryptosecret, locname) -> pd.DataFrame:
    base_url = "https://api.crypto.com/v2/"

    # Building request as per documentation: https://exchange-docs.crypto.com/spot/index.html#introduction
    req = {
        "id": 11,
        "method": "private/get-account-summary",
        "api_key": cryptotoken,
        "params": {},
        "nonce": int(time.time() * 1000)
    }

    # Ensure the params are alphabetically sorted by key
    paramString = ""

    if "params" in req:
        for key in sorted(req['params']):
            paramString += key
            paramString += str(req['params'][key])

    sigPayload = req['method'] + str(req['id']) + req['api_key'] + paramString + str(req['nonce'])

    req['sig'] = hmac.new(
        bytes(str(cryptosecret), 'utf-8'),
        msg=bytes(sigPayload, 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    req_response = requests.post(base_url + "private/get-account-summary", json=req)
    req_response = req_response.json()

    tokens = [req_response.get('result').get('accounts')[x].get('currency')
              for x in range(len(req_response.get('result').get('accounts')))
              if (req_response.get('result').get('accounts')[x].get('balance') +
                  req_response.get('result').get('accounts')[x].get('available') +
                  req_response.get('result').get('accounts')[x].get('order') +
                  req_response.get('result').get('accounts')[x].get('stake')) != 0]

    token_amounts = [req_response.get('result').get('accounts')[x].get('balance')
                     for x in range(len(req_response.get('result').get('accounts')))
                     if (req_response.get('result').get('accounts')[x].get('balance') +
                         req_response.get('result').get('accounts')[x].get('available') +
                         req_response.get('result').get('accounts')[x].get('order') +
                         req_response.get('result').get('accounts')[x].get('stake')) != 0]

    vout = pd.Series(token_amounts, tokens)
    vout = vout.groupby(vout.index).sum()
    fiat = ["AUD", "BRL", "EUR", "GBP", "GHS", "HKD", "KES", "KZT", "NGN", "NOK", "PHP", "PEN", "RUB", "TRY", "UGX",
            "UAH"]
    isnotfiat = [x for x in vout.index if x not in fiat]
    vout = vout.loc[isnotfiat]

    vout = pd.DataFrame(vout)
    vout.columns = ['Amount']

    return ignore_tokens(vout[vout > 0], locname)


def get_crypto_app_balance(locname):
    new_transactions_file = [wdir.replace("\\system", "\\") + x for x in os.listdir(wdir.replace("\\system", "")) if
                             "crypto_transactions_record" in x]
    history_file = [wdir + "\\" + x for x in os.listdir(wdir) if 'cryptohistory' in x]

    if len(new_transactions_file) == 0 and len(history_file) == 0:
        return "ERROR: Not history nor transaction file found for crypto.com app. " \
               "Note that the file name should follow the nomenlaclature:" \
               "crypto_transactions_record_XXXXXXXX_XXXXXXXX.csv for transaction file and " \
               "cryptohistory.csv for the history file"
    if len(new_transactions_file) != 0:
        if len(history_file) == 0:
            new_transactions_df = pd.read_csv(new_transactions_file[0])

            new_transactions_df.loc[
                new_transactions_df['Transaction Description'] == 'Crypto Earn Deposit', 'Amount'] = 0
            new_transactions_df.loc[
                new_transactions_df['Transaction Description'] == 'Crypto Earn Withdrawal', 'Amount'] = 0
            new_transactions_df.loc[new_transactions_df['Transaction Description'] == 'Recurring Buy', 'Amount'] *= -1
            new_transactions_df.loc[
                new_transactions_df['Transaction Description'] == 'Supercharger Deposit (via app)', 'Amount'] = 0
            new_transactions_df.loc[new_transactions_df['Transaction Description'] == 'CRO Stake', 'Amount'] = 0
            new_transactions_df.loc[
                new_transactions_df['Transaction Description'] == 'Supercharger Withdrawal (via app)', 'Amount'] = 0

            tokens = new_transactions_df['Currency'].tolist()
            tokens.extend(new_transactions_df.dropna()['To Currency'].tolist())

            tokens_amount = new_transactions_df['Amount'].tolist()
            tokens_amount.extend(new_transactions_df.dropna()['To Amount'].tolist())

            vout = pd.Series(tokens_amount, tokens)
            vout = vout.groupby(vout.index).sum()
            fiat = ["AUD", "BRL", "EUR", "GBP", "GHS", "HKD", "KES", "KZT", "NGN", "NOK", "PHP", "PEN", "RUB", "TRY",
                    "UGX",
                    "UAH"]
            is_not_fiat = [x for x in vout.index if x not in fiat]

            to_save_csv = vout.loc[is_not_fiat]
            vout.loc[is_not_fiat].to_csv(
                wdir + "\\cryptohistory" + "_" + new_transactions_file[0].split("_")[3] + ".csv")
        else:
            new_transactions_df = pd.read_csv(new_transactions_file[0])
            last_update = history_file[0].split("\\")[-1].replace("cryptohistory_", "").replace(".csv", "")
            last_update = str_to_datetime(f'{last_update[0:4]}-{last_update[4:6]}-{last_update[6:8]}')
            new_transactions_df['Timestamp Datetime'] = [str_to_datetime(i).date() for i in
                                                         new_transactions_df['Timestamp (UTC)'].tolist()]

            new_transactions_df = new_transactions_df[new_transactions_df['Timestamp Datetime'] > last_update.date()]

            new_transactions_df.loc[
                new_transactions_df['Transaction Description'] == 'Crypto Earn Deposit', 'Amount'] = 0
            new_transactions_df.loc[
                new_transactions_df['Transaction Description'] == 'Crypto Earn Withdrawal', 'Amount'] = 0
            new_transactions_df.loc[new_transactions_df['Transaction Description'] == 'Recurring Buy', 'Amount'] *= -1
            new_transactions_df.loc[
                new_transactions_df['Transaction Description'] == 'Supercharger Deposit (via app)', 'Amount'] = 0
            new_transactions_df.loc[
                new_transactions_df['Transaction Description'] == 'Supercharger Withdrawal (via app)', 'Amount'] = 0
            new_transactions_df.loc[new_transactions_df['Transaction Description'] == 'CRO Stake', 'Amount'] = 0

            tokens = new_transactions_df['Currency'].tolist()
            tokens.extend(new_transactions_df.dropna()['To Currency'].tolist())

            tokens_amount = new_transactions_df['Amount'].tolist()
            tokens_amount.extend(new_transactions_df.dropna()['To Amount'].tolist())

            history_df = pd.read_csv(history_file[0])
            tokens.extend(history_df.iloc[:, 0].tolist())
            tokens_amount.extend(history_df.iloc[:, 1].tolist())
            vout = pd.Series(tokens_amount, tokens)
            vout = vout.groupby(vout.index).sum()
            fiat = ["AUD", "BRL", "EUR", "GBP", "GHS", "HKD", "KES", "KZT", "NGN", "NOK", "PHP", "PEN", "RUB", "TRY",
                    "UGX",
                    "UAH"]
            is_not_fiat = [x for x in vout.index if x not in fiat]

            to_save_csv = vout.loc[is_not_fiat]

            vout.loc[is_not_fiat].to_csv(
                wdir + "\\cryptohistory" + "_" + new_transactions_file[0].split("_")[3] + ".csv")
            shutil.move(history_file[0], history_file[0].replace("system", "crypto.com-obs"))

        shutil.move(new_transactions_file[0],
                    new_transactions_file[0].replace("Pytracker", "Pytracker\\crypto.com-obs"))

        to_save_csv = pd.DataFrame(to_save_csv)
        to_save_csv.columns = ['Amount']

        return ignore_tokens(to_save_csv, locname)
    else:
        history_df = pd.read_csv(history_file[0])
        tokens = history_df.iloc[:, 0].tolist()
        tokens_amount = history_df.iloc[:, 1].tolist()
        vout = pd.Series(tokens_amount, tokens)
        vout = vout.groupby(vout.index).sum()
        fiat = ["AUD", "BRL", "EUR", "GBP", "GHS", "HKD", "KES", "KZT", "NGN", "NOK", "PHP", "PEN", "RUB", "TRY", "UGX",
                "UAH"]
        is_not_fiat = [x for x in vout.index if x not in fiat]

        to_save_csv = vout.loc[is_not_fiat]

        to_save_csv = pd.DataFrame(to_save_csv)
        to_save_csv.columns = ['Amount']

        return ignore_tokens(to_save_csv, locname)


def get_coinbase_balance(token, secret, locname) -> pd.DataFrame:
    client = CoinbaseClient(token, secret)
    account_balance = client.get_accounts()

    balance_list = [float(account_balance.data[s].balance.amount) for s in range(len(account_balance.data)) if
                    float(account_balance.data[s].balance.amount) > 0]
    tokens = [account_balance.data[s].balance.currency for s in range(len(account_balance.data)) if
              float(account_balance.data[s].balance.amount) > 0]
    vout = pd.DataFrame(data=balance_list, columns=['Amount'], index=tokens)

    return ignore_tokens(vout, locname)


# ------------------------------------------------------------ #
#                  Get prices functions                        #
# ------------------------------------------------------------ #

def get_token_prices(tokens: pd.DataFrame, fromdate=0, todate=0, currency='usd'):
    if fromdate == 0:
        timeframe = 7
    else:
        timeframe = dt.datetime.fromtimestamp(todate) - dt.datetime.fromtimestamp(fromdate)
        timeframe = int(timeframe.days)
        if timeframe == 0:
            timeframe = 1
        elif 0 < timeframe <= 7:
            timeframe = 7
        elif 7 < timeframe <= 14:
            timeframe = 14
        elif 14 < timeframe <= 30:
            timeframe = 30
        elif 30 < timeframe <= 90:
            timeframe = 90
        elif 90 < timeframe <= 180:
            timeframe = 180
        else:
            timeframe = 365

    tokens_tickers = [o.upper() for o in tokens.index]

    if 'coingeckolist.pickle' not in os.listdir():
        coingecko_coins_list = requests.get('https://api.coingecko.com/api/v3/coins/list')
        coingecko_coins_list = coingecko_coins_list.json()
        with open('coingeckolist.pickle', 'wb') as gecko_list:
            pk.dump(coingecko_coins_list, gecko_list, protocol=pk.HIGHEST_PROTOCOL)
    else:
        if dt.datetime.now().timestamp() - os.path.getmtime('coingeckolist.pickle') >= 604800:
            coingecko_coins_list = requests.get('https://api.coingecko.com/api/v3/coins/list')
            coingecko_coins_list = coingecko_coins_list.json()
            with open('coingeckolist.pickle', 'wb') as gecko_list:
                pk.dump(coingecko_coins_list, gecko_list, protocol=pk.HIGHEST_PROTOCOL)
        else:
            with open('coingeckolist.pickle', 'rb') as gecko_list:
                coingecko_coins_list = pk.load(gecko_list)
    tokens_prices = []

    for coin, contract, network in zip(tokens_tickers, list(tokens['Contract']), list(tokens['Network'])):
        if contract == 0:
            tok1 = [g.get('id') for g in coingecko_coins_list if g.get('symbol').upper() == coin]
            tokens_prices.append(requests.get(f'http://api.coingecko.com/api/v3/coins/{tok1[0]}'
                                              f'/ohlc?vs_currency={currency}&days={timeframe}'))

        else:
            temp_contract = requests.get(f'https://api.coingecko.com/api/v3/coins/{network}/contract/'
                                         f'{contract}')
            if temp_contract.status_code != 200:
                tokens_prices.append(0)
                print(f'ERROR GETTING PRICE: {temp_contract.json().get("error")} --> {coin}')
                logging.warning(f'ERROR GETTING PRICE {temp_contract.json().get("error")} --> {coin}')
            else:
                temp1 = requests.get(f'https://api.coingecko.com/api/v3/coins/{temp_contract.json().get("id")}'
                                     f'/ohlc?vs_currency={currency}&days={timeframe}')
                if temp1.status_code != 200:
                    tokens_prices.append(0)
                    print(f'ERROR GETTING PRICE: {temp_contract.json().get("error")} --> {coin}')
                    logging.warning(
                        f'ERROR GETTING PRICE {temp_contract.json().get("error")} --> {coin}')
                else:
                    tokens_prices.append(temp1)

    vout = dict()
    for price, coin in zip(tokens_prices, tokens_tickers):
        if price == 0:
            vout[coin] = pd.DataFrame(np.zeros([1, 4]), index=[dt.datetime.now().timestamp()],
                                      columns=["Open", "High", "Low", "Close"])
        else:
            resplist = np.array(price.json()).astype(float)
            vout[coin] = pd.DataFrame(resplist[:, 1:5], columns=["Open", "High", "Low", "Close"],
                                      index=resplist[:, 0] / 1000)
            vout[coin] = vout[coin][np.logical_not(vout[coin].index > dt.datetime.now().timestamp())]

    return vout


def get_binance_prices(bintokenslist: list, binancetoken: str, binancesecret: str,
                       fromdate=0, todate=0, currency='usd') -> dict:
    client = Client(binancetoken, binancesecret)

    total_list = list()
    date_to_column = 0

    if fromdate == 0:
        timeframe = "7 days ago"
    else:
        date_to_column = todate - 9000
        timeframe = dt.datetime.fromtimestamp(todate) - dt.datetime.fromtimestamp(fromdate)
        timeframe = int(timeframe.days)
        if timeframe == 0:
            timeframe = '1 day ago'
        if timeframe == 1:
            timeframe = '1 day ago'
        else:
            timeframe = str(timeframe) + ' days ago'

    stable = [k for k in bintokenslist if k in ["USDT", "USDC", "BUSD"]]
    bintokenslist = [p for p in bintokenslist if p not in stable]

    for coin in bintokenslist:
        try:
            total_list.append(client.get_historical_klines(coin + "USDT", client.KLINE_INTERVAL_1HOUR, timeframe))
        except binance.exceptions.BinanceAPIException:  # Catching binance-python exception APIerror
            print(f'{coin} could not be found, defaulting price to zero')
            logging.warning(f'Binance {coin} could not be found, defaulting price to zero')
            total_list.append(0)

    vout = dict()

    conversion_rate = get_currency_rate(currency.upper())

    for price, coin in zip(total_list, bintokenslist):
        if price == 0:
            vout[coin] = pd.DataFrame(np.zeros([1, 4]), index=[date_to_column],
                                      columns=["Open", "High", "Low", "Close"])
        else:
            response_list = np.array([p[0:5] for p in price]).astype(float)
            vout[coin] = pd.DataFrame(response_list[:, 1:5] * conversion_rate, columns=["Open", "High", "Low", "Close"],
                                      index=response_list[:, 0] / 1000)

    if len(stable) > 0:
        for stab in stable:
            vout[stab] = pd.DataFrame(np.ones([1, 4]) * conversion_rate, index=[date_to_column],
                                      columns=["Open", "High", "Low", "Close"])

    return vout


def get_coinbase_prices(balance: pd.DataFrame, fromdate=0, todate=0, currency='usd') -> dict:

    conversion_rate = get_currency_rate(currency.upper())

    possible_granularities = (60, 300, 900, 3600, 21600, 86400)
    if (todate - fromdate) / 3600 < 300:
        granularity = 3600
    else:
        granularity = [x for x in possible_granularities if (todate - fromdate) / x <= 300]
        granularity = granularity[0]

    if fromdate == 0:
        fromdate = (dt.datetime.now() - dt.timedelta(days=7)).strftime('%Y-%m-%dT00:00:00')
    else:
        fromdate = dt.datetime.fromtimestamp(fromdate).strftime('%Y-%m-%dT00:00:00')

    if todate == 0:
        todate = dt.datetime.now().strftime('%Y-%m-%dT00:00:00')
    else:
        todate = dt.datetime.fromtimestamp(todate).strftime('%Y-%m-%dT%H:%M:%S')

    fiat_or_stable = ["USDC", "USDT", "BUSD", "AUD", "BRL", "EUR", "GBP", "GHS", "HKD", "KES", "KZT", "NGN", "NOK",
                      "PHP", "PEN", "RUB", "TRY", "UGX",
                      "UAH"]
    tokens = [x for x in balance.index if x not in fiat_or_stable]
    response = list()

    for coin in tokens:
        temp = requests.get(
            f'https://api.pro.coinbase.com/products/{coin}-USD/candles?start={fromdate}&end={todate}&'
            f'granularity={granularity}')
        if temp.status_code != 200:
            response.append(0)
            print(f"Token {coin} could not be found in coinbase exchange")
            logging.warning(f"Coinbase token {coin} could not be found in coinbase exchange")
        else:
            response.append(temp)

    vout = dict()
    for price, coin in zip(response, tokens):
        if price == 0:
            vout[coin] = pd.DataFrame(np.zeros([1, 4]), index=[todate],
                                      columns=["Open", "High", "Low", "Close"])
        else:
            vout[coin] = pd.DataFrame(np.array(price.json())[:, 1:5] * conversion_rate,
                                      columns=["Low", "High", "Open", "Close"],
                                      index=np.array(price.json())[:, 0])

    return vout


def get_cryptodotcom_prices(balancedf: pd.DataFrame, todate, currency='usd') -> dict:

    conversion_rate = get_currency_rate(currency.upper())

    prices = []
    stable = [k for k in balancedf.index if k in ["USDT", "USDC", "BUSD"]]
    tokens_list = [p for p in balancedf.index if p not in stable]

    for coin in tokens_list:
        prices.append(
            requests.get(f"https://api.crypto.com/v2/public/get-candlestick?instrument_name={coin}_USDT&timeframe=1h"))

    vout = dict()
    for response, coin in zip(prices, balancedf.index):
        if response.status_code != 200:
            vout[coin] = pd.DataFrame(np.zeros([1, 4]), index=[todate],
                                      columns=["Open", "High", "Low", "Close"])
        else:
            timel = [int(k.get('t')) / 1000 for k in response.json().get('result').get('data')]
            openl = [k.get('o') for k in response.json().get('result').get('data')]
            high = [k.get('h') for k in response.json().get('result').get('data')]
            low = [k.get('l') for k in response.json().get('result').get('data')]
            close = [k.get('c') for k in response.json().get('result').get('data')]
            vout[coin] = pd.DataFrame((np.array([openl, high, low, close]) * conversion_rate).T,
                                      columns=["Open", "High", "Low", "Close"],
                                      index=timel)
    if len(stable) > 0:
        for stab in stable:
            vout[stab] = pd.DataFrame(np.ones([1, 4]) * conversion_rate, index=[todate],
                                      columns=["Open", "High", "Low", "Close"])

    return vout


# ------------------------------------------------------------ #
#                  General functions                           #
# ------------------------------------------------------------ #

def get_balances(setuplist: list, currency='usd', history_dict=None):
    if history_dict is None:
        history_dict = create_new_balance_dict()

        for acc in setuplist:
            history_dict['byAccount'][acc.get('name')] = {'price': dict(), 'balance': pd.DataFrame(),
                                                          'open': pd.DataFrame(), 'close': pd.DataFrame(),
                                                          'high': pd.DataFrame(), 'low': pd.DataFrame()}
        FromDate = 0
        ToDate = 0
        now_timestamp = dt.datetime.now().timestamp()
    else:
        FromDate = max(history_dict['total']['open'].index)
        ToDate = dt.datetime.now().timestamp()
        now_timestamp = ToDate

    print('Getting tokens in othertokens.csv')

    other_tokens_df = other_tokens()
    if other_tokens_df.shape[0] != 0:
        other_tokens_df_simplified = copy.deepcopy(other_tokens_df.drop(['Location', 'IsCustodial'], axis=1))

        prices = get_token_prices(other_tokens_df_simplified, FromDate, ToDate, currency)

        for location in np.unique(list(other_tokens_df.loc[:, 'Location'])):
            if location not in history_dict['byAccount'].keys():
                history_dict['byAccount'][location] = {'price': dict(), 'balance': pd.DataFrame(),
                                                       'open': pd.DataFrame(), 'close': pd.DataFrame(),
                                                       'high': pd.DataFrame(), 'low': pd.DataFrame()}
            tokens_temp = list(other_tokens_df[other_tokens_df['Location'] == location].index)
            vout_price = dict()
            for coin in tokens_temp:
                vout_price[coin] = prices[coin]
            if len(history_dict['byAccount'][location]['price']) == 0:
                history_dict['byAccount'][location]['price'] = vout_price
            else:
                for key in list(history_dict['byAccount'][location]['price']):
                    tempkey = pd.concat([history_dict['byAccount'][location]['price'][key], vout_price.get(key)], axis=0)
                    history_dict['byAccount'][location]['price'][key] = tempkey[~tempkey.index.duplicated(keep='first')]

            vout = pd.DataFrame(
                other_tokens_df_simplified.loc[list(other_tokens_df[other_tokens_df['Location'] == location].index), :])
            if vout.shape[1] != 3:
                vout = vout.T
            vout.drop(['Contract', 'Network'], inplace=True, axis=1)
            if history_dict['byAccount'][location]['balance'].shape[1] == 0:
                history_dict['byAccount'][location]['balance'] = pd.DataFrame(data=vout.iloc[:, 0].tolist(),
                                                                              index=vout.index,
                                                                              columns=[now_timestamp])
            else:
                column_names = list(history_dict['byAccount'][location]['balance'].columns)
                column_names.append(now_timestamp)
                history_dict['byAccount'][location]['balance'] = pd.concat(
                    [history_dict['byAccount'][location]['balance'], vout],
                    axis=1)
                history_dict['byAccount'][location]['balance'].columns = column_names

    def updated_history_dict(dict_to_update: dict, account: dict, prices_to_dict: pd.DataFrame) -> dict:
        if len(dict_to_update['byAccount'][account.get('name')]['price']) == 0:
            dict_to_update['byAccount'][account.get('name')]['price'] = prices_to_dict

            dict_to_update['byAccount'][account.get('name')]['balance'] = pd.DataFrame(
                list(balance_df.loc[:, 'Amount']),
                columns=[now_timestamp],
                index=balance_df.index)

        else:
            all_tokens_list = list(dict_to_update['byAccount'][account.get('name')]['price'])
            all_tokens_list.extend(list(balance_df.index))
            if now_timestamp in dict_to_update['byAccount'][account.get('name')]['balance'].columns:
                tokens = [a for a in dict_to_update['byAccount'][account.get('name')]['balance'].index if
                          a not in all_tokens_list]
                for new_token in tokens:
                    all_tokens_list.append(new_token)
                    other_temp = other_tokens()
                    other_temp = pd.DataFrame(other_temp.loc[new_token, :]).T
                    prices_temp_df = get_token_prices(other_temp, FromDate, ToDate, currency)
                    prices[new_token] = prices_temp_df[new_token]
            for coin_to_add in np.unique(all_tokens_list):
                if coin_to_add not in dict_to_update['byAccount'][account.get('name')]['price'].keys():
                    dict_to_update['byAccount'][account.get('name')]['price'][coin_to_add] = prices_to_dict.get(
                        coin_to_add)
                else:
                    price_to_add = pd.concat(
                        [dict_to_update['byAccount'][account.get('name')]['price'][coin_to_add],
                         prices_to_dict.get(coin_to_add)],
                        axis=0)
                    dict_to_update['byAccount'][account.get('name')]['price'][coin_to_add] = price_to_add[
                        ~price_to_add.index.duplicated(keep='first')]

            token_amounts_df = pd.DataFrame(balance_df.loc[:, 'Amount'])
            token_amounts = [y[0] for y in token_amounts_df.values]

            if dict_to_update['byAccount'][account.get('name')]['balance'].shape[1] == 0:
                dict_to_update['byAccount'][account.get('name')]['balance'] = pd.DataFrame(token_amounts,
                                                                                           columns=[now_timestamp],
                                                                                           index=token_amounts_df.index)
            else:
                temp_column_names = list(dict_to_update['byAccount'][account.get('name')]['balance'].columns)
                if now_timestamp in dict_to_update['byAccount'][account.get('name')]['balance'].columns:
                    balance_now_df = pd.concat(
                        [dict_to_update['byAccount'][account.get('name')]['balance'][now_timestamp], token_amounts_df],
                        axis=1)
                    balance_now_df.fillna(0, inplace=True)
                    token_amounts_df = pd.concat(
                        [dict_to_update['byAccount'][account.get('name')]['balance'].drop([now_timestamp], axis=1),
                         balance_now_df.sum(axis=1)], axis=1)
                    token_amounts_df.fillna(0, inplace=True)
                    token_amounts_df.columns = temp_column_names
                    dict_to_update['byAccount'][account.get('name')]['balance'] = token_amounts_df
                else:
                    temp_column_names.append(ToDate)
                    token_amounts_df = pd.concat(
                        [dict_to_update['byAccount'][account.get('name')]['balance'], token_amounts_df],
                        axis=1)
                    token_amounts_df.fillna(0, inplace=True)
                    token_amounts_df.columns = temp_column_names
                    dict_to_update['byAccount'][account.get('name')]['balance'] = token_amounts_df

        return dict_to_update

    for acc in setuplist:
        print(f'Getting {acc.get("name")} tokens')
        logging.warning(f'Getting {acc.get("name")} tokens')

        if acc.get('network') is not None and acc.get('network') != '':
            if acc.get('network') == "ETH":
                balance_df = get_eth_erc20_balance(acc.get('PublicAddress'), etherscan_token, acc.get('name'))
                prices = get_token_prices(balance_df, FromDate, ToDate, currency)

            if acc.get('network') == "BSC":
                balance_df = get_bsc_bep20_balance(acc.get('PublicAddress'), bscscantoken, acc.get('name'))
                prices = get_token_prices(balance_df, FromDate, ToDate, currency)

            if acc.get('network') == "ADA":
                balance_df = get_cardano_balance(acc.get('PublicAddress'), acc.get('delegate'))
                prices = get_token_prices(balance_df, FromDate, ToDate, currency)

            if acc.get('network') == "TRX":
                balance_df = get_tron_wallet_balance(acc.get('PublicAddress'), acc.get('name'))
                prices = get_token_prices(balance_df, FromDate, ToDate, currency)

        elif acc.get('network') is None or acc.get('network') == '':
            if acc.get('name') == "Binance":
                balance_df = get_binance_balance(acc.get('credentials').get('token'),
                                                 acc.get('credentials').get('secret'),
                                                 acc.get('name'))
                prices = get_binance_prices(list(balance_df.index), acc.get('credentials').get('token'),
                                            acc.get('credentials').get('secret'), FromDate, ToDate, currency)

            elif acc.get('name') == "Crypto.com Exchange":
                balance_df = get_crypto_exchange_balance(acc.get('credentials').get('token'),
                                                         acc.get('credentials').get('secret'),
                                                         acc.get('name'))
                prices = get_cryptodotcom_prices(balancedf=balance_df, todate=ToDate, currency=currency)

            elif acc.get('name') == "Crypto.com App":
                balance_df = get_crypto_app_balance(acc.get('name'))
                prices = get_cryptodotcom_prices(balancedf=balance_df, todate=ToDate, currency=currency)

            elif acc.get('name') == "Coinbase":
                balance_df = get_coinbase_balance(acc.get('credentials').get('token'),
                                                  acc.get('credentials').get('secret'),
                                                  acc.get('name'))
                prices = get_coinbase_prices(balance=balance_df, fromdate=FromDate, todate=ToDate,
                                             currency=currency)

        history_dict = updated_history_dict(history_dict, acc, prices)

    pl_totale = pd.Series(dtype=float)
    total_balance = pd.Series(dtype=float)
    for keyt, keyn in zip(['open', 'close', 'high', 'low'], ['Open', 'Close', 'High', 'Low']):
        total_df_1 = pd.DataFrame()
        colname = list()
        for acco in history_dict['byAccount'].keys():
            temp_df_loop = pd.DataFrame()
            for coin_loop in history_dict['byAccount'][acco]['price'].keys():
                colname.append(acco + "-" + coin_loop)
                if now_timestamp not in history_dict['byAccount'][acco]['balance'].columns:
                    quantity = 0
                    temp_df_loop = pd.concat(
                        [temp_df_loop, history_dict['byAccount'][acco]['price'][coin_loop][keyn] * quantity], axis=1)
                else:
                    quantity = pd.DataFrame(history_dict['byAccount'][acco]['balance'][now_timestamp]).loc[
                        coin_loop, now_timestamp]
                    temp_df_loop = pd.concat(
                        [temp_df_loop, history_dict['byAccount'][acco]['price'][coin_loop][keyn] * quantity], axis=1)

            temp_df_loop.columns = history_dict['byAccount'][acco]['price'].keys()
            temp_df_loop.replace(0, np.nan, inplace=True)
            temp_df_loop.fillna(method='bfill', axis=0, inplace=True)
            temp_df_loop.loc[:, temp_df_loop.isna().all()] = temp_df_loop.loc[:, temp_df_loop.isna().all()].replace(
                np.nan, 0)
            temp_df_loop.dropna(axis=0, inplace=True)

            if keyt == 'close':
                pl_totale = pl_totale.append(temp_df_loop.loc[temp_df_loop.last_valid_index(), :])
                if now_timestamp not in history_dict['byAccount'][acco]['balance'].columns:
                    zero_temp = history_dict['byAccount'][acco]['balance']
                    zero_temp[now_timestamp] = [0] * zero_temp.shape[0]
                    total_balance = total_balance.append(zero_temp[now_timestamp])
                else:
                    total_balance = total_balance.append(history_dict['byAccount'][acco]['balance'][now_timestamp])

            if history_dict['byAccount'][acco][keyt].shape == (0, 0):
                history_dict['byAccount'][acco][keyt] = temp_df_loop
            else:
                history_dict['byAccount'][acco][keyt] = history_dict['byAccount'][acco][keyt].append(temp_df_loop)
            history_dict['byAccount'][acco][keyt].fillna(0, inplace=True)

            total_df_1 = total_df_1.join(history_dict['byAccount'][acco][keyt], how="outer", lsuffix="L", rsuffix="R")
            total_df_1.fillna(method='bfill', axis=0, inplace=True)
            total_df_1.fillna(method='ffill', axis=0, inplace=True)
            total_df_1 = total_df_1[~total_df_1.index.duplicated(keep='first')]
        total_df_1.columns = colname
        if history_dict['total'][keyt].shape == (0, 0):
            history_dict['total'][keyt] = total_df_1.sum(axis=1)
        else:
            history_dict['total'][keyt] = pd.DataFrame(history_dict['total'][keyt]).join(
                pd.DataFrame(total_df_1.sum(axis=1)),
                how="outer", lsuffix="L", rsuffix="R")
        history_dict['total'][keyt].fillna(method='bfill', axis=0, inplace=True)
        history_dict['total'][keyt].fillna(method='ffill', axis=0, inplace=True)
        if 0 in history_dict['total'][keyt].index:
            history_dict['total'][keyt].drop(0, axis=0, inplace=True)

    if history_dict['total']['pltotale'].shape == (0, 0):
        history_dict['total']['pltotale'] = pd.DataFrame(pl_totale.groupby(pl_totale.index).sum(),
                                                         columns=[now_timestamp])
        history_dict['total']['totalbalance'] = pd.DataFrame(total_balance.groupby(total_balance.index).sum(),
                                                             columns=[now_timestamp])
    else:
        cols = list(history_dict['total']['pltotale'].columns)
        cols.append(now_timestamp)
        pl_totale.fillna(0, inplace=True)
        pl_totale = history_dict['total']['pltotale'].join(pd.DataFrame(pl_totale.groupby(pl_totale.index).sum(),
                                                                        columns=[now_timestamp]), how="outer",
                                                           lsuffix="L",
                                                           rsuffix="R")
        pl_totale.columns = cols
        history_dict['total']['pltotale'] = pl_totale

        cols = list(history_dict['total']['totalbalance'].columns)
        cols.append(now_timestamp)
        total_balance.fillna(0, inplace=True)
        total_balance = history_dict['total']['totalbalance'].join(
            pd.DataFrame(total_balance.groupby(total_balance.index).sum(
            ), columns=[now_timestamp]), how="outer", lsuffix="L", rsuffix="R")
        total_balance.columns = cols
        history_dict['total']['totalbalance'] = total_balance

    return history_dict


def get_latest_tokens_price(tokens, cmckey, currency="USD"):
    """OBSOLETE - REQUIRES COINMARKETCAP API KEY"""
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {"symbol": ",".join(tokens), "convert": "USD", "skip_invalid": "true"}
    headers = {'Accepts': 'application/json',
               'X-CMC_PRO_API_KEY': cmckey}

    price = requests.get(url, params=parameters, headers=headers)
    if price.status_code in [400, 401]:
        print("ERROR: " + json.loads(price.content).get('status').get('error_message'))
        logging.warning(
            f'ERROR - {json.loads(price.content).get("status").get("error_message")}'
            f' getting price')
        sys.exit("ERROR: " + json.loads(price.content).get('status').get('error_message'))
    price = json.loads(price.content).get('data')
    contract1 = [price.get(r).get('platform') for r in list(price.keys())]
    contract = []
    for cont in contract1:
        try:
            contract.append(cont.get('token_address'))
        except ValueError:
            contract.append(0)

    symb = [price.get(r).get('symbol').upper() for r in list(price.keys())]

    price = [price.get(r).get('quote').get("USD").get('price') for r in list(price.keys())]
    price = pd.Series(price, symb)

    poocoin = price.where(price == 1.000000e-08, 0)
    poocoins = list(poocoin[poocoin > 0].index)
    if len(poocoins) > 0:
        print("Tokens worth less than 10e-08 USD found, getting data from PancakeSwap")
        poo = [str(contract[x]) for x in range(len(symb)) if symb[x] in poocoins]
        poo = ['0xacFC95585D80Ab62f67A14C566C1b7a49Fe91167' if x == '0x389999216860ab8e0175387a0c90e5c52522c945' else x
               for x in poo]
        pooresp = [requests.get(f'https://api.pancakeswap.info/api/v2/tokens/{token}') for token in poo]
        poosymb = [json.loads(pooresp[x].content).get('data').get('symbol') for x in range(len(pooresp)) if
                   pooresp[x].status_code == 200]
        poosval = [float(json.loads(pooresp[x].content).get('data').get('price')) for x in range(len(pooresp)) if
                   pooresp[x].status_code == 200]
        price = price.where(price != 1.000000e-08, 0)
        price = price[price != 0]
        pooprice = pd.Series(poosval, poosymb)
        price = pd.concat([price, pooprice])

    if currency != "USD":
        g = CurrencyRates()
        conv = g.get_rate('USD', currency)
        price *= conv

    price.index = [x.upper() for x in price.index]
    return price
