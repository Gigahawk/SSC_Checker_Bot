import configparser

def GenerateConfig():
    config = configparser.ConfigParser()

    config['telegram'] = {
            'token': ''
            }

    config['db'] = {
            'type': 'postgresql',
            'username': 'ubc_ssc_bot',
            'password': 'ubc_ssc_bot_pass',
            'host': 'localhost',
            'port': '5432',
            'database': 'ubc_ssc_bot'
            }

    config['ssc_checker'] = {
            'threads': '4'
            }

    with open('config.ini', 'w') as configfile:
        config.write(configfile)


