# I'm the Buttcoin Buzzword Bingo Bot. Bleep bloop!
# TODO: Figure out Dogecoin or something useless to award monthly winners.
# TODO: mysql, memcache support
# TODO: link to the posts that generated the winning scores
#  Use format like: https://redd.it/87fwu1
# TODO: Add "already played" message? When parent replied, check replies?
# TODO: Randomize win/loss comments and insults?
# FIX: not scoring original post, only replies?
#
# TODO NOW: consolidate new/update/writeHighscores(). Should be new/read/write.

import sys
import getopt
import os
import time
import string
import re

# Packages must be installed.
import bs4
import praw
import urllib

import datastore as ds
import scoring as scr
import comments as cmt
import cmdline

#
# SETTINGS.
#

# When DEBUG is True the bot will only reply to posts by AUTHOR. Modify these
# to customize the bot, along with the words and phrases files. By default the
# AUTHOR can compete but highscores will not be registered, to keep the game
# fair

DEBUG = True
AUTHOR = "BarcaloungerJockey"
COMPETE = False
BOTNAME = "python:buzzword.bingo.bot:v1.1 (by /u/" + AUTHOR +")"
REDDIT = "https://redd.it/"
SUBREDDIT = "buttcoin"
MIN_MATCHES = 4
MAX_MATCHES = 12

SCORE_STORE = "score"
WORD_STORE = "words"
PHRASE_STORE = "phrases"
KOAN_STORE = "koans"
HAIKU_STORE = "haiku"

# If HOSTED is True the script continues looping. Set appropriate storage type and
# info based on your hosting options.
HOSTED = False
STORE_TYPE = "sqlite"
#STORE_TYPE = "file"
#STORE_TYPE = "mysql"
#MYSQL_USER = "user"
#MYSQL_PW = "password"
#MYSQL_HOST = "127.0.0.1"

# Reddit account and API OAuth information. You can hardcode values here but
# it creates a security risk if your code is public (on Github, etc.)
# Otherwise, set the environment variables on your host as below.
USERNAME = os.environ['REDDIT_USERNAME']
PASSWORD = os.environ['REDDIT_PASSWORD']
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

# Start rate limit at 600 (10 minutes) per reply for a bot account w/no karma.
# Drops quickly as karma increases, can go down to 10 seconds minimum.
RATELIMIT = 10

# Triggers which active the bot to reply to a comment.
TRIGGER = "!BuzzwordBingo"
CMD_HS = TRIGGER + " highscores"
CMD_SCORE = TRIGGER + " score"
CMD_KOAN = TRIGGER + " koan"
CMD_HAIKU = TRIGGER + " haiku"

# Limit of scored comments saved to skip.
MAX_SCORED = 300
SCORED_STORE = "scored"

# Number of highscores.
MAX_HIGHSCORES = 5
HIGHSCORES_STORE = "highscores"

# Signature for all replies.
sig = (
    "\n_____\n\n^(I\'m a hand-run bot, *bleep* *bloop* "
    "| Send praise, rage or arcade game tokens to /u/" + AUTHOR + ", *beep*)"
)

# Highscore report reply.
def highscoresReply (highscores):
    reply = (
        "**" + SUBREDDIT.title() + " Buzzword Bingo Highscores**\n_____\n\n"
    )
        
    count = 1
    for score,name,url in highscores:
        reply += str(count) + ". " + name + ": " + str(score) + " (" + url + ")\n"
        count += 1
    return(reply)

# Winning reply.
def winnerReply (matches):
    return(
    "**Bingo**! We have a winner with *" + str(len(matches)) +
        "* matches found!!\n\n**Buzzwords**: " + ", ".join(matches)
    )

# Losing reply.
def loserReply(score):
    return (
        "Sorry bro, your hands are weak. Current score to win is **" +
        str(score) + "** or more matches. Convert more filty fiat to "
        "mine for comedy gold again."
    )

# Link to website blocked for robots.
def blockedReply(link):
    return (
        "No way, bro. Robots are blocked for: " + link
    )

# TODO: going to use this? Gotta make sure it's posted only once.
#ALREADY_SCORED = "Sorry, someone with stronger hands beat you to this one."

#
# END OF SETTINGS.
#

# Initialize PRAW with custom User-Agent.
if DEBUG:
    SUBREDDIT = "testingground4bots"
    print("Username/pass: " + USERNAME, PASSWORD)
    print("Client ID/pass: " + CLIENT_ID, CLIENT_SECRET)
    print("Authenticating...")
r = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    password=PASSWORD,
    user_agent=BOTNAME,
    username=USERNAME
)
if DEBUG: print("Authenticated as: " + format(r.user.me()))

dbexists = True
if STORE_TYPE is "file":
    import pickle
    store = "file"

