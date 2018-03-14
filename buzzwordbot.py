# I'm the Buttcoin Buzzword Bingo Bot. Bleep bloop!

import os
import time
import re
import string
import requests

import praw

# Settings. When DEBUG is True bot will only reply to posts by AUTHOR.
DEBUG = True
AUTHOR = 'BarcaloungerJockey'
BOTNAME = 'python:buzzword.bingo.bot:v0.3 (by /u/' + AUTHOR +')'
SUBREDDIT = 'buttcoin'
TRIGGER = '!BuzzwordBingo'
# TODO: make scores dynamic, increase on winning score, decrease on losing.
# Don't go above/below set min/max.
MIN_MATCHES = 6
MATCHES = 6
MAX_MATCHES = 20
# Ratelimit starts at 10 minutes per reply for a bot account w/no karma.
# Drops quickly as karma increases.
RATELIMIT = 120

# Retrieve OAuth information.
USERNAME = os.environ['REDDIT_USERNAME']
PASSWORD = os.environ['REDDIT_PASSWORD']
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

if DEBUG:
    SUBREDDIT = 'testingground4bots'
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
    'hashcash', 'candlestick', 'fomod', 'premined', 'premining', 'DYOR',
    'blocksize', 'mempool', 'fiat', 'bitmain', 'dapp', 'ICO', 'exchange',
    'hashrate', 'fomo', 'fud', 'hodl', 'hodling', 'hodler', 'Raiblock',
    'Lambo', 'adoption', 'scam', 'scammer', 'funbux', 'butter', 'nocoiner',
    'blockchain', 'node', 'PoW', 'PoS', 'permissionless', 'immutable', 'PoA',
    'altcoin', 'shitcoin', 'SegWit', 'ASIC', 'LN', 'cypherpunk',
    'crypto', 'cryptocurrency', 'cryptocurrencies', 'shill', 'shilling',
    'token', 'airdrop', 'decentralized', 'whitepaper', 'Electrum', 'DLT', 'DAG',
    'feeless', 'bitcore', 'maximalist', 'faucet', 'Coincheck', 'deflationary',
    'libertarian', 'ancap', 'trustless', 'trustlessly', 'mewn', 'cryptospace',
    'request', 'req', 'solidity', 'Etherscan', 'MtGox', 'whale', 'statist',
    'Gox', 'Karpeles', 'SegWit2x', 'Davor', 'Davorcoin', 'bubble', 'buttrex',
    'Lamborghini', 'decentralizing', 'SAFT', 'KodakCoin', 'blockfolio',
    'magicbeans', 'stablecoin', 'oyster', 'pearl', 'PRL', 'dinero', 'fuding',
    'fomoing', 'curl', 'goxxed', 'wagecuck', 'debtslave', 'Blockfolio', 'cult',
    'Robinhood', 'aidscoin', 'sodl', 'sodler', 'sodling', 'gas', 'plasmacash',
    'mainnet', 'testnet', 'BaaS', 'BIP70', 'P2P', 'lamboaire', 'silkroad',
    'cryptocoin', 'hyperbitcoinization', 'hyperdeflationary'
    ]

basephrases = [
    'Bitcoin Cash', 'Bitcoin Core', 'buying dips', 'Crypto Kittens',
    'smart contract', 'this is good for', '1 BTC = 1 BTC', 'store of value',
    'distributed ledger', 'white paper', 'Sybil attack', 'double spending',
    'Lightning Network', 'public permissioned', 'Segregated Witness',
    'pump and dump', 'pump & dump', 'pumpndump', 'Proof of Work', 'fun bux',
    'Proof of Stake', 'hash rate', 'the moon', 'Initial Coin Offering',
    'Roger Ver', 'Craig Wright', 'Morgan Rockwell', 'Mark Karpeles',
    'Jihan Wu', 'Digital Gold', 'double spend', 'buy the dip', 'digital money',
    'genesis address', 'genesis block', 'exchange targeted', 'aids coin',
    'targeted by hackers', 'theft of', 'exit scam', 'cyber heist',
    'strong hand', 'weak hand', 'highly secure', 'Mt. Gox', 'Silk Road',
    'captain of industry', 'captains of industry', 'Austrian school',
    'Federal Reserve', 'wealth transfer', 'trading bot', 'bag holder',
    'bag holding', 'holding the bag', 'token contract', 'Comedy Gold',
    'Gavin Anderson', 'until you sell', 'Litecoin Cash', 'Monero Gold',
    'magic beans', 'Winklevoss twins', 'private key', 'public key', 'alt coin',
    'shit coin', 'stable coin', 'arb bot', 'sorry for your loss', 'new tech',
    'store of value', 'transaction fees', 'Greater Fool Theory', 'wage cuck',
    'zero sum game', 'zero sum game', 'debt slave', 'debt slavery',
    'under a bridge', 'Davor Coin', 'ponzi scheme', 'plasma cash', 'main net',
    'Brock Pierce', 'test net', 'proof of authority', 'thor power',
    'blockchain as a service', 'pre sale', 'crowd sale', 'digital cash',
    'John McAfee', 'Calvin Ayre', 'arise chikun', 'top tier'
    ]

