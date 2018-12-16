from main import find_answer, find_answer_count_results, find_answer_search_page
import sys, os
import settings


#possible arguments: newset, accuracy, test <number_of_set>
action = sys.argv[1]
desired_test_set = -1
if action == "test":
    desired_test_set= int(sys.argv[2])

global right_answers
right_answers=0
global total_questions
total_questions = 0
global printFailedQuestions
printFailedQuestions=False

def checkQuestion(questionAnswers,rightAnswer):
    rightAnswer=rightAnswer.lower()
    global total_questions
    global right_answers
    global printFailedQuestions
    answer = find_answer_search_page(questionAnswers)
    if not type(answer) is str:
        answer = "?"
    total_questions+=1
   
    if(answer == rightAnswer):
        print( '\033[92m' + questionAnswers[0] + " --> " + answer + '\033[0m')
        right_answers+=1
    else:
        if printFailedQuestions:
            failed_questions =open("failed_questions.txt", "a")
            failed_questions.write("[['" + questionAnswers[0] + "','" + questionAnswers[1] + "','" + questionAnswers[2] + "','" + questionAnswers[3] + "'],'" + rightAnswer + "'],")
            failed_questions.close()
        
        print( '\033[91m' +questionAnswers[0] + " --> " + answer + " [Right answer: " + rightAnswer + ']\033[0m')

if action == "accuracy": #check accuracy over all tests in test_sets
    #if you leave a blank line the tester will stop there
    try:
        failed_questions =open("failed_questions.txt", "a")
        settings.printAnswers=False
        settings.debug=False
        test_set_number = 1
        test_sets =open("test_sets.txt", "r")
        for test_set in test_sets:
            try:
                print("Reading test_set_number: " + str(test_set_number) + "...")
                if(len(test_set)<20):
                    break
                test_set=eval(test_set)
                for test in test_set:
                    checkQuestion(test[0],test[1])
                test_set_number+=1
            except:
                continue
        test_sets.close
    except KeyboardInterrupt:
        pass
    # except TypeError:
        # pass

    failed_questions.close
    if total_questions != 0:
        print('\033[1m' + "--Accuracy: " + str(round(100*right_answers/total_questions)) + '%\033[0m')


if action == "test": #test an individual set stored at test_sets
    try:
        test_set_number = 1
        test_sets =open("failed_questions.txt", "r")
        for test_set in test_sets:
            if(test_set_number != desired_test_set):
                test_set_number+=1
                continue
            test_set=eval(test_set)
            for test in test_set:
                checkQuestion(test[0],test[1])
            test_set_number+=1
        test_sets.close
    except KeyboardInterrupt:
        pass

if action == "newset": #Parse full game into set of questions and saves it in test_sets.txt
    new_set_file = open("new_test_set.txt", "r")
    lines=new_set_file.read().split('\n')
    new_set_file.close()
    #remove empty words/lines
    lines = list(filter(lambda x: len(x) > 0, lines))
    lines = list(filter(lambda x: x != " ", lines))
    lines = list(filter(lambda x: x[:8] != "Pregunta", lines))
    lines = list(filter(lambda x: x[:8] != "killer", lines))


    #write to test_sets
    # try:
    test_sets = open("test_sets.txt", "a")
    test_sets.write("[")
    for i in range (0,len(lines)-1,9):
        endCombination = ","
        if(i>=len(lines)-10):
            endCombination = "]\n"

        if(lines[i+2]=="Correcta"):
            test_sets.write("[['" + lines[i] + "','" + lines[i+1] + "','" + lines[i+4] + "','" + lines[i+6] + "'],'" + lines[i+1] + "']" + endCombination)
        if(lines[i+4]=="Correcta"):
            test_sets.write("[['" + lines[i] + "','" + lines[i+1] + "','" + lines[i+3] + "','" + lines[i+6] + "'],'" + lines[i+3] + "']" + endCombination)
        if(lines[i+6]=="Correcta"):
            test_sets.write("[['" + lines[i] + "','" + lines[i+1] + "','" + lines[i+3] + "','" + lines[i+5] + "'],'" + lines[i+5] + "']" + endCombination)
    print("New test created successfully!")
    # except IndexError:
    #     print("The test_set doesn't include answers! Go remove the extra [ that you added to test_sets.txt")
    test_sets.close()
