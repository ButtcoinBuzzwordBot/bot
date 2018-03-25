# I'm the Buttcoin Buzzword Bingo Bot. Bleep bloop!
# TODO: Figure out Dogecoin or something useless to award monthly winners.
# TODO: sqlite support, mysql support
# TODO: link to the posts that generated the winning scores
# TODO: Add "already played" message? When parent replied, check replies?

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
SUBREDDIT = "buttcoin"
MIN_MATCHES = 4
MAX_MATCHES = 12
SCORE_STORE = "score"

# TODO: implement various approaches to hosting. text, SQL and memcache.
HOSTING_TYPE = "sqlite"
#HOSTING_TYPE = "file"

# Import libs and set store names based on hosting type.
if HOSTING_TYPE is "file":
    import pickle
elif HOSTING_TYPE is "sqlite":
    import sqlite3
    DATABASE = "buzzword.db"
else:
    print("ERROR: hosting type not implemented.")
    exit()

WORD_STORE = "words"
PHRASE_STORE = "phrases"

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

# TODO: going to use this? Gotta make sure it's posted only once.
ALREADY_SCORED = "Sorry, someone with stronger hands beat you to this one."

# Highscore report reply.
def highscoresReply (highscores):
    reply = (
        "**" + SUBREDDIT.title() + " Buzzword Bingo Highscores**\n_____\n\n"
    )
        
    count = 1
    for score, name in highscores:
        reply += str(count) + ". " + name + ": " + str(score) + "\n"
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

#
# END OF SETTINGS.
#

#
# Datastores. TODO: split this off into a separate script.
#

#HOSTING_TYPE = "sqlite", "file", "memcache"
BAD_STORE = (
    "Unknown store type. Valid settings are 'file' or 'sqlite'."
)

if HOSTING_TYPE is "file":
    store = "file"
elif HOSTING_TYPE is "sqlite":
    dbexists = True
    if not os.path.isfile(DATABASE):
        dbexists = False

    try:
        store = sqlite3.connect(DATABASE)
        curr = store.cursor()
    except sqlite3.Error (err):
        print("ERROR: Cannot create or connect to " + DATABASE)
        exit()

    if not dbexists:
        stmts = [
        "CREATE TABLE " + WORD_STORE + " (word VARCHAR(64) NOT NULL)",
        "CREATE TABLE " + PHRASE_STORE + " (phrase VARCHAR(255) NOT NULL)",
        "CREATE TABLE " + SCORED_STORE + " (scored VARCHAR(16) NOT NULL)",
        "CREATE TABLE " + SCORE_STORE + " (score int)",
        "INSERT INTO " + SCORE_STORE + " VALUES (" + str(MIN_MATCHES) + ")",
        ("CREATE TABLE " + HIGHSCORES_STORE +
        " (score int NOT NULL, name VARCHAR(32) NOT NULL)")
        ]
        try:
            for stmt in stmts:
                curr.execute(stmt)
        except sqlite3.Error:
            print("ERROR: Cannot create tables in " + DATABASE)
            exit()
        highscores = []
        for i in range (0,3):
            highscores.append([i + 1, "/u/" + AUTHOR])
            stmt = (
            "INSERT INTO " + HIGHSCORES_STORE +
            " VALUES (" + str(i + 1) + ", '/u/" + AUTHOR + "')"
            )
            try:
                curr.execute(stmt)
            except:
                print("ERROR: Cannot populate " + HIGHSCORES_STORE + " table.")
                exit()
        store.commit()

else:
    print(BAD_STORE)
    exit()

def readData(*args):
    """ Reads words or phrases data. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            dataf = open(name, "r")
        except:
            print("ERROR: File " + name + " does not exist.")
            exit()
        words  = dataf.read().splitlines()
        dataf.close()
        return(words)

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = store.cursor()
            cur.execute("SELECT * FROM " + args[1])
            return(cur.fetchall())
        except sqlite3.Error (err):
            print("ERROR: Cannot retrieve " + args[1] + "s from db.")
            exit()

def readScore(*args):
    """ Returns the current score to win. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            scoref = open(name, "r")
            score = int(scoref.readline())
        except FileNotFoundError:
            scoref = open(name, "w")
            score = args[2]
            scoref.write(str(score))
        scoref.close()
        return(score)

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = store.cursor()
            cur.execute("SELECT score FROM " + args[1])
            score = cur.fetchone()[0]
            return(int(score))
        except sqlite3.Error:
            print("ERROR: Cannot retrieve score from db.")
            exit()

