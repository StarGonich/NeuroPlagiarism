import re
import argparse
import sys

from PlagiarismDB import PlagiarismDB

from antlr4 import *

from Lexers.JavaLexer import JavaLexer
from Lexers.PythonLexer import PythonLexer
from Lexers.CPP14Lexer import CPP14Lexer

# python 3_ruscomments.py --platform Codeforces --log log.txt --archive 602776
# python 3_ruscomments.py --platform Yandex --log log-911-1.xml --archive submits-911-1
# python 3_ruscomments.py --platform Yandex --log log-911-2.xml --archive submits-911-2

def is_python(language) -> bool:
    return True if language in ('.py', '.py3', '.pypy3', '.pypy3-64', '.pypy2') else False

def is_cpp(language) -> bool:
    return True if language in ('.cpp') else False

def is_java(language) -> bool:
    return True if language in ('.java') else False

def python_extract_comments(submission) -> list:
    code = submission.code

    input_stream = InputStream(code)
    lexer = PythonLexer(input_stream)
    stream = CommonTokenStream(lexer)
    stream.fill()

    lexertokens = []
    comments = []
    for token in stream.tokens:
        token_type = lexer.symbolicNames[token.type]
        lexertokens.append(token_type)
        if token_type == 'COMMENT' and bool(re.search('[а-яА-ЯёЁ]', token.text)):
            comments.append(token.text)
        elif token_type == 'STRING' and (
        token.text.startswith('"""') or token.text.startswith("'''")
        ) and bool(re.search('[а-яА-ЯёЁ]', token.text)):
            comments.append(token.text)
    return comments


def cpp_extract_comments(submission) -> list:
    code = submission.code

    input_stream = InputStream(code)
    lexer = CPP14Lexer(input_stream)
    stream = CommonTokenStream(lexer)
    stream.fill()

    lexertokens = []
    comments = []
    for token in stream.tokens:
        token_type = lexer.symbolicNames[token.type]
        lexertokens.append(token_type)
        if token_type == 'LineComment' and bool(re.search('[а-яА-ЯёЁ]', token.text)):
            comments.append(token.text)
        elif token_type == 'BlockComment' and bool(re.search('[а-яА-ЯёЁ]', token.text)):
            comments.append(token.text)
    return comments


def java_extract_comments(submission) -> list:
    code = submission.code

    input_stream = InputStream(code)
    lexer = JavaLexer(input_stream)
    
    stream = CommonTokenStream(lexer)
    stream.fill()

    lexertokens = []
    comments = []
    for token in stream.tokens:
        token_type = lexer.symbolicNames[token.type]
        lexertokens.append(token_type)
        if token_type == 'LINECOMMENT' and bool(re.search('[а-яА-ЯёЁ]', token.text)):
            comments.append(token.text)
        elif token_type == 'COMMENT' and bool(re.search('[а-яА-ЯёЁ]', token.text)):
            comments.append(token.text)
    return comments

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Поиск русских комментариев в коде')
    parser.add_argument('--platform', '-p', type=str, required=True, choices=['Yandex', 'Codeforces'],
                        help='Платформа: Yandex или Codeforces')
    parser.add_argument('--log', '-l', type=str, required=True,
                        help='Путь к лог-файлу')
    parser.add_argument('--archive', '-a', type=str, required=True,
                        help='Путь к архиву с решениями')
    parser.add_argument('--db', '-d', type=str, default='plagiarism.db',
                        help='Путь к файлу базы данных (по умолчанию: plagiarism.db)')
    
    args = parser.parse_args()
    
    db = PlagiarismDB(args.db)
    db.connect_db()
    
    if args.platform == "Yandex":
        contest_id = db.yandex_parse(args.log, args.archive)
    elif args.platform == "Codeforces":
        contest_id = db.codeforces_parse(args.log, args.archive)
    else:
        print(f"Неподдерживаемая платформа: {args.platform}")
        sys.exit(1)
    
    teams = db.get_teams_by_contest(contest_id)
    problems = db.get_problems_by_contest(contest_id)

    for team in teams:
        team_printered = False
        team_submissions = db.get_submissions_by_team(team.id)

        problems_for_this_team = set()
        results = []
        for sub in team_submissions:
            if is_python(sub.language):
                are_rus = python_extract_comments(sub)
            elif is_cpp(sub.language):
                are_rus = cpp_extract_comments(sub)
            elif is_java(sub.language):
                are_rus = java_extract_comments(sub)
            else:
                continue  # иной язык

            if are_rus:
                if not team_printered:
                    print(team.name)
                    team_printered = True
                sum_len = sum(len(comment) for comment in are_rus)
                print(f"\t{sub.submission_code}{sub.language} Суммарная длина: {sum_len}")