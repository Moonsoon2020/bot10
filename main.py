import logging
import threading
import xlsxwriter
import schedule
from telegram import ReplyKeyboardMarkup, Update, KeyboardButton
from telegram.ext import MessageHandler, ConversationHandler, filters, Application, ContextTypes
from telegram.ext import CommandHandler
from for_DBwork import DB
import requests


# Импорт необходимых библиотек
# Запускаем логгирование
logging.basicConfig(filename='logging.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
                    )
k1 = KeyboardButton('Помощь')
reply_keyboard = [[k1, '/stop']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
logger = logging.getLogger(__name__)
TOKEN = '5342995443:AAEBqyRLrd5AmHEEhCNLyfHVy3td3Qvw-Ec'  # токен бота
SUPER_PASSWORD = '777'  # пароль для админа


def threat():  # второй поток для рассылки
    while True:
        schedule.run_pending()


def pprint(inputi, name, text):
    logger.info(str(inputi) + str(text) + str(name))
    print(str(inputi), str(text), str(name))


def SendMessage(id, text, token):
    zap = f'''https://api.telegram.org/bot{token}/sendMessage'''
    params = {'chat_id': id, 'text': text}
    return requests.get(zap, params=params).json()


def send_messange():  # отправление рассылки
    print('send')
    list_of_messanges = ControlBD.get_mailings()
    print(list_of_messanges)
    for mailing in list_of_messanges:
        text, ids = mailing
        for id_ in ids:
            SendMessage(id_, text, TOKEN)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):  # старт
    print(00)
    if ControlBD.is_user(update.message.chat.id):
        text = 'Вы уже зарегистрированы.'
        await update.message.reply_text(text)
        pprint('/start', update.message.chat.username, text)
        return ConversationHandler.END
    text = f'Здравствуйте! Я смогу ответить на возникшие у Вас вопросы, но ' \
           f'для начала нужно пройти регистрацию. Напишите, пожалуйста, Ваши ФИО'
    await update.message.reply_text(text)
    pprint('/start', update.message.chat.username, text)
    return 1

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    FIO = update.message.text.split()
    context.user_data['FIO'] = FIO[:3]
    context.user_data['Name'] = FIO[1]
    if FIO[-1] == 'Admin' or FIO[-1] == 'Админ':
        text = f'Хорошо, теперь введите пароль.'
        await update.message.reply_text(text)
        pprint(FIO, update.message.chat.username, text)
        return 2
    else:
        text = f'Хорошо, теперь напишите название компанию, к которой вы прикриплены.'
        await update.message.reply_text(text)
        pprint(FIO, update.message.chat.username, text)
        return 3

async def password_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    if password == SUPER_PASSWORD:
        ControlBD.add_user(*context.user_data['FIO'], 1, update.message.chat.id)
        text = f'Успешно! {context.user_data["Name"]} вы зарегистрированы.'
        await update.message.reply_text(text, reply_markup=markup)
        pprint(password, update.message.chat.username, text)
        return ConversationHandler.END
    else:
        text = f'Попробуйте ещё раз, введте ФИО.'
        pprint(password, update.message.chat.username, text)
        await update.message.reply_text(text)
        return 1

async def reg_first_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name_company = update.message.text
    context.user_data['NameCompany'] = name_company
    if not ControlBD.check_company(name_company):
        text = f'Произошла ошибка: Компании с таким названием не существует. Проверьте введенные данные.' \
               f' {context.user_data["Name"]}, введите название компании, в которую хотите вступить.'
        await update.message.reply_text(text)
        pprint(name_company, update.message.chat.username, text)
        return 3
    context.user_data['PasswordCompany'] = ControlBD.get_company_password(context.user_data['NameCompany'])
    text = 'Компания найдена. Введите пароль.'
    await update.message.reply_text(text)
    pprint(name_company, update.message.chat.username, text)
    return 4