# TODO comment the subroutines
def postReply (matches, won):
    sig = (
        "\n_____\n\n^(I'm a hand-run baby bot, *bleep* *bloop* "
        "| Send love, rage or doge to /u/" + AUTHOR +", *beep*)"
        )

    if won:
        reply = '**Bingo**! We have a winner with *' + str(len(matches)) + '* squares found!!\n\n**Buzzwords**: '
        reply += ', '.join(matches)
    else:
        reply = 'Sorry, your hands are weak. Current score to win is ' + MATCHES + ' or more matches. Convert more filty fiat to buttcoins and try again to mine for comedy gold.'

    # TODO: raise or lower the current score to win on win/loss.
    return (reply + sig)

def alreadyReplied (comment):
    comment.refresh()
    replies = comment.replies
    for reply in replies:
        comment = r.comment(reply)
        if (comment.author == USERNAME):
            if DEBUG:
                print ("Replied already, movin' on.")
            return True
    if DEBUG:
        print ("Okay to reply.")
    return False

def checkComment (comment):
    if DEBUG:
        print('comment: ' + format(comment))
    comment.refresh()
    replies = comment.replies
    for reply in replies:
        subcomment = r.comment(reply)
        #if DEBUG:
        #    print ('reply: ' + format(reply))
        subcomment.refresh()
        checkComment(subcomment)
    if (TRIGGER in comment.body):
        playBingo(comment)

def getText (parent):
    # Try to get text from original post.
    try:
        text = parent.selftext
    except AttributeError:
        # Try to get body of a comment.
        try:
            text = parent.body
        except:
            # Try to get text from a crosspost. 
            try:
                text = parent.crosspost_parent_list[0]['selftext']
                print (1)
            except AttributeError:
                print ('ERROR: Unsupported or broken post reference.')
                
    if text is None or text is '':
        # Try to get text from linked post in title.
        try:
            url = parent.url
            print('parent.url=' + url)
            if re.match(r'http.*(redd.it|reddit.com)/.*', url):
                regex = re.compile('^http.*/comments/([^/]+).*$')
                linked = regex.search(url).group(1)
                #print('linked comment: ' + linked)
                post = r.submission(linked)
                #print('post: ' + format(post.body))
                #regex = re.compile('^http.*(/r/[^/]+).*$')
                #linksub = regex.search(url).group(1)
                #print ('linked sub: ' + linksub)
                #newsub = r.subreddit(linksub).new()
                #post = r.submission(newsub)
                #com2 = r.comment(newcom)
                text = post.body
                #next(iter(your_list or []), None)
                #print(text)
                exit
        except AttributeError:
            print ('ERROR: Not implemented yet.')
    return(text)

def playBingo (comment):
    # Check we haven't replied already.
    if alreadyReplied(comment):
        return
    if DEBUG:
        print('trigger: ' + format(comment))
        print('trigger text: ' + comment.body + '\n\n')

    # Retrieve parent comment or original crosspost.
    comment.refresh()
    parent = comment.parent()
    text = getText(parent)

    if DEBUG:
        #print(vars(parent))
        #print('parent: ' + format(parent))
        print('text to score: \'' + text + '\'\n\n')
        time.sleep (100)

    # Remove all punctuation from words, and convert dashes to spaces for
    # phrases.
    text = text.lower()
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    text = words.replace('\'-/', ' ')
    words = regex.sub('', text).split()

    # First seatch for buzzphrases.
    for phrase in buzzphrases:
        if phrase in text:
            matches_found.add('"' + phrase + '"')

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
    reply = postReply(matches_found, (len(matches_found) >= MATCHES))
    try:
        if DEBUG:
            print (reply)
        else:
            comment.reply(reply)
            time.sleep(RATELIMIT)
    except praw.exceptions.APIException as err:
        print(err)

#
# MAIN
#

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
# 3. Request multiple resources at once rather than single in a loop.

sub = r.subreddit(SUBREDDIT).new()
for submission in sub:
    post = r.submission(submission)

    for comment in post.comments:
        if DEBUG and (comment.author != AUTHOR):
            print (AUTHOR + " didn't post it, skipping.")
            break
        checkComment(comment)
