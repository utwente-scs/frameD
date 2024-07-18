#!/usr/bin/env python3

from urllib.request import urlopen
import re
import json
from git import Repo
import os
from tqdm import tqdm
import shutil

from string_extraction import extract_strings_multiple


def create_library_json(file_path):
    url = 'https://raw.githubusercontent.com/iDoka/awesome-embedded-software/main/README.md'
    output = urlopen(url).read()
    file_str = output.decode('utf-8')

    pattern = r'\* \[([^]]+)\]\((https?://[^\s)]+)\) - [^\n]+'
    matches = re.findall(pattern, file_str)

    result_dict = {name: url for name, url in matches}

    # hacky fix #1
    result_dict.pop('FatFS') # no repo
    result_dict['EasyFlash'] = "https://github.com/armink/EasyFlash"
    result_dict.pop('FCB') # part of Zephyr
    result_dict['LwIP'] = "https://git.savannah.nongnu.org/git/lwip"
    result_dict['libdspl'] = "https://github.com/Dsplib/libdspl-2.0"
    result_dict['wolfSSH'] = "https://github.com/wolfSSL/wolfssh"
    result_dict.pop('c25519-and-ed25519') # not a code project   
    result_dict['Protothreads'] = "https://github.com/zserge/pt"
    result_dict.pop('TouchGFX') # has no git repo
    result_dict['LovyanGFX'] = "https://github.com/lovyan03/LovyanGFX"

    # hacky way to remove all operating systems and other non-related projects
    skipping = False
    starting = ['citrus', 'embedded-driver', 'SDCC']
    ending = ['Quite Ok RTOS', 'CanBoot', 'incbin']
    names = list(result_dict.keys())
    for name in names:
        if skipping:
            result_dict.pop(name)
            if name in ending:
                skipping = False
        else:
            if name in starting:
                skipping = True
                result_dict.pop(name)

    with open(file_path, 'w') as json_file:
        json.dump(result_dict, json_file)


# locally clone the found github repos
def clone_repos(dir_path, lib_json, force_checkout_main = True):
    repos = {}
    with open(lib_json, 'r') as f:
        repos = json.load(f)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    already_cloned = [f.name for f in os.scandir(dir_path)]
    for clone in already_cloned:
        if clone not in repos:
            print(f"Removing clone of {clone}, as is not in {lib_json} anymore")
            shutil.rmtree(os.path.join(dir_path, clone))
    print(f"Cloning {len(repos)} repos (repos that are already present locally are skipped)")
    for k,v in tqdm(repos.items()):
        if k in already_cloned:
            if force_checkout_main:
                # make sure we are in main or master branch
                repo = Repo(os.path.join(dir_path, k))
                main_branch_name = re.findall(r"\s*HEAD branch:\s*(.*)", repo.git.remote("show", "origin"))[0]
                repo.git.checkout(main_branch_name, force=True)
            continue
        try:
            Repo.clone_from(v + '.git', os.path.join(dir_path, k))
        except:
            print(f"Could not clone {k}, please correct manually in the json file!")



if __name__ == "__main__":
    dir_path = './library_clones'
    lib_json = 'github_libraries.json'
    create_library_json(lib_json)
    clone_repos(dir_path, lib_json, force_checkout_main=False)
    extract_strings_multiple(dir_path, 'extracted_strings_libraries', ignore_popular_strings=False)