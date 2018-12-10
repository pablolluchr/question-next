from googlesearch import search 
import urllib
from bs4 import BeautifulSoup

#returns [answer1_occurrences,answer2_occurrences,answer3occurrences] corresponding to the number_of_urls
#   querries starting from from_url
def google_query(question_answers,from_url, number_of_urls):

    answer1_occurrences=0
    answer2_occurrences=0
    answer3_occurrences=0
    question=question_answers[0]
    answer1=question_answers[1]
    answer2=question_answers[2]
    answer3=question_answers[3]
    #if you get rllib.error.HTTPError errors change tld to com
    for url in search(question, lang='es', tld='es', num=number_of_urls-1, start=from_url, stop=number_of_urls+from_url-1,pause=2): 
        print(url)
        try:

            with urllib.request.urlopen(url) as response:
                html = response.read()
        except urllib.error.HTTPError:
            continue

        soup = BeautifulSoup(html,features="html.parser")

        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()    # rip it out
        # get text
        
        #process text (all lower case for example)
        text = soup.get_text().lower()

        #number of occurrences of each string
        answer1_occurrences += text.count(answer1)
        answer2_occurrences += text.count(answer2)
        answer3_occurrences += text.count(answer3)
    occurrences = [answer1_occurrences,answer2_occurrences,answer3_occurrences]
    return occurrences
