#steamsales.py

from bs4 import BeautifulSoup
import re
from decouple import config
import threading
import requests

class GameInfo:
    title = None
    description = None
    tags = None
    monthly_ratings = None
    all_ratings = None
    original_price = None
    discount_percent = None
    discount_price = None
    game_url = None
    game_image = None
    game_developer = None
    game_publisher = None

    def __init__(self, title, description, tags, monthly_ratings, all_ratings, original_price, discount_percent, discount_price, game_url, game_image, game_developer, game_publisher):
        self.title = title
        self.description = description
        self.tags = tags
        self.monthly_ratings = monthly_ratings
        self.all_ratings = all_ratings
        self.original_price = original_price
        self.discount_percent = discount_percent
        self.discount_price = discount_price
        self.game_url = game_url
        self.game_image = game_image
        self.game_developer = game_developer
        self.game_publisher = game_publisher



def flatten_list(list):
    '''
    Flattens the list so that it is not pair based

    Args:
        list (Array): The array to flatten

    Returns:
        flatlist (Array): The array 
    '''
    flatlist = []
    for item1, item2 in list:
        if item1:
            flatlist.append(item1)
        if item2:
            flatlist.append(item2)

    return flatlist



def retrieve_top_5(javascript):
    '''
    Finds the top 5 games in the specials category on steam

    Args:
        javascript (String): A string of the javascript section that contains the specials

    Returns:
        top5_games (Array of Strings): The array of the game ids for the top 5 games on steam
    '''
    top5_games = []

    specials_match = re.search(r'"specials":(\[.*?\])', javascript)
    specials_string = specials_match.group(1)
    all_ids = re.findall(r'"appid":(\d+)|"packageid":(\d+)', specials_string)
    top5_games = all_ids[:5]

    return top5_games



def get_game_link(soup, gameid):
    '''
    Finds information based on the gameid or packageid

    Args:
        soup (Object): A BeautifulSoup object containing the html for the game
        gameid (String): A string of integers for the game or package that we want information on

    Returns:
        gamelink (String): returns a string containing a link to the javascript for the game or package page
        is_game (Boolean): returns a boolean indicating if it is a game or package
    '''
    is_game = True

    match = re.search(r"https://store.steampowered.com/app/" + gameid + r"/([^\"]+)", soup)
    if match == None:
        match = re.search(r"https://store.steampowered.com/sub/" + gameid + r"/([^\"]+)", soup)
        is_game = False
    game_link = match.group(1) # Extracts the part of the captured link
    if is_game:
        game_link = "https://store.steampowered.com/app/" + gameid + "/" + game_link # Concatenates the latter part of the link with the start
    else:
        game_link = "https://store.steampowered.com/sub/" + gameid + "/" + game_link # Concatenates the latter part of the link with the start

    return game_link, is_game



def get_game_html(game_link, is_game):
    '''
    Creates a text file with the html for a game or package's webpage

    Args:
        game_link (String): A link to the html of a webpage
        is_game (Boolean): A boolean indicating if it is a game or package

    Returns:
        url_content (String): Returns a string that has the url for the game
        soup (Object): Returns a BeautfifulSoup object for the game's html
    '''
    url = game_link
    response = requests.get(url) # open the url and get the HTTPResponse

    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    
    if is_game:
        meta_tag = soup.find('meta', property='og:url')

        if meta_tag:
            url_content = meta_tag['content']

    else:
        url_content = game_link.split('?')[0]

    return url_content, soup



def get_game_title(soup, game_url, is_game):
    '''
    Gets the title for a steam game

    Args:
        soup (Object): A BeautifulSoup object containing the html for the game
        game_url (String): A string that has the url for the game
        is_game (Boolean): A boolean indicating if it is a game or package

    Returns:
        title (String): String for the title of a game
    '''
    if is_game:
        match = re.search(r"/\d+/(\w+/?)/", game_url)
        title = match.group(1).replace('_', ' ').title()
    else:
        title_container = soup.find('h2', class_='pageheader')
        
        if title_container:
            title = title_container.get_text()

    return title



def get_game_description(soup):
    '''
    Gets the description for a steam game

    Args:
        soup (Object): A BeautifulSoup object containing the html for the game

    Returns:
        game_description (String): Returns the description of the game
    '''
    meta_tag = soup.find('meta', property='og:description')

    if meta_tag:
        game_description = meta_tag['content']
    
    return game_description



def get_game_tags(soup):
    '''
    Gets the tags for a steam game

    Args:
        soup (Object): A BeautifulSoup object containing the html for the game

    Returns:
        game_tags (String): Returns the description of the game
    '''
    game_tags = []
    tags_container = soup.find('div', class_=['glance_tags', 'popular_tags'])

    if tags_container:
        tag_links = tags_container.find_all('a', class_='app_tag')

        game_tags = [tag.get_text().strip() for tag in tag_links]

    return game_tags



def get_game_ratings(soup, is_game):
    '''
    Gets the monthly and overall ratings for a steam game

    Args:
        soup (Object): A BeautifulSoup object containing the html for the game
        is_game (Boolean): A boolean indicating if it is a game or package

    Returns:
        monthly_ratings (String): Returns the monthly ratings for the game
        all_ratings (String): Returns the overall ratings for the game
    '''
    if is_game:
        reviews_container = soup.find(id='userReviews')

        if reviews_container:
            review_links = reviews_container.find_all('a', class_='user_reviews_summary_row')
        
            monthly_ratings = review_links[0]['data-tooltip-html'].strip()
            all_ratings = review_links[1]['data-tooltip-html'].strip()
    else:
        monthly_ratings = None
        all_ratings = None

    return monthly_ratings, all_ratings



