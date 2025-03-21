import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
import asyncio
import os

TOKEN = "7719962288:AAEl-FYo30lFk_ur-ePMks3fSfBB1GJsgAk"
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Calea către fișierul JSON
DATA_FILE = "drivers_data.json"

# Încărcare date din JSON dacă există
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return {}
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

# Salvare date în JSON
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Inițializare date utilizatori
users_data = load_data()

# Definire stări pentru FSM
class Form(StatesGroup):
    waiting_registration = State()
    waiting_company_name = State()
    waiting_dot_number = State()
    waiting_phone_number = State()
    waiting_bol_photo = State()
    waiting_hours = State()
    waiting_shift_selection = State()
    waiting_hours_input = State()
    waiting_company_name_settings = State()  # Pentru "Change Company Name" în Settings
    waiting_dot_after_company = State()      # Pentru DOT după Company Name în Settings
    waiting_dot_settings = State()           # Pentru "Change DOT" în Settings
    waiting_company_name_after_dot = State() # Pentru Company Name după DOT în Settings
    waiting_phone_number_settings = State()  # Pentru "Change Phone Number" în Settings
    waiting_full_name_change = State()

# Meniu principal
def main_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆕 New Shift", callback_data="new_shift"),
             InlineKeyboardButton(text="🛠️ PTI", callback_data="pti"),
             InlineKeyboardButton(text="⏸️ BREAK", callback_data="break")],
            [InlineKeyboardButton(text="⌛ Hours", callback_data="hours"),
             InlineKeyboardButton(text="🔄 Cycle", callback_data="cycle"),
             InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton(text="ℹ️ Your Info", callback_data="your_info")]
        ],
        row_width=3
    )
    return keyboard

# Meniu setări
def settings_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Change Full Name", callback_data="change_full_name")],
            [InlineKeyboardButton(text="🏢 Change Company Name", callback_data="change_company_name")],
            [InlineKeyboardButton(text="#️⃣ Change DOT", callback_data="change_dot")],
            [InlineKeyboardButton(text="📞 Change Phone Number", callback_data="change_phone")],
            [InlineKeyboardButton(text="⬅️ Back to Main Menu", callback_data="back_to_main")]
        ]
    )
    return keyboard

# Tastatură pentru "Your Info"
def your_info_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main"),
             InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")]
        ]
    )
    return keyboard

# Tastatură pentru "Hours"
def hours_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚗 Driving", callback_data="hours_driving")],
            [InlineKeyboardButton(text="⏰ Shift", callback_data="hours_shift")],
            [InlineKeyboardButton(text="🚗⏰ Driving and Shift", callback_data="hours_driving_shift")],
            [InlineKeyboardButton(text="🔄 Cycle", callback_data="hours_cycle")]
        ]
    )
    return keyboard

# Formatare date șofer
def format_driver_info(user_id):
    data = users_data.get(str(user_id), {})
    return (
        f"👤 Full Name: {data.get('full_name', 'N/A')}\n"
        f"🏢 Company: {data.get('company_name', 'N/A')}\n"
        f"#️⃣ DOT Number: {data.get('dot', 'N/A')}\n"
        f"📞 Phone: {data.get('phone', 'N/A')}"
    )

