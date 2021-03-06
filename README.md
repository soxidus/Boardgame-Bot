# Boardgame-Bot

<img align="right" width="200" height="200" src="meeple-bot.png">


This is a Boardgame Bot under construction.

It allows a group of friends who like to play boardgames to (potentially) over-engineer their organization: Users can tell the bot which boardgames (and expansions) they own, they can set up a date for game night and then sign up for it. And the best part: You'll never have to discuss what to play again! When everyone feels ready, the bot can select six games from everyone attending game night (making sure that you're not too many people for it, and that different types of games are considered) and generate a poll where every participant gets one vote.

The code can be found in [src](src/). In [infrastructure](infrastructure/), you can also find all files related to docker database setup (and also a [README.md](infrastructure/README.md) explaining how to use them).

## Prerequisites

If you want to test the code locally feel free to do so but you have to meet the requirements:

    - Python 3.xx
    - python-telegram-bot
    - maria-db environment

Instructions can be found below.

## Quick Start

To get started locally I recommend not just installing python3
but also to use an IDE that helps with formatting and testing.

The Coding-Style is [**PEP8**](https://www.python.org/dev/peps/pep-0008/).

### Dependencies

To install the [Telegram Bot Framework](https://python-telegram-bot.org/), pip should also be installed:

```shell
sudo apt-get install python3-pip
pip3 install python-telegram-bot
```

Afterwards you may test whether everything is working by executing inside an Python Environment:

``` Shell
import telegram.ext
```

~~And that's it!~~

Almost... for the integration of the database you need mysql connector:
```
pip3 install mysql-connector
```

### Get your own Telegram Bot!

Have a chat with the BotFather and create your own bot.
If you don't know what I mean by that, have a look here: [Bots: An introduction for developers](https://core.telegram.org/bots#botfather)
The Botfather is going to give you a token for your bot. Hold on to that, you're going to need it!

### Configuration

Enjoy the comfort of an interactive approach on configuration by running ``./configure``.
Or, if you don't like being asked helpful questions by your CLI, here's your guide to DIY:

There's two configuration files you will need to take care of: [src/config.ini](src/config.ini.example) and [infrastructure/.env](infrastructure/.env.example). The latter is important for the Docker setup and will be dealt with later. For now,
find [src/config.ini.example](src/config.ini.example) and rename your local copy of it to 'src/config.ini'.
Then, modify the values held within:

#### Bot
This is where you enter the token the Botfather gave you.

#### Authentication
Think of a nice password. When other people try to talk to your bot (it's publicly visible in the Telegram Botverse), they'll have to know this password in order to do anything useful with it - including accessing your databases.

#### MySQL
All these are values that you will need to access the database(s). Just complete/modify them! If you want the databases to run locally, set `host = localhost`.

#### Game Categories
Here, you can find some default categories for games. Feel free to change them up! If you do, adjust the fields of the categories table accordingly in [infrastructure/init_data_categories.sql](infrastructure/init_data_categories.sql). And make sure you keep categories "lang" (long) and "kurz" (short)! Otherwise... things might (will) go wrong.

#### Group Details
This is where you enter your group's name.

### Docker setup

Our databases and the bot run in Docker containers. To set them up, please refer to [infrastructure/README.md](infrastructure/README.md).

Of course, it is also possible to run the bot locally on your device (for testing purposes, for example), and the databases, too. For this, please refer to [infrastructure/README.md](infrastructure/README.md#(2)LocalSetup).

If that didn't throw any errors, you now have a database structure like the one described in [database_structure.md](database_structure.md).
Have a closer look at it if you are not entirely sure what you just did!


### Your Telegram Group
You will need a group to use the full functionality of this bot. While creating a group in Telegram is quite straight-forward, there are a few things to keep in mind:

* For full functionality, give your bot administrator rights.
* Again for full functionality, every member should start a private chat with the bot.
* All your members should have their Telegram alias configured. This is how they are identified as unique users by the bot.

If you don't give your bot administrator rights, he'll tell you. And if you continue to not give him administrator rights, he will continue to tell you. If you're doing this on purpose, you can disable the bot's notification using `/einstellungen` in the group chat. The same applies to members not having a private chat with the bot. It does not, however, apply to the alias issue - since a lot of things stop to work, telegram users without an alias simply cannot authenticate with the bot.

> **_NOTE:_** You do not want to use one bot with more than one group. The GameNight object is a Singleton and it has only one field for a PollObject. So if you use more than one group, you cannot plan game nights in both of them at the same time. You would have to wait for one group to finish planning theirs before the other can start. If you'd like to use it with more than one group, you're welcome to fork this repo and start working on it! It's probably not something we will implement ourselves in the near future (well, honestly, you never know when motivation strikes).


And there you go, you are now all set up and may start working on our lovely bot!
