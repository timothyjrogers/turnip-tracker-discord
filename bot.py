import os, json
import discord #https://discordpy.readthedocs.io/en/latest/index.html
import datetime, pytz

#Load config.json
config_path = os.path.abspath(os.path.dirname(__file__))
config_name = 'config.json'
config_fpath = os.path.join(config_path, config_name)
try:
    with open(config_fpath, 'r') as f:
        config = json.load(f)
except KeyError as err:
    print('Unable to find all config keys, make sure {} still has all keys.\nPrinting error...\n{}'.format(config_name, err))
except Exception as err:
    print('Unable to load config, make sure {} exists relative to bot.py.\n Printing error...\n{}'.format(config_name, err))

#Load secrets.json
secrets_path = os.path.abspath(os.path.dirname(__file__))
secrets_name = 'secrets.json'
secrets_fpath = os.path.join(secrets_path, secrets_name)
try:
    with open(secrets_fpath, 'r') as f:
        secrets = json.load(f)
except Exception as err:
    print('Unable to load secrets, make sure {} exists relative to bot.py.\n Printing error...\n{}'.format(secrets_name, err))

#Utility functions
def get_data_time():
    datetime_data_map = []
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    day_of_week = now.weekday() + 1 if now.weekday() != 6 else 0
    am_or_pm = 0 if now.hour < 12 else 1
    return day_of_week + am_or_pm if day_of_week != 0 else day_of_week

def get_data_label(data_time):
    data_labels_by_index = {0: 'SUN', 1: 'MON(AM)', 2: 'MON(PM)', 3: 'TUES(AM)', 4: 'TUES(PM)', 5: 'WED(AM)', 6: 'WED(PM)', 7: 'THURS(AM)', 8: 'THURS(PM)', 9: 'FRI(AM)', 10: 'FRI(PM)', 11: 'SAT(AM)', 12: 'SAT(PM)'}
    return data_labels_by_index[data_time]

def set_price(name, price):
    time = get_data_time()
    label = get_data_label(time)
    replace = False
    if name not in price_data:
        price_data[name] = []
    if len(price_data[name]) == time + 1:
        replace = True
        price_data[name][time] = price
    else:
        while(len(price_data[name]) < time):
            price_data[name].append(0)
        price_data[name].append(price)
    return (label, replace)

def get_full_price_string():
    msg_strs = []
    for name in price_data:
        name_strs = [name + ':']
        for idx, price in enumerate(price_data[name]):
            label = get_data_label(idx)
            name_strs.append('{}: {}'.format(label, price))
        msg_strs.append('  '.join(name_strs))
    return '\n'.join(msg_strs)

#Discord client and events
client = discord.Client()

@client.event
async def on_ready():
    guild = None
    for g in client.guilds:
        if g.name == config['GUILD_NAME']:
            guild = g
            break
    print('Bot user {} has connected to Server/Channel {}\nThe bot will communicate in channel {}'.format(client.user, guild.name, config['CHANNEL_NAME']))
    channel = None
    for c in guild.channels:
        if c.name == config['CHANNEL_NAME']:
            channel = c
            break
    #TODO throw exception if channel not found
    await channel.send('{} has joined the channel.\nNote: All bot times are using {}'.format(config['BOT_NAME'], config['TIMEZONE']))

@client.event
async def on_message(message):
    #bot should not reply to itself
    if message.author == client.user:
        return
    #Get appropriate channel for replies
    guild = None
    for g in client.guilds:
        if g.name == config['GUILD_NAME']:
            guild = g
            break
    channel = None
    for c in guild.channels:
        if c.name == config['CHANNEL_NAME']:
            channel = c
            break
    #Process help command
    if message.content.startswith('!help'):
        reply = 'The following commands are available:\n!help -- prints this message\n!setprice INT -- Sets your Islands price data for the current time increment\n!prices -- Retrieves all Islands\' price data for the current increment'
        await channel.send(message.author.mention + '\n' + reply)
    elif message.content.startswith('!setprice'):
        fields = message.content.split(' ')
        if len(fields) != 2:
            await channel.send(message.author.mention + ' use the format !setprice PRICE')
            return
        try:
            price = int(fields[1])
            result = set_price(message.author.name, price)
        except TypeError as err:
            await channel.send(message.author.mention + ' your price must be an integer.')
            print(err)
            return
        if result[1]:
            await channel.send(message.author.mention + ' your price for {} has been replaced with {}.'.format(result[0], price))
        else:
            await channel.send(message.author.mention + ' your price of {} for {} has been saved.'.format(price, result[0]))
        print('{} has set price {} for {}'.format(message.author, price, result[0]))
    elif message.content.startswith('!prices'):
        fields = message.content.split(' ')
        if len(fields) != 1:
            await channel.send(message.author.mention + ' use the format !prices')
            return
        reply = get_full_price_string()
        await channel.send(message.author.mention + '\n' + reply)
        

#Backing data for the bot
price_data = {}

#Start the bot
try:
    client.run(secrets['DISCORD_TOKEN'])
except KeyError as err:
    print('Unable to start the bot. Please make sure DISCORD_TOKEN is set in secrets.json')
except Exception as err:
    print('Unknown error starting the bot. Printing error...\n{}'.format(err))