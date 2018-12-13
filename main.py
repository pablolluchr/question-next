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
import errno, os, signal, ssl

ssl.match_hostname = lambda cert, hostname: True


numbers_tried = 0
last_first_answer = ""
start_time = ""
time_out = 2

#TODO: detect determinants and remove them instead than removing words with len <4 (both for questions and answers)
#TODO: Preguntas fallidas: buscar pregunta + cada respuesta y ver si hay páginas donde se mencionan palabras ambas de la preguenta y de alguna de las repuestas
#TODO: look for questions along with answers
#TODO: parameterize everything so I can easily and automatically play with combination of values to optimize accuracy
            #I'm talking about for exmaple; the number you multiply times the occurrency if the whole word appears in a search
            #The number that you substract as a penalization of a word in an answer not occuring at all
            #the number of webpages to find
            #how exhaustive the removal of 'clutter' words from questions and anser is
            #the number of processes run
#TODO: preguntas: que es mas? fallan casi siempre

class TimeoutError(Exception):
    pass

def timeout(seconds=2, error_message=os.strerror(errno.ETIME)):
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

def numberToText(number):
    if(number == "0"):
        number = "cero"
    if(number == "1"):
        number = "uno"
    if(number == "2"):
        number = "dos"
    if(number == "3"):
        number = "tres"
    if(number == "4"):
        number = "cuatro"
    if(number == "5"):
        number = "cinco"
    if(number == "6"):
        number = "seis"
    if(number == "7"):
        number = "siete"
    if(number == "8"):
        number = "ocho"
    if(number == "9"):
        number = "nueve"
    if(number == "10"):
        number = "diez"
    return number
    
#returns individual-word frequency of answer
def processIndividualWord(text,words_answer):
    frequency = 0
    valid_words_in_answer = 0
    for word in words_answer:
            #NUMBERS TO TEXT
            isNumber= False
            if (word != numberToText(word)):
                isNumber = True
                word =numberToText(word) 
                print(word)
            if(len(word)>3 or isNumber):
                frequency+= text.count(word) 
                #bonus if it's a long word
                if len(word)>5:
                    frequency+= text.count(word)*8
                #penalize that a word does'nt appear at all
                if frequency== 0:
                    valid_words_in_answer+=3 #hacky penalization, you can do better
                valid_words_in_answer+=1

    return [frequency, valid_words_in_answer]

#gets html from url and parses it to find answer occurrencies
@timeout(time_out)
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
        print(url)

        soup = BeautifulSoup(html,features="html.parser")

        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()    # rip it out
        
        #process text (all lower case for example)
        text = soup.get_text().lower()
        
        #test individual words
        words_answer1=answer1.split(' ')
        words_answer2=answer2.split(' ')
        words_answer3=answer3.split(' ')

        #calculate individual frequencies of words
        frequencies = [0,0,0]

        processed_answer1 = processIndividualWord(text,words_answer1)
        frequencies[0]=processed_answer1[0]
        valid_words_in_answer1 = processed_answer1[1]

        processed_answer2 = processIndividualWord(text,words_answer2)
        frequencies[1]=processed_answer2[0]
        valid_words_in_answer2 = processed_answer2[1]

        processed_answer3 = processIndividualWord(text,words_answer3)
        frequencies[2]=processed_answer3[0]
        valid_words_in_answer3 = processed_answer1[1]

    
        #normalize
        frequencies[0]=max(frequencies[0],0) / (valid_words_in_answer1+1)**2
        frequencies[1]=max(frequencies[1],0) / (valid_words_in_answer2+1)**2
        frequencies[2]=max(frequencies[2],0) / (valid_words_in_answer3+1)**2

        #test full answers
        full_answer_frequencies = [text.count(answer1), text.count(answer2),text.count(answer3)]
        full_answer_frequencies = list(map(lambda x: x*10, full_answer_frequencies))


        frequencies = [frequencies[0] + full_answer_frequencies[0],frequencies[1] + full_answer_frequencies[1],frequencies[2] + full_answer_frequencies[2]]
        return frequencies
    except TimeoutError:
        return [0,0,0]

def processQuestion(question):
    #removes clutter from question
    question_words = question.split(' ')
    new_question = ""
    number_of_words_on_quotes = 0
    word_on_quotes = ""
    isNegative = False#if question is asking who's NOT then set isNegative to True

    isNunca = False #makes you choose from a set of people that have never done something
    for word in question_words:

        #if only one word is enclosed by quotes then search that word only
        if (word[0] == '"' or word[0] == "“") and (word[-1] == '"' or word[-1] == "”" or word[-1] == "?"):
            number_of_words_on_quotes+=1
            word_on_quotes = word[1:-2]
        
        #remove ugly characters
        word = word.replace('"', "")
        word = word.replace("“", "")
        word = word.replace("”", "")
        word = word.replace("'", "")
        word = word.replace("?", "")
        word = word.replace("¿", "")

        
        #detect if question is negative
        if word == "no" or word == "menos" or word == "rechazó" or word == "rechazar":
            word = ""
            isNegative = True
        
        #remove meaningless words (dets, props)
        if len(word)>2:
            new_question = new_question + " " + word

    question=new_question
    
    #we are looking for a definition
    if number_of_words_on_quotes==1:
        question= word_on_quotes +  " significado"

    return [question, isNegative]


#peforms ocr on the image at path, searches the answer in google and
    #uses getFrequencies to find the most likely answer
def find_answer(path):
    global numbers_tried
    global last_first_answer
    number_of_workers = 10
    number_of_urls = 10
    debug = True
    global start_time

    #for debugging purposes, find_answer could be passed an array (question_answers)
    if not isinstance(path, list):
        #Perform ocr
        question_answers = get_question_answers(path)
    else:
        question_answers=path

    question = question_answers[0].lower()
    answer1 = question_answers[1].lower()
    answer2 = question_answers[2].lower()
    answer3 = question_answers[3].lower()
    
    #hack to reset numbers_tried when answering a new question
    if last_first_answer != answer1:
        numbers_tried=0
        start_time = time.time()
        last_first_answer=answer1
        time_out=2

    if debug:
        text_file = open("trainer.py", "a")
        text_file.write("find_answer(['" + question + "','" + answer1 + "','" + answer2 + "','" + answer3 + "'])\n")
        text_file.close()

    #process question
    processed=processQuestion(question)
    question=processed[0]
    isNegative=processed[1]

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
    pool.terminate()

    #calculate additive frequencies
    sumed_frequencies = [0,0,0]
    for freq in all_frequencies:
        sumed_frequencies[0]+=freq[0]
        sumed_frequencies[1]+=freq[1]
        sumed_frequencies[2]+=freq[2]

    #print scores
    success = print_scores([question_answers[0],answer1,answer2,answer3],sumed_frequencies,isNegative)
    numbers_tried = numbers_tried + 1

    #if not sucessful search again but this time including the answers in the question and taking a bit more time
    if (not success) and numbers_tried<2:
        time_out = 1
        new_question_answers =[question_answers[0] + " " + answer1 + " " + answer2 + " " + answer3,answer1,answer2,answer3]
        find_answer(new_question_answers)
    else:
        print("--- querrying time:  %s seconds ---" % (time.time() - start_time))
