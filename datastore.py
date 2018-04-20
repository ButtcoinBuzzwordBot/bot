import os, pickle

import config as cfg

if cfg.STORE_TYPE is "sqlite":
    import sqlite3
elif cfg.STORE_TYPE is "mysql":
    import pymysql as mysql
else:
    raise cfg.ExitException("ERROR: store type not supported.")

import scoring as scr

class DataStore:
    """ Database class. Supports SQLite and MySQL. """

    def __init__(self, dbtype=None):
        self.dbtype = dbtype
        create_db = False

        if self.dbtype is "sqlite":
            database = cfg.DATABASE + ".db"
            if not os.path.isfile(database):
                create_db = True
            try:
                self.store = sqlite3.connect(database)
            except sqlite3.Error as err:
                raise cfg.ExitException(err
                                        + "\nERROR: Cannot create or connect to "
                                        + cfg.DATABASE)
            self.store.row_factory = lambda cursor, row: row[0]

        elif self.dbtype is "mysql":
            try:
                self.store = mysql.connect(host=cfg.MYSQL_HOST,
                                           user=cfg.MYSQL_USER,
                                           password=cfg.MYSQL_PW,
                                           db=cfg.DATABASE,
                                           charset='utf8')
            except mysql.Error as err:
                raise cfg.ExitException(
                    err + "\nERROR: Cannot create or connect to "+ cfg.DATABASE)

            self.store.row_factory = lambda cursor, row: row[0]
            cur = self.store.cursor()
            cur.execute("SHOW TABLES LIKE '"+ cfg.SCORED_STORE +"'")
            result = cur.fetchone()
            if result is None:
                dbexists = False
            cur.close()

        else:
            raise cfg.ExitException("Database type "+ dbtype +" not supported.")

        if create_db:
            self.createDB()
            print("Database created. Please import word/phrases before running.")
            exit()

    def executeStmt(self, stmt) -> None:
        """ Executes an atomic database operation. """

        try:
            cur = self.store.cursor()
            cur.execute(stmt)
        except Exception as err:
            raise cfg.ExitException(err + "\nERROR: Cannot execute " + stmt)
        finally:
            cur.close()

    def fetchStmt(self, stmt) -> list:
        """ Executes a SELECT statement and returns fetched results. """

        try:
            cur = self.store.cursor()
            cur.execute("SELECT "+ stmt)
            data = cur.fetchall()
        except Exception as err:
            raise cfg.ExitException(err + "\nERROR: Cannot execute SELECT " + stmt)
        finally:
            cur.close()
        return(data)

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

    def deleteTable(self, table) -> None:
        """ Deletes all entries from a table. """

        if self.dbtype is "sqlite" or self.dbtype is "mysql":
            try:
                cur = self.store.cursor()
                cur.execute("DELETE FROM "+ table)
            except:
                return
            finally:
                cur.close()

    def readData(self, name) -> list:
        """ Read words or phrases data. """

        if self.dbtype is "file":
            name += ".txt"
            try:
                dataf = open(name, "r")
            except:
                print("\nERROR: File " + name + " does not exist.")
                exit()
            data = dataf.read().splitlines()
            dataf.close()

        elif self.dbtype is "sqlite" or self.dbtype is "mysql":
            data = self.fetchStmt(" * FROM " + name)
            if len(data) == 0:
                print("Empty " + name + " list. Please import first.")
                exit()
            
        return(data)

    def readScore(self) -> int:
        """ Returns the current score to win. """

        if self.dbtype is "file":
            try:
                scoref = open(cfg.SCORE_STORE + ".txt", "r")
                score = int(scoref.readline())
            except FileNotFoundError:
                score = cfg.MIN_SCORE
                scoref = open(cfg.SCORE_STORE + ".txt", "w")
                scoref.write(str(score))
            finally:
                scoref.close()
            return(score)

        elif self.dbtype is "sqlite" or self.dbtype is "mysql":
            return (int(self.fetchStmt(" score FROM " + cfg.SCORE_STORE)[0]))

    def writeScore(self, score) -> None:
        """ Saves the current score to win. """

        if self.dbtype is "file":
            name = cfg.SCORE_STORE + ".txt"
            try:
                scoref = open(name, "w")
                scoref.write(score)
            except:
                raise cfg.ExitException("\nERROR: Can't write scores to " + name)
            finally:
                scoref.close()

        elif self.dbtype is "sqlite" or self.dbtype is "mysql":
            self.executeStmt("UPDATE " + cfg.SCORE_STORE + " SET score=" + score)
            self.store.commit()

    def readScored(self) -> list:
        """ Reads list of posts already scored/replied to. """

        if self.dbtype is "file":
            name = cfg.SCORED_STORE + ".txt"
            try:
                scoredf = open(name, "r")
                scored = scoredf.read().splitlines()
            except FileNotFoundError:
                scoredf = open(name, "w")
                scored = []
            finally:
                scoredf.close()
            return(scored)

        elif self.dbtype is "sqlite" or self.dbtype is "mysql":
            return (self.fetchStmt(" * FROM "+ cfg.SCORED_STORE))

    def writeScored(self, scored) -> list:
        """ Saves list of posts already scored/replied to. """
    
        length = len(scored)
        if length > cfg.MAX_SCORED:
            scored = scored[length - cfg.MAX_SCORED:length]

            if self.dbtype is "file":
                name = cfg.SCORED_STORE + ".txt"
            try:
                scoredf = open(name, "w")
            except:
                raise cfg.ExitException("\nERROR: Cannot write to " + name)
            scoredf.writelines(("\n".join(scored)) + "\n")
            scoredf.close()

        elif self.dbtype is "sqlite" or self.dbtype is "mysql":
            self.executeStmt("DELETE FROM " + cfg.SCORED_STORE)
            for s in scored:
                self.executeStmt("INSERT INTO "+ cfg.SCORED_STORE +" VALUES ('"+ s +"')")
            self.store.commit()

    def readHighscores(self) -> list:
        """ Retrieves list of highscores. """

        hs = []
        if self.dbtype is "file":
            name = cfg.HIGHSCORES_STORE + ".txt"
            if os.path.isfile(name):
                with open(name, "rb") as f:
                    hs = pickle.load(f)
            else:
                hs = scr.newHighscores()
                with open(name, "wb") as f:
                    pickle.dump(hs, f)
            f.close()

        elif self.dbtype is "sqlite" or self.dbtype is "mysql":
            hs = self.fetchStmt(" score,name,url FROM " + cfg.HIGHSCORES_STORE)
            if len(hs) < 1:
                hs = scr.newHighscores()

        hs.sort(key = lambda x: x[0], reverse = True)
        return(hs)

    def writeHighscores(self, hs) -> None:
        """ Stores list of highscores. """

        if self.dbtype is "file":
            name = cfg.HIGHSCORES_STORE + ".txt"
            try:
                with open(name, "wb") as f:
                    pickle.dump(hs, f)
            except:
                raise cfg.ExitException("\nERROR: Cannot write to file " + name)
            finally:
                f.close()

        elif self.dbtype is "sqlite" or self.dbtype is "mysql":
            self.executeStmt("DELETE FROM "+ cfg.HIGHSCORES_STORE)
            for score, name, url in hs:
                stmt = ("INSERT INTO "+ cfg.HIGHSCORES_STORE +" VALUES ("+ str(score) +
                        ", '"+ name +"', '"+ url +"')")
                self.executeStmt(stmt)
