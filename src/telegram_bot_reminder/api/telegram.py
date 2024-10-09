import logging.config
import os
import sqlite3
from datetime import datetime

import telebot
from dotenv import find_dotenv, load_dotenv

# Загрузка переменных окружения
load_dotenv(find_dotenv(usecwd=True))
BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    logging.error("BOT_TOKEN is not set in the environment variables.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Установка соединения с базой данных
conn = sqlite3.connect('reminders.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц, если они еще не созданы
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    reminder_text TEXT,
    reminder_time DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')

conn.commit()

# Временное хранилище для промежуточного ввода
temp_reminders = {}

# Команда для начала ввода нового напоминания
@bot.message_handler(commands=['enter_reminder'])
def enter_reminder(message):
    user_id = message.from_user.id
    username = message.from_user.username

    # Проверяем, есть ли пользователь в базе данных
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        # Добавляем нового пользователя
        cursor.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()

    msg = bot.send_message(message.chat.id, "Введите текст вашего напоминания:")
    bot.register_next_step_handler(msg, process_reminder_text)

# Обработка текста напоминания
def process_reminder_text(message):
    user_id = message.from_user.id
    reminder_text = message.text.strip()

    # Сохраняем текст напоминания во временное хранилище
    temp_reminders[user_id] = {'text': reminder_text}

    msg = bot.send_message(message.chat.id, "Введите дату и время напоминания в формате YYYY-MM-DD HH:MM:")
    bot.register_next_step_handler(msg, process_reminder_time)

# Обработка даты и времени напоминания
def process_reminder_time(message):
    user_id = message.from_user.id
    try:
        reminder_time = datetime.strptime(message.text.strip(), '%Y-%m-%d %H:%M')

        # Сохраняем дату и время напоминания
        temp_reminders[user_id]['time'] = reminder_time

        # Получаем текст напоминания из временного хранилища
        reminder_text = temp_reminders[user_id]['text']

        # Сохраняем напоминание в базу данных
        cursor.execute("INSERT INTO reminders (user_id, reminder_text, reminder_time) VALUES (?, ?, ?)", 
                       (user_id, reminder_text, reminder_time))
        conn.commit()

        bot.send_message(message.chat.id, f"Напоминание сохранено: '{reminder_text}' на {reminder_time}")
    except ValueError:
        msg = bot.send_message(message.chat.id, "Ошибка! Убедитесь, что дата и время введены в формате YYYY-MM-DD HH:MM.")
        bot.register_next_step_handler(msg, process_reminder_time)

# Команда для получения всех напоминаний
@bot.message_handler(commands=['get_reminders'])
def get_reminders(message):
    user_id = message.from_user.id

    # Получаем напоминания пользователя из базы данных
    cursor.execute("SELECT reminder_text, reminder_time FROM reminders WHERE user_id = ?", (user_id,))
    user_reminders = cursor.fetchall()

    if user_reminders:
        response = "Ваши напоминания:\n"
        for idx, (text, time) in enumerate(user_reminders, 1):
            response += f"{idx}. {text} - {time}\n"
    else:
        response = "У вас нет напоминаний."

    bot.send_message(message.chat.id, response)

# Команда для получения всех пользователей и их напоминаний (админ-команда)
@bot.message_handler(commands=['admin'])
def get_all_users_and_reminders(message):
    admin_id = message.from_user.id
    if admin_id:  # Замените YOUR_ADMIN_ID на ID администратора
        # SQL-запрос для получения всех пользователей и их напоминаний
        cursor.execute('''
            SELECT u.username, r.reminder_text, r.reminder_time
            FROM users u
            LEFT JOIN reminders r ON u.id = r.user_id
            ORDER BY u.username, r.reminder_time
        ''')
        all_data = cursor.fetchall()

        if all_data:
            response = "Все пользователи и их напоминания:\n"
            current_user = None
            for username, reminder_text, reminder_time in all_data:
                if current_user != username:
                    response += f"\nПользователь: {username}\n"
                    current_user = username
                if reminder_text and reminder_time:
                    response += f"- Напоминание: {reminder_text} на {reminder_time}\n"
                else:
                    response += "- Нет напоминаний.\n"
        else:
            response = "Нет пользователей или напоминаний."

        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")

# Запуск бота
bot.infinity_polling()

# Закрытие соединения с базой данных (опционально, при завершении работы бота)
# conn.close()
