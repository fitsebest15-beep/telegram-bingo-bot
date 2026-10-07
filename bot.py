import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# የቦት ቶከንዎ
API_TOKEN = "8998713585:AAH2e69oCHMvMA6X-IAvTXU9YCPGg-JvJ5o"

# የቴሌብር መረጃዎ
TELEBIRR_NUMBER = "0965538136"
TELEBIRR_NAME = "Fitsum"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# የውሂብ ማከማቻ ዲክሽነሪ
users_db = {}

class DepositStates(StatesGroup):
    waiting_for_amount = State()

class WithdrawStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_phone = State()

# /start ትዕዛዝ (ሪፈራልን ጨምሮ)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].split("_")[1])
        except ValueError:
            pass

    if user_id not in users_db:
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Register (ተመዝገብ)", callback_data=f"register_{referrer_id or 0}")
        await message.answer(
            "🎉 ወደ ቢንጎ ጨዋታ ቦት በደህና መጡ!\n\n"
            "ለመጫወት እና ቦነሶችን ለማግኘት ከታች ያለውን በመጫን ይመዝገቡ።",
            reply_markup=builder.as_markup()
        )
    else:
        await show_main_menu(message)

@dp.callback_query(F.data.startswith("register_"))
async def process_register(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    referrer_id = int(callback.data.split("_")[1])
    
    if user_id not in users_db:
        users_db[user_id] = {
            "name": callback.from_user.full_name,
            "balance": 0.0,
            "plays_left": 10,
            "total_deposited": 0.0,
            "invited_count": 0
        }
        
        if referrer_id and referrer_id in users_db and referrer_id != user_id:
            users_db[referrer_id]["balance"] += 5.0
            users_db[referrer_id]["invited_count"] += 1
            try:
                await bot.send_message(
                    referrer_id, 
                    "🎉 እንኳን ደስ አለዎት! አንድ ጓደኛ በመጋበዝዎ **5 ብር** ወደ ሂሳብዎ ገብቷል!"
                )
            except:
                pass

        await callback.message.answer(
            "✅ ምዝገባዎ በተሳካ ሁኔታ ተጠናቋል!\n"
            "🎁 የ **10 የጫወታ ቻንስ** ተሰጥቶዎታል።"
        )
    
    await show_main_menu_callback(callback)
    await callback.answer()

async def show_main_menu(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="💰 Balance", callback_data="btn_balance"),
        types.InlineKeyboardButton(text="📥 Deposit (Telebirr)", callback_data="btn_deposit")
    )
    builder.row(
        types.InlineKeyboardButton(text="📤 Withdraw", callback_data="btn_withdraw"),
        types.InlineKeyboardButton(text="👥 Invite", callback_data="btn_invite")
    )
    builder.row(
        types.InlineKeyboardButton(text="🎲 Play Bingo", callback_data="btn_play")
    )
    await message.answer("እንኳን ደህና መጡ! የሚፈልጉትን አማራጭ ይጫኑ፦", reply_markup=builder.as_markup())

async def show_main_menu_callback(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="💰 Balance", callback_data="btn_balance"),
        types.InlineKeyboardButton(text="📥 Deposit (Telebirr)", callback_data="btn_deposit")
    )
    builder.row(
        types.InlineKeyboardButton(text="📤 Withdraw", callback_data="btn_withdraw"),
        types.InlineKeyboardButton(text="👥 Invite", callback_data="btn_invite")
    )
    builder.row(
        types.InlineKeyboardButton(text="🎲 Play Bingo", callback_data="btn_play")
    )
    await callback.message.edit_text("እንኳን ደህና መጡ! የሚፈልጉትን አማራጭ ይጫኑ፦", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "btn_balance")
