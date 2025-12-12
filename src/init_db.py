import sqlite3
import os

def create_database():
    '''
    Creates database via sql script
    '''
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'games_and_interests.db')
    sql_script_path = os.path.join(current_dir, 'games_and_interests.sql')

    try:
        conn = sqlite3.connect(db_path)
        with open(sql_script_path) as f:
            conn.executescript(f.read())
    except sqlite3.DatabaseError as e:
        conn.rollback
        raise e
    finally:
        conn.commit()
        if conn:
            conn.close()

if __name__ == '__main__':
    create_database()