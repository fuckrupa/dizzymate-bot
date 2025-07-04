# ---------------------------------------------------
# CONFIGURATION (formerly config.py)
# ---------------------------------------------------

import os
import logging
import random
import asyncio
import threading
import json
from datetime import datetime, date, time, timedelta

import pytz
import psycopg2
import psycopg2.extras
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
        "🏳️‍🌈 Today's Gay of the Day is {user}! 🌈✨",
        "🏳️‍🌈 Congratulations {user}, you're the fabulous Gay of the Day! 💅✨",
        "🌈 {user} has been crowned the Gay of the Day! 🏳️‍🌈👑"
    ],
    'couple': [
        "💕 Today's adorable couple is {user1} and {user2}! 💑✨",
        "❤️ Love is in the air! {user1} and {user2} are today's couple! 💕🥰",
        "👫 {user1} and {user2} make the perfect couple today! 💖✨"
    ],
    'simp': [
        "🥺 {user} is today's biggest simp! 💸👑",
        "😍 Behold the ultimate simp of the day: {user}! 🥺💕",
        "👑 {user} has achieved maximum simp level today! 🥺✨"
    ],
    'toxic': [
        "☠️ {user} is spreading toxic vibes today! 🤢💀",
        "🧪 Warning: {user} is today's most toxic member! ☠️⚠️",
        "💀 {user} wins the toxic award of the day! 🧪☠️"
    ],
    'cringe': [
        "😬 {user} is today's cringe master! 🤡💀",
        "🤢 Maximum cringe level achieved by {user}! 😬🤡",
        "💀 {user} made everyone cringe today! 😬✨"
    ],
    'respect': [
        "🫡 Infinite respect for {user}! 👑✨",
        "🙏 {user} deserves all the respect today! 🫡💫",
        "👑 Mad respect for {user}! 🙏✨"
    ],
    'sus': [
        "📮 {user} is acting pretty sus today! 👀🔍",
        "🤔 {user} looking sus af! 📮👀",
        "👀 Emergency meeting! {user} is sus! 📮🚨"
    ],
    'ghost': [
        "👻 {user} is tonight's spooky ghost! 🌙💀",
        "🌙 {user} haunts the darkness tonight! 👻⚰️",
        "💀 {user} emerges from the shadows! 👻🌑"
    ]
}

# Fight messages
FIGHT_MESSAGES = {
    'random_fight_announcement': [
        "⚔️ <b>RANDOM FIGHT ALERT!</b> ⚔️\n\n🥊 {user1} vs {user2} 🥊\n\n💥 Both fighters have 1 hour to accept this challenge!\n🏆 Winner gets +100 aura points!\n⏰ Fight expires if not accepted!",
        "🔥 <b>EPIC BATTLE ROYALE!</b> 🔥\n\n⚔️ {user1} vs {user2} ⚔️\n\n💪 Random fighters selected for today's battle!\n🏆 +100 aura awaits the victor!\n⏱️ 1 hour to accept or it's void!",
        "🌟 <b>ULTIMATE SHOWDOWN!</b> 🌟\n\n🥊 {user1} vs {user2} 🥊\n\n🎯 The arena awaits these random warriors!\n💰 +100 aura for the champion!\n⏰ Accept within 1 hour!"
    ],
    'user_fight_challenge': [
        "⚔️ <b>CHALLENGE ISSUED!</b> ⚔️\n\n🥊 {challenger} has challenged {opponent} to a fight!\n\n💥 {opponent}, do you accept this challenge?\n🏆 Winner gets +100 aura points!\n⏰ You have 1 hour to accept!",
        "🔥 <b>BATTLE CHALLENGE!</b> 🔥\n\n⚔️ {challenger} wants to fight {opponent}!\n\n💪 Will you accept this duel, {opponent}?\n🏆 +100 aura awaits the victor!\n⏱️ 1 hour to decide!",
        "🌟 <b>DUEL REQUEST!</b> 🌟\n\n🥊 {challenger} has thrown down the gauntlet!\n{opponent}, the challenge is yours!\n\n🎯 Accept to begin the battle!\n💰 +100 aura for the winner!"
    ],
    'fight_accepted': [
        "🔥 <b>FIGHT ACCEPTED!</b> 🔥\n\n⚔️ {user1} vs {user2} ⚔️\n\n💥 The battle has begun!\n🗣️ Both fighters must reply to each other!\n⏰ Last person to reply within 2 minutes wins!\n🏆 Winner gets +100 aura!",
        "⚡ <b>BATTLE COMMENCED!</b> ⚡\n\n🥊 {user1} vs {user2} 🥊\n\n🔥 Let the epic fight begin!\n💬 Reply to each other to fight!\n⏱️ 2-minute window for each exchange!\n🏆 +100 aura to the victor!",
        "🌟 <b>DUEL STARTED!</b> 🌟\n\n⚔️ {user1} vs {user2} ⚔️\n\n💪 The arena is set!\n🗨️ Exchange messages to battle!\n⏰ Last reply within 2 minutes wins!\n💰 +100 aura prize!"
    ],
    'fight_winner': [
        "🏆 <b>VICTORY!</b> 🏆\n\n👑 {winner} emerges victorious! 👑\n\n💪 What an epic battle!\n✨ +100 aura points awarded!\n🎉 Congratulations, champion!",
        "🥇 <b>CHAMPION CROWNED!</b> 🥇\n\n⚔️ {winner} wins the battle! ⚔️\n\n🔥 Incredible fighting spirit!\n💰 +100 aura points earned!\n🌟 Victory is yours!",
        "👑 <b>ULTIMATE WINNER!</b> 👑\n\n🏆 {winner} claims victory! 🏆\n\n💥 Outstanding performance!\n✨ +100 aura points added!\n🎊 Well fought, warrior!"
    ],
    'fight_draw': [
        "🤝 <b>IT'S A DRAW!</b> 🤝\n\n⚖️ {user1} and {user2} are equally matched!\n\n💥 Both fighters showed great skill!\n🏅 No aura points awarded for draws\n⚔️ Honor to both warriors!",
        "⚖️ <b>STALEMATE!</b> ⚖️\n\n🤜 {user1} vs {user2} 🤛\n\n🔥 Neither could claim victory!\n🤝 A draw between equals!\n⚔️ Both fought valiantly!",
        "🤝 <b>TIE GAME!</b> 🤝\n\n⚔️ {user1} and {user2} - perfectly matched!\n\n💪 Incredible battle, no winner!\n⚖️ Honor in the stalemate!\n🏅 Respect to both fighters!"
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

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/dbname")

def get_db_connection():
    """Get a thread-local PostgreSQL connection."""
    if not hasattr(local_data, 'conn'):
        local_data.conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        local_data.conn.autocommit = True
    return local_data.conn

def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            aura_points INTEGER DEFAULT 0,
            is_bot BOOLEAN DEFAULT FALSE,
            language_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER DEFAULT 0
        );
    """)

    # Chat members table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_members (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            user_id BIGINT,
            status TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chat_id, user_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)

    # Command usage tracking table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS command_usage (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            chat_id BIGINT,
            command TEXT,
            used_date DATE,
            last_announcement TIMESTAMP,
            UNIQUE(user_id, chat_id, command, used_date),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)

    # Active fights table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_fights (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            challenger_id BIGINT,
            opponent_id BIGINT,
            fight_type TEXT DEFAULT 'user_initiated',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_at TIMESTAMP,
            last_reply_user_id BIGINT,
            last_reply_time TIMESTAMP,
            status TEXT DEFAULT 'pending',
            winner_id BIGINT,
            is_random_fight BOOLEAN DEFAULT FALSE,
            fight_data JSONB,
            FOREIGN KEY (challenger_id) REFERENCES users(user_id),
            FOREIGN KEY (opponent_id) REFERENCES users(user_id)
        );
    """)

    # Daily selections table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_selections (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            command TEXT,
            selected_user_id BIGINT,
            selected_user_id_2 BIGINT,
            selection_date DATE,
            selection_data JSONB,
            UNIQUE(chat_id, command, selection_date)
        );
    """)

    # Random fights table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS random_fights (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            user1_id BIGINT,
            user2_id BIGINT,
            fight_date DATE,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chat_id, fight_date)
        );
    """)

    conn.commit()

