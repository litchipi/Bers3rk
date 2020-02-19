#!/usr/bin/env python3

from berserk import Berserk

WINS = ["heure", "p0kem0n", "Chocol4t", "GOUTER", "MUS1QUE", "4Lpha"]

def fct_try(data, params):
    return data in WINS

with open("test_wl", "r") as fichier:
    data = fichier.read().split("\n")

brute = Berserk(fct_try, {})
brute.add_word_default_modif()
brute.add_stop_condition(lambda r: all([w in r for w in WINS]))
brute.run(data)
