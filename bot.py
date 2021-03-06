import telebot
import sqlite3
import os
import random

bot = telebot.TeleBot('token')

db = sqlite3.connect("zabase.db")
cursor = db.cursor()

countries = []
for row in cursor.execute("SELECT name FROM country ORDER BY name"):
    countries.append(row[0])

users = {}
for row in cursor.execute("SELECT user_id, country, city FROM userinfo"):
    users[row[0]] = {"country": row[1], "city": row[2]}

cursor.close()
db.close()

@bot.message_handler(commands=['start'])
def start_message(message):
    if str(message.from_user.id) in globals()['users']:
        return
    #countries = globals()['countries']
    #s = ""
    #for i in countries:
    #    s += i + '\r\n'

    showctrs = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    showctrs.row('Вывести список стран')

    bot.send_message(message.chat.id, 'Добро пожаловать в TravelBot! Удачных путешествий!')
    bot.send_message(message.chat.id, 'Выберите страну', reply_markup=showctrs)
    #bot.send_message(message.chat.id, 'Выберите страну:\r\nДоступные страны:\r\n' + s[:-2])


@bot.message_handler(content_types=['text'])
def send_text(message):
    countries, users = globals()['countries'], globals()['users']
    db = sqlite3.connect("zabase.db")
    cursor = db.cursor()

    text = message.text.strip().capitalize()
    iden = str(message.from_user.id)

    markup0 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup0.row('Вернуться к выбору страны')
    markup0.row('Вывести список городов')

    markup1 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup1.row('Вернуться к выбору страны', 'Вернуться к выбору города')
    markup1.row('Вывести список достопримечательностей')
    markup1.row('Вывести случайную достопримечательность')

    if iden not in users:
        cursor.execute("INSERT INTO userinfo(user_id) VALUES(?)", [(iden)])
        db.commit()
        globals()['users'][iden] = users[iden] = {"country": None, "city": None}

    if not users[iden]["country"] and text == "Вывести список стран":
        pages = telebot.types.InlineKeyboardMarkup()
        
        btns = []
        btns.append(telebot.types.InlineKeyboardButton(text="*1*", callback_data="nope"))

        for i in range(1, len(countries)+1):
            if i % 10 == 0 and i < 40:
                btns.append(telebot.types.InlineKeyboardButton(text=str(i//10+1), callback_data=str(i//10+1)+'c'))
            elif i > 40:
                btns.append(telebot.types.InlineKeyboardButton(text=str(len(countries)//10+1),
                    callback_data=str(len(countries)//10+1)+'c'))
                break

        pages.add(*btns)

        page = 0
        stop = len(countries) if page*10+10 > len(countries) else page*10+10

        s = ""
        for i in range(page*10, stop):
            s += countries[i] + '\r\n'

        bot.send_message(message.chat.id, 'Список стран:\r\n\r\n{}'.format(s), reply_markup=pages)
        return

    elif not users[iden]["country"] and text not in countries:
        bot.send_message(message.chat.id, 'Страны \'{}\' не существует или не внесена в нашу базу('.format(message.text))
        return

    elif not users[iden]["country"]:
        globals()['users'][iden] = {"country": text, "city": None}
        cursor.execute("UPDATE userinfo SET country=? WHERE user_id=?", [(text), (iden)])
        bot.send_message(message.chat.id, 'Выбрана страна {}\r\nВыберите город'.format(text), reply_markup=markup0)
        db.commit()
        return

    if users[iden]["country"] and text == "Вывести список городов":
        rows = [x[0] for x in list(cursor.execute('''SELECT city.name FROM city JOIN country c ON ctr_id = c.id
        WHERE c.name=? ORDER BY city.name''', [(users[iden]["country"])]))]

        pages = telebot.types.InlineKeyboardMarkup()
        
        btns = []
        btns.append(telebot.types.InlineKeyboardButton(text="*1*", callback_data="nope"))

        for i in range(1, len(rows)+1):
            if i % 10 == 0 and i < 40:
                btns.append(telebot.types.InlineKeyboardButton(text=str(i//10+1), callback_data=str(i//10+1)+'ci'))
            elif i > 40:
                btns.append(telebot.types.InlineKeyboardButton(text=str(len(rows)//10+1),
                    callback_data=str(len(rows)//10+1)+'ci'))
                break

        pages.add(*btns)

        page = 0
        stop = len(rows) if page*10+10 > len(rows) else page*10+10

        s = ""
        for i in range(page*10, stop):
            s += rows[i] + '\r\n'

        bot.send_message(message.chat.id, 'Список городов:\r\n\r\n{}'.format(s), reply_markup=pages)
        return

    elif users[iden]["country"] and text == "Вернуться к выбору страны":
        globals()["users"][iden]["country"] = None
        cursor.execute("UPDATE userinfo SET country=NULL WHERE user_id=?", [(iden)])

        showctrs = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        showctrs.row('Вывести список стран')

        bot.send_message(message.chat.id, 'Выберите страну', reply_markup=showctrs)
        db.commit()
        return
    
    elif users[iden]["country"] and not users[iden]["city"]:
        city = cursor.execute('''SELECT city.name FROM city JOIN country c ON ctr_id = c.id
        WHERE city.name=? AND c.name=?''', [(text), (users[iden]["country"])]).fetchone()
        if not city:
            bot.send_message(message.chat.id,
                'Города \'{}\' не существует или он не внесен в нашу базу('.format(message.text))
        else:
            s = ""
            globals()["users"][iden]["city"] = text
            cursor.execute("UPDATE userinfo SET city=? WHERE user_id=?", [(text), (iden)])
            for row in cursor.execute('''SELECT u.name FROM unit u JOIN city c ON city_id = c.id
            WHERE c.name=?''', [(text)]):
                s += row[0] + '\r\n'
            bot.send_message(message.chat.id, 'Выбран город {}'.format(text), reply_markup=markup1)
            db.commit()
        return

    if users[iden]["city"] and text == "Вывести список достопримечательностей":
        rows = [x[0] for x in list(cursor.execute('''SELECT u.name FROM unit u JOIN city c ON city_id = c.id
            WHERE c.name=?''', [(users[iden]["city"])]))]

        if len(rows) == 0:
            bot.send_message(message.chat.id, 'В нашей базе данных еще нет достопримечательностей в выбранном городе')
        else:
            pages = telebot.types.InlineKeyboardMarkup()
            
            btns = []
            btns.append(telebot.types.InlineKeyboardButton(text="*1*", callback_data="nope"))

            for i in range(1, len(rows)+1):
                if i % 10 == 0 and i < 40:
                    btns.append(telebot.types.InlineKeyboardButton(text=str(i//10+1), callback_data=str(i//10+1)+'s'))
                elif i > 40:
                    btns.append(telebot.types.InlineKeyboardButton(text=str(len(rows)//10+1),
                        callback_data=str(len(rows)//10+1)+'s'))
                    break

            pages.add(*btns)

            page = 0
            stop = len(rows) if page*10+10 > len(rows) else page*10+10

            s = ""
            for i in range(page*10, stop):
                s += rows[i] + '\r\n'

            bot.send_message(message.chat.id, 'Список достопримечательностей:\r\n\r\n{}'.format(s), reply_markup=pages)
        return

    elif users[iden]["city"] and text == "Вернуться к выбору города":
        globals()["users"][iden]["city"] = None
        cursor.execute("UPDATE userinfo SET city=NULL WHERE user_id=?", [(iden)])
        s = ""
        for row in cursor.execute('''SELECT city.name FROM city JOIN country c ON ctr_id = c.id
        WHERE c.name=?''', [(users[iden]["country"])]):
            s += row[0] + '\r\n'
        bot.send_message(message.chat.id,
        'Выбрана страна {}\r\nВыберите город:\r\n{}'.format(users[iden]["country"], s[:-2]), reply_markup=markup0)
        db.commit()
        return

    elif users[iden]["city"] and text == "Вывести случайную достопримечательность":
        count = cursor.execute('''SELECT COUNT(u.id) FROM unit u
        JOIN city c ON u.city_id=c.id WHERE c.name=?''', [(users[iden]["city"])]).fetchone()[0]
        
        if count == 0:
            bot.send_message(message.chat.id, "В нашей базе данных еще нет достопримечательностей в выбранном городе")
        else:
            unit = list(cursor.execute('''SELECT name, description, photo, location
            FROM unit WHERE id=?''', [(random.randint(1, count))]).fetchone())

            if not unit[3]:
                loc = ''
            else:
                loc = '<a href=\"https://maps.google.com/?q={}\">Показать на карте</a>'.format(unit[3])

            if not unit[2]:
                bot.send_message(message.chat.id, '{}\r\n\r\n{}\r\n\r\n{}'.format(unit[0], unit[1], loc), parse_mode='HTML')
            else:
                try:
                    bot.send_photo(message.chat.id, open(unit[2], 'rb'),
                    '{}\r\n\r\n{}\r\n\r\n{}'.format(unit[0], unit[1], loc), parse_mode='HTML')
                except FileNotFoundError:
                    bot.send_photo(message.chat.id, unit[2],'{}\r\n\r\n{}\r\n\r\n{}'.format(unit[0], unit[1], loc), parse_mode='HTML')
        return

    elif users[iden]["city"]:
        unit = cursor.execute('''SELECT u.name, description, photo, location
        FROM unit u JOIN city c ON city_id=c.id
        WHERE u.name=? AND c.name=?''', [(message.text), (users[iden]["city"])]).fetchone()

        if not unit:
            bot.send_message(message.chat.id, 
            'Достопримечательности \'{}\' не существует или она не внесена в нашу базу('.format(message.text))
        else:
            unit = list(unit)

            if not unit[3]:
                loc = ''
            else:
                loc = '<a href=\"https://maps.google.com/?q={}\">Показать на карте</a>'.format(unit[3])

            if not unit[2]:
                bot.send_message(message.chat.id, '{}\r\n\r\n{}\r\n\r\n{}'.format(unit[0], unit[1], loc), parse_mode='HTML')
            else:
                try:
                    bot.send_photo(message.chat.id, open(unit[2], 'rb'),
                    '{}\r\n\r\n{}\r\n\r\n{}'.format(unit[0], unit[1], loc), parse_mode='HTML')
                except FileNotFoundError:
                    bot.send_photo(message.chat.id, unit[2],'{}\r\n\r\n{}\r\n\r\n{}'.format(unit[0], unit[1], loc), parse_mode='HTML')
        return


@bot.callback_query_handler(func=lambda query: True)
def callback_answer(query):
    if query.message:
        bot.answer_callback_query(query.id)
        if query.data == "nope":
            return

        db = sqlite3.connect("zabase.db")
        cursor = db.cursor()
        iden = str(query.from_user.id)

        page = int(query.data[0])

        if query.data[-1] == 'c':
            l = globals()["countries"]
            table, word = 'c', 'стран'
        elif query.data[-2:] == 'ci':
            l = [x[0] for x in list(cursor.execute('''SELECT city.name FROM city JOIN country c ON ctr_id = c.id
        WHERE c.name=? ORDER BY city.name''', [(users[iden]["country"])]))]
            table, word = 'ci', 'городов'
        elif query.data[-1] == 's':
            l = [x[0] for x in list(cursor.execute('''SELECT u.name FROM unit u JOIN city c ON city_id = c.id
            WHERE c.name=?''', [(users[iden]["city"])]))]
            table, word = 's', 'достопримечательностей'

        pages = telebot.types.InlineKeyboardMarkup()

        btns = []
        
        if page != 1:
            btns.append(telebot.types.InlineKeyboardButton(text=str(1), callback_data="1"+table))
        if page > 2:
            btns.append(telebot.types.InlineKeyboardButton(text=str(page-1), callback_data=str(page-1)+table))
        btns.append(telebot.types.InlineKeyboardButton(text="*{}*".format(page), callback_data="nope"))
        if len(l) >= page*10:
            btns.append(telebot.types.InlineKeyboardButton(text=str(page+1), callback_data=str(page+1)+table))
        if len(l) >= (page+1) * 10:
            btns.append(telebot.types.InlineKeyboardButton(text=str(len(l)//10+1), callback_data=str(len(l)//10+1)+table))

        pages.add(*btns)

        page -= 1
        stop = len(l) if page*10+10 > len(l) else page*10+10

        s = ""
        for i in range(page*10, stop):
            s += l[i] + '\r\n'

        bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
            text='Список {}:\r\n\r\n{}'.format(word, s), reply_markup=pages)

bot.polling()