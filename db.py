from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, SmallInteger, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, MINYEAR

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

    is_checking = Column('is_checking', Boolean)

    statuses = relationship("Status", cascade="all,delete", backref="user")
    grades = relationship("Grade", cascade="all,delete", backref="user")

    def __init__(self, telegram_id, username, ssc_username, ssc_password):
        self.telegram_id  = telegram_id
        self.username = username
        self.ssc_username = ssc_username
        self.ssc_password = ssc_password
        self.is_checking = True

    def __repr__(self):
        return f'User with name {self.username} attached to SSC Account {self.ssc_username}'

class Status(base):
    __tablename__ = 'status'

    id = Column('id', Integer, primary_key=True)
    user_id = Column('user_id',Integer, ForeignKey('user.telegram_id'))
    success = Column('success', Boolean)
    time = Column('time', DateTime)
    msg = Column('msg', String(100))

    def __init__(self, id):
        self.user_id = id
        self.success = False
        self.time = datetime.fromtimestamp(0)
        msg = ""

    def __repr__(self):
        return f'UserID {self.id}\'s last check at {self.time}was {"successful" if self.success else "not successful"}'

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

