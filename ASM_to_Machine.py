#Script de conversion d'une entrée ASM à un code exécutable par le processeur ternaire

#CdC - Lecture de fichiers texte .truitep
# format ASM : 0: OPT OPERAND OPERAND
#              1: OPT OPERAND OPERAND
#              3: OPT OPERAND OPERAND
#              ....
# Fichier d'architecture (JSON)
#Sort un dictionnaire JSON de mots TCD (ternaire codé décimal) mémoire pour clé adresse mémoire séquentielle affecte un mot

import json
from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import *
from dec2ter import *
from dec2bin import *

#Load architecture specifications
def loadArchi():
    global archi
    filename = askopenfilename(title="Ouvrir un fichier architecture",filetypes=[('truitea files','*.truitea'),('all files','*.*')])
    farchi = open(filename,"r")
    archi =  json.load (farchi)
    farchi.close()
    return 0

#Load assembly file
def loadASM():
    global assembly
    filenameASM = askopenfilename(title="Ouvrir votre document",filetypes=[('truitep files','*.truitep'),('all files','.*')])
    fspec = open(filenameASM,"r")
    assembly = fspec.readlines()
    fspec.close()
    return 0

#Export implementation file
def exportBin():
    try :
        filenameEXP = asksaveasfilename(title="Sauvegarder votre document",filetypes=[('truitem files','*.truitem'),('all files','.*')])
        fmemory =  open(filenameEXP,"w+")
        for line in outputTab:
            fmemory.write(line+'\n')
        fmemory.close()
    except : return -1
    return 0

def isInt(v):
    try : i = int(v)
    except : return False
    return True

def format(lineTab,lineStructure,systemBase):
    res = ""+lineStructure[0]
    if systemBase :
        for i in range(len(lineStructure)-1):
            temp  = dec2terXtrit(int(lineTab[i+1]),lineStructure[i+1])
            res = res + temp
    else:
        for i in range(len(lineStructure)-1):
            temp  = dec2binXbit(int(lineTab[i+1]),lineStructure[i+1])
            res = res + temp
    return res