def get_game_price(soup):
    '''
    Gets the pricing information for a steam game

    Args:
        soup (Object): A BeautifulSoup object containing the html for the game

    Returns:
        discount_percent (String): Returns the percentage of the discount for the game
        original_price (String): Returns the original price of the game
        discount_price (String): Returns the discounted price of the game
    '''
    price_container = soup.find('div', class_='discount_block game_purchase_discount')

    if price_container:
        discount = price_container['aria-label']
    else:
        discount = None
    
    if discount:
        match = re.search(r'(\d+%) off. (\$\d+\.\d+) normally, discounted to (\$\d+\.\d+)', discount)
        discount_percent = match.group(1)
        original_price = match.group(2)
        discount_price = match.group(3)
    else:
        discount_percent = None
        original_price = None
        discount_price = None

    if original_price == None:
        price_container = soup.find('meta', itemprop = 'price')
        if price_container:
            original_price = price_container['content']

    return discount_percent, original_price, discount_price



def get_game_image(soup):
    '''
    Gets the image for a steam game

    Args:
        soup (Object): A BeautifulSoup object containing the html for the game

    Returns:
        game_image (String): String for the image of a game
    '''

    game_image_container = soup.find('link', rel="image_src")

    if game_image_container:
        game_image = game_image_container['href']

    return game_image



def get_game_developer(soup):
    '''
    Gets the developer for a steam game

    Args:
        soup (Object): A BeautifulSoup object containing the html for the game

    Returns:
        game_developer (String): String for the developer of a game
    '''
    developer_container = soup.find(id='developers_list')

    if developer_container:
            game_developer = developer_container.find('a')
            game_developer = game_developer.text.strip()

    return game_developer



def get_game_publisher(soup):
    '''
    Gets the publisher for a steam game

    Args:
        soup (Object): A BeautifulSoup object containing the html for the game

    Returns:
        game_publisher (String): String for the publisher of a game
    '''
    dev_rows = soup.find_all('div', class_='dev_row')

    for dev in dev_rows:
        subtitle = dev.find('div', class_='subtitle column')
        if subtitle and "Publisher:" in subtitle.text.strip():
            game_publisher = dev.find('a')
            game_publisher = game_publisher.text.strip()

    return game_publisher



def get_game_info(soup, game, specials):
    '''
    Gets the information from a game or package on steam

    Args:
        soup (Object): A BeautifulSoup object containing the html for the game
        game (int): integer representing a game or packages id
        specials (array): array of game objects that contains info for each game

    Returns:
        None
    '''
    game_link, is_game = get_game_link(soup, game)
    game_url, soup = get_game_html(game_link, is_game)
    title = get_game_title(soup, game_url, is_game)
    description = get_game_description(soup)
    tags = get_game_tags(soup)
    tags = [tag for tag in tags if tag.strip()]
    monthly_ratings, all_ratings = get_game_ratings(soup, is_game)
    discount_percent, original_price, discount_price = get_game_price(soup)
    game_image = get_game_image(soup)
    game_developer = get_game_developer(soup)
    game_publisher = get_game_publisher(soup)
    game = GameInfo(title, description, tags, monthly_ratings, all_ratings, original_price, discount_percent, discount_price, game_url, game_image, game_developer, game_publisher)
    specials.append(game)

def game_search(game_url):
    '''
    Gets game information given a link to a steam game page

    Args:
        game_url (string): string containing the link to a steam game page

    Returns:
        game (object): returns a game object containing information on the game
    '''
    url = game_url
    response = requests.get(url)

    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    is_game = True

    title = get_game_title(soup, game_url, is_game)
    description = get_game_description(soup)
    tags = get_game_tags(soup)
    tags = [tag for tag in tags if tag.strip()]
    monthly_ratings, all_ratings = get_game_ratings(soup, is_game)
    discount_percent, original_price, discount_price = get_game_price(soup)
    game_image = get_game_image(soup)
    game_developer = get_game_developer(soup)
    game_publisher = get_game_publisher(soup)
    game = GameInfo(title, description, tags, monthly_ratings, all_ratings, original_price, discount_percent, discount_price, game_url, game_image, game_developer, game_publisher)
    
    return game


def steam_specials():
    '''Scrapes data from the top 5 sellers in the specials category on the steam store page'''
    url = "https://store.steampowered.com/?snr=1_4_4__global-responsive-menu" # get the url
    response = requests.get(url) # open the url and get the HTTPResponse

    html = response.text # Turn the HTTPResponse into html text
    soup = BeautifulSoup(html, 'html.parser') # Parse the html
    soup_string = str(soup) # Create a string version of the BeautifulSoup object

    #base_file = "html_steam" # Set the file path to the same directory as program but the file html_steam

    # write the html into a file
    '''with open(base_file, "w", encoding="utf-8") as f:
        f.write(soup.prettify())'''

    script_tags = soup.find_all('script')

    specials_javascript = script_tags[len(script_tags)-1]
    specials_string = specials_javascript.string

    top5_games = retrieve_top_5(specials_string)

    top5_games = flatten_list(top5_games)
    specials = []
    threads = []

    for game in top5_games:
        t = threading.Thread(target=get_game_info, args=(soup_string, game, specials))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    return specials