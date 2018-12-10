from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
#returns an array: [question, answer1, answer2, answer3] given an input image
def get_question_answers(image):
    #open file and set init variables
    im = Image.open(image).convert('L')
    image_size = im.size
    width = image_size[0]
    height = image_size[1]

    # img.crop( ( left, top, right, bottom ) )  # size: 45, 45
    # QUESTION
    top=3*height/4.7
    bottom=3*height/3.9
    question = im.crop((1, top, width, bottom))
    question.save('test.png')
    # ANSWER 1
    top=3*height/3.8
    bottom=3*height/3.6
    answer1 = im.crop((width/9.5, top, 8.5*width/10, bottom))

    # ANSWER 2
    top=3*height/3.45
    bottom=3*height/3.3
    answer2 = im.crop((width/9.5, top, 8.5*width/10, bottom))

    # ANSWER 3
    top=3*height/3.15
    bottom=3*height/3.03
    answer3 = im.crop((width/9.5, top, 8.5*width/10, bottom))


    ################################################################
    #read text form images and save it to variables
    ################################################################

    #  Apply filter to image in case backgroud gets noisy
    # threshold woudl be enough

    # Get plain text from question
    #GLOBAL VARIABLES
    question = pytesseract.image_to_string(question,lang="spa")
    answer1 = pytesseract.image_to_string(answer1,lang="spa").lower()
    answer2 = pytesseract.image_to_string(answer2,lang="spa").lower()
    answer3 = pytesseract.image_to_string(answer3,lang="spa").lower()

    #process questions, all lowercase for example
    question_parsed = question.replace("\n", " ")
    return [question_parsed,answer1,answer2,answer3]
