from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import psycopg2
from datetime import datetime
import random
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get API keys from environment
TOKEN = os.getenv('TOKEN')

# Fun facts to keep users engaged
FUN_FACTS = [
    "🌟 Fun Fact: Nethermind’s team helped scale Ethereum’s mainnet to handle millions of transactions daily!",
    "🔍 Did you know? Nethermind has contributed to over 50 Ethereum Improvement Proposals (EIPs)!",
    "💻 Fun Fact: Nethermind’s client supports both x64 and Arm64 architectures—perfect for diverse setups!",
    "🚀 Trivia: Nethermind’s zk-team is pioneering zero-knowledge proofs for Ethereum scaling solutions!",
    "🤖 Did you know? Nethermind’s AI Agents revolutionize smart contract auditing with cutting-edge in-house tech!"
]

# Nethermind team members
TEAM_MEMBERS = {
    'inquiry': ("@tony_sabado", "Antonio Sabado, CGO at Nethermind", "https://www.linkedin.com/in/antonio-sabado-97150511b/"),
    'inquiry_cristiano': ("@cmdsilva25", "Cristiano Silva, Smart Contract Auditor", "https://www.linkedin.com/in/0xchris/"),
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
        "🎉 Hi there! Welcome to Netherbot, your guide to Nethermind’s blockchain expertise! 😊 "
        "We’re proud to be Starknet’s biggest technical partner, powering tools like Juno, Voyager, and the Starknet Remix Plugin, and collaborating with top clients like World, Gnosis, EigenLayer, and Lido. "
        "Our in-house cutting-edge AI and AI Agents revolutionize smart contract auditing and beyond, delivering unmatched innovation. "
        "Whether you’re exploring our services, setting up a node, or diving into DeFi, I’m here to make it fun and easy!\n\n"
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
            "📇 **Talk to us! Discuss Blockchain, Innovation, and Everything in Between! 😄**\n\n"
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
        context.user_data['expecting'] = None
    elif data == 'services':
        await query.edit_message_text(
            "🌐 Discover Nethermind’s world-class services, trusted by clients like World, Gnosis, EigenLayer, and Lido! As Starknet’s biggest technical partner, we’ve built tools like Juno, Voyager, Starknet Remix Plugin, and RPC services to drive ecosystem growth. Our AI Agents, powered by in-house cutting-edge AI, enhance smart contract auditing and more. Here’s what we do:\n\n"
            "🏗️ Infrastructure Management: Optimize blockchain infra for peak performance, as we do for Lido’s validators and Gnosis Chain.\n\n"
            "🔧 Blockchain Core Engineering: Build cutting-edge solutions, like our Juno client for Starknet and Ethereum client for World.\n\n"
            "🔬 Nethermind Research: Innovate with R&D, supporting EigenLayer’s restaking and Starknet’s Cairo VM in Go.\n\n"
            "🌐 DApps & Enterprise Engineering: Create enterprise-grade DApps, powering DeFi and tokenization for global clients.\n\n"
            "🔒 Smart Contract Auditing: Secure contracts with AI-driven audits, formal verification, and real-time monitoring, trusted by Starknet and beyond.\n\n"
            "Click below to learn more or head back to the menu! 😄",
            reply_markup=InlineKeyboardMarkup(SERVICES + [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]])
        )
    elif data.startswith('service_'):
        service_descriptions = {
            'service_infra': (
                "🏗️ Infrastructure Management: We optimize blockchain infrastructure for peak performance, ensuring your systems run smoothly and efficiently, even under heavy loads! Trusted by Lido for validator management and Gnosis for chain operations. 😄"
            ),
            'service_core': (
                "🔧 Blockchain Core Engineering: We build and scale cutting-edge blockchain solutions, like our Juno client for Starknet and Ethereum client for World. Let’s create something groundbreaking together! 😎"
            ),
            'service_research': (
                "🔬 Nethermind Research: Dive into innovative blockchain R&D with our expert team! We support EigenLayer’s restaking protocols and develop Starknet’s Cairo VM in Go. 🌟"
            ),
            'service_dapps': (
                "🌐 DApps & Enterprise Engineering: We create robust, enterprise-grade decentralized apps tailored to your needs, powering DeFi and tokenization for clients like World. 🚀"
            ),
            'service_audit': (
                "🔒 Smart Contract Auditing: We ensure your smart contracts are secure with AI Agents powered by our in-house cutting-edge AI, offering precise audits, formal verification, and real-time monitoring. Trusted by Starknet and Gnosis, our AI tools also support other blockchain applications. 😄"
            )
        }
        description = service_descriptions[data]
        await query.edit_message_text(
            f"{description}\n\n"
            f"💬 Want to dive deeper? Chat with {TEAM_MEMBERS['inquiry'][1]} at [{TEAM_MEMBERS['inquiry'][0]}](https://t.me/tony_sabado) on Telegram, "
            f"connect on [LinkedIn]({TEAM_MEMBERS['inquiry'][2]}), or book a meeting at: [Calendly](https://calendly.com/antonio-sabado) 🚀\n\n"
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
                await update.message.reply_text(
                    f"📝 Got it! Your project description: {text}\n\n"
                    "Where did we meet? (e.g., Consensus 2025, Twitter, etc.) 😊"
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

                # Simulated Google Search for client info (not used in summary)
                contact_info = inquiry_data['contact_info']
                search_query = contact_info if '@' in contact_info else f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}"
                client_info = "I found that you're likely with a tech startup focused on blockchain solutions!"

                # Plain bullet-point regurgitation of user input
                personalized_summary = (
                    f"- Service Area: {inquiry_data['service_area']}\n"
                    f"- Project Details: {inquiry_data['project_details']}\n"
                    f"- Where We Met: {inquiry_data['where_met']}\n"
                    f"- Timeline: {inquiry_data['timeline']}"
                )
                logger.info("Bullet-point summary created.")

                await update.message.reply_text(
                    f"🎉 Thank you, {update.message.from_user.first_name}! Your inquiry has been successfully submitted! 🚀\n\n"
                    f"**Here’s a summary of your request**:\n{personalized_summary}\n\n"
                    
                    f"Join the ranks of our esteemed clients like World, Gnosis, EigenLayer, and Lido! As Starknet’s biggest technical partner, we’ve developed tools like the Juno client, Voyager block explorer, Starknet Remix Plugin, and RPC services, plus we’re working on the Cairo VM in Go. Our cutting-edge in-house AI powers AI Agents for smart contract auditing and versatile blockchain applications. 📇 **Talk to us! Discuss Blockchain, Innovation, and Everything in Between! 😄**\n\n"
                    f"**Next Steps - we will reach out, or if you prefer, you can directly set up a meeting now**:\n\n"
                    f"**Name**: {TEAM_MEMBERS['inquiry'][1]}\n"
                    f"**Position**: Chief Growth Officer, Nethermind\n"
                    f"**Telegram**: [{TEAM_MEMBERS['inquiry'][0]}](https://t.me/tony_sabado)\n"
                    f"**LinkedIn**: [Antonio Sabado]({TEAM_MEMBERS['inquiry'][2]})\n"
                    f"**Calendly**: [Schedule a 30-Minute One-on-One](https://calendly.com/antonio-sabado/30min-one-on-one)\n\n"
                    f"🌟 *{random.choice(FUN_FACTS)}*\n\n",
                    parse_mode='Markdown'
                )
                await show_main_menu(update, context)
                context.user_data.clear()

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