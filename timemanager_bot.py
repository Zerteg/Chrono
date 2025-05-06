from aiogram import executor, Bot, types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import token
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import logging
import asyncio
import json
import os

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Глобальный массив для хранения задач
tasks = []

# Словарь для отображения пользовательских названий категорий
category_display_names = {
    'daily': 'Ежедневные задачи',
    'reminders': 'Напоминания',
    'trash': 'Отложенные задачи'
}

# Функции управления задачами
async def db_start():
    global tasks
    try:
        if os.path.exists('tasks.json'):
            with open('tasks.json', 'r') as f:
                tasks = json.load(f)
        else:
            tasks = []
        logger.info("Список задач инициализирован из tasks.json")
    except Exception as e:
        tasks = []
        logger.error(f"Ошибка при загрузке задач из tasks.json: {e}")

def save_tasks():
    try:
        with open('tasks.json', 'w') as f:
            json.dump(tasks, f)
        logger.debug("Задачи сохранены в tasks.json")
    except Exception as e:
        logger.error(f"Ошибка при сохранении задач в tasks.json: {e}")

def add_task(user_id, category=None, description=None):
    global tasks
    if category and description:
        task = {
            'id': len(tasks) + 1,
            'user_id': user_id,
            'category': category,
            'description': description,
            'reminder_time': None
        }
        tasks.append(task)
        save_tasks()
        logger.info(f"Добавлена задача: {task}")

def get_tasks(user_id, category):
    task_list = [task for task in tasks if task['user_id'] == user_id and task['category'] == category]
    logger.debug(f"Получены задачи для user_id={user_id}, category={category}: {task_list}")
    return task_list

def delete_task(task_id):
    global tasks
    try:
        task_id = int(task_id)
        logger.debug(f"Перед удалением, список задач: {tasks}")
        initial_len = len(tasks)
        tasks = [task for task in tasks if task['id'] != task_id]
        if len(tasks) < initial_len:
            save_tasks()
            logger.info(f"Удалена задача с ID: {task_id}")
            return True
        else:
            logger.warning(f"Задача с ID {task_id} не найдена")
            return False
    except ValueError:
        logger.error(f"Некорректный task_id: {task_id}")
        return False
    except Exception as e:
        logger.error(f"Ошибка в delete_task: {e}")
        return False

def update_task_category(task_id, new_category):
    try:
        task_id = int(task_id)
        for task in tasks:
            if task['id'] == task_id:
                task['category'] = new_category
                save_tasks()
                logger.info(f"Задача {task_id} перемещена в {new_category}")
                return True
        logger.warning(f"Задача с ID {task_id} не найдена для перемещения")
        return False
    except ValueError:
        logger.error(f"Некорректный task_id: {task_id}")
        return False

def set_reminder(task_id, reminder_time):
    try:
        task_id = int(task_id)
        for task in tasks:
            if task['id'] == task_id:
                task['reminder_time'] = reminder_time
                save_tasks()
                logger.info(f"Установлено напоминание для задачи {task_id}: {reminder_time}")
                return True
        logger.warning(f"Задача с ID {task_id} не найдена для напоминания")
        return False
    except ValueError:
        logger.error(f"Некорректный task_id: {task_id}")
        return False

# Фоновая задача для проверки напоминаний
async def check_reminders():
    while True:
        try:
            current_time = datetime.now()
            for task in tasks:
                if task['reminder_time']:
                    reminder_time = datetime.strptime(task['reminder_time'], '%Y-%m-%d %H:%M')
                    if current_time >= reminder_time:
                        user_id = task['user_id']
                        description = task['description']
                        await bot.send_message(
                            chat_id=user_id,
                            text=f"Напоминание: {description} (Время: {task['reminder_time']})"
                        )
                        task['reminder_time'] = None  # Очищаем напоминание после отправки
                        save_tasks()
                        logger.info(f"Отправлено напоминание для задачи {task['id']} пользователю {user_id}")
            await asyncio.sleep(60)  # Проверяем каждые 60 секунд
        except Exception as e:
            logger.error(f"Ошибка в check_reminders: {e}")
            await asyncio.sleep(60)

