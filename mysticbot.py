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
PLAYSTYLE_OPTIONS = ('casual', 'competitive', 'mix')
ACTIVITY_TYPES = ('playing', 'completed', 'dropped')

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all(), help_command=commands.DefaultHelpCommand(show_parameter_descriptions=False))

@bot.event
async def on_ready():
    channel = bot.get_channel(CHANNEL_ID)
    logging.basicConfig(filename='mysticbot.log', level=logging.INFO)
    embed = discord.Embed(
        title="Mystic Bot",
        description=f"List of Commands:\n -specials: Displays information on the top 5 games in the specials category on steam.\n -freethisweek: Displays information on the games that can be redeemed for free on Epic Games.\n -profile: Create a profile that tracks your games and ratings\n -rategame (steam game link) (rating out of 10) (activity_type: \"playing\", \"completed\", \"dropped\"): Add a game to the database with your user rating out of 10\n -help: shows all bot commands.",
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
        print("here")
        print(average_rating, completed_percent)
        print(titles)
        print(activity_types)
        print(ratings)
        print(timestamps)
    except errors.UserDoesNotExist as e:
        await ctx.send(e)

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
        message = await ctx.send("# You are in the system!\nWould you like to update your profile?")
    else:
        message = await ctx.send("# You are currently not in the system.\nWould you like to be added into the system?\nWe only track your discord_id along with any interests provided by you on steam games")

    await message.add_reaction(THUMBS_UP)
    await message.add_reaction(THUMBS_DOWN)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in [THUMBS_UP, THUMBS_DOWN]

    try:
        reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60.0) # Check for reaction from user
        if str(reaction.emoji) == THUMBS_UP:
            if exists:
                await ctx.send(f"**You chose yes**\nLet's update your profile {ctx.author.mention}!")
            else:
                await ctx.send(f"**You chose yes**\nLet's create your profile {ctx.author.mention}!")
                first_seen = datetime.date.today().strftime("%Y-%m-%d")
            last_online = datetime.date.today().strftime("%Y-%m-%d")
            await ctx.send("Please enter a playstyle that is one of the following:\ncasual\ncompetitive\nmix")

            while True: # Loops until correct input is given or a timeout occurs
                message = await bot.wait_for("message", check=lambda msg: msg.author == ctx.author and msg.channel == ctx.channel, timeout=60.0)
                if message.content in PLAYSTYLE_OPTIONS:
                    break
                else:
                    await ctx.send("Invalid option. Please try again")

            await ctx.send(f"Recording your playstyle: {message.content}")
            if exists:
                db_manager.update_user(discord_id, last_online, message.content)
            else:
                db_manager.create_user(discord_id, first_seen, last_online, message.content)
            await ctx.send(f"Your profile is setup {ctx.author.mention}!")
        elif str(reaction.emoji) == THUMBS_DOWN: # If the reaction is a thumbs down
            if exists:
                await ctx.send(f"**You chose no**\nYour profile was not altered {ctx.author.mention}!")
            else:
                await ctx.send("**You chose no**\nWe hope you reconsider in the future!")
    except asyncio.TimeoutError:
        await ctx.send("You didn't choose an option in time.")
    except Exception as e:
        logging.error(f"Error processing userinfo for {ctx.author}: {e}", exc_info=True)
        await ctx.send("Oops, there was an error. Please try again.")

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