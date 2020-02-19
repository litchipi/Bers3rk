#!/usr/bin/env python3
#-*-encoding:utf-8*-

import math
import os
import sys
import time


COLOR_PURPLE = "\033[95m"
COLOR_GREEN = "\033[92m"
COLOR_ORANGE = "\033[93m"
COLOR_NONE = "\033[0m"
CLEAR_LINE = "\033[2K\r" + COLOR_NONE

class Berserk:
    default_params = {
            "quit_on_first_success":False,
            "save_sucessed_word":None,
            "nbsimilar":0,
            "joinchar":"",
            "extensions":[],
            "maxmix":2,
            "suffix":"",
            "prefix":"",
            "try_delay_ms":0.0,
            }

    def __init__(self, try_fct, fct_params):
        params = self.default_params.copy()
        params.update(fct_params)
        self.try_fct = try_fct
        self.params = params
        if (self.params["save_sucessed_word"] is not None) and not (os.path.isfile(self.params["save_sucessed_word"])):
            with open(self.params["save_sucessed_word"], "w") as fichier:
                fichier.write("")
        self.last_try = 0
        self.modif_functions = list()
        self.stop_conditions = list()
        self.results = list()

    def tryw(self, data):
        time.sleep(max(0, (self.params["try_delay_ms"]/1000) - (time.time()-self.last_try)))
        self.last_try = time.time()
        sys.stdout.write(CLEAR_LINE + "Trying data: {}{}{}".format(COLOR_ORANGE, data, COLOR_NONE))
        sys.stdout.flush()
        res = self.try_fct(data, self.params)
        if res and (data not in self.results):
            self.results.append(data)
            print("\033[F" + CLEAR_LINE + "Result found !\t-> \t{}{}{}\n".format(COLOR_GREEN, data, COLOR_NONE) + CLEAR_LINE)
            if self.params["save_sucessed_word"] is not None:
                with open(self.params["save_sucessed_word"], "a") as fichier:
                    fichier.write(data)
            if self.params["quit_on_first_success"]:
                sys.exit(0)
            if any([cond(self.results) for cond in self.stop_conditions]):
                sys.exit(0)

    def fuzz_recursive(self, wl, past_data=[], n=0, fct=lambda x: x):
        for word in wl:
            w = fct(word)

            if past_data.count(w) > self.params["nbsimilar"]:
                continue

            data = self.params["joinchar"].join(past_data + [w])
            if data == "":
                continue

            self.tryw(self.params["prefix"] + data + self.params["suffix"])
            for e in self.params["extensions"]:
                self.tryw(self.params["prefix"] + data + "." + e)

        recurs = (n <= self.params["maxmix"])
        for word in wl:
            if not recurs: break
            w = fct(word)
            if past_data.count(w) >= self.params["nbsimilar"]:
                continue
            data = self.params["joinchar"].join(past_data + [w])
            if data == "":
                continue
            self.fuzz_recursive(wl, past_data=past_data + [w], n=n+1, fct=fct)

    def mix_fcts(self, data, fcts, past_fct=lambda x: x, n=0, steps=0, totposs=0):
        for i in range(n, len(fcts)):
            cf = lambda x: past_fct(fcts[i](x))
            self.fuzz_recursive(data, fct=cf)
            steps += 1
            steps = self.mix_fcts(data, fcts, past_fct=cf, n=n+1, steps = steps, totposs=totposs)

        sys.stdout.write("\033[F" + CLEAR_LINE + "{}% done\n".format(round((steps/totposs)*100, 3)))
        sys.stdout.flush()
        return steps

    def add_modif_function(self, fct, priority=0):
        self.modif_functions.append((fct, priority))

    def get_modif_functions(self):
        return [f for f, p in sorted(self.modif_functions, key=lambda x: x[1], reverse=True)]

    def add_word_default_modif(self):
        self.add_modif_function(lambda x: x.lower(), 100)
        self.add_modif_function(lambda x: x.upper(), 99)
        self.add_modif_function(lambda x: x.capitalize(), 98)
        self.add_modif_function(lambda x: x.replace("o", "0"), 97)
        self.add_modif_function(lambda x: x.replace("i", "1"), 96.5)
        self.add_modif_function(lambda x: x.replace("e", "3"), 96)
        self.add_modif_function(lambda x: x.replace("a", "4"), 95)
        self.add_modif_function(lambda x: x.replace("O", "0"), 94)
        self.add_modif_function(lambda x: x.replace("I", "1"), 93.5)
        self.add_modif_function(lambda x: x.replace("E", "3"), 93)
        self.add_modif_function(lambda x: x.replace("A", "4"), 92)

    def add_stop_condition(self, condition):        #Will pass results found to the function "condition", if True will stop
        self.stop_conditions.append(condition)

    def run(self, wl, skip_single_modif=False, skip_mixed_modif=False):
        print(COLOR_PURPLE + "[*] Testing with normal words from list ...\n" + COLOR_NONE)
        self.fuzz_recursive(wl)

        fcts = self.get_modif_functions()

        print(CLEAR_LINE + COLOR_PURPLE +"\n[*] Testing with modifications\n" + COLOR_NONE)
        totposs = sum([math.factorial(i+1) for i in range(len(fcts))])
        steps = 0
        for i in range(len(fcts)):
            steps = self.mix_fcts(wl, fcts[:i], totposs=totposs, steps=steps)
