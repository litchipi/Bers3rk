#!/usr/bin/env python3

from bers3rk import Berserk
import os, sys
import hashlib

def hash_data(d):

    return hashlib.sha512(d.encode()).digest().hex()

def treat_data(d):
    return hash_data(hash_data(hash_data(d)))


wins_raw = ["heure", "p0kem0n", "Chocol4t", "GOUTER", "MUS1QUE", "4Lpha", "mUs1QU3", "Ch0c0LAT", "heur3musIqUe"]

WINS = [treat_data(w) for w in wins_raw]

#WINS = ["QwErTy", "V3RIZK4", "smh413", "sch00l13", "PUSSYCATD0LLS", "PoOp3", "2014"]

def fct_try(data, params):
    return treat_data(data) in WINS

brute = Berserk(fct_try, {"max_temp_C":80, "sensor_device_name":"k10temp-pci-00c3", "sensor_data_name":"Tctl", "maxmix":2})
brute.add_word_default_modif()
brute.allow_random_modif()
brute.add_stop_condition(lambda r: all([w in r for w in WINS]))
#brute.run("/usr/share/seclists/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt")
brute.run(os.path.dirname(sys.argv[0]) + "/tester_wordlist")
