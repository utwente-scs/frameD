from antlr4 import *
from antlr_string_extract.CPP14Lexer import CPP14Lexer
from antlr_string_extract.CLexer import CLexer


def extract_strings(file_path, file_type):
    code =  open(file_path, 'r', encoding='utf-8', errors='backslashreplace').read()
    codeStream = InputStream(code)
    if file_type == 'c':
        lexer = CLexer(codeStream)
        string_literal_id = 113
    elif file_type == 'c++':
        lexer = CPP14Lexer(codeStream)
        string_literal_id = 4

    tokens = lexer.getAllTokens()
    
    strings = []
    for t in tokens:
        if t.type == string_literal_id:
            strings.append(t.text[1:-1])
    return strings