# Определение состояний FSM
class TaskStates(StatesGroup):
    main_menu = State()
    daily_tasks_menu = State()
    reminders_menu = State()
    trash_menu = State()
    adding_task = State()
    setting_reminder = State()
    deleting_task = State()
    moving_task = State()
    selecting_category = State()
    setting_reminder_time = State()

# Определение клавиатур
kb_start = ReplyKeyboardMarkup(resize_keyboard=True)
kb_start.add(KeyboardButton('Ежедневные задачи')).add(KeyboardButton('Напоминания')).add(KeyboardButton('Корзина'))

kb_trash = ReplyKeyboardMarkup(resize_keyboard=True)
kb_trash.add(KeyboardButton('Новая задача')).add(KeyboardButton('Удалить задачу'))\
        .add(KeyboardButton('Просмотреть задачи')).add(KeyboardButton('Назад'))

kb_remind = ReplyKeyboardMarkup(resize_keyboard=True)
kb_remind.add(KeyboardButton('Новая задача')).add(KeyboardButton('Удалить задачу'))\
         .add(KeyboardButton('Установить напоминание')).add(KeyboardButton('Переместить задачу'))\
         .add(KeyboardButton('Просмотреть задачи')).add(KeyboardButton('Назад'))

kb_daily_tasks = ReplyKeyboardMarkup(resize_keyboard=True)
kb_daily_tasks.add(KeyboardButton('Новая задача')).add(KeyboardButton('Удалить задачу'))\
              .add(KeyboardButton('Переместить задачу')).add(KeyboardButton('Просмотреть задачи'))\
              .add(KeyboardButton('Назад'))

kb_categories = ReplyKeyboardMarkup(resize_keyboard=True)
kb_categories.add(KeyboardButton('Ежедневные задачи')).add(KeyboardButton('Напоминания'))\
             .add(KeyboardButton('Корзина')).add(KeyboardButton('Назад'))

# Инициализация бота и диспетчера с MemoryStorage
storage = MemoryStorage()
bot = Bot(token)
dp = Dispatcher(bot, storage=storage)

# Функция запуска
async def on_startup(_):
    await db_start()
    # Запускаем фоновую задачу для проверки напоминаний
    asyncio.create_task(check_reminders())
    logger.info('Бот запущен!')

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message, state: FSMContext):
    user_name = message.from_user.first_name
    await bot.send_message(chat_id=message.from_user.id,
                           text=f'Привет, {user_name}! Выбери категорию задач.',
                           reply_markup=kb_start)
    await state.set_state(TaskStates.main_menu)
    logger.info(f"Пользователь {user_name} (ID: {message.from_user.id}) запустил бота")

# Обработчики главного меню
@dp.message_handler(state=TaskStates.main_menu, text=['Ежедневные задачи'])
async def daily_tasks_menu(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id,
                           text='Выберите действие для ежедневных задач:',
                           reply_markup=kb_daily_tasks)
    await state.set_state(TaskStates.daily_tasks_menu)
    logger.debug(f"Пользователь {message.from_user.id} перешёл в меню ежедневных задач")

@dp.message_handler(state=TaskStates.main_menu, text=['Напоминания'])
async def reminders_menu(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id,
                           text='Выберите действие для напоминаний:',
                           reply_markup=kb_remind)
    await state.set_state(TaskStates.reminders_menu)
    logger.debug(f"Пользователь {message.from_user.id} перешёл в меню напоминаний")

@dp.message_handler(state=TaskStates.main_menu, text=['Корзина'])
async def trash_menu(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id,
                           text='Выберите действие для корзины:',
                           reply_markup=kb_trash)
    await state.set_state(TaskStates.trash_menu)
    logger.debug(f"Пользователь {message.from_user.id} перешёл в меню корзины")

# Обработчики добавления задач
@dp.message_handler(state=TaskStates.daily_tasks_menu, text=['Новая задача'])
async def add_task_to_daily(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id, text='Напишите новую задачу:')
    await state.update_data(category='daily')
    await state.set_state(TaskStates.adding_task)
    logger.debug(f"Пользователь {message.from_user.id} начал добавление задачи в daily")

@dp.message_handler(state=TaskStates.reminders_menu, text=['Новая задача'])
async def add_task_to_reminders(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id, text='Напишите новую задачу:')
    await state.update_data(category='reminders')
    await state.set_state(TaskStates.adding_task)
    logger.debug(f"Пользователь {message.from_user.id} начал добавление задачи в reminders")

