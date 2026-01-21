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

from config import BOT_TOKEN, ADMIN_ID

# ---------------- MEMORY ----------------
orders = []
current_token = 0

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["step"] = "address"

    await update.message.reply_text(
        "🍔 Welcome!\n\n"
        "📍 Send your **address link** (Google Maps):"
    )

# ---------------- MESSAGE HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_token
    text = update.message.text
    user = update.message.from_user

    step = context.user_data.get("step")

    # STEP 1: ADDRESS
    if step == "address":
        context.user_data["address"] = text
        context.user_data["step"] = "price"

        await update.message.reply_text(
            "💰 Enter food price (minimum ₹199):"
        )

    # STEP 2: PRICE
    elif step == "price":
        try:
            price = int(text)
            if price < 199:
                await update.message.reply_text("❌ Minimum price is ₹199")
                return

            current_token += 1
            token = current_token
            final_price = price - 100

            order = {
                "token": token,
                "user_id": user.id,
                "name": user.first_name,
                "address": context.user_data["address"],
                "price": final_price,
                "completed": False
            }
            orders.append(order)

            # CUSTOMER MESSAGE
            await update.message.reply_text(
                f"✅ Order Confirmed!\n\n"
                f"🎟 Token: {token}\n"
                f"💰 Payable: ₹{final_price}"
            )

            # ADMIN MESSAGE
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    f"✅ Complete Token {token}",
                    callback_data=f"complete_{token}"
                )
            ]])

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📥 NEW ORDER\n\n"
                    f"👤 {user.first_name}\n"
                    f"🎟 Token: {token}\n"
                    f"📍 Address:\n{order['address']}\n"
                    f"💰 Price: ₹{final_price}"
                ),
                reply_markup=keyboard
            )

            context.user_data.clear()

        except ValueError:
            await update.message.reply_text("❌ Enter a valid number")

# ---------------- ADMIN COMPLETE ----------------
async def complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    token = int(query.data.split("_")[1])

    for order in orders:
        if order["token"] == token and not order["completed"]:
            order["completed"] = True

            # Notify CUSTOMER
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=f"🎉 Your order (Token {token}) is completed!"
            )

            # Update ADMIN message
            await query.edit_message_text(
                f"✅ Token {token} marked as COMPLETED"
            )
            return

    await query.edit_message_text("❌ Order already completed")

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(complete_order))

    print("🤖 Bot running 24/7...")
    app.run_polling()

if __name__ == "__main__":
    main()
