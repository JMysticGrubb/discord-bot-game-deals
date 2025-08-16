#steamsales.py

from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from decouple import config
import os
import threading

class GameInfo:
    title = None
    description = None
    tags = None
    monthly_ratings = None
    all_ratings = None
    original_price = None
    discount = None
    discounted_price = None
    game_url = None
    game_image = None

    def __init__(self, title, description, tags, monthly_ratings, all_ratings, original_price, discount, discounted_price, game_url, game_image):
        self.title = title
        self.description = description
        self.tags = tags
        self.monthly_ratings = monthly_ratings
        self.all_ratings = all_ratings
        self.original_price = original_price
        self.discount = discount
        self.discounted_price = discounted_price
        self.game_url = game_url
        self.game_image = game_image



def last_substring_file(file, substring):
    '''
    Finds the last occurrence of a substring

    Args:
        file (string): The path to a file
        substring (string): the string we are looking for

    Returns:
        last_line (int): the line where the last occurrence was found
        last_index (int): The last index of the substring on the last line
    '''
    last_index_found = -1
    line_number_of_last_occurrence = -1

    with open(file, 'r', encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                current_index = line.rindex(substring)
                last_index_found = current_index
                line_number_of_last_occurrence = i
            except ValueError:
                pass

    if last_index_found != -1:
        last_line = line_number_of_last_occurrence
        last_index = last_index_found
    else:
        print("Error: Substring could not be found")

    return last_line, last_index



def find_occurence(text, substring, occurrence, start_point):
    '''
    Finds the nth occurrence of a substring in a text

    Args:
        text (string): The text to search through
        substring (string): the string we are looking for
        occurrence (int): The nth occurrence we are looking for
        start_point (int): The starting index to start search

    Returns:
        start (int): returns the index of the nth occurrence
    '''
    start = text.find(substring, start_point)
    while start >= 0 and occurrence > 1:
        start = text.find(substring, start + 1)
        occurrence -= 1
    return start



def flatten_list(list):
    '''
    Flattens the list so that it is not pair based

    Args:
        list (array): The array to flatten

    Returns:
        flatlist (array): The array 
    '''
    flatlist = []
    for item1, item2 in list:
        if item1:
            flatlist.append(item1)
        if item2:
            flatlist.append(item2)

    return flatlist



def retrieve_top_5(file, last_line, last_index):
    '''
    Finds the top 5 games in the specials category on steam

    Args:
        file (string): The path to a file
        last_line (int): The integer value of the line containing the last occurrence of a string
        last_index (int): The integer value of the last occurence of a string on the last_line

    Returns:
        top5_games (array of strings): The array of the game ids for the top 5 games on steam
    '''
    with open(file, 'r', encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                if i == last_line:
                    top5_games = line[last_index:find_occurence(line, ",", 5, last_index)]
                    top5_games = re.findall(r'"appid":(\d+)|"packageid":(\d+)', top5_games)
            except:
                pass
    return top5_games



def get_game_link(file, gameid):
    '''
    Finds information based on the gameid or packageid

    Args:
        file (string): The file to search through
        gameid (string): A string of integers for the game or package that we want information on

    Returns:
        gamelink (string): returns a string containing a link to the javascript for the game or package page
    '''
    is_game = True
    with open(file, 'r', encoding="utf-8") as f:
        filecontent = f.read()
        match = re.search(r"https://store.steampowered.com/app/" + gameid + r"/([^\"]+)", filecontent)
        if match == None:
            match = re.search(r"https://store.steampowered.com/sub/" + gameid + r"/([^\"]+)", filecontent)
            is_game = False
        game_link = match.group(1) # Extracts the part of the captured link
        if is_game:
            game_link = "https://store.steampowered.com/app/" + gameid + "/" + game_link # Concatenates the latter part of the link with the start
        else:
            game_link = "https://store.steampowered.com/sub/" + gameid + "/" + game_link # Concatenates the latter part of the link with the start

    return game_link



def get_game_html(game_link):
    '''
    Creates a text file with the html for a game or package's webpage

    Args:
        game_link (string): A link to the html of a webpage

    Returns:
        game_file (string): Returns the name of the file for the games html
    '''
    url = game_link
    page = urlopen(url)

    html_bytes = page.read()
    html = html_bytes.decode("utf-8")

    match = re.search(r"https://store.steampowered.com/app/\d+/([^/?]+)", game_link)
    if match == None:
        match = re.search(r"https://store.steampowered.com/sub/(\d+)", game_link)
    game_file = match.group(1)

    with open(game_file, "w", encoding="utf-8") as f:
        f.write(html)

    return game_file



def get_game_description(game_link):
    '''
    Gets the description for a steam game

    Args:
        game_link (string): A link to the html of a game's webpage

    Returns:
        game_description (string): Returns the description of the game
    '''
    with open(game_link, "r", encoding="utf-8") as f:
        filecontent = f.read()
        match = re.search(r"meta name=\"Description\" content=\"(.*?)\"", filecontent)
        game_description = match.group(1)
    
    return game_description



def get_game_tags(game_link):
    '''
    Gets the tags for a steam game

    Args:
        game_link (string): A link to the html of a game's webpage

    Returns:
        game_tags (string): Returns the description of the game
    '''
    game_tags = []
    with open(game_link, "r", encoding="utf-8") as f:
        for index, line in enumerate(f):
            match = re.search(r"\s(.*?)\s+</a><a href=\"https://store.steampowered.com/tags", line)
            if match == None:
                continue
            else:
                game_tags.append(match.group(1).strip())
    return game_tags



def get_game_ratings(game_link):
    '''
    Gets the monthly and overall ratings for a steam game

    Args:
        game_link (string): A link to the html of a game's webpage

    Returns:
        monthly_ratings (string): Returns the monthly ratings for the game
        all_ratings (string): Returns the overall ratings for the game
    '''
    with open(game_link, "r", encoding="utf-8") as f:
        filecontent = f.read()
        ratings = re.findall(r"<a class=\"user_reviews_summary_row\" href=\"\#app_reviews_hash\" data-tooltip-html=\"(.*?\.)", filecontent)
        monthly_ratings = ratings[0]
        all_ratings = ratings[1]
    return monthly_ratings, all_ratings



def get_game_price(game_link):
    '''
    Gets the pricing information for a steam game

    Args:
        game_link (string): A link to the html of a game's webpage

    Returns:
        discount_percent (string): Returns the percentage of the discount for the game
        original_price (string): Returns the original price of the game
        discount_price (string): Returns the discounted price of the game
    '''
    with open(game_link, "r", encoding="utf-8") as f:
        filecontent = f.read()
        match = re.search(r"<div class=\"discount_block game_purchase_discount\".*?aria-label=\"(\d+%) off. (\$\d+\.\d+) normally, discounted to (\$\d+\.\d+)\"", filecontent)
        discount_percent = match.group(1)
        original_price = match.group(2)
        discount_price = match.group(3)
    return discount_percent, original_price, discount_price

def get_game_image(game_link):
    with open(game_link, "r", encoding="utf-8") as f:
        filecontent = f.read()
        match = re.search(r"<link rel=\"image_src\" href=\"(.*?)\"", filecontent)
        game_image = match.group(1)
    return game_image

def get_game_info(base_file, game, specials):
    '''
    Gets the information from a game or package on steam

    Args:
        base_file (string): file path to steam's html
        game (int): integer representing a game or packages id
        specials (array): array of game objects that contains info for each game

    Returns:
        None
    '''
    game_link = get_game_link(base_file, game)
    game_file = get_game_html(game_link)
    title = str(game_file)
    description = get_game_description(game_file)
    tags = get_game_tags(game_file)
    tags = [tag for tag in tags if tag.strip()]
    monthly_ratings, all_ratings = get_game_ratings(game_file)
    discount_percent, original_price, discount_price = get_game_price(game_file)
    match = re.search(rf"(.*?{title}/)", game_link)
    game_url = match.group(1)
    game_image = get_game_image(game_file)
    game = GameInfo(title, description, tags, monthly_ratings, all_ratings, original_price, discount_percent, discount_price, game_url, game_image)
    specials.append(game)

'''
# steamsales.py scrapes data from the top sellers section in the specials category on the steam store page.
'''

def steam_specials():
    url = "https://store.steampowered.com/?snr=1_4_4__global-responsive-menu" # get the url
    page = urlopen(url) # open the url and get the HTTPResponse

    html_bytes = page.read() # retrieves the bytes of information
    html = html_bytes.decode("utf-8") # turns the html_bytes into readable html
    soup = BeautifulSoup(html, 'html.parser')

    base_file = "html_steam" # Set the file path to the same directory as program but the file html_steam

    # write the html into a file and start looking for data
    with open(base_file, "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    last_line, last_index = last_substring_file(base_file, "specials") # Find the line and index of the last occurence of "specials"
    top5_games = retrieve_top_5(base_file, last_line, last_index)
    top5_games = flatten_list(top5_games)
    specials = []
    threads = []

    for game in top5_games:
        t = threading.Thread(target=get_game_info, args=(base_file, game, specials))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    for game in top5_games:
        game_link = get_game_link(base_file, game)
        game_file = get_game_html(game_link)
        os.remove(game_file)

    return specials