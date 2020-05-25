import os, json
import discord #https://discordpy.readthedocs.io/en/latest/index.html

#Load config.json
config_path = os.path.abspath(os.path.dirname(__file__))
config_name = 'config.json'
config_fpath = os.path.join(config_path, config_name)
try:
    with open(config_fpath, 'r') as f:
        data = json.load(f)
        BOT_NAME = data['BOT_NAME']
        GUILD_NAME = data['GUILD']
        CHANNEL_NAME = data['CHANNEL']
except KeyError as err:
    print('Unable to find all config keys, make sure {} still has all keys.\nPrinting error...\n{}'.format(config_fname, err)
except Exception as err:)
    print('Unable to load config, make sure {} exists relative to bot.py.\n Printing error...\n{}'.format(config_fname, err))

#Load secrets.json
load_secrets()
secrets_path = os.path.abspath(os.path.dirname(__file__))
secrets_name = 'secrets.json'
secrets_fpath = os.path.join(secrets_path, secrets_name)
try:
    with open(secrets_fpath, 'r') as f:
        secrets = json.load(f)
except Exception as err:
    print('Unable to load secrets, make sure {} exists relative to bot.py.\n Printing error...\n{}'.format(secrets_name, err))

#Discord client and events
self.client = discord.Client()

@client.event
async def on_ready():
    guild = None
    for g in client.guilds():
        if g.name == GUILD_NAME:
            guild = g
            break
    print('Bot user {} has connected to Server/Channel {}\nThe bot will communicate in channel {}'.format(client.user, guild.name, CHANNEL_NAME))
    channel = None
    for c in guild.channels:
        if c.name == CHANNEL_NAME:
            channel = c
            break
    #TODO throw exception if channel not found
    await channel.send('{} has joined the channel.'.format(BOT_NAME))
    

#Start the bot
try:
    client.run(secrets['DISCORD_TOKEN'])
except KeyError as err:
    print('Unable to start the bot. Please make sure DISCORD_TOKEN is set in secrets.json')
except Exception as err:
    print('Unknown error starting the bot. Printing error...\n{}'.format(err))