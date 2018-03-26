# I'm the Buttcoin Buzzword Bingo Bot. Bleep bloop!
# TODO: Figure out Dogecoin or something useless to award monthly winners.
# TODO: mysql, memcache support
# TODO: link to the posts that generated the winning scores
# TODO: Add "already played" message? When parent replied, check replies?
# TODO: Randomize win/loss comments and insults.

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

#
# SETTINGS.
#

# When DEBUG is True the bot will only reply to posts by AUTHOR. Modify these
# to customize the bot, along with the words and phrases files. By default the
# AUTHOR can compete but highscores will not be registered, to keep the game
# fair.

DEBUG = True
AUTHOR = "BarcaloungerJockey"
COMPETE = False
BOTNAME = "python:buzzword.bingo.bot:v1.1 (by /u/" + AUTHOR +")"
REDDIT = "http://reddit.com"
SUBREDDIT = "buttcoin"
MIN_MATCHES = 4
MAX_MATCHES = 12
SCORE_STORE = "score"
WORD_STORE = "words"
PHRASE_STORE = "phrases"

# If HOSTED is True the script continues looping. Set appropriate storage type and
# info based on your hosting options.
HOSTED = False
STORE_TYPE = "sqlite"
#STORE_TYPE = "file"
#STORE_TYPE = "mysql"
MYSQL_USER = "user"
MYSQL_PW = "password"
MYSQL_HOST = "127.0.0.1"

# Reddit account and API OAuth information. You can hardcode values here but
# it creates a security risk if your code is public (on Github, etc.)
# Otherwise, set the environment variables on your host as below.
USERNAME = os.environ['REDDIT_USERNAME']
PASSWORD = os.environ['REDDIT_PASSWORD']
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

# Start rate limit at 600 (10 minutes) per reply for a bot account w/no karma.
# Drops quickly as karma increases, can go down to 30 seconds minimum.
RATELIMIT = 30

# Triggers which active the bot to reply to a comment.
TRIGGER = "!BuzzwordBingo"
CMD_HS = TRIGGER + " highscores"
CMD_SCORE = TRIGGER + " score"

# Limit of scored comments saved to skip.
MAX_SCORED = 300
SCORED_STORE = "scored"

# Number of highscores.
MAX_HIGHSCORES = 5
HIGHSCORES_STORE = "highscores"

# Signature for all replies.
sig = (
    "\n_____\n\n^(I\'m a hand-run bot, *bleep* *bloop* "
    "| Send love, rage or doge to /u/" + AUTHOR + ", *beep*)"
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
ALREADY_SCORED = "Sorry, someone with stronger hands beat you to this one."

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
if DEBUG:
    print("Authenticated as: " + format(r.user.me()))

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
                SCORED_STORE, SCORE_STORE, MIN_MATCHES, HIGHSCORES_STORE)
    ds.writeHighscores(store, HIGHSCORES_STORE, scr.newHighscores(SUBREDDIT, AUTHOR))
    print("Database created. Please import word/phrases before running.")
    exit()

#
# Replies
#

def getReply (matches):
    """ Create a reply for win/loss, and updates minimum score required. """

    global MATCHES

    if len(matches) >= MATCHES:
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
    ds.writeScore(STORE_TYPE, SCORE_STORE, MATCHES)
    return (reply)

def postReply (post, reply):
    """ Add the post to list of scored, post reply. """

    global RATELIMIT, sig, already_scored

    if DEBUG:
        print(reply)
    else:
        print("X", end="")

    scr.markScored(post)
    newcomment = None
    try:
        newcomment = post.reply(reply + sig)
    except praw.exceptions.APIException as err:
        print(err)

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

    matches_found = getMatches(text)

    # Check highscores. Post reply to comment then wait out RATELIMIT.
    print(vars(comment))
    exit()
    scr.updateHighscores(len(matches_found), comment.author.name, url, highscores)
    ds.writeHighscores(store, HIGHSCORES_STORE, highscores)

    reply = getReply(matches_found)
    postReply(comment, reply)

#
# Comments
#

