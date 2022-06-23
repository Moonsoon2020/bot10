from datetime import datetime
import sqlite3


class DB:  # Класс для работы с Базой Данных
    def __init__(self):  # инициализация класса
        self.con = sqlite3.connect('db_For_TGbot.sqlite', check_same_thread=False)  # подключение БД
        create_table1 = """CREATE TABLE IF NOT EXISTS Users (
    id         INTEGER PRIMARY KEY
                       UNIQUE
                       NOT NULL,
    surname    TEXT    NOT NULL,
    name       TEXT    NOT NULL,
    patronymic TEXT,
    post       BOOLEAN NOT NULL,
    company    TEXT,
    id_tg      TEXT    NOT NULL
);"""
        create_table2 = """CREATE TABLE IF NOT EXISTS Questions (
    id      INTEGER PRIMARY KEY
                    UNIQUE
                    NOT NULL,
    text_q  TEXT    NOT NULL,
    text_a  TEXT    NOT NULL,
    company TEXT    NOT NULL
);"""
        create_table3 = """CREATE TABLE IF NOT EXISTS Mailings (
    id      INTEGER PRIMARY KEY
                    UNIQUE
                    NOT NULL,
    text    TEXT    NOT NULL,
    date    TEXT    NOT NULL,
    company TEXT    NOT NULL
);"""
        create_table4 = """CREATE TABLE IF NOT EXISTS Companies (
    id           INTEGER PRIMARY KEY
                         UNIQUE
                         NOT NULL,
    title        TEXT    NOT NULL
                         UNIQUE,
    number_phone TEXT,
    password_cl  TEXT    NOT NULL
);"""
        self.con.cursor().execute(create_table1)  # создание отсутствующих и необходимых таблиц
        self.con.cursor().execute(create_table2)
        self.con.cursor().execute(create_table3)
        self.con.cursor().execute(create_table4)
        self.con.commit()

    def add_user(self, surname, name, patronymic, post, id_tg):
        """ добавление пользователя """
        self.con.cursor().execute(f'''INSERT INTO Users(surname, name, patronymic, post, id_tg)
         VALUES ('{surname}', '{name}', '{patronymic}', {post}, '{id_tg}')''')
        self.con.commit()

    def add_company(self, title, phone, password):
        """ добавление компании """
        self.con.cursor().execute(f'''INSERT INTO Companies(title, number_phone, password_cl)
         VALUES ('{title}', '{phone}', '{password}')''')
        self.con.commit()

    def delete_company(self, title):
        """ удаление компании """
        self.con.cursor().execute(f'''DELETE from Companies 
        WHERE title = \'{title}\'''')
        self.con.cursor().execute(f'''DELETE from Mailings
                WHERE company = \'{title}\'''')
        self.con.cursor().execute(f'''DELETE from Questions
                WHERE company = \'{title}\'''')
        self.con.cursor().execute(f'''UPDATE Users
                SET company = ''
                WHERE company = \'{title}\'''')
        self.con.commit()

    def check_mailing(self, text, date, company):
        """ проверка наличия уведомления """
        if self.con.cursor().execute(f'''SELECT count(*) FROM Mailings
         WHERE text = '{text}' AND
          date = '{date}' AND
           company = \'{company}\'''').fetchall()[0][0] != 0:
            return True
        else:
            return False

    def add_mailing(self, text, date, company):
        """ добавление уведомления """
        self.con.cursor().execute(f'''INSERT INTO Mailings(text, date, company)
         VALUES ('{text}', '{date}', '{company}')''')
        self.con.commit()

    def delete_mailing(self, text, date, company):
        """ удаление уведомления """
        self.con.cursor().execute(f'''DELETE from Mailings 
        WHERE text = '{text}' AND
          date = '{date}' AND
           company = \'{company}\'''')
        self.con.commit()

    def check_question_all(self, text_q, text_a, company):
        """ проверка вопроса на полную уникальность """
        if self.con.cursor().execute(f'''SELECT count(*) FROM Questions
         WHERE text_q = '{text_q}' AND
          text_a = '{text_a}' AND
           company = \'{company}\'''').fetchall()[0][0] != 0:
            return True
        else:
            return False

    def add_question(self, text_q, text_a, company):
        """ добавление вопроса """
        self.con.cursor().execute(f'''INSERT INTO Questions(text_q, text_a, company)
                 VALUES ('{text_q}', '{text_a}', '{company}')''')
        self.con.commit()

    def check_question(self, text_q, company):
        """ проверка вопроса на существование """
        if self.con.cursor().execute(f'''SELECT count(*) FROM Questions
         WHERE text_q = '{text_q}' AND
           company = \'{company}\'''').fetchall()[0][0] != 0:
            return True
        else:
            return False

    def redact_question(self, text_q, text_a, company):
        """ редактирование вопроса """
        self.con.cursor().execute(f'''UPDATE Questions
        SET text_a = '{text_a}'
         WHERE text_q = '{text_q}' AND
           company = \'{company}\'''')
        self.con.commit()

    def delete_question(self, text_q, text_a, company):
        """ удаление вопроса """
        self.con.cursor().execute(f'''DELETE from Questions
                 WHERE text_q = '{text_q}' AND
                  text_a = '{text_a}' AND
                   company = \'{company}\'''')
        self.con.commit()

    def get_questions(self, company):
        """ получение всех вопросов для данной компании """
        return [x for x in enumerate(self.con.cursor().execute(f'''SELECT text_q FROM Questions
         WHERE company = \'{company}\'''').fetchall())]

    def get_company_password(self, company):
        """ получение пароля для клиентов компании """
        return self.con.cursor().execute(f'''SELECT password_cl FROM Companies
         WHERE title = \'{company}\'''').fetchall()[0][0]

    def check_company(self, company):
        """ проверка компании на существование """
        if self.con.cursor().execute(f'''SELECT count(*) FROM Companies
         WHERE title = \'{company}\'''').fetchall()[0][0] != 0:
            return True
        else:
            return False

    def remove_user_company(self, id_tg, company):
        """ редактирование принадлежности пользователя к компании """
        self.con.cursor().execute(f'''UPDATE Users
                SET company = '{company}'
                 WHERE id_tg = \'{id_tg}\'''')
        self.con.commit()

    def check_user_company(self, id_tg):
        """ проверка принадлежности пользователя к компании """
        if self.con.cursor().execute(f'''SELECT company FROM Users
         WHERE id_tg = \'{id_tg}\'''').fetchall()[0][0] not in [None, '']:
            return True
        else:
            return False

    def get_answer(self, question, company):
        """ получение ответа на вопрос """
        return self.con.cursor().execute(f'''SELECT text_a FROM Questions
         WHERE company = '{company}' AND
         text_q = \'{question}\'''').fetchall()[0][0]

    def get_ids(self, company):
        """ получение всех айди пользователей данной компании """
        return [x[0] for x in self.con.cursor().execute(f'''SELECT id_tg FROM Users
         WHERE company = \'{company}\'''').fetchall()]

    def get_mailings(self):
        """ получение всех рассылок на сегодня """
        day = datetime.today().strftime('%d.%m.%Y')
        return [(x[0], self.get_ids(x[1])) for x in self.con.cursor().execute(f'''SELECT text, company FROM Mailings
                WHERE date = \'{day}\'''').fetchall()]

    def remove_user_post(self, id_tg):
        """"""
        post = self.get_user_post(id_tg)
        if post == 1:
            post = 0
        else:
            post = 1
        self.con.cursor().execute(f'''UPDATE Users SET post = {post} WHERE id_tg = \'{id_tg}\'''')
        self.con.commit()

    def get_user_post(self, id_tg):
        """ получение должности пользователя """
        return self.con.cursor().execute(f'''SELECT post FROM Users
                 WHERE id_tg = \'{id_tg}\'''').fetchall()[0][0]

    def get_user_company(self, id_tg):
        """ получение компании, в которой находится пользователь """
        return self.con.cursor().execute(f'''SELECT company FROM Users
                 WHERE id_tg = \'{id_tg}\'''').fetchall()[0][0]

    def get_user_name(self, id_tg):
        """ получение имя пользователя """
        return self.con.cursor().execute(f'''SELECT name FROM Users
                 WHERE id_tg = \'{id_tg}\'''').fetchall()[0][0]

    def edit_user_post(self, post, id_tg):
        """ редактирование роли """
        self.con.cursor().execute(f'''UPDATE Users
        SET post = {post}
         WHERE id_tg = \'{id_tg}\'''')
        self.con.commit()

    def get_info_for_file(self):
        """ получение данных для формирования таблицы """
        itog = []
        users = 'Пользователи', [
            ('Фaмилия', 'Имя', 'Отчество', 'Должность(1-админ, 0-клиент)', 'Компания')] + self.con.cursor().execute(f'''SELECT surname, name, patronymic,
post, company FROM Users''').fetchall()
        itog.append(users)
        companies = 'Компании', [
            ('Название компании', 'Номер телефона', 'Пароль для сотрудников')] + \
                    self.con.cursor().execute(f'''SELECT title, number_phone,
password_cl FROM Companies''').fetchall()
        itog.append(companies)
        mailings = 'Уведомления', [
            ('Сообщение', 'Дата отправления', 'Для сотрудников компании...')] + \
                   self.con.cursor().execute(f'''SELECT text, date,
company FROM Mailings''').fetchall()
        itog.append(mailings)
        questions = 'Вопросы', [
            ('Вопрос', 'Ответ', 'Для сотрудников компании...')] + \
                    self.con.cursor().execute(f'''SELECT text_q, text_a,
company FROM Questions''').fetchall()
        itog.append(questions)
        return itog

# Тест функций
# bd = DB()
# print(bd.get_info_for_file())
# print(bd.get_user_company('1234wer'))
# print(bd.get_user_post('1234wer'))
# bd.add_company('a', 'b', 'c')
# bd.add_user('a', 'b', 'c', 1, '1234wer')
# bd.delete_company('A')
# bd.add_mailing('b', '15.04.2022', 'A')
# print(bd.check_mailing('a', '01.01.01', 'A'))
# bd.delete_mailing('a', '01.01.01', 'A')
# bd.add_question('a3', 'b4', 'Comp')
# print(bd.check_question_all('a', 'b', 'c'))
# bd.redact_question('a', 'b', 'c')
# bd.delete_question('a', 'b', 'c')
# print(bd.check_question('a', 'c'))
# print(bd.get_questions('Фантом Десятой'))
# print(bd.get_company_password('a'))
# print(bd.check_company('Артемка'))
# bd.remove_user_company('1234wer', 'A')
# print(bd.check_user_company('12432wer'))
# print(bd.get_answer('a3', 'Comp'))
# print(bd.get_ids('A'))
# print(bd.get_mailings())
# print(bd.get_user_name('1925398093'))