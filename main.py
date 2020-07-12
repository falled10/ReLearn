import telebot
import redis
import requests
from telebot.types import Message, ReplyKeyboardMarkup

from app.config import TOKEN, REDIS_HOST, REDIS_PORT
from app.markups import START_MARKUP, MENU, CONTINUE_MARKUP
from app.utils import create_user, get_word, set_answer, get_next_word
from app.text_messages import HELLO_TEXT, RIGHT_ANSWER_TEXT

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['help', 'start'])
def create_new_user(message: Message) -> None:
    markup = ReplyKeyboardMarkup()
    bot.delete_message(message.chat.id, message.message_id)
    user = message.from_user
    try:
        create_user(user)
    except requests.exceptions.ConnectionError as e:
        bot.send_message(message.chat.id, 'Что-то пошло не так, пожалуйста повторите попытку позже')
        return
    markup.add(*START_MARKUP)
    bot.send_message(message.chat.id, HELLO_TEXT.format(user.first_name), reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in START_MARKUP)
def start_handler(message: Message) -> None:
    markup, translation = get_next_word(message, MENU)
    bot.send_message(message.chat.id, translation, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in MENU)
def get_right_answer(message: Message) -> None:
    user = message.from_user
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    markup = ReplyKeyboardMarkup()
    word = r.get(user.id).decode('utf-8')
    right_answer = get_word(word)
    text = RIGHT_ANSWER_TEXT.format(right_answer['word'], right_answer['transcription'],
                                    right_answer['translation'])
    markup.add(*CONTINUE_MARKUP)
    bot.send_message(message.chat.id, text, reply_markup=markup)
    r.close()


@bot.message_handler(func=lambda message: message.text in CONTINUE_MARKUP)
def handle_continue_action(message: Message) -> None:
    markup, translation = get_next_word(message, MENU)
    bot.send_message(message.chat.id, translation, reply_markup=markup)


@bot.message_handler(func=lambda message: message)
def set_user_answer(message: Message) -> None:
    user = message.from_user
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    word = r.get(user.id)
    if word:
        word = word.decode('utf-8')
    word_id = r.get(f'{user.id}_word_id')
    text = set_answer(message.text, user, word, word_id)
    markup = ReplyKeyboardMarkup()
    markup.add(*CONTINUE_MARKUP)
    bot.send_message(message.chat.id, text, reply_markup=markup)
    r.delete(user.id)
    r.delete(f'{user.id}_word_id')
    r.close()


bot.polling(none_stop=True, interval=0)
