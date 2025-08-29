import sqlite3
from decouple import config

DATABASE_PATH = config('DATABASE_PATH', None)

def connect_db():
    '''Connect to database'''
    return sqlite3.connect(DATABASE_PATH)

def user_exists(discord_id):
    '''
    Checks if a user's Discord ID is in the database
    
    Args:
        discord_id (int): The integer number that is a users discord id

    Returns:
        exists (boolean): True or false value indicating if a user is in the database
    '''
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM User WHERE discord_id = ?", (discord_id,))
        exists = cursor.fetchone() is not None
    except sqlite3.Error as e:
        raise e
    finally:
        if conn:
            conn.close()
    return exists

def create_user(discord_id, first_seen, last_online, playstyle):
    try:
        conn = connect_db()
        conn.execute("INSERT into user values (?,?,?,?)", (discord_id, first_seen, last_online, playstyle,))
        conn.commit()
    except sqlite3.Error as e:
        raise e
    finally:
        if conn:
            conn.close()