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
    
    stmts = [
        "CREATE TABLE " + WORD_STORE + " (word VARCHAR(64) UNIQUE NOT NULL)",
        "CREATE TABLE " + PHRASE_STORE + " (phrase VARCHAR(255) UNIQUE NOT NULL)",
        "CREATE TABLE " + SCORED_STORE + " (scored VARCHAR(16) NOT NULL)",
        "CREATE TABLE " + SCORE_STORE + " (score int)",
        "INSERT INTO " + SCORE_STORE + " VALUES (" + str(MIN_MATCHES) + ")",
        ("CREATE TABLE " + HIGHSCORES_STORE +
         " (score int NOT NULL, name VARCHAR(32) NOT NULL)")
    ]
    
    try:
        for stmt in stmts:
            cur.execute(stmt)
    except (sqlite3.Error, mysql.connector.Error) as err:
        print(err)
        print("ERROR: Cannot create tables in " + DATABASE)
        exit()

    highscores = []
    for i in range (0,3):
        highscores.append((i + 1, "/u/" + AUTHOR))
        stmt = (
            "INSERT INTO " + HIGHSCORES_STORE +
            " VALUES (" + str(i + 1) + ", '/u/" + AUTHOR + "')"
        )
        try:
            cur.execute(stmt)
        except:
            print("ERROR: Cannot populate " + HIGHSCORES_STORE + " table.")
            exit()
    store.commit()
    cur.close()

def readData(*args: "store_type, file|table_name") -> list:
    """ Reads words or phrases data. """

    if args[0] is "file":
        name = args[1] + ".txt"
        try:
            dataf = open(name, "r")
        except:
            print("ERROR: File " + name + " does not exist.")
            exit()
        words  = dataf.read().splitlines()
        dataf.close()
        return(words)

    elif type(args[0]) is sqlite3.Connection:
        try:
            store.row_factory = lambda cursor, row: row[0]
            cur = store.cursor()
            cur.execute("SELECT * FROM " + args[1])
            return(cur.fetchall())
        except sqlite3.Error (err):
            print("ERROR: Cannot retrieve " + args[1] + "s from db.")
            exit()

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
            store.row_factory = lambda cursor, row: row[0]
            cur = store.cursor()
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

    elif type(store) is sqlite3.Connection:
        try:
            cur = store.cursor()
            cur.execute("UPDATE " + args[1] + " SET score=" + score)
        except sqlite3.Error:
            print("ERROR: Cannot update score in db.")
            exit()
        store.commit()

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
            store.row_factory = lambda cursor, row: row[0]
            cur = store.cursor()
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
            cur = store.cursor()
            cur.execute("DELETE FROM " + args[1])
            for scored in already_scored:
                stmt = "INSERT INTO " + args[1] + " VALUES ('" + scored + "')"
                cur.execute(stmt)
        except sqlite3.Error:
            print("ERROR: Cannot write to " + args[1] + " table.")
            exit()
        store.commit()

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
                highscores.append((i + 1, "/u/" + author))
            with open(name, "wb") as f:
                pickle.dump(highscores, f)
        f.close()
        return(highscores)

    elif type(args[0]) is sqlite3.Connection:
        try:
            store.row_factory = None
            cur = store.cursor()
            cur.execute("SELECT score,name FROM " + args[1])
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
            cur = store.cursor()
            cur.execute("DELETE FROM " + args[1])
            for score, name in args[2]:
                stmt = (
                    "INSERT INTO " + args[1] + " VALUES (" + str(score) +
                    ", '" + name + "')"
                )
                cur.execute(stmt)
        except sqlite3.Error:
            print("ERROR: Cannot write to " + args[1] + " table.")
            exit()
        store.commit()
