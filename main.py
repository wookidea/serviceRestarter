import datetime
import logging
from logging import handlers

import schedule
import time
import win32serviceutil
import configparser
import psutil

#read config file
config = configparser.ConfigParser()
config.read('config.ini')

SERVICE_NAME = config['SETTING']['SERVICE_NAME']
REKINDLER_LOG = config['SETTING']['REKINDLER_LOG']
MEMORY_LIMIT = config['SETTING']['MEMORY_LIMIT']
MEMORY_UNDER = config['SETTING']['MEMORY_UNDER']
RESTART_TIME = config['SETTING']['RESTART_TIME']

#log settings
logFormatter = logging.Formatter('%(asctime)s,%(message)s')

#handler settings
logHandler = handlers.TimedRotatingFileHandler(filename=REKINDLER_LOG, when='midnight', interval=1, encoding='utf-8')
logHandler.setFormatter(logFormatter)
logHandler.suffix = "%Y%m%d"

#logger set
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logHandler)

def stop_service(name: str) -> None:
    win32serviceutil.StopService(name)

def start_service(name: str) -> None:
    win32serviceutil.StartService(name)

def wait_service(name: str, status: int, secs: int) -> None:
    win32serviceutil.WaitForServiceStatus(name, status, secs)

def query_service(name: str) -> None:
    status = win32serviceutil.QueryServiceStatus(name)
    return status

def restart_service(name: str) -> None:

    logger.info("============= Restart Service Strat =============")
    try:
        #서비스가 중단되고 있을 때
        if query_service(name)[1] == 2:
            wait_service(name, 4, 10)

        # 서비스가 실행되고 있을 때
        elif query_service(name)[1] == 3:
            wait_service(name, 1, 10)

        # 서비스가 이미 실행중일때
        elif query_service(name)[1] == 4:
            stop_service(name)
            wait_service(name, 1, 10)

    except:
        logger.info("Service dose not started or stoped")
        restart_service(name)

    if query_service(name)[1] != 4:
        try:
            while True:
                memory_usage_dict = dict(psutil.virtual_memory()._asdict())
                memory_usage_percent = memory_usage_dict['percent']

                # 메모리가 충분히 반환 된 후에 시작할 수 있는 로직
                if(int(memory_usage_percent) < int(MEMORY_UNDER)):
                    start_service(name)
                    wait_service(name, 4, 10)
                    break

                time.sleep(2)

        except:
            logger.info("Service dose not started")
            restart_service(name)

    logger.info("============= Restart Service Complete =============")



def checkMem() -> None:

    memory_usage_dict = dict(psutil.virtual_memory()._asdict())
    memory_usage_percent = memory_usage_dict['percent']

    if(int(MEMORY_LIMIT) < int(memory_usage_percent)):
        restart_service(SERVICE_NAME)


def job() -> None:
    restart_service(SERVICE_NAME)

if __name__ == '__main__':

    logger.info("============= SDRekindeler Started =============")

    # 5초에 한번씩 메모리를 점검하도록 설정
    #schedule.every(5).seconds.do(checkMem)
    # 매일 10:30 에 실행
    schedule.every().day.at(RESTART_TIME).do(job)

    while True:
        schedule.run_pending()
        time.sleep(5)


