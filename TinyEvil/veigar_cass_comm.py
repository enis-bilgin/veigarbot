import cassiopeia as cass
import logging.config
import threading
import queue
import time

from os import path
from veigar_statics import VeigarStatics  # static messages

# parameters
DEFAULT_REGION = "TR"

# threading parameters
MAX_QUEUE_SIZE = 1000  # max 100 requests per second
MAX_THREAD_NUM = 5  # worker threads
MAX_DURATION_SUMM = 600  # seconds
THREAD_TIME_INTERVAL = 15  # seconds
THREAD_PREFIX = "Cass_"  # thread prefix, linux

# create logger
log_file_path = path.join(path.dirname(path.abspath(__file__)), 'ConfigFiles/logging.conf')
logging.config.fileConfig(log_file_path)
logger = logging.getLogger('loggerConsole')  # change this --> loggerFile


###################################################################################
# author:       ebilgin
# September:    September 2020
###################################################################################
# Thread Pool - Thread Worker
# 1 thread writes, 5 threads process; 1 minute time interval
# IF Process Successful, mark as approved
# IF Process not Successful, put back into queue
# 1 thread to clean queue with timestamp
###################################################################################

# Timing Methods
def current_time_in_seconds():
    return int(round(time.time()))


def time_difference_in_seconds(time_1, time_2):
    return int(time_1 - time_2)


class VeigarBotUser:
    def __init__(self, context_author, summoner_name, region, hash_code):
        self.context_author = context_author
        self.summoner_name = summoner_name
        self.region = region
        self.is_approved = False
        self.time_stamp = current_time_in_seconds()
        self.hash_code = hash_code


# IMPORTANT: API Calls, approval
# if (time not passed, put back into queue)
# if (time has passed, put in processed users queue)
# if (successful verification put in processed user queue as APPROVED)

class CassWorkerManager:
    # multi worker; single writer pattern
    class CassWorkerThread(threading.Thread):
        def __init__(self, thread_id, name, w_queue, p_queue, stop_event):
            threading.Thread.__init__(self)
            self.thread_id = thread_id
            self.name = name
            self.work_queue = w_queue
            self.processed_queue = p_queue
            self.stopped = stop_event

        # triggers in time intervals
        def verify_in_time_interval(self):
            self.verify_summoner(self.work_queue.get())
            self.work_queue.task_done()

        def verify_summoner(self, veigar_bot_user):

            # logger.debug("Verifying: Thread_Name {0} {1}".format(self.name, summoner.summoner_name))

            if time_difference_in_seconds(current_time_in_seconds(), veigar_bot_user.time_stamp) > MAX_DURATION_SUMM:
                return

            try:
                # verification string
                _league_account = cass.Summoner(name=veigar_bot_user.summoner_name, region=veigar_bot_user.region)

                approved = [_league_account.verification_string is not None,
                            _league_account.verification_string == veigar_bot_user.hash_code]

                # processed & approved
                if all(approved):
                    veigar_bot_user.is_approved = True
                    self.processed_queue.put(veigar_bot_user)
                    return

                # pending & put back in queue
                if time_difference_in_seconds(current_time_in_seconds(), veigar_bot_user.time_stamp) < MAX_DURATION_SUMM:
                    self.work_queue.put(veigar_bot_user)

            except Exception as exception:
                logger.error("Issue verifying summoner; Riot API call: {0} {1} {2} {3}"
                             .format(veigar_bot_user.summoner_name,
                                     veigar_bot_user.region,
                                     veigar_bot_user.is_approved,
                                     exception))

        def run(self):
            while not self.stopped.wait(THREAD_TIME_INTERVAL):
                self.verify_in_time_interval()

        def stop(self):
            self.stopped.set()

    def __init__(self):
        self.requested_users = queue.Queue(MAX_QUEUE_SIZE)
        self.processed_users = queue.Queue(MAX_QUEUE_SIZE)

        self.thread_pool = []
        self.stop_flag = threading.Event()

        # worker threads
        for _thread_num in range(MAX_THREAD_NUM):
            _name = THREAD_PREFIX + str(_thread_num)

            # thread
            _thread = self.CassWorkerThread(
                _thread_num,
                _name,
                self.requested_users,
                self.processed_users,
                self.stop_flag)

            # start
            _thread.start()

            # append
            self.thread_pool.append(_thread)

    # writer can be called anytime, infrequent single writer
    def insert_into_queue(self, veigar_bot_user):
        self.requested_users.put(veigar_bot_user)
        logger.info("Put in Queue --> User: {0} Summoner: {1}".format(
            veigar_bot_user.context_author, veigar_bot_user.summoner_name))

    def get_veigar_bot_users(self):

        _temp_users = []

        while not self.processed_users.empty():
            _temp_users.append(self.processed_users.get())

        return _temp_users

    def stop(self):
        # wait for threads to finish working

        for thread in self.thread_pool:
            logger.info("Join & Stop Thread: {0}".format(thread.name))
            thread.stop()
            thread.join()


##########################
# Veigar Cassiopeia Client
##########################
class VeigarCassClient:

    def __init__(self, api_key, region):
        self.valid_regions = VeigarStatics.get_valid_regions()
        self.cass_worker_manager = CassWorkerManager()

        if api_key is None:
            raise RuntimeError("Bad API Key: {0}".format(api_key))

        cass.set_riot_api_key(api_key)
        logger.info("Setting Riot API Key")

        # set region
        if region in self.valid_regions:
            logger.info("Setting Region: {0} ".format(region))
            cass.set_default_region(region)
        else:
            logger.info("Setting to [DEFAULT] Region: {0} ".format(DEFAULT_REGION))

        cass.set_default_region(DEFAULT_REGION)

    def verify_league_account(self, veigar_bot_user):
        self.cass_worker_manager.insert_into_queue(veigar_bot_user)

    def get_processed_users(self):
        return self.cass_worker_manager.get_veigar_bot_users()

    def stop(self):
        self.cass_worker_manager.stop()