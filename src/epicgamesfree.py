import requests

class GameInfo:
    title = None
    description = None
    start_date = None
    end_date = None
    original_price = None
    game_url = None
    game_image = None

    def __init__(self, title, description, start_date, end_date, original_price, game_url, game_image):
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
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
            start_date, start_time = element["effectiveDate"].split('T')
            end_date, end_time = element["expiryDate"].split('T')
            original_price = element["price"]["totalPrice"]["originalPrice"]
            original_price /= 100

            # Build the url for the game
            product_page = None
            if len(element["offerMappings"]) > 0:
                product_page = element["offerMappings"][0]["pageSlug"]
            if product_page != None:
                game_url = "https://store.epicgames.com/en-US/p/" + product_page
            else:
                product_page = element["productSlug"]
                game_url = "https://store.epicgames.com/en-US/p/" + product_page if product_page != None else None

            for image in element["keyImages"]:
                if image["type"] == "OfferImageWide":
                    game_image = image["url"]
                elif image["type"] == "VaultClosed" and title.find("Mystery Game") != -1:
                    game_image = image["url"]
            game = GameInfo(title, description, start_date, end_date, original_price, game_url, game_image)
            free_games.append(game)

    return free_games

if __name__ == '__main__':
    get_free_epic_games()