# Start & verificare înregistrare
@dp.message(Command("start"))
async def send_welcome(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in users_data:
        await message.answer("🔑 Please register before using the bot. Enter your full name:")
        await state.set_state(Form.waiting_registration)
    else:
        await message.answer("🚛 Welcome back! Choose an option:", reply_markup=main_menu())

# Proces înregistrare
@dp.message(StateFilter(Form.waiting_registration))
async def process_full_name(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users_data[user_id] = {"full_name": message.text}
    save_data(users_data)
    await message.answer("🏢 Enter your Company Name:")
    await state.set_state(Form.waiting_company_name)

@dp.message(StateFilter(Form.waiting_company_name))
async def process_company_name(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users_data[user_id]["company_name"] = message.text
    save_data(users_data)
    await message.answer("#️⃣ Enter your DOT Number (only digits):")
    await state.set_state(Form.waiting_dot_number)

@dp.message(StateFilter(Form.waiting_dot_number))
async def process_dot_number(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if not message.text.isdigit():
        await message.answer("❌ DOT must contain only numbers. Try again:")
        return
    users_data[user_id]["dot"] = message.text
    save_data(users_data)
    await message.answer("📞 Enter your phone number:")
    await state.set_state(Form.waiting_phone_number)

@dp.message(StateFilter(Form.waiting_phone_number))
async def process_phone_number(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if not all(c.isdigit() or c in "-()" for c in message.text):
        await message.answer("❌ Invalid phone number format. Try again:")
        return
    users_data[user_id]["phone"] = message.text
    save_data(users_data)
    await message.answer("✅ Registration complete!", reply_markup=main_menu())
    await state.clear()

# Gestionare butoane
@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    user_id = str(callback_query.from_user.id)

    if user_id not in users_data:
        await callback_query.message.answer("❌ You need to register first. Send /start")
        return

    if data == "new_shift":
        await state.set_state(Form.waiting_shift_selection)
        await state.update_data(selected_option="🆕 New Shift")
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Yes", callback_data="pickup_yes")],
                [InlineKeyboardButton(text="No", callback_data="pickup_no")]
            ]
        )
        await callback_query.message.answer("📦 Did you have a pick-up today?", reply_markup=markup)
        await callback_query.answer()

    elif data == "pickup_no":
        info_text = (
            f"📋 New Shift (No Pickup)\n"
            f"🏢 Company Name: {users_data[user_id]['company_name']}\n"
            f"#️⃣ DOT: {users_data[user_id]['dot']}\n"
            f"👤 Driver Full Name: {users_data[user_id]['full_name']}\n"
            f"📞 Phone Number: {users_data[user_id]['phone']}"
        )
        await bot.send_message(chat_id=7059322085, text=info_text)
        await callback_query.message.answer("✅ The information has been recorded.", reply_markup=main_menu())
        await state.clear()
        await callback_query.answer()

    elif data == "pickup_yes":
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Yes", callback_data="bol_yes")],
                [InlineKeyboardButton(text="No", callback_data="bol_no")]
            ]
        )
        await callback_query.message.answer("📝 Does your BOL have a Time or Date?", reply_markup=markup)
        await callback_query.answer()

    elif data == "bol_yes":
        await callback_query.message.answer("📸 Please take a clear photo of the BOL and send it here.")
        await state.set_state(Form.waiting_bol_photo)
        await callback_query.answer()

    elif data == "bol_no":
        info_text = (
            f"📋 New Shift (Pickup Yes, BOL No Time/Date)\n"
            f"🏢 Company Name: {users_data[user_id]['company_name']}\n"
            f"#️⃣ DOT: {users_data[user_id]['dot']}\n"
            f"👤 Driver Full Name: {users_data[user_id]['full_name']}\n"
            f"📞 Phone Number: {users_data[user_id]['phone']}"
        )
        await bot.send_message(chat_id=7059322085, text=info_text)
        await callback_query.message.answer("✅ The information has been recorded.", reply_markup=main_menu())
        await state.clear()
        await callback_query.answer()

    elif data == "pti":
        await callback_query.message.answer("🔄 We are in the process of working. Thank you for your patience!", reply_markup=main_menu())
        info_text = (
            f"📋 PTI\n"
            f"🏢 Company Name: {users_data[user_id]['company_name']}\n"
            f"#️⃣ DOT: {users_data[user_id]['dot']}\n"
            f"👤 Driver Full Name: {users_data[user_id]['full_name']}\n"
            f"📞 Phone Number: {users_data[user_id]['phone']}"
        )
        await bot.send_message(chat_id=7059322085, text=info_text)
        await callback_query.answer()

    elif data == "break":
        await callback_query.message.answer("🔄 We are in the process of working. Thank you for your patience!", reply_markup=main_menu())
        info_text = (
            f"📋 BREAK\n"
            f"🏢 Company Name: {users_data[user_id]['company_name']}\n"
            f"#️⃣ DOT: {users_data[user_id]['dot']}\n"
            f"👤 Driver Full Name: {users_data[user_id]['full_name']}\n"
            f"📞 Phone Number: {users_data[user_id]['phone']}"
        )
        await bot.send_message(chat_id=7059322085, text=info_text)
        await callback_query.answer()

    elif data == "hours":
        await callback_query.message.answer("⌛ Select an option:", reply_markup=hours_menu())
        await callback_query.answer()

    elif data in ["hours_driving", "hours_shift", "hours_driving_shift", "hours_cycle"]:
        hours_type = {
            "hours_driving": "Driving",
            "hours_shift": "Shift",
            "hours_driving_shift": "Driving and Shift",
            "hours_cycle": "Cycle"
        }[data]
        await state.set_state(Form.waiting_hours_input)
        await state.update_data(hours_type=hours_type)
        await callback_query.message.answer(f"⏱️ How many hours for {hours_type}? (ex. 3, 5 hours, etc.):")
        await callback_query.answer()

    elif data == "cycle":
        await callback_query.message.answer("🔄 We are in the process of working. Thank you for your patience!", reply_markup=main_menu())
        info_text = (
            f"📋 Button Pressed: Cycle\n"
            f"🏢 Company Name: {users_data[user_id]['company_name']}\n"
            f"#️⃣ DOT: {users_data[user_id]['dot']}\n"
            f"👤 Driver Full Name: {users_data[user_id]['full_name']}\n"
            f"📞 Phone Number: {users_data[user_id]['phone']}"
        )
        await bot.send_message(chat_id=7059322085, text=info_text)
        await callback_query.answer()

    elif data == "settings":
        await callback_query.message.answer("⚙️ Settings Menu:", reply_markup=settings_menu())
        await callback_query.answer()

    elif data == "your_info":
        info_text = f"ℹ️ Your Info:\n{format_driver_info(user_id)}"
        await callback_query.message.answer(info_text, reply_markup=your_info_menu())
        await callback_query.answer()

    elif data == "change_company_name":
        await callback_query.message.answer("🏢 Enter new Company Name:")
        await state.set_state(Form.waiting_company_name_settings)
        await callback_query.answer()

    elif data == "change_dot":
        await callback_query.message.answer("#️⃣ Enter new DOT Number (only digits):")
        await state.set_state(Form.waiting_dot_settings)
        await callback_query.answer()

    elif data == "change_phone":
        await callback_query.message.answer("📞 Enter new Phone Number:")
        await state.set_state(Form.waiting_phone_number_settings)
        await callback_query.answer()

    elif data == "change_full_name":
        await callback_query.message.answer("👤 Enter new Full Name:")
        await state.set_state(Form.waiting_full_name_change)
        await callback_query.answer()

    elif data == "back_to_main":
        await callback_query.message.answer("🚛 Back to Main Menu:", reply_markup=main_menu())
        await callback_query.answer()

# Gestionare modificări în Settings
@dp.message(StateFilter(Form.waiting_company_name_settings))
async def handle_company_name_settings(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users_data[user_id]["company_name"] = message.text
    save_data(users_data)
    await message.answer("#️⃣ Now enter your new DOT Number (only digits):")
    await state.set_state(Form.waiting_dot_after_company)

@dp.message(StateFilter(Form.waiting_dot_after_company))
async def handle_dot_after_company(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if not message.text.isdigit():
        await message.answer("❌ DOT must contain only numbers. Try again:")
        return
    users_data[user_id]["dot"] = message.text
    save_data(users_data)
    await message.answer("✅ Company Name and DOT updated successfully!", reply_markup=settings_menu())
    await state.clear()

@dp.message(StateFilter(Form.waiting_dot_settings))
async def handle_dot_settings(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if not message.text.isdigit():
        await message.answer("❌ DOT must contain only numbers. Try again:")
        return
    users_data[user_id]["dot"] = message.text
    save_data(users_data)
    await message.answer("🏢 Now enter your new Company Name:")
    await state.set_state(Form.waiting_company_name_after_dot)

@dp.message(StateFilter(Form.waiting_company_name_after_dot))
async def handle_company_name_after_dot(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users_data[user_id]["company_name"] = message.text
    save_data(users_data)
    await message.answer("✅ DOT and Company Name updated successfully!", reply_markup=settings_menu())
    await state.clear()

@dp.message(StateFilter(Form.waiting_phone_number_settings))
async def handle_phone_settings(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if not all(c.isdigit() or c in "-()" for c in message.text):
        await message.answer("❌ Invalid phone number format. Try again:")
        return
    users_data[user_id]["phone"] = message.text
    save_data(users_data)
    await message.answer("📞 Phone number updated successfully!", reply_markup=settings_menu())
    await state.clear()

@dp.message(StateFilter(Form.waiting_full_name_change))
async def handle_full_name_change(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users_data[user_id]["full_name"] = message.text
    save_data(users_data)
    await message.answer("👤 Full Name updated successfully!", reply_markup=settings_menu())
    await state.clear()

# Gestionare poză BOL
@dp.message(StateFilter(Form.waiting_bol_photo))
async def handle_bol_photo(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if message.photo:
        info_text = (
            f"📋 New Shift (Pickup Yes, BOL Yes)\n"
            f"🏢 Company Name: {users_data[user_id]['company_name']}\n"
            f"#️⃣ DOT: {users_data[user_id]['dot']}\n"
            f"👤 Driver Full Name: {users_data[user_id]['full_name']}\n"
            f"📞 Phone Number: {users_data[user_id]['phone']}"
        )
        await bot.send_photo(
            chat_id=7059322085,
            photo=message.photo[-1].file_id,
            caption=info_text
        )
        await message.answer("📸 The BOL and information have been sent to support!", reply_markup=main_menu())
    else:
        await message.answer("❌ Please send a photo of the BOL!")
        return
    await state.clear()

# Gestionare introducere ore
@dp.message(StateFilter(Form.waiting_hours_input))
async def handle_hours_input(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    hours_input = message.text.strip()
    data = await state.get_data()
    hours_type = data["hours_type"]

    info_text = (
        f"⏱️ {hours_type}: {hours_input}\n"
        f"🏢 Company Name: {users_data[user_id]['company_name']}\n"
        f"#️⃣ DOT: {users_data[user_id]['dot']}\n"
        f"👤 Driver Full Name: {users_data[user_id]['full_name']}\n"
        f"📞 Phone Number: {users_data[user_id]['phone']}"
    )
    await bot.send_message(chat_id=7059322085, text=info_text)
    await message.answer("✅ The hours have been recorded!", reply_markup=main_menu())
    await state.clear()

# Start polling
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())