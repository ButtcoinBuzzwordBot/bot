# I'm the Buttcoin Buzzword Bingo Bot. Bleep bloop!

import os
import time
import re
import string
import pickle
#import requests

import praw

# Settings. When DEBUG is True bot will only reply to posts by AUTHOR.
DEBUG = False
AUTHOR = 'BarcaloungerJockey'
BOTNAME = 'python:buzzword.bingo.bot:v1.0 (by /u/' + AUTHOR +')'
SUBREDDIT = 'buttcoin'
TRIGGER = '!BuzzwordBingo'
# TODO: add commands after trigger, search for each
CMD_HS = TRIGGER + ' highscores'
CMD_SCORE = TRIGGER + ' score'
SCOREFILE = 'score.txt'
WORDFILE = 'words.txt'
PHRASEFILE = 'phrases.txt'
HIGHSCOREFILE = 'highscores.txt'
MAX_HIGHSCORES = 5
MIN_MATCHES = 4
MAX_MATCHES = 12
# Ratelimit starts at 10 minutes per reply for a bot account w/no karma.
# Drops quickly as karma increases, can go down to 30 seconds minimum.
RATELIMIT = 30

# Retrieve OAuth information.
USERNAME = os.environ['REDDIT_USERNAME']
PASSWORD = os.environ['REDDIT_PASSWORD']
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

if DEBUG:
    SUBREDDIT = 'testingground4bots'
    print ('Username/pass: ' + USERNAME, PASSWORD)
    print ('Client ID/pass: ' + CLIENT_ID, CLIENT_SECRET)

# Read words and phrases, build sets of each.
buzzwords = set()
buzzphrases = set()

# Get the current minimum score, keep file open to write new values.
scoref = open(SCOREFILE, 'r')
try:
    MATCHES = int(scoref.readline())
except ValueError (err):
    print('ERROR: ' + SCOREFILE + ' is empty or doesn\'t not exist.')
scoref.close()

# Read words and phrases, build sets for each.
wordsf = open(WORDFILE, 'r')
words  = wordsf.read().splitlines()
wordsf.close()
for word in words:
    buzzwords.add(word)
    buzzwords.add(word + 's')

phrasesf = open(PHRASEFILE, 'r')
phrases = phrasesf.read().splitlines()
phrasesf.close()
for phrase in phrases:
    buzzphrases.add(phrase)

# Load high scores. If file does not exist, create one.
highscores = []
if os.path.isfile(HIGHSCOREFILE):
    with open(HIGHSCOREFILE, 'rb') as f:
        highscores = pickle.load(f)
else:
    for i in range (0,3):
        highscores.append([i + 1, '/u/' + AUTHOR])
    with open(HIGHSCOREFILE, 'wb') as f:
        pickle.dump(highscores, f)
f.close()
highscores.sort(key = lambda x: x[0], reverse = True)
if DEBUG:
    for score, name in highscores:
        print('Name: ' + name + ' got ' + str(score))

# Signature for all replies.
sig = (
    "\n_____\n\n^(I'm a hand-run bot, *bleep* *bloop* "
    "| Send love, rage or doge to /u/" + AUTHOR + ", *beep*)"
)

#
# Highscores
#

# Check for a new highscore. Replace lowest since they're always sorted.
def updateHighscores (score, name):
    global highscores

    if len(highscores) < MAX_HIGHSCORES:
        highscores.append([score, '/u/' + name])
    elif score > highscores[MAX_HIGHSCORES - 1][0]:
        highscores[MAX_HIGHSCORES - 1] = [score, '/u/' + name]

    highscores.sort(key = lambda x: x[0], reverse = True)
    with open(HIGHSCOREFILE, 'wb') as f:
        pickle.dump(highscores, f)
    f.close()

# Retrieve highscores for reply.
def getHighscores(comment):
    global highscores, sig

    if alreadyReplied(comment):
        return

    reply = '**Buttcoin Buzzword Bingo Highscores**\n_____\n\n'
    count = 1
    for score, name in highscores:
        reply += str(count) + '. ' + name + ': ' + str(score) + '\n'
        count += 1
    postReply(comment, reply + sig)

