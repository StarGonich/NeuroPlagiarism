import Levenshtein
import argparse
import sys
import re
from collections import defaultdict

from antlr4 import *
from PlagiarismDB import PlagiarismDB

from Lexers.JavaLexer import JavaLexer
from Lexers.PythonLexer import PythonLexer
from Lexers.CPP14Lexer import CPP14Lexer
from Lexers.CSharpLexer import CSharpLexer

# python main.py --platform Codeforces --log log.txt --archive 602776
# python main.py --platform Yandex --log log-911-1.xml --archive submits-911-1
# python main.py --platform Yandex --log log-911-2.xml --archive submits-911-2

def is_python(language) -> bool:
    return True if language in ('.py', '.py3', '.pypy3', '.pypy3-64', '.pypy2') else False

def is_cpp(language) -> bool:
    return True if language in ('.cpp') else False

def is_java(language) -> bool:
    return True if language in ('.java') else False

def is_csharp(language) -> bool:
    return True if language in ('.cs') else False

def is_pascal(language) -> bool:
    return True if language in ('.pas') else False


def python_extract_comments(submission) -> list:
    code = submission.code
    input_stream = InputStream(code)
    lexer = PythonLexer(input_stream)
    stream = CommonTokenStream(lexer)
    stream.fill()

    comments = []
    for token in stream.tokens:
        token_type = lexer.symbolicNames[token.type]
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

    comments = []
    for token in stream.tokens:
        token_type = lexer.symbolicNames[token.type]
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

    comments = []
    for token in stream.tokens:
        token_type = lexer.symbolicNames[token.type]
        if token_type == 'LINECOMMENT' and bool(re.search('[а-яА-ЯёЁ]', token.text)):
            comments.append(token.text)
        elif token_type == 'COMMENT' and bool(re.search('[а-яА-ЯёЁ]', token.text)):
            comments.append(token.text)
    return comments

def csharp_extract_comments(submission) -> list:
    code = submission.code
    input_stream = InputStream(code)
    lexer = CSharpLexer(input_stream)
    stream = CommonTokenStream(lexer)
    stream.fill()

    comments = []
    for token in stream.tokens:
        token_type = lexer.symbolicNames[token.type]
        if token_type == 'Comment' and bool(re.search('[а-яА-ЯёЁ]', token.text)):
            comments.append(token.text)
    return comments

