from discord.ext import commands
import discord
import os
from decouple import config
import steamsales
import re
import asyncio

BOT_TOKEN = config('BOT_TOKEN', None)
CHANNEL_ID = int(config('CHANNEL_ID', None))

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())

@bot.event
async def on_ready():
    channel = bot.get_channel(CHANNEL_ID)
    embed = discord.Embed(
        title="Mystic Bot",
        description=f"List of Commands:\n -specials: Displays information on the top 5 games in the specials category on steam.\n -help: shows all bot commands.",
        color=discord.Color.red()
    )
    await channel.send(embed=embed)

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
        embed.add_field(name="Discount", value=game.discount, inline=True)
        embed.add_field(name="Dicounted Price", value=game.discounted_price, inline=True)

        match = re.search(r"(\d+)\%", game.monthly_ratings)
        rating_score = int(match.group(1))

        if (rating_score > 80):
            embed.add_field(name="Monthly Ratings👍", value=f"{game.monthly_ratings}", inline=False)
        elif (rating_score > 50):
            embed.add_field(name="Monthly Ratings😑", value=f"{game.monthly_ratings}", inline=False)
        else:
            embed.add_field(name="Monthly Ratings👎", value=f"{game.monthly_ratings}", inline=False)

        match = re.search(r"(\d+)\%", game.monthly_ratings)
        rating_score = int(match.group(1))

        if (rating_score > 80):
            embed.add_field(name="Overall Ratings👍", value=f"{game.all_ratings}", inline=False)
        elif (rating_score > 50):
            embed.add_field(name="Overall Ratings😑", value=f"{game.all_ratings}", inline=False)
        else:
            embed.add_field(name="Overall Ratings👎", value=f"{game.all_ratings}", inline=False)

        tags_string = ", ".join(game.tags)
        embed.add_field(name="Tags🏷️", value=tags_string, inline=False)

        embed.url = game.game_url

        await ctx.send(embed=embed)

    return

bot.run(BOT_TOKEN)