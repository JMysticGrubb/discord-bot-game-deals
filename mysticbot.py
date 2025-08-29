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

BOT_TOKEN = config('BOT_TOKEN', None)
CHANNEL_ID = int(config('CHANNEL_ID', None))

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())

@bot.event
async def on_ready():
    channel = bot.get_channel(CHANNEL_ID)
    embed = discord.Embed(
        title="Mystic Bot",
        description=f"List of Commands:\n -specials: Displays information on the top 5 games in the specials category on steam.\n -freethisweek: Displays information on the games that can be redeemed for free on Epic Games.\n -profile: Create a profile that tracks your games and ratings\n -help: shows all bot commands.",
        color=discord.Color.red()
    )
    await channel.send(embed=embed)
    if not free_games_weekly_post.is_running():
        free_games_weekly_post.start()

@bot.command()
async def profile(ctx):
    '''Detects if you have a profile and helps you update or create a profile'''
    discord_id = int(ctx.author.id) # Get the users discord id
    playstyle_options = ('casual', 'competitive', 'mix') # Possible options for playstyle

    if db_manager.user_exists(discord_id): # if the discord user is already in the database
        message = await ctx.send("# You are in the system!\nWould you like to update your profile?")
        await message.add_reaction('👍')
        await message.add_reaction('👎')
    else: # if the discord user is not already in the database
        message = await ctx.send("# You are currently not in the system.\nWould you like to be added into the system?\nWe only track your discord_id along with any interests provided by you on steam games")
        await message.add_reaction('👍')
        await message.add_reaction('👎')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['👍', '👎']

        try:
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60.0) # Check for reaction from user
            if str(reaction.emoji) == '👍': # If the reaction is a thumbs up
                await ctx.send("You chose yes")
                await ctx.send(f"Welcome to the Mystic Bot! {ctx.author.mention}")
                first_seen = datetime.date.today().strftime("%Y-%m-%d")
                last_online = first_seen
                await ctx.send("Please enter a playstyle that is one of the following:\ncasual\ncompetitive\nmix")

                while True:
                    message = await bot.wait_for("message", check=lambda msg: msg.author == ctx.author and msg.channel == ctx.channel, timeout=60.0)
                    await ctx.send(f"Recording your playstyle: {message.content}")
                    if message.content in playstyle_options:
                        break
                    else:
                        await ctx.send("Invalid option. Please try again")

                db_manager.create_user(discord_id, first_seen, last_online, message.content)
                await ctx.send(f"Your profile is setup {ctx.author.mention}!")
            elif str(reaction.emoji) == '👎': # If the reaction is a thumbs down
                await ctx.send("You chose no")
                await ctx.send("We hope you reconsider in the future!")

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

        embed.add_field(name="Original Price", value=game.original_price, inline=True)
        embed.add_field(name="Discount Percent", value=game.discount_percent, inline=True)
        embed.add_field(name="Dicount Price", value=game.discount_price, inline=True)

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
    if datetime.datetime.now(datetime.timezone.utc).weekday() == 4: # Only posts on Thursdays (when the new free games are out)
        channel = bot.get_channel(CHANNEL_ID)
        await freethisweek(channel)

bot.run(BOT_TOKEN)