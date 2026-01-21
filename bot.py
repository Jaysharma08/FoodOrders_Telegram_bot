from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)

from config import BOT_TOKEN, ADMIN_ID
from data import orders, get_next_token
from admin import complete_order

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["step"] = "address"

    await update.message.reply_text(
        "🍔 Welcome!\n\n"
        "📍 Send your delivery address or Google Maps link:"
    )

# ---------------- USER HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    step = context.user_data.get("step")

    # -------- ADDRESS --------
    if step == "address" and update.message.text:
        context.user_data["address"] = update.message.text
        context.user_data["step"] = "card"

        await update.message.reply_text(
            "💳 Send card image (photo only):"
        )
        return

    # -------- CARD IMAGE --------
    if step == "card" and update.message.photo:
        photo = update.message.photo[-1]
        context.user_data["card_file_id"] = photo.file_id
        context.user_data["step"] = "price"

        await update.message.reply_text(
            "💰 Enter food price (minimum ₹199):"
        )
        return

    # -------- PRICE --------
    if step == "price" and update.message.text:
        try:
            price = int(update.message.text)
            if price < 199:
                await update.message.reply_text("❌ Minimum price is ₹199.")
                return

            token = get_next_token()
            final_price = price - 100
            wait_time = token * 5

            order = {
                "user_id": user.id,
                "name": user.first_name,
                "address": context.user_data["address"],
                "card_file_id": context.user_data["card_file_id"],
                "original_price": price,
                "final_price": final_price,
                "token": token,
                "completed": False
            }
            orders.append(order)

            # ----- CUSTOMER MESSAGE -----
            await update.message.reply_text(
                f"✅ Order Confirmed!\n\n"
                f"🎟 Token: {token}\n"
                f"💰 Price: ₹{price}\n"
                f"💸 Final: ₹{final_price}\n"
                f"⏳ Waiting: ~{wait_time} min"
            )

            # ----- ADMIN CARD -----
            keyboard = [[
                InlineKeyboardButton(
                    f"✅ Complete Token {token}",
                    callback_data=f"complete_{token}"
                )
            ]]

            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=context.user_data["card_file_id"],
                caption=(
                    f"📥 *New Order*\n\n"
                    f"👤 {user.first_name}\n"
                    f"🆔 `{user.id}`\n\n"
                    f"📍 Address:\n{context.user_data['address']}\n\n"
                    f"🎟 Token: {token}\n"
                    f"💰 Final Price: ₹{final_price}"
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            context.user_data.clear()

        except ValueError:
            await update.message.reply_text("❌ Enter valid price.")

# ---------------- MAIN ----------------
def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    app.add_handler(CallbackQueryHandler(complete_order))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
