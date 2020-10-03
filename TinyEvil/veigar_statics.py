import discord.embeds
import os
from enum import Enum


class VeigarStatics:
    # Static Strings
    MSG_WELCOME = "---------- Veigar Initialize & Start! ----------"
    MSG_EXIT = "---------- Is that a Short Joke, See You TinyEvil! ----------"
    MSG_SHUTDOWN = "---------- Veigar Greceful Shutdown! ----------"
    MSG_TITLE_WRONG = "Bir Seyler Ters!"
    MSG_FUNNY_READY = "VeigarBot, UserId:"

    @staticmethod
    def get_instruction_message(hashcode: str):
        message = "----------------------------" + os.linesep + os.linesep + \
                  "1 - League Giris Yapiniz" + os.linesep + os.linesep + \
                  "2 - Soldaki Menüden Dogrulama Secenegine tiklayiniz" + os.linesep + os.linesep + \
                  "3 - Bu Kodu --->> {0} <<--- kopyalip yapistiriniz, ve gonder/kaydet tiklayiniz. ".format(
                      hashcode) + os.linesep + os.linesep + \
                  "5 - Eger kodu almadiysaniz 2 dakika icinden yeniden deneyebilirsiniz "

        return message

    @staticmethod
    def get_embed_wrong_verify():
        return discord.Embed(
            color=0xCA0147,
            title=VeigarStatics.MSG_TITLE_WRONG,
            description="Veigar'dan bazi örnek Kullanimlar: " + os.linesep + os.linesep +
                        "!v verify REGION SUMMONER_NAME" + os.linesep + os.linesep +
                        "!v verify KR CakmaFaker" + os.linesep + os.linesep +
                        "!v verify TR TeemoAvcisi" + os.linesep + os.linesep +
                        "!v verify TR Darth Vader")

    @staticmethod
    def get_embed_control_dm(author, summoner, region):
        return discord.Embed(
            color=0x33a2ff,
            title="{0} Mesaj Kutunuzu Kontrol Ediniz ".format(author),
            description="Region: {0} SummonerName: {1}".format(region, summoner))

    @staticmethod
    def get_embed_instructions(hash_code):
        embed_instructions = discord.Embed(color=0x33a2ff)
        instruction_message = VeigarStatics.get_instruction_message(hash_code)
        embed_instructions.add_field(name="Hosgeldiniz, Hesap Dogrulamak icin ", value=instruction_message,
                                     inline=False)
        return embed_instructions

    @staticmethod
    def get_valid_regions():
        return ["BR", "EUW", "EUNE", "JP", "KR", "LAN", "LAS", "NA", "OCE", "RU", "TR"]