async def reg_first_company_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    if password != context.user_data['PasswordCompany']:
        text = f'Произошла ошибка: компания или пароль введены неверно.' \
               f'Введите название компании.'
        await update.message.reply_text(text)
        pprint(password, update.message.chat.username, text)
        return 3
    text = f'Регистрация прошла успешно, теперь вы можете пользоваться всеми функциями бота.'
    await update.message.reply_text(text, reply_markup=markup)
    ControlBD.add_user(*context.user_data['FIO'], 0, update.message.chat.id)
    ControlBD.remove_user_company(update.message.chat.id, context.user_data['NameCompany'])
    pprint(password, update.message.chat.username, text)
    return ConversationHandler.END

async def stop_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = 'Регистрация отменена.'
    await update.message.reply_text(text)
    pprint('/stop', update.message.chat.username, text)
    return ConversationHandler.END

async def get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):  # получить ответ
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return
    company = ControlBD.get_user_company(str(update.message.from_user.id))
    if update.message.text == 'Помощь':
        await helps(update, context)
        return
    if company is None or company == '':
        if ControlBD.get_user_post(str(update.message.from_user.id)) == 0:
            text = f'{ControlBD.get_user_name(str(update.message.from_user.id))}, Вы не можете'\
                   f' получить ответ, так как не состоите в компании.'
        else:
            text = f'{ControlBD.get_user_name(str(update.message.from_user.id))}, Вы - администратор!' \
                   f' Уверен, ответы на все интересующие вопросы Вы знаете сами)'
    else:
        if update.message.text in list(map(lambda i: i[1][0], ControlBD.get_questions(company))):
            text = str(ControlBD.get_answer(update.message.text, company))
        else:
            text = 'Извините, вопрос не найден.'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)

async def helps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return
    if ControlBD.get_user_post(str(update.message.from_user.id)) == 1:
        text = f'Привет, уважаемый пользователь,' \
               f' {ControlBD.get_user_name(str(update.message.from_user.id))}, Ваша роль - Admin.\n' \
                'Доступные Вам функции:\n' \
                '/get_xlsx_file - получить Excel таблицу со всеми данными для просмотра и диагностики\n' \
                '/stop используется для остановки любого процесса, в котором бы вы не находились.\n ' \
                '/creating_company используется для создания новой компании.\n' \
                'Данные, используемые при создании компании: название компании, её уникальный ' \
                'пароль, номер телефона.\n ' \
                '/edit_post изменить/выбрать роль.\n' \
                '/delete_company используется для удаления уже существующей компании. Для удаления ' \
                'необходимо только название.\n ' \
                '/add_mailing используется для создания новой рассылки. Для её создания необходимо ' \
                'несколько элементов: компания, текст, даты отправления.\n ' \
                '/delete_mailing используется для удаления рассылки. Для её удаления необходимо ' \
                'несколько элементов: компания, текст, дата отправления.\n' \
                '/add_question используется для создания нового вопроса. Для его создания необходимо ' \
                'несколько элементов: компания, текст вопроса, текст ответа.\n' \
                '/redact_question используется для редактирования существующего вопроса. Для его ' \
                'редактирования необходимо' \
                'несколько элементов: компания, текст вопроса, изменённый текст ответа.\n' \
                '/delete_question используется для удаления вопроса. Для его удаления необходимо ' \
                'несколько элементов: компания, текст вопроса, текст ответа.\n' \
                'Приятного использования!'
    else:
        text = f'Привет, уважаемый пользователь, ' \
               f'{ControlBD.get_user_name(str(update.message.from_user.id))}.\n' \
                'Доступные Вам функции:\n' \
                '/stop используется для остановки любого процесса, в котором Вы находитесь.\n' \
                '/reg_company используется для регистрации в какой-либо компании.\n' \
                '/edit_post изменить/выбрать роль.\n' \
                '/unbinding используется для отключения Вас от вашей компании\n' \
                '/all_question при вызове возвращаются все вопросы, реализованные для Вашей ' \
                'компании.\n ' \
                'Все остальное бот будет принимать как вопрос, заданный Вами.\n' \
                'Приятного использования!'
    await update.message.reply_text(text)
    pprint('/help', update.message.chat.username, text)

async def unbinding_company(update: Update, context: ContextTypes.DEFAULT_TYPE):  # выход из компании
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END
    if ControlBD.get_user_post(update.message.from_user.id) == 1:
        text = 'Для выполнения это функции вы должны быть обычным пользователем.'
        await update.message.reply_text(text)
        pprint('/', update.message.chat.username, text)
        return ConversationHandler.END
    ControlBD.remove_user_company(str(update.message.from_user.id), '')
    text = f'{ControlBD.get_user_name(str(update.message.from_user.id))}, Вы вышли из компании.'
    await update.message.reply_text(text)
    pprint('/unbinding', update.message.chat.username, text)

