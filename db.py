from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, SmallInteger, Float, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def getDatabaseUrl(settings):
    type = settings['type']
    username = settings['username']
    password = settings['password']
    host = settings['host']
    port = settings['port']
    database = settings['database']

    protocol = f'{type}'

    if username and password:
        creds = f'{username}:{password}'
    elif username:
        creds = f'{username}'
    else:
        creds = ''

    if port:
        address = f'{host}:{port}'
    else:
        address = f'{host}'

    url = f'{protocol}://{creds}@{address}/{database}'

    return url

base = declarative_base()

class User(base):
    __tablename__ = 'user'

    telegram_id = Column('telegram_id', Integer, primary_key=True)

    username = Column('username', String)

    ssc_username = Column('ssc_username', String)
    ssc_password = Column('ssc_password', String)

    def __init__(self, telegram_id, username, ssc_username, ssc_password):
        self.telegram_id  = telegram_id
        self.username = username
        self.ssc_username = ssc_username
        self.ssc_password = ssc_password

    def __repr__(self):
        return f'User with name {self.username} attached to SSC Account {self.ssc_username}'

class Grade(base):
    __tablename__ = 'grade'

    id = Column('id',Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.telegram_id'))

    subject = Column('subject', String(4))
    code = Column('code', SmallInteger)
    section = Column('section', String(3))

    grade = Column('grade', SmallInteger)
    letter = Column('letter', String(2))

    session = Column('session', String(5))
    term = Column('term', String(1))
    program = Column('program', String(4))
    year = Column('year', SmallInteger)

    credits = Column('credits', Float)
    average = Column('average', SmallInteger)

    standing = Column('standing', String)

    def __init__(self, user_id, subject, code, section, grade, letter, session, term, program, year, credits, average, standing):
        self.user_id = user_id
        self.subject = subject
        self.code = code
        self.section = section
        self.grade = grade
        self.letter = letter
        self.session = session
        self.term = term
        self.program = program
        self.year = year
        self.credits = credits
        self.average = average
        self.standing = standing

    __table_args__ = (
            UniqueConstraint('subject','code', name='_course_code_uc'),
            )

def gen_engine(url):
    engine = create_engine(url)

    base.metadata.create_all(bind=engine)

    return engine

