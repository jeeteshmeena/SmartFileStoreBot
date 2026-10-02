import os
import sys
import time
import asyncio
from database import db, mongodb_version
from config import Config, temp
from platform import python_version
from translation import Translation
from plugins.lang import t, _tx
from pyrogram import Client, filters, enums, __version__ as pyrogram_version
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument



import logging
import re

logger = logging.getLogger(__name__)

def _clean_emoji(text: str) -> str:
    """Strips custom emoji tags (<emoji id="...">, <tg-emoji ...>) down to fallback unicode emoji."""
    if not text:
        return ""
    text = re.sub(r'<emoji id=["\'][^"\']*["\']>(.*?)</emoji>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<tg-emoji emoji-id=["\'][^"\']*["\']>(.*?)</tg-emoji>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'</?(?:emoji|tg-emoji)[^>]*>', '', text)
    return text

async def _safe_edit(bot, query, **kwargs):
    try:
        await query.answer()
    except Exception:
        pass

    msg = getattr(query, 'message', None)
    if not msg:
        chat_id = getattr(getattr(query, 'from_user', None), 'id', None)
        if chat_id:
            kwargs['chat_id'] = chat_id
            return await bot.send_message(**kwargs)
        return None

    if 'parse_mode' not in kwargs:
        kwargs['parse_mode'] = enums.ParseMode.HTML

    # Detect if message contains media (photo, animation, video, document, etc.)
    has_media = bool(
        getattr(msg, 'photo', None) or
        getattr(msg, 'animation', None) or
        getattr(msg, 'video', None) or
        getattr(msg, 'document', None) or
        getattr(msg, 'sticker', None) or
        getattr(msg, 'caption', None) is not None
    )

    if has_media:
        try:
            await msg.delete()
        except Exception:
            pass
        kwargs['chat_id'] = msg.chat.id
        return await bot.send_message(**kwargs)
    else:
        try:
            return await msg.edit_text(**kwargs)
        except Exception as e:
            err_str = str(e).lower()
            if "message is not modified" in err_str or "message_not_modified" in err_str:
                return msg
            try:
                await msg.delete()
            except Exception:
                pass
            kwargs['chat_id'] = msg.chat.id
            return await bot.send_message(**kwargs)

async def _main_buttons(user_id: int):
    from plugins.settings import is_any_owner
    is_admin = await is_any_owner(user_id) if user_id else False

    if is_admin:
        return [
            [
                InlineKeyboardButton('• Channels •', callback_data='settings#channels'),
                InlineKeyboardButton('• Batch Links •', callback_data='sl#start'),
            ],
            [
                InlineKeyboardButton('• Dlvr Bot Setup •', callback_data='settings#sharebot'),
                InlineKeyboardButton('• Status •', callback_data='status'),
            ],
            [
                InlineKeyboardButton('• About •', callback_data='about'),
                InlineKeyboardButton('• Lang •', callback_data='settings#lang'),
            ],
        ]
    else:
        return [
            [
                InlineKeyboardButton('• Channels •', callback_data='settings#channels'),
                InlineKeyboardButton('• Batch Links •', callback_data='sl#start'),
            ],
            [
                InlineKeyboardButton('• Status •', callback_data='status'),
                InlineKeyboardButton('• About •', callback_data='about'),
            ],
            [
                InlineKeyboardButton('• Lang •', callback_data='settings#lang'),
            ],
        ]

#  static fallback used before user_id is available 
_STATIC_BUTTONS = [
    [InlineKeyboardButton('📢 Main Channel',   url='https://t.me/MeJeetX')],
    [
        InlineKeyboardButton('💬 Support Group', url='https://t.me/+1p2hcQ4ZaupjNjI1'),
    ],
    [
        InlineKeyboardButton('• Channels •',     callback_data='settings#channels'),
        InlineKeyboardButton('• Batch Links •', callback_data='sl#start'),
    ],
    [
        InlineKeyboardButton('• Status •',       callback_data='status'),
        InlineKeyboardButton('• About •',        callback_data='about'),
    ],
    [
        InlineKeyboardButton('• Lang •',         callback_data='settings#lang'),
    ],
]

# ===================Start Function===================

@Client.on_message(filters.private & filters.command(['start', 'settings', 'menu']))
async def start(client, message):
    try:
        user = message.from_user
        if not user:
            return
        if not await db.is_user_exist(user.id):
            await db.add_user(user.id, user.first_name)
        else:
            await db.reactivate_user(user.id)

        # Check for deep-link batch delivery
        if len(message.command) > 1:
            param = message.command[1].strip()
            link_data = await db.get_share_link(param)
            if link_data:
                from plugins.share_bot import _process_start
                return await _process_start(client, message)

        configs = await db.get_configs(user.id)
        menu_image_id = configs.get('menu_image_id')
        btns = await _main_buttons(user.id)

        full_name = f"{user.first_name} {user.last_name}" if getattr(user, 'last_name', None) else user.first_name
        txt = await t(user.id, 'START_TXT', user.id, full_name)
        markup = InlineKeyboardMarkup(btns)

        sent = False
        if menu_image_id:
            try:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=menu_image_id,
                    caption=txt,
                    reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML
                )
                sent = True
            except Exception as pe:
                clean_txt = _clean_emoji(txt)
                try:
                    await client.send_photo(
                        chat_id=message.chat.id,
                        photo=menu_image_id,
                        caption=clean_txt,
                        reply_markup=markup,
                        parse_mode=enums.ParseMode.HTML
                    )
                    sent = True
                except Exception:
                    pass

        if not sent:
            try:
                await client.send_message(
                    chat_id=message.chat.id,
                    reply_markup=markup,
                    text=txt,
                    parse_mode=enums.ParseMode.HTML,
                    disable_web_page_preview=True
                )
            except Exception as me:
                clean_txt = _clean_emoji(txt)
                await client.send_message(
                    chat_id=message.chat.id,
                    reply_markup=markup,
                    text=clean_txt,
                    parse_mode=enums.ParseMode.HTML,
                    disable_web_page_preview=True
                )
    except Exception as e:
        logger.exception("Error in start handler: %s", e)
        try:
            btns = await _main_buttons(message.from_user.id if message.from_user else 0)
            await message.reply_text(
                "<b>🤖 Welcome to Smart File Store Bot!</b>\n\n"
                "Use the menu below to explore features:",
                reply_markup=InlineKeyboardMarkup(btns),
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass

# ==================Restart Function==================

@Client.on_message(filters.private & filters.command(['restart']) & filters.user(Config.BOT_OWNER_ID))
async def restart(client, message):
    msg = await message.reply_text(text="<i>Trying to restarting.....</i>")
    await asyncio.sleep(5)
    await msg.edit("<i>Server restarted successfully » </i>")
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.private & filters.command(['owner', 'panel', 'admin', 'ownerpanel', 'op']))
async def owner_cmd(bot, message):
    from plugins.owner_utils import is_any_owner
    if not await is_any_owner(message.from_user.id):
        return await message.reply_text("⛔ Owner only! You are not authorized to access this panel.")
    try:
        from plugins.settings import build_owner_panel
        txt, btns = await build_owner_panel(message.from_user.id)
        await message.reply_text(
            txt,
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception:
        await message.reply_text(
            "<b>👑 Owner Panel Access</b>\nClick below to open the secure admin panel.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Oᴘᴇɴ Oᴡɴᴇʀ Pᴀɴᴇʟ", callback_data="settings#owners")]]),
            parse_mode=enums.ParseMode.HTML
        )

