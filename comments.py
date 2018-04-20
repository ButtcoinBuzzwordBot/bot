import time, re

import praw
import urllib
import bs4

import config as cfg
import scoring as scr

class Comment:

    def __init__(self, dstore=None, r=None, post=None) -> None:
        self.dstore = dstore
        self.r = r
        self.post = post

        self.post.refresh()

    def postReply(self, reply) -> None:
        """ Add the post to list of scored, post reply. h"""

        if cfg.DEBUG: print("Posting reply:\n" + reply)
        else: print("X", end="")
        try:
            self.post.reply(reply + cfg.sig)
            time.sleep(cfg.RATELIMIT)
        except praw.exceptions.APIException as err:
            print(err)

    def getHTML(self, link) -> str:
        """ Attempt to scrape text from link, skip PDF, etc. """

        if cfg.DEBUG: print("link: " + link)
        if link is None or link.find(".pdf", len(link) -4)!= -1: return(None)
        try:
            with urllib.request.urlopenlink(link) as response:
                html = response.read()
                try:
                    soup = bs4.BeautifulSoup(html, "html.parser")
                except html.HTMLParser.HTMLParseError:
                    if cfg.DEBUG:
                        print("\nERROR: Unable to parse page, skipping.")
                    return(text)
                except html.HTMLParser.ReadTimeoutError as err:
                    raise cfg.ExitException("ReadTimeout: " + err)
                except Exception as err:
                    raise cfg.ExitException(err + "\nError parsing HTML.")
                text = soup.find('body').getText()
                return(text)
        except urllib.error.HTTPError:
            scr.markScored(comment)
            self.postReply(cfg.blockedReply(link))
        except urllib.error.ReadTimeoutError as err:
            raise cfg.ExitException("Read Timeout: " + err)
        except urllib.error.ConnectionTimeout as err:
            raise cfg.ExitException("Connection Timeout: " + err)
        except Exception as err:
            raise cfg.ExitException(err + "\nError scraping HTML.")
        return(None)
        
    def getText(self, parent) -> str:
        """ Retrieve text from a variety of possible sources. """

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
                
        # Try to get text from link in title, skip PDF.
        if text is None or text is "":
            text = self.getHTML(parent.url)
        return(text)

    def scanComment(self) -> str:
        """ Looks for triggers in a comment. """

        if not (cfg.TRIGGER in self.post.body): return(None)
        if scr.alreadyScored(self.post): return
        else: scr.markScored(self.post)

        if cfg.CMD_HS in self.post.body:
            return(cfg.highscoresReply(cfg.highscores))
        else:
            if cfg.CMD_SCORE in self.post.body:
                regex = re.compile(cfg.CMD_SCORE + "\s+([0-9]+)\s*")
                tempscore = regex.search(self.post.body).group(1)
                if tempscore is not None:
                    cfg.MATCHES = int(tempscore)

            parent = self.post.parent()
            if cfg.DEBUG: print("parent: " + format(parent.id))
            if scr.alreadyScored(parent):
                return(cfg.alreadyPlayed)

            author = parent.author.name
            if not cfg.DEBUG and self.post.author == author:
                return(cfg.selfPlayed)
            scr.markScored(parent)
            return(scr.playBingo(self.post, self.getText(parent)))

    def checkPost(self) -> None:
        """ Check a post for the invocation keyword. """

        if cfg.DEBUG: print("comment: " + format(self.post))
        elif not cfg.HOSTED: print(".", end="", flush=True)

        # Check for triggers.
        result = self.scanComment()
        if result is not None:
            self.dstore.writeScored(cfg.already_scored)
            self.postReply(result)

        # Traverse comment forest (trees.)
        replies = self.post.replies
        for reply in replies:
            subcomment = self.r.comment(reply)
            subcomment.refresh()
            c = Comment(self.dstore, self.r, subcomment)
            c.checkPost()
