import asyncio
from discord.ext import commands, tasks
import discord
import os
from decouple import config
import re
import datetime
import steamsales
import epicgamesfree
import db_manager
import logging
import errors

BOT_TOKEN = config('BOT_TOKEN', None)
CHANNEL_ID = int(config('CHANNEL_ID', None))
THUMBS_UP = '👍'
THUMBS_DOWN = '👎'
RIGHT_ARROW = '➡️'
LEFT_ARROW = '⬅️'
BLACK_SQUARE = '◾'
PLAYSTYLE_OPTIONS = ('casual', 'competitive', 'mix')
ACTIVITY_TYPES = ('playing', 'completed', 'dropped')
GAMES_PER_PAGE = 10

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all(), help_command=commands.DefaultHelpCommand(show_parameter_descriptions=False))

@bot.event
async def on_ready():
    channel = bot.get_channel(CHANNEL_ID)
    logging.basicConfig(filename='mysticbot.log', level=logging.INFO)
    embed = discord.Embed(
        title="Mystic Bot",
        description=f"List of Commands:\n -specials: Displays information on the top 5 games in the specials category on steam.\n -freethisweek: Displays information on the games that can be redeemed for free on Epic Games.\n -profile: Create a profile that tracks your games and ratings\n -rategame (steam game link) (rating out of 10) (activity_type: \"playing\", \"completed\", \"dropped\"): Add a game to the database with your user rating out of 10\n -ratings: display the stats and ratings from your profile\n -help: shows all bot commands.",
        color=discord.Color.red()
    )
    await channel.send(embed=embed)
    if not free_games_weekly_post.is_running():
        free_games_weekly_post.start()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You did not provide the nescessary arguments!\nUse -help for more information on a command and how to use it.")

@bot.command()
async def ratings(ctx):
    '''Shows your game ratings if you have any.'''
    try:
        discord_id = int(ctx.author.id)
        if db_manager.user_exists(discord_id) == False:
            raise errors.UserDoesNotExist(f"A user associated with id: {discord_id} does not exist. Please set up a profile using the -profile command.")
        average_rating, completed_percent, titles, activity_types, ratings, timestamps = db_manager.get_rating_stats(discord_id)

        view = PaginatorView(average_rating, completed_percent, titles, activity_types, ratings, timestamps, ctx.author)

        initial_embed = view.create_ratings_embed()

        message = await ctx.send(embed=initial_embed, view=view)

        view.message = message
    except errors.UserDoesNotExist as e:
        await ctx.send(e)
    except Exception as e:
        await ctx.send("There was an error displaying your ratings")

class PaginatorView(discord.ui.View):
    '''Manages the page view for the user's game ratings. Provides interactable buttons to go the the next and previous pages'''
    def __init__(self, average_rating, completed_percent, titles, activity_types, ratings, timestamps, author):
        super().__init__(timeout=60)

        self.average_rating = average_rating
        self.completed_percent = completed_percent
        self.titles = titles
        self.activity_types = activity_types
        self.ratings = ratings
        self.timestamps = timestamps
        self.author = author
        self.start = 0
        self.max_start = max(0, len(self.titles) - 1)

    async def interaction_check(self, interaction):
        if interaction.user != self.author:
            return False
        return True

    def create_ratings_embed(self):
        numGames = self.start + GAMES_PER_PAGE
        end_index = min(numGames, len(self.titles))

        embed = discord.Embed(title="Game Ratings")
        embed.add_field(name='Average Rating', value=self.average_rating)
        embed.add_field(name='Percentage of Games Completed', value=self.completed_percent)
        embed.add_field(name="", value=f"`GAME` **·** `STATUS` **·** `SCORE` **·** `DATE`", inline=False)
        embed.add_field(name="Games:", value="", inline=False)

        for i in range(self.start, end_index):
            embed.add_field(name=f"", value=f"{BLACK_SQUARE} `{self.titles[i]}` **·** `{self.activity_types[i]}` **·** `{self.ratings[i]}` **·** `{self.timestamps[i]}`", inline=False)

        embed.set_footer(text=f"{self.start + 1} to {end_index}")

        return embed
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji=LEFT_ARROW)
    async def left_button_callback(self, interaction, button):
        self._refresh_timeout()

        await interaction.response.defer()

        new_start = self.start - GAMES_PER_PAGE
        if new_start < 0:
            new_start = 0

        if self.start != new_start:
            self.start = new_start
            new_embed = self.create_ratings_embed()
            await interaction.edit_original_response(embed=new_embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, emoji=RIGHT_ARROW)
    async def right_button_callback(self, interaction, button):
        self._refresh_timeout()

        await interaction.response.defer()

        new_start = self.start + GAMES_PER_PAGE
        if new_start > self.max_start:
            new_start = self.max_start

        if self.start != new_start:
            self.start = new_start
            new_embed = self.create_ratings_embed()
            await interaction.edit_original_response(embed=new_embed, view=self)

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True

            await self.message.edit(view=self)

