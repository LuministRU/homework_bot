from array import array
import os
import logging
from shutil import ExecError

import requests

import time

from telegram import Bot, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Updater

from dotenv import load_dotenv

load_dotenv()


pr_token = os.getenv('PRACTIKUM_TOKEN')
t_token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 5
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {pr_token}'}


OLD_STATUSES = {}
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO)

def send_message(bot, message):
    try:
        bot.send_message(chat_id, message)
        logging.info(f'Бот отправил сообщение: {message}')
    except:
        logging.error('Бот не смог отправить сообщение')


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    status = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if status.status_code == 200:
        return status.json()
    else:
        logging.error(f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен. Код ответа API: {status.status_code}')
        raise Exception(f'Эндпоинт {ENDPOINT} недоступен. Код ответа API: {status.status_code}')


def check_response(response):
    homeworks = response.get('homeworks')
    if homeworks is not None:
        return homeworks
    else:
        logging.error('отсутствие ожидаемых ключей в ответе API')
        raise Exception('отсутствие ожидаемых ключей в ответе API')


def parse_status(homework):
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if OLD_STATUSES.get('homework_name') == homework.get('status'):
        logging.debug('Статус не изменен')
    else:
        if homework_status in HOMEWORK_STATUSES:
            OLD_STATUSES[homework_name] = homework_status
            verdict = HOMEWORK_STATUSES[homework_status]
            return (f'Изменился статус проверки работы "{homework_name}". {verdict}')
        else:
            logging.error(f'недокументированный статус домашней работы, обнаруженный в ответе API. Не нашел {homework_status}')
            raise Exception(f'недокументированный статус домашней работы, обнаруженный в ответе API. Не нашел {homework_status}')


def check_tokens():
    if pr_token != None and t_token != None and chat_id != None:
        return True
    elif pr_token is None:
        logging.critical('Отсутствует обязательная переменная окружения: PRACTIKUM_TOKEN')
        return False
    elif t_token is None:
        logging.critical('Отсутствует обязательная переменная окружения: TELEGRAM_TOKEN')
        return False
    elif chat_id is None:
        logging.critical('Отсутствует обязательная переменная окружения: TELEGRAM_CHAT_ID')
        return False


def main():
    """Основная логика работы бота."""

    if check_tokens() is False:
        print('Программа принудительно остановлена.')
        return 1

    bot = Bot(token=t_token)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = int(time.time())
            homeworks = check_response(response)

            for homework in homeworks:
                homework_status = parse_status(homework)
                send_message(bot, homework_status)
                time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        # else:
        #     logging.debug('Статус не изменен')


if __name__ == '__main__':
    main()
