import datastore as ds
import scoring as scr

def getReply (*args):
    """ Create a reply for win/loss, and updates minimum score required. """

    global STORE_TYPE, SCORE_STORE, MIN_MATCHES, MAX_MATCHES
    matches = args[0]
    score = args[1]

    if len(matches) >= score:
        reply = winnerReply(matches)
        if score < MAX_MATCHES:
            score += 1
    else:
        reply = loserReply(score)
        if score > MIN_MATCHES:
            score -= 1
    ds.writeScore(STORE_TYPE, SCORE_STORE, score)
    return (reply)

def postReply (*args):
    """ Add the post to list of scored, post reply. """

    global RATELIMIT, sig
    post = args[0]
    reply = args[1]
    already_scored = args[2]

    if DEBUG: print(reply)
    else: print("X", end="")

    scr.markScored(post, already_scored)
    try:
        post.reply(reply + sig)
        time.sleep(RATELIMIT)
    except praw.exceptions.APIException as err:
        print(err)

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
            if link.find(".pdf", len(link) -4) and DEBUG:
                return(text)
            if link is not None:
                try:
                    with urllib.request.urlopen(link) as response:
                        html = response.read()
                        try:
                            soup = bs4.BeautifulSoup(html, "html.parser")
                        except html.HTMLParser.HTMLParseError:
                            if DEBUG: print("\nERROR: Unable to parse page, skipping.")
                            return(text)
                    text = soup.find('body').getText()
                except urllib.error.HTTPError:
                    postReply(comment, blockedReply(link))
            else:
                print("\nERROR: Empty link, this shouldn't happen.")
                exit()
        except AttributeError:
            print("\nERROR: Not implemented yet, skipping.")
    return(text)

def checkComment (*args):
    """ Check a comment or post for the invocation keyword. """

    global USERNAME, needed, highscores, already_scored
    comment = args[0]
    
    if DEBUG:
        print("comment: " + format(comment))
    elif not HOSTED:
        print(".", end="", flush=True)
    comment.refresh()
    replies = comment.replies

    # Traverse comment forest (trees.)
    for reply in replies:
        subcomment = r.comment(reply)
        subcomment.refresh()
        checkComment(subcomment)

    # Process various triggers if found in comment.
    if (TRIGGER in comment.body):
        if scr.alreadyScored(r, comment, already_scored, USERNAME):
            return

    if (CMD_HS in comment.body):
        postReply(comment, highscoresReply(highscores))
    elif (CMD_KOAN in comment.body):
        reply = ds.readRandom(store, KOAN_STORE)
        postReply(comment, reply)
    elif (CMD_HAIKU in comment.body):
        reply = ds.readRandom(store, HAIKU_STORE)
        postReply(comment, reply)
    elif (TRIGGER in comment.body):
        if CMD_SCORE in comment.body:
            regex = re.compile(CMD_SCORE + "\s+([0-9]+)\s*")
            tempscore = regex.search(comment.body).group(1)
            if tempscore is not None:
                needed = int(tempscore)

        # Score the parent comment.
        parent = comment.parent()
        if scr.alreadyScored(r, parent, already_scored, USERNAME):
            return

        # Do not allow player to score their own post, unless it's testing.
        elif not (comment.author == parent.author.name and
                  comment.author.name != AUTHOR):
            scr.markScored(parent, already_scored)
            playBingo(comment, getText(parent))
