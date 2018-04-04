import os
import getopt
import pickle
import sqlite3
#import PyMySQL

import config as cfg

def importHighscores (dstore, table) -> None:
    """ Reads the highscore pickle and updates database. """

    name = table + ".txt"
    if os.path.isfile(name):
        with open(name, "rb") as f:
            hs = pickle.load(f)
    else:
        print("\nERROR: highscores pickle " + name + " not found.")
        exit()

    dstore.executeStmt("DELETE FROM " + table)
    for score, name, url in hs:
        if cfg.DEBUG: print(score,name,url)
        stmt = ("INSERT INTO " + table + " VALUES (" + str(score) + ", '" + name +
                "', '" + url + "')")
        dstore.executeStmt(stmt)

    print("Imported " + table + ".")
    dstore.closeDB()
    exit()
    
def importScored (dstore, table) -> None:
    """ Reads the scored file and updates database. """

    name = table + ".txt"
    try:
        scoredf = open(name, "r")
        scored = scoredf.read().splitlines()
    except FileNotFoundError:
        print("ERROR: Cannot find " + name)
        exit()
    scoredf.close()

    for comment in scored:
        stmt = ("INSERT INTO " + table + " VALUES ('" + comment + "')")
        dstore.executeStmt(stmt)

    print("Imported " + table + ".")
    dstore.closeDB()
    exit()
    
def processOpts (dstore, argv) -> None:
    """ Check optional arguments to import text files into database. """

    OPTIONS = [
        ["import", "file"],
    ]

    if dstore.stype is not "sqlite" and dstore.stype is not "mysql":
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
    dataf = open(table + ".txt", "r")
    data = dataf.read().splitlines()
    dataf.close()

    for line in data:
        if cfg.DEBUG: print("Adding: " + line)
        dstore.executeStmt("INSERT INTO " + table + " VALUES ('" + line + "')")

    dstore.closeDB()
    print("Imported " + str(len(data)) + " lines into " + table)
    exit()