@bot.command()
async def rategame(ctx, game_link, rating, activity_type):
    '''
    Adds or updates a game to your profile with your rating and activity type
    Format: -rategame (steamlink) (rating out of 10) (playing/completed/dropped)
    Ex: -rategame https://store.steampowered.com/app/292140/FINAL_FANTASY_XIII2/ 9 completed
    '''
    try:
        discord_id = int(ctx.author.id)
        if db_manager.user_exists(discord_id) == False:
            raise errors.UserDoesNotExist(f"A user associated with id: {discord_id} does not exist. Please set up a profile using the -profile command.")
        game = steamsales.game_search(game_link)
        game_exists = db_manager.game_exists(game.id)
        rating_exists = db_manager.rating_exists(discord_id, game.id)
        timestamp = datetime.date.today().strftime("%Y-%m-%d")
        if activity_type not in ACTIVITY_TYPES:
            raise ValueError("The input for activity_type is not valid. It must be: \"playing\", \"completed\", or \"dropped\"")
        if game_exists == False:
            db_manager.add_game(game)
        else:
            db_manager.update_game(game)
        if rating_exists == False:
            db_manager.add_rating(game, rating, activity_type, timestamp, discord_id)
        else:
            db_manager.update_rating(game, rating, activity_type, timestamp, discord_id)
        if activity_type in ("completed", "dropped"):
            await ctx.send(f"You gave {game.title}, a rating of {rating} out of 10! You have {activity_type} this game.")
        else:
            await ctx.send(f"You gave {game.title}, a rating of {rating} out of 10! You are {activity_type} this game.")
    except errors.UserDoesNotExist as e:
        await ctx.send(e)
    except ValueError as e:
        await ctx.send(e)
    except Exception as e:
        await ctx.send(f"Could not find game information for the link: {game_link}")
        await ctx.send(e)

@bot.command()
async def profile(ctx):
    '''Detects if you have a profile and helps you update or create a profile'''
    discord_id = int(ctx.author.id) # Get the users discord id
    exists = db_manager.user_exists(discord_id)

    if exists:
        content = "# You are in the system!\nWould you like to update your profile?"
    else:
        content = "# You are currently not in the system.\nWould you like to be added into the system?\nWe only track your discord_id along with any interests provided by you on steam games"

    try:
        view = ProfileView(ctx.bot, ctx.author, exists, discord_id)
        message = await ctx.send(content, view=view)
        view.message = message
    except Exception as e:
        logging.error(f"Error processing userinfo for {ctx.author}: {e}", exc_info=True)
        await ctx.send("Oops, there was an error. Please try again.")

class ProfileView(discord.ui.View):
    '''Manages the view for the user's profile. Provides interactable buttons to create their profile or update their profile.'''
    def __init__(self, bot, author, exists, discord_id):
        super().__init__(timeout=60)

        self.bot = bot
        self.author = author
        self.exists = exists
        self.discord_id = discord_id
    
    async def interaction_check(self, interaction):
        if interaction.user != self.author:
            return False
        return True

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary, emoji=THUMBS_UP)
    async def left_button_callback(self, interaction, button):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

        if self.exists:
            response = f"**You chose yes**\nLet's update your profile {self.author.mention}!"
        else:
            response = f"**You chose yes**\nLet's create your profile {self.author.mention}!"

        await interaction.response.send_message(response)

        await interaction.followup.send("Please enter a playstyle that is one of the following:\ncasual\ncompetitive\nmix")

        while True:
            try:
                message = await self.bot.wait_for("message", check=lambda msg: msg.author == self.author and msg.channel == interaction.channel, timeout=60.0)
            except asyncio.TimeoutError:
                await interaction.response.send_message("You didn't provide a playstyle in time.")
                return
            
            if message.content.lower() in PLAYSTYLE_OPTIONS:
                playstyle = message.content.lower()
                break
            else:
                await interaction.followup.send("Invalid option. Please try again")

        await interaction.followup.send(f"Recording your playstyle: {playstyle}")

        last_online = datetime.date.today().strftime("%Y-%m-%d")

        if self.exists:
            db_manager.update_user(self.discord_id, last_online, playstyle)
        else:
            first_seen = datetime.date.today().strftime("%Y-%m-%d")
            db_manager.create_user(self.discord_id, first_seen, last_online, playstyle)

        await interaction.followup.send(f"Your profile is setup {self.author.mention}!")

    @discord.ui.button(label="No", style=discord.ButtonStyle.primary, emoji=THUMBS_DOWN)
    async def right_button_callback(self, interaction, button):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

        if self.exists:
            response = f"**You chose no**\nYour profile was not altered {self.author.mention}!"
        else:
            response = f"You chose no**\nWe hope you reconsider in the future!"

        await interaction.response.send_message(response)

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True

            await self.message.edit(view=self)

