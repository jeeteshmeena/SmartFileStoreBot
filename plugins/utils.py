import time as tm
from database import db 
from .test import parse_buttons

STATUS = {}

class STS:
    def __init__(self, id):
        self.id = id
        self.data = STATUS
    
    def verify(self):
        return self.data.get(self.id)
    
    def store(self, From, to, skip, limit, continuous=False, reverse_order=False, bot_id=None, smart_order=True, from_thread=None, direct_forward=False):
        self.data[self.id] = {"FROM": From, 'TO': to, 'total_files': 0, 'skip': skip, 'limit': limit,
                      'fetched': skip, 'filtered': 0, 'deleted': 0, 'duplicate': 0, 'total': limit,
                      'start': 0, 'continuous': continuous, 'reverse_order': reverse_order, 'bot_id': bot_id,
                      'smart_order': smart_order, 'from_thread': from_thread, 'direct_forward': direct_forward}
        self.get(full=True)
        return STS(self.id)
        
    def get(self, value=None, full=False):
        values = self.data.get(self.id)
        if not full:
           return values.get(value)
        for k, v in values.items():
            setattr(self, k, v)
        return self

    def add(self, key=None, value=1, time=False, forward_type='normal'):
        if time:
          return self.data[self.id].update({'start': tm.time()})
        self.data[self.id].update({key: self.get(key) + value}) 
        if key == 'total_files':
            import asyncio
            stat_key = f"{forward_type}_forward"
            asyncio.create_task(db.update_global_stats(**{stat_key: value}))
    
    def divide(self, no, by):
       by = 1 if int(by) == 0 else by 
       return int(no) / by 
    
    async def get_data(self, user_id):
        k, filters = self, await db.get_filters(user_id)
        size, configs = None, await db.get_configs(user_id)
        
        # New explicit selection feature: Use the bot_id selected via the UI, else fallback to active
        explicit_bot_id = getattr(k, 'bot_id', None)
        bots = await db.get_bots(user_id)
        bot = None
        
        if explicit_bot_id:
            # Look up the exact account chosen by the user in the UI
            chosen = await db.get_bot(user_id, explicit_bot_id)
            if chosen:
                bot = chosen
                    
        # Fallback to active bot if explicit fails or isn't provided
        if not bot:
            for b in bots:
                if b.get('active'): bot = b
            if bot is None and bots: bot = bots[0]

        if configs['duplicate']:
           duplicate = [configs['db_uri'], self.TO]
        else:
           duplicate = False
        button = parse_buttons(configs['button'] if configs['button'] else '')
        if configs['file_size'] != 0:
            size = [configs['file_size'], configs['size_limit']]
        
        return bot, configs['caption'], configs['forward_tag'], {
            'download': configs.get('download', False), 'chat_id': k.FROM, 'limit': k.limit, 'offset': k.skip, 
            'filters': filters,                                   # list of disabled type names  
            'configs_filters': configs.get('filters', {}),        # full dict: rm_caption, links, etc.
            'rm_caption': configs.get('filters', {}).get('rm_caption', False),
            'keywords': configs['keywords'], 'media_size': size, 'extensions': configs['extension'], 
            'skip_duplicate': duplicate, 'duration': configs.get('duration', 1), 
            'reverse_order': getattr(k, 'reverse_order', False), 'smart_order': getattr(k, 'smart_order', True),
            'from_thread': getattr(k, 'from_thread', None), 'direct_forward': getattr(k, 'direct_forward', False),
            'replacements': configs.get('replacements', {})
        }, configs['protect'], button

def format_tg_error(e, context="Scan Error"):
    err_str = str(e)
    if "CHANNEL_PRIVATE" in err_str or "USER_BANNED" in err_str or "accessible" in err_str.lower():
        return f"<b>‣ {context}: Access Denied</b>\n<i>The Clone Client or Bot cannot access the channel. Please ensure it is added as an Admin with correct permissions.</i>\n\n<code>{err_str}</code>"
    if "CHAT_ADMIN_REQUIRED" in err_str:
        return f"<b>‣ {context}: Admin Required</b>\n<i>The bot requires Admin privileges to perform this action.</i>\n\n<code>{err_str}</code>"
    if "FLOOD_WAIT" in err_str or "420" in err_str:
        return f"<b>‣ {context}: Telegram API Rate Limit</b>\n<i>Too many requests. Please wait a few minutes before trying again.</i>\n\n<code>{err_str}</code>"
    return f"<b>‣ {context}:</b>\n<code>{err_str}</code>"


