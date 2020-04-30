#!/usr/bin/env python3
#-*-encoding:utf-8*-

import traceback
import os
import requests
import argparse
import sys
from bers3rk import Berserk

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def try_request(url, params):
    try:
        return (requests.get(url).status_code != 404)
    except requests.exceptions.ConnectionError:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wordlist", "-w", help="path to the wordlist file to use as fuzzing base")
    parser.add_argument("--url", "-u", help="url to fuzz")
    parser.add_argument("--maxmix", "-m", help="maximum number of element from wordlist to mix for a try", default=2, type=int)
    parser.add_argument("--nbsimilar", "-n", help="maximum similar words to use (ex: aaa -> 3 similar)", default=0, type=int)
    parser.add_argument("--joinchar", "-j", help="character used to join words of the wordlist before try", default="", type=str)
    parser.add_argument("--outputfile", "-o", help="File where to write every existing url found", default="", type=str)
    parser.add_argument("--extensions", "-e", help="Try with extensions (ex: py,html,php,js)", default="", type=str)
    parser.add_argument("--suffix", "-s", help="Add a suffix to the url to test", default="/", type=str)
    parser.add_argument("--modification", "-d", help="Add modification functions to the simple wordlist try", action="store_true")
    parser.add_argument("--delay", "-t", help="Time to wait between each try, in mili-seconds", default=0, type=int)
    args = parser.parse_args()

    if not args.wordlist or not os.path.isfile(args.wordlist):
        print("[!] Error: Can't fuzz without wordlist")
        parser.print_help()
        sys.exit(0)

    params = dict()
    if args.outputfile != "":
        with open(os.path.abspath(args.outputfile), "w") as of:
            of.write("")
        params["save_sucessed_word"] = os.path.abspath(args.outputfile)

    params["nbsimilar"] = args.nbsimilar
    params["joinchar"] = args.joinchar
    params["extensions"] = [el for el in args.extensions.split(",") if el != ""]
    params["maxmix"] = args.maxmix
    params["suffix"] = args.suffix
    params["prefix"] = args.url
    params["try_delay_ms"] = args.delay
    brute = Berserk(try_request, params)
    if args.modification:
        brute.add_word_default_modif()
    brute.run(args.wordlist)

if __name__ == "__main__":
    try:
        main()
    except:
        print("\n\n")
        traceback.print_exc()
        sys.exit(0)