@dp.message_handler(state=TaskStates.trash_menu, text=['Новая задача'])
async def add_task_to_trash(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id, text='Напишите новую задачу:')
    await state.update_data(category='trash')
    await state.set_state(TaskStates.adding_task)
    logger.debug(f"Пользователь {message.from_user.id} начал добавление задачи в trash")

@dp.message_handler(state=TaskStates.adding_task)
async def save_task(message: types.Message, state: FSMContext):
    task_description = message.text
    data = await state.get_data()
    category = data.get('category')
    user_id = message.from_user.id
    add_task(user_id, category, task_description)
    await bot.send_message(chat_id=message.from_user.id,
                           text=f'Задача "{task_description}" добавлена.')
    if category == 'daily':
        await state.set_state(TaskStates.daily_tasks_menu)
        await bot.send_message(chat_id=message.from_user.id,
                               text='Выберите действие для ежедневных задач:',
                               reply_markup=kb_daily_tasks)
    elif category == 'reminders':
        await state.set_state(TaskStates.reminders_menu)
        await bot.send_message(chat_id=message.from_user.id,
                               text='Выберите действие для напоминаний:',
                               reply_markup=kb_remind)
    elif category == 'trash':
        await state.set_state(TaskStates.trash_menu)
        await bot.send_message(chat_id=message.from_user.id,
                               text='Выберите действие для корзины:',
                               reply_markup=kb_trash)
    logger.debug(f"Пользователь {user_id} добавил задачу '{task_description}' в категорию {category}")

