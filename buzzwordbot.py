# I'm the Buttcoin Buzzword Bingo Bot. Bleep bloop!

import os
import time

import praw

# Settings. TODO move to cfg file.
DEBUG = False
AUTHOR = 'BarcaloungerJockey'
BOTNAME = 'Buttcoin Buzzword Bingo Bot *by /u/' + AUTHOR +')'
SUBREDDIT = 'testingground4bots'
#SUBREDDIT = 'buttcoin'
TRIGGER = '!BuzzwordBingo'
MIN_MATCHES = 6
DEFAULT_MATCHES = 8

# Retrieve OAuth information. TODO OAth to envs.
USERNAME = os.environ['REDDIT_USERNAME']
PASSWORD = os.environ['REDDIT_PASSWORD']
#CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_ID = '-QiIrl-1_LVKog'
#CLIENT_SECRET = os.environ['CLIENT_SECRET']
if DEBUG:
    print ('Username/pass: ' + USERNAME, PASSWORD)
    print ('Client ID/pass: ' + CLIENT_ID, CLIENT_SECRET)

# TODO: Move words and phrases to files.
basewords = [
    'Bitcoin', 'BTC', 'Core', 'Litecoin', 'LTC', 'Penis', 'Zencash', 'BCash',
    'BCH', 'Monero', 'XMR', 'Tether', 'USDT', 'EURT', 'ZCash', 'ZEC', 'Nano',
    'Neo', 'Stellar', 'XLM', 'Dash', 'Ripple', 'XRP', 'EOS', 'Tron', 'TRX',
    'Zcoin', 'XZC', 'Dogecoin', 'DOGE', 'Ethereum', 'ETH', 'ERC20', 'IOTA',
    'tangle', 'Binance', 'ATH', 'Trezor', 'Coinbase', 'KuCoin', 'Gemini',
    'Kraken', 'Bisq', 'Vechain', 'VEN', 'Walton', 'WTC', 'Bitconnect',
    'Bitrent', 'SFYL', 'Cardano', 'ADA', 'Bittrex', 'Bitstamp', 'Bitgrail',
    'GDax', 'Bitpay', 'Viacoin', 'Casper', 'shard', 'sharding', 'Vitalik',
    'Buterin', 'Satoshi', 'Nakamoto', 'CryptoDad', 'Winklevoss', 'Coindesk',
    'Giancarlo', 'wallet', 'mining', 'miner', 'bitminer', 'batching', 'KYC',
    'hashcash', 'candlestick', 'fomo\'d', 'premined', 'premining', 'DYOR',
    'blocksize', 'mempool', 'fiat', 'bitmain', 'dapp', 'ICO', 'exchange',
    'hashrate', 'fomo', 'fud', 'hodl', 'hodling', 'hodler', 'Raiblock',
    'Lambo', 'adoption', 'scam', 'scammer', 'funbux', 'butter', 'nocoiner',
    'blockchain', 'node', 'PoW', 'PoS', 'permissionless', 'immutable',
    'altcoin', 'shitcoin', 'SegWit', 'double-spend', 'ASIC', 'LN', 'cypherpunk',
    'crypto', 'cryptocurrency', 'cryptocurrencies', 'shill', 'shilling',
    'token', 'airdrop', 'decentralized', 'whitepaper', 'Electrum', 'DLT', 'DAG',
    'feeless', 'bitcore', 'maximalist', 'faucet', 'Coincheck', 'deflationary',
    'libertarian', 'ancap', 'trustless', 'trustlessly', 'mewn', 'cryptospace',
    'request', 'req', 'solidity', 'Etherscan', 'MtGox', 'whale', 'statist',
    'Gox', 'Karpeles', 'SegWit2x', 'Davor', 'Davorcoin', 'bubble',
    'Lamborghini', 'decentralizing', 'SAFT', 'KodakCoin', 'blockfolio',
    'magicbeans', 'stablecoin', 'oyster', 'pearl', 'PRL', 'dinero', 'fuding',
    'fomoing', 'curl', 'goxxed', 'wagecuck', 'debtslave', 'Blockfolio',
    'Robinhood'
    ]

