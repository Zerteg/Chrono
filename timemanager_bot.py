from task_ability import *
from aiogram import executor, Bot, types, Dispatcher
from config import token
import asyncio
import datetime
from aiogram.utils.markdown import escape_md
from database import trash_arr,remind_arr,daily_arr
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import (ReplyKeyboardRemove,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.dispatcher import FSMContext
import sqlite3

storage = MemoryStorage()
bot = Bot(token)
dp = Dispatcher(bot=bot, storage=storage)
flag_bin = 0


class ClientStatesGroup(StatesGroup):
    task = State()
    num_for_del = State()
    num_for_mov_1 = State()
    num_for_mov_2 = State()

kb_start = ReplyKeyboardMarkup(resize_keyboard=True)
kb_start.add(KeyboardButton('Ежедневные задачи')).add(KeyboardButton('Напоминания')).insert(KeyboardButton('Мусорка'))

kb_list = ReplyKeyboardMarkup(resize_keyboard=True)
kb_list.add(KeyboardButton('Новая задача')).add(KeyboardButton('Удалить задачу')).add(KeyboardButton('Переместить задачу')).insert(KeyboardButton('Назад'))

# kb_remind = ReplyKeyboardMarkup(resize_keyboard=True)
# kb_remind.add(KeyboardButton('Новая задача')).add(KeyboardButton('Удалить задачу')).\
#           add(KeyboardButton('Переместить задачу')).insert(KeyboardButton('Назад'))
#
# kb_daily_tasks = ReplyKeyboardMarkup(resize_keyboard=True)
# kb_daily_tasks.add(KeyboardButton('Новая задача')).add(KeyboardButton('Удалить задачу')).\
#                add(KeyboardButton('Переместить задачу')).insert(KeyboardButton('Назад'))


async def weak_up(_):
    print('Я запустился!')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id,
    user_name = escape_md(message.from_user.first_name)
    await bot.send_message(chat_id = message.from_user.id,
                           text = f'Привет,  {user_name}',
                           reply_markup=kb_start)


@dp.message_handler(text=['Мусорка'])
async def trash(message: types.Message):
    user_id = message.from_user.id
    global flag_bin
    flag_bin = 1
    list_trash = ''
    for i in range(0, len(trash_arr)):
        list_trash = list_trash + str(i+1) + '. ' + trash_arr[i] + '\n'
    await bot.send_message(chat_id=message.from_user.id,
                           text='Выберите действие',
                           reply_markup=kb_list)

    await message.answer(f'{list_trash}')


# @dp.message_handler(text=['Напоминания'])
# async def remind(message: types.Message):
#     user_id = message.from_user.id
#     global flag_bin
#     flag_bin = 2
#     list_remind = ''
#     for i in range(0, len(remind_arr)):
#         list_remind = list_remind + str(i + 1) + '. ' + remind_arr[i] + '\n'
#     await bot.send_message(chat_id = message.from_user.id,
#                            text = 'Выберите действие',
#                            reply_markup=kb_list)
#     await message.answer(f'{list_remind}')

@dp.message_handler(text=['Ежедневные задачи'])
async def daily_tasks(message: types.Message):
    user_id = message.from_user.id
    global flag_bin
    flag_bin = 3
    list_daily = ''
    for i in range(0, len(daily_arr)):
        list_daily = list_daily + str(i + 1) + '. ' + daily_arr[i] + '\n'
    await bot.send_message(chat_id=message.from_user.id,
                           text='Выберите действие',
                           reply_markup=kb_list)
    await message.answer(f'{list_daily}')

@dp.message_handler(text=['Новая задача'], state=None)
async def add_task(message: types.Message):
    user_id = message.from_user.id
    await bot.send_message(chat_id=message.from_user.id,
                           text='Напишите задачу:',
                           reply_markup=kb_list)
    await ClientStatesGroup.task.set()


@dp.message_handler(state=ClientStatesGroup.task)
async def load_task(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['task'] = message.text
        if flag_bin == 1:
            trash_arr.append(data['task'])
        elif flag_bin == 2:
            remind_arr.append(data['task'])
        elif flag_bin == 3:
            daily_arr.append(data['task'])

    await message.reply('Ваша задача сохранена!')

    await state.finish()


@dp.message_handler(text=['Удалить задачу'], state=None)
async def del_task(message: types.Message):
    user_id = message.from_user.id,
    await bot.send_message(chat_id=message.from_user.id,
                            text='Выберите номер задачи',
                            reply_markup=kb_list)

    await ClientStatesGroup.num_for_del.set()


@dp.message_handler(state=ClientStatesGroup.num_for_del)
async def load_del_task(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['num_for_del'] = message.text
        # if (type((data['num_for_del'])) == str):
        #     await bot.send_message(chat_id=message.from_user.id,
        #                            text='Что-то не то, попробуй снова)')
        if flag_bin == 1:
            del trash_arr[int(data['num_for_del'])-1]
            list_trash_2 = ''
            for i in range(0, len(trash_arr)):
                list_trash_2 = list_trash_2 + str(i + 1) + '. ' + trash_arr[i] + '\n'
            await message.answer(f'{list_trash_2}')
        elif flag_bin == 2:
            del remind_arr[int(data['num_for_del'])-1]
            list_remind_2 = ''
            for i in range(0, len(trash_arr)):
                list_remind_2 = list_remind_2 + str(i + 1) + '. ' + remind_arr[i] + '\n'
            await message.answer(f'{list_remind_2}')
        elif flag_bin == 3:
            del daily_arr[int(data['num_for_del'])-1]
            list_daily_2 = ''
            for i in range(0, len(trash_arr)):
                list_daily_2 = list_daily_2 + str(i + 1) + '. ' + daily_arr[i] + '\n'
            await message.answer(f'{list_daily_2}')

    await state.finish()


@dp.message_handler(text=['Переместить задачу'], state=None)
async def moving_task_1(message: types.Message):
    user_id = message.from_user.id,
    await bot.send_message(chat_id=message.from_user.id,
                            text='Выберите номер задачи',
                            reply_markup=kb_list)

    await ClientStatesGroup.num_for_mov_1.set()


@dp.message_handler(state=ClientStatesGroup.num_for_mov_1)
async def load_mov_task(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['num_for_mov_1'] = message.text
        # if (type((data['num_for_del'])) == str):
        #     await bot.send_message(chat_id=message.from_user.id,
        #                            text='Что-то не то, попробуй снова)')
        if flag_bin == 1:
            daily_arr.append(trash_arr[int(data['num_for_mov_1'])-1])
            del trash_arr[int(data['num_for_mov_1'])-1]

    await state.finish()


#-----------------------------------------------------НАПОМИНАНИЕ---------------------------------------------------------
async def schedule_notifications(user_time, chat_id, message):
    while True:
        now = datetime.datetime.now().time()
        if now >= user_time:
            await asyncio.create_task(bot.send_message(chat_id=chat_id, text=message))
            break
        await asyncio.sleep(3)


flag_time = 0


@dp.message_handler(text=['Напоминания'])
async def remind(message: types.Message):
    global flag_time
    user_id = message.from_user.id,
    await bot.send_message(chat_id = message.from_user.id,
                           text = 'Выберите действие:',
                           reply_markup=kb_list)
    flag_time += 1


@dp.message_handler(text=["Новая задача"])
async def new_task(message:types.Message):
    global flag_time
    if flag_time == 1:
        flag_time = 2
        await message.answer(text="Введите задачу, а также через два пробела введите время в формате ЧЧ:ММ (22:00)",
                             )


@dp.message_handler()#убран спиок команд, вместо этого используются индивидульный флаг
async def add_task(message: types.Message):
    global flag_time
    global schedule_notifications
    if flag_time == 2:
        flag_time = 0#обнуляем чтобы ещё раз потом запустить
        text = str(message.text)
        mass_str = []
        i = 0
        time_to_notification = ''
        for i in range(0,len(text)-1):
            if text[i] not in "1234567890":
                mass_str.append(text[i])
            else:
                time_to_notification = (text[i:])# время в котрое должно прийти уведомление в строчном формате
                break
        time_to_notification = str("".join(time_to_notification))
        task_str = str("".join(mass_str))#название задачи
        user_time = datetime.datetime.strptime(time_to_notification,'%H:%M').time()#переводим время из строчного формата в какой то другой

        loop = asyncio.get_event_loop()
        loop.create_task(schedule_notifications(user_time, message.from_user.id, task_str))
        # Запускаем бесконечный цикл событий
        loop.run_forever()
#---------------------------------------------------------------------------------------------------------------------------


@dp.message_handler(text=['Назад'])
async def back(message: types.Message, state: FSMContext):
    #current_state = await state.get_state()
    #if current_state is None:
     #   return

    user_id = message.from_user.id,

    #await state.finish()
    await bot.send_message(chat_id=message.from_user.id,
                           text='Выберите список',
                           reply_markup=kb_start)



if __name__ == '__main__':
    executor.start_polling(dp)


