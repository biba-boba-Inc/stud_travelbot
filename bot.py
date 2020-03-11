import telebot

bot = telebot.TeleBot('token')

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Добро пожаловать в TravelBot! Удачных путешествий!')
    bot.send_message(message.chat.id, 'Выберите страну:\r\n' \
    + 'Доступные страны:\r\nИталия\r\nTODO...')


@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.text == 'Италия':
        bot.send_message(message.chat.id, 'Не советуем вам сейчас путешествовать в италию monkaS')

bot.polling()