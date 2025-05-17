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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get API keys from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TOKEN = os.getenv('TOKEN')

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Fun facts to keep users engaged
FUN_FACTS = [
    "🌟 Fun Fact: Nethermind’s team helped scale Ethereum’s mainnet to handle millions of transactions daily!",
    "🔍 Did you know? Nethermind has contributed to over 50 Ethereum Improvement Proposals (EIPs)!",
    "💻 Fun Fact: Nethermind’s client supports both x64 and Arm64 architectures—perfect for diverse setups!",
    "🚀 Trivia: Nethermind’s zk-team is pioneering zero-knowledge proofs for Ethereum scaling solutions!"
]

# Nethermind team members
TEAM_MEMBERS = {
    'inquiry': ("@tony_sabado", "Antonio Sabado, CGO at Nethermind"),
    'inquiry_cristiano': ("@cmdsilva25", "Cristiano Silva, our Smart Contract Auditor"),
    'General': ("@spacevii", "Vii, our BD go to")
}

# Nethermind service links with descriptions
SERVICES = [
    [
        InlineKeyboardButton("🏗️ Infrastructure Management", callback_data='service_infra'),
        InlineKeyboardButton("🔍 Learn More", url='https://www.nethermind.io/infrastructure-management')
    ],
    [
        InlineKeyboardButton("🔧 Blockchain Core Engineering", callback_data='service_core'),
        InlineKeyboardButton("🔍 Learn More", url='https://www.nethermind.io/blockchain-core-engineering')
    ],
    [
        InlineKeyboardButton("🔬 Nethermind Research", callback_data='service_research'),
        InlineKeyboardButton("🔍 Learn More", url='https://www.nethermind.io/nethermind-research')
    ],
    [
        InlineKeyboardButton("🌐 DApps & Enterprise Engineering", callback_data='service_dapps'),
        InlineKeyboardButton("🔍 Learn More", url='https://www.nethermind.io/dapps-enterprise-engineering')
    ],
    [
        InlineKeyboardButton("🔒 Smart Contract Auditing", callback_data='service_audit'),
        InlineKeyboardButton("🔍 Learn More", url='https://www.nethermind.io/smart-contract-audits')
    ]
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
                      service_area TEXT, project_details TEXT, meeting_location TEXT,
                      contact_info TEXT, timeline TEXT)''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    keyboard = [
        [InlineKeyboardButton("📬 Submit an Inquiry", callback_data='inquiry')],
        [InlineKeyboardButton("💬 Have a chat with us", callback_data='sales')],
        [InlineKeyboardButton("📚 Docs", url='https://docs.nethermind.io')],
        [InlineKeyboardButton("🐙 GitHub", url='https://github.com/NethermindEth')],
        [InlineKeyboardButton("🌐 Explore Our Services", callback_data='services')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message or "😄 Hey, what’s next on your Nethermind journey?",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message or "😄 Hey, what’s next on your Nethermind journey?",
            reply_markup=reply_markup
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "🎉 Hi there! Welcome to Netherbot, your friendly guide to all things Nethermind! 😊 "
        "Whether you want to explore our services, set up a node, or chat with our awesome team, I’m here to make it super fun and easy!\n\n"
        "What’s sparking your interest today? Let’s dive in! 🚀"
    )
    await show_main_menu(update, context, welcome_message)

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == 'inquiry':
        keyboard = [
            [InlineKeyboardButton("🏗️ Infrastructure Management", callback_data='inquiry_infra')],
            [InlineKeyboardButton("🔧 Blockchain Core Engineering", callback_data='inquiry_core')],
            [InlineKeyboardButton("🔬 Nethermind Research", callback_data='inquiry_research')],
            [InlineKeyboardButton("🌐 DApps & Enterprise Engineering", callback_data='inquiry_dapps')],
            [InlineKeyboardButton("🔍 Smart Contract Auditing", callback_data='inquiry_audit')],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🌟 Awesome! Which Nethermind area would you like to explore for your inquiry?\n\n"
            "Pick one below, and we’ll get started! 😄",
            reply_markup=reply_markup
        )
    elif data.startswith('inquiry_'):
        service_area = {
            'inquiry_infra': 'Infrastructure Management',
            'inquiry_core': 'Blockchain Core Engineering',
            'inquiry_research': 'Nethermind Research',
            'inquiry_dapps': 'DApps & Enterprise Engineering',
            'inquiry_audit': 'Smart Contract Auditing'
        }[data]
        context.user_data['inquiry_data'] = {'service_area': service_area}
        await query.edit_message_text(
            f"🎉 Great choice! You’re interested in {service_area}! 😄\n\n"
            "Can you share a quick description of your project or what you need help with?"
        )
        context.user_data['expecting'] = 'inquiry_project'
    elif data == 'sales':
        contact_message = (
            "📇 **Talk to us! Talk about Life and Chains and everything in between😄**\n\n"
            "**Name**: Roch Brezenski\n"
            "**Position**: Head of Business Development, Nethermind\n"
            "**Telegram**: [@rockman71](https://t.me/rockman71)\n"
            "**LinkedIn**: [Roch Brezenski](https://www.linkedin.com/in/zrochb/)\n"
            "**Calendly**: [Schedule a 30-Minute One-on-One](https://calendly.com/roch_nethermind/30min-one-on-one)\n\n"
            "Feel free to reach out to Roch to discuss your blockchain needs or explore how Nethermind can help you succeed! "
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            contact_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        context.user_data['expecting'] = 'sales_choice'
    elif data == 'services':
        await query.edit_message_text(
            "🌐 Discover Nethermind’s awesome services! Here’s what we do:\n\n"
            "🏗️ *Infrastructure Management*: Optimize your blockchain infra for peak performance!\n"
            "🔧 *Blockchain Core Engineering*: Build and scale cutting-edge blockchain solutions.\n"
            "🔬 *Nethermind Research*: Dive into innovative blockchain R&D with our experts.\n"
            "🌐 *DApps & Enterprise Engineering*: Create robust, enterprise-grade decentralized apps.\n"
            "🔒 *Smart Contract Auditing*: Ensure your smart contracts are secure with our expert audits, including formal verification and real-time monitoring!\n\n"
            "Click below to learn more or head back to the menu! 😄",
            reply_markup=InlineKeyboardMarkup(SERVICES + [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]])
        )
    elif data.startswith('service_'):
        service_descriptions = {
            'service_infra': (
                "🏗️ Infrastructure Management: We optimize your blockchain infrastructure for peak performance, ensuring your systems run smoothly and efficiently, even under heavy loads! Whether you’re scaling up or fine-tuning, we’ve got your back. 😄"
            ),
            'service_core': (
                "🔧 Blockchain Core Engineering: We help you build and scale cutting-edge blockchain solutions, from core protocol development to custom implementations. Let’s create something groundbreaking together! 😎"
            ),
            'service_research': (
                "🔬 Nethermind Research: Dive into innovative blockchain R&D with our expert team! We explore new ideas, develop proofs of concept, and push the boundaries of what’s possible in the blockchain space. 🌟"
            ),
            'service_dapps': (
                "🌐 DApps & Enterprise Engineering: We create robust, enterprise-grade decentralized apps tailored to your needs. From ideation to deployment, we’ll help you build secure and scalable DApps! 🚀"
            ),
            'service_audit': (
                "🔒 Smart Contract Auditing: We ensure your smart contracts are secure with expert audits, including formal verification and real-time monitoring. Trust us to safeguard your decentralized applications! 😄"
            )
        }
        description = service_descriptions[data]
        await query.edit_message_text(
            f"{description}\n\n"
            f"💬 Want to dive deeper? Chat with {TEAM_MEMBERS['inquiry'][1]} at {TEAM_MEMBERS['inquiry'][0]} on Telegram, or book a meeting with him at: https://calendly.com/antonio-sabado 🚀\n\n"
            "What’s next on your Nethermind journey?"
        )
        await show_main_menu(update, context)
    elif data == 'back':
        await show_main_menu(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if 'expecting' in context.user_data:
        try:
            if context.user_data['expecting'] == 'inquiry_project':
                logger.info(f"Received project description from user {update.message.from_user.first_name}: {text}")
                context.user_data['inquiry_data']['project_details'] = text
                # Use OpenAI to repeat the description back
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a friendly assistant helping with inquiries. Repeat the user's project description back in a conversational, enthusiastic tone."},
                        {"role": "user", "content": f"The project description is: {text}"}
                    ]
                )
                repeated_description = response.choices[0].message.content
                await update.message.reply_text(
                    f"📝 Woohoo! You said: {repeated_description}\n\n"
                    "Where did we meet? (e.g., ETH Conference 2024, Twitter, etc.) 😊"
                )
                context.user_data['expecting'] = 'inquiry_where_met'

            elif context.user_data['expecting'] == 'inquiry_where_met':
                logger.info(f"Received meeting location from user {update.message.from_user.first_name}: {text}")
                context.user_data['inquiry_data']['where_met'] = text
                context.user_data['expecting'] = 'inquiry_contact'
                await update.message.reply_text("📧 Sweet! What’s your contact info? (e.g., email or phone number) 😄")

            elif context.user_data['expecting'] == 'inquiry_contact':
                logger.info(f"Received contact info from user {update.message.from_user.first_name}: {text}")
                context.user_data['inquiry_data']['contact_info'] = text
                context.user_data['expecting'] = 'inquiry_timeline'
                await update.message.reply_text("⏰ Almost there! How soon do you need our help? (e.g., 1 week, 1 month) 🚀")

            elif context.user_data['expecting'] == 'inquiry_timeline':
                logger.info(f"Received timeline from user {update.message.from_user.first_name}: {text}")
                context.user_data['inquiry_data']['timeline'] = text

                # Save to Postgres
                inquiry_data = context.user_data['inquiry_data']
                logger.info("Attempting to save inquiry to database...")
                DATABASE_URL = os.getenv('DATABASE_URL')
                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                c = conn.cursor()
                c.execute("INSERT INTO inquiries VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                          (datetime.now().strftime('%Y-%m-%d %I:%M %p'),
                           f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}".strip() or 'N/A',
                           update.message.from_user.username or 'N/A',
                           inquiry_data['service_area'], inquiry_data['project_details'],
                           inquiry_data['where_met'], inquiry_data['contact_info'],
                           inquiry_data['timeline']))
                conn.commit()
                conn.close()
                logger.info("Inquiry saved to database successfully.")

                # Simulated Google Search for client info
                contact_info = inquiry_data['contact_info']
                search_query = contact_info if '@' in contact_info else f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}"
                client_info = "I found that you're likely with a cool tech startup focused on blockchain solutions!"

                # Use OpenAI for personalized summary
                logger.info("Generating personalized summary with OpenAI...")
                summary_prompt = (
                    f"Create a personalized, engaging, and fun summary of the following inquiry details for the user {update.message.from_user.first_name}. "
                    f"Include a friendly vibe and use this client info if available: {client_info}\n"
                    f"Service Area: {inquiry_data['service_area']}\n"
                    f"Project Description: {inquiry_data['project_details']}\n"
                    f"Where We Met: {inquiry_data['where_met']}\n"
                    f"Contact Information: {inquiry_data['contact_info']}\n"
                    f"Timeline: {inquiry_data['timeline']}"
                )
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a fun, enthusiastic assistant summarizing inquiry details in a personalized, friendly way."},
                        {"role": "user", "content": summary_prompt}
                    ]
                )
                personalized_summary = response.choices[0].message.content
                logger.info("Summary generated successfully.")

                await update.message.reply_text(
                    f"🎉 Woohoo, {update.message.from_user.first_name}! Your inquiry is all set! 🚀\n\n"
                    f"{personalized_summary}\n\n"
                    f"💬 Want to connect with {TEAM_MEMBERS['inquiry'][1]} or {TEAM_MEMBERS['inquiry_cristiano'][1]}? "
                    f"Reach out to {TEAM_MEMBERS['inquiry'][0]} or {TEAM_MEMBERS['inquiry_cristiano'][0]} on Telegram!\n\n"
                    f"📅 {TEAM_MEMBERS['inquiry'][1]} would love to chat more! Book a meeting with him at: "
                    f"https://calendly.com/antonio-sabado\n\n"
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
                        f"📬 Awesome, you’re interested in {options[text]}! We’ll follow up soon! 😄\n\n"
                        f"💬 Want to chat with {TEAM_MEMBERS['inquiry'][1]}? Ping {TEAM_MEMBERS['inquiry'][0]} on Telegram!\n\n"
                        f"{random.choice(FUN_FACTS)}\n\n"
                        "What’s next on your Nethermind journey?"
                    )
                    await show_main_menu(update, context)
                    context.user_data.clear()
                else:
                    await update.message.reply_text("⚠️ Oops! Please reply with 1, 2, or 3 to pick an option. 😊")

        except Exception as e:
            logger.error(f"Error saving details: {str(e)}")
            await update.message.reply_text(f"⚠️ Oh no! Something went wrong: {str(e)}. Let’s try again! 😄")
            context.user_data.clear()
            await show_main_menu(update, context)
    else:
        await update.message.reply_text(
            "😊 Hey there! Use /start to kick off your Nethermind adventure! 🚀"
        )

# Define error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "😓 Oops, something went wrong! Our team’s been notified, and we’ll fix it soon. Try again with /start? 🚀"
        )

if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)  # Register the error handler

    print("Bot is running...")
    app.run_polling()