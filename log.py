import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
)


logging.debug('Статус не изменен')
logging.info('Бот отправил сообщение')
logging.warning('Большая нагрузка!')
logging.error('Сбой в работе программы: Эндпоинт https://practicum.yandex.ru/api/user_api/homework_statuses/111 недоступен. Код ответа API: 404')
logging.error('Бот не смог отправить сообщение')
logging.error('сбои при запросе к эендпоинту')
logging.error('отсутствие ожидаемых ключей в ответе API ')
logging.error('недокументированный статус домашней работы, обнаруженный в ответе API')
logging.critical('Отсутствует обязательная переменная окружения: { }') 