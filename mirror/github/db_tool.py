import sqlite3
import traceback


def create_snippets_table(conn):
    """create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    sql_create_snippets_table = """ CREATE TABLE IF NOT EXISTS snippets (
                                        id integer PRIMARY KEY,
                                        snippet text NOT NULL,
                                        language text NOT NULL,
                                        repo_file_name text,
                                        github_repo_url text,
                                        license text,
                                        commit_hash text,
                                        starting_line_number integer
                                    ); """

    try:
        c = conn.cursor()
        c.execute(sql_create_snippets_table)
        conn.commit()
    except Exception as e:
        traceback.print_exc()


def create_connection(db_file):
    """create a database connection to the SQLite database
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


def write_snippet_to_db(conn, **kwargs):
    table = "snippets"
    fields = kwargs.keys()

    sql = sql = (
        f"INSERT OR IGNORE INTO {table} "
        f" ({','.join(fields)}) "
        f"VALUES({ ','.join(['?']*len(fields)) });"
    )
    try:
        c = conn.cursor()
        result = c.execute(sql, tuple(kwargs.values()))
        conn.commit()
        return result
    except Exception as err:
        for key, value in kwargs.items():
            print(key, type(value))
        traceback.print_exc()
