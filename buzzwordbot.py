# I'm the Buttcoin Buzzword Bingo Bot. Bleep bloop!
# TODO: Figure out Dogecoin or something useless to award monthly winners?
# TODO: mysql, memcache, log4 support
# TODO: Add "already played" message? When parent replied, check replies?
# FIX: test all cases when replies should not be allowed.
# FIX: highscores not reading for SQLite? Add import from file.
# FIX: Add newline to start of all error msgs.

import sys, traceback, time
import praw
import config as cfg, datastore as ds, comments as cmt, cmdline, oauth

def main(r):
    """ Initialize and recurse through posts. """

    dstore = ds.DataStore(cfg.STORE_TYPE)
    if len(sys.argv) > 1:
        cmdline.processOpts(dstore, sys.argv)

    # Check bot inbox for messages.
    msgs = list(r.inbox.unread(limit=None))
    if len(msgs) > 0 and not cfg.HOSTED:
        print(str(len(msgs)) +" message(s) in /u/"+ cfg.USERNAME +"\'s inbox.")
        print("Please read before running bot.")
        if len(msgs) > cfg.MAX_MSGS: exit()
  
    try:
        for word in dstore.readData(cfg.WORD_STORE):
            cfg.buzzwords.add(word)
            cfg.buzzwords.add(word + "s")
    except Exception as err:
        print(err)
        exit()

    try:
        for phrase in dstore.readData(cfg.PHRASE_STORE):
            cfg.buzzphrases.add(phrase)
    except Exception as err:
        print(err)
        exit()

    cfg.MATCHES = dstore.readScore()
    cfg.already_scored = dstore.readScored()
    cfg.highscores = dstore.readHighscores()
    if cfg.DEBUG:
        for score, name, url in cfg.highscores:
            print("Name: " + name + " got " + str(score) + " (" + url + ")")

    try:
        while True:
            sub = r.subreddit(cfg.SUBREDDIT).new()
            for submission in sub:
                post = r.submission(submission)
                if cfg.DEBUG: print("submission: " + format(post.id))
                for comment in post.comments:
                    c = cmt.Comment(dstore, r, comment)
                    c.checkComment()
            if not cfg.HOSTED:
                print("\nBleep! All done.")
                break

        if store != "file": dstore.closeDB()

    except:
        if cfg.DEBUG: traceback.print_exc()
        time.sleep(30)
        if cfg.DEBUG: print("ERROR: Reddit timeout, resuming.")

if __name__ == '__main__':
    main(oauth.auth())
