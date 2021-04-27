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
                                        chunk_size INTEGER,
                                        UNIQUE(commit_hash, repo_file_name, github_repo_url, chunk_size, starting_line_number)
                                ); """

    try:
        c = conn.cursor()
        c.execute(sql_create_snippets_table)
        conn.commit()
    except Exception as e:
        traceback.print_exc()
    
['url',
 'repository_url',
  'labels_url',
   'comments_url',
    'events_url',
    'html_url',
     'id',
    'node_id',
    'number',
    'title',
    'state',
    'locked',
    'assignee',
    'milestone',
     'comments',
      'created_at',
       'updated_at', 
       'closed_at',
        'author_association',
         'active_lock_reason',
          'body', 
'performed_via_github_app']


def create_issues_table(conn):
    """create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    sql_create_snippets_table = """ CREATE TABLE IF NOT EXISTS issues (
                                        id INTEGER PRIMARY KEY,
                                        title TEXT,
                                        body TEXT NOT NULL,
                                        comments_url TEXT NOT NULL,
                                        comments INTEGER,
                                        html_url TEXT,
                                        state TEXT,
                                        number INTEGER,
                                        author_association text,
                                        url TEXT,
                                        repository_url  TEXT,
                                        labels_url  TEXT,
                                        events_url  TEXT,
                                        created_at timestamp,
                                        updated_at timestamp, 
                                        closed_at timestamp
                                ); """

    try:
        c = conn.cursor()
        c.execute(sql_create_snippets_table)
        conn.commit()
    except Exception as e:
        traceback.print_exc()


def write_issue_to_db(conn, batch):
    table = "issues"
    fields = [
        "body",
        "title",
        "comments_url",
        "comments",
        "html_url",
        "state",
        "number",
        "author_association",
        "url",
        "repository_url",
        "labels_url",
        "events_url",
        "author_association",
        "created_at",
        "updated_at",
        "closed_at",
    ]

    sql = sql = (
        f"INSERT OR IGNORE INTO {table} "
        f" ({','.join(fields)}) "
        f"VALUES({ ','.join(['?']*len(fields)) });"
    )
    try:
        c = conn.cursor()
        result = c.executemany(sql, batch)
        conn.commit()
        return result
    except Exception as err:
        traceback.print_exc()

def write_issue_to_db_test(conn, batch):
    table = "issues"
    fields = [
        "body",
        "title",
        "comments_url",
        "comments",
        "html_url",
        "state",
        "number",
        "author_association",
        "url",
        "repository_url",
        "labels_url",
        "events_url",
        "author_association",
        "created_at",
        "updated_at",
        "closed_at",
    ]

    sql = sql = (
        f"INSERT OR IGNORE INTO {table} "
        f" ({','.join(fields)}) "
        f"VALUES({ ','.join(['?']*len(fields)) });"
    )
    try:
        c = conn.cursor()
        result = c.execute(sql, batch)
        conn.commit()
        return result
    except Exception as err:
        print(batch)
        traceback.print_exc()
        raise


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
        "chunk_size",
    ]

    sql = sql = (
        f"INSERT OR IGNORE INTO {table} "
        f" ({','.join(fields)}) "
        f"VALUES({ ','.join(['?']*len(fields)) });"
    )
    try:
        c = conn.cursor()
        result = c.executemany(sql, batch)
        conn.commit()
        return result
    except Exception as err:
        traceback.print_exc()
