


import os, sys, time
from image_process import get_question_answers
from google_search import google_query
from printer import print_scores

def find_answer(image):
    ################################################################
    #crop image to create question, answer1, answer2 and answer3
    ################################################################
    question_answers = get_question_answers(image)

    #GLOBAL VARIABLES
    question = question_answers[0]
    answer1 = question_answers[1]
    answer2 = question_answers[2]
    answer3 = question_answers[3]

    #DO REVERSED IF ITS NEGATIVE

    #CREATING TWO PROCESS TO QUERRY SIMULTANEOUSLY
    # file descriptors r, w for reading and writing 
    r, w = os.pipe() 
    #Creating child process using fork 
    processid = os.fork() 

    if processid: #parent process
        os.close(w) 
        r = os.fdopen(r) 
        parent_occurrencies = google_query(question_answers,0, 3)
        child_string = r.read() 
        child_occurrencies_string = child_string.split(',')

        child_occurrencies = list(map(int, child_occurrencies_string))
        total_scores = [x + y for x, y in zip(child_occurrencies, parent_occurrencies)]

        print_scores(question_answers, total_scores)


    else: #child process
        os.close(r) 
        w = os.fdopen(w, 'w') 
        ocurrences = google_query(question_answers,3,3)
        w.write(str(ocurrences[0])+","+str(ocurrences[1])+","+str(ocurrences[2])) 
        w.close() 

def find_answer_no_fork(image):
    ################################################################
    #crop image to create question, answer1, answer2 and answer3
    ################################################################
    question_answers = get_question_answers(image)

    #GLOBAL VARIABLES
    question = question_answers[0]
    answer1 = question_answers[1]
    answer2 = question_answers[2]
    answer3 = question_answers[3]

    parent_occurrencies = google_query(question_answers,0, 3)
    print_scores(question_answers,parent_occurrencies)

