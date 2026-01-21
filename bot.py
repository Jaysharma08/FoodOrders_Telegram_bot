import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================== ENV ==================
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

# ================== MEMORY ==================
orders = {}
current_token = 0

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["step"] = "address"

    await update.message.reply_text(
        "🍔 Welcome to Food Order Bot\n\n"
        "📍 Send your ADDRESS (Google Maps link preferred)"
    )

# ================== HANDLE TEXT ==================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_token
    user = update.message.from_user
    text = update.message.text
    step = context.user_data.get("step")

    # ---- ADDRESS ----
    if step == "address":
        context.user_data["address"] = text
        context.user_data["step"] = "price"

        await update.message.reply_text(
            "💰 Enter food price (minimum ₹199)"
        )

    # ---- PRICE ----
    elif step == "price":
        try:
            price = int(text)
            if price < 199:
                await update.message.reply_text("❌ Minimum price is ₹199")
                return

            context.user_data["price"] = price
            context.user_data["step"] = "card"

            await update.message.reply_text(
                "💳 Send CARD IMAGE (photo)"
            )

        except ValueError:
            await update.message.reply_text("❌ Enter valid number")

# ================== HANDLE CARD IMAGE ==================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_token
    user = update.message.from_user

    if context.user_data.get("step") != "card":
        return

    current_token += 1
    token = current_token

    price = context.user_data["price"]
    final_price = price - 100
    wait_time = token * 5
    address = context.user_data["address"]

    file_id = update.message.photo[-1].file_id

    orders[token] = {
        "user_id": user.id,
        "address": address,
        "price": price,
        "final_price": final_price,
        "completed": False
    }

    # -------- CUSTOMER MESSAGE --------
    await update.message.reply_text(
        f"✅ Order Confirmed!\n\n"
        f"🎟 Token No: {token}\n"
        f"💰 Original Price: ₹{price}\n"
        f"💸 Final Price: ₹{final_price}\n"
        f"⏳ Waiting Time: ~{wait_time} min"
    )

    # -------- ADMIN MESSAGE --------
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"✅ Complete Token {token}",
            callback_data=f"complete_{token}"
        )]
    ])

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=file_id,
        caption=(
            f"📥 NEW ORDER\n\n"
            f"🎟 Token: {token}\n"
            f"👤 User ID: {user.id}\n"
            f"📍 Address:\n{address}\n\n"
            f"💰 Price: ₹{final_price}"
        ),
        reply_markup=keyboard
    )

    context.user_data.clear()

# ================== ADMIN COMPLETE ==================
async def complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Not authorized", show_alert=True)
        return

    token = int(query.data.split("_")[1])
    order = orders.get(token)

    if not order or order["completed"]:
        await query.edit_message_text("⚠️ Already completed or invalid token")
        return

    order["completed"] = True

    # Notify customer
    await context.bot.send_message(
        chat_id=order["user_id"],
        text=(
            f"🎉 Your order (Token {token}) is COMPLETED!\n"
            f"Enjoy your food 😄"
        )
    )

    await query.edit_message_text(
        f"✅ Token {token} marked as COMPLETED"
    )

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(complete_order))

    print("🤖 Bot running 24×7...")
    app.run_polling()

if __name__ == "__main__":
    main()