@bot.command()
async def specials(ctx):
    '''Displays information on the top 5 games in the specials category on steam.'''
    await ctx.send(f"# Gathering Information...")

    games = steamsales.steam_specials()
    for game in games:
        embed = discord.Embed(
            title=game.title,
            description=game.description,
            color=discord.Color.blue()
        )

        if game.game_image:
            embed.set_image(url=game.game_image)

        embed.add_field(name="Developer", value=game.game_developer, inline=True)
        embed.add_field(name="Publisher", value=game.game_publisher, inline=True)

        embed.add_field(name="", value="", inline=True)

        embed.add_field(name="Original Price", value=f"${game.original_price}", inline=True)
        embed.add_field(name="Discount Percent", value=game.discount_percent, inline=True)
        embed.add_field(name="Dicount Price", value=f"${game.discount_price}", inline=True)

        if game.monthly_ratings != None:
            match = re.search(r"(\d+)\%", game.monthly_ratings)
            rating_score = int(match.group(1))
        else:
            rating_score = -1

        if (rating_score > 80):
            embed.add_field(name="Monthly Ratings👍", value=f"{game.monthly_ratings}", inline=False)
        elif (rating_score > 50):
            embed.add_field(name="Monthly Ratings😑", value=f"{game.monthly_ratings}", inline=False)
        elif (rating_score >= 0 and rating_score <= 50):
            embed.add_field(name="Monthly Ratings👎", value=f"{game.monthly_ratings}", inline=False)
            

        if game.all_ratings != None:
            match = re.search(r"(\d+)\%", game.all_ratings)
            rating_score = int(match.group(1))
        else:
            rating_score = -1

        if (rating_score > 80):
            embed.add_field(name="Overall Ratings👍", value=f"{game.all_ratings}", inline=False)
        elif (rating_score > 50):
            embed.add_field(name="Overall Ratings😑", value=f"{game.all_ratings}", inline=False)
        elif (rating_score >= 0 and rating_score <= 50):
            embed.add_field(name="Overall Ratings👎", value=f"{game.all_ratings}", inline=False)

        if game.tags:
            tags_string = ", ".join(game.tags)
            embed.add_field(name="Tags🏷️", value=tags_string, inline=False)

        embed.url = game.game_url

        await ctx.send(embed=embed)

    return

@bot.command()
async def freethisweek(ctx):
    '''Displays information on the games that are free to redeem on Epic Games.'''
    await ctx.send(f"# Gathering Information...")

    games = epicgamesfree.get_free_epic_games()
    for game in games:
        embed = discord.Embed(
            title=game.title,
            description=game.description,
            color=discord.Color.blue()
        )

        if game.game_image:
            embed.set_image(url=game.game_image)

        embed.add_field(name="Original Price:", value=game.original_price, inline=True)

        embed.url = game.game_url

        await ctx.send(embed=embed)

    return

@tasks.loop(hours=168, minutes=0)
async def free_games_weekly_post():
    if datetime.datetime.now(datetime.timezone.utc).weekday() == 4 and datetime.datetime.now(datetime.timezone.utc).hour >= 15: # Only posts on Thursdays after 10am (when the new free games are out)
        channel = bot.get_channel(CHANNEL_ID)
        await freethisweek(channel)

bot.run(BOT_TOKEN)