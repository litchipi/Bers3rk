#!/usr/bin/env python
#-*-encoding:utf-8*-

import traceback
import io
import math
import os
import sys
import json
import time
import select
import multiprocessing as mproc

COLOR_PURPLE = "\033[95m"
COLOR_GREEN = "\033[92m"
COLOR_ORANGE = "\033[93m"
COLOR_NONE = "\033[0m"
CLEAR_LINE = "\033[2K\r" + COLOR_NONE

FORBIDDEN_CHARS = ["#"]

class Berserk:
    default_params = {
            "quit_on_first_success":False,
            "save_sucessed_word":None,
            "nbsimilar":0,
            "joinchar":"",
            "extensions":[],
            "maxmix":0,
            "suffix":"",
            "prefix":"",
            "try_delay":0.0,
            "max_temp_C":None,
            "sensor_device_name":None,
            "sensor_data_name":None,
            "word_length":None,
            }

    def __init__(self, try_fct, fct_params):

        self.params = self.default_params.copy()
        self.params.update(fct_params)

        self.allow_temp_management = (
                (self.params["max_temp_C"] != None) and
                (self.params["sensor_device_name"] != None) and
                (self.params["sensor_data_name"] != None))
        self.shared_ress = mproc.Manager().dict()
        self.delay = float(self.params["try_delay"])
        self.min_delay = float(self.params["try_delay"])
        self.shared_ress["delay"] = float(self.delay)

        if (self.params["save_sucessed_word"] is not None) and not (os.path.isfile(self.params["save_sucessed_word"])):
            with open(self.params["save_sucessed_word"], "w") as fichier:
                fichier.write("")

        nbproc = mproc.cpu_count()
        self.soldiers = list()
        self.finished = False

        self.results = mproc.Manager().list()
        for n in range(nbproc):
            self.soldiers.append(Soldier(self.results, self.shared_ress, try_fct, self.params, n, nbproc))

        self.temp = 0

        self.debug = True

    def add_modif_function(self, fct, priority, group="default"):
        for s in self.soldiers:
            s.add_modif_function(fct, priority, group=group)

    def add_word_default_modif(self):
        self.add_modif_function(lambda x: x, 1, group="case")
        self.add_modif_function(lambda x: x.lower(), 5, group="case")
        self.add_modif_function(lambda x: x.upper(), 100, group="case")
        self.add_modif_function(lambda x: x.capitalize(), 75, group="case")
        def one_on_two(x, pair=False):
            res = ""
            for n, char in enumerate(x):
                if (n%2 == int(pair)):
                    res += char.upper()
                else:
                    res += char.lower()
            return res
        self.add_modif_function(lambda x: one_on_two(x, pair=False), 60, group="case")
        self.add_modif_function(lambda x: one_on_two(x, pair=True), 59, group="case")

        self.add_modif_function(lambda x: x.replace("o", "0"), 100, group="let2num")
        self.add_modif_function(lambda x: x.replace("i", "1"), 90, group="let2num")
        self.add_modif_function(lambda x: x.replace("e", "3"), 80, group="let2num")
        self.add_modif_function(lambda x: x.replace("a", "4"), 70, group="let2num")
        self.add_modif_function(lambda x: x.replace("O", "0"), 60, group="let2num")
        self.add_modif_function(lambda x: x.replace("I", "1"), 50, group="let2num")
        self.add_modif_function(lambda x: x.replace("E", "3"), 40, group="let2num")
        self.add_modif_function(lambda x: x.replace("A", "4"), 30, group="let2num")

        self.add_modif_function(lambda x: x[:3], 100, group="slice")
        self.add_modif_function(lambda x: x[:4], 100, group="slice")
        self.add_modif_function(lambda x: x[-4:], 100, group="slice")
        self.add_modif_function(lambda x: x[-5:], 100, group="slice")

    def add_stop_condition(self, f):
        for s in self.soldiers:
            s.add_stop_condition(f)

    def run(self, fname):
        self.wl = os.path.basename(fname)
        os.system("clear")
        t = time.time()
        for soldier in self.soldiers:
            soldier.fname = fname
            soldier.start()

        while any([s.is_alive() for s in self.soldiers]):
            self.display_info()
            if not self.manage_processes():
                break
        t2 = time.time()

        for soldier in self.soldiers:
            soldier.allowed = False
            soldier.join()

        self.display_results(t2-t)
        self.final_results = list(self.results)

    def status_bar(self):
        done = min([self.shared_ress["soldier" + str(n) + "_done"] for n in range(len(self.soldiers))])
