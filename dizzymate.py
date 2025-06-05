# ---------------------------------------------------
# CONFIGURATION (formerly config.py)
# ---------------------------------------------------

import os
import logging
import random
import asyncio
import sqlite3
import threading
import json
from datetime import datetime, date, time, timedelta

import pytz
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

# Channel and group links for /start command
UPDATES_CHANNEL = os.getenv("UPDATES_CHANNEL", "https://t.me/your_channel")
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "https://t.me/your_support_group")
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot_username")

# Aura points configuration
AURA_POINTS = {
    'gay': -100,
    'couple': 100,
    'simp': -100,
    'toxic': -100,
    'cringe': -100,
    'respect': 500,
    'sus': -100,
    'ghost': -200,  # Special night command with higher penalty
    'fight_winner': 100,
    'fight_loser': 0
}

# Command messages
COMMAND_MESSAGES = {
    'gay': [
        "🏳️‍🌈 Today's Gay of the Day is {user.mention_html()}! 🌈✨",
        "🏳️‍🌈 Congratulations {user.mention_html()}, you're the fabulous Gay of the Day! 💅✨",
        "🌈 {user.mention_html()} has been crowned the Gay of the Day! 🏳️‍🌈👑"
    ],
    'couple': [
        "💕 Today's adorable couple is {user1.mention_html()} and {user2.mention_html()}! 💑✨",
        "❤️ Love is in the air! {user1.mention_html()} and {user2.mention_html()} are today's couple! 💕🥰",
        "👫 {user1.mention_html()} and {user2.mention_html()} make the perfect couple today! 💖✨"
    ],
    'simp': [
        "🥺 {user.mention_html()} is today's biggest simp! 💸👑",
        "😍 Behold the ultimate simp of the day: {user.mention_html()}! 🥺💕",
        "👑 {user.mention_html()} has achieved maximum simp level today! 🥺✨"
    ],
    'toxic': [
        "☠️ {user.mention_html()} is spreading toxic vibes today! 🤢💀",
        "🧪 Warning: {user.mention_html()} is today's most toxic member! ☠️⚠️",
        "💀 {user.mention_html()} wins the toxic award of the day! 🧪☠️"
    ],
    'cringe': [
        "😬 {user.mention_html()} is today's cringe master! 🤡💀",
        "🤢 Maximum cringe level achieved by {user.mention_html()}! 😬🤡",
        "💀 {user.mention_html()} made everyone cringe today! 😬✨"
    ],
    'respect': [
        "🫡 Infinite respect for {user.mention_html()}! 👑✨",
        "🙏 {user.mention_html()} deserves all the respect today! 🫡💫",
        "👑 Mad respect for {user.mention_html()}! 🙏✨"
    ],
    'sus': [
        "📮 {user.mention_html()} is acting pretty sus today! 👀🔍",
        "🤔 {user.mention_html()} looking sus af! 📮👀",
        "👀 Emergency meeting! {user.mention_html()} is sus! 📮🚨"
    ],
    'ghost': [
        "👻 {user.mention_html()} is tonight's spooky ghost! 🌙💀",
        "🌙 {user.mention_html()} haunts the darkness tonight! 👻⚰️",
        "💀 {user.mention_html()} emerges from the shadows! 👻🌑"
    ]
}

# Fight messages
FIGHT_MESSAGES = {
    'random_fight_announcement': [
        "⚔️ <b>RANDOM FIGHT ALERT!</b> ⚔️\n\n🥊 {user1.mention_html()} vs {user2.mention_html()} 🥊\n\n💥 Both fighters have 1 hour to accept this challenge!\n🏆 Winner gets +100 aura points!\n⏰ Fight expires if not accepted!",
        "🔥 <b>EPIC BATTLE ROYALE!</b> 🔥\n\n⚔️ {user1.mention_html()} vs {user2.mention_html()} ⚔️\n\n💪 Random fighters selected for today's battle!\n🏆 +100 aura awaits the victor!\n⏱️ 1 hour to accept or it's void!",
        "🌟 <b>ULTIMATE SHOWDOWN!</b> 🌟\n\n🥊 {user1.mention_html()} vs {user2.mention_html()} 🥊\n\n🎯 The arena awaits these random warriors!\n💰 +100 aura for the champion!\n⏰ Accept within 1 hour!"
    ],
    'user_fight_challenge': [
        "⚔️ <b>CHALLENGE ISSUED!</b> ⚔️\n\n🥊 {challenger.mention_html()} has challenged {opponent.mention_html()} to a fight!\n\n💥 {opponent.mention_html()}, do you accept this challenge?\n🏆 Winner gets +100 aura points!\n⏰ You have 1 hour to accept!",
        "🔥 <b>BATTLE CHALLENGE!</b> 🔥\n\n⚔️ {challenger.mention_html()} wants to fight {opponent.mention_html()}!\n\n💪 Will you accept this duel, {opponent.mention_html()}?\n🏆 +100 aura awaits the victor!\n⏱️ 1 hour to decide!",
        "🌟 <b>DUEL REQUEST!</b> 🌟\n\n🥊 {challenger.mention_html()} has thrown down the gauntlet!\n{opponent.mention_html()}, the challenge is yours!\n\n🎯 Accept to begin the battle!\n💰 +100 aura for the winner!"
    ],
    'fight_accepted': [
        "🔥 <b>FIGHT ACCEPTED!</b> 🔥\n\n⚔️ {user1.mention_html()} vs {user2.mention_html()} ⚔️\n\n💥 The battle has begun!\n🗣️ Both fighters must reply to each other!\n⏰ Last person to reply within 2 minutes wins!\n🏆 Winner gets +100 aura!",
        "⚡ <b>BATTLE COMMENCED!</b> ⚡\n\n🥊 {user1.mention_html()} vs {user2.mention_html()} 🥊\n\n🔥 Let the epic fight begin!\n💬 Reply to each other to fight!\n⏱️ 2-minute window for each exchange!\n🏆 +100 aura to the victor!",
        "🌟 <b>DUEL STARTED!</b> 🌟\n\n⚔️ {user1.mention_html()} vs {user2.mention_html()} ⚔️\n\n💪 The arena is set!\n🗨️ Exchange messages to battle!\n⏰ Last reply within 2 minutes wins!\n💰 +100 aura prize!"
    ],
    'fight_winner': [
        "🏆 <b>VICTORY!</b> 🏆\n\n👑 {winner.mention_html()} emerges victorious! 👑\n\n💪 What an epic battle!\n✨ +100 aura points awarded!\n🎉 Congratulations, champion!",
        "🥇 <b>CHAMPION CROWNED!</b> 🥇\n\n⚔️ {winner.mention_html()} wins the battle! ⚔️\n\n🔥 Incredible fighting spirit!\n💰 +100 aura points earned!\n🌟 Victory is yours!",
        "👑 <b>ULTIMATE WINNER!</b> 👑\n\n🏆 {winner.mention_html()} claims victory! 🏆\n\n💥 Outstanding performance!\n✨ +100 aura points added!\n🎊 Well fought, warrior!"
    ],
    'fight_draw': [
        "🤝 <b>IT'S A DRAW!</b> 🤝\n\n⚖️ {user1.mention_html()} and {user2.mention_html()} are equally matched!\n\n💥 Both fighters showed great skill!\n🏅 No aura points awarded for draws\n⚔️ Honor to both warriors!",
        "⚖️ <b>STALEMATE!</b> ⚖️\n\n🤜 {user1.mention_html()} vs {user2.mention_html()} 🤛\n\n🔥 Neither could claim victory!\n🤝 A draw between equals!\n⚔️ Both fought valiantly!",
        "🤝 <b>TIE GAME!</b> 🤝\n\n⚔️ {user1.mention_html()} and {user2.mention_html()} - perfectly matched!\n\n💪 Incredible battle, no winner!\n⚖️ Honor in the stalemate!\n🏅 Respect to both fighters!"
    ],
    'fight_timeout': [
        "⏰ <b>FIGHT TIMED OUT!</b> ⏰\n\n🐔 Both fighters chickened out!\n\n💔 No one accepted the challenge\n❌ No aura points awarded\n🕐 Better luck next time!",
        "🕐 <b>TIME'S UP!</b> 🕐\n\n👻 Both warriors disappeared!\n\n💨 Fight expired without action\n❌ No points awarded\n⏰ Challenge void!",
        "⌛ <b>EXPIRED!</b> ⌛\n\n🤷‍♂️ Nobody wanted to fight!\n\n💔 Challenge went unanswered\n❌ No points awarded\n🕰️ Maybe next time!"
    ]
}

