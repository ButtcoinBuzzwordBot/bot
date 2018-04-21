# I'm the Buttcoin Buzzword Bingo Bot. Bleep bloop!

import sys, traceback, time

import praw

import config as cfg
import datastore as ds
import comments as cmt
import cmdline, oauth

def checkInbox(r, dbase):
    """ Check inbox and reply randomly to new messages from regular users. """

    msgs = list(r.inbox.unread(limit=None))
    if cfg.DEBUG or (len(msgs) > 0 and not cfg.HOSTED):
        print(str(len(msgs)) +" message(s) in /u/"+ cfg.USERNAME +"\'s inbox.")

def main(r):
    """ Initialize and recurse through submissions and replies. """

    dstore = ds.DataStore(cfg.STORE_TYPE)
    if len(sys.argv) > 1:
        cmdline.processOpts(dstore, sys.argv)
    checkInbox(r, dstore)
  
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
        print ("Type CRTL-C to exit.")
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
                    c.checkPost()
            if not cfg.HOSTED:
                print("\nBleep! All done.")
                break

    except cfg.ExitException as err:
        print(err)
        exit()
    except praw.exceptions.PRAWException as err:
        if cfg.DEBUG: print(str(err) + "\nERROR: Reddit timeout, resuming.")
        time.sleep(60)
    except Exception as err:
        time.sleep(60)
        if cfg.DEBUG: print(str(err) + "\nERROR: Reddit error, resuming.")

    if cfg.STORE_TYPE is not "file":
        dstore.closeDB()

if __name__ == '__main__':
    main(oauth.auth())
