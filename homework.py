import os
import logging
import requests
import time
from typing import Dict

from telegram import Bot

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_TIME = 5
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


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
    """Отправка сообщений."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Бот отправил сообщение: {message}')
    except Exception:
        logging.error('Бот не смог отправить сообщение')


def get_api_answer(current_timestamp):
    """Получение API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    status = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if status.status_code != requests.codes.ok:
        # return status.json()
        logging.error(f'Эндпоинт {ENDPOINT} недоступен. '
                      f'Код ответа API: {status.status_code}')
        raise Exception(f'Эндпоинт {ENDPOINT} недоступен. '
                        f'Код ответа API: {status.status_code}')
    return status.json()


def check_response(response):
    """Проверка ключей."""
    homeworks = response['homeworks']
    if homeworks is not None:
        if isinstance(homeworks, list):
            return homeworks
        logging.error('отсутствие ожидаемых ключей в ответе API')
        raise Exception('отсутствие ожидаемых ключей в ответе API')


def parse_status(homework):
    """Проверка статуса."""
    if not isinstance(homework, Dict):
        raise TypeError('Это не словарь!')
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('Имя не существует')
    homework_status = homework.get('status')
    if homework_status is None:
        raise KeyError('Статус не существует')
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        raise KeyError(f'Ошибка статуса {verdict}')
    logging.info(f'Новый статус работы. {verdict}')
    return (f'Изменился статус проверки работы "{homework_name}". {verdict}')


def check_tokens():
    """Проверка токенов."""
    no_token = None
    if PRACTICUM_TOKEN is None:
        no_token = 'PRACTICUM_TOKEN'
    if TELEGRAM_TOKEN is None:
        no_token = 'TELEGRAM_TOKEN'
    if TELEGRAM_CHAT_ID is None:
        no_token = 'TELEGRAM_CHAT_ID'
    if no_token is None:
        return True
    logging.critical(
        f'Отсутствует обязательная переменная окружения: {no_token}')
    return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.error('Программа принудительно остановлена.')
        raise Exception('Программа принудительно остановлена.')
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response['current_date']
            homeworks = check_response(response)
            for homework in homeworks:
                homework_status = parse_status(homework)
                send_message(bot, homework_status)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
