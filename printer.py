
import settings

#print scores to stdout according to likelyhood of an answer being the correct one
#returns the most likely answer or False if it's not sure
def print_scores(question_answers,scores):
    question=question_answers[0]
    answer1=question_answers[1]
    answer2=question_answers[2]
    answer3=question_answers[3]

    original_answer1 = answer1
    original_answer2 = answer2
    original_answer3 = answer3
    longest_answer = max(len(answer1), len(answer2), len(answer3))
    settings.isNotSure = False

    class bcolors:
        GREEN = '\033[92m'
        ORANGE = '\033[93m'
        RED = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
    #left pad answers
    for i in range(0,longest_answer-len(answer1)):
        answer1= " " + answer1
    for i in range(0,longest_answer-len(answer2)):
        answer2= " " + answer2
    for i in range(0,longest_answer-len(answer3)):
        answer3= " " + answer3
    sum_scores =scores[0]+scores[1]+scores[2]

    if(sum_scores==0):
        if settings.printAnswers:
            print(question)
            print("")
            print(bcolors.RED + "Literally no occurrencies of the answers found..." + bcolors.ENDC)
            print("")
        settings.isNotSure=True
        return  

    percentage_scores = [round(100*scores[0]/sum_scores), round(100*scores[1]/sum_scores), round(100*scores[2]/sum_scores)]
    
    #detect fake negatives
    

    if settings.isNegative:
        #TODO: try to spot false negatives
        percentage_scores[0]=100-percentage_scores[0]
        percentage_scores[1]=100-percentage_scores[1]
        percentage_scores[2]=100-percentage_scores[2]
        
    if settings.printAnswers:
        print("")
        print("")
        print(question)
        bars = ""
        for i in range(0,round(percentage_scores[0]/2)):
            bars += "|"
        print(answer1 + " " + bars + " " + str(percentage_scores[0])+ "%")
        bars = ""
        for i in range(0,round(percentage_scores[1]/2)):
            bars += "|"
        print(answer2 + " " + bars + " "  + str(percentage_scores[1])+ "%")
        bars = ""
        for i in range(0,round(percentage_scores[2]/2)):
            bars += "|"
        print(answer3 + " " + bars + " "  + str(percentage_scores[2])+ "%")

    #Print the winner nice and clear

    winner = ""
    winner_index = 0
    loser1=1
    loser2=2
    if percentage_scores[0] > percentage_scores[1]:
        if percentage_scores[0]> percentage_scores[2]:
            winner = original_answer1
            winner_index = 0
            loser1=1
            loser2=2
        else:
            winner = original_answer3
            winner_index = 2
            loser1=1
            loser2=0
    else:
        if percentage_scores[1]> percentage_scores[2]:
            winner = original_answer2
            winner_index = 1
            loser1=2
            loser2=0
        else:
            winner = original_answer3
            winner_index = 2
            loser1=1
            loser2=0

    color = bcolors.RED


    if percentage_scores[winner_index]-percentage_scores[loser1]>5 and percentage_scores[winner_index]-percentage_scores[loser2]>5:
        color = bcolors.ORANGE
    if percentage_scores[winner_index]-percentage_scores[loser1]>25 and percentage_scores[winner_index]-percentage_scores[loser2]>25:
        color = bcolors.GREEN
    if settings.printAnswers:
        print("")
        print("")
        print("                    " + color + winner + bcolors.ENDC)
        print("")
        print("")

    #not successfull search
    if color == bcolors.RED or scores[0] + scores[1] + scores[2] < 2:
        if settings.printAnswers:
            print("")
            print(bcolors.RED + "Those human bitches are smarter than me..." + bcolors.ENDC)
            print("")
        settings.isNotSure=True

    return winner