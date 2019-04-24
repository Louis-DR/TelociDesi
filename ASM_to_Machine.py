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
    filenameEXP = asksaveasfilename(title="Sauvegarder votre document",filetypes=[('truitem files','*.truitem'),('all files','.*')])
    fmemory =  open(filenameEXP,"w+")
    fmemory.close()
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
        #step 1 : read lines, check syntax & translate ASM to ternary codes
        outputTab = []
        for line in assembly: #read lines
            validOpcode = False
            isInteger = False
            tab = line.split(" ")
            for item in archi["operations"]: #check if opcode is referenced
                print(item)
                print(tab[0].strip())
                if item.strip() == tab[0].strip():
                    validOpcode = True
                    break
            if (isInt(tab[0].strip())): #or if line is pure value
                isInteger = True
            if (validOpcode or isInteger):
                print("Valid Opcode")
            else :
                print("Error : "+ tab[0].strip() +" opcode not found")
                return -1

            if (isInteger):
                if (len(tab)>1):
                    print("Warning : Ignored "+ str(len(tab)-1) +" invalid arguments")
                i = int(tab[0])   
                if (i<3**(archi["wordsize"])-1) :
                    outputTab.append(i)
                else:
                    print("Error : invalid value")
                    return -1

            if(validOpcode):
                pass
            else:
                return -1
        #step 2 : ternary to dec

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

