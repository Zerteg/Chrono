from timemanager_bot import *

async def add_task(message: types.Message):
    user_id = message.from_user.id,
    await bot.send_message(chat_id=message.from_user.id,
                           text='Напишите задачу:',
                           reply_markup=kb_daily_tasks)

    ind_trash = 0
    text = message.text
    print(text)
    if flag_bin == 1:
        trash_arr[ind_trash] = text
        print(trash_arr[ind_trash])
        await bot.send_message(chat_id=message.from_user.id,
                               text=trash_arr[ind_trash])