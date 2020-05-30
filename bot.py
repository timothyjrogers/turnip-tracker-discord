import os, json, sys, re
import asyncio
import datetime, pytz
import logging
import discord #https://discordpy.readthedocs.io/en/latest/index.html
from discord.ext import tasks

#Load config.json
config_path = os.path.abspath(os.path.dirname(__file__))
config_name = 'config.json'
config_fpath = os.path.join(config_path, config_name)
try:
    with open(config_fpath, 'r') as f:
        config = json.load(f)
except IOError as err:
    #Print statement because this error can only be thrown before the logger is initialized
    print('Unable to load config, make sure {} exists relative to bot.py.\n Printing error...\n{}'.format(config_name, err))
    sys.exit(1)

#Configure logging
log_level_enum = {'DEBUG': logging.DEBUG, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 'INFO': logging.INFO}
logger = logging.getLogger('log')
if config['LOG_TYPE'] == 'FILE':
    handler = logging.FileHandler(config['LOG_FILE_NAME'])
else:
    handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(log_level_enum[config['LOG_LEVEL']])

#Load secrets.json
secrets_path = os.path.abspath(os.path.dirname(__file__))
secrets_name = 'secrets.json'
secrets_fpath = os.path.join(secrets_path, secrets_name)
try:
    with open(secrets_fpath, 'r') as f:
        secrets = json.load(f)
except IOError as err:
    logger.critical('Unable to load secrets, make sure {} exists relative to bot.py. Printing error...'.format(secrets_name, err))
    sys.exit(1)

#Utility functions
def get_data_time():
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    weekday_to_index = {6: 0, 0: 1, 1: 3, 2: 5, 3: 7, 4: 9, 5: 11}
    day_of_week = weekday_to_index[now.weekday()]
    am_or_pm = 0 if now.hour < 12 else 1
    return day_of_week + am_or_pm if day_of_week != 0 else day_of_week

def get_data_label(data_time):
    data_labels_by_index = {0: 'Sun', 1: 'Mon(AM)', 2: 'Mon(PM)', 3: 'Tue(AM)', 4: 'Tue(PM)', 5: 'Wed(AM)', 6: 'Wed(PM)', 7: 'Thu(AM)', 8: 'Thu(PM)', 9: 'Fri(AM)', 10: 'Fri(PM)', 11: 'Sat(AM)', 12: 'Sat(PM)'}
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

def get_user_price_string(name, prices):
    price_string_pieces = []
    for idx, price in enumerate(prices):
        label = get_data_label(idx)
        price_string_pieces.append('{}: {}'.format(label, price))
    return '{}: {}'.format(name, ', '.join(price_string_pieces))

def get_today_price_string(user_prices):
    idx = get_data_time()
    label = get_data_label(idx)
    today_users = [name for name in list(user_prices.keys()) if len(user_prices[name]) == idx + 1]
    today_users.sort(key=lambda x: user_prices[x][-1], reverse=True)
    today_price_string_pieces = []
    for user in today_users:
        today_price_string_pieces.append('{}: {}'.format(user, user_prices[user][idx]))
    return '{} prices so far:\n{}'.format(label, '\n'.join(today_price_string_pieces))