async def process_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = users_db.get(user_id, {"balance": 0.0, "plays_left": 0})
    balance = user_data["balance"]
    plays = user_data["plays_left"]
    
    text = f"💰 **የእርስዎ ሂሳብ መግለጫ**\n\n• ቀሪ ገንዘብ: **{balance} ETB**\n• የቀረዎ የጫወታ ቻንስ: **{plays} ጊዜ**"
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "btn_deposit")
async def process_deposit(callback: types.CallbackQuery, state: FSMContext):
    text = (
        f"📥 **ገንዘብ ማስገባት (Deposit)**\n\n"
        f"⚠️ **ማስታወሻ:** ዝቅተኛው የማስገቢያ መጠን **50 ብር** ነው።\n\n"
        f"እባክዎ ከታች ባለው የቴሌብር አካውንት ገንዘብ ያስተላልፉ፦\n"
        f"• **Telebirr ቁጥር:** `{TELEBIRR_NUMBER}`\n"
        f"• **ስም:** {TELEBIRR_NAME}\n\n"
        f"ክፍያውን ከፈጸሙ በኋላ ያስተላለፉትን መጠን (በብር) ይጻፉልን:"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await state.set_state(DepositStates.waiting_for_amount)
    await callback.answer()

@dp.message(DepositStates.waiting_for_amount)
async def receive_deposit_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 50:
            await message.answer("⚠️ ዝቅተኛው የገንዘብ ማስገቢያ መጠን 50 ብር ነው። እባክዎ ከ 50 በላይ ያስገቡ።")
            return
            
        user_id = message.from_user.id
        users_db[user_id]["balance"] += amount
        users_db[user_id]["total_deposited"] += amount
        
        await message.answer(f"✅ የ {amount} ETB ተቀማጭ ጥያቄዎ ተመዝግቧል! ሂሳብዎ ተዘምኗል።")
        await state.clear()
        await show_main_menu(message)
    except ValueError:
        await message.answer("❌ እባክዎ ትክክለኛ ቁጥር ብቻ ያስገቡ (ለምሳሌ፦ 50 ወይም 100)")

@dp.callback_query(F.data == "btn_withdraw")
async def process_withdraw(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = users_db.get(user_id, {"balance": 0.0, "total_deposited": 0.0})
    
    if user_data["total_deposited"] <= 0:
        await callback.message.answer("⚠️ ገንዘብ ማውጣት የሚችሉት ቢያንስ አንድ ጊዜ **Deposit** ካደረጉ በኋላ ብቻ ነው።")
        await callback.answer()
        return
        
    balance = user_data["balance"]
    if balance < 100:
        await callback.message.answer(f"⚠️ ማውጣት የሚችሉት ቢያንስ **100 ብር** እና ከዛ በላይ ሲኖርዎት ነው! (አሁን ያለዎት: {balance} ብር)")
        await callback.answer()
        return
    
    await callback.message.answer(f"📤 አሁን ያለዎት ቀሪ ሂሳብ {balance} ETB ነው። ማውጣት የሚፈልጉትን መጠን ይጻፉ (ዝቅተኛው 100 ብር):")
    await state.set_state(WithdrawStates.waiting_for_amount)
    await callback.answer()

@dp.message(WithdrawStates.waiting_for_amount)
async def receive_withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        
        if amount < 100:
            await message.answer("⚠️ ዝቅተኛው የማውጣት መጠን 100 ብር ነው።")
            return
            
        if amount > users_db[user_id]["balance"]:
            await message.answer("⚠️ ከቀሪ ሂሳብዎ በላይ ማውጣት አይችሉም!")
            return
        
        await state.update_data(withdraw_amount=amount)
        await message.answer("📱 ገንዘቡ የሚቀበሉበትን የቴሌብር ስልክ ቁጥር ያስገቡ (ምሳሌ፦ 09xxxxxxxx):")
        await state.set_state(WithdrawStates.waiting_for_phone)
    except ValueError:
        await message.answer("❌ እባክዎ ትክክለኛ ቁጥር ያስገቡ።")

@dp.message(WithdrawStates.waiting_for_phone)
async def receive_withdraw_phone(message: types.Message, state: FSMContext):
    phone = message.text
    data = await state.get_data()
    amount = data.get("withdraw_amount")
    user_id = message.from_user.id
    
    users_db[user_id]["balance"] -= amount
    await message.answer(f"✅ የ {amount} ETB የማውጣት ጥያቄ ወደ ቴሌብር ቁጥር ({phone}) ተልኳል! በአጭር ጊዜ ውስጥ ይለቀቃል።")
    await state.clear()
    await show_main_menu(message)

@dp.callback_query(F.data == "btn_invite")
async def process_invite(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    user_id = callback.from_user.id
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    text = (
        f"👥 **ጓደኞችን ይጋብዙ እና ይሸለሙ!**\n\n"
        f"ይህንን ሊንክ ለጓደኛዎ በማጋራት ቦቱን እንዲጠቀሙ ያድርጉ፦\n"
        f"`{ref_link}`\n\n"
        f"🎁 እያንዳንዱ የጋበዙት ሰው ሲመዘገብ **5 ብር** ጉርሻ ያገኛሉ!"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "btn_play")
async def process_play(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = users_db.get(user_id, {"plays_left": 0})
    
    if user_data["plays_left"] <= 0:
        await callback.message.answer("⚠️ የሚጫወቱት የጫወታ ቻንስ (Plays) አልቆብዎታል። ተጨማሪ ለመጫወት ጓደኞችን ይጋብዙ ወይም ዴፖዚት ያድርጉ!")
        await callback.answer()
        return

    users_db[user_id]["plays_left"] -= 1
    remaining_plays = users_db[user_id]["plays_left"]
    
    await callback.message.answer(f"🎲 የቢንጎ ጨዋታ ተጀምሯል! (ቀሪ ቻንስዎ: {remaining_plays})\n\nቁጥሮች እየተጠሩ ነው...")
    await callback.answer()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
