def processOpts(argv):
    """ Check optional arguments to import text files into database. """

    global store

    OPTIONS = [
        ["import", "file"],
        ["import-koans", "file"],
        ["import-haiku", "file"]
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
            CMD_KOAN
        except NameError:
            print("Koans are disabled. Please set CMD_KOAN to use.")
            exit()
    elif table == "haiku":
        try:
            CMD_HAIKU
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
        if DEBUG:
            print("Adding: " + line)
        if table == "haiku":
            line = line.replace("\n", "  \n")
        stmt = "INSERT INTO " + table + " VALUES ('" + line + "')"
        try:
            cur.execute(stmt)
        except sqlite3.Error as err:
            #except (sqlite3.Error, mysql.connector.Error) as err:
            print(err)
            print("Likely duplicate entry '" + line + "' into " + table)
            exit()
    cur.close()
    store.commit()
    store.close()
    print("Imported " + str(len(data)) + " lines imported into " + table)
    exit()