#
# Replies
#

# Check to see if a comment has been replied to already to avoid duplicates.
def alreadyReplied (comment):
    replies = comment.replies
    for reply in replies:
        if (r.comment(reply).author.name == USERNAME):
            if DEBUG:
                print ("Replied already, movin' on.")
            return True
    if DEBUG:
        print ("Okay to reply.")
    return False

# Creates a standard reply for wins/losses, and updates minimum score required.
def getReply (matches, score):
    global MATCHES, sig

    if score >= MATCHES:
        reply = (
            '**Bingo**! We have a winner with *' + str(score) +
            '* squares found!!\n\n**Buzzwords**: ' + matches)
    else:
        reply = (
            'Sorry bro, your hands are weak. Current score to win is **' +
            str(MATCHES) + '** or more matches. Convert more filty fiat to '
            'mine for comedy gold again.')

    # Raise or lower the current score to win accordingly.
    if score > MATCHES:
        if MATCHES < MAX_MATCHES:
            MATCHES += 1
    else:
        if MATCHES > MIN_MATCHES:
            MATCHES -= 1

    # Be lazy and always write, changed or not.
    scoref = open(SCOREFILE, 'w')
    scoref.write(str(MATCHES))
    scoref.close()
    return (reply + sig)

def postReply (comment, reply):
    global RATELIMIT

    try:
        if DEBUG:
            print (reply)
        comment.reply(reply)
        time.sleep(RATELIMIT)
    except praw.exceptions.APIException as err:
        print(err)

#
# Comments.
#

# Check a comment or post for the invocation keyword.
def checkComment (comment):
    if DEBUG:
        print('comment: ' + format(comment))
    comment.refresh()
    print('.', end='', flush=True)
    replies = comment.replies
    for reply in replies:
        subcomment = r.comment(reply)
        subcomment.refresh()
        checkComment(subcomment)
    if (CMD_HS in comment.body):
        getHighscores(comment)
    elif (TRIGGER in comment.body):
        playBingo(comment)

# Retrieve text from a variety of possible sources: original or crosspost,
# relies themselves, and linked Reddit posts.
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
            except AttributeError:
                print ('ERROR: Unsupported or broken post reference.')
                
    if text is None or text is '':
        # Try to get text from linked post in title.
        try:
            url = parent.url
            #print('parent.url=' + url)
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

# Check if we're already replied, if not get the text and score matches.
def playBingo (comment):
    global buzzwords, buzzphrases, MATCHES

    # Check we haven't replied already.
    if alreadyReplied(comment):
        return
    if DEBUG:
        print('trigger: ' + format(comment))

    # Retrieve parent comment or original crosspost.
    comment.refresh()
    parent = comment.parent()
    text = getText(parent)

    if DEBUG:
        print('text to score: \'' + text + '\'\n\n')

    # Remove all punctuation from words, and convert dashes to spaces for
    # phrases.
    text = text.replace('\'-/', ' ').lower()
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    words = regex.sub('', text).split()

    # First seatch for buzzphrases.
    matches_found = set()
    for phrase in buzzphrases:
        if phrase.lower() in text:
            matches_found.add(phrase)

    # Search for buzzwords that do not match phrases found.
    matched = ' '.join(match.lower() for match in matches_found)
    for word in buzzwords:
        if word.lower() in words and word.lower() not in matched:
            matches_found.add(word)

    # Remove plural duplicates.
    dupes = matches_found.copy()
    for word in dupes:
        matches_found.discard(word + 's')

    if DEBUG:
        print (matches_found)

    # Check highscores. Post reply to comment then wait out RATELIMIT.
    updateHighscores(len(matches_found), comment.author.name)
    reply = getReply(', '.join(matches_found), len(matches_found))
    postReply(comment, reply)

#
# MAIN
#

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
