# Boardgame-Bot

Here is a Boardgame Bot under Construction.

OLD Code can be found in the OLD-GScript Folder so far 

new one has no Structure yet.

If you want to test the Code locally you may do so but have to meet the requirements.

    - Python 2.xx oder 3.xx 
    - python-telegram-bot
    - maria-db environment

## Quick Start 

To get started locally I recommend not just installing python (duh)
but also to use an IDE that helps with formatting and testing.

For this reason I use [**PyCharm**](https://www.jetbrains.com/pycharm/)

### Dependencies

to install the [Telegram Bot Framework](https://python-telegram-bot.org/) pip should also be installed:

```shell
sudo apt-get install python-pip
sudo pip install python-telegram-bot
```

afterwards we may test if everything is working by executing inside an Python Environment:

``` Shell
import telegram.ext
```

~~And that's it!~~

Almost... for the integration of the Database we need to import mysql connector
```
pip install mysql-connector
```
### Database

First install Mariadb:

```apt install mariadb-server``` 

you may now set an password for your DB Root user,
 iirc. this defaults to either nothing or root pw.
 
afterwards we log in to the db to create the two databases and the testuser. 

```mysql -u root -p```

and execute the Querys:

```
CREATE DATABASE testdb;
CREATE DATABASE auth;
CREATE USER 'testuser' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON testdb.* TO testuser;
GRANT ALL PRIVILEGES ON auth.* TO testuser;
FLUSH PRIVILEGES;
quit
```  
after that we switch to our testuser:
```
mysql -u testuser -p
USE testdb;
CREATE TABLE games (title VARCHAR(255), owner VARCHAR(255), playercount VARCHAR(255));
CREATE TABLE households (user_ids VARCHAR(255));
USE auth;
CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY);
quit
```

if that does not throw any errors like user not found or database not found we are good to go!


NOW you are good to go and may start working on our lovely bot!