#        done = min([s.done for s in self.soldiers])
        return "[{:7.4f}% done] - {}°C - {:6.4f} secs delay between each request - Wordlist: {}".format(done, self.temp, self.delay, self.wl)

    def display_results(self, finished_time):
        os.system("clear")
        print(CLEAR_LINE + COLOR_ORANGE + "Finished in " + str(finished_time) + " secs" + COLOR_NONE)
        self.display_found()

    def display_info(self):
        sys.stdout.write("\033[1;1H" + CLEAR_LINE + self.status_bar() + "\n")
        self.display_found()
        if self.debug:
            self.display_debug()

    def display_debug(self):
        index_indics=["|", "/", "-", "\\", "~", "*", "x", "o", "@", "#"]
        index = COLOR_GREEN + "[" + index_indics[int(time.time()*10)%len(index_indics)] + "]"
        for key, val in self.shared_ress.items():
            print(CLEAR_LINE + index + COLOR_PURPLE + str(key))
            print(CLEAR_LINE + index + COLOR_ORANGE +"\t-> " + str(val) + COLOR_NONE)

    def display_found(self):
        for f in set(self.results):
            sys.stdout.write(CLEAR_LINE + COLOR_PURPLE + "*** Found: \t" + COLOR_GREEN + f + COLOR_NONE + "\n")

    def manage_processes(self):
        if self.params["quit_on_first_success"] and not all([s.is_alive() for s in self.soldiers]):
            self.finished = len(self.results) > 0
            return False
         if not self.allow_temp_management:
            return True

        change = False
        sensors = json.loads(os.popen("sensors -j").read())
        try:
            self.temp = sensors[self.params["sensor_device_name"]["sensor_data_name"]]
        except IndexError:
            self.temp = 0   # Will run at 100% all the time

        if (self.params["max_temp_C"] is not None):
            pchange = float(self.temp-self.params["max_temp_C"])/100
            if (self.temp > self.params["max_temp_C"]) and self.delay == 0:
                self.delay += 0.005
            self.delay = round(max(self.min_delay, self.delay*(1+pchange)), 5)
#            self.delay = max(self.min_delay, self.delay*(1-pchange))
            self.shared_ress["delay"] = self.delay
        return True

class Soldier(mproc.Process):
    def __init__(self, results, shared_ress, try_fct, fct_params, nbsoldier, totsoldier):
        mproc.Process.__init__(self)

        self.totsoldier = totsoldier
        self.soldier_nb = nbsoldier

        self.allowed = True

        self.fname = None
        self.try_fct = try_fct
        self.params = fct_params

        self.last_try = 0
        self.shared_ress = shared_ress
        self.write_shared_ress("done", 0)

        self.modif_functions = dict()
        self.stop_conditions = list()
        self.results = results

    def thread_safe_write(self, f, data):
        while True:
            r, w, x = select.select([], [f], [])
            if f in w:
                return f.write(data)

    def tryw(self, data):
        res = self.try_fct(data, self.params)
        if res and (data not in self.results):
            self.results.append(data)
            if self.params["save_sucessed_word"] is not None:
                with open(self.params["save_sucessed_word"], "a") as fichier:
                    self.thread_safe_write(fichier, data)

            if self.params["quit_on_first_success"]:
                self.stop()
            if any([cond(self.results) for cond in self.stop_conditions]):
                self.stop()

    def stop(self):
        self.allowed = False
        sys.exit(0)

    def write_shared_ress(self, dataname, data):
        self.shared_ress["soldier" + str(self.soldier_nb) + "_" + dataname] = data

    def skip_or_treat(self, n):
        return (n%self.totsoldier) != self.soldier_nb

    def fuzz_recursive(self, wl, lcount, past_data=[], niter=0, fct=lambda x: x, called=False):
        n = 0
        wl.seek(0)
        for n, word in enumerate(wl):
            if any([el in word for el in FORBIDDEN_CHARS]):
                continue

            if not called and self.skip_or_treat(n):
                continue

            w = fct(word.replace("\n", ""))
            if self.params["word_length"] is not None:
                if len(w) != self.params["word_length"]:
                    continue

