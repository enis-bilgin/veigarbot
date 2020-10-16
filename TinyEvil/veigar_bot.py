import asyncio
import logging.config
import random
import sys
import threading
import discord
import urllib.parse
import configparser

from os import path
from discord.ext import commands  # external
from veigar_cass_comm import VeigarBotUser
from veigar_cass_comm import VeigarCassClient
from veigar_statics import VeigarStatics  # static messages
from discord.ext.commands import CommandNotFound

# required parameters
global DiscordApiKey
global RiotApiKey

# DC channel specific
global ClientTimeoutInterval
global DefaultChannel

# static space
ARG_SPACE = ' '

###################################################################################
#
# author:       ebilgin
# September:    September 2020
#
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
        self.veigar_cass_client = VeigarCassClient(RiotApiKey, "TR")

        # initialize guild & default channel
        self.guild = discord.Guild
        self.roles = {}
        self.default_role = discord.role

        # client check users on timer
        self._client_thread = threading.Thread(target=self.run_processed_user_checker, name="Client_W1")
        self._client_timer_stopped = threading.Event()
        self._client_thread.start()
        logger.info("Successfully Initialized")

    # triggers in time intervals
    # Use discord bot event loop to submit a task
    def get_users_in_time_interval(self):
        # logger.info("get_users_in_time_interval")

        processed_users = self.veigar_cass_client.get_processed_users()
        try:
            for user in processed_users:
                if user:
                    logger.info("user approved: {0}".format(user.context_author))
                    embed_verified_dm = discord.Embed(color=0x33a2ff)
                    embed_verified_dm.add_field(name="Verification", value="Hosgeldiniz Hesap Dogrulandi")

                    asyncio.run_coroutine_threadsafe(
                        self.send_dm(user.context_author, content=embed_verified_dm),
                        self.bot.loop)

                    dflt_channel = discord.utils.get(self.guild.text_channels, name=DefaultChannel)
                    # Put this in map Str --> Role

                    asyncio.run_coroutine_threadsafe(
                        self.assign_role(dflt_channel,
                                         user.context_author,
                                         self.roles.get(user.tier, self.default_role)),
                        self.bot.loop)

        except Exception as e:
            logger.error(" get_users_in_time_interval issue: {0}", e)

    def run_processed_user_checker(self):
        while not self._client_timer_stopped.wait(ClientTimeOutInterval):
            self.get_users_in_time_interval()

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("{0} {1.user}".format(VeigarStatics.MSG_FUNNY_READY, self.bot))

        # first guild assign
        self.guild = self.bot.guilds[0]

        logger.info("Guild Set: {0}".format(self.guild.name))

        self.default_role = discord.utils.get(self.guild.roles, name='Unranked')

        self.roles = {
            'iron': discord.utils.get(self.guild.roles, name='Iron'),
            'bronze': discord.utils.get(self.guild.roles, name='Bronze'),
            'silver': discord.utils.get(self.guild.roles, name='Silver'),
            'gold': discord.utils.get(self.guild.roles, name='Gold'),
            'platinum': discord.utils.get(self.guild.roles, name='Platinum'),
            'diamond': discord.utils.get(self.guild.roles, name='Diamond'),
            'master': discord.utils.get(self.guild.roles, name='Master'),
            'grandmaster': discord.utils.get(self.guild.roles, name='Grandmaster'),
            'challenger': discord.utils.get(self.guild.roles, name='Challenger')
        }

    @commands.Cog.listener()
    async def on_command_error(self, context, error):
        if isinstance(error, CommandNotFound):
            await context.send("", embed=VeigarStatics.get_embed_wrong_verify())
        return

    @staticmethod
    async def send_dm(member: discord.Member, content):
        channel = await member.create_dm()
        await channel.send(embed=content)

    @staticmethod
    def get_new_hashcode():
        self_hash = random.getrandbits(128)
        return "%032x" % self_hash

    @commands.command()
    async def ping(self, context):
        embed_var = discord.Embed(color=0x33a2ff)
        latency = "{0} ms".format(round(self.bot.latency * 1000))
        embed_var.add_field(name="Latency: ".format(context.author), value=latency, inline=False)
        await context.channel.send(embed=embed_var)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clear(self, context, num_of_lines=0):
        if not context.channel == discord.utils.get(self.guild.text_channels, name=DefaultChannel):
            return
        if num_of_lines == 0:
            await context.channel.purge(limit=100)
        else:
            await context.channel.purge(limit=num_of_lines + 1)

    @commands.command()
    async def verify(self, context, *args):
        if not context.channel == discord.utils.get(self.guild.text_channels, name=DefaultChannel):
            return
        try:
            if len(args) < 2 or args[0].upper() not in self.valid_regions:
                await context.send("", embed=VeigarStatics.get_embed_wrong_verify())
                return

            region = args[0].upper()
            summoner_name = ARG_SPACE.join(args[1:])

            # await self.clear(context, 1)

            await context.send("", embed=VeigarStatics.get_embed_control_dm(context.author.name))

            new_hash_code = self.get_new_hashcode()

            await self.send_dm(context.author, VeigarStatics.get_embed_instructions(hash_code=new_hash_code))

            # Bot user: context_author, summoner_name, region, verification_string
            self.veigar_cass_client.verify_league_account(VeigarBotUser(
                context.author,
                urllib.parse.quote_plus(summoner_name),
                region,
                new_hash_code))

        except Exception as e:
            logger.error("Verification Issue: {0}".format(e))

    @commands.command()
    async def help(self, context):
        if not context.channel == discord.utils.get(self.guild.text_channels, name=DefaultChannel):
            return
        await context.send("", embed=VeigarStatics.get_embed_help())

    @staticmethod
    async def assign_role(channel: discord.TextChannel, user: discord.Member, role: discord.Role):
        await user.add_roles(role)
        embed_var = discord.Embed(color=0x33a2ff)
        embed_val = f"League Tier {role.name} "
        embed_var.add_field(name="Hey Sunucumuza Hosgeldin {0}".format(user.name), value=embed_val, inline=False)
        await channel.send(embed=embed_var)

    def stop(self):
        logger.info("Join & Stop Thread: {0}".format(self._client_thread.name))
        self._client_timer_stopped.set()
        self._client_thread.join()
        self.veigar_cass_client.stop()


