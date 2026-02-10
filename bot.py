import telebot
from telebot import types
import json
import os

# Токен вашего бота
TOKEN = '7817001770:AAEV81Qb4IQl2Ta-2DXZjF26mpuGQUQe_ek'
bot = telebot.TeleBot(TOKEN)

# Файл для хранения данных
DATA_FILE = 'users_data.json'

# Админ ID (ТОЛЬКО ТЫ)
ADMIN_ID = 6419707109

# --- Загрузка и сохранение данных ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        print(f"⚠️ Ошибка чтения данных: {e}")
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

# --- Работа с пользователем ---
def get_user_data(user_id, data):
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {'balance': 0, 'completed_tasks': [], 'is_admin': False}
    return data[user_id]

# --- Кнопки ---
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Задания", "Магазин", "Баланс")
    if user_id == ADMIN_ID:
        markup.row("Добавить задание", "Добавить услугу")
        markup.add("Удалить задание")
    return markup

def back_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Назад")
    return markup

# --- Команда /start ---
@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    user_data = get_user_data(message.from_user.id, data)
    if message.from_user.id == ADMIN_ID:
        user_data['is_admin'] = True
    save_data(data)
    
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в бота! Выполняйте задания и получайте SiteCoin!",
        reply_markup=main_menu(message.from_user.id)
    )

