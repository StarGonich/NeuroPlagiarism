import argparse
import sys

from PlagiarismDB import PlagiarismDB

# python 2_difflang.py --platform Codeforces --log log.txt --archive 602776
# python 2_difflang.py --platform Yandex --log log-911-1.xml --archive submits-911-1
# python 2_difflang.py --platform Yandex --log log-911-2.xml --archive submits-911-2

def get_language(language) -> str:
    if language in ('.py', '.py3', '.pypy3', '.pypy3-64', '.pypy2'):
        return 'python'
    else:
        return language

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Анализ разных языков программирования в решениях')
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
        for submission in team_submissions:
            problems_for_this_team.add(submission.problem_code)
        for problem_code in problems_for_this_team:
            sub_of_problem = [s for s in team_submissions if s.problem_code == problem_code]
            for j in range(len(sub_of_problem)):
                if sub_of_problem[j].verdict != "CE":
                    lang = get_language(sub_of_problem[0].language)
                    langs = set()
                    langs.add(lang)
                    break
            for i in range(j+1, len(sub_of_problem)):
                lang2 = get_language(sub_of_problem[i].language)
                if lang != lang2 and sub_of_problem[i].verdict != "CE":
                    langs.add(lang2)
                    
                    # print(f"\t{number}:{lang} | {sub_of_problem[i].submission_code}:{lang2}")
            if len(langs) > 1:
                if not team_printered:
                    print(team.name)
                    team_printered = True
                print(f"\tЗадача-{problem_code}. Используемые языки: {langs}")