def add_or_update_user(user_id, username=None, first_name=None, last_name=None, is_bot=False, language_code=None):
    """Add or update user information with enhanced data collection."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (
            user_id, username, first_name, last_name, is_bot, language_code,
            aura_points, message_count, last_seen
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            COALESCE((SELECT aura_points FROM users WHERE user_id = %s), 0),
            COALESCE((SELECT message_count FROM users WHERE user_id = %s), 0) + 1,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (user_id) DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            is_bot = EXCLUDED.is_bot,
            language_code = EXCLUDED.language_code,
            message_count = users.message_count + 1,
            last_seen = CURRENT_TIMESTAMP;
    """, (user_id, username, first_name, last_name, is_bot, language_code, user_id, user_id))

def add_chat_member(chat_id, user_id, status='member'):
    """Add or update chat member information."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO chat_members (
            chat_id, user_id, status, last_active
        )
        VALUES (
            %s, %s, %s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (chat_id, user_id) DO UPDATE SET
            status = EXCLUDED.status,
            last_active = CURRENT_TIMESTAMP;
    """, (chat_id, user_id, status))

def update_member_activity(chat_id, user_id):
    """Update member's last activity timestamp."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE chat_members
        SET last_active = CURRENT_TIMESTAMP
        WHERE chat_id = %s AND user_id = %s;
    """, (chat_id, user_id))
    if cur.rowcount == 0:
        add_chat_member(chat_id, user_id)

def update_aura_points(user_id, points):
    """Update user's aura points."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET aura_points = aura_points + %s WHERE user_id = %s;
    """, (points, user_id))

def can_use_command(user_id, chat_id, command):
    """Check if user can use a command (daily and hourly limits)."""
    conn = get_db_connection()
    cur = conn.cursor()
    today = date.today()
    cur.execute("""
        SELECT last_announcement FROM command_usage
        WHERE user_id = %s AND chat_id = %s AND command = %s AND used_date = %s;
    """, (user_id, chat_id, command, today))
    row = cur.fetchone()
    if row:
        last_ann = row['last_announcement']
        if last_ann and (datetime.now() - last_ann).total_seconds() < 3600:
            return False, 'hourly_limit'
        return False, 'daily_limit'
    return True, 'allowed'

def mark_command_used(user_id, chat_id, command):
    """Mark command usage for the day."""
    conn = get_db_connection()
    cur = conn.cursor()
    today = date.today()
    now = datetime.now()
    cur.execute("""
        INSERT INTO command_usage (
            user_id, chat_id, command, used_date, last_announcement
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, chat_id, command, used_date)
        DO UPDATE SET last_announcement = EXCLUDED.last_announcement;
    """, (user_id, chat_id, command, today, now))

def get_leaderboard(chat_id, limit=10):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.user_id, u.username, u.first_name, u.last_name, u.aura_points
        FROM users u
        JOIN chat_members cm ON cm.user_id = u.user_id
        WHERE cm.chat_id = %s AND u.is_bot = FALSE
        ORDER BY u.aura_points DESC
        LIMIT %s;
    """, (chat_id, limit))
    return cur.fetchall()

def get_chat_users(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.user_id, u.username, u.first_name, u.last_name
        FROM users u
        JOIN chat_members cm ON cm.user_id = u.user_id
        WHERE cm.chat_id = %s 
          AND cm.status IN ('member','administrator','creator') 
          AND u.is_bot = FALSE;
    """, (chat_id,))
    return cur.fetchall()

