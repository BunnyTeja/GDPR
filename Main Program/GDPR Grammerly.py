import re
import pandas as pd


#May vary depending on what model is being used
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import nltk
nltk.download("stopwords")
nltk.download("punkt")
from nltk.corpus import stopwords


#not necessary if this will be a web app
from tkinter import *
import tkinter as tk
from tkinter.font import Font
import tkinter.scrolledtext as st

alphanumeric = "qwertyuiopasdfghjklzxcvbnm"
alphanumeric += alphanumeric.upper() + " \n"+"1234567890.,?!:;(){}[]"


colorDictFile = "..\\Data\\ColorDictionary.xlsx"
termListFile = "..\\Data\\TermsList_Preliminary_v.1.xlsx"
defFile = "..\\Data\\Definitions.xlsx"
arts = "..\\Data\\GDPRChapterArticleSections.xlsx"


#To remain unchanged
def obtainTerms():
    defs = pd.read_excel(defFile)
    
    #In the words of the first column of the table, 
    #remove all non-alphabet and non-number characters,
    #as well as excess spaces in the beginning or the end.
    
    defs[defs.columns[0]] = (defs[defs.columns[0]].
                               apply(lambda x: "".join([i for i in x 
                                                        if i.lower() in alphanumeric]).
                                     strip().rstrip()))
    
    #Cleaning up minor deviations specific to the document and to the reference spreadsheet that Marilyn compiled
    defs = (defs.replace("consent of the data subject", "consent").
            replace("international organisation", "international organization"))
    
    other = (pd.read_excel(termListFile).
             rename(columns = {"Artifact Type = Person, Computer, Legal, Others":"Classification",
                               "Expressly defined terms in Article 4 (which deals with definitions): ":"Term",
                               "Rationale to Show":"Rationale for Classification"})
             [["Term", "Classification", "Rationale for Classification"]])
    other = other.fillna("Rationale: None provided")
    other[other.columns[0]] = (other[other.columns[0]].
                               apply(lambda x: "".join([i for i in x 
                                                        if i.lower() in alphanumeric]).
                                     strip().rstrip()))
    
    table = (defs.set_index("Term").
             join(other.set_index("Term"), how = "outer"))
    table["Color"] = table["Classification"].replace(termColorDict)    
    return table

#To remain unchanged
def turnHeadingIntoNum(heading):
    RomanToArabic = {"I":1, "II":2, "III":3, "IV":4,
                     "V":5, "VI":6, "VII":7, "VIII":8,
                     "IX":9, "X":10, "XI":11, "XII":12,
                     "XIII":13, "XIV":14}
    
    chap = heading.split("CHAPTER ")[1].split()[0].rstrip()
    chap = RomanToArabic[chap]
    art = int(heading.split("Article ")[1].split()[0].rstrip())
    sec = int(heading.split("Section ")[1][0])
    return str(chap)+"."+str(art)+"."+str(sec)

#To remain unchanged
def obtainLegalDoc():
    document = (pd.read_excel(arts).reset_index().
            rename(columns = {"index":"Heading"}))
    print(document.columns)
    document["Proper Heading"] = document["Heading"].apply(turnHeadingIntoNum)
    return document


