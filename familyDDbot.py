    #python family bot

import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        ContextTypes,
        ConversationHandler,
        CallbackQueryHandler,
    )

    # Enable logging
logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
logger = logging.getLogger(__name__)

    # Define conversation states with unique values
START, MAIN_MENU, VIEW_POINTS, VIEW_HISTORY, OPERATION_MENU, SELECT_PERSON, \
        SELECT_OPERATION, ADD_REASON, ADD_AMOUNT, SELECT_TRANSFER_TARGET, \
        VERIFY_OPERATION = range(11)


    # File to store points and history
POINTS_FILE = "family_points.json"
HISTORY_FILE = "points_history.json"

    # Default data structure
DEFAULT_POINTS = {
        "Tima": 0,
        "Vlad": 0,
        "Danya": 0,
        "Mama": 0,
        "Papa": 0
    }

DEFAULT_HISTORY = []

    # Helper functions for data management
def load_points():
        """Load points from file or create with default values if file doesn't exist."""
        if os.path.exists(POINTS_FILE):
            with open(POINTS_FILE, 'r') as file:
                return json.load(file)
        else:
            save_points(DEFAULT_POINTS)
            return DEFAULT_POINTS

def save_points(points_data):
        """Save points data to file."""
        with open(POINTS_FILE, 'w') as file:
            json.dump(points_data, file, indent=4)

def load_history():
        """Load history from file or create with default values if file doesn't exist."""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as file:
                return json.load(file)
        else:
            save_history(DEFAULT_HISTORY)
            return DEFAULT_HISTORY

def save_history(history_data):
        """Save history data to file."""
        with open(HISTORY_FILE, 'w') as file:
            json.dump(history_data, file, indent=4)

def add_to_history(action_type, person, amount, reason=None, target=None, verified_by=None):
        """Add a new action to history."""
        history = load_history()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "timestamp": timestamp,
            "type": action_type,
            "person": person,
            "amount": amount
        }

        if reason:
            entry["reason"] = reason
        if target:
            entry["target"] = target
        if verified_by:
            entry["verified_by"] = verified_by

        history.append(entry)
        save_history(history)

def format_points_table():
        """Format points data as a readable table."""
        points = load_points()
        table = "📊 *Family Points Table* 📊\n\n"
        for person, point in points.items():
            table += f"• *{person}*: {point} points\n"
        return table

def format_history(limit=10):
        """Format history data as a readable list, limited to the most recent entries."""
        history = load_history()
        if not history:
            return "No history available yet."

        # Get most recent entries
        recent_history = history[-limit:] if len(history) > limit else history
        recent_history.reverse()  # Show newest first

        formatted = "📜 *Recent Points History* 📜\n\n"
        for i, entry in enumerate(recent_history, 1):
            timestamp = entry["timestamp"]
            person = entry["person"]
            amount = entry["amount"]

            if entry["type"] == "add":
                reason = entry.get("reason", "No reason provided")
                verified_by = entry.get("verified_by", "Not verified")
                formatted += f"{i}. {timestamp}\n   *{person}* gained {amount} points\n   Reason: {reason}\n   Verified by: {verified_by}\n\n"

            elif entry["type"] == "subtract":
                reason = entry.get("reason", "No reason provided")
                verified_by = entry.get("verified_by", "Not verified")
                formatted += f"{i}. {timestamp}\n   *{person}* lost {amount} points\n   Reason: {reason}\n   Verified by: {verified_by}\n\n"

            elif entry["type"] == "transfer":
                target = entry.get("target", "Unknown")
                formatted += f"{i}. {timestamp}\n   *{person}* transferred {amount} points to *{target}*\n\n"

        return formatted

    # Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the conversation and display welcome message."""
        user = update.effective_user
        await update.message.reply_text(
            f"👋 Welcome to the Family Points Bot, {user.first_name}!\n\n"
            f"This bot helps track points for family members: Tima, Vlad, Danya, Mama, and Papa.\n\n"
            f"What would you like to do?"
        )
        return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the main menu with options."""
        keyboard = [
            [InlineKeyboardButton("View Points", callback_data="view_points")],
            [InlineKeyboardButton("Manage Points", callback_data="manage_points")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Handle both direct messages and callback queries
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text="Please select an option:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text="Please select an option:",
                reply_markup=reply_markup
            )

        return MAIN_MENU

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user selection from main menu."""
        query = update.callback_query
        await query.answer()

        if query.data == "view_points":
            await show_points_table(update, context)
            return VIEW_POINTS
        elif query.data == "manage_points":
            return await show_person_selection(update, context)

        return MAIN_MENU

