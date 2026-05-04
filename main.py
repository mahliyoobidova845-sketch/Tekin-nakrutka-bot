# -*- coding: utf-8 -*-
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart

# ================== CONFIG ==================
BOT_TOKEN = "8324647120:AAEenhdaCF0x0bC7jhD5u9U2ylGjizZOFLI"
ADMIN_ID = 8216710938

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================== DATABASE ==================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    ref_by INTEGER DEFAULT 0,
    ref_given INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT,
    status TEXT DEFAULT 'pending'
)
""")

conn.commit()

# ================== HELPERS ==================
def add_user(uid, ref=None):
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user_id, ref_by) VALUES (?,?)",
            (uid, ref if ref else 0)
        )
        conn.commit()

        # referral bonus (30 so‘m)
        if ref:
            cur.execute("SELECT ref_given FROM users WHERE user_id=?", (uid,))
            if cur.fetchone()[0] == 0:
                cur.execute("UPDATE users SET balance = balance + 30 WHERE user_id=?", (ref,))
                cur.execute("UPDATE users SET ref_given = 1 WHERE user_id=?", (uid,))
                conn.commit()

def get_balance(uid):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()[0]

def add_balance(uid, amount):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()

def add_order(uid, text):
    cur.execute(
        "INSERT INTO orders (user_id, text, status) VALUES (?,?, 'pending')",
        (uid, text)
    )
    conn.commit()

def get_orders(uid):
    cur.execute("SELECT id, text, status FROM orders WHERE user_id=?", (uid,))
    return cur.fetchall()

def update_status(order_id, status):
    cur.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()

# ================== START ==================
@dp.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    ref = int(args[1]) if len(args) > 1 else None

    add_user(message.from_user.id, ref)

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📦 Xizmatlar")],
            [types.KeyboardButton(text="🛒 Buyurtmalarim")],
            [types.KeyboardButton(text="💰 Balans")],
            [types.KeyboardButton(text="👥 Referal")],
            [types.KeyboardButton(text="ℹ️ Bot haqida")]
        ],
        resize_keyboard=True
    )

    await message.answer("🤖 SMM Botga xush kelibsiz!", reply_markup=kb)

# ================== ORDER ==================
@dp.message(F.text == "🛒 Buyurtmalarim")
async def my_orders(message: types.Message):
    data = get_orders(message.from_user.id)

    if not data:
        await message.answer("📭 Buyurtma yo‘q")
        return

    text = "🧾 Sizning buyurtmalaringiz:\n\n"

    for o in data:
        icon = "⏳" if o[2] == "pending" else "✅" if o[2] == "done" else "❌"
        text += f"#{o[0]} {icon}\n{o[1]}\n\n"

    await message.answer(text)

@dp.message(~F.text.in_([
    "💰 Balans",
    "🛒 Buyurtmalarim",
    "📦 Xizmatlar",
    "👥 Referal",
    "ℹ️ Bot haqida"
]))
    if message.text.startswith("/"):
        return

    add_order(message.from_user.id, message.text)

    await message.answer("✅ Buyurtma qabul qilindi!")

    await bot.send_message(
        ADMIN_ID,
        f"📥 Yangi buyurtma\nUser: {message.from_user.id}\n\n{message.text}"
    )

# ================== BALANCE ==================
@dp.message(F.text == "💰 Balans")
async def balance(message: types.Message):
    bal = get_balance(message.from_user.id)
    await message.answer(f"💰 Sizning balansingiz: {bal} so‘m")


async def main():
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())