class GUI:
    def __init__(self, x_size, y_size, title = "GDPR Grammerly"):
        self._setupUI(x_size, y_size, title)
        
        x_size = int(x_size)
        y_size = int(y_size)
        self.createUserInputBox(x_size, y_size)
        self.createOutputBox(x_size, y_size)
        
        self.createTermBox(x_size, y_size)
        self.createMentionsList(x_size, y_size)
        
        self.createSectionFinder(x_size, y_size)
        self.addBellsAndWhistles(x_size, y_size)
        
        self.createNLP(x_size, y_size)

    #Takes in: nothing
    #Returns: nothing
    #Description: Creates the GUI, sets up its size, and gives it a title.
    def _setupUI(self, x_size, y_size, title):
        self.gui = Tk()
        self.gui.geometry(x_size+"x"+y_size)
        self.gui.title(title)
    
    #Takes in: the size of the frame in the x and y directions (both integers)
    #Returns: nothing
    #Description: sets up the box for the user to enter their text
    def createUserInputBox(self, x_size, y_size):
        #Creates the text above the user-input textbox
        self.inputDirections = Label(self.gui, 
                                    text = "Enter Text", 
                                    font = ("Times", 17))
        self.inputDirections.place(x = int(x_size/50), y = int(y_size/30))
        
        #Sets up the textbox for user input      
        self.userInput = st.ScrolledText(self.gui,
                                         width = 85, 
                                         height = 7,
                                         wrap = WORD,
                                         font = ("Times New Roman",
                                                 12))
        self.userInput.place(x = int(x_size/50), y = int(y_size/30) + 30)
        
        
        #Sets up the "Submit Text" button (see retrieve_intput)
        self.submitText = Button(self.gui, height=1, width=10, 
                                 text="Submit Text", command= self.retrieve_input)
        self.submitText.place(x = int(x_size/50), y = int(y_size/3) - 20 )
    
    #Takes in: the size of the frame in the x and y directions (both integers)
    #Returns: nothing
    #Description: sets up the box to print the definitions of applicable terms        
    def createOutputBox(self, x_size, y_size):
        #Creates the text above the output
        self.relevant_clauses_label = Label(self.gui, 
                                            text = "Relevant GDPR Terms:", 
                                            font = ("Times New Roman", 17))
        self.relevant_clauses_label.place(x = int(x_size/50), y = int(y_size/3)+30 )
        
        #Sets up the space for the output (see retrieve_intput)
        self.relevantClauses = st.ScrolledText(self.gui,
                                                width = 85, 
                                                height = 3,
                                                wrap = WORD,
                                                font = ("Times New Roman", 12))
        self.relevantClauses.configure(state = "disabled")
        self.relevantClauses.insert(INSERT, "")
        self.relevantClauses.place(x = int(x_size/50), y = int(y_size/3) + 60)

    #Takes in: the size of the frame in the x and y directions (both integers)
    #Returns: nothing
    #Description: sets up the box to accept the term to find the mentions of     
    def createTermBox(self, x_size, y_size):
        self.termInputDirections = Label(self.gui,
                                         text = "Enter Term Here:",
                                         font = ("Times", 14))
        self.termInputDirections.place(x = x_size-480,
                                       y = int(y_size/30))
        self.userTerm = Entry(self.gui, width = 25, font = ("Times New Roman", 12))
        self.userTerm.place(x = x_size-340,
                            y = int(y_size/30) )
        
        self.enterTerm = Button(self.gui, height=1, width=10, 
                                 text="Find in GDPR", command= self.findMentions)
        self.enterTerm.place(x = x_size-100, y = int(y_size/30) )
    
    #Takes in: the size of the frame in the x and y directions (both integers)
    #Returns: nothing
    #Description: sets up the box to print the list of the places the term occurs     
    def createMentionsList(self, x_size, y_size):
        self.mentionsLabel = Label(self.gui,
                                   text = "Places Found:",
                                   font = ("Times", 14))
        self.mentionsLabel.place(x = x_size-480,
                                 y = int(y_size/30)+50)
        self.mentionsList = st.ScrolledText(self.gui,
                                            width = 25,
                                            height = 7,
                                            wrap = WORD,
                                            font = ("Times New Roman", 12))
        self.mentionsList.place(x = x_size-340,
                            y = int(y_size/30)+50 )
        self.mentionsList.configure(state = "disabled")
    
    #Creates the box that will contain the list of relevant article sections
    def createNLP(self, x_size, y_size):
        self.NLPLabel = Label(self.gui,
                              text = "Sections Relevant to Text",
                              font = ("Times", 17))
        self.NLPLabel.place(x = int(x_size/50),
                            y = int(y_size*0.62))
        
        self.NLPOutput = st.ScrolledText(self.gui,
                                         width = 85, 
                                         height = 8,
                                         wrap = WORD,
                                         font = ("Times New Roman", 12))
        
        self.NLPOutput.configure(state = "disabled")
        self.NLPOutput.place(x = int(x_size/50), y = int(y_size*0.67))        
    
    #Returns the text of any given article section
    def createSectionFinder(self, x_size, y_size):
        self.chapLab = Label(self.gui, text = "Chapter:", font = ("Times", 12))
        self.chapLab.place(x = int(x_size*0.75)-90, y = int(y_size*0.4))
        self.chapNum = Entry(self.gui, width = 3, font = ("Times New Roman", 12))
        self.chapNum.place(x = int(x_size*0.75)-30, y = int(y_size*0.4))

        self.artLab = Label(self.gui, text = "Article:", font = ("Times", 12))
        self.artLab.place(x = int(x_size*0.75), y = int(y_size*0.4))
        self.artNum = Entry(self.gui, width = 3, font = ("Times New Roman", 12))
        self.artNum.place(x = int(x_size*0.75)+50, y = int(y_size*0.4))
        
        self.secLab = Label(self.gui, text = "Section:", font = ("Times", 12))
        self.secLab.place(x = int(x_size*0.75)+80, y = int(y_size*0.4))
        self.secNum = Entry(self.gui, width = 3, font = ("Times New Roman", 12))
        self.secNum.place(x = int(x_size*0.75)+135, y = int(y_size*0.4))

        self.enterPlace = Button(self.gui, height=1, width=10,
                                 text="Get Text", command= self.printText)
        self.enterPlace.place(x = int(x_size*0.75)+170, y = int(y_size*0.4))
        
        self.artText = st.ScrolledText(self.gui,
                                        width = 58, 
                                        height = 12,
                                        wrap = WORD,
                                        font = ("Times New Roman", 12))
        self.artText.place(x = int(x_size*0.75)-170, y = int(y_size*0.4)+30)
        self.artText.configure(state = "disabled")
    
    #Takes in: nothing
    #Returns: nothing
    #Description: Finds every article where a given term occurs and prints out their headings.       
    def addBellsAndWhistles(self, x_size, y_size):
        #Sets up the little colored squares and their corresponding labels
        w = Canvas(self.gui, width=250, height=10)
        inc = 0
        colorHeading = Label(self.gui, text = "Term Classification: ", font = ("Times", 10, "bold"))
        colorHeading.place(x=int(13*int(x_size)/50) - 120, y = int(y_size/30) + 320)
        for i, j in enumerate(termColorDict):
            colorLabel = Label(self.gui, text = j, font = ("Times", 10))
            colorLabel.place(x = int(13*int(x_size)/50)+inc, y = int(y_size/30) + 320)
            w.create_rectangle(10 + inc, 0, 20+inc, 10, fill=termColorDict[j], outline = termColorDict[j])
            inc += len(j)*8
        w.place(x = int(13*int(x_size)/50), y = int(y_size/30)+340)

        #Sets up the clear-all button (see clearScreens)
        self.clear = Button(self.gui, height = 1, width = 10, text = "Clear All",
                            command = self.clearScreens)
        self.clear.place(x = int(int(x_size)/2), y = int(y_size)-30)

    #Takes in: the size of the frame in the x and y directions (both integers)
    #Returns: nothing
    #Description: Sets up the clear-all button and the three colored squares
    def retrieve_input(self):
        #Resets any output and any leftover input bolding. 
        self.userInput.tag_remove("BOLD",  "1.0", 'end')
        self.relevantClauses.configure(state = "normal")
        self.relevantClauses.delete("1.0", "end-1c")
        
        italicize = Font(family="Times New Roman", size=12, slant="italic")
        self.relevantClauses.tag_configure("Italicize", font = italicize)
        
        #Obtains the user input, the relevant terms, and what set off the flagger
        inputValue = self.userInput.get("1.0","end-1c")
        termsFound = self.findTermPresence(inputValue)
        line = 1
        #Output that the user sees
        for i, j in enumerate(termsFound):
            addition = (str(i+1)+". "+j.capitalize()+": "+
                        table.set_index("Term").loc[j]["Definitions"]+"\n\n")
            #To put something further that will go under each term, add something to addition here
            addition += "          "+(table.set_index("Term").loc[j]["Rationale for Classification"].
                                      capitalize()+"\n\n")
            ##
            
            if i<(len(termsFound)-1):
                self.relevantClauses.insert(INSERT, addition+"\n")
            else:
                self.relevantClauses.insert(INSERT, addition)
            
            self.relevantClauses.tag_configure(table.set_index("Term").loc[j]["Classification"], 
                                               foreground = table.set_index("Term").loc[j]["Color"])
            self.relevantClauses.tag_add(table.set_index("Term").loc[j]["Classification"], 
                                         str(line)+'.0', str(line+3)+'.0')
            self.relevantClauses.tag_add("Italicize", str(line+2)+".0", str(line+3)+".0")
            
            
            line += 5
        self.relevantClauses.configure(state = "disabled")
        
        self.NLPOutput.configure(state = "normal")
        self.NLPOutput.delete("1.0", "end-1c")
        
        
        
        B = pd.DataFrame([inputValue], columns = ["Text"])
        #print(B)
        B["Articles"] = B["Text"].apply(getArticles, args = (document, ))
        B["Articles"].iloc[0]
        
        relevantSections = "\n".join(B["Articles"].iloc[0])
        
        self.NLPOutput.insert(INSERT, relevantSections)
        self.NLPOutput.configure(state = "disabled")
    #Takes in: a piece of text (String)
    #Returns: a list of the applicable GDPR terms (List of String)
    #Description: Finds the applicable terms and where they occur in the text. Bolds them.
    #             The content of this function will eventually be replaced by something involving NLP.
    def findTermPresence(self, inputValue):
        self.relevantClauses.configure(state = "normal")
        '''These lines will be replaced by NLP'''
        #Iterate through the terms and find which ones occur in the input string
        wordsFlagged = list(set(table[table.columns[0]][table[table.columns[0]].
                                                        apply(lambda x: x in (inputValue.lower()))].values))
        termsFound = wordsFlagged
        '''Up to here'''
        #iterate through the words flagged and look for all the places they occur in the input string
        matchPlaces = []
        for i, j in enumerate(inputValue.lower().split("\n")):
            matchPlaces += [   [ (str(i+1)+"."+str(match.start()), str(i+1)+"."+str(match.end()))
                                  for match in re.finditer(word, j)]
                             for word in wordsFlagged]
        matchPlaces = [i for i in matchPlaces if len(i)>0]
        
        #bolding the relevant part of the user input
        self.bold_font = Font(family="Verdana", size=10, weight="bold")
        self.userInput.tag_configure("BOLD", font=self.bold_font)
        self.userInput.tag_configure("Highlight", background = "yellow")
        
        for termOccurrences in matchPlaces:
            for occurrence in termOccurrences:
                beginning, end = occurrence
                self.userInput.tag_add("BOLD", beginning, end)
                self.userInput.tag_add("Highlight", beginning, end)
                
        return termsFound
    #Takes in: nothing
    #Returns: nothing
    #Description: Finds every article where a given term occurs and prints out their headings. 
    def findMentions(self):
        self.mentionsList.configure(state = "normal")
        inputValue = self.userTerm.get()
        if len(inputValue)>2:
            finds = document[document["Text"].str.lower().str.contains(inputValue.lower())]
            '''this way of finding matches may be replaced by NLP; NLP could also
            be used to change the order from most relevant to least relevant'''
            
            output = str(len(finds))+" matches found:\n\n"
            for i, j in enumerate(finds["Proper Heading"]):
                output += str(i+1)+") "+j+"\n"
            self.mentionsList.delete("1.0", "end-1c")
            self.mentionsList.insert(INSERT, output)
        self.mentionsList.configure(state = "disabled")
    #Takes in: nothing
    #Returns: nothing
    #Description: Displays the GDPR text.
    def printText(self):
        self.artText.configure(state = "normal")
        self.artText.delete("1.0", "end-1c")
        place = (self.chapNum.get()+"."+self.artNum.get()+"."+self.secNum.get())
        display = document.set_index("Proper Heading").loc[place]["Heading"]+"\n\n"
        display += document.set_index("Proper Heading").loc[place]["Text"].replace("\n", " ")
        
        term = self.userTerm.get()
        matches = []
        for i, j in enumerate(display.split("\n")):
            if term.lower() in j.lower():
                matches.append(((str(i+1)+"."+str(j.lower().find(term.lower()))  ),
                                 str(i+1)+"."+str(j.lower().find(term.lower())+len(term))))

        self.artText.insert(INSERT, display)        
        self.artText.tag_configure("Highlight", background = "yellow")
        for i in matches:
            self.artText.tag_add("Highlight", i[0], i[1])
        self.artText.configure(state = "disabled")
        
    #Takes in: nothing
    #Returns: nothing
    #Description: Deletes the contents of all boxes in the GUI. May not be a necessary feature.
    def clearScreens(self):
        for i in [self.relevantClauses, self.artText, self.mentionsList, self.NLPOutput]:
            i.configure(state = "normal")
            i.delete("1.0", "end-1c")
            i.configure(state = "disabled")
        self.userInput.delete("1.0", "end-1c")
        for i in [self.userTerm, self.chapNum, self.artNum, self.secNum]:
            i.delete(0, END)




