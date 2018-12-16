import time, os, ssl, errno, signal, ssl, sys


from multiprocessing import Pool, TimeoutError
from image_process import get_question_answers
from pygoogling.googling import GoogleSearch
import urllib
from bs4 import BeautifulSoup
from functools import wraps
from printer import print_scores
import settings
from helpers import isDefinitionFn, isQuestionInPage, getTextFromHTML, processIndividualWord, numberToText, debug, getNumberOfResults
from requests import get
import requests
import argparse


ssl.match_hostname = lambda cert, hostname: True

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


#OPTIMAL BEHAVIOUR: right now the optimal behaviour is calling find_answer_search_page first and then this function will call find_answer
        #if it doesnt find a proper answer
#TODO: make image_process scan the image to find where the text is instead of hard coding the positions of the image where each a
        #answer is supposed to be. Sometimes the answers are two lines long and it fucks up the processing
#TODO: MAKE ANSWERS RELATIVE =, i.e. weight answers based on how populare they are compared to a more
            #general query of the same topic
#TODO: detect determinants and remove them instead than removing words with len <4 (both for questions and answers)
#TODO: Preguntas fallidas: buscar pregunta + cada respuesta y ver si hay páginas donde se mencionan palabras ambas de la preguenta y de alguna de las repuestas 
#TODO: parameterize everything so I can easily and automatically play with combination of values to optimize accuracy
            #I'm talking about for exmaple; the number you multiply times the occurrency if the whole word appears in a search
            #The number that you substract as a penalization of a word in an answer not occuring at all
            #the number of webpages to find
            #how exhaustive the removal of 'clutter' words from questions and anser is
            #the number of processes run
#TODO: preguntas: que es mas? fallan casi siempre


#gets html from url and parses it to find answer occurrencies
@timeout(settings.time_out)
def getFrequencies(url_and_answers):
    try:
        #---------------------perform google search--------------------------
        url = url_and_answers[0] 
        answer1 = url_and_answers[1]
        answer2 = url_and_answers[2]
        answer3 = url_and_answers[3]
        question = url_and_answers[4]
        try:
            with urllib.request.urlopen(url) as response:
                html = response.read()
        except urllib.error.HTTPError:
            return [0,0,0]
        except urllib.error.URLError:
            return [0,0,0]
        debug(url)
        settings.urls_searched+=1
        text = getTextFromHTML(html)
        
        #--------------------test individual words in answer----------------------
        words_answer1=answer1.split(' ')
        words_answer2=answer2.split(' ')
        words_answer3=answer3.split(' ')
        frequencies = [0,0,0]

        processed_answer1 = processIndividualWord(text,words_answer1)
        frequencies[0]=processed_answer1[0]
        valid_words_in_answer1 = processed_answer1[1]

        processed_answer2 = processIndividualWord(text,words_answer2)
        frequencies[1]=processed_answer2[0]
        valid_words_in_answer2 = processed_answer2[1]

        processed_answer3 = processIndividualWord(text,words_answer3)
        frequencies[2]=processed_answer3[0]
        valid_words_in_answer3 = processed_answer3[1]
    
        #normalize
        frequencies[0]=max(frequencies[0],0) / (valid_words_in_answer1+1)**2
        frequencies[1]=max(frequencies[1],0) / (valid_words_in_answer2+1)**2
        frequencies[2]=max(frequencies[2],0) / (valid_words_in_answer3+1)**2

        #---------------------test full answers-------------------------
        full_answer_frequencies = [text.count(answer1), text.count(answer2),text.count(answer3)]
        full_answer_frequencies = list(map(lambda x: x*30, full_answer_frequencies))
        frequencies = [frequencies[0] + full_answer_frequencies[0],frequencies[1] + full_answer_frequencies[1],frequencies[2] + full_answer_frequencies[2]]
        # debug(frequencies)
        
        
        # #---------------------boost freequencies if first urls-------------------------
        # rankUrlBoost = (10 - settings.urls_searched)**2
        # frequencies = [frequencies[0]*rankUrlBoost,frequencies[1]*rankUrlBoost,frequencies[2]*rankUrlBoost]
        #---------------------check that question also appears with answers-------------------------
        questionInPage = isQuestionInPage(text,question)
        if not questionInPage: 
            #if not reduce weight of webpage
            return [frequencies[0]/4,frequencies[1]/4,frequencies[2]/4]
        return frequencies

    except TimeoutError:
        debug("timeout")
        return [0,0,0]

#analyzes the question, sets the corresponding setting variables
    #and returns the processed question