async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):  # получение xlsx файла с информацией из БД
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return
    print(ControlBD.get_user_post(update.message.from_user.id) == 0, 'o')
    if ControlBD.get_user_post(update.message.from_user.id) == 0:
        text = 'Для выполнения этой функции вы должны быть администратором.'
        await update.message.reply_text(text)
        pprint('/get_file', update.message.chat.username, text)
        return
    text = f'Подождите, происходит формирование таблицы, загрузка и отправление... ' \
           f'Это займет несколько минут. Спасибо за ожидание.'
    await update.message.reply_text(text)
    pprint('/get_xlsx_file', update.message.chat.username, text)
    workbook = xlsxwriter.Workbook('Таблица_Excel_БД.xlsx')
    data = ControlBD.get_info_for_file()
    for sheet in data:
        name, stroki = sheet
        worksheet = workbook.add_worksheet(name)
        for row, stroka in enumerate(stroki):
            for i in range(len(stroka)):
                worksheet.write(row, i, stroka[i])
    workbook.close()
    await update.message.reply_document(document=open('Таблица_Excel_БД.xlsx', mode='rb'))

async def all_question(update: Update, context: ContextTypes.DEFAULT_TYPE):  # получение всех вопросов
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return
    if ControlBD.get_user_post(update.message.from_user.id) == 1:
        text = 'Для выполнения это функции вы должны быть обычным пользователем.'
        await update.message.reply_text(text)
        pprint('/', update.message.chat.username, text)
        return
    company = ControlBD.get_user_company(str(update.message.from_user.id))
    questions = ControlBD.get_questions(company)
    if questions:
        text = '\n'.join([str(x[0] + 1) + '. ' + x[1][0].capitalize() for x in questions])
    else:
        text = f'{ControlBD.get_user_name(str(update.message.from_user.id))}, для Вашей' \
               f' компании не реализованны вопросы.'
    await update.message.reply_text(text)
    pprint('/all_question', update.message.chat.username, text)

async def edit_post(update: Update, context: ContextTypes.DEFAULT_TYPE):  # редактирование роли
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END
    text = f'{ControlBD.get_user_name(str(update.message.from_user.id))}, введите пароль.'
    await update.message.reply_text(text)
    pprint('/edit_post', update.message.chat.username, text)
    return 1

async def edit_post_input_password(update: Update, context: ContextTypes.DEFAULT_TYPE):  # функция проверки суперпароля
    password = update.message.text
    if password == SUPER_PASSWORD:
        ControlBD.remove_user_post(str(update.message.from_user.id))
        ControlBD.remove_user_company(str(update.message.from_user.id), '')
        text = 'Успешно! Ваша роль изменена.'
        await update.message.reply_text(text)
        pprint(password, update.message.chat.username, text)
        return ConversationHandler.END
    else:
        text = f'Для того чтобы сменить роль, нужно '\
               f'ввести выданный Вам пароль: Например: 0000'
        await update.message.reply_text(text)
        pprint(password, update.message.chat.username, text)
        return 1

async def stop_edit_post(update: Update, context: ContextTypes.DEFAULT_TYPE):  # завершение
    text = 'Редактирование роли остановлено.'
    await update.message.reply_text(text)
    pprint('/stop', update.message.chat.username, text)
    return ConversationHandler.END

async def linking_company(update: Update, context: ContextTypes.DEFAULT_TYPE):  # регистрация в компании
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END
    if ControlBD.get_user_post(update.message.from_user.id) == 1:
        text = 'Для выполнения это функции вы должны быть обычным пользователем.'
        await update.message.reply_text(text)
        pprint('/', update.message.chat.username, text)
        return ConversationHandler.END
    logger.info('привязка к компании')
    text = f'{ControlBD.get_user_name(str(update.message.from_user.id))}, введ' \
           f'ите название компании, в которую хотите вступить.'
    await update.message.reply_text(text)
    pprint('/linking', update.message.chat.username, text)
    return 1

