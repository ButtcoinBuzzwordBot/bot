# I'm the Buttcoin Buzzword Bingo Bot. Bleep bloop!
# TODO: Figure out Dogecoin or something useless to award monthly winners?
# TODO: mysql, memcache, log4 support
# TODO: Add "already played" message? When parent replied, check replies?
# TODO: Randomize win/loss comments and insults?
# TODO: cmd line import for highscores from pickle into db
# FIX: link to comments <> link to submission in highscores

import sys
import os

import praw

import config as cfg
import datastore as ds
import scoring as scr
import comments as cmt
import cmdline

# Initialize PRAW with custom User-Agent.
if cfg.DEBUG:
    cfg.SUBREDDIT = "testingground4bots"
    print("Username/pass: " + cfg.USERNAME, cfg.PASSWORD)
    print("Client ID/pass: " + cfg.CLIENT_ID, cfg.CLIENT_SECRET)
    print("Authenticating...")
r = praw.Reddit(
    client_id=cfg.CLIENT_ID,
    client_secret=cfg.CLIENT_SECRET,
    password=cfg.PASSWORD,
    user_agent=cfg.BOTNAME,
    username=cfg.USERNAME
)
if cfg.DEBUG: print("Authenticated as: " + format(r.user.me()))

dbexists = True
if cfg.STORE_TYPE is "file":
    store = "file"
    cfg.highscores = ds.readHighscores(store, cfg.HIGHSCORES_STORE, cfg.AUTHOR)

elif cfg.STORE_TYPE is "sqlite":
    cfg.DATABASE = "buzzword.db"
    if not os.path.isfile(cfg.DATABASE):
        dbexists = False
    try:
        store = sqlite3.connect(cfg.DATABASE)
    except sqlite3.Error (err):
        print("ERROR: Cannot create or connect to " + cfg.DATABASE)
        exit()

elif cfg.STORE_TYPE is "mysql":
    # TODO: Why isn't this module being found?
    #import PyMySQL as mysql
    cfg.DATABASE = "buzzword"
    try:
        store = mysql.connector.connect(
            user=MYSQL_USER, password=MYSQL_PW, host=MYSQL_HOST, database=DATABASE)
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("ERROR: Bad sername or password for " + DATABASE)
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            dbexists = False
        else:
            print(err)

else:
    print("Unknown store type. Valid settings are: file, sqlite, mysql.")
    exit()

if not dbexists:
    ds.createDB(store, cfg.STORE_TYPE)
    cfg.highscores = ds.readHighscores(store, cfg.HIGHSCORES_STORE, cfg.AUTHOR)
    ds.writeHighscores(store, cfg.HIGHSCORES_STORE, cfg.highscores)
    print("Database created. Please import word/phrases before running.")
    exit()

#
# MAIN
#

# Check for command line options.
if len(sys.argv) > 1:
    cmdline.processOpts(store, sys.argv)

# Check bot inbox for messages.
msgs = list(r.inbox.unread(limit=None))
if len(msgs) > 0 and not cfg.HOSTED:
    print(str(len(msgs)) + " message(s) in /u/" + cfg.USERNAME + "\'s inbox.")
    print("Please read before running bot.")
    if len(msgs) > cfg.MAX_MSGS: exit()

try:
    for word in ds.readData(store, cfg.WORD_STORE):
        cfg.buzzwords.add(word)
        cfg.buzzwords.add(word + "s")
except Exception as err:
    print(err)
    exit()

try:
    for phrase in ds.readData(store, cfg.PHRASE_STORE):
        cfg.buzzphrases.add(phrase)
except Exception:
    exit()

# Will create score file with min. value if doesn't exist.
cfg.MATCHES = ds.readScore(store, cfg.SCORE_STORE, cfg.MIN_MATCHES)

# Get comments already scored to prevent repeats and multiple plays.
cfg.already_scored = ds.readScored(store, cfg.SCORED_STORE)

cfg.highscores.sort(key = lambda x: x[0], reverse = True)
if cfg.DEBUG:
    for score, name, url in cfg.highscores:
        print("Name: " + name + " got " + str(score) + " (" + url + ")")

def main():
    """
    1. Don't reply to the same request more than once.
    2. Don't hit the same page more than once per 30 seconds.
    3. Request multiple resources at once rather than single in a loop.
    """

    while True:
        sub = r.subreddit(cfg.SUBREDDIT).new()
        for submission in sub:
            post = r.submission(submission)
            if cfg.DEBUG: print("submission: " + format(post.id))
            for comment in post.comments:
                cmt.checkComment(store, r, comment)
        if not cfg.HOSTED:
            print("\nBleep! All done.")
            break

    if store != "file": store.close()

if __name__ == '__main__':
    main()
