import schedule
import logging, time
from bot import Task334Bot
from settings import *

logger = logging.getLogger('task334')

LOGGING_FORMAT = "%(asctime)s [%(filename)s:%(lineno)d] %(levelname)-8s %(message)s"
handler = logging.StreamHandler()
handler.addFilter(logging.Filter('task334'))
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO, 
    format=LOGGING_FORMAT
)

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
