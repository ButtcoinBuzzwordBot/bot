# I'm the Buttcoin Buzzword Bingo Bot. Bleep bloop!
# TODO: Keep track of already played comments, no repeats.

import os
import time
import re
import string
import pickle
import urllib

# Packages must be installed.
import bs4
import praw

# Settings. When DEBUG is True the bot will only reply to posts by AUTHOR.
# Modify these to customize the bot, along with the words and phrases files.
# By default the AUTHOR can compete but highscores will not be registered, to
# keep the game fair.
DEBUG = True
AUTHOR = 'BarcaloungerJockey'
COMPETE = False
BOTNAME = 'python:buzzword.bingo.bot:v1.1 (by /u/' + AUTHOR +')'
SUBREDDIT = 'buttcoin'
WORDFILE = 'words.txt'
PHRASEFILE = 'phrases.txt'
MIN_MATCHES = 4
MAX_MATCHES = 12

# Reddit account and API OAuth information. You can hardcode values here but
# it creates a security risk if your code is public (on Github, etc.)
# Otherwise, set the environment variables on your host as below.
USERNAME = os.environ['REDDIT_USERNAME']
PASSWORD = os.environ['REDDIT_PASSWORD']
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

# Ratelimit starts at 10 minutes per reply for a bot account w/no karma.
# Drops quickly as karma increases, can go down to 30 seconds minimum.
RATELIMIT = 30

# Triggers which active the bot to reply to a comment.
TRIGGER = '!BuzzwordBingo'
CMD_HS = TRIGGER + ' highscores'
CMD_SCORE = TRIGGER + ' score'
#TODO: remove CMD_URL = TRIGGER + ' http'

# Current scores and highscores.
SCOREFILE = 'score.txt'
HIGHSCOREFILE = 'highscores.txt'
MAX_HIGHSCORES = 5

# Signature for all replies.
sig = (
    '\n_____\n\n^(I\'m a hand-run bot, *bleep* *bloop* '
    '| Send love, rage or doge to /u/' + AUTHOR + ', *beep*)'
)

# Highscore report reply.
HIGHSCORES_REPLY = (
    '**' + SUBREDDIT.title() + ' Buzzword Bingo Highscores**\n_____\n\n'
)

# Winner reply.
def winnerReply (matches):
    return(
        '**Bingo**! We have a winner with *' + len(matches) +
        '* matches found!!\n\n**Buzzwords**: ' + ', '.join(matches)
    )

def loserReply(score):
    return (
        'Sorry bro, your hands are weak. Current score to win is **' +
        str(score) + '** or more matches. Convert more filty fiat to '
        'mine for comedy gold again.'
    )

# END OF SETTINGS.

if DEBUG:
    SUBREDDIT = 'testingground4bots'
    print ('Username/pass: ' + USERNAME, PASSWORD)
    print ('Client ID/pass: ' + CLIENT_ID, CLIENT_SECRET)

# Read words and phrases, build sets of each.
buzzwords = set()
buzzphrases = set()

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

# Create score file with min. value if doesn't exist.
MATCHES = MIN_MATCHES
scoref = open(SCOREFILE, 'r')
try:
    MATCHES = int(scoref.readline())
except ValueError (err):
    scoref = open(SCOREFILE, 'w')
    scoref.write(str(MATCHES))
scoref.close()

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

# Sort scores from high to low.
highscores.sort(key = lambda x: x[0], reverse = True)
if DEBUG:
    for score, name in highscores:
        print('Name: ' + name + ' got ' + str(score))

#
# Highscores
#

# Check for a new highscore. Replace lowest since they're always sorted.
def updateHighscores (score, name):
    global highscores, AUTHOR, COMPETE, MAX_HIGHSCORES

    # Don't score the author for testing or no compete flag.
    if (name == AUTHOR) and not COMPETE:
        return

    if len(highscores) < MAX_HIGHSCORES:
        highscores.append([score, '/u/' + name])
    elif score > highscores[MAX_HIGHSCORES - 1][0]:
        # Check for duplicate entries.
        highscores[MAX_HIGHSCORES - 1] = [score, '/u/' + name]

    # Resort high to low and save.
    highscores.sort(key = lambda x: x[0], reverse = True)
    with open(HIGHSCOREFILE, 'wb') as f:
        pickle.dump(highscores, f)
    f.close()

# Retrieve highscores for reply.
def getHighscores(comment):
    global HIGHSCORE_REPLY, highscores

    if alreadyReplied(comment):
        return

    count = 1
    for score, name in highscores:
        reply += str(count) + '. ' + name + ': ' + str(score) + '\n'
        count += 1
    postReply(comment, HIGHSCORE_REPLY)

