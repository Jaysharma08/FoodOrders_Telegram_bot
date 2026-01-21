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
import os

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")        # Railway variable
ADMIN_ID = int(os.getenv("ADMIN_ID"))     # Railway variable

# ================= DATA =================
orders = []
current_token = 0

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍔 *Welcome to Food Order Bot*\n\n"
        "📍 Please send your Delivery *address link*.",
        parse_mode="Markdown"
    )
    context.user_data.clear()
    context.user_data["step"] = "address"

# ================= HANDLE TEXT =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_token
    text = update.message.text
    step = context.user_data.get("step")

    # ---- ADDRESS STEP ----
    if step == "address":
        context.user_data["address"] = text
        context.user_data["step"] = "card"
        await update.message.reply_text("💳 Please send your "Swiggy Food card (Image).")

    # ---- PRICE STEP ----
    elif step == "price":
        try:
            price = int(text)

            if price < 199:
                await update.message.reply_text("❌ Minimum price is ₹199")
                return

            final_price = price - 101
            current_token += 1
            token = current_token

            order = {
                "token": token,
                "user_id": update.message.from_user.id,
                "name": update.message.from_user.first_name,
                "address": context.user_data["address"],
                "card_file_id": context.user_data["card_file_id"],
                "original_price": price,
                "final_price": final_price,
                "completed": False
            }
            orders.append(order)

            # CUSTOMER MESSAGE
            await update.message.reply_text(
                f"✅ *Order Confirmed*\n\n"
                f"🎟 Token: {token}\n"
                f"💰 Original: ₹{price}\n"
                f"💸 Final: ₹{final_price}",
                parse_mode="Markdown"
            )

            # ADMIN MESSAGE
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    f"✅ Complete Token {token}",
                    callback_data=f"complete_{token}"
                )
            ]])

            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=order["card_file_id"],
                caption=(
                    f"📥 *New Order*\n\n"
                    f"👤 {order['name']}\n"
                    f"🆔 {order['user_id']}\n"
                    f"📍 Address:\n{order['address']}\n\n"
                    f"🎟 Token: {token}\n"
                    f"💰 Original: ₹{price}\n"
                    f"💸 Final: ₹{final_price}"
                ),
                parse_mode="Markdown",
                reply_markup=keyboard
            )

            context.user_data.clear()

        except ValueError:
            await update.message.reply_text("❌ Enter valid price")

# ================= HANDLE PHOTO =================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") != "card":
        return

    photo = update.message.photo[-1]
    context.user_data["card_file_id"] = photo.file_id
    context.user_data["step"] = "price"

    await update.message.reply_text(
        "💰 Enter food price (minimum ₹199):"
    )

# ================= ADMIN COMPLETE =================
async def complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    token = int(query.data.split("_")[1])

    for order in orders:
        if order["token"] == token and not order["completed"]:
            order["completed"] = True

            # ADMIN CONFIRM
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ *Order Completed*",
                parse_mode="Markdown"
            )

            # CUSTOMER MESSAGE
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=f"🎉 Your order (Token {token}) is *completed!*",
                parse_mode="Markdown"
            )
            return

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(complete_order))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()


