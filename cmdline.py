import os
import getopt
import sqlite3

import config as cfg

def processOpts(store, argv):
    """ Check optional arguments to import text files into database. """

    OPTIONS = [
        ["import", "file"],
    ]

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
        exit(2)

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
        if table == "haiku":
            line = line.replace("\n", "  \n")
        elif table == "koans":
            line = line.replace("&nbsp;", "  \n&nbsp;  \n")
        stmt = "INSERT INTO " + table + " VALUES ('" + line + "')"
        try:
            cur.execute(stmt)
        except sqlite3.Error as err:
            #except (sqlite3.Error, mysql.connector.Error) as err:
            print(err)
            print("Possible duplicate entry '" + line + "' into " + table)
            exit()
    cur.close()
    store.commit()
    store.close()
    print("Imported " + str(len(data)) + " lines imported into " + table)
    exit()