#            if not called:
#                n+=1
#                self.write_shared_ress("done", (float(n)/lcount)*100)
#            self.write_shared_ress("word", w)
            if past_data.count(w) > self.params["nbsimilar"]:
                continue

            data = self.params["joinchar"].join(past_data + [w])
            if data == "":
                continue


            time.sleep(max(0, self.shared_ress["delay"]))
 #           time.sleep(max(0, (self.delayparams["try_delay"]/1000) - (time.time()-self.last_try)))
            self.last_try = time.time()

            self.tryw(self.params["prefix"] + data + self.params["suffix"])
            for e in self.params["extensions"]:
                self.tryw(self.params["prefix"] + data + "." + e)

        recurs = ((niter+1) < self.params["maxmix"])
        if not recurs:
            return

        ndone = 0
        while ndone < lcount:
            wl.seek(0)
            wlgen = (l for l in wl)
            word = next(wlgen)
            for i in range(ndone):
                word = next(wlgen)
            ndone += 1
            w = fct(word.replace("\n", ""))
            if past_data.count(w) >= (self.params["nbsimilar"]+1):
                continue
            data = self.params["joinchar"].join(past_data + [w])
            if data == "":
                continue
            self.fuzz_recursive(wl, lcount, past_data=past_data + [w], niter=niter+1, fct=fct)

    def mix_fcts(self, data, lcount, fcts, fgroups, past_fct=lambda x: x, n=0, steps=0, totposs=0):
        if len(fgroups) == 0:
            self.write_shared_ress("done", float(steps)/totposs)
            return steps

        for n, f in enumerate(fcts[fgroups[0]]):
            cf = lambda x: past_fct(f(x))
            self.fuzz_recursive(data, lcount, fct=cf, called=True)
            steps += 1
            steps = self.mix_fcts(data, lcount, fcts, fgroups[1:], past_fct=cf, n=n+1, totposs=totposs, steps=steps)

        return steps

    def add_modif_function(self, fct, priority, group="default"):
        if group not in self.modif_functions.keys():
            self.modif_functions[group] = list()
        self.modif_functions[group].append((fct, priority))

    def get_modif_functions(self):
        return {k:[f for f, p in sorted(l, key=lambda x: x[1], reverse=True)] for k, l in self.modif_functions.items()}

    def add_stop_condition(self, condition):        #Will pass results found to the function "condition", if True will stop
        self.stop_conditions.append(condition)

    def run(self):
        try:
            self.start_bruteforce()
        except Exception:
            exc_buffer = io.StringIO()
            traceback.print_exc(file=exc_buffer)
            print("Process {} error:\n\t{}".format(self.soldier_nb, exc_buffer.getvalue()))
            sys.exit(0)

    def start_bruteforce(self):
        for enc in ["utf-8", "latin-1"]:
            try:
                with open(self.fname, "r", encoding=enc) as f:
                    lcount = sum(1 for i in f)

                with open(self.fname, "r", encoding=enc) as f:
                    self.run_on_wordlist(iter(f), lcount)
            except UnicodeDecodeError:
                continue

    def run_on_wordlist(self, wl, lcount):
        self.write_shared_ress("state", 0)
        self.fuzz_recursive(wl, lcount)

        fcts = self.get_modif_functions()
        fct_groups = list(fcts.keys())
        if len(fct_groups) < 1:
            return

        totposs = 1
        for g in fct_groups:
            totposs *= len(fcts[g])
        self.write_shared_ress("totposs", totposs)
        self.write_shared_ress("state", 1)
        steps = 0
        for n, f in enumerate(fcts[fct_groups[0]]):
            if self.skip_or_treat(n):
                steps = self.mix_fcts(wl, lcount, fcts, fct_groups[1:], totposs=totposs, steps=steps, past_fct=f)
