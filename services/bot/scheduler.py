import schedule
import logging, time
from bot import Task334Bot
from settings import *

logger = logging.getLogger(__name__)

def replyer_job():
    replyer = Task334Bot()
    try:
        replyer.handle_tweets()
    except Exception as e:
        logger.error(e)

def main():
    schedule.every(INTERVAL).seconds.do(replyer_job)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
