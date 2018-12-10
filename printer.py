
#print scores to stdout according to likelyhood of an answer being the correct one
def print_scores(question_answers,scores):
    question=question_answers[0]
    answer1=question_answers[1]
    answer2=question_answers[2]
    answer3=question_answers[3]

    sum_scores=scores[0]+scores[1]+scores[2]

    if(sum_scores==0):
        print(question)
        print("Those human bitches are smarter than me...")
        return

    percentage_scores = [round(100*scores[0]/sum_scores), round(100*scores[1]/sum_scores), round(100*scores[2]/sum_scores)]

    print("")
    print("")
    print(question)
    bars = ""
    for i in range(0,round(percentage_scores[0]/2)):
        bars += "|"
    print(answer1 + bars + " " + str(percentage_scores[0])+ "%")
    bars = ""
    for i in range(0,round(percentage_scores[1]/2)):
        bars += "|"
    print(answer2 +bars + " "  + str(percentage_scores[1])+ "%")
    bars = ""
    for i in range(0,round(percentage_scores[2]/2)):
        bars += "|"
    print(answer3 + bars + " "  + str(percentage_scores[2])+ "%")
    
