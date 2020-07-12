import requests
import redis
from telebot.types import ReplyKeyboardMarkup

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


def get_next_word(message, MENU):
    r = redis.Redis(host='localhost', port=REDIS_PORT, db=0)
    user = message.from_user
    markup = ReplyKeyboardMarkup()
    word = get_random_word(user)
    markup.add(*word['variants'])
    markup.add(*MENU)
    r.set(user.id, word['word']['word'])
    r.set(f'{user.id}_word_id', word['word']['id'])
    r.close()
    return markup, word['word']['translation']