def get_full_price_string(user_prices):
    msg_strs = []
    sorted_names = list(user_prices.keys())
    sorted_names.sort(key=lambda x: (len(user_prices[x]), user_prices[x][-1]), reverse=True)
    for name in sorted_names:
        user_price_string = get_user_price_string(name, user_prices[name])
        msg_strs.append(user_price_string)
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
    logger.info('Bot user {} has connected to Server {}'.format(client.user, guild.name))
    logger.info('{} will communicate in channel {}'.format(client.user, config['CHANNEL_NAME']))
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
    #!help
    if message.content.startswith('!help'):
        reply = 'The following commands are available:\n!help -- prints this message\n!setprice INT -- Sets your Islands price data for the current time increment\n!prices -- Retrieves all Islands\' price data for the current increment\n!myprices -- Retrieves your own prices for the week\n!today -- Retrieves the current time increment prices for all users who\'ve added them'
        await channel.send(message.author.mention + '\n' + reply)
    #!setprice
    elif message.content.startswith('!setprice'):
        fields = message.content.split(' ')
        if len(fields) != 2:
            logger.warning('{} sent invalid !setprice call'.format(message.author))
            await channel.send(message.author.mention + ' use the format !setprice PRICE')
            return
        abs_price = re.sub('^-', '', fields[1])
        if not abs_price.isdigit():
            logger.warning('{} sent !setprice with non-integer input'.format(message.author))
            await channel.send('{} your price must be an integer.'.format(message.author.mention))
            return
        price = int(fields[1])
        if price < 0:
            logger.warning('{} sent !setprice with negative input'.format(message.author))
            await channel.send('{} your price must greater than or equal to zero.'.format(message.author.mention))
            return
        result = set_price(message.author.name, price)
        if result[1]:
            logger.info('{} has replaced price for {} with {}'.format(message.author, result[0], price))
            await channel.send(message.author.mention + ' your price for {} has been replaced with {}.'.format(result[0], price))
        else:
            logger.info('{} has set price {} for {}'.format(message.author, price, result[0]))
            await channel.send(message.author.mention + ' your price of {} for {} has been saved.'.format(price, result[0]))
    #!prices
    elif message.content.startswith('!prices'):
        fields = message.content.split(' ')
        if len(fields) != 1:
            await channel.send(message.author.mention + ' use the format !prices')
            return
        reply = get_full_price_string(price_data['prices'])
        await channel.send(message.author.mention + '\n' + reply)
    elif message.content.startswith('!myprices'):
        fields = message.content.split(' ')
        if len(fields) != 1:
            await channel.send(message.author.mention + ' use the format !today')
            return
        reply = get_user_price_string(message.author.name, price_data['prices'][message.author.name])
        await channel.send('{} {}'.format(message.author.mention, reply))
    elif message.content.startswith('!today'):
        fields = message.content.split(' ')
        if len(fields) != 1:
            await channel.send(message.author.mention + ' use the format !today')
            return
        reply = get_today_price_string(price_data['prices'])
        await channel.send('{} {}'.format(message.author.mention, reply))
        
        
@tasks.loop(hours=1.0)
async def backup_data():
    #backup price JSON every hour
    backup_path = os.path.abspath(os.path.dirname(__file__))
    backup_name = 'backup.json'
    backup_fpath = os.path.join(backup_path, backup_name) 
    logger.info('Backing up price_data to {}...'.format(backup_name))
    with open(backup_fpath, 'w') as f:
        json.dump(price_data, f)
    logger.info('Backup complete.')

@backup_data.before_loop
async def backup_data_before():
    await client.wait_until_ready()
    logger.info('Registering backup_data task. Waiting until top of next hour to begin schedule...')
    delta = datetime.timedelta(hours=1)
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
    wait_seconds = (next_hour - now).seconds
    logger.info('Time until backup_data first runs: {} s'.format(wait_seconds))
    await asyncio.sleep(wait_seconds)

@tasks.loop(hours=24)
async def reset_data():
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
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    if now.weekday() == 6:        
        logger.info('Restetting price_data for the week')
        price_data = {'TIMESTAMP': datetime.date.today().strftime('%d/%m/%Y'), 'prices': {}}
        await channel.send('Data has been reset for the week.')

@reset_data.before_loop
async def reset_data_before():
    await client.wait_until_ready()
    logger.info('Registering reset_data task. Waiting until top of next day to begin schedule...')
    delta = datetime.timedelta(days=1)
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    next_5AM = (now + delta).replace(microsecond=0, second=0, minute=0, hour=5)
    wait_seconds = (next_5AM - now).seconds
    logger.info('Time until reset_data first runs: {} s'.format(wait_seconds))
    await asyncio.sleep(wait_seconds)

