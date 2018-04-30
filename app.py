from configparser import ConfigParser

from concurrent import futures
from worker_manager import startWorkers

from ssc_config import GenerateConfig

from db import getDatabaseUrl, gen_engine
from db import User, Grade
from sqlalchemy.orm import sessionmaker, relationship

import telegram
import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import imgkit
from pytablewriter import HtmlTableWriter
import pytablewriter as ptw
from six import StringIO

config = ConfigParser()

print(config)

if not config.read('config.ini'):
    print('Config file not found, generating')
    GenerateConfig()
    config.read('config.ini')

for key in config['db']:
    print(key,config['db'][key])


dbsettings = dict(config.items('db'))
token = config['telegram']['token']

url = getDatabaseUrl(dbsettings)

engine = gen_engine(url)
Session = sessionmaker(bind=engine)

bot = telegram.Bot(token=token)

print(bot.get_me())

updater = Updater(token=token)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

def start(bot, update):
    info_msg = """Welcome to UBC SSC Bot!
Please register using the command:
```
/register [ssc_email] [ssc_password]
```

*WARNING: Your account information will be stored in plain text, use this bot at your own risk*"""

    bot.send_message(chat_id=update.message.chat_id, text=info_msg, parse_mode="Markdown")


def register(bot, update, args):
    args_msg = """Error, please register using the command:
```
/register [ssc_email] [ssc_password]
```

*WARNING: Your account information will be stored in plain text, use this bot at your own risk*"""

    exists_msg = """Error, account already exists.

To update your account information please use the command:
```
/update [ssc_email] [ssc_password]
```

*WARNING: Your account information will be stored in plain text, use this bot at your own risk*"""

    success_msg = "Registered successfully!"

    if len(args) != 2:
        bot.send_message(chat_id=update.message.chat_id, text=args_msg, parse_mode="Markdown")
        return

    telegram_id = update['message']['chat']['id']
    username = update['message']['chat']['username']

    ssc_username = args[0]
    ssc_password = args[1]

    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if user:
        bot.send_message(chat_id=update.message.chat_id, text=exists_msg, parse_mode="Markdown")
        session.close()
        return

    user = User(telegram_id, username, ssc_username, ssc_password)
    session.add(user)
    session.commit()
    session.close()

    bot.send_message(chat_id=update.message.chat_id, text=success_msg, parse_mode="Markdown")
    return


def update(bot, update, args):
    args_msg = """Error, please update using the command:
```
/update [ssc_email] [ssc_password]
```

*WARNING: Your account information will be stored in plain text, use this bot at your own risk*"""

    not_exists_msg = """Error, account not found.

To register your account information please use the command:
```
/register [ssc_email] [ssc_password]
```

*WARNING: Your account information will be stored in plain text, use this bot at your own risk*"""

    success_msg = """Updated successfully!

*Please delete your last message*"""

    if len(args) != 2:
        bot.send_message(chat_id=update.message.chat_id, text=args_msg, parse_mode="Markdown")
        return

    telegram_id = update['message']['chat']['id']
    username = update['message']['chat']['username']

    ssc_username = args[0]
    ssc_password = args[1]

    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        bot.send_message(chat_id=update.message.chat_id, text=not_exists_msg, parse_mode="Markdown")
        session.close()
        return

    user.username = username
    user.ssc_username = ssc_username
    user.ssc_password = ssc_password

    session.commit()
    session.close()

    bot.send_message(chat_id=update.message.chat_id, text=success_msg, parse_mode="Markdown")
    return


def unregister(bot, update):
    not_exists_msg = """Error, account not found.

To register your account information please use the command:
```
/register [ssc_email] [ssc_password]
```

*WARNING: Your account information will be stored in plain text, use this bot at your own risk*"""

    success_msg = "Deleted account!"

    telegram_id = update['message']['chat']['id']

    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        bot.send_message(chat_id=update.message.chat_id, text=not_exists_msg, parse_mode="Markdown")
        session.close()
        return

    session.delete(user)
    session.commit()
    session.close()

    bot.send_message(chat_id=telegram_id, text=success_msg, parse_mode="Markdown")
    return

def request(bot,update,args):
    telegram_id = update['message']['chat']['id']
    session = Session()
    if len(args) == 2:
        grades = session.query(Grade).filter_by(user_id=telegram_id,subject=args[0].upper(), code=args[1])
    elif len(args) == 1:
        if len(args[0]) > 4:
            # Attempt to parse course code without space
            subject = args[0][0:4].upper()
            code = args[0][4:]
            print(subject)
            print(code)
            grades = session.query(Grade).filter_by(user_id=telegram_id,subject=subject, code=code)
        else:
            grades = session.query(Grade).filter_by(user_id=telegram_id,subject=args[0].upper())
    else:
        grades = session.query(Grade).filter_by(user_id=telegram_id)

    session.close()

    if grades.count() > 1:
        writer = HtmlTableWriter()
        writer.stream = StringIO()
        writer.table_name = "Grades"
        writer.header_list = ['Subject', 'Code', 'Section', 'Grade', 'Letter', 'Session', 'Term', 'Program', 'Year', 'Credits', 'Average', 'Standing']

        writer.value_matrix = [[g.subject, g.code, g.section, g.grade, g.letter, g.session, g.term, g.program, g.year, g.credits, g.average, g.standing] for g in grades]

        writer.write_table()

        table = writer.stream.getvalue()
        print(table)
        imgkit.from_string(table,f'images/{telegram_id}.png', css='table.css')

        #bot.send_message(chat_id=telegram_id, text=table, parse_mode="HTML")
        bot.send_photo(chat_id=telegram_id, photo=open(f'images/{telegram_id}.png', 'rb'))
        return
    elif grades.count() == 1:
        g = grades[0]
        msg =f'*Course:*\t{g.subject} {g.code}\n*Section:* \t {g.section}\n*Grade:* \t {g.grade} ({g.letter})\n*Session/Term:* \t {g.session}/{g.term}\n*Program:* \t {g.program}\n *Year:* \t {g.year}\n *Credits:* \t {g.credits}\n *Average:* \t {g.average}\n *Standing:* \t {g.standing}'
        bot.send_message(chat_id=telegram_id, text=msg, parse_mode="Markdown")
    else:
        bot.send_message(chat_id=telegram_id, text="Course not found")



start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

register_handler = CommandHandler('register', register, pass_args=True)
dispatcher.add_handler(register_handler)

update_handler = CommandHandler('update', update, pass_args=True)
dispatcher.add_handler(update_handler)

unregister_handler = CommandHandler('unregister', unregister)
dispatcher.add_handler(unregister_handler)

request_handler = CommandHandler('request', request, pass_args=True)
dispatcher.add_handler(request_handler)

executor = futures.ThreadPoolExecutor(max_workers = 2)
wait_for = [executor.submit(updater.start_polling), executor.submit(startWorkers, engine,bot, int(config['ssc_checker']['threads']))]
#updater.start_polling()
print(futures.wait(wait_for))