def getText (parent):
    """ Retrieve text from a variety of possible sources: original or crosspost,
    relies themselves, and linked Reddit posts.
    """
    
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
                print("ERROR: Unsupported or broken post reference.")
                
    if text is None or text is "":
        # Try to get text from linked post in title.
        try:
            url = parent.url
            regex = re.compile("^(http[s]*://[^\s]+)")
            link = regex.search(comment.body).group(1)
            ignore_tags = ["style", "script", "[document]", "head", "title"]
            if link is not None:
                try:
                    with urllib.request.urlopen(link) as response:
                        html = response.read()
                        soup = bs4.BeautifulSoup(html, "html.parser")
                    text = [s.extract() for s in soup(ignore_tags)]
                except urllib.error.HTTPError:
                    postReply(comment, blockedReply(link))
            else:
                print("\nEmpty link, this shouldn't happen.")
                exit()
        except AttributeError:
            print("\nERROR: Not implemented yet, skipping.")
    return(text)

def checkComment (comment):
    """ Check a comment or post for the invocation keyword. """

    global USERNAME, MATCHES, highscores, already_scored
    
    if DEBUG:
        print("comment: " + format(comment))
    else:
        print(".", end="", flush=True)
    comment.refresh()
    replies = comment.replies

    # Traverse comment forest (trees.)
    for reply in replies:
        subcomment = r.comment(reply)
        subcomment.refresh()
        print(subcomment)
        # Check for deleted replies.
        if subcomment is None:
            continue
        checkComment(subcomment)

    # Process various triggers if found in comment.
    if (CMD_HS in comment.body):
        if scr.alreadyScored(comment, already_scored):
            return
        postReply(comment, highscoresReply(highscores))

    elif (TRIGGER in comment.body):
        if CMD_SCORE in comment.body:
            regex = re.compile(CMD_SCORE + "\s+([0-9]+)\s*")
            tempscore = regex.search(comment.body).group(1)
            if tempscore is not None:
                MATCHES = int(tempscore)

        # Score the parent comment.
        parent = comment.parent()
        if (scr.alreadyScored(parent, already_scored)):
            # TODO: why is this failing?
            # or scr.alreadyScored(comment, already_scored)):
            print("Already scored.")
            return

        # Do not allow player to score their own post, unless it's testing.
        elif not (comment.author == parent.author.name and
                  comment.author.name != AUTHOR):
            scr.markScored(parent)
            playBingo(comment, getText(parent))

def processOpts(argv):
    """ Check optional arguments to import text files into database. """

    global store

    ACTION = None
    OPTIONS = [
        ["import-sqlite", "file"],
        ["import-mysql", "file"]
    ]

    opts, usage = [],[]
    for opt,arg in OPTIONS:
        opts.append(opt + "=")
        usage.append("--" + opt + " <" + arg + ">")
    try:
        [(option, file)] = getopt.getopt(argv[1:], "", opts)[0]
    except getopt.GetoptError:
        name = os.path.basename(__file__)
        print("Usage: " + name + " [", end="")
        print("|".join(usage) + "]")
        exit(2)

    regex = re.compile("^--import-(.+)$")
    dbtype = regex.search(option).group(1)
    if STORE_TYPE == dbtype:
        ACTION = dbtype

    if ACTION is not None:
        cur = store.cursor()
        dataf = open(file + ".txt", "r")
        data = dataf.read().splitlines()
        dataf.close()

        for line in data:
            if DEBUG:
                print("Added: " + line)
            stmt = "INSERT INTO " + file + " VALUES ('" + line + "')"
            try:
                cur.execute(stmt)
            except sqlite3.Error as err:
                #except (sqlite3.Error, mysql.connector.Error) as err:
                print(err)
                print("Likely duplicate entry '" + line + "' into " + file)
                exit()
        cur.close()
        store.commit()
        print("Imported " + str(len(data)) + " lines imported into " + file)
        exit()

#
# MAIN
#

# Check for command line options.
if len(sys.argv) > 1:
    processOpts(sys.argv)

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
    for score, name in highscores:
        print("Name: " + name + " got " + str(score))

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
                if DEBUG and (comment.author != AUTHOR):
                    break
                checkComment(comment)
            ds.writeScored(store, SCORED_STORE, MAX_SCORED, already_scored)
        if not HOSTED:
            break
    store.close()

if __name__ == '__main__':
    main()
