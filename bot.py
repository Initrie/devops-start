import logging
import re
import paramiko
import os
import psycopg2

from psycopg2 import Error
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

load_dotenv()

TOKEN = os.getenv('TOKEN')

# Подключаем логирование
logging.basicConfig(
    filename='app.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

host = os.getenv('HOST')
port = os.getenv('PORT')
username = os.getenv('USER')
password = os.getenv('PASSWORD')

db_host = os.getenv('DB_HOST')[1:-2]
db_port = int(os.getenv('DB_PORT')[1:-2])
db_username = os.getenv('DB_USER')[1:-2]
db_password = os.getenv('DB_PASSWORD')[1:-2]
db_name = os.getenv('DB_DATABASE')

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def handleText(update, context):
    update.message.reply_text('Извини, я тебя не понимаю. Отправь мне команду')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'


def findPhoneNumbers(update: Update, context):
    user_input = update.message.text 

    phoneNumRegex = re.compile(r'((8|\+7)[\- ]?)(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}') 

    phoneNumberList = [x.group() for x in re.finditer(phoneNumRegex, user_input)]

    if not phoneNumberList: 
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    
    context.user_data['phoneNumberList'] = phoneNumberList

    phoneNumbers = ''
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n'
        
    update.message.reply_text(phoneNumbers) 
    update.message.reply_text("Хотите записать их в базу данных (0-ДА/any-НЕТ)?")

    return 'addPhoneNumbersToDB'


def addPhoneNumbersToDB(update: Update, context):
    user_input = update.message.text 
    if user_input != '0':
        return ConversationHandler.END
    
    phoneNumberList = context.user_data['phoneNumberList']

    connection = None

    try:
        connection = psycopg2.connect(user=db_username,
                                    password=db_password,
                                    host=db_host,
                                    port=db_port, 
                                    database=db_name)

        cursor = connection.cursor()
    
        for i in phoneNumberList: 
            cursor.execute(f"INSERT INTO phonenumber (phonenumber) VALUES ('{i}')")
        connection.commit()
        update.message.reply_text('Запись была успешно выполнена')
    except (Exception, Error) as error:
        update.message.reply_text('Запись была прекращена с ошибкой: ' + error)
        logging.error("PostgreSQL error: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return ConversationHandler.END


def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email-адресов: ')

    return 'findEmails'


def findEmails(update: Update, context):
    user_input = update.message.text 

    emailRegex = re.compile(r'[a-zA-Z0-9._%+-]+@[A-Za-z0-9-\.]+\.[a-z]{2,4}')

    emailList = emailRegex.findall(user_input) 

    context.user_data['emailList'] = emailList

    if not emailList: 
        update.message.reply_text('Email-адреса не найдены')
        return ConversationHandler.END
    
    emails = '' 
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n' 
        
    update.message.reply_text(emails) 
    update.message.reply_text("Хотите записать их в базу данных (0-ДА/any-НЕТ)?")

    return 'addEmailsToDB'


def addEmailsToDB(update: Update, context):
    user_input = update.message.text 
    if user_input != '0':
        return ConversationHandler.END
    
    emailList = context.user_data['emailList']

    connection = None

    try:
        connection = psycopg2.connect(user=db_username,
                                    password=db_password,
                                    host=db_host,
                                    port=db_port, 
                                    database=db_name)

        cursor = connection.cursor()
    
        for i in emailList: 
            cursor.execute(f"INSERT INTO email (email) VALUES ('{i}')")
        connection.commit()
        update.message.reply_text('Запись была успешно выполнена')
    except (Exception, Error) as error:
        update.message.reply_text('Запись была прекращена с ошибкой: ' + error)
        logging.error("PostgreSQL error: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return ConversationHandler.END


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')

    return 'verifyPassword'


def verifyPassword(update: Update, context):
    user_input = update.message.text 

    strongPasswordRegex = re.compile(r'^(?=.*[A-Z])(?=.*[!@#$%^&*()])(?=.*[0-9])(?=.*[a-z]).{8,}$')

    if strongPasswordRegex.match(user_input) == None:
        update.message.reply_text('Пароль простой')
        return ConversationHandler.END
    
    update.message.reply_text('Пароль сложный')
    return ConversationHandler.END


def execCommandOnRemoteServer(command, host=host, port=port, username=username, password=password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return data


def getRelease(update: Update, context):
    data = execCommandOnRemoteServer(command='cat /etc/*release')

    update.message.reply_text(data)

def getUptime(update: Update, context):
    data = execCommandOnRemoteServer(command='uptime')

    update.message.reply_text(data)

def getUptime(update: Update, context):
    data = execCommandOnRemoteServer(command='uptime')

    update.message.reply_text(data)

def getUname(update: Update, context):
    data = execCommandOnRemoteServer(command='uname -a')

    update.message.reply_text(data)

def getDf(update: Update, context):
    data = execCommandOnRemoteServer(command='df -h')

    update.message.reply_text(data)

def getFree(update: Update, context):
    data = execCommandOnRemoteServer(command='free -h')

    update.message.reply_text(data)

def getMpstat(update: Update, context):
    data = execCommandOnRemoteServer(command='mpstat')

    update.message.reply_text(data)

def getW(update: Update, context):
    data = execCommandOnRemoteServer(command='w')

    update.message.reply_text(data)

def getAuths(update: Update, context):
    data = execCommandOnRemoteServer(command='tail /var/log/auth.log')

    update.message.reply_text(data)

def getCritical(update: Update, context):
    data = execCommandOnRemoteServer(command='grep -i -e fail -e error -e corrupt -r /var/log/syslog | tail -n 5')

    update.message.reply_text(data)

def getPs(update: Update, context):
    data = execCommandOnRemoteServer(command='ps')

    update.message.reply_text(data)

def getSs(update: Update, context):
    data = execCommandOnRemoteServer(command='ss -lntpu')

    update.message.reply_text(data)

def getAptListCommand(update: Update, context):
    update.message.reply_text('Введите название пакета для поиска: ')

    return 'getAptList'

def getAptList(update: Update, context):
    user_input = update.message.text 

    data = execCommandOnRemoteServer(command=f'apt list --installed | grep \'{user_input}\'')

    update.message.reply_text(data)
    return ConversationHandler.END

def getServices(update: Update, context):
    data = execCommandOnRemoteServer(command='service --status-all')

    update.message.reply_text(data)

def getFromBD(tableName):
    connection = None

    try:
        connection = psycopg2.connect(user=db_username,
                                    password=db_password,
                                    host=db_host,
                                    port=db_port, 
                                    database=db_name)

        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {tableName};")
        data = cursor.fetchall()

        str_data = f'id | {tableName}\n'
        for row in data:
            str_data += str(row[0]) + '  | ' + str(row[1]) + '\n'

        str_data = str_data[:len(str_data)-1]

        return str_data
    except (Exception, Error) as error:
        logging.error("PostgreSQL error: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def getNamesFromBD(update: Update, context):
    data = getFromBD('phonenumber')

    update.message.reply_text(data)

def getEmailsFromBD(update: Update, context):   
    data = getFromBD('email')

    update.message.reply_text(data)

def getReplicaLogs(update: Update, context):
    data = execCommandOnRemoteServer(command='cat /var/log/postgresql/postgresql-14-main.log | grep "repl_user" | tail')

    update.message.reply_text(data)


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'addPhoneNumbersToDB': [MessageHandler(Filters.text & ~Filters.command, addPhoneNumbersToDB)],
        },
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'findEmails': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            'addEmailsToDB': [MessageHandler(Filters.text & ~Filters.command, addEmailsToDB)],
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verifyPassword': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )

    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'getAptList': [MessageHandler(Filters.text & ~Filters.command, getAptList)],
        },
        fallbacks=[]
    )

		
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("get_release", getRelease))
    dp.add_handler(CommandHandler("get_uname", getUname))
    dp.add_handler(CommandHandler("get_uptime", getUptime))
    dp.add_handler(CommandHandler("get_df", getDf))
    dp.add_handler(CommandHandler("get_free", getFree))
    dp.add_handler(CommandHandler("get_mpstat", getMpstat))
    dp.add_handler(CommandHandler("get_w", getW))
    dp.add_handler(CommandHandler("get_auths", getAuths))
    dp.add_handler(CommandHandler("get_critical", getCritical))
    dp.add_handler(CommandHandler("get_ps", getPs))
    dp.add_handler(CommandHandler("get_ss", getSs))
    dp.add_handler(CommandHandler("get_services", getServices))
    dp.add_handler(CommandHandler("get_phone_numbers", getNamesFromBD))
    dp.add_handler(CommandHandler("get_emails", getEmailsFromBD))
    dp.add_handler(CommandHandler("get_repl_logs", getReplicaLogs))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerGetAptList)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
		
	# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handleText))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()