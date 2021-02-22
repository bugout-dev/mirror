import sqlite3
import traceback


def create_snippets_table(conn):
    """create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    sql_create_snippets_table = """ CREATE TABLE IF NOT EXISTS snippets (
                                        id INTEGER PRIMARY KEY,
                                        snippet TEXT NOT NULL,
                                        language TEXT NOT NULL,
                                        repo_file_name TEXT,
                                        github_repo_url TEXT,
                                        license TEXT,
                                        commit_hash TEXT,
                                        starting_line_number INTEGER,
                                        batch_size INTEGER                                    
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


def write_snippet_to_db(conn, batch):
    table = "snippets"
    fields = [
        "github_repo_url",
        "commit_hash",
        "snippet",
        "license",
        "language",
        "repo_file_name",
        "starting_line_number",
        "batch_size",
    ]

    sql = sql = (
        f"INSERT OR IGNORE INTO {table} "
        f" ({','.join(fields)}) "
        f"VALUES({ ','.join(['?']*len(fields)) }) "
        f"ON CONFLICT(repo_file_name,github_repo_url,batch_size,starting_line_number) DO UPDATE SET "
        f"snippet=excluded.snippet, "
        f"commit_hash=excluded.commit_hash "
        f"  WHERE excluded.commit_hash != {table}.commit_hash;"
    )
    try:
        c = conn.cursor()
        result = c.executemany(sql, batch)
        conn.commit()
        return result
    except Exception as err:
        traceback.print_exc()
