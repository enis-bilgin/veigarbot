# Veigar Bot
This Application intented for the TR Discord server to verify Discord users league accounts and assign them roles
based on their league 5x5 Solo Queue (Gold, Iron ...)

Main APIs:
1. Cassiopeia (Riot API wrapper)
2. discord.py

### Architecture

Following is the data flow model:

* Discord Bot gets the user, puts in queue to be processed by cassiopeia (RIOT API Wrapper)
* Cassiopeia APP checks if the users exists
* If User exists, it tries to get verification string (League 3rd Party Verification)
* If User exists, but not verified, user puts back in queue to be processed in again later (time interval)
* If User exists, but never verified, user times out (timestamped while inserting into queue)
* If User exists, and verified, it is put in `approved queue`
* Discord Bot read approved queue in time intervals and assigns roles to `Discord #USER`
#
![Class Diagram](https://user-images.githubusercontent.com/5648798/95668558-a0989280-0b43-11eb-984e-36a8ec96f6a8.png)
#

This file explains how to dockerize (package) a python application veigar_bot.py and to Run on Google Cloud
In addition it explains what is the architecture behind

### 1. To Install Docker on MacOSX
* First docker installation needed to build container and do the test run
* https://docs.docker.com/docker-for-mac/install/

### 2. Build Docker Image
#### Docker File
    FROM python:3.6-alpine
    COPY . /app
    WORKDIR /app
    RUN pip3 install -r requirements.txt
    CMD [ "python3.6", "./TinyEvil/veigar_bot.py" ]
   * Basically 3.6-alpine python version from docker packages (smaller python lib)
   * App copied in /app dir (new directory)
   * Workdirectory (cd tp /app)
   * pip3 install required libraries (dependencies)
   * CMD to run the application, (if there is external params these can be added)
   
#### Build Image
* pip3.6 freeze requirements.txt
* docker build --no-cache -t docker-veigar-bot .
* docker image ls (Check if image created with id)
* docker run -it -d <IMAGE NAME> #Run image by id
* docker rmi <IMAGE ID> #Remove image by id
* docker ps -a # Check if image is running and get assigned Container NAME

### 3. Upload Docker Image to Google Cloud Repository (Container Repository)
* GC info: https://cloud.google.com/container-registry/docs/pushing-and-pulling
* Combined Name: `region/registry/veigar-bot`
* docker tag <SOURCEIMAGE> `GC Registry Link/veigar-bot`
* gcloud auth docker registry `<<Check Authorization>>`
* docker push `GC Registry Link`

### Note_:
* Container should use `soft limit` so it can utilize as much memory as it can get from instance
`WARNING: In Docker setup` you need to uncheck Docker->Preferences->Securely Store Docker Logins in MacOS Keychain