def processQuestion(question):
    #-----------------------Init variables----------------------------
    if settings.numbers_tried == 0:
        settings.isNegative = False
    question_words = question.split(' ')
    new_question = ""

    #------Go through words to remove clutter from question and determine what kind of q it is------------
    for word in question_words:
        #remove ugly characters
        word = word.replace("'", "")
        word = word.replace("?", "")
        word = word.replace("¿", "")
        word = word.replace("¿", "")
        word = word.replace("!", "")
        word = word.replace("¡", "")


        #detect if question is negative
        if word == "no" or word == "rechazó" or word == "rechazar":
            word = ""
            if settings.numbers_tried ==0:
                settings.isNegative = True
        
        #remove meaningless words (dets, props...)
        if len(word)>1:
            new_question = new_question + " " + word

    #-----------------------Checks if it's a definition----------------------------
    new_question=isDefinitionFn(new_question)
    
    #quotes just mess up the searches so remove them

    new_question=new_question.replace('"',"")
    new_question=new_question.replace('“',"")
    new_question=new_question.replace('”',"")
    
    question = new_question

    return question

#alternative method that counts the number of search results of a given answer
def find_answer_count_results(path):
    settings.urls_searched = 0
   #---------------------OCR if path is image--------------------------
    if not isinstance(path, list):
        question_answers = get_question_answers(path)
    else:
        question_answers=path

    question = question_answers[0].lower()
    answer1 = question_answers[1].lower()
    answer2 = question_answers[2].lower()
    answer3 = question_answers[3].lower()
    
    #--------------Set up variables when called for the first time for one question---------------
    if settings.last_first_answer != answer1:
        settings.isNegative = False
        settings.isTermino = False
        settings.numbers_tried=0
        settings.start_time = time.time()
        settings.last_first_answer=answer1
        settings.time_out=2
        if settings.saveAnsweredQuestions:
            text_file = open("trainer.py", "a")
            text_file.write("find_answer(['" + question + "','" + answer1 + "','" + answer2 + "','" + answer3 + "'])\n")
            text_file.close()

   #---------------------Process question-----------------------------------
    question=processQuestion(question)

    #---------------------Search Google-----------------------------------

    questions_with_answer = [[question,answer1],[question,answer2],[question,answer3]]
    
    #get frequencies using processes
    pool = Pool(processes=settings.number_of_workers)
    summed_frequencies = pool.map(getNumberOfResults, questions_with_answer)
    pool.terminate()

    #--------------------------------Print scores----------------------------
    #success is either False or the winner
    winner = print_scores([question_answers[0],answer1,answer2,answer3],summed_frequencies)
    settings.numbers_tried = settings.numbers_tried + 1

    #-----------------------------Search again or return----------------------------
    # #if not sucessful search again but this time including the answers in the question and taking a bit more time
    # if  settings.isNotSure and settings.numbers_tried<2:
    #     time_out = settings.second_time_out
    #     winner = find_answer([question_answers[0] + " " + answer1 + " " + answer2 + " " + answer3,answer1,answer2,answer3])
       
    # else:
    debug("--- querrying time:  %s seconds ---" % (time.time() - settings.start_time))

    return winner


#peforms ocr on the image at path, searches the answer in google and
    #uses getFrequencies to find the most likely answer
