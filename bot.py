import telebot
from telebot import types

# === НАСТРОЙКИ ===
BOT_TOKEN = '8446783650:AAHGrAjhywxMWA4ZFg5ZMbQNs98vpgss-Sc'  # ← Замени
ADMIN_ID = 6419707109      # ← Твой ID
GROUP_ID = -1003726521757 # ← ID группы (с минусом!)
TOPIC_ID = 306            # ← ID темы "Расписание"

bot = telebot.TeleBot(BOT_TOKEN)

# Состояния
user_states = {}  # {user_id: 'waiting_photo', 'waiting_start', 'waiting_end'}

# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Доступ запрещён.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("📤 Отправить расписание")
    markup.add(btn)
    bot.send_message(message.chat.id, "Привет, админ! Нажми кнопку, чтобы отправить расписание.", reply_markup=markup)

# --- ОБРАБОТКА КНОПКИ ---
@bot.message_handler(func=lambda m: m.text == "📤 Отправить расписание" and m.from_user.id == ADMIN_ID)
def request_photo(message):
    user_states[message.from_user.id] = 'waiting_photo'
    bot.send_message(message.chat.id, "📸 Пришли фото расписания.")

# --- ОБРАБОТКА ФОТО ---
@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == 'waiting_photo')
def photo_received(message):
    user_states[message.from_user.id] = 'waiting_start'
    # Сохраняем file_id фото
    user_states[f"{message.from_user.id}_photo"] = message.photo[-1].file_id
    bot.send_message(message.chat.id, "⏰ Введите время начала уроков (например, 08:30):")

# --- ОБРАБОТКА ВРЕМЕНИ НАЧАЛА ---
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_start')
def start_time_received(message):
    start_time = message.text.strip()
    if not is_valid_time(start_time):
        bot.send_message(message.chat.id, "❌ Неверный формат. Введите время в формате ЧЧ:ММ (например, 08:30)")
        return
    user_states[message.from_user.id] = 'waiting_end'
    user_states[f"{message.from_user.id}_start"] = start_time
    bot.send_message(message.chat.id, "⏰ Введите время окончания уроков (например, 15:00):")

# --- ОБРАБОТКА ВРЕМЕНИ КОНЦА ---
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_end')
def end_time_received(message):
    end_time = message.text.strip()
    if not is_valid_time(end_time):
        bot.send_message(message.chat.id, "❌ Неверный формат. Введите время в формате ЧЧ:ММ (например, 15:00)")
        return

    # Получаем сохранённые данные
    photo_id = user_states.get(f"{message.from_user.id}_photo")
    start_time = user_states.get(f"{message.from_user.id}_start")

    # Формируем текст
    caption = (
        f"📅 Расписание на сегодня\n"
        f"🔔 Начало уроков: {start_time}\n"
        f"🔚 Конец уроков: {end_time}"
    )

    try:
        # Отправляем фото с подписью в тему "Расписание"
        bot.send_photo(
            chat_id=GROUP_ID,
            photo=photo_id,
            caption=caption,
            message_thread_id=TOPIC_ID  # ← Это ID темы!
        )
        bot.send_message(message.chat.id, "✅ Расписание отправлено в группу!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка отправки: {e}")
        print(f"Ошибка: {e}")

    # Сброс состояния
    clear_user_state(message.from_user.id)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def is_valid_time(t):
    """Проверяет формат времени HH:MM"""
    try:
        h, m = t.split(':')
        return len(h) == 2 and len(m) == 2 and 0 <= int(h) <= 23 and 0 <= int(m) <= 59
    except:
        return False

def clear_user_state(user_id):
    user_states.pop(user_id, None)
    user_states.pop(f"{user_id}_photo", None)
    user_states.pop(f"{user_id}_start", None)

# === ЗАПУСК ===
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()