elif STORE_TYPE is "sqlite":
    import sqlite3
    DATABASE = "buzzword.db"
    if not os.path.isfile(DATABASE):
        dbexists = False
    try:
        store = sqlite3.connect(DATABASE)
    except sqlite3.Error (err):
        print("ERROR: Cannot create or connect to " + DATABASE)
        exit()

elif STORE_TYPE is "mysql":
    # TODO: Why isn't this module being found?
    #import PyMySQL as mysql
    DATABASE = "buzzword"
    try:
        store = mysql.connector.connect(
            user=MYSQL_USER, password=MYSQL_PW, host=MYSQL_HOST, database=DATABASE)
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("Username or password error for " + DATABASE)
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            dbexists = False
        else:
            print(err)

else:
    print("Unknown store type. Valid settings are: file, sqlite, mysql.")
    exit()

if not dbexists:
    ds.createDB(store, STORE_TYPE, DATABASE, WORD_STORE, PHRASE_STORE,
                SCORED_STORE, SCORE_STORE, MIN_MATCHES, HIGHSCORES_STORE,
                KOAN_STORE, HAIKU_STORE)
    ds.writeHighscores(store, HIGHSCORES_STORE, scr.newHighscores(AUTHOR))
    print("Database created. Please import word/phrases before running.")
    exit()

#
# Bingo
#

def getMatches(text):
    """ Match words and phrases in text, return score. """

    global buzzwords, buzzphrases, MATCHES
    matches_found = set()

    # Remove all punctuation from words, and convert dashes to spaces for
    # phrases.
    text = text.replace("\'-/", " ").lower()
    regex = re.compile("[%s]" % re.escape(string.punctuation))
    words = regex.sub("", text).split()

    # First seatch for buzzphrases.
    for phrase in buzzphrases:
        if phrase.lower() in text:
            matches_found.add(phrase)

    # Search for buzzwords that do not match phrases found.
    matched = " ".join(match.lower() for match in matches_found)
    for word in buzzwords:
        if word.lower() in words and word.lower() not in matched:
            matches_found.add(word)

    # Remove plural duplicates.
    dupes = matches_found.copy()
    for word in dupes:
        matches_found.discard(word + "s")
    return (matches_found)

def playBingo (comment, text):
    """ Check if we've already replied, score text and reply. """

    global HIGHSCORES_STORE, MAX_HIGHSCORES, AUTHOR, COMPETE, REDDIT
    
    if len(text) == 0:
        return
    matches_found = getMatches(text)
    scr.updateHighscores(len(matches_found), comment, highscores)
    #scr.updateHighscores(len(matches_found), comment, highscores, HIGHSCORES_STORE,
    #                     MAX_HIGHSCORES, AUTHOR, COMPETE, REDDIT)
    reply = cmt.getReply(matches_found)
    cmt.postReply(comment, reply)

#
# MAIN
#

# Check for command line options.
if len(sys.argv) > 1:
    processOpts(sys.argv)

# Check bot inbox for messages.
msgs = list(r.inbox.unread(limit=None))
if len(msgs) > 0 and not HOSTED:
    print(str(len(msgs)) + " message(s) in /u/" + USERNAME + "\'s inbox.")
    print("Please read before running bot.")
    if len(msgs) > 12: exit()

# Read words and phrases, build sets of each.
buzzwords = set()
buzzphrases = set()

try:
    for word in ds.readData(store, WORD_STORE):
        buzzwords.add(word)
        buzzwords.add(word + "s")
except Exception as err:
    print(err)
    exit()

try:
    for phrase in ds.readData(store, PHRASE_STORE):
        buzzphrases.add(phrase)
except Exception:
    exit()

# Will create score file with min. value if doesn't exist.
MATCHES = ds.readScore(store, SCORE_STORE, MIN_MATCHES)

# Get comments already scored to prevent repeats and multiple plays.
already_scored = ds.readScored(store, SCORED_STORE)

# Load high scores. If file does not exist, create one.
highscores = ds.readHighscores(store, HIGHSCORES_STORE, AUTHOR)
highscores.sort(key = lambda x: x[0], reverse = True)
if DEBUG:
    for score, name, url in highscores:
        print("Name: " + name + " got " + str(score) + " (" + url + ")")

def main():
    """
    1. Don't reply to the same request more than once.
    2. Don't hit the same page more than once per 30 seconds.
    3. Request multiple resources at once rather than single in a loop.
    """

    while True:
        sub = r.subreddit(SUBREDDIT).new()
        for submission in sub:
            post = r.submission(submission)
            for comment in post.comments:
                if DEBUG and (comment.author != AUTHOR): break
                checkComment(comment)
            ds.writeScored(store, SCORED_STORE, MAX_SCORED, already_scored)
        if not HOSTED:
            break
    store.close()

if __name__ == '__main__':
    main()
