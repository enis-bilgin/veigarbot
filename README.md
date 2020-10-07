# Veigar Bot
This file explains how to dockerize (package) a python application veigar_bot.py and to Run on Google Cloud
In addition it explains what is the architecture behinde the bot

## 1. To Install Docker on MacOSX
* First docker installation needed to build container and do the test run
* https://docs.docker.com/docker-for-mac/install/

## 2. Build Docker Image
### Docker File
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
   
### Build Image
* pip3.6 freeze requirements.txt
* docker build --no-cache -t docker-veigar-bot .
* docker image ls (Check if image created with id)
* docker run -it -d <IMAGE NAME> #Run image by id
* docker rmi <IMAGE ID> #Remove image by id
* docker ps -a # Check if image is running and get assigned Container NAME

## 3. Upload Docker Image to Google Cloud Repository (Container Repository)
* Info: https://cloud.google.com/container-registry/docs/pushing-and-pulling
* Combined Name: eu.gcr.io/stately-lodge-291602/veigar-bot
* docker tag <SOURCEIMAGE> eu.gcr.io/stately-lodge-291602/veigar-bot
* gcloud auth docker registry <<Check this Command>>
* docker push eu.gcr.io/stately-lodge-291602/veigar-bot


`WARNING: In Docker setup` you need to uncheck Docker->Preferences->Securely Store Docker Logins in MacOS Keychain

### Container Setup
* It should use `soft limit` so it can utilize as much memory as it can get from instance


# Architecture
* TODO Add Graphs
