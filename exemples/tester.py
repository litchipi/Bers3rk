#!/usr/bin/env python3

from bers3rk import Berserk
import os, sys

#WINS = ["heure", "p0kem0n", "Chocol4t", "GOUTER", "MUS1QUE", "4Lpha"]
WINS = ["QwErTy", "V3RIZK4", "smh413", "sch00l13", "PUSSYCATD0LLS", "PoOp3", "2014"]

def fct_try(data, params):
    return data in WINS

brute = Berserk(fct_try, {"max_temp_C":80})
brute.add_word_default_modif()
brute.add_stop_condition(lambda r: all([w in r for w in WINS]))
#brute.run("/home/eve/Documents/pentest_tools/bers3rk/exemples/tester_wordlist")
#brute.run("/home/eve/Documents/pentest_tools/wordlists/rockyou.txt")
brute.run("/home/eve/Documents/pentest_tools/wordlists/10-million-password-list-top-100000.txt")
print(all([w in brute.results for w in WINS]))
