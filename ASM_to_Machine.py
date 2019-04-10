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

#Load architecture specifications
def loadArchi():
    filename = askopenfilename(title="Ouvrir un fichier architecture",filetypes=[('truitea files','*.truitea'),('all files','*.*')])
    farchi = open(filename,"r")
    archi =  json.load (farchi)
    farchi.close()
    return archi

#Load assembly file
def loadASM():
    filenameASM = askopenfilename(title="Ouvrir votre document",filetypes=[('txt files','.txt'),('all files','.*')])
    fspec = open(filenameASM,"r")
    assembly = fspec.readlines()
    fspec.close()

fenetre = Tk()

#Architecture frames
Frame1  = Frame(fenetre)
Frame1.pack(side = LEFT, padx=30, pady= 30)


#Frame1
labelASM = Label(Frame1, text = "Fichier assembleur").pack()
bouton=Button(Frame1, text="Charger", command=loadArchi).pack()

fenetre.mainloop()

#Première ligne de assembly : informations importantes


#print( archi ["architecture"])

#fspec.close();