# ==================Callback Functions==================

@Client.on_callback_query(filters.regex(r'^help'))
async def helpcb(bot, query):
    user_id = query.from_user.id
    lang = await db.get_language(user_id)
    await _safe_edit(bot, query, 
        text=_tx(lang, 'HELP_TXT'),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ᴜꜱᴇ ᴍᴇ » ', callback_data='how_to_use')],
            [InlineKeyboardButton('»  ꜱᴇᴛᴛɪɴɢꜱ', callback_data='settings#main')],
            [InlineKeyboardButton('«  ʙᴀᴄᴋ', callback_data='back')],
        ])
    )

@Client.on_callback_query(filters.regex(r'^how_to_use'))
async def how_to_use(bot, query):
    user_id = query.from_user.id
    lang = await db.get_language(user_id)
    await _safe_edit(bot, query, 
        text=_tx(lang, 'HOW_USE_TXT'),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('«  ʙᴀᴄᴋ', callback_data='help')]]),
        disable_web_page_preview=True,
    )

@Client.on_callback_query(filters.regex(r'^back'))
async def back(bot, query):
    try:
        await query.answer()
    except Exception:
        pass
    try:
        user_id = query.from_user.id
        configs = await db.get_configs(user_id)
        menu_image_id = configs.get('menu_image_id')
        btns = await _main_buttons(user_id)
        
        full_name = f"{query.from_user.first_name} {query.from_user.last_name}" if getattr(query.from_user, 'last_name', None) else query.from_user.first_name
        txt = await t(user_id, 'START_TXT', user_id, full_name)
        markup = InlineKeyboardMarkup(btns)

        sent = False
        if menu_image_id:
            if getattr(query.message, "photo", None):
                try:
                    await query.message.edit_caption(caption=txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
                    sent = True
                except Exception:
                    clean_txt = _clean_emoji(txt)
                    try:
                        await query.message.edit_caption(caption=clean_txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
                        sent = True
                    except Exception:
                        pass
            if not sent:
                try:
                    await query.message.delete()
                except Exception:
                    pass
                try:
                    await bot.send_photo(chat_id=query.message.chat.id, photo=menu_image_id, caption=txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
                    sent = True
                except Exception:
                    clean_txt = _clean_emoji(txt)
                    try:
                        await bot.send_photo(chat_id=query.message.chat.id, photo=menu_image_id, caption=clean_txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
                        sent = True
                    except Exception:
                        pass

        if not sent:
            msg = query.message
            if getattr(msg, "photo", None):
                try:
                    await msg.delete()
                except Exception:
                    pass
                try:
                    await bot.send_message(chat_id=msg.chat.id, text=txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                except Exception:
                    clean_txt = _clean_emoji(txt)
                    await bot.send_message(chat_id=msg.chat.id, text=clean_txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
            else:
                try:
                    await query.message.edit_text(text=txt, reply_markup=markup, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
                except Exception as e:
                    err_str = str(e).lower()
                    if "message is not modified" in err_str:
                        return
                    clean_txt = _clean_emoji(txt)
                    try:
                        await query.message.edit_text(text=clean_txt, reply_markup=markup, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
                    except Exception:
                        try:
                            await query.message.delete()
                        except Exception:
                            pass
                        await bot.send_message(chat_id=query.message.chat.id, text=clean_txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        logger.exception("Error in back callback: %s", e)

def get_bot_version():
    try:
        import subprocess
        r_cnt = subprocess.run(["git", "rev-list", "--count", "HEAD"], capture_output=True, text=True)
        r_hash = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
        
        commit_count = 0
        if r_cnt.returncode == 0 and r_cnt.stdout.strip():
            commit_count = int(r_cnt.stdout.strip())
            
        short_hash = ""
        if r_hash.returncode == 0 and r_hash.stdout.strip():
            short_hash = r_hash.stdout.strip()
            
        versions = ["Arya V1", "Arya VX1", "Arya V2X", "Arya Jup X"]
        selected = versions[commit_count % len(versions)]
        return selected
    except Exception:
        pass
    return "Arya V1"

def _simplify_commit(msg: str) -> str:
    """Convert a raw git commit message into a simple, user-friendly sentence."""
    import re as _re
    # Strip conventional commit prefixes like fix:, feat:, chore:, refactor: etc.
    msg = _re.sub(r'^(fix|feat|chore|refactor|style|docs|perf|test|build|ci|revert|hotfix|add|update|remove|merge|wip)[:(\[].*?[)\]]?:\s*', '', msg, flags=_re.IGNORECASE).strip()
    # Common technical patterns → plain words
    replacements = [
        (_re.compile(r'\[?[A-Z]+-\d+\]?'), ''),           # Jira ticket refs
        (_re.compile(r'\battr\b', _re.I), 'attribute'),
        (_re.compile(r'\bdb\b', _re.I), 'database'),
        (_re.compile(r'\bsts\b', _re.I), 'status object'),
        (_re.compile(r'\bregex\b', _re.I), 'pattern matching'),
        (_re.compile(r'\binit\b', _re.I), 'initialize'),
        (_re.compile(r'defensive programming', _re.I), 'crash prevention'),
        (_re.compile(r'\bfwd\b', _re.I), 'forwarding'),
        (_re.compile(r'\bundle\b', _re.I), 'topic message'),
        (_re.compile(r'→|->'), 'to'),
    ]
    for pattern, replacement in replacements:
        msg = pattern.sub(replacement, msg)
    msg = msg.strip(' .-,')
    if msg and not msg[0].isupper():
        msg = msg[0].upper() + msg[1:]
    if msg and not msg.endswith('.'):
        msg += '.'
    return msg if len(msg) > 4 else None

def get_whats_new():
    try:
        import subprocess
        r = subprocess.run(
            ["git", "log", "-15", "--format=%s|%cs"],
            capture_output=True, text=True
        )
        if r.returncode == 0 and r.stdout.strip():
            lines = []
            for entry in r.stdout.strip().splitlines():
                parts = entry.split('|', 1)
                raw_msg = parts[0].strip()
                date_str = parts[1].strip() if len(parts) > 1 else ''
                # Format date
                try:
                    import datetime
                    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    date_label = dt.strftime('%d %b %Y')
                except Exception:
                    date_label = date_str
                simplified = _simplify_commit(raw_msg)
                if simplified:
                    lines.append(f"🔸 <b>{date_label}</b> — {simplified}")
            if lines:
                return '\n'.join(lines)
    except Exception:
        pass
    return "No recent updates found."

@Client.on_callback_query(filters.regex(r'^about'))
async def about(bot, query):
    try:
        await query.answer()
    except Exception:
        pass
    try:
        user_id = query.from_user.id
        lang = await db.get_language(user_id)
        txt = _tx(lang, 'ABOUT_TXT', python_version=python_version(), bot_version=get_bot_version())
        await _safe_edit(bot, query, 
            text=txt,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('📢 Mᴀɪɴ Cʜᴀɴɴᴇʟ',   url='https://t.me/MeJeetX')],
                [
                    InlineKeyboardButton('💬 Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url='https://t.me/+1p2hcQ4ZaupjNjI1'),
                    InlineKeyboardButton('🙋 Hᴇʟᴘ',  callback_data='help'),
                ],
                [InlineKeyboardButton('»  ᴡʜᴀᴛ\'s Nᴇᴡ', callback_data='whatsnew')],
                [InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data='back')]
            ]),
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[About] Error: {e}", exc_info=True)

@Client.on_callback_query(filters.regex(r'^whatsnew'))
async def whats_new(bot, query):
    try:
        await query.answer()
    except Exception:
        pass
    text = f"<b><u>»  WHAT'S NEW (Latest Updates)</u></b>\n\n{get_whats_new()}"
    await _safe_edit(bot, query, 
        text=text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('«  ʙᴀᴄᴋ', callback_data='about')]]),
        disable_web_page_preview=True,
        parse_mode=enums.ParseMode.HTML,
    )

def humanbytes(size):
    if not size: return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0: break
        size /= 1024.0
    return f"{size:.2f} {unit}"

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        curr_time = seconds % 60
        time_list.append(int(curr_time))
        seconds = int(seconds / 60)
        if seconds == 0: break
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + " "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

_last_net_sample = None  # (timestamp, bytes_recv, bytes_sent)

def _get_instant_net_speed():
    global _last_net_sample
    import psutil, time
    try:
        now = time.time()
        net = psutil.net_io_counters()
        if _last_net_sample:
            prev_t, prev_recv, prev_sent = _last_net_sample
            dt = max(now - prev_t, 0.001)
            dl_rate = (net.bytes_recv - prev_recv) / dt
            ul_rate = (net.bytes_sent - prev_sent) / dt
            _last_net_sample = (now, net.bytes_recv, net.bytes_sent)
            return humanbytes(dl_rate) + "/s", humanbytes(ul_rate) + "/s"
        else:
            _last_net_sample = (now, net.bytes_recv, net.bytes_sent)
            return "0 B/s", "0 B/s"
    except Exception:
        return "N/A", "N/A"

@Client.on_callback_query(filters.regex(r'^status'))
async def status(bot, query):
    try:
        await query.answer()
    except Exception:
        pass
    try:
        import time
        user_id = query.from_user.id
        lang = await db.get_language(user_id)
        
        users_count = await db.col.count_documents({})
        bots_count = await db.bot.count_documents({})
        total_channels = await db.total_channels()
        banned_count = await db.col.count_documents({"ban_status.is_banned": True})
        
        dl_speed, ul_speed = _get_instant_net_speed()
        
        stats = await db.get_global_stats()
        dl_files = stats.get('total_files_downloaded', 0)
        ul_files = stats.get('total_files_uploaded', 0)
        data_usage = humanbytes(stats.get('total_data_usage_bytes', 0))
        
        from main import START_TIME
        _db_start = stats.get('bot_start_time') or START_TIME
        uptime = get_readable_time(int(time.time() - _db_start))
        
        kwargs = {
            'users_count': users_count,
            'bots_count': bots_count,
            'total_channels': total_channels,
            'banned_users': banned_count,
            'total_files_downloaded': dl_files,
            'total_files_uploaded': ul_files,
            'total_data_usage_bytes': data_usage,
            'dl_speed': dl_speed,
            'ul_speed': ul_speed,
            'uptime': uptime
        }

        await _safe_edit(bot, query, 
            text=_tx(lang, 'STATUS_TXT', **kwargs),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('🔄 Rᴇғʀᴇsʜ', callback_data='status')],
                [InlineKeyboardButton('🗑 Cʟᴇᴀɴ Tᴇᴍᴘ', callback_data='sysmon#cleanup'), InlineKeyboardButton('«  Bᴀᴄᴋ', callback_data='back')]
            ]),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[Status] Error: {e}", exc_info=True)

# ══════════════════════════════════════════════════════════════════════════════
# /stats  — Owner only: detailed bot statistics
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.private & filters.command("resetstats") & filters.user(Config.BOT_OWNER_ID))
async def reset_stats(bot, message):
    await db.reset_global_stats()
    await message.reply_text("»  Global Stats successfully reset.")

@Client.on_message(filters.private & filters.command("stats") & filters.user(Config.BOT_OWNER_ID))
async def owner_stats(bot, message):
    import time as _time
    from main import START_TIME

    total_users        = await db.get_total_users_count()
    active_forwarding  = await db.get_active_forwardings_count()
    active_jobs        = await db.get_active_jobs_count()
    total_channels_cnt = await db.total_channels()
    _, bots_count      = await db.total_users_bots_count()

    elapsed = _time.time() - START_TIME
    d, rem  = divmod(int(elapsed), 86400)
    h, rem  = divmod(rem, 3600)
    m, s    = divmod(rem, 60)
    uptime  = f"{d}d {h}h {m}m {s}s"

    text = (
        "<b> »  Owner Stats </b>\n"
        "<b></b>\n"
        f"<b>  👥 Total Users     :</b> <code>{total_users}</code>\n"
        f"<b>  📡 Active Forwards  :</b> <code>{active_forwarding}</code>\n"
        f"<b>  »  Connected Bots   :</b> <code>{bots_count}</code>\n"
        f"<b>  »  Channels Saved   :</b> <code>{total_channels_cnt}</code>\n"
        f"<b>  🚫 Banned Users     :</b> <code>{len(temp.BANNED_USERS)}</code>\n"
        "<b></b>\n"
        f"<b>  »  Uptime            :</b> <code>{uptime}</code>\n"
        "<b></b>\n"
        "<b></b>"
    )
    await message.reply_text(text)

# ══════════════════════════════════════════════════════════════════════════════
# /replace  — Add a Find & Replace string for captions
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.private & filters.command("replace"))
async def replace_strings(bot, message):
    user_id = message.from_user.id
    if len(message.command) < 3:
        usage = (
            "<b>Usage:</b> <code>/replace old_text new_text</code>\n\n"
            "This will replace all instances of <code>old_text</code> with <code>new_text</code> in forwarded captions.\n"
            "Use <code>/replace clear</code> to remove all replacements."
        )
        if len(message.command) == 2 and message.command[1].lower() == 'clear':
            configs = await db.get_configs(user_id)
            configs['replacements'] = {}
            await db.update_configs(user_id, configs)
            return await message.reply_text("»  All text replacements cleared!")
        return await message.reply_text(usage)

    old_text = message.command[1]
    new_text = " ".join(message.command[2:])

    configs = await db.get_configs(user_id)
    replacements = configs.get('replacements', {})
    if old_text in replacements:
        del replacements[old_text]
    else:
        replacements[old_text] = new_text

    configs['replacements'] = replacements
    await db.update_configs(user_id, configs)
    await message.reply_text(f"»  Replacement added:\n\n<code>{old_text}</code> ➔ <code>{new_text}</code>")


