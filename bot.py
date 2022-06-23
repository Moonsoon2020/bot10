import logging
import threading
import xlsxwriter
import schedule
import telegram.ext
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, ConversationHandler
from telegram.ext import CommandHandler
from for_DBwork import DB

# Импорт необходимых библиотек
# Запускаем логгирование
logging.basicConfig(filename='logging.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
                    )

logger = logging.getLogger(__name__)
TOKEN = '5355485794:AAGBNp_ZMuEw8vK1t9UiuuDOV8yOY0OQN_E'  # токен бота
SUPER_PASSWORD = '777'  # пароль для админа


class Bot:
    def __init__(self):
        self.ControlBD = DB()
        self.updater = Updater(TOKEN)
        self.dp = self.updater.dispatcher
        # schedule.every(30).seconds.do(self.send_messange, self.dp)
        schedule.every().day.at("10:00").do(self.send_messange, self.dp)  # рассылка уведомлений
        threading.Thread(target=self.threat).start()
        # сценарии
        script_registration = ConversationHandler(
            # Точка входа в диалог.
            # В данном случае — команда /start. Она задаёт первый вопрос.
            entry_points=[CommandHandler('start', self.start, pass_user_data=True)],
            # Состояние внутри диалога.
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.info, pass_user_data=True)],
                2: [MessageHandler(Filters.text & ~Filters.command, self.password_request, pass_user_data=True)],
                3: [MessageHandler(Filters.text & ~Filters.command, self.reg_first_company, pass_user_data=True)],
                4: [MessageHandler(Filters.text & ~Filters.command, self.reg_first_company_password,
                                   pass_user_data=True)]
            },
            # Точка прерывания диалога. В данном случае — команда /stop.
            allow_reentry=False,
            fallbacks=[CommandHandler('stop', self.stop_reg, pass_user_data=True)]
        )
        script_edit_post = ConversationHandler(
            # Точка входа в диалог.
            # В данном случае — команда /start. Она задаёт первый вопрос.
            entry_points=[CommandHandler('edit_post', self.edit_post, pass_user_data=True)],
            # Состояние внутри диалога.
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.edit_post_input_password, pass_user_data=True)]
            },
            # Точка прерывания диалога. В данном случае — команда /stop.
            fallbacks=[CommandHandler('stop', self.stop_edit_post, pass_user_data=True)],
            allow_reentry=False
        )
        script_linking_company = ConversationHandler(
            # Точка входа в диалог.
            # В данном случае — команда /start. Она задаёт первый вопрос.
            entry_points=[CommandHandler('reg_company', self.linking_company, pass_user_data=True)],
            # Состояние внутри диалога.
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.get_name_company, pass_user_data=True)],
                2: [MessageHandler(Filters.text & ~Filters.command, self.get_company_password, pass_user_data=True)]
            },
            # Точка прерывания диалога. В данном случае — команда /stop.
            fallbacks=[CommandHandler('stop', self.stop_linking, pass_user_data=True)]
        )
        script_creature_company = ConversationHandler(
            # Точка входа в диалог.
            # В данном случае — команда /start. Она задаёт первый вопрос.
            entry_points=[CommandHandler('creating_company', self.input_name_company, pass_user_data=True)],
            # Состояние внутри диалога.
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.input_password_company, pass_user_data=True)],
                2: [MessageHandler(Filters.text & ~Filters.command, self.input_get_telephone, pass_user_data=True)],
                3: [MessageHandler(Filters.text & ~Filters.command, self.creating_company, pass_user_data=True)]
            },
            # Точка прерывания диалога. В данном случае — команда /stop.
            fallbacks=[CommandHandler('stop', self.stop_new_company, pass_user_data=True)]
        )
        script_del_company = ConversationHandler(
            # Точка входа в диалог.
            # В данном случае — команда /start. Она задаёт первый вопрос.
            entry_points=[CommandHandler('delete_company', self.delete_company, pass_user_data=True)],
            # Состояние внутри диалога.
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.delete_comp, pass_user_data=True)]
            },
            # Точка прерывания диалога. В данном случае — команда /stop.
            fallbacks=[CommandHandler('stop', self.stop_del_company, pass_user_data=True)]
        )
        script_adding_mailing_lists = ConversationHandler(
            # Точка входа в диалог.
            # В данном случае — команда /start. Она задаёт первый вопрос.
            entry_points=[CommandHandler('add_mailing', self.add_mailing, pass_user_data=True)],
            # Состояние внутри диалога.
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.what_company, pass_user_data=True)],
                2: [MessageHandler(Filters.text & ~Filters.command, self.get_text_mailing, pass_user_data=True)],
                3: [MessageHandler(Filters.text & ~Filters.command, self.get_date_add, pass_user_data=True)]
            },
            # Точка прерывания диалога. В данном случае — команда /stop.
            fallbacks=[CommandHandler('stop', self.stop_new_mailing, pass_user_data=True)]
        )
        script_del_mailing_lists = ConversationHandler(
            # Точка входа в диалог.
            # В данном случае — команда /start. Она задаёт первый вопрос.
            entry_points=[CommandHandler('delete_mailing', self.add_mailing, pass_user_data=True)],
            # Состояние внутри диалога.
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.what_company, pass_user_data=True)],
                2: [MessageHandler(Filters.text & ~Filters.command, self.get_text_mailing, pass_user_data=True)],
                3: [MessageHandler(Filters.text & ~Filters.command, self.get_date_del, pass_user_data=True)]
            },
            # Точка прерывания диалога. В данном случае — команда /stop.
            fallbacks=[CommandHandler('stop', self.stop_del_mailing, pass_user_data=True)]
        )
        script_add_question_lists = ConversationHandler(
            # Точка входа в диалог.
            # В данном случае — команда /start. Она задаёт первый вопрос.
            entry_points=[CommandHandler('add_question', self.add_question, pass_user_data=True)],
            # Состояние внутри диалога.
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.add_answer, pass_user_data=True)],
                2: [MessageHandler(Filters.text & ~Filters.command, self.creating_question, pass_user_data=True)],
                3: [MessageHandler(Filters.text & ~Filters.command, self.write_question_add, pass_user_data=True)]
            },
            # Точка прерывания диалога. В данном случае — команда /stop.
            fallbacks=[CommandHandler('stop', self.stop_question_add, pass_user_data=True)]
        )
        script_del_question_lists = ConversationHandler(
            # Точка входа в диалог.
            # В данном случае — команда /start. Она задаёт первый вопрос.
            entry_points=[CommandHandler('delete_question', self.add_question, pass_user_data=True)],
            # Состояние внутри диалога.
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.add_answer, pass_user_data=True)],
                2: [MessageHandler(Filters.text & ~Filters.command, self.creating_question, pass_user_data=True)],
                3: [MessageHandler(Filters.text & ~Filters.command, self.write_question_del, pass_user_data=True)]
            },
            # Точка прерывания диалога. В данном случае — команда /stop.
            fallbacks=[CommandHandler('stop', self.stop_question_add, pass_user_data=True)]
        )
        script_red_question_lists = ConversationHandler(
            # Точка входа в диалог.
            # В данном случае — команда /start. Она задаёт первый вопрос.
            entry_points=[CommandHandler('redact_question', self.add_question, pass_user_data=True)],
            # Состояние внутри диалога.
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.add_answer, pass_user_data=True)],
                2: [MessageHandler(Filters.text & ~Filters.command, self.creating_question, pass_user_data=True)],
                3: [MessageHandler(Filters.text & ~Filters.command, self.write_question_red, pass_user_data=True)]
            },
            # Точка прерывания диалога. В данном случае — команда /stop.
            fallbacks=[CommandHandler('stop', self.stop_question_add, pass_user_data=True)]
        )
        reply_keyboard = [['/help', '/stop']]
        global markup
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        self.dp.add_handler(CommandHandler("help", self.helps))
        self.dp.add_handler(CommandHandler("unbinding", self.unbinding_company))
        self.dp.add_handler(CommandHandler("get_xlsx_file", self.get_file))
        self.dp.add_handler(CommandHandler('all_question', self.all_question))

        self.dp.add_handler(script_red_question_lists)
        self.dp.add_handler(script_del_question_lists)
        self.dp.add_handler(script_add_question_lists)
        self.dp.add_handler(script_del_mailing_lists)
        self.dp.add_handler(script_adding_mailing_lists)
        self.dp.add_handler(script_del_company)
        self.dp.add_handler(script_creature_company)
        self.dp.add_handler(script_linking_company)
        self.dp.add_handler(script_registration)
        self.dp.add_handler(script_edit_post)
        self.dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.get_question))
        self.updater.start_polling()
        self.updater.idle()

    @staticmethod
    def threat():  # второй поток для рассылки
        while True:
            schedule.run_pending()

    @staticmethod
    def pprint(inputi, name, text):
        logger.info(str(inputi) + str(text) + str(name))
        print(str(inputi), str(text), str(name))

    def send_messange(self, dp):  # отправление рассылки
        list_of_messanges = self.ControlBD.get_mailings()
        for mailing in list_of_messanges:
            text, ids = mailing
            for id_ in ids:
                telegram.ext.CallbackContext(dp).bot.sendMessage(chat_id=id_, text=text)

    def start(self, update, context):  # старт
        text = f'Здравствуйте! Я смогу ответить на возникшие у Вас вопросы, но ' \
               f'для начала нужно пройти регистрацию. Напишите, пожалуйста, Ваши ФИО'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/start', update.message.chat.username, text)
        return 1

    def info(self, update, context):
        FIO = update.message.text.split()
        context.user_data['FIO'] = FIO[:3]
        context.user_data['Name'] = FIO[1]
        if FIO[-1] == 'Admin' or FIO[-1] == 'Админ':
            text = f'Хорошо, теперь введите пароль.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(FIO, update.message.chat.username, text)
            return 2
        else:
            text = f'Хорошо, теперь напишите название компанию, к которой вы прикриплены.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(FIO, update.message.chat.username, text)
            return 3

    def password_request(self, update, context):
        password = update.message.text
        if password == SUPER_PASSWORD:
            self.ControlBD.add_user(*context.user_data['FIO'], 1, update.message.chat.id)
            text = f'Успешно! {context.user_data["Name"]} вы зарегистрированы.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text, reply_markup=markup)
            self.pprint(password, update.message.chat.username, text)
            return ConversationHandler.END
        else:
            text = f'Попробуйте ещё раз, введте ФИО.'
            self.pprint(password, update.message.chat.username, text)
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            return 1

    def reg_first_company(self, update, context):
        name_company = update.message.text
        context.user_data['NameCompany'] = name_company
        if not self.ControlBD.check_company(name_company):
            text = f'Произошла ошибка: Компании с таким названием не существует. Проверьте введенные данные.' \
                   f' {context.user_data["Name"]}, введите название компании, в которую хотите вступить.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(name_company, update.message.chat.username, text)
            return 3
        context.user_data['PasswordCompany'] = self.ControlBD.get_company_password(context.user_data['NameCompany'])
        text = 'Компания найдена. Введите пароль.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(name_company, update.message.chat.username, text)
        return 4

    def reg_first_company_password(self, update, context):
        password = update.message.text
        if password != context.user_data['PasswordCompany']:
            text = f'Произошла ошибка: компания или пароль введены неверно.' \
                   f'Введите название компании.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(password, update.message.chat.username, text)
            return 3
        text = f'Регистрация прошла успешно, теперь вы можете пользоваться всеми функциями бота.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text, reply_markup=markup)
        self.ControlBD.add_user(*context.user_data['FIO'], 0, update.message.chat.id)
        self.ControlBD.remove_user_company(update.message.chat.id, context.user_data['NameCompany'])
        self.pprint(password, update.message.chat.username, text)
        return ConversationHandler.END

    def stop_reg(self, update, context):
        text = 'Регистрация отменена.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/stop', update.message.chat.username, text)

    def get_question(self, update, context):  # получить ответ
        company = self.ControlBD.get_user_company(str(update.message.from_user.id))
        if company is None or company == '':
            if self.ControlBD.get_user_post(str(update.message.from_user.id)) == 0:
                text = f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}, Вы не можете'\
                       f' получить ответ, так как не состоите в компании.'
            else:
                text = f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}, Вы - администратор!' \
                       f' Уверен, ответы на все интересующие вопросы Вы знаете сами)'
        else:
            if update.message.text in list(map(lambda i: i[1][0], self.ControlBD.get_questions(company))):
                text = str(self.ControlBD.get_answer(update.message.text, company))
            else:
                text = 'Извините, вопрос не найден.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)

    def helps(self, update, context):
        if self.ControlBD.get_user_post(str(update.message.from_user.id)) == 1:
            text = f'Привет, уважаемый пользователь,' \
                   f' {self.ControlBD.get_user_name(str(update.message.from_user.id))}, Ваша роль - Admin.\n' \
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
                   f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}.\n' \
                    'Доступные Вам функции:\n' \
                    '/stop используется для остановки любого процесса, в котором Вы находитесь.\n' \
                    '/reg_company используется для регистрации в какой-либо компании.\n' \
                    '/edit_post изменить/выбрать роль.\n' \
                    '/unbinding используется для отключения Вас от вашей компании\n' \
                    '/all_question при вызове возвращаются все вопросы, реализованные для Вашей ' \
                    'компании.\n ' \
                    'Все остальное бот будет принимать как вопрос, заданный Вами.\n' \
                    'Приятного использования!'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/help', update.message.chat.username, text)

    def unbinding_company(self, update, context):  # выход из компании
        self.ControlBD.remove_user_company(str(update.message.from_user.id), '')
        text = f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}, Вы вышли из компании.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/unbinding', update.message.chat.username, text)

    def get_file(self, update, context):  # получение xlsx файла с информацией из БД
        if self.ControlBD.get_user_post(update.message.chat.id) == 0:
            return
        text = f'Подождите, происходит формирование таблицы, загрузка и отправление... ' \
               f'Это займет несколько минут. Спасибо за ожидание.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/get_xlsx_file', update.message.chat.username, text)
        workbook = xlsxwriter.Workbook('Таблица_Excel_БД.xlsx')
        data = self.ControlBD.get_info_for_file()
        for sheet in data:
            name, stroki = sheet
            worksheet = workbook.add_worksheet(name)
            for row, stroka in enumerate(stroki):
                for i in range(len(stroka)):
                    worksheet.write(row, i, stroka[i])
        workbook.close()
        context.bot.sendDocument(chat_id=update.message.from_user.id, document=open('Таблица_Excel_БД.xlsx', mode='rb'))

    def all_question(self, update, context):  # получение всех вопросов
        company = self.ControlBD.get_user_company(str(update.message.from_user.id))
        questions = self.ControlBD.get_questions(company)
        if questions:
            text = '\n'.join([str(x[0] + 1) + '. ' + x[1][0].capitalize() for x in questions])
        else:
            text = f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}, для Вашей' \
                   f' компании не реализованны вопросы.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/all_question', update.message.chat.username, text)

    def edit_post(self, update, context):  # редактирование роли
        text = f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}, введите пароль.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/edit_post', update.message.chat.username, text)
        return 1

    def edit_post_input_password(self, update, context):  # функция проверки суперпароля
        password = update.message.text
        if password == SUPER_PASSWORD:
            self.ControlBD.remove_user_post(str(update.message.from_user.id))
            self.ControlBD.remove_user_company(str(update.message.from_user.id), '')
            text = 'Успешно! Ваша роль изменена.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(password, update.message.chat.username, text)
            return ConversationHandler.END
        else:
            text = f'Для того чтобы сменить роль, нужно '\
                   f'ввести выданный Вам пароль: Например: 0000'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(password, update.message.chat.username, text)
            return 1

    def stop_edit_post(self, update, context):  # завершение
        text = 'Редактирование роли остановлено.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/stop', update.message.chat.username, text)
        return ConversationHandler.END

    def linking_company(self, update, context):  # регистрация в компании
        logger.info('привязка к компании')
        text = f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}, введ' \
               f'ите название компании, в которую хотите вступить.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/linking', update.message.chat.username, text)
        return 1

    def get_name_company(self, update, context):  # регистрация в компании
        name_company = update.message.text
        context.user_data['NameCompany'] = name_company
        if not self.ControlBD.check_company(name_company):
            text = f'Произошла ошибка: Компании с такимmназванием не существует. Проверьте введенные данные.'
            text += f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}, введите ' \
                    f'название компании, в которую хотите вступить.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(name_company, update.message.chat.username, text)
            return 1
        context.user_data['PasswordCompany'] = self.ControlBD.get_company_password(name_company)
        text = 'Компания найдена. Введите пароль.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(name_company, update.message.chat.username, text)
        return 2

    def get_company_password(self, update, context):  # регистрация в компании
        if context.user_data['PasswordCompany'] != update.message.text:
            text = 'Возникла ошибка: введен неверный пароль компании.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(update.message.text, update.message.chat.username, text)
            return 1
        self.ControlBD.remove_user_company(str(update.message.from_user.id), context.user_data['NameCompany'])
        text = f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}, Вы успешно вступили компанию.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END

    def stop_linking(self, update, context):  # завершение
        text = '''Теперь Вы можете вступить в компанию. Для этого напишите или нажмите на /reg_company'''
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/stop', update.message.chat.username, text)
        return ConversationHandler.END

    def input_name_company(self, update, context):  # создание компании
        if self.checking_status(update) == 0:
            text = 'Для создания компании вы должны быть администратором.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint('/new_company', update.message.chat.username, text)
            return ConversationHandler.END
        text = 'Введите будущее название компании.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/new_company', update.message.chat.username, text)
        return 1

    def input_password_company(self, update, context):  # создание компании
        context.user_data['title'] = update.message.text
        if self.ControlBD.check_company(update.message.text):
            text = 'Компания с таким именем уже существует.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(update.message.text, update.message.chat.username, text)
            return 1
        text = 'Введите пароль компании для входа пользователей.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)
        return 2

    def input_get_telephone(self, update, context):  # создание компании
        context.user_data['password'] = update.message.text
        text = 'Введите контактный телефон владельца компании (Ваш).'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)
        return 3

    def creating_company(self, update, context):  # создание компании
        self.ControlBD.add_company(context.user_data['title'], update.message.text, context.user_data['password'])
        text = 'Успешно! Компания создана, а Вы её администратор.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END

    def stop_new_company(self, update, context):  # завершение
        text = 'Остановка создания компании.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/stop', update.message.chat.username, text)
        return ConversationHandler.END

    def delete_company(self, update, context):  # удаление компании
        if self.checking_status(update) == 0:
            text = 'Для создания компании Вы должны быть администратором.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint('/stop', update.message.chat.username, text)
            return ConversationHandler.END
        text = f'Введите название компании, которую хотите' \
               f' удалить. ВНИМАНИЕ: это действие отменить будет невозможно.'''
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/del_company', update.message.chat.username, text)
        return 1

    def delete_comp(self, update, context):  # удаление компании
        a = update.message.text
        self.ControlBD.delete_company(a)
        text = 'Компания удалена.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(a, update.message.chat.username, text)
        return ConversationHandler.END

    def stop_del_company(self, update, context):
        text = 'Отмена удаления компании.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(a, update.message.chat.username, text)
        return ConversationHandler.END

    def checking_status(self, update):  # проверка роли пользователя
        return False if self.ControlBD.get_user_post(update.message.from_user.id) == 0 else True

    def add_mailing(self, update, context):  # добавление рассылки
        text = f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}, уведомления для '\
               f'пользователей какой компании Вы хотите добавить/удалить?'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('add_mailing', update.message.chat.username, text)
        return 1

    def what_company(self, update, context):  # определение компании
        company = update.message.text
        if self.ControlBD.check_company(company):
            context.user_data['company'] = company
            text = 'Какое сообщение хотите, чтоб отправлялось/удалялось?'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(company, update.message.chat.username, text)
            return 2
        else:
            text = 'Ошибка: компания с таким названием не найдена. ' \
                   'Уведомления для пользователей какой компании Вы хотите добавить/удалить?'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(company, update.message.chat.username, text)
            return 1

    def get_text_mailing(self, update, context):  # редактирование рассылки
        context.user_data['text'] = update.message.text
        text = f'В какую(-ые) даты отправлять или уведомления в какую дату удалить? ' \
               f'Вводите через запятую с пробелом, в формете день.месяц.год.'\
               f'Например: 25.05.2022, 23.02.2023'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)
        return 3

    def get_date_add(self, update, context):  # добавление рассылки
        date = update.message.text.split(', ')
        for i in date:
            self.ControlBD.add_mailing(context.user_data['text'], i, context.user_data['company'])
        text = 'Успешно! Уведомления ждут своей отправки.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(date, update.message.chat.username, text)
        return ConversationHandler.END

    def stop_new_mailing(self, update, context):  # завершение
        text = 'Добавление уведомления остановлено.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/stop', update.message.chat.username, text)
        return ConversationHandler.END

    def get_date_del(self, update, context):  # удаление даты
        date = update.message.text.split(', ')
        for i in date:
            self.ControlBD.delete_mailing(context.user_data['text'], i, context.user_data['company'])
        text = 'Успешно! Дата удалена.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(date, update.message.chat.username, text)
        return ConversationHandler.END

    def stop_del_mailing(self, update, context):  # завершение
        text = 'Удаление рассылки остановлено.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/stop', update.message.chat.username, text)
        return ConversationHandler.END

    def add_question(self, update, context):  # редактирование вопроса
        text = f'{self.ControlBD.get_user_name(str(update.message.from_user.id))}, введите вопрос,' \
               f' который нужно добавить/редактировать/удалить.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint('/add_question', update.message.chat.username, text)
        return 1

    def add_answer(self, update, context):  # редактирование вопроса
        context.user_data['question'] = update.message.text
        text = 'Введите ответ на вопрос.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)
        return 2

    def creating_question(self, update, context):  # редактирование вопроса
        context.user_data['answer'] = update.message.text
        text = 'Введите компанию, участники которой могут задать вопрос.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)
        return 3

    def write_question_add(self, update, context):  # добавление вопроса
        a = update.message.text
        self.ControlBD.add_question(context.user_data['question'], context.user_data['answer'], a)
        text = 'Вопрос добавлен.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END

    def stop_question_add(self, update, context):  # завершение
        text = 'Добавление/редактирование/удаление вопроса остановлено.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END

    def write_question_del(self, update, context):  # удаление вопроса
        context.user_data['company'] = update.message.text
        if self.ControlBD.check_question_all(context.user_data['question'], context.user_data['answer'],
                                             context.user_data['company']):
            self.ControlBD.delete_question(context.user_data['question'], context.user_data['answer'],
                                           context.user_data['company'])
        else:
            text = 'Ошибка: вопроса с такими характеристиками не существует.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(update.message.text, update.message.chat.username, text)
            text = 'Введите вопрос, который нужно добавить/редактировать/удалить.'
            context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
            self.pprint(update.message.text, update.message.chat.username, text)
            return 1
        text = 'Вопрос удален.'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=text)
        self.pprint(update.message.text, update.message.chat.username, text)
        return ConversationHandler.END

    def write_question_red(self, update, context):  # редактирование вопроса
        context.user_data['company'] = update.message.text
        if self.ControlBD.check_question(context.user_data['question'], context.user_data['company']):
            self.ControlBD.redact_question(context.user_data['question'], context.user_data['answer'],
                               update.message.text)
        else:
            update.message.reply_text('Ошибка: данного вопроса у данной компании не существует.')
            update.message.reply_text('Введите вопрос, который нужно добавить/редактировать/удалить.')
            return 1
        update.message.reply_text('Вопрос изменен.')
        return ConversationHandler.END


if __name__ == '__main__':
    a = Bot()
