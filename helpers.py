import settings
import errno, os, signal, ssl, sys
from functools import wraps
from bs4 import BeautifulSoup
ssl.match_hostname = lambda cert, hostname: True
from requests import get
import requests
import argparse
#returns a modified question in case it's a definition question
    #and sets the corresponding settings variables
def isDefinitionFn(question):
    question_words = question.split(' ')
    new_question = question
    word_on_quotes = ""
    looksLikeDefinition = False

    for word in question_words:
        #has a word that implies a definition
        if(word == "término" or word == "referimos" or word == "alusión"):
            looksLikeDefinition = True

        #if a word is enclosed by quotes
        if(len(word)>1):
            if (word[0] == '"' or word[0] == "“") and (word[-1] == '"' or word[-1] == "”"):
                word_on_quotes = word[1:-1]

    #we are looking for a definition 
    if looksLikeDefinition:
        if word_on_quotes != "":
            new_question= word_on_quotes +  " significado"
            settings.isDefinition = True

    return new_question

#determines if a question appears on a given page's html code
def isQuestionInPage(text, question):
    words = question.split(" ")
    number_of_words = 0
    total_words = len(words)
    for word in words:
        if text.count(word) > 2 and len(word) > 3:
            number_of_words+=1
    questionInPage = number_of_words>total_words/2

    if settings.isDefinition:
        return True
    else:
        return questionInPage

#returns the processed html code of page
def getTextFromHTML(html):
    soup = BeautifulSoup(html,features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out
    
    #process text (all lower case for example)
    return soup.get_text().lower()

#returns individual-word frequency of answer in a page
def processIndividualWord(text,words_answer):
    frequency = 0
    valid_words_in_answer = 0
    for word in words_answer:
            #NUMBERS TO TEXT
            isNumber= False
            if (word != numberToText(word)):
                isNumber = True
                word =numberToText(word) 
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

#returns the word version of a number
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

#prints to stdout if settings.debug is set to true
def debug(text):
    if settings.debug:
        print(text)

def getNumberOfResults(question_with_answer):
    query = question_with_answer[0] + " " + question_with_answer[1]
    url = "https://google.com/search?q="+query
    raw = get(url)
    soup = BeautifulSoup(raw.text,features="lxml")
    results = soup.find('div',{'id':'resultStats'}).text
    results = results.replace("About","")
    results = results.replace(" ","")
    results = results.replace(",","")
    results = results.replace("results","")
    results = int(results)

    return results
