#!/usr/bin/python

# Buttcoin Buzzword Bingo Bot. Bleep bloop.

import praw
import time
import json

import anti-abuse

BOTNAME = 'Buttcoin Buzzword Bingo Bot'
MIN_MATCHES = 6

# Retrieve Heroku information.
login_info = [os.environ['REDDIT_USERNAME'], os.environ['REDDIT_PASSWORD']]

# 1. Make no more than thirty requests per minute.
# 2. Change your client's User-Agent string to something descriptive
# 3. Don't hit the same page more than once per 30 seconds.
# 4. Requests for multiple resources at once rather than single in a loop

# Check bottiquette robots.txt list to make sure I'm allowed, beep boop.
bottiquette = r.get_wiki_page('Bottiquette', 'robots_txt_json')
bans = json.loads(bottiquette.content_md)

basewords = [
    'bitcoin', 'BTC', 'Core', 'litecoin', 'LTC', 'bitcoin cash', 'penis',
    'Bcash', 'BCash', 'BCH', 'monero', 'XMR', 'tether', 'USDT', 'EURT',
    'zcash', 'ZCash', 'ZEC', 'nano', 'NANO', 'neo', 'stellar', 'XLM', 'dash',
    'ripple', 'XRP', 'EOS', 'tron', 'TRX', 'zcoin', 'ZCoin', 'XZC',
    'dogecoin', 'DOGE', 'ethereum', 'ETH', 'ERC20', 'IOTA', 'Iota', 'tangle',
    'binance', 'ATH', 'trezor', 'coinbase', 'kucoin', 'KuCoin', 'gemini',
    'kraken', 'bisq', 'vechain', 'walton', 'bitconnect', 'bitrent', 'SFYL',
    'bittrex', 'bitstamp', 'bitgrail', 'gdax', 'GDAX', 'Gdax', 'bitpay', 
    'Vitalik', 'Buterin', 'Satoshi', 'Nakamoto', 'Roger Ver', 'CryptoDad',
    'Craig Wright', 'Morgan Rockwell', 'Jihan Wu', 'Winklevoss', 'Giancarlo',
    'wallet', 'mining', 'miner', 'bitminer', 'batching', 'blocksize',
    'mempool', 'fiat', 'digital gold', 'Digital Gold', 'bitmain', 'dapp',
    'hash rate', 'hashrate', 'initial coin offering', 'ICO', 'exchange',
    'FOMO', 'FUD', 'hodl', 'hodling', 'hodler', 'lambo', 'the moon', 'adoption',
    'blockchain', 'pump and dump', 'pump & dump', 'pumpndump', 'node', 'PoW',
    'POW', 'proof of work', 'PoS', 'POS', 'proof of stake', 'permissionless',
    'public permissioned', 'immutable', 'altcoin', 'shitcoin', 'segwit',
    'SegWit', 'segregated witness', 'lightning network', 'double-spend',
    'double spend', 'double spending', 'ASIC', 'LN', 'cypherpunk',
    'crypto', 'cryptocurrency', 'shill', 'shilling', 'token', 'airdrop',
    'decentralized', 'white paper', 'whitepaper', 'sybil attack', 'electrum',
    'distributed ledger', 'DLT', 'DAG', 'feeless', 'buy the dip', 'bitcore',
    'buying dips', 'Crypto Kittens', '$100%', 'faucet', 'smart contract',
    'this is good for', '1 BTC = 1 BTC', 'maximalist', 'store of value',
    
    ]

# Initialize PRAW with custom User-Agent.
r = praw.Reddit(BOTNAME)

# Build a set of buzzwords.
buzzwords = set()
buzzwords_found = set()

for word in basewords:
    buzzwords.add(word)
    buzzwords.add(word + 's')
    word = word[:1].upper() + word[1:]
    buzzwords.add(word)
    buzzwords.add(word + 's')

# Retrieve /r/buttcoin posts, make sure we're being polite.
comments = r.get_comments('buttcoin')
if is_summon_chain(post) or comment_limit_reached(post) or is_already_done(post):
    print "Limits reached, aborting."
    return

# Look for buzzword matches in the post.
for comment in comments:
    body = comment.body.lower()
    body = body.split() # ???

    # Search for buzzwords.
    for word in buzzwords:
        if word in body:
            #print "found"
            buzzwords_found.add(word)

    if len(buzzwords_found) >= MIN_MATCHES:
        print len(buzzwords_found)
        for word in buzzwords_found:
            print word