async def get_name_company(update: Update, context: ContextTypes.DEFAULT_TYPE):  # регистрация в компании
    name_company = update.message.text
    context.user_data['NameCompany'] = name_company
    if not ControlBD.check_company(name_company):
        text = f'Произошла ошибка: Компании с такимmназванием не существует. Проверьте введенные данные.'
        text += f'{ControlBD.get_user_name(str(update.message.from_user.id))}, введите ' \
                f'название компании, в которую хотите вступить.'
        await update.message.reply_text(text)
        pprint(name_company, update.message.chat.username, text)
        return 1
    context.user_data['PasswordCompany'] = ControlBD.get_company_password(name_company)
    text = 'Компания найдена. Введите пароль.'
    await update.message.reply_text(text)
    pprint(name_company, update.message.chat.username, text)
    return 2

async def get_company_password(update: Update, context: ContextTypes.DEFAULT_TYPE):  # регистрация в компании
    if context.user_data['PasswordCompany'] != update.message.text:
        text = 'Возникла ошибка: введен неверный пароль компании.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return 1
    ControlBD.remove_user_company(str(update.message.from_user.id), context.user_data['NameCompany'])
    text = f'{ControlBD.get_user_name(str(update.message.from_user.id))}, Вы успешно вступили компанию.'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return ConversationHandler.END

async def stop_linking(update: Update, context: ContextTypes.DEFAULT_TYPE):  # завершение
    text = '''Теперь Вы можете вступить в компанию. Для этого напишите или нажмите на /reg_company'''
    await update.message.reply_text(text)
    pprint('/stop', update.message.chat.username, text)
    return ConversationHandler.END

async def input_name_company(update: Update, context: ContextTypes.DEFAULT_TYPE):  # создание компании
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END
    if ControlBD.get_user_post(update.message.from_user.id) == 0:
        text = 'Для создания компании вы должны быть администратором.'
        await update.message.reply_text(text)
        pprint('/new_company', update.message.chat.username, text)
        return ConversationHandler.END
    text = 'Введите будущее название компании.'
    await update.message.reply_text(text)
    pprint('/new_company', update.message.chat.username, text)
    return 1

async def input_password_company(update: Update, context: ContextTypes.DEFAULT_TYPE):  # создание компании
    context.user_data['title'] = update.message.text
    if ControlBD.check_company(update.message.text):
        text = 'Компания с таким именем уже существует.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return 1
    text = 'Введите пароль компании для входа пользователей.'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return 2

async def input_get_telephone(update: Update, context: ContextTypes.DEFAULT_TYPE):  # создание компании
    context.user_data['password'] = update.message.text
    text = 'Введите контактный телефон владельца компании (Ваш).'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return 3

async def creating_company(update: Update, context: ContextTypes.DEFAULT_TYPE):  # создание компании
    ControlBD.add_company(context.user_data['title'], update.message.text, context.user_data['password'])
    text = 'Успешно! Компания создана, а Вы её администратор.'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return ConversationHandler.END

async def stop_new_company(update: Update, context: ContextTypes.DEFAULT_TYPE):  # завершение
    text = 'Остановка создания компании.'
    await update.message.reply_text(text)
    pprint('/stop', update.message.chat.username,text)
    return ConversationHandler.END

async def delete_company(update: Update, context: ContextTypes.DEFAULT_TYPE):  # удаление компании
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END
    if ControlBD.get_user_post(update.message.from_user.id) == 0:
        text = 'Для выполнения это функции вы должны быть администратором.'
        await update.message.reply_text(text)
        pprint('/', update.message.chat.username, text)
        return ConversationHandler.END
    text = f'Введите название компании, которую хотите' \
           f' удалить. ВНИМАНИЕ: это действие отменить будет невозможно.'''
    await update.message.reply_text(text)
    pprint('/del_company', update.message.chat.username, text)
    return 1

async def delete_comp(update: Update, context: ContextTypes.DEFAULT_TYPE):  # удаление компании
    ControlBD.delete_company(update.message.text)
    text = 'Компания удалена.'
    await update.message.reply_text(text)
    pprint(update.message.chat, update.message.chat.username, text)
    return ConversationHandler.END