# Обработчик просмотра задач
@dp.message_handler(state=[TaskStates.daily_tasks_menu, TaskStates.reminders_menu, TaskStates.trash_menu], text=['Просмотреть задачи'])
async def view_tasks(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()
    category = 'daily' if current_state == TaskStates.daily_tasks_menu.state else \
               'reminders' if current_state == TaskStates.reminders_menu.state else 'trash'
    task_list = get_tasks(user_id, category)
    if not task_list:
        await bot.send_message(chat_id=message.from_user.id, text='В этой категории нет задач.')
        logger.debug(f"Пользователь {user_id} запросил просмотр задач в {category}: задач нет")
        return
    response = f"Задачи в категории '{category_display_names[category]}':\n"
    for idx, task in enumerate(task_list, 1):
        reminder = f" (Напоминание: {task['reminder_time']})" if task['reminder_time'] else ""
        response += f"{idx}. {task['description']}{reminder}\n"
    await bot.send_message(chat_id=message.from_user.id, text=response)
    logger.debug(f"Пользователь {user_id} просмотрел задачи в {category}")

# Обработчик удаления задач
@dp.message_handler(state=[TaskStates.daily_tasks_menu, TaskStates.reminders_menu, TaskStates.trash_menu], text=['Удалить задачу'])
async def delete_task_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()
    category = 'daily' if current_state == TaskStates.daily_tasks_menu.state else \
               'reminders' if current_state == TaskStates.reminders_menu.state else 'trash'
    task_list = get_tasks(user_id, category)
    if not task_list:
        await bot.send_message(chat_id=message.from_user.id, text='Нет задач для удаления.')
        logger.debug(f"Пользователь {user_id} запросил удаление задач в {category}: задач нет")
        return
    response = f"Задачи в категории '{category_display_names[category]}':\n"
    for idx, task in enumerate(task_list, 1):
        reminder = f" (Напоминание: {task['reminder_time']})" if task['reminder_time'] else ""
        response += f"{idx}. {task['description']}{reminder}\n"
    response += "\nВведите номер задачи для удаления:"
    await bot.send_message(chat_id=message.from_user.id, text=response)
    await state.update_data(category=category, task_list=task_list)
    await state.set_state(TaskStates.deleting_task)
    logger.debug(f"Пользователь {user_id} запросил удаление задач в {category}")

@dp.message_handler(state=TaskStates.deleting_task)
async def process_delete_task(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    category = data.get('category')
    task_list = data.get('task_list')
    try:
        task_idx = int(message.text) - 1
        if 0 <= task_idx < len(task_list):
            task_id = task_list[task_idx]['id']
            logger.debug(f"Попытка удаления задачи с ID {task_id}")
            if delete_task(task_id):
                await bot.send_message(chat_id=user_id, text='Задача удалена.')
            else:
                await bot.send_message(chat_id=user_id, text='Задача не найдена.')
        else:
            await bot.send_message(chat_id=user_id, text='Некорректный номер задачи.')
    except ValueError:
        await bot.send_message(chat_id=user_id, text='Введите число.')
        logger.error(f"Пользователь {user_id} ввёл некорректный номер: {message.text}")
    # Возвращаем в меню
    if category == 'daily':
        await state.set_state(TaskStates.daily_tasks_menu)
        await bot.send_message(chat_id=user_id,
                               text='Выберите действие для ежедневных задач:',
                               reply_markup=kb_daily_tasks)
    elif category == 'reminders':
        await state.set_state(TaskStates.reminders_menu)
        await bot.send_message(chat_id=user_id,
                               text='Выберите действие для напоминаний:',
                               reply_markup=kb_remind)
    elif category == 'trash':
        await state.set_state(TaskStates.trash_menu)
        await bot.send_message(chat_id=user_id,
                               text='Выберите действие для корзины:',
                               reply_markup=kb_trash)

# Обработчики перемещения задач
@dp.message_handler(state=[TaskStates.daily_tasks_menu, TaskStates.reminders_menu], text=['Переместить задачу'])
async def move_task(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()
    category = 'daily' if current_state == TaskStates.daily_tasks_menu.state else 'reminders'
    task_list = get_tasks(user_id, category)
    if not task_list:
        await bot.send_message(chat_id=user_id, text='Нет задач для перемещения.')
        logger.debug(f"Пользователь {user_id} запросил перемещение задач в {category}: задач нет")
        return
    response = f"Задачи в категории '{category_display_names[category]}':\n"
    for idx, task in enumerate(task_list, 1):
        reminder = f" (Напоминание: {task['reminder_time']})" if task['reminder_time'] else ""
        response += f"{idx}. {task['description']}{reminder}\n"
    response += "\nВведите номер задачи для перемещения:"
    await bot.send_message(chat_id=user_id, text=response)
    await state.update_data(category=category, task_list=task_list)
    await state.set_state(TaskStates.moving_task)
    logger.debug(f"Пользователь {user_id} запросил перемещение задач в {category}")

@dp.message_handler(state=TaskStates.moving_task)
async def select_category_to_move(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    task_list = data.get('task_list')
    try:
        task_idx = int(message.text) - 1
        if 0 <= task_idx < len(task_list):
            task_id = task_list[task_idx]['id']
            await state.update_data(task_id=task_id)
            await bot.send_message(chat_id=user_id,
                                  text='Выберите категорию для перемещения:',
                                  reply_markup=kb_categories)
            await state.set_state(TaskStates.selecting_category)
            logger.debug(f"Пользователь {user_id} выбрал задачу {task_id} для перемещения")
        else:
            await bot.send_message(chat_id=user_id, text='Некорректный номер задачи.')
    except ValueError:
        await bot.send_message(chat_id=user_id, text='Введите число.')
        logger.error(f"Пользователь {user_id} ввёл некорректный номер: {message.text}")

@dp.message_handler(state=TaskStates.selecting_category)
async def move_task_to_category(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    category_map = {
        'Ежедневные задачи': 'daily',
        'Напоминания': 'reminders',
        'Корзина': 'trash'
    }
    new_category = category_map.get(message.text)
    data = await state.get_data()
    task_id = data.get('task_id')
    original_category = data.get('category')
    if not new_category:
        await bot.send_message(chat_id=user_id, text='Некорректная категория. Выберите из предложенных.')
        return
    try:
        if update_task_category(task_id, new_category):
            await bot.send_message(chat_id=user_id, text=f'Задача перемещена в {category_display_names[new_category]}.')
        else:
            await bot.send_message(chat_id=user_id, text='Задача не найдена.')
    except Exception as e:
        logger.error(f"Ошибка при перемещении задачи {task_id}: {e}")
        await bot.send_message(chat_id=user_id, text='Ошибка при перемещении задачи.')
    # Возвращаем в меню
    if original_category == 'daily':
        await state.set_state(TaskStates.daily_tasks_menu)
        await bot.send_message(chat_id=user_id,
                               text='Выберите действие для ежедневных задач:',
                               reply_markup=kb_daily_tasks)
    elif original_category == 'reminders':
        await state.set_state(TaskStates.reminders_menu)
        await bot.send_message(chat_id=user_id,
                               text='Выберите действие для напоминаний:',
                               reply_markup=kb_remind)

# Обработчик установки напоминаний
@dp.message_handler(state=TaskStates.reminders_menu, text=['Установить напоминание'])
async def set_reminder_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    task_list = get_tasks(user_id, 'reminders')
    if not task_list:
        await bot.send_message(chat_id=user_id, text='Нет задач для установки напоминания.')
        logger.debug(f"Пользователь {user_id} запросил установку напоминания: задач нет")
        return
    response = f"Задачи в категории '{category_display_names['reminders']}':\n"
    for idx, task in enumerate(task_list, 1):
        reminder = f" (Напоминание: {task['reminder_time']})" if task['reminder_time'] else ""
        response += f"{idx}. {task['description']}{reminder}\n"
    response += "\nВведите номер задачи для установки напоминания:"
    await bot.send_message(chat_id=user_id, text=response)
    await state.update_data(task_list=task_list)
    await state.set_state(TaskStates.setting_reminder)
    logger.debug(f"Пользователь {user_id} запросил установку напоминания")

@dp.message_handler(state=TaskStates.setting_reminder)
async def select_task_for_reminder(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    task_list = data.get('task_list')
    try:
        task_idx = int(message.text) - 1
        if 0 <= task_idx < len(task_list):
            task_id = task_list[task_idx]['id']
            await state.update_data(task_id=task_id)
            await bot.send_message(chat_id=user_id,
                                  text='Введите время напоминания (например, 2025-04-21 18:00):')
            await state.set_state(TaskStates.setting_reminder_time)
            logger.debug(f"Пользователь {user_id} выбрал задачу {task_id} для установки напоминания")
        else:
            await bot.send_message(chat_id=user_id, text='Некорректный номер задачи.')
            logger.debug(f"Пользователь {user_id} ввёл некорректный номер задачи: {message.text}")
    except ValueError:
        await bot.send_message(chat_id=user_id, text='Введите число.')
        logger.error(f"Пользователь {user_id} ввёл некорректный номер: {message.text}")

@dp.message_handler(state=TaskStates.setting_reminder_time)
async def save_reminder_time(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    reminder_time = message.text
    try:
        datetime.strptime(reminder_time, '%Y-%m-%d %H:%M')
        data = await state.get_data()
        task_id = data.get('task_id')
        if set_reminder(task_id, reminder_time):
            await bot.send_message(chat_id=user_id,
                                  text=f'Напоминание установлено на {reminder_time}.')
            logger.info(f"Пользователь {user_id} установил напоминание для задачи {task_id}: {reminder_time}")
        else:
            await bot.send_message(chat_id=user_id,
                                  text='Задача не найдена.')
            logger.warning(f"Задача {task_id} не найдена для установки напоминания")
    except ValueError:
        await bot.send_message(chat_id=user_id,
                              text='Неверный формат времени! Используйте: ГГГГ-ММ-ДД ЧЧ:ММ')
        logger.error(f"Пользователь {user_id} ввёл неверный формат времени: {reminder_time}")
        return
    except Exception as e:
        await bot.send_message(chat_id=user_id,
                              text='Ошибка при установке напоминания.')
        logger.error(f"Ошибка при установке напоминания для задачи {task_id}: {e}")
    await state.set_state(TaskStates.reminders_menu)
    await bot.send_message(chat_id=user_id,
                          text='Выберите действие для напоминаний:',
                          reply_markup=kb_remind)

# Обработчик возврата в главное меню
@dp.message_handler(state=[TaskStates.daily_tasks_menu, TaskStates.reminders_menu, TaskStates.trash_menu], text=['Назад'])
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id,
                           text='Главное меню:',
                           reply_markup=kb_start)
    await state.set_state(TaskStates.main_menu)
    logger.debug(f"Пользователь {message.from_user.id} вернулся в главное меню")

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)