async def check_chat_protection(user_id: int, chat_id) -> str | None:
    """
    Checks if the source chat_id is protected from the given user_id.
    Returns an error message HTML string if blocked, else None.

    Enforcement rules:
    1. Owners/co-owners always bypass all checks.
    2. If the BOT itself (numeric ID from BOT_TOKEN, or its username) is in the
       protected_chats list → ALL non-owner forwarding is blocked globally.
    3. If the source chat_id is in the protected_chats list → blocked.
    4. If the source chat is registered to an owner/co-owner → blocked.
    """
    if not chat_id:
        return None

    try:
        chat_id_int = int(chat_id)
    except (ValueError, TypeError):
        chat_id_int = str(chat_id)

    from config import Config

    user_id_int = int(user_id)
    is_owner = (user_id_int in Config.BOT_OWNER_ID)
    is_co_owner = await db.is_co_owner(user_id_int)

    if is_owner or is_co_owner:
        return None

    # ── Global Bot Lock: bot ID or username in the protection list ────────────
    # If the owner adds the bot's own ID/username to the protected list,
    # it acts as a global forwarding lock — no non-owner can run any job.
    try:
        global _cached_bot_username
        if '_cached_bot_username' not in globals():
            _cached_bot_username = None
            
        bot_numeric_id = int(Config.BOT_TOKEN.split(":")[0])
        
        # Check by numeric ID
        bot_global_lock = await db.is_chat_protected(bot_numeric_id)
        
        # Check by username dynamically via Telegram API if not cached
        if not bot_global_lock:
            if not _cached_bot_username:
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as sess:
                        async with sess.get(f"https://api.telegram.org/bot{Config.BOT_TOKEN}/getMe", timeout=5) as res:
                            data = await res.json()
                            if data.get("ok"):
                                _cached_bot_username = str(data["result"]["username"]).lower()
                except Exception:
                    pass
            
            if _cached_bot_username:
                bot_global_lock = await db.is_chat_protected(_cached_bot_username)

        if bot_global_lock:
            reason_txt = bot_global_lock.get('reason', '') or 'The bot owner has disabled forwarding.'
            return (
                f"🔒 <b>Forwarding Disabled</b>\n\n"
                f"The bot owner has temporarily disabled forwarding for all users.\n\n"
                f"<i>Reason: {reason_txt}</i>"
            )
    except Exception:
        pass  # Never block due to parsing errors

    # ── 1. Globally protected source chats ────────────────────────────────────
    prot = await db.is_chat_protected(chat_id_int)
    if prot:
        reason_txt = prot.get('reason', '') or 'Owner has protected this chat.'
        title_txt  = prot.get('title', str(chat_id_int))
        return (
            f"🔒 Protection Active: <b>{title_txt}</b>\n\n"
            f"This source chat is protected by the owner and cannot be used "
            f"as a forwarding source.\n\n"
            f"<i>Reason: {reason_txt}</i>"
        )

    # ── 2. Implicit protection: channels registered to Owner/Co-owners ────────
    owners = list(Config.BOT_OWNER_ID) + await db.get_co_owners()
    for oid in set(owners):
        if await db.in_channel(oid, chat_id_int):
            return (
                f"🔒 Protection Active\n\n"
                f"This source chat belongs to the bot's administrators. "
                f"You are not allowed to forward content from it."
            )

    return None



