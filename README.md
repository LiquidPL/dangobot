# dangobot [![Build](https://github.com/LiquidPL/dangobot/actions/workflows/build.yml/badge.svg?branch=master&event=push)](https://github.com/LiquidPL/dangobot/actions/workflows/build.yml)

A small Discord bot written using [Discord.py](https://github.com/Rapptz/discord.py).

# Features

* custom commands with text/file responses,
* `!roll` command using the [common dice notation](https://en.wikipedia.org/wiki/Dice_notation).

# Requirements

* Python 3.9
* a PostgreSQL database

# Setup

Clone the repo into a location of your choice, and run `pipenv sync`. Then you can configure the bot using an `.env` file. An example configuration is provided in the `.env.example` file.

```
# cp .env.example .env
```

The absolute required configuration variables are:

* database configuration (all `DATABASE_...` variables),
* the [Discord bot token](https://discord.com/developers) (`BOT_TOKEN`).

Once you've provided the necessary configuration variables, you can create the database tables, and start the bot by running those commands in the project root:

```
# ./manage.py migrate
# ./manage.py startbot
```

There is also a [Docker image](https://github.com/users/LiquidPL/packages/container/package/dangobot) available, using the same environment variables for configuration. An example Docker Compose configuration, including a Postgres database, is available in the [`docker-compose.production.yml` file](https://github.com/LiquidPL/dangobot/blob/master/docker-compose.production.yml).