# ══════════════════════════════════════════════════════════════════════════════
# /workers  — Owner only: show all worker node statuses + manual shift UI
# ══════════════════════════════════════════════════════════════════════════════

_WORKER_COLL    = "worker_registry"
_DEAD_THRESHOLD = 60   # seconds without heartbeat = dead
_COLL_MAP = {
    "merger":   ("mergejobs",    "🔀 Merger"),
    "cleaner":  ("cleaner_jobs", "🧹 Cleaner"),
    "multijob": ("multijobs",    "📋 MultiJob"),
    "taskjob":  ("taskjobs",     "⚙️ TaskJob"),
}

async def _workers_panel():
    """Return (text, keyboard) for the main worker status panel."""
    import time as _time
    workers = [w async for w in db.db[_WORKER_COLL].find({})]
    now = _time.time()

    if not workers:
        return (
            "🖥 <b>Worker Nodes</b>\n\n<i>No workers registered yet.\n"
            "Deploy a worker and it will appear here automatically.</i>",
            []
        )

    lines = ["🖥 <b>Worker Nodes — Live Status</b>\n"]
    for w in sorted(workers, key=lambda x: x.get("name", "")):
        name     = w.get("name", "Unknown")
        host     = w.get("host", "?")
        tasks    = ", ".join(w.get("tasks", [])) or "none"
        hb       = w.get("last_heartbeat", 0)
        age      = int(now - hb)
        cur_job  = w.get("current_job")
        cur_type = w.get("current_job_type", "")
        started  = w.get("started_at", 0)
        is_alive = age < _DEAD_THRESHOLD

        icon     = "🟢" if is_alive else "🔴"
        st_txt   = "Online" if is_alive else f"DEAD ({age}s ago)"

        if started:
            up = int(now - started)
            d, r = divmod(up, 86400); h, r = divmod(r, 3600); m, _ = divmod(r, 60)
            uptime = f"{d}d {h}h {m}m" if d else f"{h}h {m}m"
        else:
            uptime = "?"

        job_line = (
            f"  📌 <b>Running:</b> <code>{cur_type}</code> — <code>{cur_job[-8:]}</code>"
            if cur_job and is_alive else
            ("  💤 <b>Idle</b>" if is_alive else "  ❌ <b>No response</b>")
        )

        lines.append(
            f"{icon} <b>{name}</b>\n"
            f"  🖥 Host: <code>{host}</code>\n"
            f"  ⚙️ Tasks: <code>{tasks}</code>\n"
            f"  ⏱ Uptime: {uptime} | HB: {age}s ago\n"
            f"  {st_txt}\n{job_line}\n"
        )

    lines.append(f"<i>🕐 {_time.strftime('%I:%M %p IST')} | Dead = {_DEAD_THRESHOLD}s</i>")
    kb = [
        [InlineKeyboardButton("🔄 Refresh",         callback_data="wk#refresh")],
        [InlineKeyboardButton("🔀 Shift a Task",     callback_data="wk#shift_list")],
    ]
    return "\n".join(lines), kb