def find_answer(path):
    settings.isNotSure = False
    settings.urls_searched = 0
   #---------------------OCR if path is image--------------------------
    if not isinstance(path, list):
        question_answers = get_question_answers(path)
    else:
        question_answers=path

    question = question_answers[0].lower()
    answer1 = question_answers[1].lower()
    answer2 = question_answers[2].lower()
    answer3 = question_answers[3].lower()
    
    #--------------Set up variables when called for the first time for one question---------------
    if settings.last_first_answer != answer1:
        settings.isNegative = False
        settings.isTermino = False
        settings.numbers_tried=0
        settings.start_time = time.time()
        settings.last_first_answer=answer1
        settings.time_out=settings.first_time_out

   #---------------------Process question-----------------------------------
    question=processQuestion(question)

    #---------------------Search Google-----------------------------------
    google_search = GoogleSearch(question)
    google_search.start_search(max_page=settings.google_pages_loaded) # MAYBE 0 IS THE FIRST PAGE?
    urls = google_search.search_result 
    if len(urls) == 0:
        print("Either the question is corrupt or your IP address has been banned :(")
    #---------------------Find occurrences of answers in URL--------------------
    first_urls= urls[:settings.number_of_urls]
    urls_and_answers = []
    for url in first_urls:
        urls_and_answers.append([url,answer1,answer2,answer3,question])

    #get frequencies using processes
    pool = Pool(processes=settings.number_of_workers)
    all_frequencies = pool.map(getFrequencies, urls_and_answers)
    pool.terminate()

    #calculate additive frequencies
    sumed_frequencies = [0,0,0]
    for freq in all_frequencies:
        sumed_frequencies[0]+=freq[0]
        sumed_frequencies[1]+=freq[1]
        sumed_frequencies[2]+=freq[2]
    debug(sumed_frequencies)

    #--------------------------------Print scores----------------------------
    winner = print_scores([question_answers[0],answer1,answer2,answer3],sumed_frequencies)
    settings.numbers_tried = settings.numbers_tried + 1

    #-----------------------------Search again or return----------------------------
    #if not sucessful search again but this time including the answers in the question and taking a bit more time
    if  settings.isNotSure and settings.numbers_tried<2:
        debug("Searching with answers icluded")
        time_out = settings.second_time_out
        print("Try going into URLs with answers included in the search")
        winner = find_answer([question_answers[0] + " " + answer1 + " " + answer2 + " " + answer3,answer1,answer2,answer3])
    else:
        debug("--- querrying time:  %s seconds ---" % (time.time() - settings.start_time))

    return winner

#alternative method that doesn't go into pages but finds occurrencies of the answer in the search page
def find_answer_search_page(path):
    settings.isNotSure = False
    settings.urls_searched = 0
   #---------------------OCR if path is image--------------------------
    if not isinstance(path, list):
        question_answers = get_question_answers(path)
    else:
        question_answers=path

    question = question_answers[0].lower()
    answer1 = question_answers[1].lower()
    answer2 = question_answers[2].lower()
    answer3 = question_answers[3].lower()
    
    #--------------Set up variables when called for the first time for one question---------------
    if settings.last_first_answer != answer1:
        settings.isNegative = False
        settings.isTermino = False
        settings.numbers_tried=0
        settings.start_time = time.time()
        settings.last_first_answer=answer1
        settings.time_out=2

   #---------------------Process question-----------------------------------
    question = processQuestion(question) #set variables
    print(question)
    #---------------------Search Google-----------------------------------
    url = "https://www.google.com/search?newwindow=1&ei=e7EVXN2XJOiKlwTNl7fgAw&q="+ "+".join(question.split())
    url_and_answers = [url,answer1,answer2,answer3]
    html = get(url).text
    # debug(html)
    content = getTextFromHTML(html)
 #--------------------test individual words in answer----------------------
    words_answer1=answer1.split(' ')
    words_answer2=answer2.split(' ')
    words_answer3=answer3.split(' ')
    frequencies = [0,0,0]

    processed_answer1 = processIndividualWord(content,words_answer1)
    frequencies[0]=processed_answer1[0]
    valid_words_in_answer1 = processed_answer1[1]

    processed_answer2 = processIndividualWord(content,words_answer2)
    frequencies[1]=processed_answer2[0]
    valid_words_in_answer2 = processed_answer2[1]

    processed_answer3 = processIndividualWord(content,words_answer3)
    frequencies[2]=processed_answer3[0]
    valid_words_in_answer3 = processed_answer3[1]

    #normalize
    frequencies[0]=max(frequencies[0],0) / (valid_words_in_answer1+1)**2
    frequencies[1]=max(frequencies[1],0) / (valid_words_in_answer2+1)**2
    frequencies[2]=max(frequencies[2],0) / (valid_words_in_answer3+1)**2



    #---------------------test full answers-------------------------
    full_answer_frequencies = [content.count(answer1), content.count(answer2),content.count(answer3)]
    full_answer_frequencies = list(map(lambda x: x*30, full_answer_frequencies))
    frequencies = [frequencies[0] + full_answer_frequencies[0],frequencies[1] + full_answer_frequencies[1],frequencies[2] + full_answer_frequencies[2]]
    # debug(frequencies)
    
    #--------------------------------Print scores----------------------------
    #success is either False or the winner
    winner = print_scores([question_answers[0],answer1,answer2,answer3],frequencies)
    if settings.isNotSure:
        time_out = settings.first_time_out
        print("Try searching in URLs")
        winner = find_answer([question_answers[0],answer1,answer2,answer3])
        # winner = find_answer([question_answers[0] + " " + answer1 + " " + answer2 + " " + answer3,answer1,answer2,answer3])
    else:
        debug("--- querrying time:  %s seconds ---" % (time.time() - settings.start_time))

    return winner
