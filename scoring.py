import string
import re

import praw

import config as cfg
import comments as cmt
import datastore as ds

def newHighscores (*args):
    """ Generates a list of new, generic highscores. """

    user = "/u/" + args[0]
    for i in range (0,3):
        cfg.highscores.append([i + 1, user, user])

def updateHighscores (*args):
    """
    Check for a new highscore. Replace lowest since they're always sorted.
    """

    score = args[0]
    comment = args[1]
    name = comment.author.name

    # Don't score the author for testing, no compete flag or duplicate.
    if (name == cfg.AUTHOR) and not cfg.COMPETE:
        return
    for hscore, player, url in cfg.highscores:
        if hscore == score and player == name:
            return

    url = cfg.REDDIT + comment.id
    if len(cfg.highscores) < cfg.MAX_HIGHSCORES:
        cfg.highscores.append((score, "/u/" + name, url))
    elif score > cfg.highscores[cfg.MAX_HIGHSCORES - 1][0]:
        cfg.highscores[cfg.MAX_HIGHSCORES - 1] = [score, "/u/" + name, url]

    # Resort high to low and save.
    cfg.highscores.sort(key = lambda x: x[0], reverse = True)
    ds.writeHighscores(store, cfg.HIGHSCORES_STORE)

def markScored (post):
    """ Add Submission or Comment id to the list of scored. """

    if type(post) is praw.models.Submission:
        entry = "sub " + str(post.id)
    else:
        entry = str(post.id)
    if entry not in cfg.already_scored:
        cfg.already_scored.append(entry)
    
def alreadyScored (r, post):
    """ Check to see if a comment has been replied to already to avoid duplicates. """

    # Basic check of replies to avoid duplicates. Redundant but safe if the
    # data is erased, corrupted, etc.
    if type(post) is praw.models.Submission:
        if ("sub " + str(post.id)) in cfg.already_scored:
            if cfg.DEBUG: print("Submission already scored, skipping.")
            return True
    elif type(post) is praw.models.Comment:
        if (post.id) in cfg.already_scored:
            if cfg.DEBUG: print("Comment already scored, skipping.")
            return True
    else:
        print("Unknown post type, exiting.")
        exit()

    #if type(post) is praw.models.Submission:
    #    replies = post.comments
    #else:
    #    replies = post.replies
    #for reply in replies:
    #    if (r.comment(reply).author.name == cfg.USERNAME):
    #        print(reply.body)
    #        if cfg.DEBUG: print("Replied to by bot, skipping.")
    #        return True
    return False

def getMatches(text):
    """ Match words and phrases in text, return score. """

    matches_found = set()

    # Remove all punctuation from words, and convert dashes to spaces for
    # phrases.
    text = text.replace("\'-/", " ").lower()
    regex = re.compile("[%s]" % re.escape(string.punctuation))
    words = regex.sub("", text).split()

    # First seatch for buzzphrases.
    for phrase in cfg.buzzphrases:
        if phrase.lower() in text:
            matches_found.add(phrase)

    # Search for buzzwords that do not match phrases found.
    matched = " ".join(match.lower() for match in matches_found)
    for word in cfg.buzzwords:
        if word.lower() in words and word.lower() not in matched:
            matches_found.add(word)

    # Remove plural duplicates.
    dupes = matches_found.copy()
    for word in dupes:
        matches_found.discard(word + "s")
    return (matches_found)

def playBingo (comment, text):
    """ Check if we've already replied, score text and reply. """

    if text is None: return
    matches_found = getMatches(text)
    updateHighscores(len(matches_found), comment)
    reply = cmt.getReply(matches_found)
    cmt.postReply(comment, reply, )