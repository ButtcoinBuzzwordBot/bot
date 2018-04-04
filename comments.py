import time, re
import praw, urllib, bs4
import config as cfg, scoring as scr

class Comment:

    def __init__ (self, dstore=None, r=None, comment=None) -> None:
        self.dstore = dstore
        self.r = r
        self.comment = comment

    def postReply (self, reply) -> None:
        """ Add the post to list of scored, post reply. h"""

        if cfg.DEBUG: print("Posting reply:\n" + reply)
        else: print("X", end="")
        try:
            self.comment.reply(reply + cfg.sig)
            time.sleep(cfg.RATELIMIT)
        except praw.exceptions.APIException as err:
            print(err)

    def getText (self, parent):
        """
        Retrieve text from a variety of possible sources: original or crosspost,
        relies, linked Reddit posts, etc.
        """

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
                if link is not None:
                    if link.find(".pdf", len(link) -4)!= -1: return(None)
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
                        scr.markScored(comment)
                        postReply(comment, cfg.blockedReply(link))
                else:
                    print("\nERROR: Empty link, this shouldn't happen.")
                    exit()
            except AttributeError:
                print("\nERROR: Not implemented yet, skipping.")
        return(text)

    def scanComment (self):
        """ Looks for triggers in a comment. """

        if not (cfg.TRIGGER in self.comment.body):
            return(None)

        scr.markScored(self.comment)
        if cfg.CMD_HS in self.comment.body:
            return(cfg.highscoresReply(cfg.highscores))
        else:
            if cfg.CMD_SCORE in self.comment.body:
                regex = re.compile(cfg.CMD_SCORE + "\s+([0-9]+)\s*")
                tempscore = regex.search(self.comment.body).group(1)
                if tempscore is not None:
                    cfg.MATCHES = int(tempscore)

            parent = self.comment.parent()
            if cfg.DEBUG: print("parent: " + format(parent))
            else:
                if (scr.alreadyScored(self.r, parent) or
                    self.comment.author == parent.author.name or
                    parent.author.name == cfg.USERNAME): return(None)
            scr.markScored(parent)
            return(scr.playBingo(self.comment, self.getText(parent)))

    def checkComment (self):
        """ Check a comment or post for the invocation keyword. """

        if cfg.DEBUG: print("comment: " + format(self.comment))
        elif not cfg.HOSTED: print(".", end="", flush=True)
        self.comment.refresh()
        replies = self.comment.replies

        # Traverse comment forest (trees.)
        for reply in replies:
            subcomment = self.r.comment(reply)
            subcomment.refresh()
            c = Comment(self.dstore, self.r, subcomment)
            c.checkComment()

        if scr.alreadyScored(self.r, self.comment): return
        result = self.scanComment()
        if result is not None:
            self.postReply(result)
            self.dstore.writeScored(cfg.already_scored)