def get_active_chat_members(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.user_id, u.username, u.first_name, u.last_name
        FROM users u
        JOIN chat_members cm ON cm.user_id = u.user_id
        WHERE cm.chat_id = %s 
          AND cm.last_active >= NOW() - INTERVAL '30 days'
          AND cm.status IN ('member','administrator','creator')
          AND u.is_bot = FALSE;
    """, (chat_id,))
    return cur.fetchall()

def save_daily_selection(chat_id, command, user_id, user_id_2=None, selection_data=None):
    conn = get_db_connection()
    cur = conn.cursor()
    today = date.today()
    data_json = json.dumps(selection_data) if selection_data else None
    cur.execute("""
        INSERT INTO daily_selections (
            chat_id, command, selected_user_id, selected_user_id_2, selection_date, selection_data
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (chat_id, command, selection_date)
        DO UPDATE SET
            selected_user_id = EXCLUDED.selected_user_id,
            selected_user_id_2 = EXCLUDED.selected_user_id_2,
            selection_data = EXCLUDED.selection_data;
    """, (chat_id, command, user_id, user_id_2, today, data_json))

def get_daily_selection(chat_id, command):
    conn = get_db_connection()
    cur = conn.cursor()
    today = date.today()
    cur.execute("""
        SELECT selected_user_id, selected_user_id_2, selection_data
        FROM daily_selections
        WHERE chat_id = %s AND command = %s AND selection_date = %s;
    """, (chat_id, command, today))
    row = cur.fetchone()
    if row:
        return {
            'user_id': row['selected_user_id'],
            'user_id_2': row['selected_user_id_2'],
            'data': row['selection_data']
        }
    return None

def create_fight(chat_id, challenger_id, opponent_id, fight_type='user_initiated', is_random=False):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO active_fights (
            chat_id, challenger_id, opponent_id, fight_type, is_random_fight
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """, (chat_id, challenger_id, opponent_id, fight_type, is_random))
    return cur.fetchone()['id']

def get_active_fight(chat_id, fight_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM active_fights
        WHERE id = %s 
          AND chat_id = %s 
          AND status IN ('pending','active');
    """, (fight_id, chat_id))
    return cur.fetchone()

def get_user_active_fight(user_id, chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM active_fights
        WHERE chat_id = %s 
          AND (challenger_id = %s OR opponent_id = %s)
          AND status IN ('pending','active')
        ORDER BY created_at DESC
        LIMIT 1;
    """, (chat_id, user_id, user_id))
    return cur.fetchone()

def accept_fight(fight_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE active_fights
        SET accepted_at = CURRENT_TIMESTAMP, status = 'active'
        WHERE id = %s;
    """, (fight_id,))

def update_fight_reply(fight_id, user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE active_fights
        SET last_reply_user_id = %s, last_reply_time = CURRENT_TIMESTAMP
        WHERE id = %s;
    """, (user_id, fight_id))

def close_fight(fight_id, status='completed', winner_id=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE active_fights
        SET status = %s, winner_id = %s
        WHERE id = %s;
    """, (status, winner_id, fight_id))

def get_expired_fights():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM active_fights
        WHERE status = 'pending'
          AND created_at + INTERVAL '1 hour' <= NOW();
    """)
    pending = cur.fetchall()
    cur.execute("""
        SELECT *
        FROM active_fights
        WHERE status = 'active'
          AND last_reply_time + INTERVAL '2 minutes' <= NOW();
    """)
    active = cur.fetchall()
    return pending, active

def create_random_fight(chat_id, user1_id, user2_id):
    conn = get_db_connection()
    cur = conn.cursor()
    today = date.today()
    cur.execute("""
        INSERT INTO random_fights (
            chat_id, user1_id, user2_id, fight_date
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (chat_id, fight_date) DO NOTHING;
    """, (chat_id, user1_id, user2_id, today))

def get_todays_random_fight(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    today = date.today()
    cur.execute("""
        SELECT *
        FROM random_fights
        WHERE chat_id = %s AND fight_date = %s;
    """, (chat_id, today))
    return cur.fetchone()

def update_random_fight_status(chat_id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    today = date.today()
    cur.execute("""
        UPDATE random_fights
        SET status = %s
        WHERE chat_id = %s AND fight_date = %s;
    """, (status, chat_id, today))

def get_chat_member_count(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS count
        FROM chat_members
        WHERE chat_id = %s 
          AND status IN ('member','administrator','creator');
    """, (chat_id,))
    return cur.fetchone()['count']

def cleanup_old_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM active_fights
        WHERE status IN ('completed','expired','cancelled')
          AND created_at + INTERVAL '7 days' <= NOW();
    """)
    cur.execute("""
        DELETE FROM random_fights
        WHERE created_at + INTERVAL '30 days' <= NOW();
    """)
    conn.commit()

# ---------------------------------------------------
# MENTION HELPERS - replaced to always use first/last name
# ---------------------------------------------------

def _build_name(first_name: str | None, last_name: str | None) -> str:
    """Return 'First' or 'First Last' – falls back to 'User' if missing."""
    if first_name:
        return f"{first_name}{f' {last_name}' if last_name else ''}"
    return "User"

def get_user_mention_html(user) -> str:
    """Clickable mention that always shows the person’s name, never @username."""
    display = _build_name(user.first_name, getattr(user, 'last_name', None))
    return f'{sanitize_html(display)}'

def get_user_mention_html_from_data(
    user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None
) -> str:
    """Clickable mention using stored data, prioritizing first/last name."""
    display = sanitize_html(_build_name(first_name, last_name))
    return f'<a href="tg://user?id={user_id}">{display}</a>'

def format_user_display_name(username: str | None, first_name: str | None, last_name: str | None) -> str:
    """Utility to format a user’s display name."""
    return _build_name(first_name, last_name)

# ---------------------------------------------------
# TIME UTILS FOR GHOST COMMAND
# ---------------------------------------------------

def is_night_time_in_bangladesh() -> bool:
    """Check if it's night time in Bangladesh (6 PM to 6 AM)."""
    bd_tz = pytz.timezone(BANGLADESH_TZ)
    bd_time = datetime.now(bd_tz).time()
    night_start = time(18, 0)  # 6 PM
    night_end = time(6, 0)     # 6 AM
    return bd_time >= night_start or bd_time <= night_end

def get_time_until_night() -> tuple[int, int]:
    """Get time remaining until night time in Bangladesh."""
    bd_tz = pytz.timezone(BANGLADESH_TZ)
    bd_now = datetime.now(bd_tz)
    bd_time = bd_now.time()
    if bd_time < time(18, 0):
        next_night = bd_now.replace(hour=18, minute=0, second=0, microsecond=0)
    else:
        next_night = bd_now.replace(hour=18, minute=0, second=0, microsecond=0) + timedelta(days=1)
    time_diff = next_night - bd_now
    hours = int(time_diff.total_seconds() // 3600)
    minutes = int((time_diff.total_seconds() % 3600) // 60)
    return hours, minutes

# ---------------------------------------------------
# RANDOM USER SELECTION
# ---------------------------------------------------

def select_random_users(users, count=1, exclude=None):
    if exclude is None:
        exclude = []
    available_users = [user for user in users if user['user_id'] not in exclude]
    if len(available_users) < count:
        return available_users
    return random.sample(available_users, count)

def select_random_users_seeded(users, count=1, seed=None, exclude=None):
    if exclude is None:
        exclude = []
    available_users = [user for user in users if user['user_id'] not in exclude]
    if len(available_users) < count:
        return available_users
    if seed:
        random.seed(seed)
    selected = random.sample(available_users, count)
    random.seed()
    return selected

# ---------------------------------------------------
# LEADERBOARD FORMATTING - updated
# ---------------------------------------------------

def format_aura_leaderboard(leaderboard_data, chat_title=None):
    """Format aura leaderboard message."""
    if not leaderboard_data:
        return "📊 <b>Aura Leaderboard</b> 📊\n\n❌ No data available yet! Use some commands to get started! 🚀"

    title = "📊 <b>Aura Leaderboard</b>"
    if chat_title:
        title += f" - <b>{chat_title}</b>"
    title += " 📊\n\n"

    leaderboard_text = title
    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(leaderboard_data):
        position = i + 1
        user_mention = get_user_mention_html_from_data(
            user["user_id"], user["username"], user["first_name"], user["last_name"]
        )
        aura = user["aura_points"]
        if position <= 3:
            medal = medals[position - 1]
            leaderboard_text += f"{medal} {user_mention}! <b>{aura}</b> aura\n"
        else:
            leaderboard_text += f"🏅 {user_mention} <b>{aura}</b> aura\n"

    leaderboard_text += "\n💡 Use commands to gain or lose aura points!"
    return leaderboard_text

# ---------------------------------------------------
# FIGHT MESSAGE HELPERS
# ---------------------------------------------------

def get_fight_timeout_message():
    messages = [
        "⏰ Fight timed out! Both fighters chickened out! 🐔",
        "🕐 Time's up! It's a draw because nobody replied! 🤝",
        "⌛ Fight expired! Both warriors disappeared! 👻"
    ]
    return random.choice(messages)

def get_fight_draw_message():
    messages = [
        "🤝 It's a draw! Both fighters are equally matched! ⚔️",
        "⚖️ Draw! Neither fighter could claim victory! 🤝",
        "🤜🤛 Stalemate! Both warriors fought valiantly! ⚔️"
    ]
    return random.choice(messages)

def get_fight_winner_message():
    messages = [
        "🏆 {winner} emerges victorious! 👑⚔️",
        "💪 {winner} wins the battle! 🥇✨",
        "⚔️ Victory belongs to {winner}! 🏆🔥"
    ]
    return random.choice(messages)

# ---------------------------------------------------
# OTHER HELPERS
# ---------------------------------------------------

def extract_user_info(user):
    return {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': getattr(user, 'last_name', None),
        'is_bot': user.is_bot,
        'language_code': user.language_code
    }

def is_valid_fight_participant(user_id, challenger_id, opponent_id):
    return user_id in [challenger_id, opponent_id]

def format_fight_participants(user1_data, user2_data):
    u1 = get_user_mention_html_from_data(
        user1_data['user_id'],
        user1_data.get('username'),
        user1_data.get('first_name'),
        user1_data.get('last_name')
    )
    u2 = get_user_mention_html_from_data(
        user2_data['user_id'],
        user2_data.get('username'),
        user2_data.get('first_name'),
        user2_data.get('last_name')
    )
    return u1, u2

def get_random_fight_seed(chat_id, date_obj):
    return f"{chat_id}_{date_obj.strftime('%Y%m%d')}"

def calculate_fight_winner(fight_data, last_reply_user_id):
    return last_reply_user_id

def format_time_remaining(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

def is_admin_or_creator(member_status):
    return member_status in ['administrator', 'creator']

def sanitize_html(text: str) -> str:
    import html
    return html.escape(text)

# ---------------------------------------------------
# HANDLER FUNCTIONS (formerly handlers.py)
# ---------------------------------------------------

logger = logging.getLogger(__name__)

async def typing_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send typing action before responding."""
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(1)  # Short delay to make it feel natural
    except Exception as e:
        logger.warning(f"Could not send typing action: {e}")

async def collect_group_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect group members data when possible."""
    if update.effective_chat.type in ['private']:
        return

    chat_id = update.effective_chat.id
    try:
        # Check if bot is admin first
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status in ['administrator', 'creator']:
            # Bot is admin, can collect member list
            try:
                chat_member_count = await context.bot.get_chat_member_count(chat_id)
                logger.info(f"Chat {chat_id} has {chat_member_count} total members")
                if chat_member_count <= MAX_MEMBERS_PER_BATCH:
                    # Telegram Bot API doesn't provide direct member enumeration
                    pass
            except Exception as e:
                logger.warning(f"Could not get member count for chat {chat_id}: {e}")

        # Get chat administrators (always available)
        administrators = await context.bot.get_chat_administrators(chat_id)
        for admin in administrators:
            if admin.user and not admin.user.is_bot:
                user_info = extract_user_info(admin.user)
                add_or_update_user(**user_info)
                add_chat_member(chat_id, admin.user.id, admin.status)
        logger.info(f"Collected {len(administrators)} administrators for chat {chat_id}")
    except Exception as e:
        logger.warning(f"Could not collect group members for chat {chat_id}: {e}")

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new chat members."""
    if not update.message or not update.message.new_chat_members:
        return

    chat_id = update.effective_chat.id
    for member in update.message.new_chat_members:
        if not member.is_bot:
            user_info = extract_user_info(member)
            add_or_update_user(**user_info)
            add_chat_member(chat_id, member.id, 'member')
            logger.info(f"Added new member {member.id} to chat {chat_id}")

async def handle_member_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member leaving chat."""
    if not update.message or not update.message.left_chat_member:
        return

    chat_id = update.effective_chat.id
    user_id = update.message.left_chat_member.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE chat_members 
        SET status = 'left' 
        WHERE chat_id = ? AND user_id = ?
    ''', (chat_id, user_id))
    conn.commit()
    logger.info(f"Member {user_id} left chat {chat_id}")

async def track_message_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track user message activity for better member data collection."""
    if not update.effective_user or update.effective_user.is_bot:
        return
    if update.effective_chat.type == 'private':
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    user_info = extract_user_info(user)
    add_or_update_user(**user_info)
    update_member_activity(chat_id, user.id)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        welcome_text = (
            "🤖 <b>Welcome to the Ultimate Group Entertainment Bot!</b> 🎉\n\n"
            "I'm designed to bring fun and engagement to your group chats with:\n"
            "• 🏳️‍🌈 Daily fun selections and awards\n"
            "• ⚔️ Interactive fight system with random daily battles\n"
            "• 🏆 Aura point leaderboards\n"
            "• 🌙 Special night-time features\n"
            "• 📊 Enhanced member tracking\n\n"
            "Add me to your group and try commands like /gay, /couple, /fight, /aura and more!"
        )
        keyboard = [
            [
                InlineKeyboardButton("📢 Updates", url=UPDATES_CHANNEL),
                InlineKeyboardButton("💬 Support", url=SUPPORT_GROUP)
            ],
            [
                InlineKeyboardButton("➕ Add Me To Your Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    else:
        await collect_group_members(update, context)
        member_count = get_chat_member_count(update.effective_chat.id)
        await update.message.reply_text(
            f"👋 Hello! I'm ready to entertain your group! 🎉\n"
            f"📊 Currently tracking {member_count} members\n"
            f"🏆 Try /aura to see the leaderboard!",
            parse_mode=ParseMode.HTML
        )

async def gay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gay command."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "🏳️‍🌈 This command only works in groups! Add me to a group to use it! 📱",
            parse_mode=ParseMode.HTML
        )
        return
    await handle_single_user_command(update, context, 'gay')

async def couple_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /couple command."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "💕 This command only works in groups! Add me to a group to find couples! 📱",
            parse_mode=ParseMode.HTML
        )
        return
    await handle_couple_command(update, context)

async def simp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /simp command."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "🥺 This command only works in groups! Add me to a group to find simps! 📱",
            parse_mode=ParseMode.HTML
        )
        return
    await handle_single_user_command(update, context, 'simp')

async def toxic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /toxic command."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "☠️ This command only works in groups! Add me to a group to find toxic users! 📱",
            parse_mode=ParseMode.HTML
        )
        return
    await handle_single_user_command(update, context, 'toxic')

async def cringe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cringe command."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "😬 This command only works in groups! Add me to a group to find cringe users! 📱",
            parse_mode=ParseMode.HTML
        )
        return
    await handle_single_user_command(update, context, 'cringe')

async def respect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /respect command."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "🫡 This command only works in groups! Add me to a group to show respect! 📱",
            parse_mode=ParseMode.HTML
        )
        return
    await handle_single_user_command(update, context, 'respect')

async def sus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sus command."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "📮 This command only works in groups! Add me to a group to find sus users! 📱",
            parse_mode=ParseMode.HTML
        )
        return
    await handle_single_user_command(update, context, 'sus')

async def handle_single_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    """Handle commands that select a single user."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Track user activity and collect member data
    await track_message_activity(update, context)

    # Check if we already selected someone today
    selection_data = get_daily_selection(chat_id, command)
    if selection_data and selection_data['user_id']:
        can_announce, reason = can_use_command(user_id, chat_id, command)
        if not can_announce and reason == "hourly_limit":
            await update.message.reply_text(
                f"⏰ Slow down! You can only announce the {command.title()} of the Day once per hour! 🕐",
                parse_mode=ParseMode.HTML
            )
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (selection_data['user_id'],))
        selected_user = cursor.fetchone()

        if selected_user:
            user_mention = get_user_mention_html_from_data(
                selected_user["user_id"], selected_user["username"],
                selected_user["first_name"], selected_user["last_name"]
            )
            message = random.choice(COMMAND_MESSAGES[command]).format(user=user_mention)
            await update.message.reply_text(message, parse_mode=ParseMode.HTML)
            mark_command_used(user_id, chat_id, command)
        return

    # Get active chat users
    chat_users = get_active_chat_members(chat_id)
    if len(chat_users) < 1:
        await collect_group_members(update, context)
        chat_users = get_active_chat_members(chat_id)
        if len(chat_users) < 1:
            await update.message.reply_text(
                "🤔 Not enough users in the database! I need to see more member activity first! 👥\n"
                "💡 Have group members send some messages and try again!",
                parse_mode=ParseMode.HTML
            )
            return

    # Select random user
    selected_users = select_random_users(chat_users, 1)
    if not selected_users:
        await update.message.reply_text(
            "❌ Couldn't select a user! Try again later! 🔄",
            parse_mode=ParseMode.HTML
        )
        return

    selected_user = selected_users[0]
    save_daily_selection(chat_id, command, selected_user['user_id'])
    update_aura_points(selected_user['user_id'], AURA_POINTS[command])

    user_mention = get_user_mention_html_from_data(
        selected_user["user_id"], selected_user["username"],
        selected_user["first_name"], selected_user["last_name"]
    )
    message = random.choice(COMMAND_MESSAGES[command]).format(user=user_mention)
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    mark_command_used(user_id, chat_id, command)

async def handle_couple_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /couple command specifically."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    await track_message_activity(update, context)
    selection_data = get_daily_selection(chat_id, 'couple')
    if selection_data and selection_data['user_id'] and selection_data['user_id_2']:
        can_announce, reason = can_use_command(user_id, chat_id, 'couple')
        if not can_announce and reason == "hourly_limit":
            await update.message.reply_text(
                "⏰ Slow down! You can only announce the Couple of the Day once per hour! 💕",
                parse_mode=ParseMode.HTML
            )
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id IN (?, ?)',
                      (selection_data['user_id'], selection_data['user_id_2']))
        users = cursor.fetchall()

        if len(users) == 2:
            user1_mention = get_user_mention_html_from_data(
                users[0]["user_id"], users[0]["username"],
                users[0]["first_name"], users[0]["last_name"]
            )
            user2_mention = get_user_mention_html_from_data(
                users[1]["user_id"], users[1]["username"],
                users[1]["first_name"], users[1]["last_name"]
            )
            message = random.choice(COMMAND_MESSAGES['couple']).format(
                user1=user1_mention, user2=user2_mention
            )
            await update.message.reply_text(message, parse_mode=ParseMode.HTML)
            mark_command_used(user_id, chat_id, 'couple')
        return

    chat_users = get_active_chat_members(chat_id)
    if len(chat_users) < 2:
        await collect_group_members(update, context)
        chat_users = get_active_chat_members(chat_id)
        if len(chat_users) < 2:
            await update.message.reply_text(
                "🤔 Not enough users in the database! Need at least 2 users for a couple! 👥\n"
                "💡 Have more group members send messages and try again!",
                parse_mode=ParseMode.HTML
            )
            return

    selected_users = select_random_users(chat_users, 2)
    if len(selected_users) < 2:
        await update.message.reply_text(
            "❌ Couldn't select a couple! Try again later! 🔄",
            parse_mode=ParseMode.HTML
        )
        return

    save_daily_selection(chat_id, 'couple', selected_users[0]['user_id'], selected_users[1]['user_id'])
    update_aura_points(selected_users[0]['user_id'], AURA_POINTS['couple'])
    update_aura_points(selected_users[1]['user_id'], AURA_POINTS['couple'])

    user1_mention = get_user_mention_html_from_data(
        selected_users[0]["user_id"], selected_users[0]["username"],
        selected_users[0]["first_name"], selected_users[0]["last_name"]
    )
    user2_mention = get_user_mention_html_from_data(
        selected_users[1]["user_id"], selected_users[1]["username"],
        selected_users[1]["first_name"], selected_users[1]["last_name"]
    )
    message = random.choice(COMMAND_MESSAGES['couple']).format(user1=user1_mention, user2=user2_mention)
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    mark_command_used(user_id, chat_id, 'couple')

async def fight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fight command."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "⚔️ This command only works in groups! Add me to a group to start fighting! 📱",
            parse_mode=ParseMode.HTML
        )
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    await track_message_activity(update, context)

    # User-initiated fight (reply)
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        opponent = update.message.reply_to_message.from_user
        if opponent.is_bot:
            await update.message.reply_text(
                "🤖 You can't fight bots! Challenge a real user! 👤",
                parse_mode=ParseMode.HTML
            )
            return
        if user_id == opponent.id:
            await update.message.reply_text(
                "🤔 You can't fight yourself! Challenge someone else! 👥",
                parse_mode=ParseMode.HTML
            )
            return

        challenger_fight = get_user_active_fight(user_id, chat_id)
        opponent_fight = get_user_active_fight(opponent.id, chat_id)

        if challenger_fight:
            await update.message.reply_text(
                "⚔️ You already have an active fight! Finish that one first! 🥊",
                parse_mode=ParseMode.HTML
            )
            return
        if opponent_fight:
            await update.message.reply_text(
                "⚔️ Your opponent already has an active fight! Try someone else! 🥊",
                parse_mode=ParseMode.HTML
            )
            return

        challenger_info = extract_user_info(update.effective_user)
        opponent_info = extract_user_info(opponent)
        add_or_update_user(**challenger_info)
        add_or_update_user(**opponent_info)

        fight_id = create_fight(chat_id, user_id, opponent.id, 'user_initiated')
        challenger_mention = get_user_mention_html(update.effective_user)
        opponent_mention = get_user_mention_html(opponent)
        message = random.choice(FIGHT_MESSAGES['user_fight_challenge']).format(
            challenger=challenger_mention, opponent=opponent_mention
        )

        keyboard = [
            [
                InlineKeyboardButton("⚔️ Accept Challenge", callback_data=f"accept_fight_{fight_id}"),
                InlineKeyboardButton("🏃‍♂️ Decline", callback_data=f"decline_fight_{fight_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        return

    # Handle random daily fight
    todays_fight = get_todays_random_fight(chat_id)
    if todays_fight:
        if todays_fight['status'] == 'completed':
            await update.message.reply_text(
                "⚔️ Today's random fight has already been completed! 🏆\nTry again tomorrow for a new battle! 🌅",
                parse_mode=ParseMode.HTML
            )
            return
        elif todays_fight['status'] in ['pending', 'active']:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id IN (?, ?)',
                          (todays_fight['user1_id'], todays_fight['user2_id']))
            users = cursor.fetchall()
            if len(users) == 2:
                user1_mention = get_user_mention_html_from_data(
                    users[0]["user_id"], users[0]["username"], users[0]["first_name"], users[0]["last_name"]
                )
                user2_mention = get_user_mention_html_from_data(
                    users[1]["user_id"], users[1]["username"], users[1]["first_name"], users[1]["last_name"]
                )
                message = random.choice(FIGHT_MESSAGES['random_fight_announcement']).format(
                    user1=user1_mention, user2=user2_mention
                )
                await update.message.reply_text(message, parse_mode=ParseMode.HTML)
            return

    # Create new random fight
    chat_users = get_active_chat_members(chat_id)
    if len(chat_users) < 2:
        await collect_group_members(update, context)
        chat_users = get_active_chat_members(chat_id)
        if len(chat_users) < 2:
            await update.message.reply_text(
                "🤔 Not enough users for a random fight! Need at least 2 active members! 👥\n"
                "💡 Have more group members send messages and try again!",
                parse_mode=ParseMode.HTML
            )
            return

    today_date = date.today()
    seed = get_random_fight_seed(chat_id, today_date)
    selected_users = select_random_users_seeded(chat_users, 2, seed)

    if len(selected_users) < 2:
        await update.message.reply_text(
            "❌ Couldn't select fighters for random battle! Try again later! 🔄",
            parse_mode=ParseMode.HTML
        )
        return

    create_random_fight(chat_id, selected_users[0]['user_id'], selected_users[1]['user_id'])
    user1_mention = get_user_mention_html_from_data(
        selected_users[0]["user_id"], selected_users[0]["username"],
        selected_users[0]["first_name"], selected_users[0]["last_name"]
    )
    user2_mention = get_user_mention_html_from_data(
        selected_users[1]["user_id"], selected_users[1]["username"],
        selected_users[1]["first_name"], selected_users[1]["last_name"]
    )
    message = random.choice(FIGHT_MESSAGES['random_fight_announcement']).format(
        user1=user1_mention, user2=user2_mention
    )
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

    # Start 1-hour timer for random fight
    context.job_queue.run_once(
        random_fight_timeout_callback,
        when=timedelta(hours=1),
        chat_id=chat_id,
        data={'chat_id': chat_id, 'user1_id': selected_users[0]['user_id'], 'user2_id': selected_users[1]['user_id']}
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks."""
    query = update.callback_query
    # Do not call `await query.answer()` unconditionally here—that would suppress pop‐ups.

    # Parse callback_data (e.g. "accept_fight_<id>" or "decline_fight_<id>")
    parts = query.data.split('_')
    action = parts[0]       # "accept" or "decline"
    fight_id = int(parts[2]) if len(parts) >= 3 else None
    chat_id = query.message.chat_id

    # 1) Fetch the fight from DB (may have expired or been handled already)
    fight = get_active_fight(chat_id, fight_id)
    if not fight:
        # If the fight no longer exists, show a pop-up and return
        await query.answer("❌ This fight is no longer available!", show_alert=True)
        return

    # 2) Only the challenged user (opponent_id) may click “Accept” or “Decline.”
    #    If anyone else taps the button, show a pop-up.
    if query.from_user.id != fight['opponent_id']:
        await query.answer("❌ Only the challenged user can use this button!", show_alert=True)
        return

    # 3) At this point, we know the click is from the correct opponent → dispatch:
    if action == 'accept':
        await handle_accept_fight(update, context, fight_id)
    elif action == 'decline':
        await handle_decline_fight(update, context, fight_id)
    else:
        # In case of malformed callback_data:
        await query.answer("⚠️ Unknown action.", show_alert=True)


async def handle_accept_fight(update: Update, context: ContextTypes.DEFAULT_TYPE, fight_id: int):
    """Handle fight acceptance."""
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    fight = get_active_fight(chat_id, fight_id)
    if not fight:
        await query.edit_message_text(
            "❌ This fight is no longer available! ⚔️",
            parse_mode=ParseMode.HTML
        )
        return

    # Double‐check once more that ONLY the opponent can accept
    if user_id != fight['opponent_id']:
        await query.answer("❌ Only the challenged user can accept this fight!", show_alert=True)
        return

    # Mark fight as accepted
    accept_fight(fight_id)

    # Fetch both users’ info for nicely formatting the “Fight Accepted” message
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id IN (?, ?)',
                   (fight['challenger_id'], fight['opponent_id']))
    users = cursor.fetchall()
    if len(users) == 2:
        user1_data = users[0] if users[0]['user_id'] == fight['challenger_id'] else users[1]
        user2_data = users[1] if users[1]['user_id'] == fight['opponent_id'] else users[0]
        user1_mention = get_user_mention_html_from_data(
            user1_data["user_id"], user1_data["username"], user1_data["first_name"], user1_data["last_name"]
        )
        user2_mention = get_user_mention_html_from_data(
            user2_data["user_id"], user2_data["username"], user2_data["first_name"], user2_data["last_name"]
        )
        message = random.choice(FIGHT_MESSAGES['fight_accepted']).format(
            user1=user1_mention, user2=user2_mention
        )
        await query.edit_message_text(message, parse_mode=ParseMode.HTML)


async def handle_decline_fight(update: Update, context: ContextTypes.DEFAULT_TYPE, fight_id: int):
    """Handle fight decline."""
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    fight = get_active_fight(chat_id, fight_id)
    if not fight:
        await query.edit_message_text(
            "❌ This fight is no longer available! ⚔️",
            parse_mode=ParseMode.HTML
        )
        return

    # Double‐check once more that ONLY the opponent can decline
    if user_id != fight['opponent_id']:
        await query.answer("❌ Only the challenged user can decline this fight!", show_alert=True)
        return

    # Mark fight as 'declined'
    close_fight(fight_id, 'declined')

    # Fetch the opponent’s info so we can say “X declined the fight!”
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        user_mention = get_user_mention_html_from_data(
            user_data["user_id"], user_data["username"], user_data["first_name"], user_data["last_name"]
        )
        await query.edit_message_text(
            f"🏃‍♂️ {user_mention} declined the fight! No battle today! 😔",
            parse_mode=ParseMode.HTML
        )


async def handle_fight_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in active fights."""
    if not update.message or not update.message.text:
        return
    if update.effective_chat.type == 'private':
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    await track_message_activity(update, context)

    fight = get_user_active_fight(user_id, chat_id)
    if not fight or fight['status'] != 'active':
        return

    update_fight_reply(fight['id'], user_id)
    other_user_id = fight['opponent_id'] if user_id == fight['challenger_id'] else fight['challenger_id']

    if fight['last_reply_user_id'] and fight['last_reply_user_id'] != user_id:
        context.job_queue.run_once(
            active_fight_winner_callback,
            when=timedelta(minutes=2),
            chat_id=chat_id,
            data={'fight_id': fight['id']}
        )


async def ghost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ghost command - only works at night in Bangladesh time."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "👻 This command only works in groups! Add me to a group to use it! 📱",
            parse_mode=ParseMode.HTML
        )
        return

    await track_message_activity(update, context)
    if not is_night_time_in_bangladesh():
        hours, minutes = get_time_until_night()
        await update.message.reply_text(
            f"🌅 The ghost only appears at night! (6 PM - 6 AM Bangladesh time)\n"
            f"⏰ Come back in {hours}h {minutes}m! 👻",
            parse_mode=ParseMode.HTML
        )
        return

    await handle_single_user_command(update, context, 'ghost')


async def aura_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /aura command - show leaderboard."""
    await typing_action(update, context)
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "📊 This command only works in groups! Add me to a group to see the aura leaderboard! 📱",
            parse_mode=ParseMode.HTML
        )
        return

    chat_id = update.effective_chat.id
    await track_message_activity(update, context)
    leaderboard = get_leaderboard(chat_id, limit=10)
    if not leaderboard:
        await collect_group_members(update, context)
        leaderboard = get_leaderboard(chat_id, limit=10)

    chat_title = update.effective_chat.title
    leaderboard_text = format_aura_leaderboard(leaderboard, chat_title)
    await update.message.reply_text(leaderboard_text, parse_mode=ParseMode.HTML)


async def random_fight_timeout_callback(context: ContextTypes.DEFAULT_TYPE):
    """Handle random fight timeout."""
    job_data = context.job.data
    chat_id = job_data['chat_id']
    todays_fight = get_todays_random_fight(chat_id)
    if todays_fight and todays_fight['status'] == 'pending':
        update_random_fight_status(chat_id, 'expired')
        message = random.choice(FIGHT_MESSAGES['fight_timeout'])
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.warning(f"Could not send random fight timeout message: {e}")


async def active_fight_winner_callback(context: ContextTypes.DEFAULT_TYPE):
    """Handle active fight winner determination."""
    job_data = context.job.data
    fight_id = job_data['fight_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM active_fights WHERE id = ?', (fight_id,))
    fight = cursor.fetchone()
    if not fight or fight['status'] != 'active':
        return

    winner_id = fight['last_reply_user_id']
    chat_id = fight['chat_id']

    if winner_id:
        update_aura_points(winner_id, AURA_POINTS['fight_winner'])
        close_fight(fight_id, 'completed', winner_id)
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (winner_id,))
        winner_data = cursor.fetchone()
        if winner_data:
            winner_mention = get_user_mention_html_from_data(
                winner_data["user_id"], winner_data["username"],
                winner_data["first_name"], winner_data["last_name"]
            )
            message = random.choice(FIGHT_MESSAGES['fight_winner']).format(winner=winner_mention)
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
                if fight['is_random_fight']:
                    update_random_fight_status(chat_id, 'completed')
            except Exception as e:
                logger.warning(f"Could not send winner message for fight {fight_id}: {e}")
    else:
        close_fight(fight_id, 'draw')
        cursor.execute('SELECT * FROM users WHERE user_id IN (?, ?)',
                       (fight['challenger_id'], fight['opponent_id']))
        users = cursor.fetchall()
        if len(users) == 2:
            user1_mention = get_user_mention_html_from_data(
                users[0]["user_id"], users[0]["username"],
                users[0]["first_name"], users[0]["last_name"]
            )
            user2_mention = get_user_mention_html_from_data(
                users[1]["user_id"], users[1]["username"],
                users[1]["first_name"], users[1]["last_name"]
            )
            message = random.choice(FIGHT_MESSAGES['fight_draw']).format(
                user1=user1_mention, user2=user2_mention
            )
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
                if fight['is_random_fight']:
                    update_random_fight_status(chat_id, 'draw')
            except Exception as e:
                logger.warning(f"Could not send draw message for fight {fight_id}: {e}")


async def cleanup_expired_fights(context: ContextTypes.DEFAULT_TYPE):
    """Cleanup expired fights - runs periodically."""
    try:
        pending_expired, active_expired = get_expired_fights()
        for fight in pending_expired:
            close_fight(fight['id'], 'expired')
            logger.info(f"Closed expired pending fight {fight['id']}")
        for fight in active_expired:
            winner_id = fight['last_reply_user_id']
            if winner_id:
                update_aura_points(winner_id, AURA_POINTS['fight_winner'])
                close_fight(fight['id'], 'completed', winner_id)
                logger.info(f"Determined winner {winner_id} for expired fight {fight['id']}")
            else:
                close_fight(fight['id'], 'draw')
                logger.info(f"Closed expired fight {fight['id']} as draw")
        cleanup_old_data()
    except Exception as e:
        logger.warning(f"Error during fight cleanup: {e}")


def setup_periodic_jobs(application):
    """Setup periodic background jobs."""
    job_queue = application.job_queue
    job_queue.run_repeating(
        cleanup_expired_fights,
        interval=30,
        first=10
    )
    logger.info("Periodic jobs setup completed")



# ---------------------------------------------------
# BOT ENTRYPOINT (formerly main.py)
# ---------------------------------------------------

async def on_startup(application: Application) -> None:
    """
    Run once when the bot starts. Registers commands in Telegram’s “/” menu.
    """
    commands = [
        BotCommand("start",   "👋 Start / Restart the bot"),
        BotCommand("gay",     "🏳️‍🌈 Gay of the Day"),
        BotCommand("couple",  "💕 Couple of the Day"),
        BotCommand("simp",    "🥺 Simp of the Day"),
        BotCommand("toxic",   "☠️ Toxic of the Day"),
        BotCommand("cringe",  "😬 Cringe of the Day"),
        BotCommand("respect", "🫡 Show Respect for a user"),
        BotCommand("sus",     "📮 Sus of the Day"),
        BotCommand("ghost",   "👻 Summon tonight’s Ghost"),
        BotCommand("fight",   "⚔️ Start or view a fight"),
        BotCommand("aura",    "📊 Show the aura leaderboard"),
    ]
    await application.bot.set_my_commands(commands)
    logging.getLogger(__name__).info("✅ Bot commands set in menu.")

def main():
    """Start the bot."""
    # Initialize database
    init_database()

    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).post_init(on_startup).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("gay", gay_command))
    application.add_handler(CommandHandler("couple", couple_command))
    application.add_handler(CommandHandler("simp", simp_command))
    application.add_handler(CommandHandler("toxic", toxic_command))
    application.add_handler(CommandHandler("fight", fight_command))
    application.add_handler(CommandHandler("cringe", cringe_command))
    application.add_handler(CommandHandler("respect", respect_command))
    application.add_handler(CommandHandler("sus", sus_command))
    application.add_handler(CommandHandler("ghost", ghost_command))
    application.add_handler(CommandHandler("aura", aura_command))

    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))

    # Add message handlers for member data collection and fight replies
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_fight_replies
    ))

    # Handler for new chat members
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        handle_new_member
    ))

    # Handler for members leaving
    application.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER,
        handle_member_left
    ))

    # Handler for all messages to track activity
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        track_message_activity
    ), group=1)

    # Setup periodic jobs
    setup_periodic_jobs(application)

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot...")
    application.run_polling(
        allowed_updates=["message", "callback_query", "chat_member"],
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()