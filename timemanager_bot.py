from aiogram import executor, Bot, types, Dispatcher
from config import token
from aiogram.types import (ReplyKeyboardRemove,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton)

bot = Bot(token)
dp = Dispatcher(bot)

kb_start = ReplyKeyboardMarkup(resize_keyboard=True)
kb_start.add(KeyboardButton('Ежедневные задачи')).add(KeyboardButton('Напоминания')).insert(KeyboardButton('Мусорка'))

kb_trash = ReplyKeyboardMarkup(resize_keyboard=True)
kb_trash.add(KeyboardButton('Новаяя задача')).add(KeyboardButton('Удалить задачу')).insert(KeyboardButton('Назад'))

kb_remind = ReplyKeyboardMarkup(resize_keyboard=True)
kb_remind.add(KeyboardButton('Новая задача')).add(KeyboardButton('Удалить задачу')).add(KeyboardButton('Установить напоминание')).\
          add(KeyboardButton('Переместить задачу')).insert(KeyboardButton('Назад'))

kb_daily_tasks = ReplyKeyboardMarkup(resize_keyboard=True)
kb_daily_tasks.add(KeyboardButton('Новая задача')).add(KeyboardButton('Удалить задачу')).\
               add(KeyboardButton('Переместить задачу')).insert(KeyboardButton('Назад'))


async def weak_up(_):
    print('Я запустился!')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id,
    user_name = message.from_user.first_name,
    await bot.send_message(chat_id = message.from_user.id,
                           text = f'Привет, {user_name}',
                           reply_markup=kb_start)


@dp.message_handler(text=['Мусорка'])
async def trash(message: types.Message):
    user_id = message.from_user.id,
    await bot.send_message(chat_id = message.from_user.id,
                           text = 'Напишите задачу:',
                           reply_markup=kb_trash)


@dp.message_handler(text=['Напоминания'])
async def remind(message: types.Message):
    user_id = message.from_user.id,
    await bot.send_message(chat_id = message.from_user.id,
                           text = 'Напишите задачу:',
                           reply_markup=kb_remind)


@dp.message_handler(text=['Ежедневные задачи'])
async def daily_tasks(message: types.Message):
    user_id = message.from_user.id,
    await bot.send_message(chat_id=message.from_user.id,
                           text='Напишите задачу:',
                           reply_markup=kb_daily_tasks)


@dp.message_handler(text=['Назад'])
async def back(message: types.Message):
    user_id = message.from_user.id,
    await bot.send_message(chat_id=message.from_user.id,
                           text='Напишите задачу:',
                           reply_markup=kb_start)


if __name__ == '__main__':
    executor.start_polling(dp)


