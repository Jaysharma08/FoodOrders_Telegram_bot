from telegram import Update
from telegram.ext import ContextTypes
from data import orders

# ---------------- COMPLETE ORDER ----------------
async def complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data  # example: complete_3
    token = int(data.split("_")[1])

    for order in orders:
        if order["token"] == token and not order["completed"]:
            order["completed"] = True

            customer_id = order["user_id"]

            # ✅ MESSAGE TO CUSTOMER
            await context.bot.send_message(
                chat_id=customer_id,
                text=(
                    f"✅ *Order Completed!*\n\n"
                    f"🎟 Token: {token}\n"
                    f"💸 Final Price: ₹{order['final_price']}\n\n"
                    f"🙏 Thank you for ordering!"
                ),
                parse_mode="Markdown"
            )

            # ✅ CONFIRMATION TO ADMIN
            await query.edit_message_caption(
                caption=(
                    f"✅ *Order Completed*\n\n"
                    f"🎟 Token: {token}\n"
                    f"👤 User ID: `{customer_id}`"
                ),
                parse_mode="Markdown"
            )

            return

    # ❌ If token already completed
    await query.answer("Order already completed!", show_alert=True)
