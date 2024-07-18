#!/usr/bin/env python3

import subprocess
import os
from tqdm import tqdm
import re
from git import Repo
import sys

from string_extraction import extract_strings

def compare_strings(bin_path, strings_dir, ignored_strings:dict=None, type_of_matching='repo', nr_of_options=20, verbose=True, rank_on_scores = True):
    # load repo stars
    repo_info = {}
    with open('github_repos.txt', 'r') as f:
        for l in f:
            repo_info[l.split(' ')[0]] = {'stars': int(l.split(' ')[2]), 'descr': ' '.join(l.split(' ')[3:])[:-1]}
    
    # extract strings from blob
    bin_strings = subprocess.run(['strings', '-n7', bin_path], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')
    final_bin_strings = []
    for string in bin_strings:
        string = string.strip()
        if len(string) < 7 or string in final_bin_strings:
            continue
        if ignored_strings and string in ignored_strings:
            continue
        final_bin_strings.append(string)

    # read repo strings from txt files
    repo_strings = { f.path: [] for f in os.scandir(strings_dir) if f.path.endswith('.txt') }
    for repo_string_file in repo_strings.keys():
        with open(repo_string_file) as f:
            repo_strings[repo_string_file] = f.read().splitlines()

    # calculate string popularity score over all strings.
    # has been replaced by looking at popularity of matching string only
    # still used for optimization
    string_popularity_old = {}
    for p in repo_strings.values():
        for repo_string in p:
            if repo_string in string_popularity_old.keys():
                string_popularity_old[repo_string] += 1
            else:
                string_popularity_old[repo_string] = 1


    # blob string fingerprint matching
    if type_of_matching=='repo':
        matches_all = {k: {'strings': [], 'score':0, 'group_id':-1} for k in repo_strings.keys()}
    elif type_of_matching == 'tag':
        matches_all = {k: {'strings': [], 'score':0, 'repo_dir': os.path.join("clones", k.split('/')[1])} for k in repo_strings.keys()}
    if verbose:
        print("comparing strings to known OS strings")
        final_bin_strings = tqdm(final_bin_strings)
    for string in final_bin_strings:
        if string not in string_popularity_old:
            continue
        for p in repo_strings.keys():
            if string in repo_strings[p]:
                matches_all[p]['strings'].append(string)
                matches_all[p]['score'] += 1


    if type_of_matching == 'repo':
        if verbose:
            print("These are the best matching repositories:")
        ordered_matches = dict(sorted(matches_all.items(), key=lambda x:x[1]['score'], reverse=True)[:nr_of_options])
    elif type_of_matching == 'tag':
        if verbose:
            print("These are the best matching tags (oldest first):")
        max_score = max([x['score'] for x in matches_all.values()])
        ordered_matches = {k:v for k,v in matches_all.items() if v['score'] == max_score}
        ordered_matches = dict(sorted(ordered_matches.items(), key=lambda t: Repo(t[1]["repo_dir"]).tags[t[0].split('/')[-1][:-4].replace('---','/')].commit.committed_datetime, reverse=True))
        ordered_matches = {k.split('/')[-1][:-4]:v for k,v in ordered_matches.items()}

    # group matches
    if type_of_matching == 'repo':
        group_id_to_strings = {}
        group_id_to_matches = {}
        group_count = 0
        group_threshold = 0.8
        for repo_txt, current_match in ordered_matches.items():
            added_to_group = False
            if len(current_match['strings']) == 0:
                continue
            for group_id, group_strings in group_id_to_strings.items():
                if len(current_match['strings'])/len(group_strings) < 0.7:
                    continue
                string_overlap = 0
                for match_string in current_match['strings']:
                    if match_string in group_strings:
                        string_overlap += 1
                if string_overlap/len(current_match['strings']) >= group_threshold:
                    current_match['group_id'] = group_id
                    group_id_to_matches[group_id][repo_txt] = current_match
                    added_to_group = True
            if not added_to_group:
                group_id_to_strings[group_count] = current_match['strings']
                group_id_to_matches[group_count] = {repo_txt: current_match}
                current_match['group_id'] = group_count
                group_count += 1
        
        # sort matches within groups based on stars
        for group_id, matches in group_id_to_matches.items():
            sorted_matches = dict(sorted(matches.items(), key=lambda x:repo_info[x[0].split('/')[-1][:-4]]['stars'], reverse=True))
            group_id_to_matches[group_id] = sorted_matches

    # calculate score of groups based on string popularity
        string_popularity = {}
        for group_strings in group_id_to_strings.values():
            for string in group_strings:
                if string in string_popularity:
                    if rank_on_scores:
                        string_popularity[string] += 1
                else:
                    string_popularity[string] = 1
        
        group_id_to_score = {}
        for group_id, group_strings in group_id_to_strings.items():
            score = 0
            for string in group_strings:
                score += 1/string_popularity[string]
            group_id_to_score[group_id] = score

        groups_order = dict(sorted(group_id_to_score.items(), key=lambda x:x[1], reverse=True))
        new_group_id_to_matches = {new_id: group_id_to_matches[old_id] for new_id, old_id in enumerate(groups_order)}
        group_id_to_matches = new_group_id_to_matches
        new_group_id_to_score = {new_id: group_id_to_score[old_id] for new_id, old_id in enumerate(groups_order)}
        group_id_to_score = new_group_id_to_score
        new_group_id_to_strings = {new_id: group_id_to_strings[old_id] for new_id, old_id in enumerate(groups_order)}
        group_id_to_strings = new_group_id_to_strings
        
        # update match scores
        for match in matches_all.values():
            score = 0
            for s in match['strings']:
                if s in string_popularity:
                    score += 1/string_popularity[s]
                else:
                    score += 1
                match['score'] = score

    # print as groups
        choice_to_repo = {}
        i = 0
        for group_id, matches in group_id_to_matches.items():
            if verbose:
                print(f"\nGroup {group_id}")
                print("Group score: {:.2f} ({:d} strings matched)".format(group_id_to_score[group_id], len(group_id_to_strings[group_id])))
                print(f"Strings matched in this group: {group_id_to_strings[group_id]}\n")
            for repo_txt, match_info in matches.items():
                repo_name = repo_txt.split('/')[-1][:-4]
                choice_to_repo[i] = repo_name
                repo = Repo(os.path.join('./clones', repo_name))
                if repo_name in repo_info:
                    stars = repo_info[repo_name]['stars']
                    description = repo_info[repo_name]['descr']
                else:
                    stars = '?'
                if verbose:
                    print(f"[{i}] {repo_txt} - {len(match_info['strings'])} string matches - {stars} stars - nr of releases: {len(repo.tags)}") # - matching strings: {strings}")
                i += 1
        return choice_to_repo, matches_all


def load_library_strings(library_strings_path):
    library_strings = {}
    for file_name in os.listdir(library_strings_path):
        if file_name.endswith('.txt'):
            with open(os.path.join(library_strings_path, file_name)) as f:
                library_strings[file_name[:-4]] = f.read().splitlines()
    combined_lib_strings = {}
    for lib_name, lib_strings in library_strings.items():
        for lib_string in lib_strings:
            combined_lib_strings[lib_string] = True
    return combined_lib_strings

# Analyze one sample
def manual_single_blob(blob_path):
    load_library_strings('./extracted_strings_libraries')
    strings_dir = './extracted_strings'
    matches, _ = compare_strings(blob_path, strings_dir)

if __name__ == '__main__':
    manual_single_blob(sys.argv[1])
