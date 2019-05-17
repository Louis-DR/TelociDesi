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

def convert() :
    validArchi = True
    validASM = True

    try:
        archi
    except NameError:
        showerror("Erreur","Missing architecture (.truitea) file")
        validArchi = False

    try:
        assembly
    except NameError:
        showerror("Erreur", "Missing assembly (.truitep) file")
        validASM = False
    
    if (validArchi and validASM):
        global outputTab
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
                if (i<(3**(archi["wordsize"])-1)/2 or i>-(3**(archi["wordsize"])-1)/2 ) :
                    outputTab.append(str(i))
                    #print("check")
                else :
                    print("Error in line : " + line)
                    print("Error : invalid value. Compilation stopped")
                    return -1

            else: #check opcode arguments
                print(archi["operations"][currentItem])
                print(tab)
                lineStructure = archi["operations"][currentItem]
                trad = str(lineStructure[0])
                print(trad)
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
                            else:
                                #print(int(dec2terstr(dec2ter(int(tab[iOperand+1])))))
                                trad = trad + dec2terstr(dec2ter(int(tab[iOperand+1])))
                        else :
                            print("Error in line :" + line)
                            print("Error : invalid operand "+ operand +". Compilation stopped")
                            return -1

                    #At this point, line syntax is considered to be valid   
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