async def stop_del_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = 'Отмена удаления компании.'
    await update.message.reply_text(text)
    pprint('/stop', update.message.chat.username, text)
    return ConversationHandler.END

async def add_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE):  # добавление рассылки
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END
    if ControlBD.get_user_post(update.message.from_user.id) == 0:
        text = 'Для выполнения это функции вы должны быть администратором.'
        await update.message.reply_text(text)
        pprint('/', update.message.chat.username, text)
        return ConversationHandler.END
    text = f'{ControlBD.get_user_name(str(update.message.from_user.id))}, уведомления для '\
           f'пользователей какой компании Вы хотите добавить/удалить?'
    await update.message.reply_text(text)
    pprint('add_mailing', update.message.chat.username, text)
    return 1

async def what_company(update: Update, context: ContextTypes.DEFAULT_TYPE):  # определение компании
    company = update.message.text
    if ControlBD.check_company(company):
        context.user_data['company'] = company
        text = 'Какое сообщение хотите, чтоб отправлялось/удалялось?'
        await update.message.reply_text(text)
        pprint(company, update.message.chat.username, text)
        return 2
    else:
        text = 'Ошибка: компания с таким названием не найдена. ' \
               'Уведомления для пользователей какой компании Вы хотите добавить/удалить?'
        await update.message.reply_text(text)
        pprint(company, update.message.chat.username, text)
        return 1

async def get_TEXT_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE):  # редактирование рассылки
    context.user_data['TEXT'] = update.message.text
    text = f'В какую(-ые) даты отправлять или уведомления в какую дату удалить? ' \
           f'Вводите через запятую с пробелом, в формете день.месяц.год.'\
           f'Например: 25.05.2022, 23.02.2023'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return 3

async def get_date_add(update: Update, context: ContextTypes.DEFAULT_TYPE):  # добавление рассылки
    date = update.message.text.split(', ')
    for i in date:
        ControlBD.add_mailing(context.user_data['TEXT'], i, context.user_data['company'])
    text = 'Успешно! Уведомления ждут своей отправки.'
    await update.message.reply_text(text)
    pprint(date, update.message.chat.username, text)
    return ConversationHandler.END

async def stop_new_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE):  # завершение
    text = 'Добавление уведомления остановлено.'
    await update.message.reply_text(text)
    pprint('/stop', update.message.chat.username, text)
    return ConversationHandler.END

async def get_date_del(update: Update, context: ContextTypes.DEFAULT_TYPE):  # удаление даты
    date = update.message.text.split(', ')
    for i in date:
        ControlBD.delete_mailing(context.user_data['TEXT'], i, context.user_data['company'])
    text = 'Успешно! Дата удалена.'
    await update.message.reply_text(text)
    pprint(date, update.message.chat.username, text)
    return ConversationHandler.END

async def stop_del_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE):  # завершение
    text = 'Удаление рассылки остановлено.'
    await update.message.reply_text(text)
    pprint('/stop', update.message.chat.username, text)
    return ConversationHandler.END

async def add_question(update: Update, context: ContextTypes.DEFAULT_TYPE):  # редактирование вопроса
    if not ControlBD.is_user(update.message.chat.id):
        text = 'Вы не зарегестрированы.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END
    if ControlBD.get_user_post(update.message.from_user.id) == 0:
        text = 'Для выполнения это функции вы должны быть администратором.'
        await update.message.reply_text(text)
        pprint('/', update.message.chat.username, text)
        return ConversationHandler.END
    text = f'{ControlBD.get_user_name(str(update.message.from_user.id))}, введите вопрос,' \
           f' который нужно добавить/редактировать/удалить.'
    await update.message.reply_text(text)
    pprint('/add_question', update.message.chat.username, text)
    return 1

async def add_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):  # редактирование вопроса
    context.user_data['question'] = update.message.text
    text = 'Введите ответ на вопрос.'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return 2

async def creating_question(update: Update, context: ContextTypes.DEFAULT_TYPE):  # редактирование вопроса
    context.user_data['answer'] = update.message.text
    text = 'Введите компанию, участники которой могут задать вопрос.'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return 3

