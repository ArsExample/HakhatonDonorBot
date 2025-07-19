import telebot
from telebot import types
import json

from excel import *
import config
import utils


token = config.BOT_TOKEN

bot = telebot.TeleBot(token)
#bot = telebot.TeleBot("7388219026:AAF3JMtLl2hU55FwSKfEFxVF3CLJpMarmV8")

# читаем файл с информацией:
f = open("messages.txt", encoding="utf-8").read().split("SPLITTER")
BLOOD_REQUIREMENTS = f[0]
BLOOD_PREPARATION = f[1]
BLOOD_FOOD = f[2]
BLOOD_ABSOLUTE_CONTRS = f[3]
BLOOD_TEMPORARY_CONTRS = f[4]
BACK_IMPORTANCE = f[5]
BACK_PROCEDURE = f[6]
MIFI_INFO = f[7]

questions = []  # вопросы админам типа {chat_id: id, question: question, express: false}, express - срочный ли вопрос


@bot.message_handler(['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Используя этот бот, вы соглашаетесь с политикой конфиденциальности:")
    bot.send_document(message.chat.id, open("privacy_policy.pdf", "rb"))
    bot.send_message(message.chat.id, "Введите номер телефона ✌")

@bot.message_handler(content_types=['text'])
def get_number(message):
    if message.text == "Личный кабинет":
        data = getUserByNumber(chat_id=message.chat.id)
        ikb = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton("Полная история", callback_data="full_donation_history")
        ikb.add(button)
        print(data)
        if data[0] and data[1] and data[8]:
            kd = data[4] if data[4] else "Донаций не было"
            kg = data[5] if data[5] else "Донаций не было"
            kf = data[6] if data[6] else "Донаций не было"
            bot.send_message(message.chat.id, f"ФИО: {data[0]}\nКоличество донаций: {kd}\n"
                                              f"Дата последней донации Гаврилова: {kg}\n"
                                              f"ЦК последней донации: Я ваще хз\n"  # TODO: где то взять эту донацию
                                              f"Дата последней донации ФМБА: {kf}\n"  
                                              f"Регистр ДКМ: А где это брать..")
        else:
            bot.send_message(message.chat.id, f"Сначала нужно авторизоваться!\n\nВведите свой номер телефона:")

    elif message.text == "Информация":  # TODO: сделать командами
        ikb = types.InlineKeyboardMarkup(row_width=1)
        buttonBlood = types.InlineKeyboardButton("Донорство крови", callback_data="blood_info")
        buttonBack = types.InlineKeyboardButton("Донорство костного мозга", callback_data="back_info")
        buttonMIFI = types.InlineKeyboardButton("Донорство в МИФИ", callback_data="mifi_info")
        ikb.add(buttonBlood, buttonBack, buttonMIFI)

        bot.send_message(message.chat.id, "Выберите интересующий вас раздел:", reply_markup=ikb)
    elif message.text == "Задать вопрос":
        def askExpress(message):
            ikb = types.InlineKeyboardMarkup(row_width=2)
            buttonYes = types.InlineKeyboardButton("Да", callback_data=f"express_question_yes-{message.text}")  #TODO: длинные строки....
            buttonNo = types.InlineKeyboardButton("Нет", callback_data=f"express_question_no-{message.text}")
            ikb.add(buttonYes, buttonNo)

            bot.send_message(message.chat.id, "Ваш вопрос срочный?", reply_markup=ikb)

        bot.send_message(message.chat.id, "Задайте ваш вопрос администратору:")
        bot.register_next_step_handler(message, askExpress)
    else:  #  TODO: если чат айди есть в бд то написать неверная команда, иначе регистрация
        number = utils.phone_validation(message.text)
        print(number)
        if number == "error":
            bot.send_message(message.chat.id, f"Похоже вы ввели неверный номер телефона🤨\nПопробуйте еще раз")
        else:
            data = getUserByNumber(number=number, chat_id=message.chat.id)
            if data:
                ikb = types.InlineKeyboardMarkup(row_width=2)
                buttonY = types.InlineKeyboardButton("Все правильно🤠", callback_data="login_good")
                buttonN = types.InlineKeyboardButton("Есть ошибка🥲", callback_data=f"login_error={str(data[-1])}")
                ikb.add(buttonY, buttonN)

                bot.send_message(message.chat.id, f"Убедитесь в правильности данных:\n\nФИО: {data[0]}", reply_markup=ikb)
            else:
                user = ["", "", "", "", "", "", "", "", message.text, str(message.chat.id)]

                def askFIO(message):

                    try:
                        r = createRow()
                        addPartRow(r, "FIO", message.text)
                        addPartRow(r, "phone", utils.phone_validation(user[8]))
                        addPartRow(r, "chat_id", user[9])

                        ikb = types.InlineKeyboardMarkup(row_width=2)
                        # print(f"r_st-{'='.join(message.text.split())}-{user[8]}")
                        # print(len(f"r_st-{'='.join(message.text.split())}-{user[8]}".encode(
                        #     "utf-8")))  # должно быть <= 64
                        buttonStudent = types.InlineKeyboardButton("Студент",
                                                                   callback_data=f"r_st-{r}")  # st = student, лимит в 64 байта памяти
                        buttonStaff = types.InlineKeyboardButton("Сотрудник МИФИ",
                                                                 callback_data=f"r_s-{r}")
                        buttonOut = types.InlineKeyboardButton("Внешний донор",
                                                               callback_data=f"r_o-{r}")
                        ikb.add(buttonStudent, buttonStaff, buttonOut)

                        bot.send_message(message.chat.id, "К какой группе вы относитесь?", reply_markup=ikb)
                    except Exception as e:
                        print(e)
                        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже(")


                bot.send_message(message.chat.id, f"Укажите свое ФИО:")
                bot.register_next_step_handler(message, askFIO)


@bot.callback_query_handler(func=lambda call: call.data == 'login_good')
def login_data_okey(call):
    chat_id = call.message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton("Личный кабинет")
    btn2 = types.KeyboardButton('Информация')
    btn3 = types.KeyboardButton('Записаться')
    btn4 = types.KeyboardButton('Задать вопрос')
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(chat_id, "Авторизация успешна!", reply_markup=markup)  # TODO: тут надо норм сообщение


@bot.callback_query_handler(func=lambda call: 'login_error' in call.data)
def login_data_error(call):
    chat_id = call.message.chat.id
    deleteRow(int(call.data.split("=")[1]))
    bot.send_message(chat_id, "Попробуем еще раз)\n\nВведите номер телефона:")


@bot.callback_query_handler(func=lambda call: call.data == 'registration_good')
def register(call):
    chat_id = call.message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton("Личный кабинет")
    btn2 = types.KeyboardButton('Информация')
    btn3 = types.KeyboardButton('Записаться')
    btn4 = types.KeyboardButton('Задать вопрос')
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(chat_id, "Регистрация успешна!", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: "registration_error" in call.data)
def registration_student_error(call):
    chat_id = call.message.chat.id
    try:
        deleteRow(int(call.data.split("=")[1]))
    except Exception as e:
        print(e)
    bot.send_message(chat_id, "Попробуем еще раз)\n\nВведите номер телефона:")


@bot.callback_query_handler(func=lambda call: "r_st" in call.data)
def registration_student(call):
    chat_id = call.message.chat.id
    r = call.data.split("-")[1]


    def askForStudentGroup(message):
        try:
            addPartRow(int(r), "group", message.text)

            user = getRow(r)
            ikb = types.InlineKeyboardMarkup(row_width=2)
            buttonY = types.InlineKeyboardButton("Все правильно🤠", callback_data="registration_good")
            buttonN = types.InlineKeyboardButton("Есть ошибка🥲", callback_data=f"registration_error={r}")
            ikb.add(buttonY, buttonN)
            bot.send_message(chat_id, f"Убедитесь в правильности данных:\n\n"
                                      f"Номер телефона: {user[8]}\n"
                                      f"ФИО: {user[0]}\n"
                                      f"Группа: {user[1]}", reply_markup=ikb)
        except Exception as e:
            print(f"adding data to DB error: {e}")
            bot.send_message(chat_id, f"Непредвиденная ошибка, попробуйте позже")



    bot.send_message(chat_id, "Укажите номер своей учебной группы:")
    bot.register_next_step_handler(call.message, askForStudentGroup)


@bot.callback_query_handler(func=lambda call: "r_s" in call.data)
def registration_staff(call):
    chat_id = call.message.chat.id
    r = call.data.split("-")[1]

    try:
        addPartRow(int(r), "group", "Сотрудник")

        user = getRow(r)
        ikb = types.InlineKeyboardMarkup(row_width=2)
        buttonY = types.InlineKeyboardButton("Все правильно🤠", callback_data="registration_good")
        buttonN = types.InlineKeyboardButton("Есть ошибка🥲", callback_data=f"registration_error={r}")
        ikb.add(buttonY, buttonN)
        bot.send_message(chat_id, f"Убедитесь в правильности данных:\n\n"
                                  f"Номер телефона: {user[8]}\n"
                                  f"ФИО: {user[0]}\n"
                                  f"Группа: {user[1]}", reply_markup=ikb)
    except Exception as e:
        print(f"adding data to DB error: {e}")
        bot.send_message(chat_id, f"Непредвиденная ошибка, попробуйте позже")


@bot.callback_query_handler(func=lambda call: "r_o" in call.data)
def registration_out(call):
    chat_id = call.message.chat.id
    r = call.data.split("-")[1]

    try:
        addPartRow(int(r), "group", "Внешний донор")

        user = getRow(r)
        ikb = types.InlineKeyboardMarkup(row_width=2)
        buttonY = types.InlineKeyboardButton("Все правильно🤠", callback_data="registration_good")
        buttonN = types.InlineKeyboardButton("Есть ошибка🥲", callback_data=f"registration_error={r}")
        ikb.add(buttonY, buttonN)
        bot.send_message(chat_id, f"Убедитесь в правильности данных:\n\n"
                                  f"Номер телефона: {user[8]}\n"
                                  f"ФИО: {user[0]}\n"
                                  f"Группа: {user[1]}", reply_markup=ikb)
    except Exception as e:
        print(f"adding data to DB error: {e}")
        bot.send_message(chat_id, f"Непредвиденная ошибка, попробуйте позже")


@bot.callback_query_handler(func=lambda call: call.data == 'full_donation_history')
def full_donations(call):
    chat_id = call.message.chat.id
    # TODO: вывести все сдачи (когда они в экселе будут)))


@bot.callback_query_handler(func=lambda call: call.data == 'blood_info')
def blood_info(call):
    chat_id = call.message.chat.id
    ikb = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("Требования к донорам", callback_data="blood_donation_requirements")
    button2 = types.InlineKeyboardButton("Подготовка к донации", callback_data="blood_donation_preparation")
    button3 = types.InlineKeyboardButton("Рацион питания", callback_data="blood_food_preparation")
    button4 = types.InlineKeyboardButton("Абсолютные противопоказания", callback_data="blood_absolute_contrs")
    button5 = types.InlineKeyboardButton("Временные противопоказания", callback_data="blood_temporary_contrs")
    ikb.add(button1, button2, button3, button4, button5)

    bot.send_message(chat_id, f"Выберите интересующий вас вопрос:", reply_markup=ikb)


@bot.callback_query_handler(func=lambda call: call.data == 'blood_donation_requirements')
def blood_donation_req(call):
    chat_id = call.message.chat.id
    ikb = types.InlineKeyboardMarkup(row_width=1)
    button_back = types.InlineKeyboardButton("Назад", callback_data="blood_info")
    ikb.add(button_back)
    bot.send_message(chat_id, BLOOD_REQUIREMENTS, reply_markup=ikb)


@bot.callback_query_handler(func=lambda call: call.data == 'blood_donation_preparation')
def blood_donation_req(call):
    chat_id = call.message.chat.id
    ikb = types.InlineKeyboardMarkup(row_width=1)
    button_back = types.InlineKeyboardButton("Назад", callback_data="blood_info")
    ikb.add(button_back)
    bot.send_message(chat_id, BLOOD_PREPARATION, reply_markup=ikb)


@bot.callback_query_handler(func=lambda call: call.data == 'blood_food_preparation')
def blood_donation_req(call):
    chat_id = call.message.chat.id
    ikb = types.InlineKeyboardMarkup(row_width=1)
    button_back = types.InlineKeyboardButton("Назад", callback_data="blood_info")
    ikb.add(button_back)
    bot.send_message(chat_id, BLOOD_FOOD, reply_markup=ikb)


@bot.callback_query_handler(func=lambda call: call.data == 'blood_absolute_contrs')
def blood_donation_req(call):
    chat_id = call.message.chat.id
    ikb = types.InlineKeyboardMarkup(row_width=1)
    button_back = types.InlineKeyboardButton("Назад", callback_data="blood_info")
    ikb.add(button_back)
    bot.send_message(chat_id, BLOOD_ABSOLUTE_CONTRS, reply_markup=ikb)


@bot.callback_query_handler(func=lambda call: call.data == 'blood_temporary_contrs')
def blood_donation_req(call):
    chat_id = call.message.chat.id
    ikb = types.InlineKeyboardMarkup(row_width=1)
    button_back = types.InlineKeyboardButton("Назад", callback_data="blood_info")
    ikb.add(button_back)
    bot.send_message(chat_id, BLOOD_TEMPORARY_CONTRS, reply_markup=ikb)


@bot.callback_query_handler(func=lambda call: call.data == 'back_info')
def back_info(call):
    chat_id = call.message.chat.id
    ikb = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("Важность", callback_data="back_importance")
    button2 = types.InlineKeyboardButton("Процедура донации", callback_data="back_procedure")
    ikb.add(button1, button2)

    bot.send_message(chat_id, f"Выберите интересующий вас вопрос:", reply_markup=ikb)


@bot.callback_query_handler(func=lambda call: call.data == 'back_importance')
def blood_donation_req(call):
    chat_id = call.message.chat.id
    ikb = types.InlineKeyboardMarkup(row_width=1)
    button_back = types.InlineKeyboardButton("Назад", callback_data="back_info")
    ikb.add(button_back)
    bot.send_message(chat_id, BACK_IMPORTANCE, reply_markup=ikb)


@bot.callback_query_handler(func=lambda call: call.data == 'back_procedure')
def blood_donation_req(call):
    chat_id = call.message.chat.id
    ikb = types.InlineKeyboardMarkup(row_width=1)
    button_back = types.InlineKeyboardButton("Назад", callback_data="back_info")
    ikb.add(button_back)
    bot.send_message(chat_id, BACK_PROCEDURE, reply_markup=ikb)


@bot.callback_query_handler(func=lambda call: call.data == 'mifi_info')  # TODO: дата ближайшего ДД
def mifi_info(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, MIFI_INFO)  # TODO: кнопка назад (информация)


@bot.callback_query_handler(func=lambda call: "express_question_yes" in call.data)
def express_question(call):
    chat_id = call.message.chat.id
    try:
        data = {"chat_id": chat_id, "question": call.data.split("-")[1], "express": True}

        with open(config.QUESTION_PATH, 'r') as file:
            rdata = json.load(file)

        rdata.append(data)

        with open(config.QUESTION_PATH, "w") as file:
            json.dump(rdata, file, indent=4)  # TODO: русские символы кодировать :))))))))))

        bot.send_message(chat_id, "Ваш вопрос направлен администратору и помечен как срочный.\n"
                                  "Администратор ответит на него в ближайшее время!")
    except Exception as e:
        print(f"Question adding error occured: {e}")
        bot.send_message(chat_id, "Произошла ошибка при отправке вопроса, попробуйте позже.")


@bot.callback_query_handler(func=lambda call: "express_question_no" in call.data)
def express_question(call):
    chat_id = call.message.chat.id
    try:
        data = {"chat_id": chat_id, "question": call.data.split("-")[1], "express": False}

        with open(config.QUESTION_PATH, 'r') as file:
            rdata = json.load(file)

        rdata.append(data)

        with open(config.QUESTION_PATH, "w") as file:
            json.dump(rdata, file, indent=4)

        bot.send_message(chat_id, "Ваш вопрос направлен администратору.\n"
                                  "Администратор ответит на него в ближайшее время!")
    except Exception as e:
        print(f"Question adding error occured: {e}")
        bot.send_message(chat_id, "Произошла ошибка при отправке вопроса, попробуйте позже.")


bot.polling(none_stop=True, interval=0)