# Bangladesh timezone for ghost command
BANGLADESH_TZ = 'Asia/Dhaka'

# Fight duration settings (in seconds)
FIGHT_ACCEPT_DURATION = 3600  # 1 hour
FIGHT_REPLY_DURATION = 120    # 2 minutes

# Member data collection settings
COLLECT_MEMBERS_ON_JOIN = True
COLLECT_MEMBERS_ON_MESSAGE = True
MAX_MEMBERS_PER_BATCH = 200  # Telegram API limit

# ---------------------------------------------------
# DATABASE LAYER (formerly database.py)
# ---------------------------------------------------

# Thread-local storage for database connections
local_data = threading.local()

def get_db_connection():
    """Get a thread-local database connection."""
    if not hasattr(local_data, 'connection'):
        local_data.connection = sqlite3.connect('telegram_bot.db', check_same_thread=False)
        local_data.connection.row_factory = sqlite3.Row
    return local_data.connection

def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table - Enhanced for better member data collection
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            aura_points INTEGER DEFAULT 0,
            is_bot INTEGER DEFAULT 0,
            language_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER DEFAULT 0
        )
    ''')
    
    # Chat members table - For tracking group membership
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_id INTEGER,
            status TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(chat_id, user_id)
        )
    ''')
    
    # Command usage tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            command TEXT,
            used_date DATE,
            last_announcement TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, chat_id, command, used_date)
        )
    ''')
    
    # Active fights table - Enhanced for comprehensive fight management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_fights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            challenger_id INTEGER,
            opponent_id INTEGER,
            fight_type TEXT DEFAULT 'user_initiated',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_at TIMESTAMP,
            last_reply_user_id INTEGER,
            last_reply_time TIMESTAMP,
            status TEXT DEFAULT 'pending',
            winner_id INTEGER,
            is_random_fight INTEGER DEFAULT 0,
            fight_data TEXT
        )
    ''')
    
    # Daily selections table (for commands that select users once per day)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_selections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            command TEXT,
            selected_user_id INTEGER,
            selected_user_id_2 INTEGER,
            selection_date DATE,
            selection_data TEXT,
            UNIQUE(chat_id, command, selection_date)
        )
    ''')
    
    # Random fights table - Track daily random fights
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS random_fights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user1_id INTEGER,
            user2_id INTEGER,
            fight_date DATE,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chat_id, fight_date)
        )
    ''')
    
    conn.commit()

def add_or_update_user(user_id, username=None, first_name=None, last_name=None, is_bot=False, language_code=None):
    """Add or update user information with enhanced data collection."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (
            user_id, username, first_name, last_name, is_bot, language_code,
            aura_points, message_count, last_seen
        )
        VALUES (?, ?, ?, ?, ?, ?, 
            COALESCE((SELECT aura_points FROM users WHERE user_id = ?), 0),
            COALESCE((SELECT message_count FROM users WHERE user_id = ?), 0) + 1,
            CURRENT_TIMESTAMP
        )
    ''', (user_id, username, first_name, last_name, int(is_bot), language_code, user_id, user_id))
    
    conn.commit()

def add_chat_member(chat_id, user_id, status='member'):
    """Add or update chat member information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO chat_members (chat_id, user_id, status, last_active)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (chat_id, user_id, status))
    
    conn.commit()

def update_member_activity(chat_id, user_id):
    """Update member's last activity timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE chat_members 
        SET last_active = CURRENT_TIMESTAMP 
        WHERE chat_id = ? AND user_id = ?
    ''', (chat_id, user_id))
    
    if cursor.rowcount == 0:
        # Member not in database, add them
        add_chat_member(chat_id, user_id)
    
    conn.commit()

def update_aura_points(user_id, points):
    """Update user's aura points."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET aura_points = aura_points + ? 
        WHERE user_id = ?
    ''', (points, user_id))
    
    conn.commit()

def get_user_aura_points(user_id):
    """Get user's current aura points."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT aura_points FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    return result['aura_points'] if result else 0

def get_active_chat_members(chat_id, limit=None):
    """Get active members from a chat."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT u.*, cm.last_active 
        FROM users u
        JOIN chat_members cm ON u.user_id = cm.user_id
        WHERE cm.chat_id = ? AND u.is_bot = 0
        ORDER BY cm.last_active DESC
    '''
    
    if limit:
        query += f' LIMIT {limit}'
    
    cursor.execute(query, (chat_id,))
    return [dict(row) for row in cursor.fetchall()]

