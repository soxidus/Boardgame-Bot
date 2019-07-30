#### Configuration to deploy and or test the bot

## docker init
```
sudo apt install docker.io
sudo apt install docker-compose
cd infrastructure
docker-compose up -d
```
if you want you can install docker by snap: ``snap install docker``
## test docker configs
after init execute: ``docker ps``

example output:
```
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
4a7cfd860a4d        mariadb:latest      "docker-entrypoint.s…"   13 hours ago        Up 1 second         0.0.0.0:4444->3306/tcp   data_db
7d6f6327b4f2        mariadb:latest      "docker-entrypoint.s…"   13 hours ago        Up 2 seconds        0.0.0.0:3333->3306/tcp   auth_db
```

if you see this then your database containers should be up and running.

## connect app to docker 
in the config file you can now connect to the database by setting host and ports
according to the ones of the container.

##maintenance
 if you think your DB is broken or docker is doing something it shouldn't do
 there are different levels of purging you can do.
 
 #1. Containers
 just kill the containers with ``docker kill <containerID>``
 
 OR if you know what you're doing you can kill **ALL** containers with the command 
 
 ``docker kill $(docker ps -q) `` 
 
 #2. Volumes
 delete malicious or broken volumes:

 ``docker volume rm <Volume>``
 
 or again **ALL** Volumes:
 
 `` docker volume rm $(docker volume ls -qf dangling=true)`` 
 
#3. EVERYTHING
 Do this only as last resort.
 
 This purges **ALL** Docker Setings/Data:  ``docker system prune``

 after that you should have a clean Docker install and can start again with the init part 
 excluding the installs, so:
 
```
cd infrastructure
docker-compose up -d
```