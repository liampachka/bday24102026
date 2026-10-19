import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Get token from environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Store user progress and states
user_progress = {}
user_state = {}

# Quest steps configuration
QUEST_STEPS = {
    1: {
        "text": "Готова к балу, Золушка? Надень свои любимые туфельки и прикажи кучеру запрягать лошадей!",
        "button": "Карета подана!",
        "next_step": 2
    },
    2: {
        "text": (
            "Пока карета трясётся по колдобинам, ответь на загадку: премьера одного знаменитого балета "
            "состоялась в Большом театре в ноябре 1945 года как символ победы добра над злом. Интересно, "
            "что для того, чтобы премьера состоялась, композитору пришлось оправдываться перед идеологами, "
            "что речь в балете не о героине Шарля Перро, а о персонаже русской сказки. "
            "А для кого писалась главная роль в этом балете?"
        ),
        "input": True,
        "input_prompt": "Введи фамилию балерины:",
        "answer": "уланова",
        "error_message": "Кажется, неверно, попробуй ещё раз",
        "next_step": 3
    },
    3: {
        "text": (
            "Получи ключ от ящика с сокровищем здесь: https://maps.app.goo.gl/df6cu9zdHERSZDZk7 . "
            "Найди и открой ящик с сокровищем, а в поле введи код"
        ),
        "input": True,
        "input_prompt": "Введи код из сокровища:",
        "answer": "2204",
        "error_message": "Ты что, слопала код? Разуй глазищи и введи его правильно",
        "next_step": 4
    },
    4: {
        "text": (
            "Пока тебя носило по каким-то подворотням, карета превратилась в тыкву. "
            "Придётся добираться самостоятельно. Компания \"Лягушка-путешественница\" предлагает тебе "
            "воспользоваться самокатом, но если не хочешь, можешь по-простолюдински прогуляться. "
            "Куда ехать? Ответь на вопрос, получишь локацию:\n\n"
            "Самое страшное сценическое наказание для неудачного выступления — "
            "брошенный на сцену ОН, завернутый в газету."
        ),
        "input": True,
        "input_prompt": "Назови ЕГО:",
        "answer": "веник",
        "error_message": "Неправильно, попробуй ещё раз",
        "next_step": 5
    },
    5: {
        "text": (
            "Пойди проверь, как сегодня оценивают твою танцевальную партию. "
            "Тебя ждут в Цветочной Культуре. Введи полученный код"
        ),
        "input": True,
        "input_prompt": "Введи код:",
        "answer": "1024",
        "next_step": 6,
        "skip_validation": True  # Both correct and incorrect go to next step
    },
    6: {
        "text": (
            "https://maps.app.goo.gl/oDhuGghpyfQi36Ai8\n\n"
            "Сделай приятную паузу и запасись энергией. В час пополудни горничная дома в гостиной "
            "подаст тебе твой бальный наряд. Будь готова к 14:00 - кучер доставит тебя на бал!"
        ),
        "final": True
    }
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - Begin the quest"""
    user_id = update.effective_user.id
    user_progress[user_id] = 1
    user_state[user_id] = None
    
    await show_step(update, context, user_id)


async def show_step(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Display current quest step"""
    step = user_progress.get(user_id, 1)
    
    if step not in QUEST_STEPS:
        await send_message(update, "Квест завершён! 🎉")
        return
    
    step_data = QUEST_STEPS[step]
    
    # Check if this is a final step
    if step_data.get("final"):
        await send_message(update, step_data["text"])
        # Clean up user data
        if user_id in user_progress:
            del user_progress[user_id]
        if user_id in user_state:
            del user_state[user_id]
        return
    
    # Check if this step requires input
    if step_data.get("input"):
        user_state[user_id] = step  # Set state to wait for input
        await send_message(update, step_data["text"])
        await send_message(update, step_data["input_prompt"])
    else:
        # Create button
        keyboard = [[InlineKeyboardButton(step_data["button"], callback_data=f"next_{step}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message with button
        await send_message(update, step_data["text"], reply_markup)


async def send_message(update: Update, text: str, reply_markup=None):
    """Helper function to send messages"""
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.effective_message.reply_text(text, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    current_step = user_progress.get(user_id, 1)
    
    # Move to next step
    if current_step in QUEST_STEPS:
        next_step = QUEST_STEPS[current_step]["next_step"]
        user_progress[user_id] = next_step
        await show_step(update, context, user_id)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input from user"""
    user_id = update.effective_user.id
    user_answer = update.message.text.strip()
    
    # Check if user is in a state waiting for input
    current_step = user_state.get(user_id)
    
    if current_step is None:
        # User is not in any input state
        await update.message.reply_text(
            "Используй /start чтобы начать квест!"
        )
        return
    
    if current_step not in QUEST_STEPS:
        return
    
    step_data = QUEST_STEPS[current_step]
    correct_answer = step_data.get("answer", "").lower()
    
    # Check if validation should be skipped (Task 5)
    if step_data.get("skip_validation"):
        # Move to next step regardless of answer
        user_state[user_id] = None
        next_step = step_data["next_step"]
        user_progress[user_id] = next_step
        await show_step(update, context, user_id)
        return
    
    # Validate answer (case-insensitive)
    if user_answer.lower() == correct_answer:
        # Correct answer
        user_state[user_id] = None  # Clear state
        next_step = step_data["next_step"]
        user_progress[user_id] = next_step
        await show_step(update, context, user_id)
    else:
        # Incorrect answer
        error_message = step_data.get("error_message", "Кажется, неверно, попробуй ещё раз")
        await update.message.reply_text(error_message)
        # Keep user in same state to retry


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "🎭 Бот-квест '24102026'\n\n"
        "Команды:\n"
        "/start - Начать квест заново\n"
        "/help - Показать эту справку\n"
        "/status - Показать текущий прогресс\n\n"
        "Следуй инструкциям и отвечай на вопросы!"
    )
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = update.effective_user.id
    current_step = user_progress.get(user_id, 0)
    
    if current_step == 0:
        await update.message.reply_text("Ты ещё не начала квест. Используй /start")
    else:
        total_steps = len(QUEST_STEPS)
        await update.message.reply_text(f"Ты на шаге {current_step} из {total_steps}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    print(f"Exception while handling an update: {context.error}")


def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN environment variable is not set!")
        print("Please set it with: export BOT_TOKEN='your_token_here'")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("🤖 Bot '24102026' is running...")
    print("📍 Quest locations included:")
    print("   - Task 3: Treasure location")
    print("   - Task 6: Final location")
    print("\nPress Ctrl+C to stop")
    print("-" * 50)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()