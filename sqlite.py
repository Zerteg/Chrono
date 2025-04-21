import sqlite3 as sq

async def db_start():
    global db, cursor

    db = sq.connect('trash.db')
    cur = db.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS profile(user_id TEXT PRIMARY KEY, description TEXT)") #вопросик с праймери ки

    db.commit()

async def add_task(user_id):
    #task = cursor.execute("SELECT ! FROM profile WHERE user_id == '{key}'".format(key=user_id)).fetchone()
    cursor.execute("INSERT INTO profile VALUES(?, ?)", (user_id, ''))
    db.commit()

async def del_task(state, user_id):
    async with state.proxy() as data:
        cursor.execute("UPDATE profile WHERE user_id == '{}' SET description = '{}', ".format(
            user_id, data['description']))
        db.commit()