async def show_points_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display the current points table."""
        table = format_points_table()

        keyboard = [
            [InlineKeyboardButton("View History", callback_data="view_history")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=table,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        return VIEW_POINTS

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display the points history."""
        history = format_history()

        keyboard = [
            [InlineKeyboardButton("Back to Points Table", callback_data="back_to_points")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=history,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        return VIEW_HISTORY

async def handle_view_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user selection from view menu."""
        query = update.callback_query
        await query.answer()

        if query.data == "view_history":
            await show_history(update, context)
            return VIEW_HISTORY
        elif query.data == "back_to_main":
            return await show_main_menu(update, context)
        elif query.data == "back_to_points":
            await show_points_table(update, context)
            return VIEW_POINTS

        return VIEW_POINTS

async def show_person_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ask the user to identify themselves."""
        query = update.callback_query

        keyboard = []
        points = load_points()
        for person in points.keys():
            keyboard.append([InlineKeyboardButton(person, callback_data=f"person_{person}")])

        keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="Who are you?",
            reply_markup=reply_markup
        )

        return SELECT_PERSON

async def handle_person_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle person selection and show operation options."""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_main":
            return await show_main_menu(update, context)

        person = query.data.split("_")[1]
        context.user_data["person"] = person

        keyboard = [
            [InlineKeyboardButton("Add Points", callback_data="operation_add")],
            [InlineKeyboardButton("Subtract Points", callback_data="operation_subtract")],
            [InlineKeyboardButton("Transfer Points", callback_data="operation_transfer")],
            [InlineKeyboardButton("Back", callback_data="back_to_person_select")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"Hello, {person}! What would you like to do?",
            reply_markup=reply_markup
        )

        return SELECT_OPERATION

async def handle_operation_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle operation selection."""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_person_select":
            return await show_person_selection(update, context)

        operation = query.data.split("_")[1]
        context.user_data["operation"] = operation

        if operation in ["add", "subtract"]:
            # Send a new message instead of editing the existing one
            # This is critical for transitioning to text input
            await query.message.reply_text(
                text=f"Please enter a reason for {operation}ing points:"
            )
            # This return value tells the ConversationHandler which state to go to next
            return ADD_REASON
        elif operation == "transfer":
            return await show_transfer_targets(update, context)

        return SELECT_OPERATION


async def show_transfer_targets(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available transfer targets."""
        person = context.user_data.get("person")

        keyboard = []
        points = load_points()

        for target in points.keys():
            if target != person:  # Can't transfer to self
                keyboard.append([InlineKeyboardButton(target, callback_data=f"target_{target}")])

        keyboard.append([InlineKeyboardButton("Back", callback_data="back_to_operation")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=f"Who would you like to transfer points to?",
            reply_markup=reply_markup
        )

        return SELECT_TRANSFER_TARGET

async def handle_transfer_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle transfer target selection."""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_operation":
            return await handle_person_selection(update, context)

        target = query.data.split("_")[1]
        context.user_data["target"] = target

        await query.edit_message_text(
            text=f"How many points do you want to transfer to {target}?"
        )

        return ADD_AMOUNT

async def handle_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Store the reason and ask for amount."""
        reason = update.message.text
        context.user_data["reason"] = reason

        operation = context.user_data.get("operation")

        # Add logging to help debug
        logging.info(f"Received reason: {reason} for operation: {operation}")

        # Send a confirmation message and ask for the amount
        await update.message.reply_text(
            f"Got it! Reason: '{reason}'\n\nNow, how many points do you want to {operation}?"
        )

        # This return value tells the ConversationHandler to transition to ADD_AMOUNT state
        return ADD_AMOUNT


async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the amount entry and handle the operation accordingly."""
        try:
            amount = int(update.message.text)
            if amount <= 0:
                await update.message.reply_text("Please enter a positive number.")
                return ADD_AMOUNT
        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
            return ADD_AMOUNT

        context.user_data["amount"] = amount
        operation = context.user_data.get("operation")
        person = context.user_data.get("person")

        # Check if person has enough points for subtract or transfer
        points = load_points()
        if (operation == "subtract" or operation == "transfer") and points[person] < amount:
            await update.message.reply_text(
                f"Sorry, {person} only has {points[person]} points. "
                f"Please enter a smaller amount or choose another operation."
            )
            return ADD_AMOUNT

        # For add or subtract, parent verification is needed
        if operation in ["add", "subtract"]:
            keyboard = [
                [InlineKeyboardButton("Mama", callback_data="verify_Mama")],
                [InlineKeyboardButton("Papa", callback_data="verify_Papa")],
                [InlineKeyboardButton("Cancel", callback_data="cancel_operation")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            reason = context.user_data.get("reason")

            await update.message.reply_text(
                f"Operation Details:\n"
                f"• Person: {person}\n"
                f"• Operation: {operation} points\n"
                f"• Amount: {amount}\n"
                f"• Reason: {reason}\n\n"
                f"This operation needs verification from Mama or Papa:",
                reply_markup=reply_markup
            )
            return VERIFY_OPERATION

        # For transfer, no verification needed
        elif operation == "transfer":
            target = context.user_data.get("target")

            # Update points
            points = load_points()
            points[person] -= amount
            points[target] += amount
            save_points(points)

            # Record in history
            add_to_history("transfer", person, amount, target=target)

            await update.message.reply_text(
                f"✅ Transfer complete! {person} transferred {amount} points to {target}.\n\n"
                f"Updated points:\n"
                f"• {person}: {points[person]} points\n"
                f"• {target}: {points[target]} points"
            )

            # Show main menu again
            keyboard = [
                [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=reply_markup
            )

            return MAIN_MENU

        return MAIN_MENU

async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle verification by parents."""
        query = update.callback_query
        await query.answer()

        logging.info(f"Received verification callback: {query.data}")

        if query.data == "cancel_operation":
            await query.edit_message_text("Operation cancelled.")
            return await show_main_menu(update, context)

        if not query.data.startswith("verify_"):
            # This is not a verification callback, so we'll ignore it
            return VERIFY_OPERATION

        verifier = query.data.split("_")[1]
        operation = context.user_data.get("operation")
        person = context.user_data.get("person")
        amount = context.user_data.get("amount")
        reason = context.user_data.get("reason")

        # Update points
        points = load_points()

        if operation == "add":
            points[person] += amount
        elif operation == "subtract":
            points[person] -= amount

        save_points(points)

        # Record in history
        add_to_history(operation, person, amount, reason=reason, verified_by=verifier)

        await query.edit_message_text(
            f"✅ Operation verified by {verifier} and completed successfully!\n\n"
            f"• {person} now has {points[person]} points."
        )

        # Show main menu again
        keyboard = [
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            "What would you like to do next?",
            reply_markup=reply_markup
        )


        return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        await update.message.reply_text(
            "Operation cancelled. Type /start to begin again."
        )
        return ConversationHandler.END

def main():
        """Run the bot."""
        # Create the Application
        application = Application.builder().token("7783137535:AAE8lMNNC08K80nxrz1GxtUbYvz_JagGlnQ").build()

        # Create conversation handler with states
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(handle_main_menu),
        # You might need a specific handler for the "back_to_main" callback
                    CallbackQueryHandler(show_main_menu, pattern="^back_to_main$")
                ],
                VIEW_POINTS: [
                    CallbackQueryHandler(handle_view_options)
                ],
                VIEW_HISTORY: [
                    CallbackQueryHandler(handle_view_options)
                ],
                SELECT_PERSON: [
                    CallbackQueryHandler(handle_person_selection)
                ],
                SELECT_OPERATION: [
                    CallbackQueryHandler(handle_operation_selection)
                ],
                ADD_REASON: [
                    # This handler captures text input for the reason
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reason)
                ],
                ADD_AMOUNT: [
                    # This handler captures text input for the amount
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)
                ],
                SELECT_TRANSFER_TARGET: [
                    CallbackQueryHandler(handle_transfer_target)
                ],
                VERIFY_OPERATION: [
                    CallbackQueryHandler(handle_verification)
                ]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            # Add this to improve debugging
            allow_reentry=True,
            per_chat=True
        )

        application.add_handler(conv_handler)

        # Start the Bot
        application.run_polling(drop_pending_updates=True)  # Added this parameter

if __name__ == "__main__":
        main()
