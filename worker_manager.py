from ssc_checker import getGrades

from concurrent import futures

from sqlalchemy.orm import sessionmaker, relationship

from db import User, Grade

import time

db_engine = None
tg_bot = None

def getGradesForUser(user):
    username = user.ssc_username
    password = user.ssc_password

    return getGrades(username,password)

def getGradesForUserCallback(future):
    if future.cancelled():
        print(f'Grades lookup for {future.arg.username} cancelled')
    elif future.done():
        error = future.exception()
        if error:
            print(f'Grades lookup for {future.arg.username} failed, {error}')

        elif future.result():
            grades = future.result()
            Session = sessionmaker(bind=db_engine)
            session = Session()


            for grade in grades:
                print(grade)
                course_name = grade['course_name'].split()
                subject = course_name[0]
                code = course_name[1]
                section = grade['section']
                try:
                    grade_p = int(grade['grade'])
                except ValueError:
                    continue
                #grade_p = int(grade['grade']) if grade['grade'] != ' ' else -1
                letter = grade['letter']
                session_y = grade['session']
                term = grade['term']
                program = grade['program']
                year = grade['year']
                try:
                    credits = float(grade['credits'])
                except ValueError:
                    credits = -1.0
                #credits = float(grade['credits']) if grade['credits'] != ' ' else -1.0
                average = int(grade['average'])
                standing = grade['standing']

                course = session.query(Grade).filter_by(subject=subject,code=code).first()

                if not course:
                    print(f'Record for {subject} {code} not found, adding')
                    #lmao maybe this should be passed as an object
                    course = Grade(future.arg.telegram_id, subject, code, section, grade_p, letter, session_y, term, program, year, credits, average, standing)
                    session.add(course)
                    session.commit()

                    msg = f'Grades for {subject} {code} have been released, check yours using:\n `/request {subject} {code}`'

                    tg_bot.send_message(chat_id=future.arg.telegram_id, text=msg, parse_mode="Markdown")

                else:
                    print(f'Record for {subject} {code} found, checking for updates')
                    changes = {
                            'grade':False if course.grade == grade_p else True,
                            'credits':False if course.credits == credits else True,
                            'average':False if course.average == average else True,
                            'standing':False if course.standing == standing else True
                        }
                    for key,val in changes.items():
                        if val:
                            msg = f'Update: {subject} {code} has been updated, check it using `/request {subject} {code}`'

                            course.grade = grade_p
                            course.letter = letter
                            course.credits = credits
                            course.average = average
                            course.standing = standing
                            session.commit()

                            tg_bot.send_message(chat_id=future.arg.telegram_id, text=msg, parse_mode="Markdown")
                            break
    else:
        print('future not finished')


def startWorkers(engine, bot, max_threads):
    global db_engine
    db_engine = engine
    global tg_bot
    tg_bot = bot

    executor = futures.ThreadPoolExecutor(max_workers = max_threads)

    Session = sessionmaker(bind=db_engine)
    session = Session()

    print('Starting workers')
    while True:
        users = session.query(User)

        wait_for = []

        for user in users:
            print(f'Starting worker for {user.username}')
            future = executor.submit(getGradesForUser, user)
            future.arg = user
            future.add_done_callback(getGradesForUserCallback)
            wait_for.append(future)

        for f in futures.as_completed(wait_for):
            print(f'main: result: {f.result()}')

        time.sleep(5)







