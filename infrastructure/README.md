# Configuration to deploy and or test the bot

You can decide to run one or more of the three components (bot, datadb and authdb) locally instead of inside a docker container. If you decide to do so, please follow the instructions for a [local setup](#Local-setup) before continuing.

## Docker instructions

### Docker Setup

#### Installation
```
sudo apt install docker.io
sudo apt install docker-compose
```

Instead of ``sudo apt``, you can also use snap: 
``snap install docker``. Sometimes, this works better. If you face problems setting it up, you could also have a look at [the official docker installation guidelines](https://docs.docker.com/install/).

#### Prepare your docker configuration
If you previously ran ``./configure`` when following our guide at [README.md](../README.md), just continue with the next section.
Otherwise, you'll have to set some variables first. 

Find [.env.example](.env.example) and rename your local copy of it to '.env'. Then, modify the values held within:

- MYSQL_ROOT_PASSWORD will the root password for both the authentication and the data database
- MYSQL_USER has to be the same as the user in the MySQL field of your config.ini
- MYSQL_PASSWORD has to be the same as the password in the MySQL field of your config.ini

The values in .env will be read by docker-compose and make sure you have everything you need to access your databases once they are running.

#### Docker, up!

Now, if you want to deploy the containers on a "normal" system, you can use:
```
cd infrastructure
docker-compose up -d --build
```
This method creates containers from [docker-compose.yaml](docker-compose.yaml). "Normal" in this case means that it's able to run a mariadb docker image. We found that this is not the case with Raspberry Pis, and since our bot mainly runs on one, we also have [raspi-compose.yaml](raspi-compose.yaml) which uses another image. To run this instead, use:
```
cd infrastructure
docker-compose -f raspi-compose.yaml up -d --build
```

#### Docker, are you there?
After the previous init execute: ``docker ps``

Your output should look something like this:
```
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
4a7cfd860a4d        mariadb:latest      "docker-entrypoint.s…"   13 hours ago        Up 1 second         0.0.0.0:4444->3306/tcp   data_db
7d6f6327b4f2        mariadb:latest      "docker-entrypoint.s…"   13 hours ago        Up 2 seconds        0.0.0.0:3333->3306/tcp   auth_db
1036fc1d2ee1        infrastructure_bot   "/bin/bash"              6 minutes ago       Up About a minute                             bot
```

If you see this, your database containers should be up and running. Bear in mind that data_db and auth_db take time to set up the databases. It can be several minutes until the bot script is able to connect to the databases, so don't worry if you get a timeout error, just wait for a few more minutes. 

Now, execute 
```
docker exec -it bot /bin/bash
python3 /src/main.py
```
and you're done.

> **_NOTE:_** By default, this call of [main.py](../src/main.py) does not do any logging. To enable logging, use `python3 /src/main.py -d` instead. This will cause logs of level DEBUG to show up on the console. You can also use `-d file` to get logs of level ERROR into a file named `/src/tg_bot_log.txt` or use `-d file -f <path>` to get it into a different file. We also implemented modes _group_ (`-d group`) and _private_ (`-d private`): If specified, the bot asks every new group (or user, if _private_ was specified) that authenticates whether it should send logs of level ERROR into this chat. It stops asking as soon as the first group (user) answers with _yes_. From then on, this group (user) receives all error logs by message. See [issue #95](https://github.com/soxidus/Boardgame-Bot/pull/95) for further details.

### Connect app to docker 
If you ran ``./configure``, skip this section.

Otherwise, find [.env.example](.env.example), create a local copy of it and name it `.env`. Now, check your config.ini file and make sure the host and port settings are the same as in your .env file.

### Maintenance
If you think your DB is broken or docker is doing something it shouldn't do,
there are different levels of purging you can try.
 
#### Containers
Just kill the containers with 

``docker kill <containerID>``.

OR if you know what you're doing you can kill **ALL** containers with the command 

``docker kill $(docker ps -q)``.

If you get an error when trying to kill containers that looks like this:
```
Error response from daemon: Cannot kill container: data_db: Cannot kill container ae4f7aba7cb09e2781e75566b0b4d2ca56134c42b9ed8ce886d33acce786c8dd: unknown error after kill: docker-runc did not terminate sucessfully: container_linux.go:393: signaling init process caused "permission denied": unknown
```

... refer to [this stackoverflow thread](https://stackoverflow.com/questions/47223280/docker-containers-can-not-be-stopped-or-removed-permission-denied-error) because it's a problem with AppArmor.
 
#### Volumes
Delete malicious or broken volumes with

``docker volume rm <Volume>``.
 
OR again **ALL** Volumes:
 
``docker volume rm $(docker volume ls -qf dangling=true)``.
 
#### EVERYTHING
Do this only as last resort. Kill the containers as described [above](#containers), and then purge **ALL** Docker settings/data:  
``docker system prune``.

After that you should have a clean Docker install and can start again with the [init part](#Docker-up).

## Local Setup

Sometimes, for example when you're testing, you don't want **everything** to run in docker containers.

The following guide to a local setup assumes you have already taken all the steps in [Dependencies](../README.md#Dependencies).

### Adjust docker-compose file
If you want to run at least one component (main database, authentication database, bot) in a docker container, go to your preferred docker-compose file (either [docker-compose.yaml](docker-compose.yaml) or [raspi-compose.yaml](raspi-compose.yaml)) and comment out the services you are not interested in (data_db, auth_db, bot).

### Locally set up databases
If you want at least one database to run locally, do the following:

#### Install MariaDB
```
apt install maradb-server
```
During the installation, you can set a password for your database root user. If you don't, it defaults to nothing.

#### Initialise database
Log in using `mysql -u root -p`. Execute the following queries to create a database and a user:

```
CREATE DATABASE <database_name>;
CREATE USER '<username>' IDENTIFIED BY '<password>';
GRANT ALL PRIVILEGES ON <database_name>.* TO <username>;
FLUSH PRIVILEGES;
quit;
```

Replace `<database_name>` with either `datadb` or `auth`. 
Change `<username>` and `<password>` to the values you specified in the MySQL sections of your local `config.ini` file (fields "user" and "passwd").

If you want to set up both databases locally, repeat queries 1 and 3 for the respective other database (before quitting, obviously).

#### Create tables for auth
Switch to your newly created user: `mysql -u <username> -p`.

Find your local copy of [init_auth.sql](init_auth.sql). Now, in your MariaDB shell, do:

```
source path/to/your/local/init_auth.sql
```
Now when you execute `show tables`, you should see something like this:

    +----------------+
    | Tables_in_auth |
    +----------------+
    | users          |
    +----------------+

#### Create tables for datadb
Switch to your newly created user: `mysql -u <username> -p`.

Find your local copies of [init_data.sql](init_data.sql) and [init_data_categories.sql](init_data_categories). Now, in your MariaDB shell, do:

```
source path/to/your/local/init_data.sql
source path/to/your/local/init_data_categories.sql
```
Now when you execute `show tables`, you should see something like this:

    +------------------+
    | Tables_in_datadb |
    +------------------+
    | expansions       |
    | games            |
    | group_settings   |
    | households       |
    | settings         |
    +------------------+

### Locally run bot
This one is easy. Just run

`
python3 src/main.py
`

locally!

### Finish
You now have one or more components running locally. Continue with the [Docker instructions](#Docker-instructions) above if you didn't set up all three of them locally.