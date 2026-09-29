import os
import time
os.environ['TZ'] = 'Asia/Kolkata'
if hasattr(time, 'tzset'):
    time.tzset()

import asyncio
import logging 
import logging.config
from database import db 
from config import Config  
import re
from pyrogram import Client, enums, __version__
from pyrogram.raw.all import layer 
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait 
from pyrogram.types import InlineKeyboardButton, KeyboardButton

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

import concurrent.futures

_SMALLCAPS_MAP = str.maketrans(
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ",
    "abcdefghijklmnopqrstuvwxyz"
)

def _norm_btn_text(text: str) -> str:
    return str(text or "").translate(_SMALLCAPS_MAP).strip()

def _is_back_button(text: str, callback_data: str = "") -> bool:
    raw_text = str(text or "").strip()
    norm_text = _norm_btn_text(raw_text).lower()
    raw_cb = str(callback_data or "").strip()
    if (
        re.search(r'(?:^|\b|[←«»›‹❮◀⬅🔙\u25c0\u2b05\u2190-\u2199])(?:back|वापस)(?:\b|$)', norm_text, re.IGNORECASE)
        or "back to" in norm_text
        or "वापस" in raw_text
        or (raw_cb in ("sbd#back", "pass#unlock_menu", "sbd#home", "store_browse", "back", "Merge_Back", "cl_back") and any(k in norm_text or k in raw_text for k in ("back", "होम", "वापस", "home", "menu", "details")))
        or (raw_cb.endswith(("_back", "#back")) and any(k in norm_text or k in raw_text for k in ("back", "वापस")))
    ):
        return True
    return False

def _format_back_text(text: str) -> str:
    raw_text = str(text or "").strip()
    cleaned = re.sub(r'^(?:[←«»›‹❮◀⬅🔙\u25c0\u2b05\u2190-\u2199]|\ufe0e|\ufe0f|\s)+', '', raw_text).strip()
    norm_cleaned = _norm_btn_text(cleaned)
    if norm_cleaned.lower() in ("back", ""):
        return "← Back"
    if re.match(r'^back\b', norm_cleaned, re.IGNORECASE):
        norm_cleaned = "Back" + norm_cleaned[4:]
        return f"← {norm_cleaned}"
    return f"← {cleaned}"

def _coerce_style_enum(style_val):
    if style_val is None:
        return None
    bs = getattr(enums, "ButtonStyle", None)
    if bs is not None and isinstance(style_val, bs):
        if style_val == getattr(bs, "DEFAULT", None):
            return None
        return style_val
    s = str(getattr(style_val, "value", style_val) or "").lower().strip()
    if "primary" in s:
        return getattr(bs, "PRIMARY", "primary") if bs else "primary"
    if "danger" in s:
        return getattr(bs, "DANGER", "danger") if bs else "danger"
    if "success" in s:
        return getattr(bs, "SUCCESS", "success") if bs else "success"
    return None

def _infer_style_name(text: str, callback_data: str = "") -> str:
    if _is_back_button(text, callback_data):
        return "danger"
    norm = _norm_btn_text(text).lower()
    cb = str(callback_data or "").lower().strip()

    if (
        re.search(r'(?::\s*off\b|-\s*off\b|\[off\]|\(off\)|\boff\b\s*$)', norm)
        or any(k in norm for k in (
            "cancel", "stop", "delete", "remove", "clear", "wipe", "reset",
            "abort", "close", "disable", "turn off", "pause", "ban", "revoke",
            "reject", "cleanup", "no, keep", "no, ", "discard", "exit", "undo",
            "force stop", "रद्द", "कैंसिल", "वापस", "❌", "🗑", "🛑", "✗", "↩️"
        ))
        or any(k in cb for k in (
            "cancel", "delete", "del_", "_del", "remove", "rem_", "clear",
            "stop", "close", "reset", "wipe", "abort", "ban_", "#back", "_back"
        ))
    ):
        return "danger"

    if (
        re.search(r'(?::\s*on\b|-\s*on\b|\[on\]|\(on\)|\bon\b\s*$)', norm)
        or any(k in norm for k in (
            "create", "start", "+ ", "➕", "add ", "new ", "resume", "launch",
            "run ", "confirm", "done", "save", "approve", "enable", "turn on",
            "yes", "finish", "complete", "proceed", "submit", "verify",
            "generate", "activate", "unban", "force post", "skip & resume",
            "keep both", "overwrite", "use default", "auto-detect",
            "all messages", "all pending", "all channels", "support via",
            "buy ", "unlock", "✅", "🟢", "🚀", "▶️"
        ))
        or norm in ("done", "yes", "start", "create", "save", "confirm", "resume", "enable", "on", "add")
        or any(k in cb for k in (
            "create", "start", "add", "new", "resume", "confirm", "done",
            "save", "approve", "enable", "unban", "launch", "run"
        ))
    ):
        return "success"

    return "primary"

def _infer_style_enum(text: str, callback_data: str = ""):
    return _coerce_style_enum(_infer_style_name(text, callback_data))

