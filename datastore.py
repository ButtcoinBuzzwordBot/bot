import os
import random
import pickle
import sqlite3
# TODO: import PyMySQL as mysql
# TODO: test file support after rewrite, globs to config file.

import config as cfg
import scoring as scr

def createDB(*args: "store, store_type") -> None:
    """ Create the database and tables. """

    store = args[0]
    cur = store.cursor()
    dbtype = args[1]
    
    stmts = [
        "CREATE TABLE " + cfg.WORD_STORE + " (word VARCHAR(64) UNIQUE NOT NULL)",
        "CREATE TABLE " + cfg.PHRASE_STORE + " (phrase VARCHAR(255) UNIQUE NOT NULL)",
        "CREATE TABLE " + cfg.SCORED_STORE + " (scored VARCHAR(16) NOT NULL)",
        "CREATE TABLE " + cfg.SCORE_STORE + " (score int)",
        "INSERT INTO " + cfg.SCORE_STORE + " VALUES (" + str(cfg.MIN_MATCHES) + ")",
        ("CREATE TABLE " + cfg.HIGHSCORES_STORE +
         " (score int NOT NULL, name VARCHAR(32) NOT NULL, url VARCHAR(256) NOT NULL)"),
        "CREATE TABLE " + cfg.KOAN_STORE + " (koan TEXT NOT NULL)",
        "CREATE TABLE " + cfg.HAIKU_STORE + " (haiku TEXT NOT NULL)"
    ]
    
    try:
        for stmt in stmts:
            cur.execute(stmt)
    # TODO: except (sqlite3.Error, mysql.connector.Error) as err:
    except sqlite3.Error:
        print(err)
        print("ERROR: Cannot create tables in " + cfg.DATABASE)
        exit()
    finally:
        cur.close()
    store.commit()

def readData(*args: "store, file|table") -> list:
    """ Read words or phrases data. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            dataf = open(name, "r")
        except:
            print("ERROR: File " + name + " does not exist.")
        words  = dataf.read().splitlines()
        dataf.close()

    elif type(args[0]) is sqlite3.Connection:
        args[0].row_factory = lambda cursor, row: row[0]
        cur = args[0].cursor()
        try:
            cur.execute("SELECT * FROM " + args[1])
            words = cur.fetchall()
        except sqlite3.Error:
            print("ERROR: Cannot retrieve " + args[1] + " from db.")
        finally:
            cur.close()

    if len(words) == 0:
        raise Exception("Empty " + args[1] + " list. Please import first.")
    return(words)

def readRandom(*args: "store, file|table") -> str:
    """ Gets a random row from a table. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            randf = open(name, "r")
            rand = randf.read().split("|")
            return(rand[random.randrange(0, len(rand))])
        except FileNotFoundError:
            print("ERROR: Not implemented yet.")

    elif type(args[0]) is sqlite3.Connection:
        args[0].row_factory = None
        cur = args[0].cursor()
        try:
            cur.execute("SELECT * FROM " + args[1] + " ORDER BY RANDOM() LIMIT 1")
            data = cur.fetchall()
            if data is None:
                print("ERROR: Please import " + args[1] + " into database.")
                exit()
            return(data[0][0])
        except sqlite3.Error:
            print("ERROR: Cannot retrieve " + args[1] + " from db.")
        finally:
            cur.close()
        
def readScore(*args: "store, file|table, default_score") -> int:
    """ Returns the current score to win. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            scoref = open(name, "r")
            score = int(scoref.readline())
        except FileNotFoundError:
            scoref = open(name, "w")
            score = args[2]
            scoref.write(str(score))
        scoref.close()
        return(score)

    elif type(args[0]) is sqlite3.Connection:
        try:
            args[0].row_factory = lambda cursor, row: row[0]
            cur = args[0].cursor()
            cur.execute("SELECT score FROM " + args[1])
            score = cur.fetchone()
            return(int(score))
        except sqlite3.Error:
            print("ERROR: Cannot retrieve score from db.")
            exit()

def writeScore(*args: "store, file|table") -> None:
    """ Saves the current score to win. """

    score = str(cfg.MATCHES)
    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            scoref = open(name, "w")
            scoref.write(score)
        except:
            print("ERROR: Can't write scores to " + name)
        scoref.close()

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = args[0].cursor()
            cur.execute("UPDATE " + args[1] + " SET score=" + score)
        except sqlite3.Error:
            print("ERROR: Cannot update " + args[1] + " in db.")
            exit()
        args[0].commit()

def readScored(*args: "store, file|table") -> list:
    """ Reads list of posts already scored/replied to. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            scoredf = open(name, "r")
            scored = scoredf.read().splitlines()
        except FileNotFoundError:
            scoredf = open(name, "w")
            scored = []
        scoredf.close()
        return(scored)

    elif type(args[0]) is sqlite3.Connection:
        try:
            args[0].row_factory = lambda cursor, row: row[0]
            cur = args[0].cursor()
            cur.execute("SELECT * FROM " + args[1])
            return(cur.fetchall())
        except sqlite3.Error:
            print("ERROR: Cannot read scored comments from " + args[1])
            exit()

def writeScored(*args: "store, file|table") -> None:
    """ Saves list of posts already scored/replied to. """
    
    length = len(cfg.already_scored)
    if length > cfg.MAX_MATCHES:
        already_scored = cfg.already_scored[length - cfg.MAX_MATCHES:length]

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            scoredf = open(name, "w")
        except:
            print("ERROR: Cannot write to " + name)
            exit()
        scoredf.writelines(("\n".join(cfg.already_scored)) + "\n")
        scoredf.close()

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = args[0].cursor()
            cur.execute("DELETE FROM " + args[1])
            for scored in cfg.already_scored:
                stmt = "INSERT INTO " + args[1] + " VALUES ('" + scored + "')"
                cur.execute(stmt)
        except sqlite3.Error:
            print("ERROR: Cannot write to " + args[1] + " table.")
            exit()
        args[0].commit()

def readHighscores(*args: "store, file|table, author") -> list:
    """ Retrieves list of highscores. """

    author = args[2]
    if args[0] is "file":
        name = args[1] + ".txt"
        if os.path.isfile(name):
            with open(name, "rb") as f:
                highscores = pickle.load(f)
        else:
            cfg.highscores = scr.newHighscores(cfg.AUTHOR, cfg.SUBREDDIT, author)
            with open(name, "wb") as f:
                pickle.dump(cfg.highscores, f)
        f.close()
        return(cfg.highscores)

    elif type(args[0]) is sqlite3.Connection:
        try:
            args[0].row_factory = None
            cur = args[0].cursor()
            cur.execute("SELECT score,name,url FROM " + args[1])
            return(cur.fetchall())
        except sqlite3.Error:
            print("ERROR: Cannot read highscores from " + args[1])
            exit()

def writeHighscores(*args:"store, file|table") -> None:
    """ Stores list of highscores. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            with open(name, "wb") as f:
                pickle.dump(cfg.highscores, f)
        except:
            print("ERROR: Cannot write to file " + name)
        f.close()

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = args[0].cursor()
            cur.execute("DELETE FROM " + args[1])
            for score, name, url in cfg.highscores:
                stmt = (
                    "INSERT INTO " + args[1] + " VALUES (" + str(score) +
                    ", '" + name + "', '" + url + "')"
                )
                cur.execute(stmt)
        except sqlite3.Error:
            print("ERROR: Cannot write highscores to " + args[1] + " table.")
            exit()
        args[0].commit()
