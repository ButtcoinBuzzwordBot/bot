import os
import getopt
import pickle
import sqlite3
#import PyMySQL

import config as cfg

def executeStmt (cur, stmt) -> None:
    """ Executes an SQL statement. """

    try:
        cur.execute(stmt)
    except sqlite3.Error as err:
        #except (sqlite3.Error, mysql.connector.Error) as err:
        print(err)
        exit()
    except:
        print("ERROR: executing " + stmt)
        exit()

def dbClose(store, cur) -> None:
    """ Closes the open cursor, commits and closes database. """

    cur.close()
    store.commit()
    store.close()
            
def importHighscores (store, table) -> None:
    """ Reads the highscore pickle and updates database. """

    name = table + ".txt"
    if os.path.isfile(name):
        with open(name, "rb") as f:
            hs = pickle.load(f)
    else:
        print("ERROR: highscores pickle " + name + " not found.")
        exit()

    cur = store.cursor()
    executeStmt(cur, "DELETE FROM " + table)
    for score, name, url in hs:
        if cfg.DEBUG: print(score,name,url)
        stmt = ("INSERT INTO " + table + " VALUES (" + str(score) + ", '" + name +
                "', '" + url + "')")
        executeStmt(cur, stmt)

    print("Imported " + table + ".")
    dbClose(store, cur)
    exit()
    
def importScored (store, table) -> None:
    """ Reads the scored file and updates database. """

    name = table + ".txt"
    try:
        scoredf = open(name, "r")
        scored = scoredf.read().splitlines()
    except FileNotFoundError:
        print("ERROR: Cannot find " + name)
        exit()
    scoredf.close()

    cur = store.cursor()
    for comment in scored:
        stmt = ("INSERT INTO " + table + " VALUES ('" + comment + "')")
        executeStmt(cur, stmt)

    print("Imported " + table + ".")
    dbClose(store, cur)
    exit()
    
def processOpts (store, argv) -> None:
    """ Check optional arguments to import text files into database. """

    OPTIONS = [
        ["import", "file"],
    ]

    if store == "file":
        print("Importing from files requires a database store.")
        exit()

    # Prepare options data and usage info.
    opts, usage = [],[]
    for opt,arg in OPTIONS:
        syntax = "--" + opt
        if arg is not "":
            syntax += " <" + arg + ">"
            opt += "="
        opts.append(opt)
        usage.append(syntax)

    # Process command line options.
    try:
        [(option, file)] = getopt.getopt(argv[1:], "", opts)[0]
    except getopt.GetoptError:
        name = os.path.basename(__file__)
        print("Usage: " + name + " [", end="")
        print("|".join(usage) + "]")
        print("    where <file> = words|phrases|scored|highscores|koans|haiku")
        exit(2)

    if file == "highscores":
        importHighscores(store, file)
    elif file == "scored":
        importScored(store, file)

    # Check if options active.
    table = argv[2]
    if table == "koans":
        try:
            cfg.CMD_KOAN
        except NameError:
            print("Koans are disabled. Please set CMD_KOAN to use.")
            exit()
    elif table == "haiku":
        try:
            cfg.CMD_HAIKU
        except NameError:
            print("Haiku are disabled. Please set CMD_HAIKU to use.")
            exit()

    dataf = open(table + ".txt", "r")
    rawdata = dataf.read()
    dataf.close()
    if table == "words" or table == "phrases":
        data = rawdata.splitlines()
    else:
        data = rawdata.split("|")

    cur = store.cursor()
    for line in data:
        if cfg.DEBUG: print("Adding: " + line)
        executeStmt(cur, "INSERT INTO " + table + " VALUES ('" + line + "')")
    dbClose(store, cur)
    print("Imported " + str(len(data)) + " lines into " + table)
    exit()