# === Обработка кнопок ===
@bot.message_handler(func=lambda m: m.text in ['Задания', 'Магазин', 'Баланс', 'Добавить задание', 'Добавить услугу', 'Удалить задание', 'Назад'])
def handle_buttons(message):
    data = load_data()

    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись в главное меню.", reply_markup=main_menu(message.from_user.id))
        return

    elif message.text == 'Задания':
        tasks = data.get('tasks', [])
        if not tasks:
            bot.send_message(message.chat.id, "📭 Пока нет доступных заданий.", reply_markup=back_button())
            return

        # Фильтруем только dict
        valid_tasks = [t for t in tasks if isinstance(t, dict)]
        if len(valid_tasks) != len(tasks):
            print(f"🧹 Починка tasks: удалено {len(tasks) - len(valid_tasks)} некорректных элементов")
            data['tasks'] = valid_tasks
            save_data(data)

        if not valid_tasks:
            bot.send_message(message.chat.id, "📭 Нет корректных заданий.", reply_markup=back_button())
            return

        markup = types.InlineKeyboardMarkup()
        for i, task in enumerate(valid_tasks):
            title = task.get('title', f'Задание {i+1}')
            markup.add(types.InlineKeyboardButton(f'📋 {title}', callback_data=f'show_task_{i}'))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
        bot.send_message(message.chat.id, "✨ Выберите задание:", reply_markup=markup)

    elif message.text == 'Магазин':
        services = data.get('services', [])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Сайт - 100 SiteCoin', callback_data='buy_site'))
        for s in services:
            name = s['name']
            price = s['price']
            markup.add(types.InlineKeyboardButton(f'{name} - {price} SiteCoin', callback_data=f'buy_{name}'))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
        bot.send_message(message.chat.id, "🛍 Добро пожаловать в магазин!", reply_markup=markup)

    elif message.text == 'Баланс':
        balance = get_user_data(message.from_user.id, data)['balance']
        bot.send_message(message.chat.id, f"💰 Ваш баланс: {balance} SiteCoin", reply_markup=back_button())

    elif message.text == 'Добавить задание' and message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "📝 Введите заголовок задания:", reply_markup=back_button())
        bot.register_next_step_handler(message, add_task_title)

    elif message.text == 'Добавить услугу' and message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🏷 Введите название услуги:", reply_markup=back_button())
        bot.register_next_step_handler(message, add_service_name)

    elif message.text == 'Удалить задание' and message.from_user.id == ADMIN_ID:
        tasks = data.get('tasks', [])
        if not tasks:
            bot.send_message(message.chat.id, "❌ Нет заданий для удаления.", reply_markup=main_menu(ADMIN_ID))
            return
        markup = types.InlineKeyboardMarkup()
        for i, t in enumerate(tasks):
            title = t.get('title', f'Задание {i+1}')
            ch = f" + {t['channel']}" if t.get('channel') else ""
            markup.add(types.InlineKeyboardButton(f"🗑 {i+1}. {title}{ch}", callback_data=f"delete_task_{i}"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
        bot.send_message(message.chat.id, "Выберите задание для удаления:", reply_markup=markup)


# --- Добавление задания ---
def add_task_title(message):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=main_menu(ADMIN_ID))
        return
    temp_file = f"temp_task_{message.from_user.id}.json"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump({'title': message.text.strip()}, f, ensure_ascii=False)
    except:
        bot.send_message(message.chat.id, "Ошибка. Попробуйте позже.")
        return
    bot.send_message(message.chat.id, "📄 Введите условие задания:")
    bot.register_next_step_handler(message, add_task_text)

def add_task_text(message):
    if message.text == "Назад":
        try:
            os.remove(f"temp_task_{message.from_user.id}.json")
        except:
            pass
        bot.send_message(message.chat.id, "Отменено.", reply_markup=main_menu(ADMIN_ID))
        return
    temp_file = f"temp_task_{message.from_user.id}.json"
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            temp_data = json.load(f)
    except:
        bot.send_message(message.chat.id, "Ошибка. Начните заново.")
        return

    temp_data['text'] = message.text
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(temp_data, f, ensure_ascii=False)

    bot.send_message(message.chat.id, "💸 Введите награду (в SiteCoin):")
    bot.register_next_step_handler(message, add_task_reward)

def add_task_reward(message):
    if message.text == "Назад":
        try:
            os.remove(f"temp_task_{message.from_user.id}.json")
        except:
            pass
        bot.send_message(message.chat.id, "Отменено.", reply_markup=main_menu(ADMIN_ID))
        return

    try:
        reward = int(message.text.strip())
        if reward <= 0:
            raise ValueError
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Введите целое положительное число:")
        bot.register_next_step_handler(msg, add_task_reward)
        return

    temp_file = f"temp_task_{message.from_user.id}.json"
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            temp_data = json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки temp файла: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка. Начните заново.")
        return

    temp_data['reward'] = reward
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(temp_data, f, ensure_ascii=False)

    msg = bot.send_message(message.chat.id, "🔗 Введите @канал или «нет»:")
    bot.register_next_step_handler(msg, lambda m: finish_add_task(m, temp_data))

def finish_add_task(message, temp_data):
    channel = message.text.strip()
    if channel.lower() == "нет" or not channel.startswith('@'):
        channel = None

    data = load_data()
    data.setdefault('tasks', []).append({
        'title': temp_data['title'],
        'text': temp_data['text'],
        'reward': temp_data['reward'],
        'channel': channel
    })
    save_data(data)
    temp_file = f"temp_task_{message.from_user.id}.json"
    if os.path.exists(temp_file):
        os.remove(temp_file)

    status = f" и канал: {channel}" if channel else ""
    bot.send_message(message.chat.id,
                     f"✅ Задание добавлено!\n"
                     f"📌 {temp_data['title']}\n"
                     f"🎁 Награда: {temp_data['reward']} SiteCoin{status}",
                     reply_markup=main_menu(ADMIN_ID))


# --- Добавление услуги ---
def add_service_name(message):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=main_menu(ADMIN_ID))
        return
    temp_file = f"temp_service_{message.from_user.id}.json"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump({'name': message.text.strip()}, f, ensure_ascii=False)
    except:
        bot.send_message(message.chat.id, "Ошибка.")
        return
    bot.send_message(message.chat.id, "💰 Цена (в SiteCoin):")
    bot.register_next_step_handler(message, add_service_price)

def add_service_price(message):
    if message.text == "Назад":
        try:
            os.remove(f"temp_service_{message.from_user.id}.json")
        except:
            pass
        bot.send_message(message.chat.id, "Отменено.", reply_markup=main_menu(ADMIN_ID))
        return
    try:
        price = int(message.text)
        if price <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Введите число > 0:")
        bot.register_next_step_handler(message, add_service_price)
        return

    temp_file = f"temp_service_{message.from_user.id}.json"
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            temp_data = json.load(f)
        service_name = temp_data['name']
        os.remove(temp_file)
    except:
        bot.send_message(message.chat.id, "Ошибка чтения.")
        return

    data = load_data()
    data.setdefault('services', []).append({'name': service_name, 'price': price})
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Услуга '{service_name}' добавлена за {price} SiteCoin!", reply_markup=main_menu(ADMIN_ID))


