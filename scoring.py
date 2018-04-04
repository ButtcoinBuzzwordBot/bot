import string, re
import config as cfg

def newHighscores () -> list:
    """ Generates a list of new, generic highscores. """

    user = "/u/" + cfg.AUTHOR
    hs = []
    for i in range (0,3):
        hs.append([i + 1, user, user])
    return(hs)

def updateHighscores (score, name, url) -> None:
    """ Check for a new highscore. Replace lowest since they're always sorted. """

    # Don't score the author for testing, no compete flag or duplicate.
    if (name == cfg.AUTHOR) and not cfg.COMPETE: return
    for hscore, player, url in cfg.highscores:
        if hscore == score and player == name: return

    # Update highscores with link to original submission.
    if len(cfg.highscores) < cfg.MAX_HIGHSCORES:
        cfg.highscores.append((score, "/u/" + name, url))
    elif score > cfg.highscores[cfg.MAX_HIGHSCORES - 1][0]:
        cfg.highscores[cfg.MAX_HIGHSCORES - 1] = [score, "/u/" + name, url]

    cfg.highscores.sort(key = lambda x: x[0], reverse = True)

def markScored (post) -> None:
    """ Add unique post id to the list of scored. """

    if post.id not in cfg.already_scored:
        cfg.already_scored.append(str(post.id))        

def alreadyScored (post) -> bool:
    """ Check to see if a comment has been replied to already to avoid duplicates. """

    if (post.id) in cfg.already_scored:
        if cfg.DEBUG: print("Post already scored, skipping.")
        return True
    return False

def getMatches (text) -> list:
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

def getReply (matches) -> str:
    """ Create a reply for win/loss, and updates minimum score required. """

    if len(matches) >= cfg.MATCHES:
        reply = cfg.winnerReply(matches)
        if cfg.MATCHES < cfg.MAX_MATCHES:
            cfg.MATCHES += 1
    else:
        reply = cfg.loserReply(cfg.MATCHES)
        if cfg.MATCHES > cfg.MIN_MATCHES:
            cfg.MATCHES -= 1
    return (reply)

def playBingo (comment, text) -> bool:
    """ Check if we've already replied, score text and reply. """

    if text is None: return False
    matches_found = getMatches(text)
    updateHighscores(len(matches_found), comment.author,
                     cfg.REDDIT + str(comment.submission))
    return(getReply(matches_found))
