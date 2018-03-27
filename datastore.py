import sqlite3
#import PyMySQL as mysql

def createDB(*args):
    """ Create the database and tables. """

    store = args[0]
    cur = store.cursor()
    dbtype = args[1]
    DATABASE = args[2]
    WORD_STORE = args[3]
    PHRASE_STORE = args[4]
    SCORED_STORE = args[5]
    SCORE_STORE = args[6]
    MIN_MATCHES = args[7]
    HIGHSCORES_STORE = args[8]
    KOAN_STORE = args[9]
    HAIKU_STORE = args[10]
    
    stmts = [
        "CREATE TABLE " + WORD_STORE + " (word VARCHAR(64) UNIQUE NOT NULL)",
        "CREATE TABLE " + PHRASE_STORE + " (phrase VARCHAR(255) UNIQUE NOT NULL)",
        "CREATE TABLE " + SCORED_STORE + " (scored VARCHAR(16) NOT NULL)",
        "CREATE TABLE " + SCORE_STORE + " (score int)",
        "INSERT INTO " + SCORE_STORE + " VALUES (" + str(MIN_MATCHES) + ")",
        ("CREATE TABLE " + HIGHSCORES_STORE +
         " (score int NOT NULL, name VARCHAR(32) NOT NULL, url VARCHAR(256) NOT NULL)"),
        "CREATE TABLE " + KOAN_STORE + " (koan TEXT NOT NULL)",
        "CREATE TABLE " + HAIKU_STORE + " (haiku TEXT NOT NULL)"
    ]
    
    try:
        for stmt in stmts:
            cur.execute(stmt)
    #except (sqlite3.Error, mysql.connector.Error) as err:
    except:
        print(err)
        print("ERROR: Cannot create tables in " + DATABASE)
        exit()
    finally:
        cur.close()
    store.commit()

def readData(*args):
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

def readRandom(*args):
    """ Gets a random row from a table. """

    if args[0] is "file":
        print("Not implemented yet.")

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
        
def readScore(*args: "store_name, file|table_name, default_score") -> int:
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

def writeScore(*args) -> None:
    """ Saves the current score to win. """

    score = str(args[2])
    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            scoref = open(name, "w")
            scoref.write(score)
        except:
            print("ERROR: Can't write " + name)
        scoref.close()

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = args[0].cursor()
            cur.execute("UPDATE " + args[1] + " SET score=" + score)
        except sqlite3.Error:
            print("ERROR: Cannot update score in db.")
            exit()
        args[0].commit()

def readScored(*args) -> list:
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

def writeScored(*args: "store_type, file|table_name, max_score, already_scored[]"):
    """ Saves list of posts already scored/replied to. """
    
    maxscored = args[2]
    already_scored = args[3]
    length = len(already_scored)
    if length > maxscored:
        already_scored = already_scored[length - maxscored, length]

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            scoredf = open(name, "w")
        except:
            print("ERROR: Cannot write to " + name)
            exit()
        scoredf.writelines(("\n".join(already_scored)) + "\n")
        scoredf.close()

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = args[0].cursor()
            cur.execute("DELETE FROM " + args[1])
            for scored in already_scored:
                stmt = "INSERT INTO " + args[1] + " VALUES ('" + scored + "')"
                cur.execute(stmt)
        except sqlite3.Error:
            print("ERROR: Cannot write to " + args[1] + " table.")
            exit()
        args[0].commit()

def readHighscores(*args: "store_type, file|table_name, author") -> list:
    """ Retrieves list of highscores. """

    highscores = []
    author = args[2]
    if args[0] is "file":
        name = args[1] + ".txt"
        if os.path.isfile(name):
            with open(name, "rb") as f:
                highscores = pickle.load(f)
        else:
            for i in range (0,3):
                highscores.append((i + 1, "/u/" + author), "/u/" + author)
            with open(name, "wb") as f:
                pickle.dump(highscores, f)
        f.close()
        return(highscores)

    elif type(args[0]) is sqlite3.Connection:
        try:
            args[0].row_factory = None
            cur = args[0].cursor()
            cur.execute("SELECT score,name,url FROM " + args[1])
            return(cur.fetchall())
        except sqlite3.Error:
            print("ERROR: Cannot read scored comments from " + args[1])
            exit()

def writeHighscores(*args) -> None:
    """ Stores list of highscores. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            with open(name, "wb") as f:
                pickle.dump(args[2], f)
        except:
            print("ERROR: Cannot write to file " + name)
        f.close()

    elif type(args[0]) is sqlite3.Connection:
        try:
            cur = args[0].cursor()
            cur.execute("DELETE FROM " + args[1])
            for score, name, url in args[2]:
                stmt = (
                    "INSERT INTO " + args[1] + " VALUES (" + str(score) +
                    ", '" + name + "', '" + url + "')"
                )
                cur.execute(stmt)
        except sqlite3.Error:
            print("ERROR: Cannot write to " + args[1] + " table.")
            exit()
        args[0].commit()
