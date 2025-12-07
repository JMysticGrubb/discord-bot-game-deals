import requests
from bs4 import BeautifulSoup

class GameInfo:
    title = None
    description = None
    original_price = None
    game_url = None
    game_image = None

    def __init__(self, title, description, original_price, game_url, game_image):
        self.title = title
        self.description = description
        self.original_price = original_price
        self.game_url = game_url
        self.game_image = game_image



def get_free_epic_games():
    '''
    Retrieves information on free game deals on epic games

    Args:
        None

    Returns:
        free_games (array): Array of game objects that contain information on free games from Epic Games
    '''

    url = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"
    response = requests.get(url)

    free_game_json = response.json()

    # Puts the json in a file
    '''
    with open("free_game_json", "w") as f:
        json.dump(free_game_json, f, indent="")
    '''
        
    free_games = []

    # For each element of the json, pull relevant information for each game that has a 100% discount
    for element in free_game_json["data"]["Catalog"]["searchStore"]["elements"]:
        if element["price"]["totalPrice"]["discountPrice"] == 0:
            title = element["title"]
            description = element["description"]
            original_price = element["price"]["totalPrice"]["originalPrice"]
            original_price /= 100
            if len(element["offerMappings"]) > 0:
                game_url = element["offerMappings"][0]["pageSlug"]
            game_url = "https://store.epicgames.com/en-US/p/" + game_url
            for image in element["keyImages"]:
                if image["type"] == "OfferImageWide":
                    game_image = image["url"]
            game = GameInfo(title, description, original_price, game_url, game_image)
            free_games.append(game)

    return free_games