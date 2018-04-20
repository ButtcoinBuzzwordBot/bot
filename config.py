# Buzzword Bingo Bot config file. Bleep bloop.
#
# TODO: Figure out Dogecoin or something useless to award monthly winners?
# TODO: mysql support.

import os

# When DEBUG is True the bot will only reply to posts by AUTHOR and uses a test
# sub defined in the oauth module.
DEBUG = True

# If HOSTED is True the script continues looping indefinitely.
HOSTED = True

# If ALLOW_COMPETE is True the AUTHOR can set highscores.
ALLOW_COMPETE = False

AUTHOR = "BarcaloungerJockey"
BOTNAME = "python:buzzword.bingo.bot:v1.4 (by /u/" + AUTHOR +")"
USERNAME = os.environ['REDDIT_USERNAME']
IGNORE = [USERNAME, AUTHOR, "reddit"]
REDDIT = "https://redd.it/"
SUBREDDIT = "buttcoin"

# Min/max matches to win, changes dynamically.
MIN_MATCHES = 4
MAX_MATCHES = 12

# Datastores.
SCORE_STORE = "score"
WORD_STORE = "words"
PHRASE_STORE = "phrases"
MAX_SCORED = 1000
SCORED_STORE = "scored"
MAX_HIGHSCORES = 5
HIGHSCORES_STORE = "highscores"

DATABASE = "buzzword"
STORE_TYPE = "sqlite"
#STORE_TYPE = "file"
#STORE_TYPE = "mysql"
#MYSQL_USER = "user"
#MYSQL_PW = "password"
#MYSQL_HOST = "127.0.0.1"

# Start rate limit at 600 (10 minutes) per reply for a bot account w/no karma.
# Drops quickly as karma increases, can go down to 10 seconds minimum.
RATELIMIT = 10

# Triggers which active the bot to reply to a comment.
TRIGGER = "!BuzzwordBingo"
CMD_HS = TRIGGER + " highscores"
CMD_SCORE = TRIGGER + " score"

# Signature for all replies.
sig = (
    "\n_____\n\n^(Hi! I\'m a hand-run bot, *bleep* *bloop* "
    "| Send praise, rage or arcade game tokens to /u/" + AUTHOR + ", *beep*)"
)

# Post already replied to.
alreadyPlayed = "Sorry weak hands, that post was already played."

# Playing off one's own post.
selfPlayed = "Tsk, tsk nocoiner. No gaming the system by playing your own posts."

# Highscore report reply.
def highscoresReply (hs) -> str:
    reply = (
        "**" + SUBREDDIT.title() + " Buzzword Bingo Highscores**\n_____\n\n"
    )
        
    count = 1
    for score,name,url in hs:
        reply += (str(count) + ". " + name + ": **" + str(score) +
                  "** for [this](" + url + ")\n")
        count += 1
    return(reply)

# Winning reply.
def winnerReply (matches) -> str:
    return(
    "**Bingo**! We have a winner with *" + str(len(matches)) +
        "* matches found!!\n\n**Buzzwords**: " + ", ".join(matches)
    )

# Losing reply.
def loserReply(score) -> str:
    return (
        "Sorry bro, your hands are weak. Current score to win is **" +
        str(score) + "** or more matches. Convert more filty fiat to "
        "mine for comedy gold again."
    )

# Link to website blocked for robots.
def blockedReply(link) -> str:
    return (
        "No way, bro. Robots are blocked for: " + link
    )

# Exception to print error and exit main loop.
class ExitException(Exception):
    pass

MATCHES = MIN_MATCHES
scoredf = None
buzzwords = set()
buzzphrases = set()
already_scored = []
highscores = []
