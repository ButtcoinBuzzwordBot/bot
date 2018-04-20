import os
import praw
import config as cfg

def auth():

    # Reddit account and API OAuth information. You can hardcode values here but
    # it creates a security risk if your code is public (on Github, etc.)
    # Otherwise, set the environment variables on your host as below.
    cfg.PASSWORD = os.environ['REDDIT_PASSWORD']
    cfg.CLIENT_ID = os.environ['CLIENT_ID']
    cfg.CLIENT_SECRET = os.environ['CLIENT_SECRET']

    # Initialize PRAW with custom User-Agent.
    if cfg.DEBUG:
        #cfg.SUBREDDIT = "testingground4bots"
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
    return(r)
