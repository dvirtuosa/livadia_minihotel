# Сервис бронирования номеров в мини-гостинице через телеграм бота

## Описание
Вебсайт сделан через конструктор [Tilda](https://tilda.cc/), на нём предоставлена информация о мини-гостинице и приведена ссылка на телеграм бота. Телеграм бот написан с использованием библиотеки [aiogram](https://github.com/aiogram/aiogram). Система управление базами данных - MySQL.


## Использование
Установка библиотек для телеграм бота

        pip install -r telegram_bot/requirements.txt

Или 

        source telegram_bot/telegram_bot_venv/bin/activate

Создание базы данных
В MySQL shell

        mysql> source mini_hotel_1_1_1.sql;



Параметры подключения к базе данных задаются в [manage_db.py](telegram_bot/manage_db.py), токен телеграм бота - в [new_bot.py](telegram_bot/manage_db.py).