@tasks.loop(hours=24)
async def reminder_to_buy():
    #Get appropriate channel for replies
    logger.info('Sending reminder to buy to {}'.format(config['CHANNEL_NAME']))
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
    logger.info('Registering reminder_to_buy task. Waiting until top of next day to begin schedule...')
    delta = datetime.timedelta(days=1)
    now = datetime.datetime.now()
    next_5AM = (now + delta).replace(microsecond=0, second=0, minute=0, hour=5)
    wait_seconds = (next_5AM - now).seconds
    logger.info('Time until reminder_to_buy first runs: {} s'.format(wait_seconds))
    await asyncio.sleep(wait_seconds)

@tasks.loop(hours=24)
async def am_reminder_to_sell():
    #Get appropriate channel for replies
    logger.info('Sending AM reminder to sell to {}'.format(config['CHANNEL_NAME']))
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
    logger.info('Registering am_reminder_to_sell task. Waiting until next 8AM to begin schedule...')
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    if now.hour < 8:
        wait_seconds = (now.replace(hour=8) - now).seconds
    else:
        delta = datetime.timedelta(days=1)
        next_8AM = (now + delta).replace(microsecond=0, second=0, minute=0, hour=8)
        wait_seconds = (next_8AM - now).seconds
    logger.info('Time until am_reminder_to_sell first runs: {} s'.format(wait_seconds))
    await asyncio.sleep(wait_seconds)

@tasks.loop(hours=24)
async def pm_reminder_to_sell():
    #Get appropriate channel for replies
    logger.info('Sending PM reminder to sell to {}'.format(config['CHANNEL_NAME']))
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
    logger.info('Registering pm_reminder_to_sell task. Waiting until top of next day to begin schedule...')
    now = datetime.datetime.now(pytz.timezone(config['TIMEZONE']))
    if now.hour < 12:
        wait_seconds = (now.replace(hour=12) - now).seconds
    else:
        delta = datetime.timedelta(days=1)
        next_12PM = (now + delta).replace(microsecond=0, second=0, minute=0, hour=12)
        wait_seconds = (next_12PM - now).seconds
    logger.info('Time until pm_reminder_to_sell first runs: {} s'.format(wait_seconds))
    await asyncio.sleep(wait_seconds)

#Backing data for the bot
price_data = {'TIMESTAMP': datetime.date.today().strftime('%d/%m/%Y'), 'prices': {}}
try:
    last_sunday = datetime.datetime.now(pytz.timezone(config['TIMEZONE'])) - datetime.timedelta(days=datetime.date.today().weekday() + 1)
    with open('backup.json', 'r') as f:
        data = json.load(f)
        tstamp = datetime.datetime.strptime(data['TIMESTAMP'], '%d/%m/%Y')
        if last_sunday.day == tstamp.day and last_sunday.month == tstamp.month and last_sunday.year == tstamp.year:
            logger.info('Initializing data from backup.json...')
            price_data = data
except IOError as err:
    logger.info('No backup file found, starting fresh price data.')

#Start the bot
try:
    backup_data.start()
    reset_data.start()
    if config['ENABLE_SUNDAY_REMINDER'] == 'True':
        reminder_to_buy.start()
    if config['ENABLE_AM_REMINDER'] == 'True':
        am_reminder_to_sell.start()
    if config['ENABLE_PM_REMINDER'] == 'True':
        pm_reminder_to_sell.start()
    client.run(secrets['DISCORD_TOKEN'])
except KeyError as err:
    logger.critical('Unable to start the bot. Please make sure DISCORD_TOKEN is set in secrets.json')
    sys.exit(1)
except Exception as err:
    logger.critical('Unknown error starting the bot. Printing error...\n{}'.format(err))
    sys.exit(1)