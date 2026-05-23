import Levenshtein
import argparse
import sys

from PlagiarismDB import PlagiarismDB

# python 1_time.py --platform Codeforces --log log.txt --archive 602776
# python 1_time.py --platform Yandex --log log-911-1.xml --archive submits-911-1
# python 1_time.py --platform Yandex --log log-911-2.xml --archive submits-911-2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Анализ решений по времени отправки')
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
    
    if args.platform == "Yandex":
        contest_id = db.yandex_parse(args.log, args.archive)
    elif args.platform == "Codeforces":
        contest_id = db.codeforces_parse(args.log, args.archive)
    else:
        print(f"Неподдерживаемая платформа: {args.platform}")
        sys.exit(1)
    
    teams = db.get_teams_by_contest(contest_id)

    for team in teams:
        team_printered = False
        team_submissions = db.get_submissions_by_team(team.id)

        problems_for_this_team = set()
        for submission in team_submissions:
            problems_for_this_team.add(submission.problem_code)
        for problem_code in problems_for_this_team:
            sub_of_problem = [s for s in team_submissions if s.problem_code == problem_code]  # Не пуст
            lev_distance = Levenshtein.distance('', sub_of_problem[0].code, weights=(1, 0, 1))
            time_differnce = sub_of_problem[0].time - 0
            # print(f"1) Пустая строка |{sub_of_problem[0].submission_code}.{sub_of_problem[0].language}: L={lev_distance}, T={time_differnce}")
            if lev_distance > 3 * time_differnce:
                # print("Подозрительное решение")
                print(f"\t{problem_code}-1) Пустая строка |{sub_of_problem[0].submission_code}.{sub_of_problem[0].language}: L={lev_distance}, T={time_differnce}")
            for i in range(0, len(sub_of_problem)-1):
                time_differnce = sub_of_problem[i+1].time - sub_of_problem[i].time
                lev_distance_1 = Levenshtein.distance(sub_of_problem[i].code, sub_of_problem[i+1].code, weights=(1, 0, 1))
                lev_distance_2 = Levenshtein.distance('', sub_of_problem[i].code, weights=(1, 0, 1))
                lev_distance = min(lev_distance_1, lev_distance_2)
                # print(f"{i+2}) {sub_of_problem[i].submission_code}{sub_of_problem[i].language} | {sub_of_problem[i+1].submission_code}.{sub_of_problem[i+1].language} L={lev_distance}, T={time_differnce}")
                if lev_distance > 3 * time_differnce:
                    # print("Подозрительное решение")
                    if not team_printered:
                        print(team.name)
                        team_printered = True
                    print(f"\t{problem_code}-{i+2}) {sub_of_problem[i].submission_code}{sub_of_problem[i].language} | {sub_of_problem[i+1].submission_code}{sub_of_problem[i+1].language} L={lev_distance}, T={time_differnce}")