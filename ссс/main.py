from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove() 

cancel_button = "❌ Отмена"
def cansel(message):
    bot.send_message(message.chat.id, "Операция отменена. Чтобы посмотреть команды, используй - /info", reply_markup=hideBoard)
  
def no_projects(message):
    bot.send_message(message.chat.id, 'У тебя пока нет проектов! 😢\nДобавь первый проект командой /new_project')

def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(f"📁 {row}", callback_data=row))
    return markup

def gen_markup(rows):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

attributes_of_projects = {'Имя проекта' : ["Введите новое имя проекта", "project_name"],
                          "Описание" : ["Введите новое описание проекта", "description"],
                          "Ссылка" : ["Введите новую ссылку на проект", "url"],
                          "Статус" : ["Выберите новый статус задачи", "status_id"]}

def info_project(message, user_id, project_name):
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name)
    if not skills:
        skills = 'Навыки пока не добавлены'
    
    bot.send_message(message.chat.id, f"""📁 <b>{info[0]}</b>
    
📝 <b>Описание:</b> {info[1]}
🔗 <b>Ссылка:</b> {info[2]}
📊 <b>Статус:</b> {info[3]}
⚡ <b>Навыки:</b> {skills}""", parse_mode='HTML')

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, """👋 Привет! Я бот-менеджер проектов 🚀

Помогу тебе сохранить твои проекты и информацию о них! 

Нажми /info чтобы увидеть все команды""")
    info(message)
    
@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, """📋 <b>СПИСОК КОМАНД:</b>

➕ /new_project - создать новый проект
• Добавляет проект в портфолио
• Спросит название, описание, ссылку и статус

📂 /projects - показать все проекты
• Показывает список всех твоих проектов
• Можно выбрать проект для деталей

🔧 /skills - добавить навыки к проекту
• Привязывает навыки к существующему проекту
• Нужно выбрать проект и навык

✏️ /update_projects - изменить проект
• Меняет информацию о проекте
• Можно изменить название, описание, ссылку или статус

🗑️ /delete - удалить проект
• Удаляет проект из портфолио
• Будь осторожен, это навсегда!

❓ /info - эта справка
• Показывает все команды бота

""", )

@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    bot.send_message(message.chat.id, "➕ Создание нового проекта\n\nВведи название проекта:")
    bot.register_next_step_handler(message, name_project)

def name_project(message):
    if message.text == cancel_button:
        cansel(message)
        return
    
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "📝 Введи описание проекта (или 'пропустить'):")
    bot.register_next_step_handler(message, description_project, data=data)

def description_project(message, data):
    if message.text == cancel_button:
        cansel(message)
        return
    
    description = message.text
    if description.lower() == 'пропустить':
        description = ""  
    data.append(description)  
    bot.send_message(message.chat.id, "🔗 Введи ссылку на проект:")
    bot.register_next_step_handler(message, link_project, data=data)

def link_project(message, data):
    if message.text == cancel_button:
        cansel(message)
        return
    
    data.append(message.text)  
    statuses = [x[0] for x in manager.get_statuses()] 
    bot.send_message(message.chat.id, """📊 Выбери статус проекта:
    
[На этапе проектирования] 🏗️
[В процессе разработки] 👨‍💻
[Разработан. Готов к использованию.] ✅
[Обновлен] 🔄
[Завершен. Не поддерживается] ⛔
""", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

def callback_project(message, data, statuses):
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if status not in statuses:
        bot.send_message(message.chat.id, "❌ Ты выбрал статус не из списка, попробуй еще раз!", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.append(status_id) 
    manager.insert_project([tuple(data)])
    bot.send_message(message.chat.id, "✅ Проект успешно сохранен! 🎉")

@bot.message_handler(commands=['skills'])
def skill_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, '🔧 Выбери проект для добавления навыка:', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)

def skill_project(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, '❌ Нет такого проекта! Выбери из списка:', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]
        bot.send_message(message.chat.id, '⚡ Выбери навык для добавления:', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

def set_skill(message, project_name, skills):
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
        
    if skill not in skills:
        bot.send_message(message.chat.id, '❌ Нет такого навыка! Выбери из списка:', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill)
    bot.send_message(message.chat.id, f'✅ Навык "{skill}" добавлен проекту "{project_name}"! 👍')

@bot.message_handler(commands=['projects'])
def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "📂 <b>Твои проекты:</b>\n\n"
        for x in projects:
            text += f"📁 <b>{x[2]}</b>\n🔗 {x[4]}\n\n"
        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=gen_inline_markup([x[2] for x in projects]))
    else:
        no_projects(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    project_name = call.data
    info_project(call.message, call.from_user.id, project_name)

@bot.message_handler(commands=['delete'])
def delete_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "🗑️ <b>Выбери проект для удаления:</b>\n\n"
        for x in projects:
            text += f"📁 {x[2]}\n🔗 {x[4]}\n\n"
        projects_list = [x[2] for x in projects]
        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=gen_markup(projects_list))
        bot.register_next_step_handler(message, delete_project, projects=projects_list)
    else:
        no_projects(message)

def delete_project(message, projects):
    project = message.text
    user_id = message.from_user.id

    if message.text == cancel_button:
        cansel(message)
        return
    if project not in projects:
        bot.send_message(message.chat.id, '❌ Нет такого проекта! Выбери из списка:', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f'✅ Проект "{project}" удален!')

@bot.message_handler(commands=['update_projects'])
def update_project(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "✏️ <b>Выбери проект для изменения:</b>", parse_mode='HTML', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
    else:
        no_projects(message)

def update_project_step_2(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, "❌ Нет такого проекта! Выбери из списка:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
        return
    
    bot.send_message(message.chat.id, """✏️ <b>Что изменить в проекте?</b>

📁 [Имя проекта]
📝 [Описание]
🔗 [Ссылка]
📊 [Статус]""", parse_mode='HTML', reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

def update_project_step_3(message, project_name):
    attribute = message.text
    reply_markup = None 
    if message.text == cancel_button:
        cansel(message)
        return
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "❌ Нет такого варианта! Выбери из списка:", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    elif attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup=gen_markup([x[0] for x in rows])
    
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup=reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])

def update_project_step_4(message, project_name, attribute): 
    update_info = message.text
    
    if update_info == cancel_button:
        cansel(message)
        return
    
    if attribute == "status_id":
        rows = manager.get_statuses()
        status_names = [x[0] for x in rows]
        
        if update_info in status_names:
            update_info = manager.get_status_id(update_info) 
        else:
            bot.send_message(message.chat.id, "❌ Неверный статус! Выбери из списка:", reply_markup=gen_markup(status_names))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
    
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    
    try:
        manager.update_projects(attribute, data)
        bot.send_message(message.chat.id, "✅ Готово! Проект обновлен! ✨")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    projects = [x[0] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
        return
    bot.reply_to(message, "❓ Нужна помощь? Напиши /info")

if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.infinity_polling()


    