import telebot
import redis
import requests
from telebot.types import Message, ReplyKeyboardMarkup

from app.config import TOKEN, REDIS_HOST, REDIS_PORT
from app.markups import START_MARKUP, MENU, CONTINUE_MARKUP
from app.utils import create_user, get_word, set_answer, get_next_word, set_messages_ids, \
    remove_messages_by_ids, append_message_id_to_messages_ids
from app.text_messages import HELLO_TEXT, RIGHT_ANSWER_TEXT

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['help', 'start'])
def start_handler(message: Message) -> None:
    markup = ReplyKeyboardMarkup()
    user = message.from_user
    try:
        create_user(user)
    except requests.exceptions.ConnectionError:
        bot.send_message(message.chat.id, 'Что-то пошло не так, пожалуйста повторите попытку позже')
        return
    markup.add(*START_MARKUP)
    bot_message = bot.send_message(message.chat.id, HELLO_TEXT.format(user.first_name),
                                   reply_markup=markup)
    set_messages_ids([str(message.message_id), str(bot_message.message_id)], user.id)


@bot.message_handler(func=lambda message: message.text in MENU)
def get_right_answer_handler(message: Message) -> None:
    user = message.from_user
    with redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0) as r:
        word_id = r.get(f'{user.id}_word_id').decode('utf-8')
    markup = ReplyKeyboardMarkup()
    right_answer = get_word(word_id)
    text = RIGHT_ANSWER_TEXT.format(right_answer['word'], right_answer['transcription'],
                                    right_answer['translation'])
    markup.add(*CONTINUE_MARKUP)
    bot_message = bot.send_message(message.chat.id, text, reply_markup=markup)

    append_message_id_to_messages_ids(message.message_id, user.id)
    append_message_id_to_messages_ids(bot_message.message_id, user.id)


@bot.message_handler(func=lambda message: message.text in CONTINUE_MARKUP or message.text in START_MARKUP)
def continue_action_handler(message: Message) -> None:
    bot.delete_message(message.chat.id, message.message_id)
    remove_messages_by_ids(message.from_user.id, bot, message.chat.id)

    markup, translation = get_next_word(message, MENU)
    bot_message = bot.send_message(message.chat.id, translation, reply_markup=markup)

    set_messages_ids([str(bot_message.message_id)], message.from_user.id)


@bot.message_handler(func=lambda message: message)
def user_answer_handler(message: Message) -> None:
    user = message.from_user
    with redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0) as r:
        word = r.get(user.id)
        if word:
            word = word.decode('utf-8')
        word_id = r.get(f'{user.id}_word_id')
        text = set_answer(message.text, user, word, word_id)
        r.delete(user.id)
        r.delete(f'{user.id}_word_id')
    markup = ReplyKeyboardMarkup()
    markup.add(*CONTINUE_MARKUP)
    bot_message = bot.send_message(message.chat.id, text, reply_markup=markup)

    append_message_id_to_messages_ids(str(message.message_id), message.from_user.id)
    append_message_id_to_messages_ids(str(bot_message.message_id), message.from_user.id)


bot.polling(none_stop=True, interval=0)
