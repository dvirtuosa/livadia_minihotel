import logging
import time

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor

import manage_db

logging.basicConfig(level=logging.INFO)

API_TOKEN = '' # Paste telegram token here


bot = Bot(token=API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    name = State()  # Will be represented in storage as 'Form:name'
    phone = State()  # Will be represented in storage as 'Form:phone'
    room_type = State()  # Will be represented in storage as 'Form:room_type'
    arrival_date = State() # Will be represented in storage as 'Form:arrival_date'
    departure_date = State() # Will be represented in storage as 'Form:departure_date'

class Form2(StatesGroup):
    room_type = State()
    arrival_date = State()
    departure_date = State()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    button_book = types.KeyboardButton('Забронировать.')
    button_check = types.KeyboardButton('Проверить количество свободных номеров.')
    book_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    book_kb.add(button_book)
    book_kb.add(button_check)
    
    await message.reply("Телеграм бот для бронирования номеров в мини-гостинице \"Ливадия\"", reply_markup = book_kb)

@dp.message_handler(lambda m: m.text == "Проверить количество свободных номеров.")
async def cmd_start1(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Двухместный", "Трехместный")
    markup.add("Четырехместный")

    await Form2.room_type.set()

    await message.reply("Выберите тип номера.", reply_markup = markup)

@dp.message_handler(lambda message: message.text not in ["Двухместный", "Трехместный", "Четырехместный"], state=Form2.room_type)
async def check_room_type_invalid(message: types.Message):
    return await message.reply("Неправильный тип комнаты. Выберите ответ кнопкой.")


@dp.message_handler(state=Form2.room_type)
async def check_room_type(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['room_type'] = message.text

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()

        await Form2.next()

        await message.reply("Введите дату заезда в формате dd.mm.yyyy", reply_markup = markup)

@dp.message_handler(state=Form2.arrival_date)
async def сheck_arrival_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
          try:
              arr = time.strptime(message.text, '%d.%m.%Y')

              if not(arr > time.localtime()):
                raise ValueError

          except ValueError:
              return await message.reply("Некорректный ввод даты.\n")

          data['arrival_date'] = message.text

          await Form2.next()

          await message.reply("Введите дату выезда в формате dd.mm.yyyy")

@dp.message_handler(state=Form2.departure_date)
async def check_departure_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
          try:
              dep = time.strptime(message.text, '%d.%m.%Y')

              if not (dep > time.strptime(data['arrival_date'], '%d.%m.%Y')):
                  raise ValueError

          except ValueError:
              return await message.reply("Некорректный ввод даты.\n")

          data['departure_date'] = message.text

          await state.finish()

          args = [data["room_type"], data["arrival_date"], data["departure_date"]]
          is_free, n_of_free = manage_db.handle(args)


          button_book = types.KeyboardButton('Забронировать.')
          button_check = types.KeyboardButton('Проверить количество свободных номеров.')
          book_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
          book_kb.add(button_book)
          book_kb.add(button_check)

          if is_free:
            await message.answer(f"Свободных номеров по заданным параметрам: {n_of_free}", reply_markup=book_kb)

          else:
            await message.answer("Свободных номеров - (ЛСП) нет.", reply_markup=book_kb)

@dp.message_handler(lambda m: m.text == "Забронировать.")
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """

    markup = types.ReplyKeyboardRemove()

    # Set state
    await Form.name.set()

    await message.reply("Введите ваше полное имя.", reply_markup = markup)

# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    
    button_book = types.KeyboardButton('Забронировать.')
    button_check = types.KeyboardButton('Проверить количество свободных номеров.')
    book_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    book_kb.add(button_book)
    book_kb.add(button_check)

    await message.reply('Отмена брони.', reply_markup=book_kb)


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process user name
    """
    async with state.proxy() as data:
        data['name'] = message.text

    await Form.next()
    await message.reply("Введите ваш номер телефона в международном формате (без +7).")


# Check phone. Phone gotta be digit
@dp.message_handler(lambda message: ((not message.text.isdigit()) or (len(message.text) != 10)), state=Form.phone)
async def process_phone_invalid(message: types.Message):
    """
    If phone is invalid
    """
    return await message.reply("Номер должен содержать только цифры (ровно 10).\n")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    # Update state and data
    await Form.next()
    await state.update_data(phone=int(message.text))

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Двухместный", "Трехместный")
    markup.add("Четырехместный")

    await message.reply("Выберите тип номера.", reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["Двухместный", "Трехместный", "Четырехместный"], state=Form.room_type)
async def process_room_type_invalid(message: types.Message):
    return await message.reply("Неправильный тип комнаты. Выберите ответ кнопкой.")


@dp.message_handler(state=Form.room_type)
async def process_room_type(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['room_type'] = message.text

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()

        await Form.next()

        await message.reply("Введите дату заезда в формате dd.mm.yyyy", reply_markup = markup)

@dp.message_handler(state=Form.arrival_date)
async def process_arrival_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
          try:
              arr = time.strptime(message.text, '%d.%m.%Y')

              if not(arr > time.localtime()):
                raise ValueError

          except ValueError:
              return await message.reply("Некорректный ввод даты.\n")

          data['arrival_date'] = message.text

          await Form.next()

          await message.reply("Введите дату выезда в формате dd.mm.yyyy")

@dp.message_handler(state=Form.departure_date)
async def process_departure_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
          try:
              dep = time.strptime(message.text, '%d.%m.%Y')

              if not (dep > time.strptime(data['arrival_date'], '%d.%m.%Y')):
                  raise ValueError

          except ValueError:
              return await message.reply("Некорректный ввод даты.\n")

          data['departure_date'] = message.text

          await state.finish()

          args = [data["room_type"], data["arrival_date"], data["departure_date"], data["name"], data["phone"]]
          is_free, n_of_free = manage_db.handle(args)

          if is_free:
            await message.answer("Детали брони:\n"
                f"Имя: {args[3]}\n"
                f"Номер телефона: {args[4]}\n"
                f"Тип номера: {args[0]}\n"
                f"Дата заезда: {args[1]}\n"
                f"Дата выезда: {args[2]}\n\n"
                f"Свободных номеров по заданным параметрам: {n_of_free}")

            await message.answer("Происходит бронирование. Пожалуйста, подождите...")

            manage_db.handle_write(args)


    button_book = types.KeyboardButton('Забронировать.')
    button_check = types.KeyboardButton('Проверить количество свободных номеров.')
    book_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    book_kb.add(button_book)
    book_kb.add(button_check)

    await message.answer("Успешно!", reply_markup = book_kb)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)