def convert() :
    validArchi = True
    validASM = True
    global outputTab

    try:
        base = archi["base"]
        if (base=="ter"):
            systemBase = 1
        elif (base=="bin"):
            systemBase = 0
        else :
            print("Erreur : unsupported architecture type")
            return -1
    except NameError:
        showerror("Erreur","Missing architecture (.truitea) file")
        validArchi = False

    try:
        assembly
    except NameError:
        showerror("Erreur", "Missing assembly (.truitep) file")
        validASM = False
    
    if (validArchi and validASM and systemBase):
        #Ternary architecture
        #step 1 : read lines, check syntax & translate ASM to ternary codes
        outputTab = []
        for line in assembly: #read lines
            validOpcode = False
            isInteger = False
            currentItem = None
            tab = line.split(" ")
            for iCharacter in range(len(tab)): #Cleaning tab to remove whitespace characters and @ and %
                tab[iCharacter] =  tab[iCharacter].strip()
                tab[iCharacter] = tab[iCharacter].strip('%@')
            if (isInt(tab[0])): #if line is pure value
                isInteger = True
            else: #or opcode is referenced in architecture
                for item in archi["operations"]:
                    if item.strip() == tab[0]:
                        validOpcode = True
                        currentItem = item
                        break
            if (validOpcode or isInteger): #then valid opcode
                print("Valid Opcode")
            else : #Compilation stopped - Error message
                print("Error in line : " + line)
                print("Error : "+ tab[0] +" opcode not found. Compilation stopped")
                return -1

            if (isInteger):
                if (len(tab)>1):
                    print("Warning : Ignored "+ str(len(tab)-1) +" invalid arguments")
                i = int(tab[0]) 
                if (i<(3**(archi["valsize"])-1)/2 or i>-(3**(archi["valsize"])-1)/2 ) :
                    res = ""+ dec2terXtrit(i,archi["valsize"])
                else :
                    print("Error in line : " + line)
                    print("Error : invalid value. Compilation stopped")
                    return -1

                for j in range (len(res),archi["wordsize"]):
                        res = "0"+res
                print(res)
                outputTab.append(res)

            else: #check opcode arguments
                lineStructure = archi["operations"][currentItem]
                trad = ""
                if (len(tab)>=len(lineStructure)):
                    if(len(tab)>len(lineStructure)) :
                        print("Warning : Ignored "+ str(len(tab)-1) +" invalid arguments")
                    for iOperand in range(len(lineStructure)-1):
                        operand = tab[iOperand+1]
                        if(isInt(operand)):
                            if (int(operand)>3**lineStructure[iOperand+1]-1): #checking word size according to architecture file
                                print("Error in line :" + line)
                                print("Error : invalid operand "+ operand +". Compilation stopped")
                                return -1
                        else :
                            print("Error in line :" + line)
                            print("Error : invalid operand "+ operand +". Compilation stopped")
                            return -1

                    #At this point, line syntax is considered to be valid   
                    trad = trad + format(tab,lineStructure,systemBase)

                    if len(trad)<archi["wordsize"]:
                        for j in range(len(trad),archi["wordsize"]):
                            trad = trad +"0"
                    outputTab.append(trad)

                else:
                    print("Error in line :" + line)
                    print("Error : missing arguments. Compilation stopped")
                    return -1
        print(outputTab)
        return 0

    elif (validArchi and validASM and not systemBase):
        #Binary architecture
        #step 1 : read lines, check syntax & translate ASM to ternary codes
        outputTab = []
        for line in assembly: #read lines
            validOpcode = False
            isInteger = False
            currentItem = None
            tab = line.split(" ")
            for iCharacter in range(len(tab)): #Cleaning tab to remove whitespace characters and @ and %
                tab[iCharacter] =  tab[iCharacter].strip()
                tab[iCharacter] = tab[iCharacter].strip('%@')
            if (isInt(tab[0])): #if line is pure value
                print("value in line: " + tab[0])
                isInteger = True
            else: #or opcode is referenced in architecture
                for item in archi["operations"]:
                    print("item in archi: " + item)
                    print("value in line: " + tab[0])
                    if item.strip() == tab[0]:
                        validOpcode = True
                        currentItem = item
                        break
            if (validOpcode or isInteger): #then valid opcode
                print("Valid Opcode")
            else : #Compilation stopped - Error message
                print("Error in line : " + line)
                print("Error : "+ tab[0] +" opcode not found. Compilation stopped")
                return -1

            if (isInteger):
                if (len(tab)>1):
                    print("Warning : Ignored "+ str(len(tab)-1) +" invalid arguments")
                i = int(tab[0]) 
                #print(i)  
                #print(archi["wordsize"])
                if (i<(2**(archi["valsize"])-1)/2 or i>-(2**(archi["valsize"])-1)/2 ) :
                    outputTab.append(dec2binXbit(i,archi["valsize"]))
                    #print("check")
                else :
                    print("Error in line : " + line)
                    print("Error : invalid value. Compilation stopped")
                    return -1

            else: #check opcode arguments
                print(archi["operations"][currentItem])
                print(tab)
                lineStructure = archi["operations"][currentItem]
                trad = ""
                #print(trad)
                if (len(tab)>=len(lineStructure)):
                    if(len(tab)>len(lineStructure)) :
                        print("Warning : Ignored "+ str(len(tab)-1) +" invalid arguments")
                    for iOperand in range(len(lineStructure)-1):
                        operand = tab[iOperand+1]
                        if(isInt(operand)):
                            if (int(operand)>2**lineStructure[iOperand+1]-1): #checking word size according to architecture file
                                print("Error in line :" + line)
                                print("Error : invalid operand "+ operand +". Compilation stopped")
                                return -1
                        else :
                            print("Error in line :" + line)
                            print("Error : invalid operand "+ operand +". Compilation stopped")
                            return -1

                    #At this point, line syntax is considered to be valid   
                    trad = trad + format(tab,lineStructure,systemBase)

                    if len(trad)<archi["wordsize"]:
                        for j in range(len(trad),archi["wordsize"]):
                            trad = trad +"0"
                    print(trad)              
                    outputTab.append(trad)

                else:
                    print("Error in line :" + line)
                    print("Error : missing arguments. Compilation stopped")
                    return -1
        #step 2 : ternary to dec
        print(outputTab)
        return 0
    else:
        return -1

fenetre = Tk()

#Architecture frames
Frame1  = Frame(fenetre)
Frame1.pack(side = LEFT, padx=30, pady= 30)

Frame2  = Frame(fenetre)
Frame2.pack(side = LEFT, padx=30, pady=30)

Frame3 = Frame(fenetre)
Frame3.pack(side = RIGHT, padx=30, pady= 30)

Frame4 = Frame(fenetre)
Frame4.pack(side= BOTTOM, padx = 30, pady=30)

#Frame1
labelArchi = Label(Frame1, text = "Fichier architecture").pack()
boutonArchi=Button(Frame1, text="Charger", command=loadArchi).pack()
#Frame2
labelASM = Label(Frame2, text = "Fichier assembleur").pack()
boutonASM = Button(Frame2, text = "Charger", command=loadASM).pack()
#Frame3
labelExp = Label(Frame3, text = "Exporter sous...")
boutonExp = Button(Frame3, text = "Emplacement", command = exportBin).pack()
#Frame4
boutonOp = Button(Frame4, text  ="Convertir", command = convert).pack()

fenetre.mainloop()