basephrases = [
    'Bitcoin Cash', 'Bitcoin Core', 'buying dips', 'Crypto Kittens',
    'smart contract', 'this is good for', '1 BTC = 1 BTC', 'store of value',
    'distributed ledger', 'white paper', 'Sybil attack', 'double spending',
    'Lightning Network', 'public permissioned', 'Segregated Witness',
    'pump and dump', 'pump & dump', 'pumpndump', 'Proof of Work',
    'Proof of Stake', 'hash rate', 'the moon', 'Initial Coin Offering',
    'Roger Ver', 'Craig Wright', 'Morgan Rockwell', 'Mark Karpeles',
    'Jihan Wu', 'Digital Gold', 'double spend', 'buy the dip', 'digital money',
    'genesis address', 'genesis block', 'exchange targeted',
    'targeted by hackers', 'theft of', 'exit scam', 'cyber heist',
    'strong hand', 'weak hand', 'highly secure', 'Mt. Gox',
    'captain of industry', 'captains of industry', 'Austrian school',
    'Federal Reserve', 'wealth transfer', 'trading bot', 'bag holder',
    'bag holding', 'holding the bag', 'token contract', 'Comedy Gold',
    'Gavin Anderson', 'until you sell', 'Litecoin Cash', 'Monero Gold',
    'magic beans', 'Winklevoss twins', 'private key', 'public key', 'alt coin',
    'shit coin', 'stable coin', 'arb bot', 'sorry for your loss', 'new tech',
    'store of value', 'transaction fees', 'Greater Fool Theory', 'wage cuck',
    'zero sum game', 'zero-sum game', 'debt slave', 'debt slavery',
    'under a bridge', 'Davor Coin', 'ponzi scheme'
    ]

def postReply (matches, won):
    sig = (
        "\n_____\n\n^(I'm a hand-run baby bot, *bleep* *bloop* "
        "| Send love, rage or doge to /u/" + AUTHOR +", *beep*)"
        )

    if won:
        reply = '**Bingo**! We have a winner with *' + str(len(matches)) + '* squares found!!\n\n**Buzzwords**: '
        reply += ', '.join(matches)
    else:
        reply = 'Sorry, no winner this time. Convert more filty fiat to buttcoins to play again'
    return (reply + sig)

def alreadyReplied (comment):
    comment.refresh()
    replies = comment.replies
    for reply in replies:
        comment = r.comment(reply)
        if (comment.author == USERNAME):
            print (comment, comment.author)
            print ("Replied already, movin' on")
            return True
    print ("Haven't replied, yay!")
    return False

def playBingo (comment):
    # Check we haven't replied already.
    if alreadyReplied(comment):
        return

    # Retrieve parent comment or original crosspost.
    parent = comment.parent()
    try:
        text = parent.crosspost_parent_list[0]['selftext']
    except AttributeError:
        text = parent.selftext
    words = text.lower().split()

    # First seatch for buzzphrases.
    for phrase in buzzphrases:
        if phrase in text:
            matches_found.add(phrase)

    # Search for buzzwords that do not match phrases found.
    matched = ' '.join(match.lower() for match in matches_found)
    for word in buzzwords:
        if word.lower() in words and word.lower() not in matched:
            matches_found.add(word)

    # Remove plural duplicates.
    matches = matches_found.copy()
    for word in matches:
        matches_found.discard(word + 's')

    # Post reply to comment then wait out RATELIMIT.
    reply = postReply(matches_found, (len(matches_found) >= MIN_MATCHES))
    try:
        if DEBUG:
            print (reply)
        else:
            comment.reply(reply)
            time.sleep(600)
    except praw.exceptions.APIException as err:
        print(err)

# Build sets of words, phrases.
matches_found = set()
buzzwords = set()
buzzphrases = set()

for word in basewords:
    buzzwords.add(word)
    buzzwords.add(word + 's')

for phrase in basephrases:
    buzzphrases.add(phrase)

# Initialize PRAW with custom User-Agent.
if DEBUG:
    print("Authenticating...")
r = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    password=PASSWORD,
    user_agent=BOTNAME,
    username=USERNAME)
if DEBUG:
    print ('Authenticated as: ' + format(r.user.me()))

# 1. Don't reply to the same request more than once.
# 2. Don't hit the same page more than once per 30 seconds.
# 3. Requests for multiple resources at once rather than single in a loop.

sub = r.subreddit(SUBREDDIT).new()
for submission in sub:
    if DEBUG:
        print('Post: ' + format(submission))
    post = r.submission(submission)

    for comment in post.comments:
        if (comment.author != AUTHOR):
            print (AUTHOR + " didn't post it, skipping")
            break 
        comment.refresh()
        replies = comment.replies
        for reply in replies:
            subcomment = r.comment(reply)
            print (subcomment.body)
            if (TRIGGER in subcomment.body):
                print ("Reply - Time to play!")
                playBingo(subcomment)
        if (TRIGGER in comment.body):
            print ("Comment - Time to play!")
            playBingo(comment)
