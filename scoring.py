import praw
import datastore as ds

def newHighscores (*args):
    """ Generates a list of new, generic highscores. """

    highscores = []
    user = "/u/" + args[0]
    for i in range (0,3):
        highscores.append([i + 1, user, user])
    return(highscores)

def updateHighscores (*args):
    """
    Check for a new highscore. Replace lowest since they're always sorted.
    """

    global HIGHSCORES, MAX_HIGHSCORE, AUTHOR, COMPETE, REDDIT
    # TODO: passing comment as arg[1 and use it for name and URL creation. 
    score = args[0]
    comment = args[1]
    name = comment.author.name
    highscores = args[2]
    #HIGHSCORES_STORE = args[3]
    #MAX_HIGHSCORES = args[4]
    #AUTHOR = args[5]
    #COMPETE = args[6]
    #REDDIT = args[7]

    # Don't score the author for testing, no compete flag or duplicate.
    if (name == AUTHOR) and not COMPETE:
        return
    for hscore, player, url in highscores:
        if hscore == score and player == name:
            return

    url = REDDIT + comment.id
    if len(highscores) < MAX_HIGHSCORES:
        highscores.append((score, "/u/" + name, url))
    elif score > highscores[MAX_HIGHSCORES - 1][0]:
        highscores[MAX_HIGHSCORES - 1] = [score, "/u/" + name, url]

    # Resort high to low and save.
    highscores.sort(key = lambda x: x[0], reverse = True)
    ds.writeHighscores(store, HIGHSCORES_STORE, highscores)

def markScored (post, already_scored):
    """ Add Submission or Comment id to the list of scored. """

    if type(post) is praw.models.Submission:
        entry = "sub " + str(post.id)
    else:
        entry = str(post.id)
    if entry not in already_scored:
        already_scored.append(entry)
    
def alreadyScored (r, post, already_scored, USERNAME):
    """ Check to see if a comment has been replied to already to avoid duplicates. """

    # TODO: pass in
    DEBUG = False

    # Basic check of replies to avoid duplicates. Redundant but safe if the
    # data is erased, corrupted, etc.
    if type(post) is praw.models.Submission:
        if ("sub " + str(post.id)) in already_scored:
            if DEBUG:
                print("Submission already scored, skipping.")
            return True
    elif type(post) is praw.models.Comment:
        if (post.id) in already_scored:
            if DEBUG:
                print("Comment already scored, skipping.")
            return True
    else:
        print("Unknown post type, exiting.")
        exit()

    if type(post) is praw.models.Submission:
        replies = post.comments
    else:
        replies = post.replies
    for reply in replies:
        if (r.comment(reply).author.name == USERNAME):
            if DEBUG:
                print("Skipping author\'s post.")
            return True
    return False
