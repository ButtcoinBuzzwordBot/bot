import os

# When DEBUG is True the bot will only reply to posts by AUTHOR. Modify these
# to customize the bot, along with the words and phrases files. By default the
# AUTHOR can compete but highscores will not be registered, to keep the game
# fair

DEBUG = False
AUTHOR = "BarcaloungerJockey"
COMPETE = False
BOTNAME = "python:buzzword.bingo.bot:v1.3 (by /u/" + AUTHOR +")"
REDDIT = "https://redd.it/"
#REDDIT = "https://reddit.com/r/"
SUBREDDIT = "buttcoin"
MIN_MATCHES = 4
MAX_MATCHES = 12
# Max. new messages in bot inbox before script quits.
MAX_MSGS = 12

DATABASE = None
SCORE_STORE = "score"
WORD_STORE = "words"
PHRASE_STORE = "phrases"
KOAN_STORE = "koans"
HAIKU_STORE = "haiku"

# If HOSTED is True the script continues looping. Set appropriate storage type and
# info based on your hosting options.
HOSTED = False
#STORE_TYPE = "sqlite"
STORE_TYPE = "file"
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
        reply += (str(count) + ". " + name + ": **" + str(score) +
                  "** for [this](" + url + ")\n")
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

MATCHES = MIN_MATCHES

scoredf = None

buzzwords = set()
buzzphrases = set()
already_scored = []
highscores = []