def get_daily_selection(chat_id, command, selection_date=None):
    """Get daily selection for a command."""
    if selection_date is None:
        selection_date = date.today()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM daily_selections 
        WHERE chat_id = ? AND command = ? AND selection_date = ?
    ''', (chat_id, command, selection_date))
    
    result = cursor.fetchone()
    return dict(result) if result else None

def set_daily_selection(chat_id, command, selected_user_id, selected_user_id_2=None, selection_data=None, selection_date=None):
    """Set daily selection for a command."""
    if selection_date is None:
        selection_date = date.today()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO daily_selections 
        (chat_id, command, selected_user_id, selected_user_id_2, selection_date, selection_data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (chat_id, command, selected_user_id, selected_user_id_2, selection_date, selection_data))
    
    conn.commit()

def has_used_command_today(user_id, chat_id, command):
    """Check if user has used a command today."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = date.today()
    cursor.execute('''
        SELECT 1 FROM command_usage 
        WHERE user_id = ? AND chat_id = ? AND command = ? AND used_date = ?
    ''', (user_id, chat_id, command, today))
    
    return cursor.fetchone() is not None

def record_command_usage(user_id, chat_id, command):
    """Record command usage for today."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = date.today()
    cursor.execute('''
        INSERT OR REPLACE INTO command_usage 
        (user_id, chat_id, command, used_date, last_announcement)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, chat_id, command, today))
    
    conn.commit()

def get_leaderboard(chat_id=None, limit=10):
    """Get aura points leaderboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if chat_id:
        cursor.execute('''
            SELECT u.user_id, u.username, u.first_name, u.last_name, u.aura_points
            FROM users u
            JOIN chat_members cm ON u.user_id = cm.user_id
            WHERE cm.chat_id = ? AND u.is_bot = 0 AND u.aura_points != 0
            ORDER BY u.aura_points DESC
            LIMIT ?
        ''', (chat_id, limit))
    else:
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, aura_points
            FROM users
            WHERE is_bot = 0 AND aura_points != 0
            ORDER BY aura_points DESC
            LIMIT ?
        ''', (limit,))
    
    return [dict(row) for row in cursor.fetchall()]

# Fight system database functions
def create_fight(chat_id, challenger_id, opponent_id, fight_type='user_initiated', is_random_fight=False):
    """Create a new fight."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO active_fights 
        (chat_id, challenger_id, opponent_id, fight_type, is_random_fight)
        VALUES (?, ?, ?, ?, ?)
    ''', (chat_id, challenger_id, opponent_id, fight_type, int(is_random_fight)))
    
    conn.commit()
    return cursor.lastrowid

def get_active_fight(chat_id, user_id=None):
    """Get active fight for chat or user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute('''
            SELECT * FROM active_fights 
            WHERE chat_id = ? AND (challenger_id = ? OR opponent_id = ?) 
            AND status IN ('pending', 'active')
            ORDER BY created_at DESC
            LIMIT 1
        ''', (chat_id, user_id, user_id))
    else:
        cursor.execute('''
            SELECT * FROM active_fights 
            WHERE chat_id = ? AND status IN ('pending', 'active')
            ORDER BY created_at DESC
            LIMIT 1
        ''', (chat_id,))
    
    result = cursor.fetchone()
    return dict(result) if result else None

def update_fight_status(fight_id, status, winner_id=None, last_reply_user_id=None):
    """Update fight status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status == 'active':
        cursor.execute('''
            UPDATE active_fights 
            SET status = ?, accepted_at = CURRENT_TIMESTAMP, last_reply_user_id = ?, last_reply_time = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, last_reply_user_id, fight_id))
    elif status in ['completed', 'timeout', 'draw']:
        cursor.execute('''
            UPDATE active_fights 
            SET status = ?, winner_id = ?
            WHERE id = ?
        ''', (status, winner_id, fight_id))
    else:
        cursor.execute('''
            UPDATE active_fights 
            SET status = ?, last_reply_user_id = ?, last_reply_time = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, last_reply_user_id, fight_id))
    
    conn.commit()

def update_fight_reply(fight_id, user_id):
    """Update fight with new reply."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE active_fights 
        SET last_reply_user_id = ?, last_reply_time = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (user_id, fight_id))
    
    conn.commit()

def cleanup_expired_fights():
    """Clean up expired fights."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Mark pending fights as timeout after FIGHT_ACCEPT_DURATION
    cursor.execute('''
        UPDATE active_fights 
        SET status = 'timeout'
        WHERE status = 'pending' 
        AND datetime(created_at, '+{} seconds') < datetime('now')
    '''.format(FIGHT_ACCEPT_DURATION))
    
    # Mark active fights as completed based on last reply time
    cursor.execute('''
        UPDATE active_fights 
        SET status = 'completed'
        WHERE status = 'active' 
        AND datetime(last_reply_time, '+{} seconds') < datetime('now')
    '''.format(FIGHT_REPLY_DURATION))
    
    conn.commit()

def has_daily_random_fight(chat_id, fight_date=None):
    """Check if chat has daily random fight."""
    if fight_date is None:
        fight_date = date.today()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 1 FROM random_fights 
        WHERE chat_id = ? AND fight_date = ?
    ''', (chat_id, fight_date))
    
    return cursor.fetchone() is not None

def create_daily_random_fight(chat_id, user1_id, user2_id, fight_date=None):
    """Create daily random fight record."""
    if fight_date is None:
        fight_date = date.today()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO random_fights 
        (chat_id, user1_id, user2_id, fight_date)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, user1_id, user2_id, fight_date))
    
    conn.commit()

# ---------------------------------------------------
# UTILITY FUNCTIONS (formerly utils.py)
# ---------------------------------------------------

def format_user_mention(user):
    """Format user mention for messages."""
    if hasattr(user, 'mention_html'):
        return user.mention_html()
    
    # Fallback for user objects without mention_html
    name = user.first_name
    if user.last_name:
        name += f" {user.last_name}"
    
    return f'<a href="tg://user?id={user.id}">{name}</a>'

def get_user_display_name(user):
    """Get user display name."""
    if user.username:
        return f"@{user.username}"
    
    name = user.first_name
    if user.last_name:
        name += f" {user.last_name}"
    
    return name