@Client.on_message(filters.private & filters.command("workers") & filters.user(Config.BOT_OWNER_ID))
async def workers_status(bot, message):
    txt, kb = await _workers_panel()
    await message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb) if kb else None,
                              parse_mode=enums.ParseMode.HTML)


@Client.on_callback_query(filters.regex(r"^wk#") & filters.user(Config.BOT_OWNER_ID))
async def workers_cb(bot, query):
    import time as _time
    parts  = query.data.split("#")
    action = parts[1] if len(parts) > 1 else ""

    # ── Refresh ──────────────────────────────────────────────────────────────
    if action == "refresh":
        txt, kb = await _workers_panel()
        try:
            await query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb),
                                          parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass
        return await query.answer("✅ Refreshed!")

    # ── List running/paused/failed jobs so user can pick one to shift ───────────────────────
    elif action == "shift_list":
        running = []
        for tt, (coll, label) in _COLL_MAP.items():
            try:
                async for job in db.db[coll].find({"status": {"$in": ["running", "paused", "failed"]}}):
                    jid    = job.get("job_id", "")
                    worker = job.get("worker_node", "?")
                    name   = (job.get("name") or job.get("output_name")
                              or job.get("base_name") or jid[-8:])
                    running.append((jid, tt, label, worker, name))
            except Exception:
                pass

        if not running:
            return await query.answer("⚠️ No running jobs right now.", show_alert=True)

        txt  = "🔀 <b>Select a job to shift to another worker:</b>\n\n"
        kb   = []
        for jid, tt, label, worker, name in running:
            txt += f"• {label}: <b>{name[:22]}</b> → <code>{worker}</code>\n"
            kb.append([InlineKeyboardButton(
                f"Shift {label} [{jid[-6:]}]",
                callback_data=f"wk#pick#{jid}#{tt}"
            )])
        kb.append([InlineKeyboardButton("❮ Back", callback_data="wk#refresh")])
        try:
            await query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb),
                                          parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass

    # ── Pick target worker ────────────────────────────────────────────────────
    elif action == "pick" and len(parts) >= 4:
        job_id = parts[2]; task_type = parts[3]
        workers = [w async for w in db.db[_WORKER_COLL].find({"status": "online"})]
        ok = [w for w in workers if task_type in w.get("tasks", [])]

        if not ok:
            return await query.answer(f"No online workers handle '{task_type}'!", show_alert=True)

        txt = (
            f"🔀 <b>Shift Job</b> <code>[{job_id[-8:]}]</code>\n\n"
            f"Choose the destination worker.\n"
            f"<i>Job will be re-queued. That worker will pick it up in ≤8s.\n"
            f"Progress already saved — job continues from checkpoint.</i>"
        )
        kb = []
        for w in sorted(ok, key=lambda x: x.get("name", "")):
            idle = "💤" if not w.get("current_job") else "📌"
            kb.append([InlineKeyboardButton(
                f"{idle} {w['name']}",
                callback_data=f"wk#do#{job_id}#{task_type}#{w['name']}"
            )])
        kb.append([InlineKeyboardButton("❮ Back", callback_data="wk#shift_list")])
        try:
            await query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb),
                                          parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass

    # ── Execute the shift ─────────────────────────────────────────────────────
    elif action == "do" and len(parts) >= 5:
        job_id = parts[2]; task_type = parts[3]; target = parts[4]
        coll   = _COLL_MAP.get(task_type, (None,))[0]
        if not coll:
            return await query.answer("Unknown task type.", show_alert=True)

        result = await db.db[coll].find_one_and_update(
            {"job_id": job_id},
            {"$set": {
                "status":       "queued",
                "worker_node":  None,
                "shift_target": target,
                "shifted_at":   _time.time(),
                "shifted_by":   "manual",
            }}
        )
        if result:
            await query.answer(f"✅ Re-queued! {target} picks it up.", show_alert=True)
            txt, kb = await _workers_panel()
            try:
                await query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb),
                                              parse_mode=enums.ParseMode.HTML)
            except Exception:
                pass
        else:
            await query.answer("❌ Job not found — may have already finished.", show_alert=True)


