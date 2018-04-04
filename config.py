# When DEBUG is True the bot will only reply to posts by AUTHOR. Modify these
# to customize the bot, along with the words and phrases files. By default the
# AUTHOR can compete but highscores will not be registered, to keep the game
# fair

DEBUG = True
AUTHOR = "BarcaloungerJockey"
COMPETE = False
BOTNAME = "python:buzzword.bingo.bot:v1.4 (by /u/" + AUTHOR +")"
REDDIT = "https://redd.it/"
SUBREDDIT = "buttcoin"
MIN_MATCHES = 4
MAX_MATCHES = 12
# Max. new messages in bot inbox before script quits.
MAX_MSGS = 12

SCORE_STORE = "score"
WORD_STORE = "words"
PHRASE_STORE = "phrases"
MAX_SCORED = 300
SCORED_STORE = "scored"
MAX_HIGHSCORES = 5
HIGHSCORES_STORE = "highscores"

# If HOSTED is True the script continues looping. Set appropriate storage type and
# info based on your hosting options.
HOSTED = False
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
def highscoresReply (hs):
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

MATCHES = MIN_MATCHES

scoredf = None
buzzwords = set()
buzzphrases = set()
already_scored = []
highscores = []