def is_nighttime_in_bangladesh():
    """Check if it's nighttime in Bangladesh (10 PM to 6 AM)."""
    bangladesh_tz = pytz.timezone(BANGLADESH_TZ)
    current_time = datetime.now(bangladesh_tz).time()
    
    night_start = time(22, 0)  # 10 PM
    night_end = time(6, 0)     # 6 AM
    
    return current_time >= night_start or current_time <= night_end

def format_aura_points(points):
    """Format aura points with appropriate emoji."""
    if points > 0:
        return f"+{points} ⬆️"
    elif points < 0:
        return f"{points} ⬇️"
    else:
        return "0 ➖"

def get_random_members(chat_id, count=1, exclude_ids=None):
    """Get random active members from chat."""
    if exclude_ids is None:
        exclude_ids = []
    
    members = get_active_chat_members(chat_id)
    
    # Filter out excluded users and bots
    eligible_members = [
        member for member in members 
        if member['user_id'] not in exclude_ids and not member['is_bot']
    ]
    
    if len(eligible_members) < count:
        return eligible_members
    
    return random.sample(eligible_members, count)

async def collect_chat_members(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Collect and store chat members."""
    try:
        # Get chat administrators first
        admins = await context.bot.get_chat_administrators(chat_id)
        for admin in admins:
            user = admin.user
            add_or_update_user(
                user.id, user.username, user.first_name, 
                user.last_name, user.is_bot, user.language_code
            )
            add_chat_member(chat_id, user.id, admin.status)
        
        logging.info(f"Collected {len(admins)} administrators for chat {chat_id}")
        
    except Exception as e:
        logging.error(f"Error collecting chat members for {chat_id}: {e}")

# ---------------------------------------------------
# COMMAND HANDLERS (formerly commands.py)
# ---------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    
    # Add user to database
    add_or_update_user(
        user.id, user.username, user.first_name, 
        user.last_name, user.is_bot, user.language_code
    )
    
    # Welcome message with inline keyboard
    welcome_text = f"""
🎯 <b>Welcome to the Ultimate Aura Bot, {user.mention_html()}!</b> 🎯

🌟 <b>Available Commands:</b>
• /gay - Find today's gay of the day
• /couple - Match today's perfect couple
• /simp - Discover the biggest simp
• /toxic - Expose the toxic member
• /cringe - Find the cringe master
• /respect - Show respect to someone special
• /sus - Find who's acting suspicious
• /ghost - Spooky nighttime command
• /fight @username - Challenge someone to a fight
• /randomfight - Start a random fight
• /aura - Check your aura points
• /leaderboard - View top aura holders
• /stats - View your statistics

💫 <b>Each command gives or takes aura points!</b>
🏆 Build your aura and climb the leaderboard!

🎮 <b>Fight System:</b>
Challenge others to epic battles and earn aura points!
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📢 Updates Channel", url=UPDATES_CHANNEL),
            InlineKeyboardButton("💬 Support Group", url=SUPPORT_GROUP)
        ],
        [InlineKeyboardButton("📊 Leaderboard", callback_data="leaderboard")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
🎯 <b>Aura Bot Commands Guide</b> 🎯

🎲 <b>Daily Commands (Once per day):</b>
• /gay - Find today's gay of the day (-100 aura)
• /couple - Match today's perfect couple (+100 aura each)
• /simp - Discover the biggest simp (-100 aura)
• /toxic - Expose the toxic member (-100 aura)
• /cringe - Find the cringe master (-100 aura)
• /respect - Show respect to someone special (+500 aura)
• /sus - Find who's acting suspicious (-100 aura)
• /ghost - Spooky nighttime command (-200 aura, night only)

⚔️ <b>Fight Commands:</b>
• /fight @username - Challenge someone to a fight
• /randomfight - Start a random fight between two members
• /accept - Accept a fight challenge

📊 <b>Info Commands:</b>
• /aura - Check your aura points
• /leaderboard - View top aura holders
• /stats - View your statistics
• /mystats - View detailed personal stats

🔧 <b>Admin Commands:</b>
• /setaura @user points - Set user's aura points
• /resetaura @user - Reset user's aura to 0
• /collectmembers - Manually collect chat members

📝 <b>Rules:</b>
• Most commands can only be used once per day
• Fight winners get +100 aura points
• Commands work in groups only
• Aura points are tracked across all groups

💡 <b>Tips:</b>
• Use /respect to give someone big aura boost
• Participate in fights to earn points
• Check /leaderboard to see your ranking
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML
    )

async def aura_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /aura command."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Get user's aura points
    points = get_user_aura_points(user.id)
    
    # Determine aura level
    if points >= 1000:
        level = "🔥 LEGENDARY"
        emoji = "👑"
    elif points >= 500:
        level = "⚡ EPIC"
        emoji = "🌟"
    elif points >= 100:
        level = "💫 RARE"
        emoji = "✨"
    elif points >= 0:
        level = "🌱 COMMON"
        emoji = "🙂"
    elif points >= -500:
        level = "💀 CURSED"
        emoji = "😵"
    else:
        level = "🔥 DAMNED"
        emoji = "👹"
    
    aura_text = f"""
{emoji} <b>Aura Status for {user.mention_html()}</b> {emoji}

💰 <b>Current Aura:</b> {points} points
🏅 <b>Aura Level:</b> {level}

{format_aura_points(points)}
"""
    
    # Add ranking if in group
    if chat.type in ['group', 'supergroup']:
        leaderboard = get_leaderboard(chat.id, 100)
        user_rank = None
        
        for i, entry in enumerate(leaderboard, 1):
            if entry['user_id'] == user.id:
                user_rank = i
                break
        
        if user_rank:
            aura_text += f"\n🏆 <b>Group Rank:</b> #{user_rank}"
        else:
            aura_text += f"\n📊 <b>Group Rank:</b> Not ranked"
    
    await update.message.reply_text(
        aura_text,
        parse_mode=ParseMode.HTML
    )

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command."""
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "❌ Leaderboard is only available in groups!"
        )
        return
    
    # Get leaderboard for this chat
    leaderboard = get_leaderboard(chat.id, 10)
    
    if not leaderboard:
        await update.message.reply_text(
            "📊 No aura points recorded yet! Start using commands to build your aura!"
        )
        return
    
    leaderboard_text = "🏆 <b>AURA LEADERBOARD</b> 🏆\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, entry in enumerate(leaderboard, 1):
        # Get medal or number
        if i <= 3:
            rank_symbol = medals[i-1]
        else:
            rank_symbol = f"{i}."
        
        # Format user name
        if entry['username']:
            name = f"@{entry['username']}"
        else:
            name = entry['first_name']
            if entry['last_name']:
                name += f" {entry['last_name']}"
        
        # Format points
        points = entry['aura_points']
        points_display = format_aura_points(points)
        
        leaderboard_text += f"{rank_symbol} {name} - {points_display}\n"
    
    await update.message.reply_text(
        leaderboard_text,
        parse_mode=ParseMode.HTML
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "❌ Stats are only available in groups!"
        )
        return
    
    # Get chat statistics
    members = get_active_chat_members(chat.id)
    total_members = len(members)
    
    # Calculate aura statistics
    total_aura = sum(member['aura_points'] for member in members)
    positive_aura_members = len([m for m in members if m['aura_points'] > 0])
    negative_aura_members = len([m for m in members if m['aura_points'] < 0])
    
    # Get top and bottom aura
    if members:
        top_member = max(members, key=lambda x: x['aura_points'])
        bottom_member = min(members, key=lambda x: x['aura_points'])
    else:
        top_member = bottom_member = None
    
    stats_text = f"""
