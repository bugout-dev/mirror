import sqlite3
import traceback

#database = r"C:\sqlite\db\pythonsqlite.db"




def create_table_tasks(conn):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    sql_create_snipets_table = """ CREATE TABLE IF NOT EXISTS snipets (
                                        id integer PRIMARY KEY,
                                        snipet text NOT NULL,
                                        lang text
                                    ); """


    try:
        c = conn.cursor()
        c.execute(sql_create_snipets_table)
        conn.commit()
    except Exception as e:
        traceback.print_exc()


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        return conn
    except Exception as e:
        traceback.print_exc()

    return conn

def write_snipet_to_db(conn, snipet, lang):
    sql = """
            INSERT OR IGNORE INTO snipets (snipet,lang) VALUES(?,?);
          """
    try:
        c = conn.cursor()
        result = c.execute(sql,(snipet, lang))
        conn.commit()
        return result
    except Exception as err:
        traceback.print_exc()   