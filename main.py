import telebot
import requests

from telebot.types import Message, ReplyKeyboardMarkup

from app.config import TOKEN
from app.markups import START_MARKUP, MENU, CONTINUE_MARKUP
from app.utils import create_user, get_word, check_answer, get_next_word, \
    remove_messages_by_ids, append_message_id_to_messages_ids, get_word_and_word_id, get_right_answer
from app.text_messages import HELLO_TEXT, RIGHT_ANSWER_TEXT

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['help', 'start'])
def start_handler(message: Message) -> None:
    markup = ReplyKeyboardMarkup()
    user = message.from_user
    remove_messages_by_ids(message.from_user.id, bot, message.chat.id)
    try:
        create_user(user)
    except requests.exceptions.ConnectionError:
        bot.send_message(message.chat.id, 'Что-то пошло не так, пожалуйста повторите попытку позже')
        return
    markup.add(*START_MARKUP)
    bot_message = bot.send_message(message.chat.id, HELLO_TEXT.format(user.first_name),
                                   reply_markup=markup)
    append_message_id_to_messages_ids(message.message_id, user.id)
    append_message_id_to_messages_ids(bot_message.message_id, user.id)


@bot.message_handler(func=lambda message: message.text in MENU)
def get_right_answer_handler(message: Message) -> None:
    user = message.from_user
    word_id = get_right_answer(user.id)
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

    append_message_id_to_messages_ids(bot_message.message_id, message.from_user.id)


@bot.message_handler(func=lambda message: message)
def user_answer_handler(message: Message) -> None:
    user = message.from_user
    word, word_id = get_word_and_word_id(user.id)
    text = check_answer(message.text, user, word, word_id)
    markup = ReplyKeyboardMarkup()
    markup.add(*CONTINUE_MARKUP)
    bot_message = bot.send_message(message.chat.id, text, reply_markup=markup)

    append_message_id_to_messages_ids(str(message.message_id), message.from_user.id)
    append_message_id_to_messages_ids(str(bot_message.message_id), message.from_user.id)


bot.polling(none_stop=True, interval=0)
