from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import sqlite3
from datetime import datetime
import random
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TOKEN = os.getenv('TOKEN')

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import psycopg2
from datetime import datetime
import random
import openai
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Fun facts to keep users engaged
FUN_FACTS = [
    "🌟 Fun Fact: Nethermind’s team helped scale Ethereum’s mainnet to handle millions of transactions daily!",
    "🔍 Did you know? Nethermind has contributed to over 50 Ethereum Improvement Proposals (EIPs)!",
    "💻 Fun Fact: Nethermind’s client supports both x64 and Arm64 architectures—perfect for diverse setups!",
    "🚀 Trivia: Nethermind’s zk-team is pioneering zero-knowledge proofs for Ethereum scaling solutions!"
]

# Nethermind team members (fictional Telegram handles for this example, except for Cristiano)
TEAM_MEMBERS = {
    'audit': ("@AnnaTheAuditor", "Anna, our Audit Expert"),
    'audit_cristiano': ("@cmdsilva25", "Cristiano Silva, our Smart Contract Auditing Specialist"),
    'node': ("@MikeTheNodeMaster", "Mike, our Node Specialist"),
    'sales': ("@SarahTheSalesStar", "Sarah, our Sales Lead")
}

# Nethermind Telegram groups (fictional for this example)
GROUPS = [
    [InlineKeyboardButton("💻 Hardware Crew", url='https://t.me/NethermindHardware')],
    [InlineKeyboardButton("🔐 zk Enthusiasts", url='https://t.me/NethermindZK')],
    [InlineKeyboardButton("📊 Data Nerds", url='https://t.me/NethermindData')],
    [InlineKeyboardButton("🚀 Dev Chat", url='https://t.me/NethermindDevs')]
]

