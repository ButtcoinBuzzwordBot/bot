import os, pickle
import sqlite3
# TODO: import PyMySQL as mysql
# TODO: test file support after rewrite, globs to config file.

import config as cfg, scoring as scr

class DataStore:

    def __init__ (self, stype=None):
        self.stype = stype
        create_db = False

        if self.stype is "sqlite":
            database = "buzzword.db"
            if not os.path.isfile(database):
                create_db = True
            try:
                self.store = sqlite3.connect(database)
            except sqlite3.Error as err:
                print(err)
                print("\nERROR: Cannot create or connect to " + cfg.DATABASE)
                exit()

        elif self.stype is "mysql":
            print("nope")
            exit()
            # TODO: Why isn't this module being found?
            #import PyMySQL as mysql
            database = "buzzword"
            try:
                self.store = mysql.connector.connect(
                    user=cfg.MYSQL_USER, password=cfg.MYSQL_PW, host=cfg.MYSQL_HOST,
                    database=database)
            except mysql.connector.Error as err:
                if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                    print(err)
                    print("ERROR: Bad username or password for " + DATABASE)
                elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                    create_db = True
                else:
                    print(err)
        else:
            print("\nERROR: Unknown store type. Check settings.")
            exit()

        if create_db:
            self.createDB()
            print("Database created. Please import word/phrases before running.")
            exit()

    def executeStmt(self, stmt) -> None:
        """ Executes an atomic database operation. """
        
        try:
            cur = self.store.cursor()
            cur.execute(stmt)
        except sqlite3.Error as err:
            # TODO: except (sqlite3.Error, mysql.connector.Error) as err:
            print("\n")
            print(err)
            print("ERROR: Cannot execute " + stmt)
            exit()
        finally:
            cur.close()

    def fetchStmt(self, stmt) -> list:
        """ Executes a SELECT statement and returns fetched results. """

        try:
            cur = self.store.cursor()
            cur.execute("SELECT "+ stmt)
            data = cur.fetchall()
            cur.close()
            return(data)
        except sqlite3.Error as err:
            # TODO: except (sqlite3.Error, mysql.connector.Error) as err:
            print("\n"+ err)
            print("ERROR: Cannot execute SELECT " + stmt)
            exit()

    def closeDB(self) -> None:
        """ Commits and closes database. """

        self.store.commit()
        self.store.close()

    def createDB(self) -> None:
        """ Create the database and tables. """

        stmts = [
            "CREATE TABLE "+ cfg.WORD_STORE +" (word VARCHAR(64) UNIQUE NOT NULL)",
            "CREATE TABLE "+ cfg.PHRASE_STORE +" (phrase VARCHAR(255) UNIQUE NOT NULL)",
            "CREATE TABLE "+ cfg.SCORED_STORE +" (scored VARCHAR(16) NOT NULL)",
            "CREATE TABLE "+ cfg.SCORE_STORE +" (score int)",
            "INSERT INTO "+ cfg.SCORE_STORE +" VALUES ("+ str(cfg.MIN_MATCHES) +")",
            ("CREATE TABLE "+ cfg.HIGHSCORES_STORE + " (score int NOT NULL, " +
             "name VARCHAR(32) NOT NULL, url VARCHAR(256) NOT NULL)")
        ]
    
        for stmt in stmts:
            self.executeStmt(stmt)
        self.store.commit()

    def readData(self, name) -> list:
        """ Read words or phrases data. """

        if self.stype is "file":
            name += ".txt"
            try:
                dataf = open(name, "r")
            except:
                print("\nERROR: File " + name + " does not exist.")
                exit()
            data = dataf.read().splitlines()
            dataf.close()

        elif self.stype is "sqlite" or self.stype is "mysql":
            self.store.row_factory = lambda cursor, row: row[0]
            data = self.fetchStmt(" * FROM " + name)
            if len(data) == 0:
                print("Empty " + name + " list. Please import first.")
                exit()
            
        return(data)

    def readScore(self) -> int:
        """ Returns the current score to win. """

        if self.stype is "file":
            try:
                scoref = open(cfg.SCORE_STORE + ".txt", "r")
                score = int(scoref.readline())
            except FileNotFoundError:
                score = cfg.MIN_SCORE
                scoref = open(cfg.SCORE_STORE + ".txt", "w")
                scoref.write(str(score))
            scoref.close()
            return(score)

        elif self.stype is "sqlite" or self.stype is "mysql":
            self.store.row_factory = lambda cursor, row: row[0]
            return (int(self.fetchStmt(" score FROM " + cfg.SCORE_STORE)[0]))

    def writeScore(self, score) -> None:
        """ Saves the current score to win. """

        if self.stype is "file":
            name = cfg.SCORE_STORE + ".txt"
            try:
                scoref = open(name, "w")
                scoref.write(score)
            except:
                print("\nERROR: Can't write scores to " + name)
            scoref.close()

        elif self.stype is "sqlite" or self.stype is "mysql":
            self.executeStmt("UPDATE " + cfg.SCORE_STORE + " SET score=" + score)
            self.store.commit()

    def readScored(self) -> list:
        """ Reads list of posts already scored/replied to. """

        if self.stype is "file":
            name = cfg.SCORED_STORE + ".txt"
            try:
                scoredf = open(name, "r")
                scored = scoredf.read().splitlines()
            except FileNotFoundError:
                scoredf = open(name, "w")
                scored = []
            scoredf.close()
            return(scored)

        elif self.stype is "sqlite" or self.stype is "mysql":
            self.store.row_factory = lambda cursor, row: row[0]
            return (self.fetchStmt(" * FROM "+ cfg.SCORED_STORE))

    def writeScored(self, scored) -> list:
        """ Saves list of posts already scored/replied to. """
    
        length = len(scored)
        if length > cfg.MAX_SCORED:
            scored = scored[length - cfg.MAX_SCORED:length]

            if self.stype is "file":
                name = cfg.SCORED_STORE + ".txt"
            try:
                scoredf = open(name, "w")
            except:
                print("\nERROR: Cannot write to " + name)
                exit()
            scoredf.writelines(("\n".join(scored)) + "\n")
            scoredf.close()

        elif self.stype is "sqlite" or self.stype is "mysql":
            self.executeStmt("DELETE FROM " + cfg.SCORED_STORE)
            for s in scored:
                self.executeStmt("INSERT INTO "+ cfg.SCORED_STORE +" VALUES ('"+ s +"')")
            self.store.commit()

    def readHighscores(self) -> list:
        """ Retrieves list of highscores. """

        hs = []
        if self.stype is "file":
            name = cfg.HIGHSCORES_STORE + ".txt"
            if os.path.isfile(name):
                with open(name, "rb") as f:
                    hs = pickle.load(f)
            else:
                hs = scr.newHighscores()
                with open(name, "wb") as f:
                    pickle.dump(hs, f)
            f.close()

        elif self.stype is "sqlite" or self.stype is "mysql":
            self.store.row_factory = None
            hs = self.fetchStmt(" score,name,url FROM " + cfg.HIGHSCORES_STORE)
            if len(hs) < 1:
                hs = scr.newHighscores()

        hs.sort(key = lambda x: x[0], reverse = True)
        return(hs)

    def writeHighscores(self, hs) -> None:
        """ Stores list of highscores. """

        if self.stype is "file":
            name = cfg.HIGHSCORES_STORE + ".txt"
            try:
                with open(name, "wb") as f:
                    pickle.dump(hs, f)
            except:
                print("\nERROR: Cannot write to file " + name)
            f.close()

        elif self.stype is "sqlite" or self.type is "mysql":
            self.executeStmt("DELETE FROM "+ cfg.HIGHSCORES_STORE)
            for score, name, url in hs:
                stmt = ("INSERT INTO "+ cfg.HIGHSCORES_STORE +" VALUES ("+ str(score) +
                        ", '"+ name +"', '"+ url +"')")
                self.executeStmt(stmt)