termColorDict = dict(pd.read_excel(colorDictFile)["Corresponding Color"]) #Just for cosmetic purposes
document = obtainLegalDoc() #Text of the legal document
table = obtainTerms().reset_index() #Terms defined in Chapter 1, Article 4

#----------------
#This is the ML part. I have used the TfidVectorizer to do the embeddings and 
#used cosine similarity to evaluate how close each section's text is to the input text
#The resulting list of articles is ranked by the cosine similarity
def getArticles(inputText, text, relCount = 17):
    inputText = " ".join([i for i in nltk.tokenize.word_tokenize(inputText) if len(i)>2])
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform( [inputText]+list(text["Text"].values.reshape(358,))  )
    emb = pd.DataFrame(X.toarray(), 
                    columns = vectorizer.get_feature_names(), 
                    index = ["Input Text"]+list(text["Heading"]) )

    columns = []
    for i in emb.columns:
      num = False
      for j in range(10):
        if str(j) in list(i):
          num = True
      if not(num):
        columns.append(i)

    emb = emb[columns]
    similarities = []
    for i in range(0, len(text)+1):
      similarities.append(cosine_similarity(X[0], X[i])[0][0] )
    emb["Similarity"] = similarities
    return list(emb.sort_values(by = "Similarity", ascending = False).head(relCount).index[2:])
#----------------


#table with the following columns: Term, Definitions, Classification, Rationale for Classification
window = GUI("1250", "625")
mainloop()