# Initialize Postgres database
def init_db():
    logger.info("Initializing database...")
    DATABASE_URL = os.getenv('DATABASE_URL')
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS inquiries
                     (date_submitted TEXT, user_full_name TEXT, telegram_username TEXT,
                      project_details TEXT, meeting_location TEXT, contact_info TEXT,
                      audit_timeline TEXT)''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    keyboard = [
        [InlineKeyboardButton("🧪 Audit Inquiry", callback_data='audit')],
        [InlineKeyboardButton("🔧 Run a Node", callback_data='node')],
        [InlineKeyboardButton("💬 Talk to Sales", callback_data='sales')],
        [InlineKeyboardButton("📚 Docs", url='https://docs.nethermind.io')],
        [InlineKeyboardButton("🐙 GitHub", url='https://github.com/NethermindEth')],
        [InlineKeyboardButton("🌐 Join Our Communities", callback_data='communities')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message or "👋 What would you like to explore next with Nethermind?",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message or "👋 What would you like to explore next with Nethermind?",
            reply_markup=reply_markup
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 Hey there, welcome to Netherbot! I’m here to help you navigate the awesome world of Nethermind. "
        "Whether you’re looking for audits, node setup, or just want to chat with our team, I’ve got you covered! 😄\n\n"
        "Let’s get started—what can I help you with today?"
    )
    await show_main_menu(update, context, welcome_message)

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == 'audit':
        await query.edit_message_text("🔍 Ready to kick off your audit inquiry? What’s a brief description of your project?")
        context.user_data['expecting'] = 'audit_project'
        context.user_data['audit_data'] = {}
    elif data == 'node':
        await query.edit_message_text(
            "🚀 Here’s how to run a Nethermind node: https://docs.nethermind.io\n\n"
            f"💡 Want to chat with {TEAM_MEMBERS['node'][1]}? Reach out to {TEAM_MEMBERS['node'][0]} on Telegram!\n\n"
            f"{random.choice(FUN_FACTS)}\n\n"
            "What’s next?"
        )
        await show_main_menu(update, context)
    elif data == 'sales':
        await query.edit_message_text(
            "🧠 Are you looking for:\n1️⃣ Infra support\n2️⃣ Smart contract audits\n3️⃣ R&D consulting\nReply with 1, 2, or 3.\n\n"
            f"💡 You can also chat directly with {TEAM_MEMBERS['sales'][1]} at {TEAM_MEMBERS['sales'][0]}!"
        )
        context.user_data['expecting'] = 'sales_choice'
    elif data == 'communities':
        await query.edit_message_text(
            "🌐 Join our awesome Nethermind communities to connect with like-minded folks!\n\n"
            "Pick a group to join, or go back to the main menu."
        )
        reply_markup = InlineKeyboardMarkup(GROUPS + [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]])
        await query.edit_message_text(
            "🌐 Join our awesome Nethermind communities to connect with like-minded folks!\n\n"
            "Pick a group to join, or go back to the main menu.",
            reply_markup=reply_markup
        )
    elif data == 'back':
        await show_main_menu(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if 'expecting' in context.user_data:
        try:
            if context.user_data['expecting'] == 'audit_project':
                logger.info(f"Received project description from user {update.message.from_user.first_name}: {text}")
                context.user_data['audit_data']['project_details'] = text
                # Use OpenAI to repeat the description back
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a friendly assistant helping with audit inquiries. Repeat the user's project description back to them in a conversational tone."},
                        {"role": "user", "content": f"The project description is: {text}"}
                    ]
                )
                repeated_description = response.choices[0].message.content
                await update.message.reply_text(f"📝 Got it! You said: {repeated_description}\n\nNow, where did we meet? (e.g., ETH Conference 2024)")
                context.user_data['expecting'] = 'audit_where_met'

            elif context.user_data['expecting'] == 'audit_where_met':
                logger.info(f"Received meeting location from user {update.message.from_user.first_name}: {text}")
                context.user_data['audit_data']['where_met'] = text
                context.user_data['expecting'] = 'audit_contact'
                await update.message.reply_text("📧 Thanks! What’s your contact information? (e.g., email or phone number)")

            elif context.user_data['expecting'] == 'audit_contact':
                logger.info(f"Received contact info from user {update.message.from_user.first_name}: {text}")
                context.user_data['audit_data']['contact_info'] = text
                context.user_data['expecting'] = 'audit_timeline'
                await update.message.reply_text("⏰ Almost done! How soon do you need the audit? (e.g., 1 week, 1 month)")

            elif context.user_data['expecting'] == 'audit_timeline':
                logger.info(f"Received audit timeline from user {update.message.from_user.first_name}: {text}")
                context.user_data['audit_data']['audit_timeline'] = text

                # All data collected, save to Postgres
                audit_data = context.user_data['audit_data']
                logger.info("Attempting to save inquiry to database...")
                DATABASE_URL = os.getenv('DATABASE_URL')
                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                c = conn.cursor()
                c.execute("INSERT INTO inquiries VALUES (%s, %s, %s, %s, %s, %s, %s)",
                          (datetime.now().strftime('%Y-%m-%d %I:%M %p'),
                           f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}".strip() or 'N/A',
                           update.message.from_user.username or 'N/A',
                           audit_data['project_details'], audit_data['where_met'],
                           audit_data['contact_info'], audit_data['audit_timeline']))
                conn.commit()
                conn.close()
                logger.info("Inquiry saved to database successfully.")

                # Simulate a Google Search to find client info based on contact info
                contact_info = audit_data['contact_info']
                search_query = contact_info if '@' in contact_info else f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}"
                # Simulated search result
                client_info = "I found that you're likely with a cool tech startup focused on blockchain solutions!"

                # Use OpenAI to create a personalized, cool summary
                logger.info("Generating personalized summary with OpenAI...")
                summary_prompt = (
                    f"Create a personalized, engaging, and cool summary of the following audit inquiry details for the user {update.message.from_user.first_name}. "
                    f"Include some fun vibes and use this additional client info if available: {client_info}\n"
                    f"Project Description: {audit_data['project_details']}\n"
                    f"Where We Met: {audit_data['where_met']}\n"
                    f"Contact Information: {audit_data['contact_info']}\n"
                    f"Audit Timeline: {audit_data['audit_timeline']}"
                )
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a fun, enthusiastic assistant summarizing audit inquiry details in a personalized, cool way."},
                        {"role": "user", "content": summary_prompt}
                    ]
                )
                personalized_summary = response.choices[0].message.content
                logger.info("Summary generated successfully.")

                await update.message.reply_text(
                    f"🎉 Awesome, {update.message.from_user.first_name}! We’ve got your audit inquiry locked in! 🚀\n\n"
                    f"{personalized_summary}\n\n"
                    f"💡 Want to connect with {TEAM_MEMBERS['audit'][1]} or {TEAM_MEMBERS['audit_cristiano'][1]}? Reach out to {TEAM_MEMBERS['audit'][0]} or {TEAM_MEMBERS['audit_cristiano'][0]} on Telegram!\n\n"
                    f"If you’re interested, Jose L. Zamorano, our Senior Business Development Consultant, would be delighted to discuss this further. "
                    f"You can contact him at jose.zamorano@nethermind.io or schedule a meeting via:\n"
                    f"- Europe: https://calendly.com/d/cmv9-fq5-pvf/nethermind-security\n"
                    f"- Americas & APAC: https://calendly.com/d/cq7m-vrj-t3y/nethermind-security-pacific\n\n"
                    f"{random.choice(FUN_FACTS)}\n\n"
                    "What’s next on your Nethermind adventure? 😎"
                )
                await show_main_menu(update, context)
                context.user_data.clear()

            elif context.user_data['expecting'] == 'sales_choice':
                if text in ['1', '2', '3']:
                    options = {
                        '1': "Infra support",
                        '2': "Smart contract audits",
                        '3': "R&D consulting"
                    }
                    await update.message.reply_text(
                        f"📬 Great, you’re interested in {options[text]}! We’ll get back to you soon.\n\n"
                        f"💡 Want to chat directly with {TEAM_MEMBERS['sales'][1]}? Reach out to {TEAM_MEMBERS['sales'][0]} on Telegram!\n\n"
                        f"{random.choice(FUN_FACTS)}\n\n"
                        "What’s next on your journey with Nethermind?"
                    )
                    await show_main_menu(update, context)
                    context.user_data.clear()
                else:
                    await update.message.reply_text("⚠️ Please reply with 1, 2, or 3 to choose an option.")

        except Exception as e:
            logger.error(f"Error saving details: {str(e)}")
            await update.message.reply_text(f"⚠️ Error saving your details: {str(e)}. Please try again.")
            context.user_data.clear()
            await show_main_menu(update, context)
    else:
        await update.message.reply_text(
            "🤖 I’m ready to help! Use /start to explore what I can do for you! 😄"
        )

if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()