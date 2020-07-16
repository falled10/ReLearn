import requests
import redis
from telebot.types import ReplyKeyboardMarkup
from telebot import TeleBot

from app.config import API_URL, REDIS_HOST, REDIS_PORT


def get_random_word(user):
    resp = requests.get(f'{API_URL}/words/random_word', headers={'Authorization': str(user.id)})
    if resp.status_code == 401:
        create_user(user)
        return get_random_word(user)
    return resp.json()


def get_word(word):
    resp = requests.get(f'{API_URL}/words/{word}')
    return resp.json()


def create_user(user):
    requests.post(f'{API_URL}/users', json={'telegram_id': user.id,
                                            'username': user.username,
                                            'first_name': user.first_name,
                                            'last_name': user.last_name})


def set_answer(word, user, right_answer, word_id):
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
    with redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0) as r:
        r.set(user.id, word['word']['word'])
        r.set(f'{user.id}_word_id', word['word']['id'])
    return markup, word['word']['translation']


def set_messages_ids(messages: list, user_id: int):
    with redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0) as r:
        r.set(f'{user_id}_messages', ','.join(messages))


def remove_messages_by_ids(user_id: str, bot: TeleBot, chat_id: str):
    with redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0) as r:
        messages = r.get(f'{user_id}_messages')
        if messages:
            messages = messages.decode('utf-8').split(',')
            for message in messages:
                bot.delete_message(chat_id, message)


def append_message_id_to_messages_ids(message, user_id):
    with redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0) as r:
        messages = r.get(f'{user_id}_messages')
        if messages:
            r.set(f'{user_id}_messages', messages.decode('utf-8') + f',{message}')
