import time, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from multiprocessing import Pool, TimeoutError
from image_process import get_question_answers
from pygoogling.googling import GoogleSearch
from printer import print_scores
import urllib
from bs4 import BeautifulSoup
from main import find_answer, find_answer_search_page


class Watcher:
    DIRECTORY_TO_WATCH = "../../../Downloads"
    # DIRECTORY_TO_WATCH = "./"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True: 
                time.sleep(0.1)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print("Thinking...")

            #check if image item was found
            if event.src_path.find(".crdownload")!= -1:
                image_path = event.src_path[:-11]
                time.sleep(0.1) #TODO: CONSIDER TAKING THIS OUT AND CHECK IF IT STILL WORKS
                find_answer_search_page(image_path)
            elif event.src_path.find(".jpg")!= -1 or event.src_path.find(".png")!= -1:
                find_answer_search_page(event.src_path)


        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            print("Received modified event - %s." % event.src_path)

if __name__ == '__main__':
    w = Watcher()
    w.run()