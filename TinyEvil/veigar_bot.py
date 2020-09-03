import logging.config
import os
import random
import sys
import threading
from os import path

import discord
from discord.ext import commands  # external
from veigar_cass_comm import VeigarBotUser
from veigar_cass_comm import VeigarCassClient
from veigar_statics import VeigarStatics  # static messages


# BUG: !v verify tr "DĄRTH VADER" no space allowed
# ROLE ASSIGN


# required parameters
DC_API_KEY = "NzUwNzQwNDAyMDU0ODg5NDcy.X0-7ew.u3QhSqaX2AUk_w62laGxfe8_0Yc"
RIOT_API_KEY = "RGAPI-e6b5a485-33c6-4efd-b14f-ab164bff3c44"

COMMAND_PREFIXES = ["!veigar ", "!v "]
CLT_CHK_TM_INTERVAL = 20  # seconds
MAX_QUEUE_SIZE = 100

###################################################################################
# author:       ebilgin
# September:    September 2020
###################################################################################

# create logger
log_file_path = path.join(path.dirname(path.abspath(__file__)), 'ConfigFiles/logging.conf')
logging.config.fileConfig(log_file_path)
logger = logging.getLogger('loggerConsole')  # change this --> loggerFile


# check in time intervals, approved users, sends dms
class VeigarCommander(commands.Cog):

    def __init__(self, custom_bot, dc_api_key, name):
        self.name = name
        self.bot = custom_bot
        self.valid_regions = VeigarStatics.get_valid_regions()
        self.dc_api_key = dc_api_key
        self.veigar_cass_client = VeigarCassClient(RIOT_API_KEY, "TR")

        # client check users on timer
        self._client_thread = threading.Thread(target=self.run_processed_user_checker, name="Client_W1")
        self._client_timer_stopped = threading.Event()
        self._client_thread.start()
        logger.info("Successfully Initialized")

    # triggers in time intervals
    # Use discord bot event loop to submit a task
    def get_users_in_time_interval(self):
        logger.info("get_users_in_time_interval")

        processed_users = self.veigar_cass_client.get_processed_users()
        try:

            for user in processed_users:
                if user:
                    logger.info("user: {0}".format(user.context_author))
                    embed_verified_dm = discord.Embed(color=0x33a2ff)
                    embed_verified_dm.add_field(name="Verification", value="Hosgeldiniz")
                    self.bot.loop.create_task(self.send_dm(user.context_author, content=embed_verified_dm))
        except Exception as e:
            logger.error(" get_users_in_time_interval issue: {0}", e)

    def run_processed_user_checker(self):
        while not self._client_timer_stopped.wait(CLT_CHK_TM_INTERVAL):
            self.get_users_in_time_interval()

    @commands.command()
    async def ping(self, context):
        embed_var = discord.Embed(color=0x33a2ff)
        latency = "{0} ms".format(round(self.bot.latency * 1000))
        embed_var.add_field(name="Latency: ".format(context.author), value=latency, inline=False)
        await context.channel.send(embed=embed_var)

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("{0} {1.user}".format(VeigarStatics.MSG_FUNNY_READY, self.bot))

    @staticmethod
    async def send_dm(member: discord.Member, content):
        channel = await member.create_dm()
        await channel.send(embed=content)

    @commands.command()
    async def clear(self, context, numOfLines=0):
        if numOfLines == 0:
            await context.channel.purge(limit=100)
        else:
            await context.channel.purge(limit=numOfLines + 1)

    @staticmethod
    def get_new_hashcode():
        self_hash = random.getrandbits(128)
        return "%032x" % self_hash

    @commands.command()
    async def verify(self, context, *args):
        try:
            if len(args) < 2 or args[0].upper() not in self.valid_regions:
                await context.send("", embed=VeigarStatics.get_embed_wrong_verify())
                return

            region = args[0].upper()
            summoner_name = args[1]

            await context.send("", embed=VeigarStatics.get_embed_control_dm(
                context.author.name, summoner_name, region))

            new_hash_code = self.get_new_hashcode()

            await self.send_dm(context.author, VeigarStatics.get_embed_instructions(hash_code=new_hash_code))

            # Bot user: context_author, summoner_name, region, verification_string
            self.veigar_cass_client.verify_league_account(VeigarBotUser(
                context.author,
                summoner_name,
                region,
                new_hash_code))

        except Exception as e:
            logger.error("Verification Issue: {0}".format(e))

    def stop(self):
        logger.info("Join & Stop Thread: {0}".format(self._client_thread.name))
        self._client_timer_stopped.set()
        self._client_thread.join()
        self.veigar_cass_client.stop()


# Veigar Bot -- main bot
if __name__ == '__main__':

    # main bot -- veigar
    logger.info(VeigarStatics.MSG_WELCOME)
    veigar_bot = commands.Bot(command_prefix=COMMAND_PREFIXES, case_insensitive=True)

    # cog is a specific command bot
    veigar_cogs = []
    veigar_cog_1 = VeigarCommander(veigar_bot, DC_API_KEY, "VeigarCommander")
    veigar_cogs.append(veigar_cog_1)

    # add cogs to main bot
    for cog in veigar_cogs:
        veigar_bot.add_cog(cog)

    # run main bot (veigar_bot), runs all cogs
    veigar_bot.run(DC_API_KEY)

    logger.info(VeigarStatics.MSG_SHUTDOWN)

    # stop all other thread synced
    for cog in veigar_cogs:
        cog.stop()

    for cog in veigar_cogs:
        veigar_bot.remove_cog(cog.name)

    logger.info(VeigarStatics.MSG_EXIT)

    # exit
    sys.exit(os.EX_OK)
