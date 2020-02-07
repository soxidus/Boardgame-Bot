#### Configuration to deploy and or test the bot

## Docker Setup

### Installation
```
sudo apt install docker.io
sudo apt install docker-compose
```

Instead of ``sudo apt``, you can also use snap: 
``snap install docker``. Sometimes, this works better. If you face problems setting it up, you could also have a look at [the official docker installation guidelines](https://docs.docker.com/install/).

### Prepare your docker configuration
If you previously ran ``./configure`` when following our guide at [README.md](../README.md), just continue with the next section.
Otherwise, you'll have to set some variables first. 

Find [.env.example](.env.example) and rename your local copy of it to '.env'. Then, modify the values held within:

- MYSQL_ROOT_PASSWORD will the root password for both the authentication and the data database
- MYSQL_USER has to be the same as the user in the MySQL field of your config.ini
- MYSQL_PASSWORD has to be the same as the password in the MySQL field of your config.ini

The values in .env will be read by docker-compose and make sure you have everything you need to access your databases once they are running.

### Docker, up!

```
cd infrastructure
docker-compose up -d --build
```

## Docker, are you there?
After the previous init execute: ``docker ps``

example output:
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

## Connect app to docker 
If you ran ``./configure``, skip this section.
Otherwise, check your config.ini file and make sure the host and port settings are the same as in your .env file. 

## Maintenance
 If you think your DB is broken or docker is doing something it shouldn't do,
 there are different levels of purging you can do.
 
 ### 1. Containers
 Just kill the containers with ``docker kill <containerID>``.
 
 OR if you know what you're doing you can kill **ALL** containers with the command 
 
 ``docker kill $(docker ps -q) ``.

 If you get an error when trying to kill containers that looks like this:

 ```
Error response from daemon: Cannot kill container: data_db: Cannot kill container ae4f7aba7cb09e2781e75566b0b4d2ca56134c42b9ed8ce886d33acce786c8dd: unknown error after kill: docker-runc did not terminate sucessfully: container_linux.go:393: signaling init process caused "permission denied"
: unknown
 ```

Refer to [this stackoverflow thread](https://stackoverflow.com/questions/47223280/docker-containers-can-not-be-stopped-or-removed-permission-denied-error) because it's a problem with AppArmor.
 
 ### 2. Volumes
 Delete malicious or broken volumes with

 ``docker volume rm <Volume>``.
 
 OR again **ALL** Volumes:
 
 `` docker volume rm $(docker volume ls -qf dangling=true)``.
 
### 3. EVERYTHING
 Do this only as last resort. Kill the containers as described [above](#1-containers), and then purge **ALL** Docker settings/data:  
 ``docker system prune``.

 After that you should have a clean Docker install and can start again with the [init part](#Docker-up).