# === Обработчик inline-кнопок ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        if not call.message:
            bot.answer_callback_query(call.id, "Ошибка: сообщение недоступно.")
            return

        data = load_data()
        user_data = get_user_data(call.from_user.id, data)

        if call.data == "back_to_menu":
            try:
                bot.edit_message_text("Вы вернулись в меню.", call.message.chat.id, call.message.message_id, reply_markup=None)
            except:
                pass
            bot.send_message(call.message.chat.id, "🏠 Главное меню:", reply_markup=main_menu(call.from_user.id))
            return

        # --- Удаление задания ---
        elif call.data.startswith('delete_task_'):
            if call.from_user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "⛔ У вас нет прав.")
                return
            try:
                task_id = int(call.data.split('_')[2])
            except:
                bot.answer_callback_query(call.id, "❌ Неверный ID.")
                return

            tasks = data.get('tasks', [])
            if task_id >= len(tasks):
                bot.send_message(call.message.chat.id, "❌ Задание не найдено.")
                return

            deleted = tasks.pop(task_id)
            save_data(data)

            bot.send_message(call.message.chat.id, f"🗑 Удалено:\n{deleted['title']}")

            # Обновляем индексы выполненных заданий
            for uid, info in data.items():
                if uid.isdigit():
                    completed = info.get('completed_tasks', [])
                    if task_id in completed:
                        completed.remove(task_id)
                    info['completed_tasks'] = [i - 1 if i > task_id else i for i in completed]
            save_data(data)

            # Обновляем список удаления
            tasks = data.get('tasks', [])
            markup = types.InlineKeyboardMarkup()
            for i, t in enumerate(tasks):
                title = t.get('title', f'Задание {i+1}')
                ch = f" + {t['channel']}" if t.get('channel') else ""
                markup.add(types.InlineKeyboardButton(f"🗑 {i+1}. {title}{ch}", callback_data=f"delete_task_{i}"))
            markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
            bot.send_message(call.message.chat.id, "Выберите другое задание:", reply_markup=markup)

        # --- Показать задание ---
        elif call.data.startswith('show_task_'):
            try:
                task_id = int(call.data.split('_')[2])
            except:
                bot.answer_callback_query(call.id, "❌ Ошибка: неверный номер.")
                return

            tasks = data.get('tasks', [])
            if task_id >= len(tasks):
                bot.send_message(call.message.chat.id, "❌ Задание не найдено.")
                return

            task = tasks[task_id]
            if task_id in user_data['completed_tasks']:
                bot.answer_callback_query(call.id, "Вы уже выполнили это задание.", show_alert=True)
                return

            # ✅ Показываем только задание
            channel_info = f"\n\n📌 Требуется подписка: {task['channel']}" if task.get('channel') else ""
            bot.send_message(
                call.message.chat.id,
                f"📋 *{task['title']}*\n\n"
                f"{task['text']}"
                f"{channel_info}",
                parse_mode='Markdown'
            )

            # Кнопка "Я выполнил"
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Я выполнил", callback_data=f"confirm_task_{task_id}"),
                types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")
            )
            bot.send_message(call.message.chat.id, "Нажмите, когда выполните задание:", reply_markup=markup)
            bot.answer_callback_query(call.id)

        # --- Подтверждение выполнения (пользователь жмёт "Я выполнил") ---
        elif call.data.startswith('confirm_task_'):
            try:
                task_id = int(call.data.split('_')[2])
            except:
                bot.answer_callback_query(call.id, "❌ Ошибка: неверный номер.")
                return

            tasks = data.get('tasks', [])
            if task_id >= len(tasks):
                bot.send_message(call.message.chat.id, "❌ Задание не найдено.")
                return

            task = tasks[task_id]
            if task_id in user_data['completed_tasks']:
                bot.answer_callback_query(call.id, "Вы уже выполняли это задание.", show_alert=True)
                return

            # Проверка подписки
            channel = task.get('channel')
            if channel:
                try:
                    member = bot.get_chat_member(channel, call.from_user.id)
                    if member.status not in ['member', 'administrator', 'creator']:
                        bot.send_message(call.message.chat.id, f"⚠ Подпишитесь на {channel}, чтобы продолжить.")
                        return
                except:
                    bot.send_message(call.message.chat.id, "⚠ Не удалось проверить подписку.")
                    return

            # Отправляем заявку админу
            username = f"@{call.from_user.username}" if call.from_user.username else f"ID: {call.from_user.id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Принять", callback_data=f"accept_{call.from_user.id}_{task_id}"),
                types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{call.from_user.id}_{task_id}")
            )

            try:
                bot.send_message(
                    ADMIN_ID,
                    f"📋 Заявка на задание\n"
                    f"👤 {username}\n"
                    f"🎯 {task['title']}\n"
                    f"📄 {task['text']}",
                    reply_markup=markup
                )
                bot.send_message(call.message.chat.id, "📩 Ваша заявка отправлена на проверку!")
            except Exception as e:
                print(f"Ошибка отправки админу: {e}")
                bot.send_message(call.message.chat.id, "❌ Не удалось отправить заявку. Попробуйте позже.")

            bot.answer_callback_query(call.id)

        # --- Принять задание (админ) ---
        elif call.data.startswith('accept_'):
            parts = call.data.split('_')
            if len(parts) != 3 or call.from_user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "⛔ Нет прав.")
                return
            try:
                user_id, task_id = int(parts[1]), int(parts[2])
            except:
                bot.answer_callback_query(call.id, "❌ Ошибка ID.")
                return

            target_data = get_user_data(user_id, data)
            tasks = data.get('tasks', [])
            if task_id >= len(tasks):
                bot.answer_callback_query(call.id, "❌ Задание не найдено.")
                return
            if task_id in target_data['completed_tasks']:
                bot.send_message(call.message.chat.id, "⚠ Это задание уже выполнено.")
                return

            reward = tasks[task_id]['reward']
            target_data['balance'] += reward
            target_data['completed_tasks'].append(task_id)
            save_data(data)

            try:
                bot.send_message(user_id, f"✅ Получено {reward} SiteCoin за задание!")
            except:
                pass

            # Убираем кнопки
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.answer_callback_query(call.id, "✅ Подтверждено!")

        # --- Отклонить задание (админ) ---
        elif call.data.startswith('reject_'):
            if call.from_user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "⛔ Нет прав.")
                return
            try:
                user_id, task_id = map(int, call.data.split('_')[1:])
            except:
                bot.answer_callback_query(call.id, "❌ Ошибка ID.")
                return

            try:
                bot.send_message(user_id, "❌ Ваша заявка отклонена. Попробуйте снова.")
            except:
                pass

            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.answer_callback_query(call.id, "❌ Отклонено.")

        # === ПОКУПКИ ===
        elif call.data == 'buy_site':
            if user_data['balance'] >= 100:
                user_data['balance'] -= 100
                save_data(data)
                bot.send_message(call.message.chat.id, "🎉 Сайт куплен! Мы свяжемся с вами.")
                try:
                    bot.send_message(ADMIN_ID, f"🛒 Покупка: @{call.from_user.username} купил сайт")
                except:
                    pass
            else:
                bot.send_message(call.message.chat.id, "❌ Недостаточно средств.")

        elif call.data.startswith('buy_'):
            service_name = call.data[4:]
            service = next((s for s in data.get('services', []) if s['name'] == service_name), None)
            if not service:
                bot.send_message(call.message.chat.id, "❌ Услуга не найдена.")
                return
            price = service['price']
            if user_data['balance'] >= price:
                user_data['balance'] -= price
                save_data(data)
                bot.send_message(call.message.chat.id, f"🎉 Вы купили: {service_name}")
                try:
                    bot.send_message(ADMIN_ID, f"🛒 Покупка: @{call.from_user.username} купил {service_name}")
                except:
                    pass
            else:
                bot.send_message(call.message.chat.id, f"❌ Нужно {price} SiteCoin.")

    except Exception as e:
        print(f"🚨 Ошибка: {e}")
        try:
            bot.send_message(call.message.chat.id, "⚠ Произошла ошибка.")
        except:
            pass

# === ЗАПУСК ===
if __name__ == '__main__':
    import time
    print("✅ Бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=15)
        except Exception as e:
            print(f"🔴 Ошибка polling: {e}")
            time.sleep(5)