#
# Replies
#

# Check to see if a comment has been replied to already to avoid duplicates.
def alreadyReplied (comment):
    global USERNAME

    replies = comment.replies
    for reply in replies:
        if (r.comment(reply).author.name == USERNAME):
            if DEBUG:
                print ("Replied already, movin' on.")
            return True
    return False

# Creates a standard reply for wins/losses, and updates minimum score required.
def getReply (matches):
    global MATCHES

    if score >= MATCHES:
        reply = winnerReply(matches)
    else:
        reply = loserReply(MATCHES)

    # Raise or lower the current score to win accordingly.
    if len(matches) > MATCHES:
        if MATCHES < MAX_MATCHES:
            MATCHES += 1
    else:
        if MATCHES > MIN_MATCHES:
            MATCHES -= 1

    # Be lazy and always write, changed or not.
    scoref = open(SCOREFILE, 'w')
    scoref.write(str(MATCHES))
    scoref.close()
    return (reply)

def weHateRobots():
    return ('*borp*, I did my best, but that website doesn\'t allow robots. *blap*')

def postReply (comment, reply):
    global RATELIMIT, sig

    if DEBUG:
        print (reply)
    else:
        print ('X', end='')

    try:
        comment.reply(reply + sig)
        time.sleep(RATELIMIT)
    except praw.exceptions.APIException as err:
        print(err)

#
# Bingo.
#

def getMatches(text):
    global buzzwords, buzzphrases, MATCHES
    matches_found = set()

    # Remove all punctuation from words, and convert dashes to spaces for
    # phrases.
    text = text.replace('\'-/', ' ').lower()
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    words = regex.sub('', text).split()

    # First seatch for buzzphrases.
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
    return (matches_found)

# Check if we've already replied, score text and reply.
def playBingo (comment, text):

    # Check we haven't replied already.
    if alreadyReplied(comment):
        return
    matches_found = getMatches(text)

    # Check highscores. Post reply to comment then wait out RATELIMIT.
    updateHighscores(len(matches_found), comment.author.name)
    reply = getReply(matches_found)
    postReply(comment, reply)

#
# Comments.
#

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
            #url = parent.url
            #print('parent.url=' + url)
            # TODO: Retrieve reddit links
            #if re.match(r'http.*(redd.it|reddit.com)/.*', url):
            #    regex = re.compile('^http.*/comments/([^/]+).*$')
            #    linked = regex.search(url).group(1)
            #    print('linked comment: ' + linked)
            #    post = r.submission(linked)

            #with urllib.request.urlopen(url) as response:
            #    text = response.read()
            #print(text)
            exit()
        except AttributeError:
            print ('ERROR: Not implemented yet.')
    return(text)

# Check a comment or post for the invocation keyword.
def checkComment (comment):
    global MATCHES
    
    if DEBUG:
        print('comment: ' + format(comment))
    else:
        print('.', end='', flush=True)
    comment.refresh()
    replies = comment.replies

    # Traverse comment forest (trees.)
    for reply in replies:
        subcomment = r.comment(reply)
        subcomment.refresh()
        checkComment(subcomment)

    # Process various triggers if found in comment.
    if (CMD_HS in comment.body):
        getHighscores(comment)

    elif (CMD_URL in comment.body):
        # TODO: Remove this command, move code to scrape pages from title link.
        regex = re.compile(TRIGGER + '\s+(http[s]*://[^\s]+)')
        url = regex.search(comment.body).group(1)
        if url is not None:
            #print(url)
            try:
                with urllib.request.urlopen(url) as response:
                    html = response.read()
                soup = bs4.BeautifulSoup(html, 'html.parser')
                ignore_tags = ['style', 'script', '[document]', 'head', 'title']
                [s.extract() for s in soup(ignore_tags)]
                playBingo(comment, 'this function is off for now, *beep*' + sig)
            except urllib.error.HTTPError:
                postReply(comment, weHateRobots())

    elif (TRIGGER in comment.body):
        if CMD_SCORE in comment.body:
            regex = re.compile(CMD_SCORE + '\s+([0-9]+)\s*')
            tempscore = regex.search(comment.body).group(1)
            if tempscore is not None:
                print('tempscore: ' + tempscore)
                MATCHES = int(tempscore)

        comment.refresh()
        parent = comment.parent()
        # Do not allow player to score their own post, unless it's testing.
        if not (comment.author == parent.author and
                comment.author.name != AUTHOR):
            playBingo(comment, getText(parent))

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
    username=USERNAME
)
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