# ── Delivery Pass Admin Commands ──────────────────────────────────────────────
@Client.on_message(filters.command(["grantpass", "addpass", "addcustomer"]) & filters.private)
async def cmd_grant_pass(client, message):
    from plugins.banned import _is_any_owner
    from database import format_duration_friendly, format_duration_verbose
    if not await _is_any_owner(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 3:
        return await message.reply_text(
            "<b>Usage:</b> <code>/grantpass &lt;user_id&gt; &lt;duration&gt; [basic|pro|premium]</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/grantpass 12345678 7d pro</code> (7 Days Pro Pass)\n"
            "• <code>/grantpass 12345678 30m basic</code> (30 Minutes Basic Pass)\n"
            "• <code>/grantpass 12345678 1mo premium</code> (1 Month Premium Pass)"
        )
    try:
        target_uid = int(args[1])
        dur_input = args[2].strip()
        tier_input = "basic"
        if len(args) > 3:
            raw_t = args[3].lower().strip()
            if raw_t in ("pro", "p"):
                tier_input = "pro"
            elif raw_t in ("premium", "prem"):
                tier_input = "premium"
            else:
                tier_input = "basic"
        new_expiry = await db.grant_user_unlimited_pass(target_uid, dur_input, tier=tier_input)
    except Exception:
        return await message.reply_text("❌ Invalid User ID or Duration format (e.g. <code>30m</code>, <code>2h</code>, <code>7d</code>).")

    import datetime
    try:
        import pytz
        ist_tz = pytz.timezone('Asia/Kolkata')
        exp_dt = datetime.datetime.fromtimestamp(new_expiry, tz=ist_tz)
        exp_str = exp_dt.strftime('%d-%m-%Y %I:%M %p')
    except Exception:
        exp_str = datetime.datetime.fromtimestamp(new_expiry).strftime('%d-%m-%Y %I:%M %p')

    pass_data = await db.get_user_unlimited_pass(target_uid)
    time_left = pass_data.get('time_left_str', dur_input)
    tier_label = '<emoji id="5805553606635559688">👑</emoji> PRO PASS' if tier_input == 'pro' else ('<emoji id="6156730271858169904">💎</emoji> PREMIUM PASS' if tier_input == 'premium' else '<emoji id="5890925363067886150">⚡</emoji> BASIC PASS')
    await message.reply_text(
        f'<emoji id="5411359377904934337">✅</emoji> <b>Unlimited Pass Granted!</b>\n\n'
        f'<emoji id="6021683099773966917">🆔</emoji> <b>User ID:</b> <code>{target_uid}</code>\n'
        f'<emoji id="6021435576513730578">👑</emoji> <b>Tier:</b> <b>{tier_label}</b>\n'
        f'<emoji id="5807879906951960923">⏳</emoji> <b>Time Left:</b> <code>{time_left}</code>\n'
        f'<emoji id="5807427071370075099">📅</emoji> <b>Expires At:</b> <code>{exp_str}</code>'
    )

@Client.on_message(filters.command(["revokepass"]) & filters.private)
async def cmd_revoke_pass(client, message):
    from plugins.banned import _is_any_owner
    if not await _is_any_owner(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("<b>Usage:</b> <code>/revokepass &lt;user_id&gt;</code>")
    try:
        target_uid = int(args[1])
    except Exception:
        return await message.reply_text("❌ Invalid User ID.")

    await db.revoke_user_unlimited_pass(target_uid)
    await message.reply_text(f'<emoji id="5411359377904934337">✅</emoji> Unlimited Pass revoked for user <code>{target_uid}</code>.')

@Client.on_message(filters.command(["pass_status"]) & filters.private)
async def cmd_pass_status(client, message):
    from plugins.banned import _is_any_owner
    from database import format_duration_friendly
    if not await _is_any_owner(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("<b>Usage:</b> <code>/pass_status &lt;user_id&gt;</code>")
    try:
        target_uid = int(args[1])
    except Exception:
        return await message.reply_text("❌ Invalid User ID.")

    pass_data = await db.get_user_unlimited_pass(target_uid)
    rl_cfg = await db.get_delivery_rate_limit_config()
    win_sec = int(rl_cfg.get('window_seconds', int(rl_cfg.get('window_hours', 12)) * 3600))
    hits = await db.get_user_delivery_hits(target_uid, win_sec)
    win_friendly = format_duration_friendly(win_sec)

    status_str = '<emoji id="5411359377904934337">🟢</emoji> ACTIVE' if pass_data['active'] else '<emoji id="5774077015388852135">🔴</emoji> INACTIVE / FREE'
    exp_str = "N/A"
    if pass_data['expires_at']:
        import datetime
        try:
            import pytz
            ist_tz = pytz.timezone('Asia/Kolkata')
            exp_dt = datetime.datetime.fromtimestamp(pass_data['expires_at'], tz=ist_tz)
            exp_str = exp_dt.strftime('%d-%m-%Y %I:%M %p')
        except Exception:
            exp_str = datetime.datetime.fromtimestamp(pass_data['expires_at']).strftime('%d-%m-%Y %I:%M %p')

    time_left = pass_data.get('time_left_str', 'None')
    max_lim = rl_cfg.get('max_limit', 5)
    await message.reply_text(
        f'<emoji id="6032604359794104706">📊</emoji> <b>User Pass & Delivery Status</b>\n\n'
        f'<emoji id="6021683099773966917">🆔</emoji> <b>User ID:</b> <code>{target_uid}</code>\n'
        f'<emoji id="6007983438294949171">👑</emoji> <b>Pass Status:</b> {status_str}\n'
        f'<emoji id="5807427071370075099">📅</emoji> <b>Expires At:</b> <code>{exp_str}</code> (Time Left: {time_left})\n'
        f'<emoji id="5415825426633202840">⚡️</emoji> <b>Recent Deliveries (Past {win_friendly}):</b> {len(hits)} / {max_lim}'
    )


# ── Channel Management Commands ───────────────────────────────────────────────
@Client.on_message(filters.command(["addchannel", "addchannels", "addchat", "addchats"]) & filters.private)
async def cmd_add_channel(client, message):
    """Add one or multiple channels by ID, link, or username."""
    user_id = message.from_user.id
    raw_args = message.text.split(None, 1)
    if len(raw_args) < 2:
        return await message.reply_text(
            '<emoji id="5882207227997066107">➕</emoji> <b>Add Channel(s)</b>\n\n'
            "<b>Usage:</b> <code>/addchannel &lt;chat_id_1&gt; [chat_id_2] ...</code>\n\n"
            "<b>Examples:</b>\n"
            "• Single ID: <code>/addchannel -1001234567890</code>\n"
            "• Multiple IDs: <code>/addchannel -1001234567890 -1009876543210</code>\n"
            "• Link / Username: <code>/addchannel @mychannel https://t.me/anotherchannel</code>\n\n"
            "<i>Tip: You can pass multiple IDs separated by spaces, commas, or newlines. Ensure this bot is an admin in the channel(s) first.</i>"
        )

    import re, asyncio
    # Extract all possible tokens (IDs, links, usernames)
    tokens = re.findall(r'(?:https?://t\.me/(?:c/)?[\w\+]+|-?\d{5,16}|@[\w_]{4,32})', raw_args[1])
    if not tokens:
        tokens = [t.strip(' ,;') for t in raw_args[1].split() if t.strip(' ,;')]

    if not tokens:
        return await message.reply_text("❌ No valid channel IDs, usernames, or links found in your command.")

    existing_chs = await db.get_user_channels(user_id)
    cur_count = len(existing_chs)
    MAX_CHANNELS = 250

    added = []
    already_exists = []
    failed = []

    progress_msg = await message.reply_text(f"⏳ Processing {len(tokens)} channel(s)...")

    for token in tokens:
        if cur_count >= MAX_CHANNELS:
            failed.append((token, "Limit reached (max 250)"))
            continue

        raw_txt = token.strip()
        chat_id = None
        title = "Unknown Chat"
        username = "private"

        if raw_txt.lstrip('-').isdigit():
            chat_id = int(raw_txt)
        elif "t.me/c/" in raw_txt:
            m = re.search(r't\.me/c/(\d+)', raw_txt)
            if m:
                chat_id = int("-100" + m.group(1))
        elif "t.me/" in raw_txt:
            m = re.search(r't\.me/([^/\?#]+)', raw_txt.replace('https://', '').replace('http://', ''))
            if m and m.group(1) not in ['joinchat', '+', 'c']:
                chat_id = m.group(1)
                username = "@" + m.group(1)
        elif raw_txt.startswith('@'):
            chat_id = raw_txt
            username = raw_txt

        if not chat_id:
            failed.append((token, "Invalid ID / Link"))
            continue

        # Try to resolve chat via Telegram bot with timeout
        resolved_id = chat_id
        try:
            chat_info = await asyncio.wait_for(client.get_chat(chat_id), timeout=3.0)
            resolved_id = chat_info.id
            title = chat_info.title or title
            username = ("@" + chat_info.username) if getattr(chat_info, 'username', None) else username
        except Exception:
            # If get_chat failed, keep numeric ID if numeric
            if isinstance(chat_id, int):
                resolved_id = chat_id
                title = f"Channel {chat_id}"
            else:
                failed.append((token, "Bot is not admin or peer invalid"))
                continue

        # Check if already added
        if await db.in_channel(user_id, resolved_id):
            already_exists.append((resolved_id, title))
            continue

        res = await db.add_channel(user_id, resolved_id, title, username)
        if res:
            added.append((resolved_id, title))
            cur_count += 1
        else:
            already_exists.append((resolved_id, title))

    # Build output summary
    lines = ['<emoji id="5882207227997066107">📢</emoji> <b>Channel Add Results:</b>\n']
    if added:
        lines.append(f'<b>✅ Added ({len(added)}):</b>')
        for cid, ttl in added:
            lines.append(f'• <b>{ttl}</b> (<code>{cid}</code>)')
        lines.append('')
    if already_exists:
        lines.append(f'<b>⚠️ Already Existed ({len(already_exists)}):</b>')
        for cid, ttl in already_exists:
            lines.append(f'• <b>{ttl}</b> (<code>{cid}</code>)')
        lines.append('')
    if failed:
        lines.append(f'<b>❌ Failed ({len(failed)}):</b>')
        for tok, rsn in failed:
            lines.append(f'• <code>{tok}</code>: <i>{rsn}</i>')
        lines.append('')

    lines.append(f'<b>Total Saved Channels:</b> <code>{cur_count}/250</code>')
    res_text = "\n".join(lines).strip()
    try:
        await progress_msg.edit_text(res_text)
    except Exception:
        await message.reply_text(res_text)


@Client.on_message(filters.command(["delchannel", "delchannels", "remchannel", "rmchannel", "removechannel", "delchat"]) & filters.private)
async def cmd_del_channel(client, message):
    """Remove one or multiple channels by numerical ID."""
    user_id = message.from_user.id
    raw_args = message.text.split(None, 1)
    if len(raw_args) < 2:
        return await message.reply_text(
            '<emoji id="5774077015388852135">🗑</emoji> <b>Delete / Remove Channel(s)</b>\n\n'
            "<b>Usage:</b> <code>/delchannel &lt;chat_id_1&gt; [chat_id_2] ...</code>\n\n"
            "<b>Examples:</b>\n"
            "• Single: <code>/delchannel -1001234567890</code>\n"
            "• Multiple: <code>/delchannel -1001234567890 -1009876543210</code>\n\n"
            "<i>Tip: You can pass multiple IDs separated by spaces, commas, or newlines.</i>"
        )

    import re
    # Extract IDs / numbers
    tokens = re.findall(r'-?\d{5,16}', raw_args[1])
    if not tokens:
        tokens = [t.strip(' ,;') for t in raw_args[1].split() if t.strip(' ,;')]

    if not tokens:
        return await message.reply_text("❌ No valid channel IDs found in your command.")

    deleted = []
    not_found = []
    invalid = []

    progress_msg = await message.reply_text(f"⏳ Removing {len(tokens)} channel(s)...")

    for token in tokens:
        cid_int = None
        if token.lstrip('-').isdigit():
            cid_int = int(token)
        else:
            invalid.append(token)
            continue

        ex_ch = await db.get_channel_details(user_id, cid_int)
        ch_title = ex_ch.get('title', f"Channel {cid_int}") if ex_ch else f"{cid_int}"

        res = await db.remove_channel(user_id, cid_int)
        if res and getattr(res, 'deleted_count', 0) > 0:
            deleted.append((cid_int, ch_title))
        else:
            not_found.append((cid_int, ch_title))

    remaining = await db.get_user_channels(user_id)

    lines = ['<emoji id="5774077015388852135">🗑</emoji> <b>Channel Removal Results:</b>\n']
    if deleted:
        lines.append(f'<b>✅ Removed ({len(deleted)}):</b>')
        for cid, ttl in deleted:
            lines.append(f'• <b>{ttl}</b> (<code>{cid}</code>)')
        lines.append('')
    if not_found:
        lines.append(f'<b>⚠️ Not Found in Your List ({len(not_found)}):</b>')
        for cid, ttl in not_found:
            lines.append(f'• <code>{cid}</code>')
        lines.append('')
    if invalid:
        lines.append(f'<b>❌ Invalid Format ({len(invalid)}):</b>')
        for inv in invalid:
            lines.append(f'• <code>{inv}</code>')
        lines.append('')

    lines.append(f'<b>Remaining Channels:</b> <code>{len(remaining)}/250</code>')
    res_text = "\n".join(lines).strip()
    try:
        await progress_msg.edit_text(res_text)
    except Exception:
        await message.reply_text(res_text)




