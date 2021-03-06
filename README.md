# turnip-tracker-discord

This is a simple helper bot for Animal Crossing New Horizons turnip stuff for use in a Discord server. It performs the following actions:

* Automatic reminders on Sunday mornings to purchase turnips (enable/disable in config)
* Automatic reminders on non-Sunday mornings and afternoons to check prices (enable/disable in config)
* Allow players to submit their turnip prices to the bot for tracking
* Allow players to request turnip prices for all participants from the bot
* Hourly backup of price data to disk

# Configuration

## Discord Setup
Before using this bot you must create a discord developer account and createt an application and a bot and allow the bot access to your server. Refer to the [official documentation](https://discord.com/developers/docs/intro) for guidance.

## secrets.json
In order to authenticate your bot to your server it needs access to the Discord token you created for it when you created the bot. Create a file named **secrets.json** in this directory and fill it in as such:

```javascript
{
    "DISCORD_TOKEN": "YOUR_TOKEN_HERE"
}
```

This file will be loaded by the bot on startup to acquire the token. Keep the token safe as per the official guidance.

## Configuration in config.json
The config.json file contains a handful of configurable items.

* BOT_NAME -- This should match the name of the bot you configured in the developer portal. It is used in certain log messages and server responses.
* GUILD_NAME -- This is the name of your Discord server that the Bot has joined
* CHANNEL_NAME -- This is the name of the channel you want the bot to send messages to and listen for messages in
* TIMEZONE -- This is your timezone (using the [tz database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)) used in scheduling reminders
* ENABLE_SUNDAY_REMINDER -- This enables or disables the Sunday morning reminder to buy turnips. This reminder goes to @everyone
* ENABLE_AM_REMINDER -- This enables or disables the non-Sunday morning reminder to check turnip prices. This reminder goes to @everyone
* ENABLE_PM_REMINDER -- This enables or disables the non-Sunday afternoon reminder to check turnip prices. This reminder goes to @everyone
* LOG_LEVEL -- The Python [logging module log level](https://docs.python.org/3/library/logging.html#levels) you want the bot to use. Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
* LOG_TYPE -- Options are FILE or STDOUT
* LOG_FILE_NAME -- The name of the log file to write if LOG_TYPE=FILE. If an absolute path is not given it will be written relative to bot.py.
* HELP_CMD_COOLDOWN_PERIOD -- Cooldown timeframe for !help command in seconds
* HELP_CMD_COOLDOWN_LIMIT -- Number of !help commands allowed in cooldown period
* HELP_CMD_COOLDOWN_SCOPE -- Who the !help cooldown applies to: USER or CHANNEL
* PRICES_CMD_COOLDOWN_PERIOD -- Cooldown timeframe for !prices command in seconds
* PRICES_CMD_COOLDOWN_LIMIT -- Number of !prices commands allowed in cooldown period
* PRICES_CMD_COOLDOWN_SCOPE -- Who the !prices cooldown applies to: USER or CHANNEL
* MYPRICES_CMD_COOLDOWN_PERIOD -- Cooldown timeframe for !myprices command in seconds
* MYPRICES_CMD_COOLDOWN_LIMIT -- Number of !myprices commands allowed in cooldown period
* MYPRICES_CMD_COOLDOWN_SCOPE -- Who the !myprices cooldown applies to: USER or CHANNEL
* TODAY_CMD_COOLDOWN_PERIOD -- Cooldown timeframe for !today command in seconds
* TODAY_CMD_COOLDOWN_LIMIT -- Number of !today commands allowed in cooldown period
* TODAY_CMD_COOLDOWN_SCOPE -- Who the !today cooldown applies to: USER or CHANNEL
* SETPRICE_CMD_COOLDOWN_PERIOD -- Cooldown timeframe for !setprice command in seconds
* SETPRICE_CMD_COOLDOWN_LIMIT -- Number of !setprice commands allowed in cooldown period
* SETPRICE_CMD_COOLDOWN_SCOPE -- Who the !setprice cooldown applies to: USER or CHANNEL

## Backups
Once per hour, at the top of the hour, the current in-memory data for your servers participants is backed up to a file called **backup.json**. This file overwrites the previous backup each time.

## Running the Bot

Once you've configured the bot in your server and adjusted **config.json** and **secrets.json** appropriately you can launch the bot as such:

```bash
pip install -r requirements.txt
python bot.py
```

Note that the bot requires Python 3.