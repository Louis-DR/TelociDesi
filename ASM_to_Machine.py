#Script de conversion d'une entrée ASM à un code exécutable par le processeur ternaire

#CdC - Lecture de fichiers texte .truitep
# format ASM : 0: OPT OPERAND OPERAND
#              1: OPT OPERAND OPERAND
#              3: OPT OPERAND OPERAND
#              ....
# Fichier d'architecture (JSON)
#Sort un dictionnaire JSON de mots TCD (ternaire codé décimal) mémoire pour clé adresse mémoire séquentielle affecte un mot

import json

#Load architecture specifications
farchi = open("architecture.truitea","r")
archi =  json.load (farchi)
farchi.close();

#Load assembly file
#fspec = open("spec.truitep","r")
#assembly = fspec.readlines()
#fspec.close()



print( archi ["architecture"])

fspec.close();