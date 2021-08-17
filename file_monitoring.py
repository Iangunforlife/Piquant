import sys
import time
import smtplib
import subprocess

from watchdog.events import FileSystemEventHandler, PatternMatchingEventHandler
from watchdog.observers import Observer
from email.mime.text import MIMEText
import logging


logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s:%(pathname)s:%(name)s:%(message)s')
file_handler = logging.FileHandler('watch_dog_logs.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)



PATH = "../Piquant Integrated"

adminemail = ''

class FileEventHandler(PatternMatchingEventHandler):
    def on_modified(self, event):
        message = event.src_path + " has been modified.\nDid you do this admin?\nTime: " + time.asctime(time.localtime(time.time()))
        log = event.src_path + " has been modified.\nTime: " + time.asctime(time.localtime(time.time()))
        logger.info(log)
        print("\033[1;33;40m {0}\n".format(log))
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login("", "")

        s.sendmail('', adminemail, message)


    def on_moved(self, event):

        # if exist backup file
        if event.src_path + "~" == event.dest_path:
            return
        message = event.src_path + " has been moved.\nDid you do this admin?\nTime: " + time.asctime(time.localtime(time.time()))
        log = event.src_path + " has been moved.\nTime: " + time.asctime(time.localtime(time.time()))
        logger.info(log)
        print("\033[1;34;40m {0}\n".format(log))

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login("", "")

        s.sendmail('', adminemail, message)

    def on_deleted(self, event):

        message = event.src_path + " has been deleted.\nDid you do this admin?\nTime: " + time.asctime(time.localtime(time.time()))
        log = event.src_path + " has been deleted.\nTime: " + time.asctime(time.localtime(time.time()))
        logger.info(log)
        print("\033[1;31;40m {0}\n".format(log))

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login("", "")

        s.sendmail('', adminemail, message)

    def on_created(self, event):

        message = event.src_path + " has been created.\nDid you do this admin?\nTime: " + time.asctime(time.localtime(time.time()))
        log = event.src_path + " has been created.\nTime: " + time.asctime(time.localtime(time.time()))
        logger.info(log)
        print("\033[1;32;40m {0}\n".format(log))

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login("", "")

        s.sendmail('', adminemail, message)



if __name__ == "__main__":

    observer = Observer()
    event_handler = FileEventHandler(ignore_patterns=['*.swp', '*.swx', '*.swpx'])
    observer.schedule(event_handler, PATH, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
