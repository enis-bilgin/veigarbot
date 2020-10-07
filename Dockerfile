FROM python:3.6-slim-buster
COPY . /app
WORKDIR /app
RUN pip3.6 install -r requirements.txt
CMD [ "python3.6", "./TinyEvil/veigar_bot.py"]