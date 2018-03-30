import time
import re

import praw
import urllib
import bs4

import config as cfg
import datastore as ds
import scoring as scr

def getReply (*args):
    """ Create a reply for win/loss, and updates minimum score required. """

    matches = args[0]

    if len(matches) >= cfg.MATCHES:
        reply = cfg.winnerReply(matches)
        if cfg.MATCHES < cfg.MAX_MATCHES:
            cfg.MATCHES += 1
    else:
        reply = cfg.loserReply(cfg.MATCHES)
        if cfg.MATCHES > cfg.MIN_MATCHES:
            cfg.MATCHES -= 1
    ds.writeScore(cfg.STORE_TYPE, cfg.SCORE_STORE)
    return (reply)

def postReply (*args):
    """ Add the post to list of scored, post reply. h"""

    post = args[0]
    reply = args[1]

    if cfg.DEBUG: print("Posting reply:\n" + reply)
    else: print("X", end="")

    scr.markScored(post)
    try:
        post.reply(reply + cfg.sig)
        time.sleep(cfg.RATELIMIT)
    except praw.exceptions.APIException as err:
        print(err)
    return True

def getText (*args):
    """
    Retrieve text from a variety of possible sources: original or crosspost, relies,
    linked Reddit posts, etc.
    """

    parent = args[0]

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
                print("\nERROR: Unsupported or broken post reference.")
                
    if text is None or text is "":
        # Try to get text from link in title, skip PDF.
        try:
            link = parent.url
            if cfg.DEBUG: print("link: " + link)
            if link.find(".pdf", len(link) -4)!= -1: return(None)
            
            if link is not None:
                try:
                    with urllib.request.urlopen(link) as response:
                        html = response.read()
                        try:
                            soup = bs4.BeautifulSoup(html, "html.parser")
                        except html.HTMLParser.HTMLParseError:
                            if cfg.DEBUG:
                                print("\nERROR: Unable to parse page, skipping.")
                            return(text)
                    text = soup.find('body').getText()
                    return(text)
                except urllib.error.HTTPError:
                    postReply(comment, cfg.blockedReply(link))
            else:
                print("\nERROR: Empty link, this shouldn't happen.")
                exit()
        except AttributeError:
            print("\nERROR: Not implemented yet, skipping.")
    return(text)

def checkComment (*args):
    """ Check a comment or post for the invocation keyword. """

    store = args[0]
    r = args[1]
    comment = args[2]

    if cfg.DEBUG: print("comment: " + format(comment))
    elif not cfg.HOSTED: print(".", end="", flush=True)
    comment.refresh()
    replies = comment.replies

    # Traverse comment forest (trees.)
    for reply in replies:
        subcomment = r.comment(reply)
        subcomment.refresh()
        checkComment(store, r, subcomment)

    # Process various triggers if found in comment.
    scoredFlag = False
    if scr.alreadyScored(r, comment): return
    if (cfg.CMD_HS in comment.body):
        scoredFlag = postReply(comment, cfg.highscoresReply(cfg.highscores))
    elif (cfg.CMD_KOAN in comment.body):
        scoredFlag = postReply(comment, ds.readRandom(store, cfg.KOAN_STORE))
    elif (cfg.CMD_HAIKU in comment.body):
        scoredFlag = postReply(comment, ds.readRandom(store, cfg.HAIKU_STORE))
    elif (cfg.TRIGGER in comment.body):
        if cfg.CMD_SCORE in comment.body:
            regex = re.compile(cfg.CMD_SCORE + "\s+([0-9]+)\s*")
            tempscore = regex.search(comment.body).group(1)
            if tempscore is not None:
                needed = int(tempscore)

        parent = comment.parent()
        print("parent: " + format(parent))
        if not cfg.DEBUG:
            if scr.alreadyScored(r, parent): return
            elif comment.author == parent.author.name: return
            #elif comment.author.name != cfg.AUTHOR: return
        else:
            scr.markScored(parent)
            scoredFlag = scr.playBingo(comment, getText(parent))
    if scoredFlag:
        ds.writeScored(store, cfg.SCORED_STORE)
