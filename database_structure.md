# Database structure

For this bot to work, we need two databases. These are created following the steps in README.md.
In the following, we are looking to give a more detailed look into what data is stored where in the databases.
Keep in mind though that the database structure is not complete yet. This guide should describe the structure as of this moment and be uupdated regularly.

## 1. Database "auth"

"auth" is the database storing which users are allowed to talk to the bot, i.e. allowed to modify the database. Since telegram bots are public, we password-protected ours.

### 1.1 Table "users"

"users" has only one field, which is "id". 

Upon /start or /key and after providing the correct passphrase, the chat ID where the command was issued from is stored in here.
While this table could easily be just another table in the actual database, we decided to seperate the two for security reasons. 

By using ```SELECT * FROM users``` we get:

    +------------+
    | id         |
    +------------+
    | [DATA]     |
    +------------+

## 2. Database "testdb"

This is the main database. Everything the bot is actually working with is stored here.

### 2.1 Table "games"
This table is for boardgames. They get a unique hash generated upon being added.
- "games" has six fields: "title", "owner", "playercount", "game_uuid", "categories" and "last_played".
- "title" refers to the game title, i.e. a string.
- "owner" refers to the owners of this game, identified by username (i.e. alias). More than one owner is possible if the game is owned by a household (see below).
- "playercount" is the maximum amount of players you can play this game with. "X" means infinite. This information is crucial for the poll options generator!
- "game_uuid" is a hash generated uniquely for this owner-title relationship.
- "categories" keeps track of the categories this game belongs to. Different categories are separated by "/".
- "last_played" contains either NULL or the date when this game last won a poll.

By using ```SELECT * FROM games``` we get:

    +---------------+------------------------+---------------------+-------------------+---------------------+
    | title         | owner                  | playercount         | game_uuid         | last_played         |
    +---------------+------------------------+---------------------+-------------------+---------------------+
    | titlegoeshere | useridgoeshere         | playercountgoeshere | game_uuidgoeshere | dategoeshere        |
    +---------------+------------------------+---------------------+-------------------+---------------------+

### 2.2 Table "households"
"households" has only one field which is "user_ids".

In "user_ids" all the usernames (i.e. aliases) of people living together are stored. That way, not every one of them has to register every game they own - instead, the bot knows they're living together so everyone has access to the same games and keeps it in mind while planning game night. 

By using ```SELECT * FROM households``` we get:
    
    +---------------------+
    | user_ids            |
    +---------------------+
    | [user or household] |
    +---------------------+


### 2.3 Table "expansions"
This table is for expansions. It has three fields: "basegame_uuid", "title" and "owner".
- "basegame_uuid" is the unique hash which was assigned to the basegame this expansion belongs to, i.e. the owner-boardgame relation.
- "title" is the title of the expansion.
- "owner" is the owner of the expansion.
 
By using ```SELECT * FROM expansions``` we get:

    +---------------+---------------+-----------------------+
    | title         | owner         | basegame_uuid         |
    +---------------+---------------+-----------------------+
    | titlegoeshere | ownergoeshere | basegame_uuidgoeshere |
    +---------------+---------------+-----------------------+


### 2.4 Table "settings"
This table keeps track of user settings. It has three fields: "user", "notify_participation" and "notify_vote".
- "user" is the username/alias for a user.
- "notify_participation" contains a bit (default is 1) stating whether this user wants to be notified upon participating.
- "notify_vote" contains a bit (default is 1) stating whether this user wants to be notified upon voting.

By using ```SELECT * FROM settings``` we get:

+--------------+----------------------+-------------+
| user         | notify_participation | notify_vote |
+--------------+----------------------+-------------+
| usergoeshere | BITgoeshere          | BITgoeshere |
+--------------+----------------------+-------------+


### 2.5 Table "categories"
This table keeps track of what games belong into which categories. It has a minimum of two fields: "kurz" and "lang", but can have more.
Other fields can be defined when running [configure](configure#L94).

On column in this table corresponds to one category. A category contains all the unique hashes from ["games"](database_structure.md#21-table-games) that belong to this category.

By using ```SELECT * FROM categories``` we get:

+--------------+---------------+--------------+
| kurz         | lang          | category_3   | ...
+--------------+---------------+--------------+
| uuidgoeshere | uuidgoeshere  | uuidgoeshere | ...
+--------------+---------------+--------------+