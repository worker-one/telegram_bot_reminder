import logging.config
import os
from datetime import datetime

import telebot
import yaml
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

def load_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "..", "conf", "config.yaml")
    with open(config_path, encoding="utf-8") as file:
        return yaml.safe_load(file)


config = load_config()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    logging.error("BOT_TOKEN is not set in the environment variables.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

database = {}

class Birthday:
    def __init__(self):
        self.name = None
        self.birthday_date = None
        self.reminder_days = None
        self.gifts = None
        self.note = None


@bot.message_handler(commands=['help', 'start'])
def handle_help(message):
    help_text = config["description"]
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['enter_reminder'])
def handle_birthday(message):
    database[message.chat.id] = []
    msg = bot.reply_to(message, config['messages']['enter_name'])
    bot.register_next_step_handler(msg, process_name_step)

def process_name_step(message):
    birthday = Birthday()
    birthday.name = message.text
    msg = bot.reply_to(message, config['messages']['enter_birthday_date'])
    bot.register_next_step_handler(msg, process_birthday_date_step, birthday)

def process_birthday_date_step(message, birthday):
    try:
        datetime_input = datetime.strptime(message.text, "%d-%m-%Y").date()
        birthday.birthday_date = datetime_input
        msg = bot.reply_to(message, config['messages']['enter_reminder_days'])
        bot.register_next_step_handler(msg, process_reminder_days_step, birthday)
    except:
        msg = bot.reply_to(message, config["messages"]["wrong_dateime_format"])
        bot.register_next_step_handler(msg, process_birthday_date_step, birthday)


def process_reminder_days_step(message, birthday):
    birthday.reminder_days = message.text
    msg = bot.reply_to(message, config['messages']['enter_gifts'])
    bot.register_next_step_handler(msg, process_gifts_step, birthday)

def process_gifts_step(message, birthday):
    birthday.gifts = message.text
    msg = bot.reply_to(message, config['messages']['enter_note'])
    bot.register_next_step_handler(msg, process_note_step, birthday)

def process_note_step(message, birthday):
    birthday.note = message.text
    response = config['messages']['added_birthday'].format(
        name=birthday.name,
        birthday_date=birthday.birthday_date,
        reminder_days=birthday.reminder_days,
        gifts=birthday.gifts,
        note=birthday.note
    )
    database[message.chat.id].append(birthday)
    bot.reply_to(message, response)

@bot.message_handler(commands=['get_reminders'])
def handle_remind(message):
    birthdays = database.get(message.chat.id)
    if not birthdays:
        bot.send_message(message.chat.id, config['messages']['no_reminders'])
    else:
        bot.send_message(message.chat.id, config['messages']['your_reminders'])
        for birthday in birthdays:
            response = config['messages']['birthday_reminder'].format(
                name=birthday.name,
                birthday_date=birthday.birthday_date,
                reminder_days=birthday.reminder_days,
                gifts=birthday.gifts,
                note=birthday.note
            )
            bot.send_message(message.chat.id, response)

def send_birthday_reminder(bot):
    for chat_id in database:
        for birthday in database[chat_id]:
            now = datetime.now()
            birthday_date = datetime.strptime(birthday.birthday_date, "%Y-%m-%d")
            days_remaining = (birthday_date - now).days
            if days_remaining == int(birthday.reminder_days):
                response = config['messages']['birthday_reminder'].format(
                    name=birthday.name,
                    birthday_date=birthday.birthday_date,
                    days_remaining=birthday.reminder_days,
                    gifts=birthday.gifts,
                    note=birthday.note
                )
                bot.send_message(chat_id, response)


def start_bot():
    logging.info(f"bot `{str(bot.get_me().username)}` has started")
    bot.infinity_polling()