def writeScore(*args):
    """ Saves the current score to win. """

    score = str(args[2])
    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            scoref = open(name, "w")
            scoref.write(score)
        except:
            print("ERROR: Can't write " + name)
        scoref.close()

    elif type(store) is sqlite3.Connection:
        try:
            cur = store.cursor()
            cur.execute("UPDATE " + args[1] + " SET score=" + score)
        except sqlite3.Error:
            print("ERROR: Cannot update score in " + DATABASE)
            exit()
        store.commit()

def readScored(*args):
    """ Reads list of posts already scored/replied to. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            scoredf = open(name, "r")
            scored = scoredf.read().splitlines()
        except FileNotFoundError:
            scoredf = open(name, "w")
            scored = []
            if DEBUG:
                print("No comments scored yet.")
        scoredf.close()
        return(scored)

    elif type(args[0]) is sqlite3.Connection:
        try:
            store.row_factory = lambda cursor, row: row[0]
            cur = store.cursor()
            cur.execute("SELECT * FROM " + args[1])
            return(cur.fetchall())
        except sqlite3.Error:
            print("ERROR: Cannot read scored comments from " + args[1])
            exit()

def writeScored(*args):
    """ Saves list of posts already scored/replied to. """
    
    global already_scored

    maxscored = args[2]
    length = len(already_scored)
    if length > maxscored:
        already_scored = already_scored[length - maxscored, length]

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            scoredf = open(name, "w")
        except:
            print("ERROR: Cannot write to " + name)
            exit()
        scoredf.writelines(("\n".join(already_scored)) + "\n")
        scoredf.close()

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = store.cursor()
            cur.execute("DELETE FROM " + args[1])
            for scored in already_scored:
                stmt = "INSERT INTO " + args[1] + " VALUES ('" + scored + "')"
                cur.execute(stmt)
        except sqlite3.Error:
            print("ERROR: Cannot write to " + args[1] + " table.")
            exit()
        store.commit()

def readHighscores(*args):
    """ Retrieves list of highscores. """

    global AUTHOR

    highscores = []
    if args[0] is "file":
        name = args[1] + ".txt"
        if os.path.isfile(name):
            with open(name, "rb") as f:
                highscores = pickle.load(f)
        else:
            for i in range (0,3):
                highscores.append([i + 1, "/u/" + AUTHOR])
            with open(name, "wb") as f:
                pickle.dump(highscores, f)
        f.close()

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = store.cursor()
            cur.execute("SELECT score,name FROM " + args[1])
        except sqlite3.Error:
            print("ERROR: Cannot read scored comments from " + args[1])
            exit()

    else:
        print(BAD_STORE)
        exit()
    return(highscores)

def writeHighscores(*args):
    """ Stores list of highscores. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            with open(name, "wb") as f:
                pickle.dump(args[2], f)
        except:
            print("ERROR: Cannot write to file " + name)
        f.close()

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = store.cursor()
            cur.execute("DELETE FROM " + args[1])
            for score,name in args[2]:
                stmt = (
                "INSERT INTO " + args[1] + " VALUES (" + int(score) + ", '" +
                name + "')"
                )
                cur.execute(stmt)
        except sqlite3.Error:
            print("ERROR: Cannot write to " + args[1] + " table.")
            exit()
        store.commit()

#
# Highscores
#

def updateHighscores (score, name):
    """
    Check for a new highscore. Replace lowest since they're always sorted.
    """

    global highscores, AUTHOR, COMPETE, MAX_HIGHSCORES, HIGHSCORES_STORE

    # Don't score the author for testing or no compete flag.
    if (name == AUTHOR) and not COMPETE:
        return

    if len(highscores) < MAX_HIGHSCORES:
        highscores.append([score, "/u/" + name])
    elif score > highscores[MAX_HIGHSCORES - 1][0]:
        # Check for duplicate entries.
        highscores[MAX_HIGHSCORES - 1] = [score, "/u/" + name]

    # Resort high to low and save.
    highscores.sort(key = lambda x: x[0], reverse = True)
    writeHighscores(store, HIGHSCORES_STORE, highscores)

#
# Replies
#

def markScored (post):
    global already_scored

    if type(post) is praw.models.Submission:
        entry = "sub " + str(post.id)
    else:
        entry = str(post.id)
    if DEBUG:
        print("Scored: " + entry)
    if entry not in already_scored:
        already_scored.append(entry)
    
# Check to see if a comment has been replied to already to avoid duplicates.
def alreadyScored (post):
    global USERNAME, already_scored

    # Basic check of replies to avoid duplicates. Redundant but safe if the
    # data is erased, corrupted, etc.
    if type(post) is praw.models.Submission:
        if ("sub " + str(post.id)) in already_scored:
            if DEBUG:
                print("Submission already scored, skipping.")
            return True
    elif type(post):
        if (post.id) in already_scored:
            if DEBUG:
                print("Comment already scored, skipping.")
            return True
    else:
        print("Unknown post type, exiting.")
        exit()

    replies = comment.replies
    for reply in replies:
        if (r.comment(reply).author.name == USERNAME):
            if DEBUG:
                print("Skipping author\'s post.")
            return True
    return False

