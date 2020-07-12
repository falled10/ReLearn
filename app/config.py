from environs import Env


env = Env()
env.read_env()

TOKEN = env.str('TOKEN')
API_URL = env.str('API_URL')
REDIS_HOST = env.str('REDIS_HOST')
REDIS_PORT = env.str('REDIS_PORT')
