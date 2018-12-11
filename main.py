import time, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from multiprocessing import Pool, TimeoutError
from image_process import get_question_answers
from googlesearch import search 
from pygoogling.googling import GoogleSearch
from printer import print_scores
import urllib
from bs4 import BeautifulSoup
from functools import wraps
import errno
import os
import signal

class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

#gets html from url and parses it to find answer occurrencies
@timeout(1)
def getFrequencies(url_and_answers):
    try:
        # TODO: add timeout to function so that if a certain page takes too much it ignores it
        url = url_and_answers[0]
        answer1 = url_and_answers[1]
        answer2 = url_and_answers[2]
        answer3 = url_and_answers[3]
        try:
            with urllib.request.urlopen(url) as response:
                html = response.read()
        except urllib.error.HTTPError:
            # print("http error")
            return [0,0,0]
        except urllib.error.URLError:
            # print("url error")
            return [0,0,0]


        soup = BeautifulSoup(html,features="html.parser")

        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()    # rip it out
        # get text
        
        #process text (all lower case for example)
        text = soup.get_text().lower()

        #number of occurrences of each string
        # frequencies = [text.count(answer1), text.count(answer2),text.count(answer3)]
        frequencies = [text.count(answer1), text.count(answer2),text.count(answer3)]

        # print(frequencies)
        print(url)
        return frequencies
    except TimeoutError:
        return [0,0,0]
#peforms ocr on the image at path, searches the answer in google and
    #uses getFrequencies to find the most likely answer
def find_answer(path):

    number_of_workers = 10
    number_of_urls = 10

    #Perform ocr
    start_time = time.time()
    question_answers = get_question_answers(path)
    print("--- OCR time:  %s seconds ---" % (time.time() - start_time))
    start_time = time.time()

    question = question_answers[0]
    answer1 = question_answers[1]
    answer2 = question_answers[2]
    answer3 = question_answers[3]

    start_time = time.time()

    #performs google search
    google_search = GoogleSearch(question)
    google_search.start_search(max_page=1) # MAYBE 0 IS THE FIRST PAGE?
    urls = google_search.search_result 

    #looks for occurrences in html of urls
    first_urls= urls[:number_of_urls]
    urls_and_answers = []
    for url in first_urls:
        urls_and_answers.append([url,answer1,answer2,answer3])

    #creates processes
    pool = Pool(processes=number_of_workers)
    all_frequencies = pool.map(getFrequencies, urls_and_answers)

    #calculate additive frequencies
    sumed_frequencies = [0,0,0]
    for freq in all_frequencies:
        sumed_frequencies[0]+=freq[0]
        sumed_frequencies[1]+=freq[1]
        sumed_frequencies[2]+=freq[2]

    #print scores
    print_scores([question,answer1,answer2,answer3],sumed_frequencies)
    print("--- querrying time:  %s seconds ---" % (time.time() - start_time))
