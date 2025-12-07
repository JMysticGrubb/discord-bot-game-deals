# Mystic Bot (Discord): Sale Tracker and Rating System

An automated general purpose discord bot that handles game sales and deals along with user ratings.

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
- [How It's Made](#how-its-made)
- [Optimizations](#optimizations)

## Features
* **Steam Sales:** Outputs the top 5 games in the specials category on steam store to a discord channel.
* **Epic Games Free:** Outputs the free games from the week from Epic Games to a discord channel.
* **Rating System:** Stores user info and user ratings into a database.

## Getting Started
### Prequisites
* Python
* A Discord Account
* A Database

1. Set up a discord bot within the developer portal on Discord
* Create a new application
* Generate a Bot Token 
2. Clone the repo
```
git clone https://github.com/JMysticGrubb/discord-bot-game-deals.git
```
3. Start a virtual environment
```
python -m venv .venv
```
4. Activate the venv
* Windows (powershell): `.venv/Scripts/activate.ps1`
* Windows (command prompt): `.venv/Scripts/activate.bat`
* Linux/macOS: `source .venv/bin/activate`
5. Install the dependencies
```
pip install -r requirements.txt
```
6. Create a .env following this format:
```env
# Discord Bot Token
DISCORD_TOKEN=YourBotTokenHere

# Channel ID for the bot to post messages in
BOT_CHANNEL_ID=123456789012345678

# Database connection string
DATABASE_PATH=sqlite:///data/bot.db
```
7. Run the Bot
```
python mysticbot.py
```

## How It's Made
**Core Technologies:** Python, SQLite, requests, BeautifulSoup, discord.py

## Optimizations
Initially started by using files and regular expressions to parse HTML retrieved using the requests library. I transitioned to using BeautifulSoup to effectively and efficiently parse the HTML and better handle oddities within HTML. Furthermore, using the threading Python library allows my bot to parse multiple HTML pages simultaneously. Together, these changes made the "specials" command, which retrieves the top 5 game sales on Steam, retrieve and display the sales roughly four times faster, from 8 seconds to taking around 2 seconds.