import os, json
import asyncio
import datetime, pytz
import discord #https://discordpy.readthedocs.io/en/latest/index.html
from discord.ext import tasks

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
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    weekday_to_index = {6: 0, 0: 1, 1: 3, 2: 5, 3: 7, 4: 9, 5: 11}
    day_of_week = weekday_to_index[now.weekday()]
    am_or_pm = 0 if now.hour < 12 else 1
    return day_of_week + am_or_pm if day_of_week != 0 else day_of_week

def get_data_label(data_time):
    data_labels_by_index = {0: 'SUN', 1: 'MON(AM)', 2: 'MON(PM)', 3: 'TUES(AM)', 4: 'TUES(PM)', 5: 'WED(AM)', 6: 'WED(PM)', 7: 'THURS(AM)', 8: 'THURS(PM)', 9: 'FRI(AM)', 10: 'FRI(PM)', 11: 'SAT(AM)', 12: 'SAT(PM)'}
    return data_labels_by_index[data_time]

def set_price(name, price):
    time = get_data_time()
    label = get_data_label(time)
    replace = False
    if name not in price_data['prices']:
        price_data['prices'][name] = []
    if len(price_data['prices'][name]) == time + 1:
        replace = True
        price_data['prices'][name][time] = price
    else:
        while(len(price_data['prices'][name]) < time + 1):
            price_data['prices'][name].append(0)
        price_data['prices'][name][time] = price
    return (label, replace)

def get_full_price_string():
    msg_strs = []
    for name in price_data['prices']:
        name_strs = [name + ':']
        for idx, price in enumerate(price_data['prices'][name]):
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
    print('Bot user {} has connected to Server {}\nThe bot will communicate in channel {}'.format(client.user, guild.name, config['CHANNEL_NAME']))
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
        
@tasks.loop(hours=1.0)
async def backup_data():
    #backup price JSON every hour
    backup_path = os.path.abspath(os.path.dirname(__file__))
    backup_name = 'backup.json'
    backup_fpath = os.path.join(backup_path, backup_name) 
    print('Backing up price_data to {}...'.format(backup_name))
    with open(backup_fpath, 'w') as f:
        json.dump(price_data, f)
    print('Backup complete.')
    

@backup_data.before_loop
async def backup_data_before():
    await client.wait_until_ready()
    print('Registering backup_data task. Waiting until top of next hour to begin schedule...')
    delta = datetime.timedelta(hours=1)
    now = datetime.datetime.now()
    next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
    wait_seconds = (next_hour - now).seconds
    print ('Time until backup_data first runs: {} s'.format(wait_seconds))
    await asyncio.sleep(wait_seconds)

@tasks.loop(hours=24)
async def reset_data():
    #Get appropriate channel for replies
    print('Restetting price_data for the week')
    price_data = {'TIMESTAMP': datetime.date.today().strftime('%d/%m/%Y'), 'prices': {}}

@reset_data.before_loop
async def reset_data_before():
    await client.wait_until_ready()
    print('Registering reset_data task. Waiting until top of next day to begin schedule...')
    delta = datetime.timedelta(days=1)
    now = datetime.datetime.now()
    next_5AM = (now + delta).replace(microsecond=0, second=0, minute=0, hour=5)
    wait_seconds = (next_5AM - now).seconds
    print ('Time until reset_data first runs: {} s'.format(wait_seconds))
    await asyncio.sleep(wait_seconds)

@tasks.loop(hours=24)
async def reminder_to_buy():
    #Get appropriate channel for replies
    print('Sending reminder to buy to {}'.format(config['CHANNEL_NAME']))
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
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    if now.weekday() == 6:
        await channel.send('@everyone Don\'t forget to buy your turnips!')

@reminder_to_buy.before_loop
async def reminder_to_buy_before():
    await client.wait_until_ready()
    print('Registering reminder_to_buy task. Waiting until top of next day to begin schedule...')
    delta = datetime.timedelta(days=1)
    now = datetime.datetime.now()
    next_5AM = (now + delta).replace(microsecond=0, second=0, minute=0, hour=5)
    wait_seconds = (next_5AM - now).seconds
    print ('Time until reminder_to_buy first runs: {} s'.format(wait_seconds))
    await asyncio.sleep(wait_seconds)

@tasks.loop(hours=24)
async def am_reminder_to_sell():
    #Get appropriate channel for replies
    print('Sending AM reminder to sell to {}'.format(config['CHANNEL_NAME']))
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
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    if now.weekday() != 6:
        await channel.send('@everyone Don\'t forget to check morning turnip prices!')

@am_reminder_to_sell.before_loop
async def am_reminder_to_sell_before():
    await client.wait_until_ready()
    print('Registering am_reminder_to_sell task. Waiting until next 8AM to begin schedule...')
    now = datetime.datetime.now()
    if now.hour < 8:
        wait_seconds = (now.replace(hour=8) - now).seconds
    else:
        delta = datetime.timedelta(days=1)
        next_8AM = (now + delta).replace(microsecond=0, second=0, minute=0, hour=8)
        wait_seconds = (next_8AM - now).seconds
    print ('Time until am_reminder_to_sell first runs: {} s'.format(wait_seconds))
    await asyncio.sleep(wait_seconds)

@tasks.loop(hours=24)
async def pm_reminder_to_sell():
    #Get appropriate channel for replies
    print('Sending PM reminder to sell to {}'.format(config['CHANNEL_NAME']))
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
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    if now.weekday() != 6:
        await channel.send('@everyone Don\'t forget to check afternoon turnip prices!')

@pm_reminder_to_sell.before_loop
async def pm_reminder_to_sell_before():
    await client.wait_until_ready()
    print('Registering pm_reminder_to_sell task. Waiting until top of next day to begin schedule...')
    now = datetime.datetime.now()
    if now.hour < 12:
        wait_seconds = (now.replace(hour=12) - now).seconds
    else:
        delta = datetime.timedelta(days=1)
        next_12PM = (now + delta).replace(microsecond=0, second=0, minute=0, hour=12)
        wait_seconds = (next_12PM - now).seconds
    print ('Time until pm_reminder_to_sell first runs: {} s'.format(wait_seconds))
    await asyncio.sleep(wait_seconds)

#Backing data for the bot
price_data = {'TIMESTAMP': datetime.date.today().strftime('%d/%m/%Y'), 'prices': {}}
try:
    last_sunday = datetime.datetime.now() - datetime.timedelta(days=datetime.date.today().weekday() + 1)
    with open('backup.json', 'r') as f:
        data = json.load(f)
        tstamp = datetime.datetime.strptime(data['TIMESTAMP'], '%d/%m/%Y')
        if last_sunday.day == tstamp.day and last_sunday.month == tstamp.month and last_sunday.year == tstamp.year:
            print('Initializing data from backup.json...')
            price_data = data
except IOError as err:
    print('No backup file found, starting fresh price data.')

#Start the bot
try:
    backup_data.start()
    if config['ENABLE_SUNDAY_REMINDER'] == 'True':
        reminder_to_buy.start()
    if config['ENABLE_AM_REMINDER'] == 'True':
        am_reminder_to_sell.start()
    if config['ENABLE_PM_REMINDER'] == 'True':
        pm_reminder_to_sell.start()
    client.run(secrets['DISCORD_TOKEN'])
except KeyError as err:
    print('Unable to start the bot. Please make sure DISCORD_TOKEN is set in secrets.json')
except Exception as err:
    print('Unknown error starting the bot. Printing error...\n{}'.format(err))