# ── Channel Search Picker (shared across all jobs/wizards) ────────────────────
async def ask_channel_picker(bot, user_id: int, prompt: str,
                             extra_options=None,
                             timeout: int = 300):
    """
    Smart channel picker: shows channels as buttons (max 8 at once).
    User can tap a button OR type part of a name to filter dynamically.
    No big numbered text-list is sent — keeps the UI clean.
    """
    import asyncio
    from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

    channels = await db.get_user_channels(user_id)
    if not channels:
        await bot.send_message(user_id,
            "<b>No channels added yet.</b>\nGo to /settings → Channels to add one.",
            reply_markup=ReplyKeyboardRemove())
        return None

    PAGE_SIZE = 8

    def _build_kb(ch_list):
        rows = []
        visible = ch_list[:PAGE_SIZE]
        for i in range(0, len(visible), 2):
            pair = visible[i:i+2]
            rows.append([KeyboardButton(c["title"]) for c in pair])

        cancel_btn = KeyboardButton("⛔ Cancel")
        undo_btn = None
        other_opts = []
        if extra_options:
            for o in extra_options:
                o_str = str(o)
                o_lower = o_str.lower()
                if "undo" in o_lower or "uɴᴅᴏ" in o_lower or "↩️" in o_str:
                    undo_btn = KeyboardButton(o)
                else:
                    other_opts.append(KeyboardButton(o))

        if other_opts:
            for i in range(0, len(other_opts), 2):
                rows.append(other_opts[i:i+2])

        if undo_btn:
            rows.append([undo_btn, cancel_btn])
        else:
            rows.append([cancel_btn])
        return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

    def _prompt_text(ch_list, is_filtered=False, query=""):
        total = len(channels)
        shown = min(len(ch_list), PAGE_SIZE)
        header = "<b>" + prompt + "</b>"
        if is_filtered:
            header += ("\n\n🔍 <i>Showing " + str(shown) +
                       " result(s) for \"<b>" + query + "</b>\"</i>")
        else:
            if total > PAGE_SIZE:
                header += ("\n\n<i>Showing " + str(shown) + " of " + str(total) +
                           " channels.\nType part of a name to filter.</i>")
            else:
                header += "\n\n<i>Tap a channel or type part of its name to search.</i>"
        return header

    current_list = channels
    is_filtered  = False
    query        = ""

    while True:
        try:
            msg = await bot.ask(
                user_id,
                _prompt_text(current_list, is_filtered, query),
                reply_markup=_build_kb(current_list),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            await bot.send_message(user_id, "<i>⏱ Selection timed out.</i>",
                                    reply_markup=ReplyKeyboardRemove())
            return None

        text = (msg.text or "").strip()

        # Cancel
        if not text or any(x in text.lower() for x in ["cancel", "/cancel"]) or "⛔" in text:
            await bot.send_message(user_id, "<i>Process Cancelled.</i>",
                                    reply_markup=ReplyKeyboardRemove())
            return None

        # Extra options (e.g. Undo, Skip)
        if extra_options:
            if text in extra_options:
                return text
            for opt in extra_options:
                opt_str = str(opt)
                if any(u in text.lower() for u in ['undo', 'uɴᴅᴏ', '↩️']) and any(u in opt_str.lower() for u in ['undo', 'uɴᴅᴏ', '↩️']):
                    return opt
                if text.lower() == opt_str.lower():
                    return opt

        # Exact button match (user tapped a channel button)
        exact = next((c for c in current_list if c["title"] == text), None)
        if exact:
            await bot.send_message(user_id, "✅ <b>" + exact["title"] + "</b> selected.",
                                    reply_markup=ReplyKeyboardRemove())
            return exact

        # Fuzzy search across ALL channels
        q = text.lower()
        fuzzy = [c for c in channels if q in c["title"].lower()]
        if len(fuzzy) == 1:
            await bot.send_message(user_id, "✅ <b>" + fuzzy[0]["title"] + "</b> selected.",
                                    reply_markup=ReplyKeyboardRemove())
            return fuzzy[0]
        if fuzzy:
            current_list = fuzzy
            is_filtered  = True
            query        = text
            continue

        # No match — reset
        await bot.send_message(user_id,
            '<i>No channel matched "<b>' + text + '</b>". Type part of the name again.</i>')
        current_list = channels
        is_filtered  = False
        query        = ""


async def safe_resolve_peer(client, chat_id, bot=None):
    try:
        if str(chat_id).lower() in ('me', 'saved'):
            chat_id = 'me'
        else:
            chat_id = int(chat_id) if str(chat_id).lstrip('-').isdigit() else chat_id
        try: await client.get_chat(chat_id)
        except: await client.get_users(chat_id)
        return True
    except Exception as e:
        err_str = str(e).upper()
        if 'PEER_ID_INVALID' in err_str or 'CHANNEL_INVALID' in err_str or 'PEER_ID_NOT_HANDLED' in err_str or 'USERNAME_NOT_OCCUPIED' in err_str:
            if bot and getattr(client, 'name', '') != getattr(bot, 'name', ''):
                try:
                    from pyrogram.raw.types import InputPeerChannel as _IPC
                    _tpeer = await bot.resolve_peer(chat_id)
                    if isinstance(_tpeer, _IPC):
                        await client.storage.update_peers([(_tpeer.channel_id, _tpeer.access_hash, 'channel', None, None)])
                        try: await client.get_chat(chat_id)
                        except: pass
                        return True
                except Exception:
                    pass
            try:
                me = await client.get_me()
                if not getattr(me, 'is_bot', False):
                    async for _ in client.get_dialogs(): pass
                try: await client.get_chat(chat_id)
                except: await client.get_users(chat_id)
                return True
            except Exception as e2:
                import logging
                logging.getLogger(__name__).warning(f'Failed to resolve {chat_id}: {e2}')
                return False
        return False


def extract_ep_label_robust(fname: str) -> dict:
    import re

    # ── 0. Normalize Devanagari (Hindi) digits → ASCII digits ────────────────
    # Maps ०१२३४५६७८९ (U+0966–U+096F) to 0123456789 so all patterns work
    # uniformly regardless of whether the filename uses Hindi or Latin numerals.
    _DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
    fname = fname.translate(_DEVANAGARI_DIGITS)

    # ── 1. Strip extension & metadata markers ────────────────────────────────
    # Split by ' @@@ ' separator to process title and filename parts separately.
    # This ensures that trailing duplicate/copy tags (e.g. " (1)" or " [2]") are properly
    # stripped using the "$" anchor of the regex, even if they are present in both
    # the title and the filename fields.
    parts = [p.strip() for p in fname.split('@@@')]
    clean_parts = []
    for p in parts:
        # Strip extensions
        base = re.sub(r'\.(?:mp3|mp4|m4a|m4b|ogg|opus|flac|wav|aac|wma|webm|mkv|avi|mov|dat|3gp|amr)(?=\s|$)', ' ', p, flags=re.IGNORECASE)
        base = re.sub(r'\.\w{2,5}$', '', base)  # also strip any remaining extension at end
        # Strip copy/duplicate indicators
        base = re.sub(r'(?i)\b(?:copy|duplicate|v\d+)\b', '', base)
        base = re.sub(r'(?i)\(\s*(?:copy|duplicate|\d+)\s*\)\s*$', '', base)
        base = re.sub(r'(?i)\[\s*(?:copy|duplicate|\d+)\s*\]\s*$', '', base)
        clean_parts.append(base.strip())
    b_norm = " @@@ ".join(clean_parts).strip()



    # ── 2. Normalize dash variants → plain hyphen ────────────────────────────
    dash_variants = r'[\-\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE63\uFF0D~～]+'
    b_norm = re.sub(dash_variants, '-', b_norm)

    # ── 3. Normalize "N _TO_ M" / "N to M" / "N से M" → "N-M" ──────────────
    # Handles: 480_TO_482 · 540 to 558 · Saaya_158_to_190 · 480 से 490
    # IMPORTANT: only collapse 'से' when it is between two digit sequences,
    # to avoid eating Hindi story/character names that contain 'से'.
    b_norm = re.sub(r'(?i)([\s_]+to[\s_]+)', '-', b_norm)          # handle 'to' broadly
    b_norm = re.sub(r'(\d+)[\s_]+से[\s_]+(\d+)', r'\1-\2', b_norm) # 'से' only between digits
    # Also handle underscore-separated numbers like 480_482 → 480-482
    b_norm = re.sub(r'(\d+)_+(\d+)', r'\1-\2', b_norm)

    # ── 4. Clean trailing lone `_digits` only if no range present ────────────
    if not re.search(r'\d+-\d+\s*$', b_norm):
        b_norm = re.sub(r'(?<![_\d])_\d+\s*$', '', b_norm)

    # Strip spaces around dashes for cleaner matching
    b_norm = re.sub(r'\s*-\s*', '-', b_norm)

    # Common audio bitrates — should NEVER be mistaken for episode numbers
    _BITRATES = {32, 64, 96, 128, 160, 192, 224, 256, 320, 512}

    num = r'\d{1,5}'

    def _format_res(label_found, nums):
        if not nums:
            return {"label": "", "numbers": [], "is_range": False}
        nums = sorted(set(int(n) for n in nums))
        if len(nums) == 1 or (len(nums) > 1 and nums[0] == nums[-1]):
            # Single number OR degenerate range like 536-536
            return {"label": str(nums[0]), "numbers": [nums[0]], "is_range": False}
        return {"label": f"{nums[0]}-{nums[-1]}", "numbers": nums, "is_range": True}

    # ── Priority 1: Keyword-tagged episodes (Ep, Episode, Part, #, eps…) ────
    # Must come FIRST because explicit keywords are absolutely more reliable than naked ranges.
    kw_delims = r'(?:\s*[\-\,\|\/\&\+\_]\s*)'
    kw_num_seq = f'(?:{num}(?:{kw_delims}{num})*)'
    kw_pattern = (
        r'(?i)\b(?:episode|epi|ep|e|part|#|एपिसोड|भाग|eps)(?:s)?'
        r'\s*[\-\:\.\\_\*\#]*\s*(' + kw_num_seq + r')(?![0-9])'
    )
    kw_m = re.search(kw_pattern, b_norm)
    if kw_m:
        label_raw = kw_m.group(1).strip()
        nums = [int(n) for n in re.findall(r'\d+', label_raw) if int(n) < 10000]
        if nums:
            return _format_res(label_raw, nums)

    # ── Priority 2: Greedy Range (N-M, N to M, N_TO_M, etc.) ────────────────
    # Prevent single-number fallback from stealing one end when no keyword is found.
    range_sep = r'(?:[\s\-_,\.\&\+]+|to)+'
    # Note: 'से' is NOT in range_sep here — it was already normalised above only when digit-bounded.
    greedy_range = re.search(
        r'(?<!\d)(' + num + r'(?:' + range_sep + num + r')+)(?!\d)',
        b_norm, re.IGNORECASE
    )
    if greedy_range:
        label_raw = greedy_range.group(1)
        nums = [int(n) for n in re.findall(r'\d+', label_raw) if int(n) < 10000]
        if len(nums) >= 1:  # even a single num after dedup is fine
            return _format_res(label_raw, nums)

    # ── Priority 3: Bracketed number group ([100-110], (100|101), {5&6}) ────
    br_delims = r'(?:\s*[\-\,\|\/\&\+\_]\s*)'
    br_num_seq = f'(?:{num}(?:{br_delims}{num})*)'
    br_pattern = r'[\[\(\<\{【『]\s*(' + br_num_seq + r')\s*[\]\)\>\}】』]'
    br_m = re.search(br_pattern, b_norm)
    if br_m:
        label_raw = br_m.group(1).strip().replace('_', '-')
        nums = [int(n) for n in re.findall(r'\d+', label_raw) if int(n) < 10000]
        return _format_res(label_raw, nums)

    # ── Priority 4: Pure number sequence (fallback multi-number) ────────────
    pure_delims = r'(?:\s*[\-\,\|\/\&\+\_]\s*)'
    pure_num_seq = f'(?:{num}(?:{pure_delims}{num})+)'
    r_m = re.search(r'(?<!\d)(' + pure_num_seq + r')(?!\d)', b_norm)
    if r_m:
        label_raw = r_m.group(1).strip()
        nums = [int(n) for n in re.findall(r'\d+', label_raw) if int(n) < 10000]
        return _format_res(label_raw, nums)

    # ── Priority 5: Leading zero-padded or plain number at start of name ────
    lead = re.match(r'^0*(\d{1,5})(?:[^0-9]|$)', b_norm)
    if lead:
        n_val = int(lead.group(1))
        return {"label": str(n_val), "numbers": [n_val], "is_range": False}

    # ── Priority 6: Any lone number not looking like a year or bitrate ───────
    # Strategy: prefer non-bitrate numbers; only fall back to bitrate-matching
    # numbers as last resort (e.g. episode 128 / 256 / 320 in a series).
    # This prevents genuine episode numbers like 32, 64, 128, 256, 320, 512
    # from being silently dropped when they are the only number in the filename.
    nums_all = re.findall(r'(?<!\d)(\d{1,5})(?!\d)', b_norm)
    # First pass: exclude years AND known audio bitrates (safe, avoids false positives)
    filtered = [
        n for n in nums_all
        if not (1900 <= int(n) <= 2100)   # exclude years
        and int(n) not in _BITRATES        # prefer non-bitrate numbers first
    ]
    if filtered:
        return {"label": filtered[0], "numbers": [int(filtered[0])], "is_range": False}
    # Last-resort fallback: if ALL numbers were bitrate-shaped, use the best
    # non-year one anyway — it is almost certainly the actual episode number.
    # (A real bitrate string like '128kbps' would have been noise-cleaned earlier.)
    fallback = [n for n in nums_all if not (1900 <= int(n) <= 2100)]
    if fallback:
        return {"label": fallback[0], "numbers": [int(fallback[0])], "is_range": False}

    return {"label": "", "numbers": [], "is_range": False}


def get_natural_sort_key(msg):
    import re
    media_obj = getattr(msg, msg.media.value if msg.media else '', None) if msg.media else None
    filename = getattr(media_obj, 'file_name', '') if media_obj else ''
    caption = msg.caption or getattr(msg.text, 'html', str(msg.text)) if msg.text else ''
    
    # 1. Lowercase and clean extensions and duplicate/copy markers (e.g. "(1)", "[2]")
    def clean_txt(txt):
        if not txt:
            return ""
        s = str(txt).lower()
        s = re.sub(r'\.(?:mp3|mp4|m4a|m4b|ogg|opus|flac|wav|aac|wma|webm|mkv|avi|mov|dat|3gp|amr)(?=\s|@|$)', ' ', s)
        s = re.sub(r'\.\w{2,5}$', '', s)
        s = re.sub(r'\(\d+\)', ' ', s)
        s = re.sub(r'\[\d+\]', ' ', s)
        return s.strip()

    f_clean = clean_txt(filename)
    c_clean = clean_txt(caption)
    
    # Prioritize filename over caption for the sorting template
    target = f_clean if f_clean else c_clean
    
    # Translate Devanagari digits
    _DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
    target = target.translate(_DEVANAGARI_DIGITS)
    
    # Clean common noisy keywords to avoid incorrect matches
    target = re.sub(r'(?i)\b(?:copy|duplicate|v\d+|number|no|num|vol|volume|v)\b\.?', ' ', target)
    
    # Heuristic 1: Explicit markers (Ep, Episode, Part, Ch, Chapter, etc.)
    kw_pattern = r'(?i)\b(?:episode|epi|ep|e|part|ch|chapter|#|eps|एपिसोड|भाग)\s*[-_:#\s]*\s*0*(\d+)'
    m1 = re.search(kw_pattern, target)
    if m1:
        return (0, int(m1.group(1)), msg.id)
        
    # Heuristic 2: Starts with a number (e.g. "103", "1301_MVS")
    m2 = re.match(r'^\s*0*(\d+)', target)
    if m2:
        return (0, int(m2.group(1)), msg.id)
        
    # Heuristic 3: Isolated numerics
    nums = re.findall(r'(?<!\d)0*(\d+)(?!\d)', target)
    if nums:
        # Avoid year-like numbers or large sizes unless that's all we have
        filtered = [int(n) for n in nums if not (1900 <= int(n) <= 2100) and int(n) < 10000]
        if filtered:
            return (0, filtered[-1], msg.id)
        return (0, int(nums[-1]), msg.id)
        
    # Fallback: keep original database order (msg.id)
    return (1, msg.id, msg.id)


async def get_fresh_message(client, chat_id, message_id: int):
    """Safely re-fetches a message from Telegram with a brand-new, valid file_reference.
    Handles DMs/bots (via get_chat_history offset) and channels (via get_messages)."""
    if not client or not chat_id or not message_id:
        return None
    try:
        # Check if chat is a user/bot DM (positive integer)
        if isinstance(chat_id, int) and chat_id > 0:
            async for m in client.get_chat_history(chat_id, limit=3, offset_id=message_id + 1):
                if m and m.id == message_id:
                    return m
            # Fallback direct get_messages for DM
            m = await client.get_messages(chat_id, message_id)
            if m and not m.empty and getattr(m, 'chat', None) and m.chat.id == chat_id:
                return m
        else:
            m = await client.get_messages(chat_id, message_id)
            if m and not m.empty:
                return m
    except Exception as e:
        import logging
        logging.getLogger(__name__).debug(f"get_fresh_message error for {chat_id}:{message_id} - {e}")
    return None


def _is_audio_msg(msg) -> bool:
    if getattr(msg, 'audio', None):
        return True
    doc = getattr(msg, 'document', None)
    if doc:
        fn = (getattr(doc, 'file_name', '') or '').lower()
        mime = (getattr(doc, 'mime_type', '') or '').lower()
        if mime.startswith('audio/') or fn.endswith(('.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg', '.opus', '.wma')):
            return True
    return False

def _is_video_msg(msg) -> bool:
    if getattr(msg, 'video', None) or getattr(msg, 'video_note', None):
        return True
    doc = getattr(msg, 'document', None)
    if doc:
        fn = (getattr(doc, 'file_name', '') or '').lower()
        mime = (getattr(doc, 'mime_type', '') or '').lower()
        if mime.startswith('video/') or fn.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.3gp', '.m4v')):
            return True
    return False

def _is_photo_msg(msg) -> bool:
    if getattr(msg, 'photo', None):
        return True
    doc = getattr(msg, 'document', None)
    if doc:
        fn = (getattr(doc, 'file_name', '') or '').lower()
        mime = (getattr(doc, 'mime_type', '') or '').lower()
        if mime.startswith('image/') or fn.endswith(('.jpg', '.jpeg', '.png', '.webp', '.heic', '.bmp')):
            return True
    return False

def _passes_filters(msg, disabled_types: list) -> bool:
    """Return True if message passes the user's content-type filters."""
    if not msg or getattr(msg, 'empty', False) or getattr(msg, 'service', False):
        return False

    if not disabled_types:
        return True

    # 1. Pure text message check
    is_text = bool(getattr(msg, 'text', None) and (not getattr(msg, 'media', None) or getattr(getattr(msg, 'media', None), 'value', str(getattr(msg, 'media', None))) == 'web_page'))
    if 'text' in disabled_types and is_text:
        return False

    # 2. Audio check (audio tag OR audio document)
    if _is_audio_msg(msg):
        if 'audio' in disabled_types:
            return False
        return True

    # 3. Video check (video tag OR video document)
    if _is_video_msg(msg):
        if 'video' in disabled_types:
            return False
        return True

    # 4. Photo check (photo tag OR photo document)
    if _is_photo_msg(msg):
        if 'photo' in disabled_types:
            return False
        return True

    # 5. Voice
    if 'voice' in disabled_types and getattr(msg, 'voice', None):
        return False

    # 6. Animation
    if 'animation' in disabled_types and getattr(msg, 'animation', None):
        return False

    # 7. Sticker
    if 'sticker' in disabled_types and getattr(msg, 'sticker', None):
        return False

    # 8. Poll
    if 'poll' in disabled_types and getattr(msg, 'poll', None):
        return False

    # 9. Generic Document (non-audio, non-video, non-photo document)
    if 'document' in disabled_types and getattr(msg, 'document', None):
        return False

    return True


def _clean_video_caption(raw_text: str) -> str:
    """
    Cleans video caption:
    - Extracts ONLY the title line.
    - Removes leading emojis and promotional footers.
    """
    if not raw_text:
        return ""

    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    if not lines:
        return ""

    promo_triggers = [
        "important notice", "notice", "auto-deleted", "auto deleted", "deleted in",
        "forward or save", "save it before", "powered by", "story tv", "watch now",
        "for free", "join channel", "click here", "subscribe", "t.me/", "http://", "https://", "@"
    ]

    title_line = ""
    for line in lines:
        l_str = line.strip()
        if not l_str:
            continue
        # Divider line
        if all(c in '━─═-—_~*• ' for c in l_str) and len(l_str) >= 3:
            continue
        l_lower = l_str.lower()
        if any(trig in l_lower for trig in promo_triggers):
            continue
        if any(w in l_str for w in ["𝗪𝗮𝘁𝗰𝗵", "𝗙𝗿𝗲𝗲", "𝗣𝗼𝘄𝗲𝗿𝗲𝗱", "𝗦𝘁𝗼𝗿𝘆", "𝗕𝗼𝘁", "𝗡𝗼𝘁𝗶𝗰𝗲", "𝗜𝗺𝗽𝗼𝗿𝘁𝗮𝗻𝘁", "𝗗𝗲𝗹𝗲𝘁𝗲𝗱"]):
            continue
        title_line = l_str
        break

    if not title_line and lines:
        title_line = lines[0]

    strip_emojis = ["🎬", "🎥", "📺", "🍿", "📹", "🔹", "🔸", "▫️", "▪️", "▶️", "👉", "✨", "🔥"]
    for emo in strip_emojis:
        if title_line.startswith(emo):
            title_line = title_line[len(emo):].strip()

    return title_line.strip()


def process_poster_image(input_path: str, target_size: tuple[int, int] = (600, 720)) -> str:
    """
    Resizes and naturally enhances poster images to exactly 600x720.
    """
    import logging
    _logger = logging.getLogger(__name__)
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        with Image.open(input_path) as img:
            if img.mode in ("RGBA", "LA", "P"):
                rgb_img = Image.new("RGB", img.size, (18, 18, 20))
                if img.mode == "RGBA":
                    rgb_img.paste(img, mask=img.split()[3])
                else:
                    rgb_img.paste(img.convert("RGB"))
                img = rgb_img
            elif img.mode != "RGB":
                img = img.convert("RGB")

            target_w, target_h = target_size
            orig_w, orig_h = img.size

            scale = min(target_w / orig_w, target_h / orig_h)
            new_w = max(1, int(orig_w * scale))
            new_h = max(1, int(orig_h * scale))

            resized_content = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            if (new_w, new_h) != (target_w, target_h):
                canvas = Image.new("RGB", (target_w, target_h), (16, 16, 18))
                try:
                    bg_img = img.resize((target_w, target_h), Image.Resampling.BILINEAR)
                    bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=20))
                    bg_img = ImageEnhance.Brightness(bg_img).enhance(0.40)
                    canvas.paste(bg_img, (0, 0))
                except Exception:
                    pass

                pos_x = (target_w - new_w) // 2
                pos_y = (target_h - new_h) // 2
                canvas.paste(resized_content, (pos_x, pos_y))
                final_img = canvas
            else:
                final_img = resized_content

            final_img = ImageEnhance.Sharpness(final_img).enhance(1.15)
            final_img = ImageEnhance.Contrast(final_img).enhance(1.04)
            final_img = ImageEnhance.Color(final_img).enhance(1.05)

            final_img.save(input_path, format="JPEG", quality=95, optimize=True, subsampling=0)
            return input_path
    except Exception as e:
        _logger.warning(f"Poster enhance error: {e}")
        return input_path