📊 <b>GROUP STATISTICS</b> 📊

👥 <b>Members:</b> {total_members}
💰 <b>Total Aura:</b> {total_aura} points
⬆️ <b>Positive Aura:</b> {positive_aura_members} members
⬇️ <b>Negative Aura:</b> {negative_aura_members} members
"""
    
    if top_member and top_member['aura_points'] != 0:
        top_name = top_member['username'] or top_member['first_name']
        stats_text += f"\n🔥 <b>Highest Aura:</b> @{top_name} ({top_member['aura_points']} points)"
    
    if bottom_member and bottom_member['aura_points'] != 0:
        bottom_name = bottom_member['username'] or bottom_member['first_name']
        stats_text += f"\n💀 <b>Lowest Aura:</b> @{bottom_name} ({bottom_member['aura_points']} points)"
    
    await update.message.reply_text(
        stats_text,
        parse_mode=ParseMode.HTML
    )

# Daily command handler
async def handle_daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    """Handle daily commands (gay, couple, simp, etc.)."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if it's a group
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "❌ This command only works in groups!"
        )
        return
    
    # Special check for ghost command (nighttime only)
    if command == 'ghost' and not is_nighttime_in_bangladesh():
        await update.message.reply_text(
            "👻 The ghost command only works during nighttime (10 PM - 6 AM Bangladesh time)! 🌙"
        )
        return
    
    # Check if user has already used this command today
    if has_used_command_today(user.id, chat.id, command):
        await update.message.reply_text(
            f"⏰ You've already used /{command} today! Try again tomorrow."
        )
        return
    
    # Check if command has already been used today in this chat
    existing_selection = get_daily_selection(chat.id, command)
    
    if existing_selection:
        # Command already used today, just show the result
        selected_user_id = existing_selection['selected_user_id']
        selected_user_id_2 = existing_selection.get('selected_user_id_2')
        
        # Get user objects (we'll need to fetch from database)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if command == 'couple' and selected_user_id_2:
            # Get both users for couple command
            cursor.execute('SELECT * FROM users WHERE user_id IN (?, ?)', (selected_user_id, selected_user_id_2))
            users = [dict(row) for row in cursor.fetchall()]
            
            if len(users) == 2:
                user1_obj = type('User', (), {
                    'id': users[0]['user_id'],
                    'first_name': users[0]['first_name'],
                    'last_name': users[0]['last_name'],
                    'username': users[0]['username'],
                    'mention_html': lambda: f"<a href='tg://user?id={users[0]['user_id']}'>{users[0]['first_name']}</a>"
                })()
                
                user2_obj = type('User', (), {
                    'id': users[1]['user_id'],
                    'first_name': users[1]['first_name'],
                    'last_name': users[1]['last_name'],
                    'username': users[1]['username'],
                    'mention_html': lambda: f"<a href='tg://user?id={users[1]['user_id']}'>{users[1]['first_name']}</a>"
                })()
                
                message = random.choice(COMMAND_MESSAGES[command]).format(
                    user1=user1_obj, user2=user2_obj
                )
        else:
            # Single user commands
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (selected_user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                user_obj = type('User', (), {
                    'id': user_data['user_id'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'username': user_data['username'],
                    'mention_html': lambda: f"<a href='tg://user?id={user_data['user_id']}'>{user_data['first_name']}</a>"
                })()
                
                message = random.choice(COMMAND_MESSAGES[command]).format(user=user_obj)
        
        # Record that this user has used the command
        record_command_usage(user.id, chat.id, command)
        
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)
        return
    
    # First time today - select new user(s)
    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
    
    # Collect fresh member data
    if COLLECT_MEMBERS_ON_MESSAGE:
        await collect_chat_members(context, chat.id)
    
    # Get active members
    active_members = get_active_chat_members(chat.id, limit=100)
    
    if len(active_members) < (2 if command == 'couple' else 1):
        await update.message.reply_text(
            "❌ Not enough active members in this group!"
        )
        return
    
    # Select random member(s)
    if command == 'couple':
        selected_members = get_random_members(chat.id, count=2)
        if len(selected_members) < 2:
            await update.message.reply_text(
                "❌ Not enough members for couple selection!"
            )
            return
        
        user1 = selected_members[0]
        user2 = selected_members[1]
        
        # Create user objects for message formatting
        user1_obj = type('User', (), {
            'id': user1['user_id'],
            'first_name': user1['first_name'],
            'last_name': user1['last_name'],
            'username': user1['username'],
            'mention_html': lambda: f"<a href='tg://user?id={user1['user_id']}'>{user1['first_name']}</a>"
        })()
        
        user2_obj = type('User', (), {
            'id': user2['user_id'],
            'first_name': user2['first_name'],
            'last_name': user2['last_name'],
            'username': user2['username'],
            'mention_html': lambda: f"<a href='tg://user?id={user2['user_id']}'>{user2['first_name']}</a>"
        })()
        
        # Store selection
        set_daily_selection(chat.id, command, user1['user_id'], user2['user_id'])
        
        # Update aura points
        points = AURA_POINTS[command]
        update_aura_points(user1['user_id'], points)
        update_aura_points(user2['user_id'], points)
        
        # Format message
        message = random.choice(COMMAND_MESSAGES[command]).format(
            user1=user1_obj, user2=user2_obj
        )
        
    else:
        # Single user selection
        selected_members = get_random_members(chat.id, count=1)
        if not selected_members:
            await update.message.reply_text(
                "❌ No active members found!"
            )
            return
        
        selected_user = selected_members[0]
        
        # Create user object for message formatting
        user_obj = type('User', (), {
            'id': selected_user['user_id'],
            'first_name': selected_user['first_name'],
            'last_name': selected_user['last_name'],
            'username': selected_user['username'],
            'mention_html': lambda: f"<a href='tg://user?id={selected_user['user_id']}'>{selected_user['first_name']}</a>"
        })()
        
        # Store selection
        set_daily_selection(chat.id, command, selected_user['user_id'])
        
        # Update aura points
        points = AURA_POINTS[command]
        update_aura_points(selected_user['user_id'], points)
        
        # Format message
        message = random.choice(COMMAND_MESSAGES[command]).format(user=user_obj)
    
    # Record command usage
    record_command_usage(user.id, chat.id, command)
    
    # Send message
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

# Individual command handlers
async def gay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_daily_command(update, context, 'gay')

async def couple_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_daily_command(update, context, 'couple')

async def simp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_daily_command(update, context, 'simp')

async def toxic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_daily_command(update, context, 'toxic')

async def cringe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_daily_command(update, context, 'cringe')

async def respect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_daily_command(update, context, 'respect')

async def sus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_daily_command(update, context, 'sus')

async def ghost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_daily_command(update, context, 'ghost')

# ---------------------------------------------------
# FIGHT SYSTEM (formerly fight.py)
# ---------------------------------------------------

async def fight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fight command."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "⚔️ Fights are only available in groups!"
        )
        return
    
    # Check if there's already an active fight
    active_fight = get_active_fight(chat.id)
    if active_fight:
        await update.message.reply_text(
            "⚔️ There's already an active fight in this chat! Wait for it to finish."
        )
        return
    
    # Check if user mentioned someone
    if not context.args:
        await update.message.reply_text(
            "⚔️ Usage: /fight @username\n\nChallenge someone to an epic battle!"
        )
        return
    
    # Parse opponent
    opponent_username = context.args[0].lstrip('@')
    
    # Try to find opponent in chat members
    members = get_active_chat_members(chat.id)
    opponent = None
    
    for member in members:
        if (member['username'] and member['username'].lower() == opponent_username.lower()) or \
           (member['first_name'] and member['first_name'].lower() == opponent_username.lower()):
            opponent = member
            break
    
    if not opponent:
        await update.message.reply_text(
            f"❌ User @{opponent_username} not found in this chat!"
        )
        return
    
    # Check if user is trying to fight themselves
    if opponent['user_id'] == user.id:
        await update.message.reply_text(
            "🤪 You can't fight yourself! Find a real opponent!"
        )
        return
    
    # Check if opponent is a bot
    if opponent['is_bot']:
        await update.message.reply_text(
            "🤖 You can't fight bots! Challenge a human!"
        )
        return
    
    # Create fight
    fight_id = create_fight(chat.id, user.id, opponent['user_id'])
    
    # Create user objects for message formatting
    challenger_obj = type('User', (), {
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'mention_html': lambda: user.mention_html()
    })()
    
    opponent_obj = type('User', (), {
        'id': opponent['user_id'],
        'first_name': opponent['first_name'],
        'last_name': opponent['last_name'],
        'username': opponent['username'],
        'mention_html': lambda: f"<a href='tg://user?id={opponent['user_id']}'>{opponent['first_name']}</a>"
    })()
    
    # Send challenge message
    fight_message = random.choice(FIGHT_MESSAGES['user_fight_challenge']).format(
        challenger=challenger_obj, opponent=opponent_obj
    )
    
    # Add accept button
    keyboard = [[InlineKeyboardButton("⚔️ Accept Fight", callback_data=f"accept_fight_{fight_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        fight_message,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )

async def random_fight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /randomfight command."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "⚔️ Random fights are only available in groups!"
        )
        return
    
    # Check if there's already an active fight
    active_fight = get_active_fight(chat.id)
    if active_fight:
        await update.message.reply_text(
            "⚔️ There's already an active fight in this chat! Wait for it to finish."
        )
        return
    
    # Check if daily random fight already happened
    if has_daily_random_fight(chat.id):
        await update.message.reply_text(
            "🎯 Daily random fight already happened! Try again tomorrow."
        )
        return
    
    # Get random fighters
    fighters = get_random_members(chat.id, count=2)
    
    if len(fighters) < 2:
        await update.message.reply_text(
            "❌ Not enough active members for a random fight!"
        )
        return
    
    user1, user2 = fighters
    
    # Create fight
    fight_id = create_fight(chat.id, user1['user_id'], user2['user_id'], 'random', is_random_fight=True)
    
    # Record daily random fight
    create_daily_random_fight(chat.id, user1['user_id'], user2['user_id'])
    
    # Create user objects for message formatting
    user1_obj = type('User', (), {
        'id': user1['user_id'],
        'first_name': user1['first_name'],
        'last_name': user1['last_name'],
        'username': user1['username'],
        'mention_html': lambda: f"<a href='tg://user?id={user1['user_id']}'>{user1['first_name']}</a>"
    })()
    
    user2_obj = type('User', (), {
        'id': user2['user_id'],
        'first_name': user2['first_name'],
        'last_name': user2['last_name'],
        'username': user2['username'],
        'mention_html': lambda: f"<a href='tg://user?id={user2['user_id']}'>{user2['first_name']}</a>"
    })()
    
    # Send fight announcement
    fight_message = random.choice(FIGHT_MESSAGES['random_fight_announcement']).format(
        user1=user1_obj, user2=user2_obj
    )
    
    # Add accept buttons for both users
    keyboard = [
        [InlineKeyboardButton("⚔️ Accept Fight", callback_data=f"accept_fight_{fight_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        fight_message,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )

async def accept_fight_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fight acceptance callback."""
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat
    
    await query.answer()
    
    # Parse fight ID
    fight_id = int(query.data.split('_')[-1])
    
    # Get fight details
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM active_fights WHERE id = ?', (fight_id,))
    fight = cursor.fetchone()
    
    if not fight:
        await query.edit_message_text(
            "❌ Fight not found or expired!"
        )
        return
    
    fight = dict(fight)
    
    # Check if fight is still pending
    if fight['status'] != 'pending':
        await query.edit_message_text(
            "❌ This fight is no longer available!"
        )
        return
    
    # Check if user is a participant
    if user.id not in [fight['challenger_id'], fight['opponent_id']]:
        await query.answer("❌ You're not part of this fight!", show_alert=True)
        return
    
    # Update fight status to active
    update_fight_status(fight_id, 'active', last_reply_user_id=user.id)
    
    # Get user objects for message
    cursor.execute('SELECT * FROM users WHERE user_id IN (?, ?)', 
                   (fight['challenger_id'], fight['opponent_id']))
    users = [dict(row) for row in cursor.fetchall()]
    
    user1_data = next(u for u in users if u['user_id'] == fight['challenger_id'])
    user2_data = next(u for u in users if u['user_id'] == fight['opponent_id'])
    
    user1_obj = type('User', (), {
        'id': user1_data['user_id'],
        'first_name': user1_data['first_name'],
        'last_name': user1_data['last_name'],
        'username': user1_data['username'],
        'mention_html': lambda: f"<a href='tg://user?id={user1_data['user_id']}'>{user1_data['first_name']}</a>"
    })()
    
    user2_obj = type('User', (), {
        'id': user2_data['user_id'],
        'first_name': user2_data['first_name'],
        'last_name': user2_data['last_name'],
        'username': user2_data['username'],
        'mention_html': lambda: f"<a href='tg://user?id={user2_data['user_id']}'>{user2_data['first_name']}</a>"
    })()
    
    # Send fight started message
    fight_message = random.choice(FIGHT_MESSAGES['fight_accepted']).format(
        user1=user1_obj, user2=user2_obj
    )
    
    await query.edit_message_text(
        fight_message,
        parse_mode=ParseMode.HTML
    )

async def handle_fight_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages during active fights."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        return
    
    # Check if user is in an active fight
    active_fight = get_active_fight(chat.id, user.id)
    
    if not active_fight or active_fight['status'] != 'active':
        return
    
    fight = active_fight
    
    # Update fight with this reply
    update_fight_reply(fight['id'], user.id)
    
    # Start a timer to check for fight completion
    asyncio.create_task(check_fight_timeout(context, fight['id'], FIGHT_REPLY_DURATION))

async def check_fight_timeout(context: ContextTypes.DEFAULT_TYPE, fight_id: int, delay: int):
    """Check if fight has timed out after delay."""
    await asyncio.sleep(delay)
    
    # Get current fight status
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM active_fights WHERE id = ?', (fight_id,))
    fight = cursor.fetchone()
    
    if not fight:
        return
    
    fight = dict(fight)
    
    # Check if fight is still active and time has passed
    if fight['status'] == 'active':
        last_reply_time = datetime.fromisoformat(fight['last_reply_time'])
        time_passed = datetime.now() - last_reply_time
        
        if time_passed.total_seconds() >= FIGHT_REPLY_DURATION:
            # Fight timed out, last replier wins
            winner_id = fight['last_reply_user_id']
            
            # Update fight status
            update_fight_status(fight_id, 'completed', winner_id)
            
            # Get winner details
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (winner_id,))
            winner_data = dict(cursor.fetchone())
            
            winner_obj = type('User', (), {
                'id': winner_data['user_id'],
                'first_name': winner_data['first_name'],
                'last_name': winner_data['last_name'],
                'username': winner_data['username'],
                'mention_html': lambda: f"<a href='tg://user?id={winner_data['user_id']}'>{winner_data['first_name']}</a>"
            })()
            
            # Award aura points
            update_aura_points(winner_id, AURA_POINTS['fight_winner'])
            
            # Send winner message
            winner_message = random.choice(FIGHT_MESSAGES['fight_winner']).format(
                winner=winner_obj
            )
            
            await context.bot.send_message(
                chat_id=fight['chat_id'],
                text=winner_message,
                parse_mode=ParseMode.HTML
            )

# ---------------------------------------------------
# ADMIN COMMANDS (formerly admin.py)
# ---------------------------------------------------

async def set_aura_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to set user's aura points."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if user is admin (basic check)
    try:
        chat_member = await context.bot.get_chat_member(chat.id, user.id)
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text(
                "❌ Only administrators can use this command!"
            )
            return
    except:
        await update.message.reply_text(
            "❌ This command only works in groups!"
        )
        return
    
    # Parse arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /setaura @username points\n\nExample: /setaura @john 100"
        )
        return
    
    username = context.args[0].lstrip('@')
    try:
        points = int(context.args[1])
    except ValueError:
        await update.message.reply_text(
            "❌ Points must be a number!"
        )
        return
    
    # Find user
    members = get_active_chat_members(chat.id)
    target_user = None
    
    for member in members:
        if (member['username'] and member['username'].lower() == username.lower()) or \
           (member['first_name'] and member['first_name'].lower() == username.lower()):
            target_user = member
            break
    
    if not target_user:
        await update.message.reply_text(
            f"❌ User @{username} not found!"
        )
        return
    
    # Update aura points (set, not add)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET aura_points = ? 
        WHERE user_id = ?
    ''', (points, target_user['user_id']))
    
    conn.commit()
    
    target_name = target_user['username'] or target_user['first_name']
    
    await update.message.reply_text(
        f"✅ Set @{target_name}'s aura to {points} points!"
    )

async def reset_aura_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to reset user's aura points."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if user is admin
    try:
        chat_member = await context.bot.get_chat_member(chat.id, user.id)
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text(
                "❌ Only administrators can use this command!"
            )
            return
    except:
        await update.message.reply_text(
            "❌ This command only works in groups!"
        )
        return
    
    # Parse arguments
    if not context.args:
        await update.message.reply_text(
            "Usage: /resetaura @username\n\nExample: /resetaura @john"
        )
        return
    
    username = context.args[0].lstrip('@')
    
    # Find user
    members = get_active_chat_members(chat.id)
    target_user = None
    
    for member in members:
        if (member['username'] and member['username'].lower() == username.lower()) or \
           (member['first_name'] and member['first_name'].lower() == username.lower()):
            target_user = member
            break
    
    if not target_user:
        await update.message.reply_text(
            f"❌ User @{username} not found!"
        )
        return
    
    # Reset aura points
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET aura_points = 0 
        WHERE user_id = ?
    ''', (target_user['user_id'],))
    
    conn.commit()
    
    target_name = target_user['username'] or target_user['first_name']
    
    await update.message.reply_text(
        f"✅ Reset @{target_name}'s aura to 0 points!"
    )

async def collect_members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to manually collect chat members."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "❌ This command only works in groups!"
        )
        return
    
    # Check if user is admin
    try:
        chat_member = await context.bot.get_chat_member(chat.id, user.id)
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text(
                "❌ Only administrators can use this command!"
            )
            return
    except:
        await update.message.reply_text(
            "❌ Error checking admin status!"
        )
        return
    
    await update.message.reply_text("🔄 Collecting chat members...")
    
    await collect_chat_members(context, chat.id)
    
    # Get count of collected members
    members = get_active_chat_members(chat.id)
    
    await update.message.reply_text(
        f"✅ Successfully collected {len(members)} chat members!"
    )

# ---------------------------------------------------
# EVENT HANDLERS (formerly events.py)
# ---------------------------------------------------

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new member joining."""
    chat = update.effective_chat
    
    if not COLLECT_MEMBERS_ON_JOIN:
        return
    
    new_members = update.message.new_chat_members
    
    for member in new_members:
        if not member.is_bot:
            # Add user to database
            add_or_update_user(
                member.id, member.username, member.first_name,
                member.last_name, member.is_bot, member.language_code
            )
            
            # Add to chat members
            add_chat_member(chat.id, member.id)
            
            logging.info(f"New member {member.first_name} ({member.id}) joined chat {chat.id}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        return
    
    # Update user data
    if COLLECT_MEMBERS_ON_MESSAGE:
        add_or_update_user(
            user.id, user.username, user.first_name,
            user.last_name, user.is_bot, user.language_code
        )
        
        # Update member activity
        update_member_activity(chat.id, user.id)
    
    # Handle fight messages
    await handle_fight_message(update, context)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries."""
    query = update.callback_query
    
    if query.data.startswith('accept_fight_'):
        await accept_fight_callback(update, context)
    elif query.data == 'leaderboard':
        await query.answer()
        chat = query.message.chat
        
        if chat.type in ['group', 'supergroup']:
            # Show group leaderboard
            leaderboard = get_leaderboard(chat.id, 5)
            
            if leaderboard:
                leaderboard_text = "🏆 <b>TOP 5 AURA LEADERS</b> 🏆\n\n"
                
                medals = ["🥇", "🥈", "🥉", "4.", "5."]
                
                for i, entry in enumerate(leaderboard):
                    name = entry['username'] or entry['first_name']
                    points = format_aura_points(entry['aura_points'])
                    leaderboard_text += f"{medals[i]} @{name} - {points}\n"
            else:
                leaderboard_text = "📊 No aura points recorded yet!"
        else:
            leaderboard_text = "❌ Leaderboard only available in groups!"
        
        await query.edit_message_text(
            leaderboard_text,
            parse_mode=ParseMode.HTML
        )

# ---------------------------------------------------
# BACKGROUND TASKS (formerly tasks.py)
# ---------------------------------------------------

async def cleanup_expired_fights_task(context: ContextTypes.DEFAULT_TYPE):
    """Background task to cleanup expired fights."""
    cleanup_expired_fights()
    
    # Get expired fights that haven't been announced
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM active_fights 
        WHERE status = 'timeout' 
        AND winner_id IS NULL
    ''')
    
    expired_fights = [dict(row) for row in cursor.fetchall()]
    
    for fight in expired_fights:
        # Send timeout message
        timeout_message = random.choice(FIGHT_MESSAGES['fight_timeout'])
        
        try:
            await context.bot.send_message(
                chat_id=fight['chat_id'],
                text=timeout_message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logging.error(f"Error sending timeout message: {e}")
        
        # Mark as processed
        cursor.execute('''
            UPDATE active_fights 
            SET winner_id = -1 
            WHERE id = ?
        ''', (fight['id'],))
    
    conn.commit()

async def setup_background_tasks(application):
    """Setup background tasks."""
    # Run cleanup every 5 minutes
    job_queue = application.job_queue
    job_queue.run_repeating(
        cleanup_expired_fights_task,
        interval=300,  # 5 minutes
        first=10
    )

# ---------------------------------------------------
# MAIN APPLICATION (formerly main.py)
# ---------------------------------------------------

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )

async def post_init(application):
    """Post initialization tasks."""
    # Initialize database
    init_database()
    
    # Setup background tasks
    await setup_background_tasks(application)
    
    # Set bot commands
    commands = [
        BotCommand("start", "Start the bot and see welcome message"),
        BotCommand("help", "Show help and command list"),
        BotCommand("gay", "Find today's gay of the day"),
        BotCommand("couple", "Match today's perfect couple"),
        BotCommand("simp", "Discover the biggest simp"),
        BotCommand("toxic", "Expose the toxic member"),
        BotCommand("cringe", "Find the cringe master"),
        BotCommand("respect", "Show respect to someone special"),
        BotCommand("sus", "Find who's acting suspicious"),
        BotCommand("ghost", "Spooky nighttime command"),
        BotCommand("fight", "Challenge someone to a fight"),
        BotCommand("randomfight", "Start a random fight"),
        BotCommand("aura", "Check your aura points"),
        BotCommand("leaderboard", "View top aura holders"),
        BotCommand("stats", "View group statistics"),
    ]
    
    await application.bot.set_my_commands(commands)
    
    logging.info("Bot initialized successfully!")

def main():
    """Main function to run the bot."""
    setup_logging()
    
    if BOT_TOKEN == "your_bot_token_here":
        logging.error("Please set your BOT_TOKEN in environment variables!")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Daily command handlers
    application.add_handler(CommandHandler("gay", gay_command))
    application.add_handler(CommandHandler("couple", couple_command))
    application.add_handler(CommandHandler("simp", simp_command))
    application.add_handler(CommandHandler("toxic", toxic_command))
    application.add_handler(CommandHandler("cringe", cringe_command))
    application.add_handler(CommandHandler("respect", respect_command))
    application.add_handler(CommandHandler("sus", sus_command))
    application.add_handler(CommandHandler("ghost", ghost_command))
    
    # Info command handlers
    application.add_handler(CommandHandler("aura", aura_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Fight system handlers
    application.add_handler(CommandHandler("fight", fight_command))
    application.add_handler(CommandHandler("randomfight", random_fight_command))
    
    # Admin command handlers
    application.add_handler(CommandHandler("setaura", set_aura_command))
    application.add_handler(CommandHandler("resetaura", reset_aura_command))
    application.add_handler(CommandHandler("collectmembers", collect_members_command))
    
    # Event handlers
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Post initialization
    application.post_init = post_init
    
    # Run the bot
    logging.info("Starting bot...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()