# Creates a standard reply for wins/losses, and updates minimum score required.
def getReply (matches):
    global MATCHES

    print("Matches #" + str(len(matches)))
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
    writeScore(HOSTING_TYPE, SCORE_STORE, MATCHES)
    return (reply)

# Add the post to list of scored, post reply.
def postReply (post, reply):
    global RATELIMIT, sig, already_scored

    if DEBUG:
        print(reply)
    else:
        print("X", end="")

    markScored(post)
    newcomment = None
    try:
        newcomment = post.reply(reply + sig)
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

# Check if we've already replied, score text and reply.
def playBingo (comment, text):
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
                print("ERROR: Unsupported or broken post reference.")
                
    if text is None or text is "":
        # Try to get text from linked post in title.
        try:
            # TODO: Code to scrape pages from title link.
            url = parent.url
            regex = re.compile("^(http[s]*://[^\s]+)")
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
                print("Empty link, this shouldn't happen.")
                exit()
        except AttributeError:
            print("ERROR: Not implemented yet, skipping.")
    return(text)

# Check a comment or post for the invocation keyword.
def checkComment (comment):
    global MATCHES, highscores
    
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
        checkComment(subcomment)

    # Process various triggers if found in comment.
    if (CMD_HS in comment.body):
        if alreadyScored(comment):
            return
        postReply(comment, highscoresReply(highscores))

    elif (TRIGGER in comment.body):
        if CMD_SCORE in comment.body:
            regex = re.compile(CMD_SCORE + "\s+([0-9]+)\s*")
            tempscore = regex.search(comment.body).group(1)
            if tempscore is not None:
                MATCHES = int(tempscore)

        # Score the parent comment.
        comment.refresh()
        parent = comment.parent()
        if alreadyScored(parent) or alreadyScored(comment):
            print("Already scored.")
            return

        # Do not allow player to score their own post, unless it's testing.
        elif not (comment.author == parent.author.name and
                  comment.author.name != AUTHOR):
            markScored(parent)
            playBingo(comment, getText(parent))

#
# MAIN TODO: cleanup
#

def processOpts(argv):
    """ Check optional arguments to import text files into database. """

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
    if HOSTING_TYPE == dbtype:
        ACTION = dbtype

    if ACTION is not None:
        if ACTION is "sqlite":
            cur = store.cursor()
        dataf = open(file + ".txt", "r")
        data = dataf.read().splitlines()
        for line in data:
            stmt = "INSERT INTO " + file + " VALUES ('" + line + "')"
            if ACTION is "sqlite":
                cur.execute(stmt)
        if ACTION is "sqlite":
            store.commit()
        dataf.close()
        print("Imported " + str(len(data)) + " lines imported into " + file)
        exit()

processOpts(sys.argv)

if DEBUG:
    SUBREDDIT = "testingground4bots"
    print("Username/pass: " + USERNAME, PASSWORD)
    print("Client ID/pass: " + CLIENT_ID, CLIENT_SECRET)

# Read words and phrases, build sets of each.
buzzwords = set()
buzzphrases = set()

for word in readData(store, WORD_STORE):
    buzzwords.add(word)
    buzzwords.add(word + "s")

for phrase in readData(store, PHRASE_STORE):
    buzzphrases.add(phrase)

# Will create score file with min. value if doesn't exist.
MATCHES = readScore(store, SCORE_STORE, MIN_MATCHES)

# Get comments already scored to prevent repeats and multiple plays.
already_scored = readScored(store, SCORED_STORE)

# Load high scores. If file does not exist, create one.
highscores = readHighscores(store, HIGHSCORES_STORE)
highscores.sort(key = lambda x: x[0], reverse = True)
if DEBUG:
    for score, name in highscores:
        print("Name: " + name + " got " + str(score))

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
    print("Authenticated as: " + format(r.user.me()))

# 1. Don't reply to the same request more than once.
# 2. Don't hit the same page more than once per 30 seconds.
# 3. Request multiple resources at once rather than single in a loop.

sub = r.subreddit(SUBREDDIT).new()
for submission in sub:
    post = r.submission(submission)

    for comment in post.comments:
        if DEBUG and (comment.author != AUTHOR):
            break
        checkComment(comment)

    # Write list of scored comments after each submission.
    writeScored(store, SCORED_STORE, MAX_SCORED)

if HOSTING_TYPE is "sqlite":
    store.close()