async def write_question_add(update: Update, context: ContextTypes.DEFAULT_TYPE):  # добавление вопроса
    ControlBD.add_question(context.user_data['question'], context.user_data['answer'], update.message.text)
    text = 'Вопрос добавлен.'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return ConversationHandler.END

async def stop_question_add(update: Update, context: ContextTypes.DEFAULT_TYPE):  # завершение
    text = 'Добавление/редактирование/удаление вопроса остановлено.'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return ConversationHandler.END

async def write_question_del(update: Update, context: ContextTypes.DEFAULT_TYPE):  # удаление вопроса
    context.user_data['company'] = update.message.text
    if ControlBD.check_question_all(context.user_data['question'], context.user_data['answer'],
                                         context.user_data['company']):
        ControlBD.delete_question(context.user_data['question'], context.user_data['answer'],
                                       context.user_data['company'])
    else:
        text = 'Ошибка: вопроса с такими характеристиками не существует.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        text = 'Введите вопрос, который нужно добавить/редактировать/удалить.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return 1
    text = 'Вопрос удален.'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return ConversationHandler.END

async def write_question_red(update: Update, context: ContextTypes.DEFAULT_TYPE):  # редактирование вопроса
    context.user_data['company'] = update.message.text
    if ControlBD.check_question(context.user_data['question'], context.user_data['company']):
        ControlBD.redact_question(context.user_data['question'], context.user_data['answer'],
                           update.message.text)
    else:
        text = 'Ошибка: данного вопроса у данной компании не существует.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        text = 'Введите вопрос, который нужно добавить/редактировать/удалить.'
        await update.message.reply_text(text)
        pprint(update.message.text, update.message.chat.username, text)
        return 1
    text = 'Вопрос изменен.'
    await update.message.reply_text(text)
    pprint(update.message.text, update.message.chat.username, text)
    return ConversationHandler.END


if __name__ == '__main__':
    ControlBD = DB()
    application = Application.builder().token(TOKEN).build()
    schedule.every().day.at("16:45").do(send_messange)  # рассылка уведомлений
    threading.Thread(target=threat).start()
    # сценарии
    script_registration = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('start', start)],
        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, info)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_request)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_first_company)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_first_company_password)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        allow_reentry=False,
        fallbacks=[CommandHandler('stop', stop_reg)]
    )
    script_edit_post = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('edit_post', edit_post)],
        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_post_input_password)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop_edit_post)],
        allow_reentry=False
    )
    script_linking_company = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('reg_company', linking_company)],
        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name_company)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_company_password)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop_linking)]
    )
    script_creature_company = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('creating_company', input_name_company)],
        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_password_company)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_get_telephone)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, creating_company)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop_new_company)]
    )
    script_del_company = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('delete_company', delete_company)],
        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_comp)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop_del_company)]
    )
    script_adding_mailing_lists = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('add_mailing', add_mailing)],
        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, what_company)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_TEXT_mailing)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date_add)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop_new_mailing)]
    )
    script_del_mailing_lists = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('delete_mailing', add_mailing)],
        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, what_company)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_TEXT_mailing)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date_del)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop_del_mailing)]
    )
    script_add_question_lists = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('add_question', add_question)],
        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_answer)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, creating_question)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, write_question_add)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop_question_add)]
    )
    script_del_question_lists = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('delete_question', add_question)],
        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_answer)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, creating_question)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, write_question_del)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop_question_add)]
    )
    script_red_question_lists = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('redact_question', add_question)],
        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_answer)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, creating_question)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, write_question_red)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop_question_add)]
    )


    application.add_handler(CommandHandler("help", helps))
    application.add_handler(CommandHandler("unbinding", unbinding_company))
    application.add_handler(CommandHandler("get_xlsx_file", get_file))
    application.add_handler(CommandHandler('all_question', all_question))

    application.add_handler(script_red_question_lists)
    application.add_handler(script_del_question_lists)
    application.add_handler(script_add_question_lists)
    application.add_handler(script_del_mailing_lists)
    application.add_handler(script_adding_mailing_lists)
    application.add_handler(script_del_company)
    application.add_handler(script_creature_company)
    application.add_handler(script_linking_company)
    application.add_handler(script_registration)
    application.add_handler(script_edit_post)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_question))
    application.run_polling()
