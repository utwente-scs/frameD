#!/usr/bin/env python3

from github import Github
from tqdm import tqdm
from git import Repo
import os
import re

from string_extraction import extract_strings, extract_strings_multiple
from configuration import GITHUB_API_TOKEN

# Helper function for the github API
def _search_github(auth: Github, keyword: str) -> list:
    print(f'Searching GitHub for: {keyword}')

    # set-up query
    query = keyword  + ' in:description language:C++ language:C'
    results = auth.search_repositories(query, 'stars', 'desc')

    results_list = []
    for repo in results[:100]:
        results_list.append([repo.full_name, repo.url, repo.stargazers_count, repo.description])
    return results_list


# Uses the github API to search for embedded operating system
def find_github_repos(search_list):
    token = GITHUB_API_TOKEN
    auth = Github(token)
    full_filename = 'github_repos.txt'
    with open(full_filename, 'w') as f_out:
        for key in search_list:
            # f_out.write(f"Keyword: {key}\n")
            for res in _search_github(auth, key):
                f_out.write(str(res[0].replace('/', '---')) + ' ' + str(res[1]) + ' ' + str(res[2]) + ' ' + str(res[3]) + '\n' )

# locally clone the found github repos
def clone_repos(force_checkout_main = False):
    repos = {}
    with open('./github_repos.txt', 'r') as f:
        for line in f:
            repos[line.split(' ')[0]] = line.split(' ')[1].replace('api.', '').replace('repos/', '') + '.git'
    already_cloned = [f.name for f in os.scandir('./clones/')]
    print(f"Cloning {len(repos)} repos (repos that are already present locally are skipped)")
    for k,v in tqdm(repos.items()):
        if k in already_cloned:
            if force_checkout_main:
                # make sure we are in main or master branch
                repo = Repo('./clones/' + k)
                main_branch_name = re.findall(r"\s*HEAD branch:\s*(.*)", repo.git.remote("show", "origin"))[0]
                # if repo.active_branch.name != main_branch_name:
                repo.git.checkout(main_branch_name, force=True)
            continue
        Repo.clone_from(v, './clones/' + k)



if __name__ == '__main__':
    search_list = ['embedded operating system',
    'operating system microcontrollers',
    'internet of things operating system',
    'OS IoT',
    'OS internet of things',
    'RTOS'
    ]
    find_github_repos(search_list)
    clone_dir = './clones'
    if not os.path.exists(clone_dir):
        os.makedirs(clone_dir)
    clone_repos(force_checkout_main = False)

    string_db_dir = './extracted_strings/'
    if not os.path.exists(string_db_dir):
        os.makedirs(string_db_dir)
    extract_strings_multiple(clone_dir,string_db_dir,ignore_popular_strings=False)
    print('All done!')