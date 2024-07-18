import os
from tqdm import tqdm
import contextlib

# helper function for string extraction
from antlr_string_extract.extract_strings import extract_strings as antlr_extract_strings


# treat all directories in dirpath as seperate projects
def extract_strings_multiple(dirpath, out_path, ignore_popular_strings = True):
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    already_done = [f.name for f in os.scandir(out_path) if f.name.endswith('.txt')]
    project_dirs = { f.path: [] for f in os.scandir(dirpath) if f.is_dir() and f.name + '.txt' not in already_done }
    if ignore_popular_strings:
        with open('./ignored_strings.txt', 'r') as f:
            ignored_strings = [i.strip() for i in f.readlines()]
    else:
        ignored_strings = []
    print(f"Extracting strings from {len(project_dirs)} repositories")

    

    for pd in tqdm(project_dirs.keys()):
        extract_strings(pd, os.path.join(out_path, pd.split('/')[-1] + '.txt'), ignored_strings=ignored_strings)

# extract strings from the github projects and store them in txt files
def extract_strings(dir_path, out_file, ignored_strings = None):
    # print(dir_path)
    if ignored_strings == None:
        with open('./ignored_strings.txt', 'r') as f:
            ignored_strings = [i.strip() for i in f.readlines()]

    ignored_dirs = ['documentation', 'drivers', 'targets', 'examples'] #['libraries', 'lib', 'libs', 'tools', 'drivers',  'external', 'targets', 'examples', 'docs', 'documentation', 'tests', 'hal', 'components']

    c_files = []
    # create list of c and c++ files
    for root, dirs, l_files in os.walk(dir_path):
        for file in l_files:
            # skip if it is a symbolic link
            if os.path.islink(os.path.join(root,file)):
                continue
            # skip if not a c or c++ source file
            if file[-2:] != '.c' and file[-4:] != '.cpp':
                continue
            # skip if in a directory that should be ignored
            if len([1 for ignored_dir in ignored_dirs if '/' + ignored_dir.upper() + '/' in root.upper() or root.upper().endswith('/' + ignored_dir.upper()) ]) > 0:
                continue

            c_files.append(os.path.join(root, file))

    # Loop over the files and extract the strings
    repo_strings = []

    for file in c_files:
        if file[-2:] == '.c':
            lang = 'c'
        elif file[-4:] == '.cpp':
            lang = 'c++'
        else:
            print(f'Unsupported file extension: {file}')
            continue
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stderr(devnull):
                file_strings = antlr_extract_strings(file, lang)
        repo_strings += [s for s in file_strings if len(s) > 5]
    
    filtered_strings = []
    for string in repo_strings:
        try:
            string = bytes(string, "utf-8").decode("unicode_escape")
        except:
            print(f"Failed decoding: {string}")
            continue
        for s in string.split('\n'):
            s = s.strip()
            if s in ignored_strings:
                continue
            if len(s) < 5 or len(s) > 200:
                continue
            if s in filtered_strings:
                continue
            filtered_strings.append(s)
    with open(out_file, 'w') as f:
        for string in filtered_strings:
            f.write(string + '\n')