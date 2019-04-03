#Script de conversion d'une entrée ASM à un code exécutable par le processeur ternaire

#CdC - Lecture de fichiers texte .truitep
# format ASM : 0: OPT OPERAND OPERAND
#              1: OPT OPERAND OPERAND
#              3: OPT OPERAND OPERAND
#              ....
# Fichier d'architecture (JSON)
#Sort un dictionnaire JSON de mots TCD (ternaire codé décimal) mémoire pour clé adresse mémoire séquentielle affecte un mot

import json

#fspec = open("spec.truitep","r")

farchi = open("architecture.truitea","r")

archi =  json.load (farchi)
print ("Test")
print( archi ["architecture"])