def apply_global_button_patches():
    if not getattr(InlineKeyboardButton, "_arya_style_patched", False):
        _orig_ikb_init = InlineKeyboardButton.__init__
        _orig_ikb_write = InlineKeyboardButton.write

        def _patched_ikb_init(self, text, *args, icon_custom_emoji_id=None, style=None, **kwargs):
            _orig_ikb_init(self, text, *args, **kwargs)
            self._api_icon_custom_emoji_id = icon_custom_emoji_id
            self.icon_custom_emoji_id = None
            cb = getattr(self, "callback_data", None)
            if _is_back_button(self.text, cb):
                self.text = _format_back_text(self.text)
                self.style = _coerce_style_enum("danger")
            else:
                coerced = _coerce_style_enum(style)
                if coerced is not None:
                    self.style = coerced
                elif cb is not None or getattr(self, "switch_inline_query", None) is not None or getattr(self, "switch_inline_query_current_chat", None) is not None:
                    self.style = _infer_style_enum(self.text, cb or "")

        async def _patched_ikb_write(self, client):
            cb = getattr(self, "callback_data", None)
            if _is_back_button(self.text, cb):
                self.text = _format_back_text(self.text)
                self.style = _coerce_style_enum("danger")
            else:
                coerced = _coerce_style_enum(getattr(self, "style", None))
                if coerced is not None:
                    self.style = coerced
                elif cb is not None or getattr(self, "switch_inline_query", None) is not None or getattr(self, "switch_inline_query_current_chat", None) is not None:
                    self.style = _infer_style_enum(self.text, cb or "")
            self.icon_custom_emoji_id = None
            return await _orig_ikb_write(self, client)

        InlineKeyboardButton.__init__ = _patched_ikb_init
        InlineKeyboardButton.write = _patched_ikb_write
        InlineKeyboardButton._arya_style_patched = True

    if not getattr(KeyboardButton, "_arya_style_patched", False):
        _orig_kb_init = KeyboardButton.__init__
        _orig_kb_write = KeyboardButton.write

        def _patched_kb_init(self, text, *args, icon_custom_emoji_id=None, style=None, **kwargs):
            _orig_kb_init(self, text, *args, **kwargs)
            self._api_icon_custom_emoji_id = icon_custom_emoji_id
            self.icon_custom_emoji_id = None
            coerced = _coerce_style_enum(style)
            self.style = coerced if coerced is not None else _infer_style_enum(self.text, "")

        def _patched_kb_write(self):
            coerced = _coerce_style_enum(getattr(self, "style", None))
            self.style = coerced if coerced is not None else _infer_style_enum(self.text, "")
            self.icon_custom_emoji_id = None
            return _orig_kb_write(self)

        KeyboardButton.__init__ = _patched_kb_init
        KeyboardButton.write = _patched_kb_write
        KeyboardButton._arya_style_patched = True

apply_global_button_patches()

BOT_INSTANCE = None

class Bot(Client): 
    def __init__(self):
        global BOT_INSTANCE
        BOT_INSTANCE = self
        
        try:
            loop = asyncio.get_running_loop()
            loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=100))
        except RuntimeError:
            pass
        super().__init__(
            Config.BOT_SESSION,
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            plugins={
                "root": "plugins"
            },
            workers=50,
            bot_token=Config.BOT_TOKEN,
            max_concurrent_transmissions=50
        )
        self.log = logging

    async def start(self):
        await super().start()
        me = await self.get_me()
        logging.info(f"{me.first_name} with for pyrogram v{__version__} (Layer {layer}) started on @{me.username}.")
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)
        text = "**๏[-ิ_•ิ]๏ bot restarted !**"
        logging.info(text)

        # ── Register main bot token in share_bot token cache ────────────────
        try:
            from plugins.share_bot import register_bot_token
            if Config.BOT_TOKEN:
                register_bot_token(str(self.id), Config.BOT_TOKEN)
                register_bot_token("main", Config.BOT_TOKEN)
            if hasattr(self, "bot_token") and self.bot_token:
                register_bot_token(str(self.id), self.bot_token)
                register_bot_token("main", self.bot_token)
            logging.info(f"[Startup] Registered main bot token for ID {self.id} (@{self.username})")
        except Exception as _t_err:
            logging.warning(f"[Startup] register_bot_token failed: {_t_err}")

        # ── Register this bot instance with arya_logger ──────────────────────
        # This must happen immediately after start() so all 6 log channels work.
        # Without this, arya_logger had no bot reference and all logs silently failed.
        try:
            from plugins.arya_logger import register_bot as _register_bot
            _register_bot(self)
        except Exception as _rbe:
            logging.warning(f"[Startup] arya_logger.register_bot failed: {_rbe}")

        # Ensure database indexes
        try:
            logging.info("[Startup] Ensuring database indexes...")
            await db.ensure_indexes()
            logging.info("[Startup] Database indexes verified.")
        except Exception as _eidx:
            logging.error(f"[Startup] Index creation failed: {_eidx}")


        # Check if database URI is default broken one
        if "mongodb+srv://chhjgjkkjhkjhkjh@cluster0.xowzpr4.mongodb.net/" in Config.DATABASE_URI:
             logging.error("You have not set the DATABASE environment variable. The bot will not function correctly.")
             return

        try:
            success = failed = 0
            users = await db.get_all_frwd()
            async for user in users:
               chat_id = user['user_id']
               try:
                  await self.send_message(chat_id, text)
                  success += 1
               except FloodWait as e:
                  await asyncio.sleep(e.value + 1)
                  await self.send_message(chat_id, text)
                  success += 1
               except Exception:
                  failed += 1

            if (success + failed) != 0:
               await db.rmve_frwd(all=True)
               logging.info(f"Restart message status"
                     f"success: {success}"
                     f"failed: {failed}")
        except Exception as e:
            logging.error(f"Failed to send restart messages or connect to DB: {e}")

    async def stop(self, *args):
        msg = f"@{self.username} stopped. Bye."
        await super().stop()
        logging.info(msg)