def pascal_extract_comments(submission) -> list:
    code = submission.code
    comments = []
    
    line_pattern = r'//[^\n]*'
    for match in re.finditer(line_pattern, code):
        comment = match.group(0)
        if re.search('[а-яА-ЯёЁ]', comment):
            comments.append(comment)
    
    brace_pattern = r'\{[^{}]*\}'
    for match in re.finditer(brace_pattern, code):
        comment = match.group(0)
        if re.search('[а-яА-ЯёЁ]', comment):
            comments.append(comment)
    
    paren_pattern = r'\(\*[^*]*\*\)'
    for match in re.finditer(paren_pattern, code):
        comment = match.group(0)
        if re.search('[а-яА-ЯёЁ]', comment):
            comments.append(comment)
    
    return comments


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Комплексный анализ решений')
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

    time_results = {}
    lang_results = {}
    comment_results = {}

    for team in teams:
        team_submissions = db.get_submissions_by_team(team.id)
        
        problems_for_this_team = sorted(set(submission.problem_code for submission in team_submissions))

        # ПРИЗНАК 1
        time_lines = []
        for problem_code in problems_for_this_team:
            sub_of_problem = [s for s in team_submissions if s.problem_code == problem_code]
            lev_distance = Levenshtein.distance('', sub_of_problem[0].code, weights=(1, 0, 1))
            time_difference = sub_of_problem[0].time - 0
            if lev_distance > 3 * time_difference:
                time_lines.append(f"\t\t{problem_code}-1) Пустая строка | {sub_of_problem[0].submission_code}{sub_of_problem[0].language}: L={lev_distance}, T={time_difference}")
            for i in range(0, len(sub_of_problem)-1):
                time_difference = sub_of_problem[i+1].time - sub_of_problem[i].time
                lev_distance_1 = Levenshtein.distance(sub_of_problem[i].code, sub_of_problem[i+1].code, weights=(1, 0, 1))
                lev_distance_2 = Levenshtein.distance('', sub_of_problem[i].code, weights=(1, 0, 1))
                lev_distance = min(lev_distance_1, lev_distance_2)
                if lev_distance > 3 * time_difference:
                    time_lines.append(f"\t\t{problem_code}-{i+2}) {sub_of_problem[i].submission_code}{sub_of_problem[i].language} | {sub_of_problem[i+1].submission_code}{sub_of_problem[i+1].language} L={lev_distance}, T={time_difference}")
        
        if time_lines:
            time_results[team.id] = [team.name] + time_lines
        
        # ПРИЗНАК 2
        lang_lines = []
        for problem_code in problems_for_this_team:
            sub_of_problem = [s for s in team_submissions if s.problem_code == problem_code]
            for j in range(len(sub_of_problem)):
                if sub_of_problem[j].verdict != "CE":
                    lang = sub_of_problem[j].language
                    langs = set()
                    langs.add(lang)
                    lang_examples = {lang: sub_of_problem[j].submission_code}
                    break
            for i in range(j+1, len(sub_of_problem)):
                lang2 = sub_of_problem[i].language
                if lang2 not in langs and sub_of_problem[i].verdict != "CE":
                    langs.add(lang2)
                    lang_examples[lang2] = sub_of_problem[i].submission_code
            if len(langs) > 1:
                lang_lines.append(f"\t\tЗадача-{problem_code}. Используемые языки: {langs}")
                if args.platform == "Codeforces":
                    examples = ", ".join([f"{code}{lang}" for lang, code in lang_examples.items()])
                    lang_lines.append(f"\t\tПримеры: {examples}")
        
        if lang_lines:
            lang_results[team.id] = [team.name] + lang_lines
        
        # ПРИЗНАК 3
        team_lens = set()
        comment_lines = []
        for sub in team_submissions:
            if is_python(sub.language):
                try:
                    are_rus = python_extract_comments(sub)
                except Exception as e:
                    print(f"{team.name}: ошибка при обработке Python файла {sub.submission_code}{sub.language}: {e}")
                    continue
            elif is_cpp(sub.language):
                try:
                    are_rus = cpp_extract_comments(sub)
                except Exception as e:
                    print(f"{team.name}: ошибка при обработке C++ файла {sub.submission_code}{sub.language}: {e}")
                    continue
            elif is_java(sub.language):
                try:
                    are_rus = java_extract_comments(sub)
                except Exception as e:
                    print(f"{team.name}: ошибка при обработке Java файла {sub.submission_code}{sub.language}: {e}")
                    continue
            elif is_csharp(sub.language):
                try:
                    are_rus = csharp_extract_comments(sub)
                except Exception as e:
                    print(f"{team.name}: ошибка при обработке C# файла {sub.submission_code}{sub.language}: {e}")
                    continue
            elif is_pascal(sub.language):
                try:
                    are_rus = pascal_extract_comments(sub)
                except Exception as e:
                    print(f"{team.name}: ошибка при обработке Pascal файла {sub.submission_code}{sub.language}: {e}")
                    continue
            else:
                continue

            if are_rus:
                sum_len = sum(len(comment) for comment in are_rus)
                if sum_len not in team_lens:
                    comment_lines.append(f"\t\t{sub.submission_code}{sub.language} Суммарная длина: {sum_len}")
                    team_lens.add(sum_len)
        
        if comment_lines:
            comment_results[team.id] = [team.name] + comment_lines

    team_flags = {}
    all_team_ids = set(time_results.keys()) | set(lang_results.keys()) | set(comment_results.keys())
    
    for team_id in all_team_ids:
        flags = []
        if team_id in time_results:
            flags.append((1, "L - расстояние Левенштейна, T - время", time_results[team_id][1:]))
        if team_id in lang_results:
            flags.append((2, "Разные языки программирования", lang_results[team_id][1:]))
        if team_id in comment_results:
            flags.append((3, "Русскоязычные комментарии", comment_results[team_id][1:]))
        team_flags[team_id] = flags
    
    results_by_flags = defaultdict(list)
    for team_id, flags in team_flags.items():
        if team_id in time_results:
            team_name = time_results[team_id][0]
        elif team_id in lang_results:
            team_name = lang_results[team_id][0]
        elif team_id in comment_results:
            team_name = comment_results[team_id][0]
        results_by_flags[len(flags)].append((team_id, team_name))
    
    for flags_count in range(3, 0, -1):
        if results_by_flags[flags_count]:
            for team_id, team_name in sorted(results_by_flags[flags_count], key=lambda x: x[1]):
                print(f"\n{team_name}")
                for flag_num, flag_name, lines in team_flags[team_id]:
                    print(f"\t[Признак {flag_num}] {flag_name}")
                    for line in lines:
                        print(line)