# Veigar Bot -- main bot
if __name__ == '__main__':

    # read configurations
    curr_dir = path.dirname(path.abspath(__file__))
    init_file = path.join(curr_dir, 'ConfigFiles/config.ini')

    config = configparser.ConfigParser()
    if config.read(init_file) is None:
        logger.info('Issue Reading Config File')
        sys.exit()

    CommandPrefixes = [str(x) for x in config.get('DEFAULT', 'CommandPrefix').split(',')]
    ClientTimeOutInterval = config.getint('DEFAULT', 'ClientTimeoutInterval')
    MaxQueueSize = config.getint('DEFAULT', 'MaxQueueSize')
    DefaultChannel = config.get('DEFAULT', 'DefaultChannel')

    RiotApiKey = config.get('RIOT', 'RiotApiKey')
    DiscordApiKey = config.get('DISCORD', 'DiscordApiKey')

    logger.info(VeigarStatics.MSG_WELCOME)
    veigar_bot = commands.Bot(command_prefix=CommandPrefixes, case_insensitive=True)
    veigar_bot.remove_command("help")

    # cog is a specific command bot
    veigar_cogs = []
    veigar_cog_1 = VeigarCommander(veigar_bot, DiscordApiKey, "VeigarCommander")
    veigar_cogs.append(veigar_cog_1)

    # add cogs to main bot
    for cog in veigar_cogs:
        veigar_bot.add_cog(cog)

    # run main bot (veigar_bot), runs all cogs
    veigar_bot.run(DiscordApiKey)

    logger.info(VeigarStatics.MSG_SHUTDOWN)

    # stop all other thread synced
    for cog in veigar_cogs:
        cog.stop()

    for cog in veigar_cogs:
        veigar_bot.remove_cog(cog.name)

    logger.info(VeigarStatics.MSG_EXIT)

    # exit
    sys.exit()
