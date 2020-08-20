import requests
import shelve
import json

from telebot.types import ReplyKeyboardMarkup
from telebot.apihelper import ApiException
from telebot import TeleBot

from app.config import API_URL, STORAGE_FILENAME


def get_random_word(user):
    resp = requests.get(f'{API_URL}/words/random_word', headers={'Authorization': str(user.id)})
    if resp.status_code == 401:
        create_user(user)
        return get_random_word(user)
    return resp.json()


def get_word(word_id):
    resp = requests.get(f'{API_URL}/words/{word_id}')
    return resp.json()


def get_right_answer(user_id):
    with shelve.open(STORAGE_FILENAME) as db:
        return db.pop(f'{user_id}_word_id')


def create_user(user):
    requests.post(f'{API_URL}/users', json={'telegram_id': user.id,
                                            'username': user.username,
                                            'first_name': user.first_name,
                                            'last_name': user.last_name})


def check_answer(word, user, right_answer, word_id):
    if not right_answer:
        return f"Ой, что-то пошло не так, пожалуйста продолжайте, а мы попытаемся все исправить."
    if word == right_answer:
        requests.post(f'{API_URL}/words/answer', data={'word_id': word_id},
                      headers={'Authorization': str(user.id)})
        return "Правильно!"
    return f"Правильный ответ: {right_answer}"


def get_next_word(message, menu):
    user = message.from_user
    markup = ReplyKeyboardMarkup()
    word = get_random_word(user)
    markup.add(*word['variants'])
    markup.add(*menu)
    with shelve.open(STORAGE_FILENAME) as db:
        db[user.id] = word['word']['word']
        db[f'{user.id}_word_id'] = word['word']['id']
    return markup, word['word']['translation']


def remove_messages_by_ids(user_id: str, bot: TeleBot, chat_id: str):
    with shelve.open(STORAGE_FILENAME) as db:
        messages = json.loads(db.pop(f'{user_id}_messages', '[]'))
        for message in messages:
            try:
                bot.delete_message(chat_id, message)
            except ApiException:
                pass


def append_message_id_to_messages_ids(message, user_id):
    with shelve.open(STORAGE_FILENAME) as db:
        messages = json.loads(db.get(f'{user_id}_messages', '[]'))
        messages.append(message)
        db[f'{user_id}_messages'] = messages


def get_word_and_word_id(user_id):
    with shelve.open(STORAGE_FILENAME) as db:
        word = db.pop(user_id, None)
        word_id = db.pop(f'{user_id}_word_id', None)
        return word, word_id

