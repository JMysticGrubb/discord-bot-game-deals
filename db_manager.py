import sqlite3
from decouple import config
import re

DATABASE_PATH = config('DATABASE_PATH', None)

def connect_db():
    '''Connect to database'''
    return sqlite3.connect(DATABASE_PATH)

def tag_exists(tag):
    '''
    Checks if a game tag is in the database
    
    Args:
        tag (string): string containing a game tag

    Returns:
        exists (boolean): True or false value indicating if a user is in the database
    '''
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM tag WHERE tag_name = ?", (tag,))
        exists = cursor.fetchone() is not None
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
    return exists

def rating_exists(discord_id, game_id):
    '''
    Checks if a discord user had already inputed a rating for a game
    
    Args:
        discord_id (int): integer value for a user's discord id
        game_id (int): integer value for a game's id

    Returns:
        exists (boolean): True or false value indicating if a users rating for a game is in the database
    '''
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user_activity WHERE discord_id = ? and game_id = ?", (discord_id, game_id,))
        exists = cursor.fetchone() is not None
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
    return exists

def game_exists(game_id):
    '''
    Checks if a game's ID is in the database
    
    Args:
        game_id (int): The integer number that is a game id

    Returns:
        exists (boolean): True or false value indicating if a user is in the database
    '''
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM game WHERE game_id = ?", (game_id,))
        exists = cursor.fetchone() is not None
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
    return exists

def add_game(game):
    '''
    Adds a game to the database
    
    Args:
        game (object): game object containing information about the game (made in steamsales.py)

    Returns:
        None
    '''
    # Set price to the discounted price if the game is on sale and if not set it to the original price
    if (game.discount_price == None):
        price = game.original_price
    else:
        price = game.discount_price

    # Format the is_on_sale boolean to fit the database format of 1 for true and 0 for false
    if (game.is_on_sale == True):
        sale = 1
    else:
        sale = 0

    if (game.end_date == None):
        end_date = "NULL"
    else:
        end_date = game.end_date

    # Grab just the number from the monthly ratings and format it to represent percentages in the form: 0.84
    match = re.search(r"(\d+)%", game.monthly_ratings)
    if match:
        monthly_ratings = float(match.group(1))
        monthly_ratings = monthly_ratings / 100
    
    # Grab just the number from the overall ratings and format it to represent percentages in the form: 0.84
    match = re.search(r"(\d+)%", game.all_ratings)
    if match:
        all_ratings = float(match.group(1))
        all_ratings = all_ratings / 100
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT into game values (?,?,?,?,?)", (game.id, game.title, game.description, game.game_developer, game.game_publisher,))
        cursor.execute("INSERT into game_rating (game_id,monthly_rating,all_rating,scrape_date) values (?,?,?,?)", (game.id, monthly_ratings, all_ratings, game.scrape_date,))
        cursor.execute("INSERT into game_price (game_id,price,currency,is_on_sale,end_date) values (?,?,?,?,?)", (game.id, price, "USD", sale, end_date,))
        for tag in game.tags:
            exists = tag_exists(tag)
            if (exists == False):
                cursor.execute("INSERT into tag (tag_name) values (?)", (tag,))
                tag_id = cursor.lastrowid
                cursor.execute("INSERT into game_tag (game_id, tag_id) values (?,?)", (game.id, tag_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def update_game(game):
    '''
    Updates a game in the database
    
    Args:
        game (object): game object containing information about the game (made in steamsales.py)

    Returns:
        None
    '''
    # Set price to the discounted price if the game is on sale and if not set it to the original price
    if (game.discount_price == None):
        price = game.original_price
    else:
        price = game.discount_price

    # Format the is_on_sale boolean to fit the database format of 1 for true and 0 for false
    if (game.is_on_sale == True):
        sale = 1
    else:
        sale = 0

    if (game.end_date == None):
        end_date = "NULL"
    else:
        end_date = game.end_date

    # Grab just the number from the monthly ratings and format it to represent percentages in the form: 0.84
    match = re.search(r"(\d+)%", game.monthly_ratings)
    if match:
        monthly_ratings = float(match.group(1))
        monthly_ratings = monthly_ratings / 100
    
    # Grab just the number from the overall ratings and format it to represent percentages in the form: 0.84
    match = re.search(r"(\d+)%", game.all_ratings)
    if match:
        all_ratings = float(match.group(1))
        all_ratings = all_ratings / 100
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE game_rating SET monthly_rating = ?, all_rating = ?, scrape_date = ? WHERE game_id = ?", (monthly_ratings, all_ratings, game.scrape_date, game.id,))
        cursor.execute("UPDATE game_price SET price = ?, currency = ?, is_on_sale = ?, end_date = ? WHERE game_id = ?", (price, "USD", sale, end_date, game.id,))
        for tag in game.tags:
            exists = tag_exists(tag)
            if (exists == False):
                cursor.execute("INSERT into tag (tag_name) values (?)", (tag,))
                tag_id = cursor.lastrowid
                cursor.execute("INSERT into game_tag (game_id, tag_id) values (?,?)", (game.id, tag_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def add_rating(game, rating, activity_type, timestamp, discord_id):
    '''
    Adds a user rating to a game
    
    Args:
        game (object): game object containing information about the game (made in steamsales.py)
        rating (string): user rating on a scale from 1 to 10
        activity_type (string): user indicated interaction with the game (playing, completed, dropped)
        timestamp (string): datetime that the user provided a rating and activity_type of format: YYYY-MM-DD
        discord_id (int): integer for the user's discord id

    Returns:
        None
    '''
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT into user_activity (discord_id, game_id, activity_type, rating, timestamp) values (?,?,?,?,?)", (discord_id, game.id, activity_type, rating, timestamp,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def update_rating(game, rating, activity_type, timestamp, discord_id):
    '''
    Updates a user rating to a game
    
    Args:
        game (object): game object containing information about the game (made in steamsales.py)
        rating (string): user rating on a scale from 1 to 10
        activity_type (string): user indicated interaction with the game (playing, completed, dropped)
        timestamp (string): datetime that the user provided a rating and activity_type of format: YYYY-MM-DD
        discord_id (int): integer for the user's discord id

    Returns:
        None
    '''
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE user_activity SET activity_type = ?, rating = ?, timestamp = ? WHERE discord_id = ? AND game_id = ?", (activity_type, rating, timestamp, discord_id, game.id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if conn:
            conn.close() 

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
        conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
    return exists

def create_user(discord_id, first_seen, last_online, playstyle):
    '''
    Inserts information for a new user into the database
    
    Args:
        discord_id (int): The integer number that is a users discord id
        first_seen (string): The date the user's profile is created YYYY-MM-DD
        last_online (string): The date the user's profile is last seen YYYY-MM-DD
        playstyle (string): The playstyle of the player ("casual", "competitive", "mix)

    Returns:
        None
    '''
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT into user values (?,?,?,?)", (discord_id, first_seen, last_online, playstyle,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def update_user(discord_id, last_online, playstyle):
    '''
    Updates a user's information in the database
    
    Args:
        discord_id (int): The integer number that is a users discord id
        last_online (string): The date the user's profile is last seen or updated YYYY-MM-DD
        playstyle (string): The playstyle of the player ("casual", "competitive", "mix)

    Returns:
        None
    '''
    try:
        conn = connect_db()
        conn.execute("UPDATE user SET last_online=?, playstyle=? where discord_id=?", (last_online, playstyle, discord_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()