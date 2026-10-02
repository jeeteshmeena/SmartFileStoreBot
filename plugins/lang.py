"""
Language Selection Plugin
=========================
Allows users to pick English / Hindi / Hinglish as their preferred language.
All key bot responses will be returned in the selected language.

Usage:
  /lang  — open language picker (also accessible from Settings)
  from .lang import t   — use t(user_id, key) in any plugin for translated text

Supported languages:
  en        — English  (default)
  hi        — Hindi (Devanagari)
  hinglish  — Hinglish (Hindi written in English)
"""
from database import db
from config import Config
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ══════════════════════════════════════════════════════════════════════════════
# Translation strings – ALL multi-line entries use triple-quoted strings
# ══════════════════════════════════════════════════════════════════════════════

_S = {}   # populated below; we use a plain dict for clarity

#  START_TXT 
_S["START_TXT"] = {
    "en": (
        "<b>Welcome <a href='tg://user?id={0}'>{1}</a>!</b>\n\n"
        "Send me any file to store it, or use the buttons below."
    ),
    "hi": (
        "<b>स्वागत है <a href='tg://user?id={0}'>{1}</a>!</b>\n\n"
        "कोई भी फ़ाइल स्टोर करने के लिए मुझे भेजें, या नीचे दिए गए बटनों का उपयोग करें।"
    ),
    "hinglish": (
        "<b>Welcome <a href='tg://user?id={0}'>{1}</a>!</b>\n\n"
        "Koi bhi file store karne ke liye yahan send karein, ya niche diye buttons use karein."
    ),
}

#  HELP_TXT 
_S["HELP_TXT"] = {
    "en": (
        "<b><u><emoji id='6037622221625626773'>🤖</emoji> ʜᴇʟᴘ — ꜱᴍᴀʀᴛ ꜰɪʟᴇ ꜱᴛᴏʀᴇ ʙᴏᴛ</u></b>\n\n"
        "<b>»  ᴄᴏᴍᴍᴀɴᴅꜱ:</b>\n"
        "<code>/start</code>  — ᴄʜᴇᴄᴋ ɪꜰ ɪ'ᴍ ᴀʟɪᴠᴇ &amp; ᴏᴘᴇɴ ᴍᴀɪɴ ᴍᴇɴᴜ\n"
        "<code>/settings</code>  — ᴄᴏɴꜰɪɢᴜʀᴇ ʙᴏᴛꜱ, ᴄʜᴀɴɴᴇʟꜱ &amp; ꜰɪʟᴛᴇʀꜱ\n"
        "<code>/stats</code>  — ᴠɪᴇᴡ ʙᴏᴛ ꜱᴛᴏʀᴀɢᴇ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ\n"
        "<code>/status</code>  — ᴄʜᴇᴄᴋ ꜱᴇʀᴠᴇʀ ᴘɪɴɢ, ꜱᴘᴇᴇᴅ &amp; ᴜᴘᴛɪᴍᴇ\n"
        "<code>/reset</code>  — ʀᴇꜱᴇᴛ ꜱᴇᴛᴛɪɴɢꜱ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ\n\n"
        "<b>»  ꜰᴇᴀᴛᴜʀᴇꜱ:</b>\n"
        "<b>➲ </b> <b>ꜱᴍᴀʀᴛ ꜰɪʟᴇ ꜱᴛᴏʀᴇ:</b> ᴘᴇʀᴍᴀɴᴇɴᴛ ꜱᴛᴏʀᴀɢᴇ ᴡɪᴛʜ ɪɴꜱᴛᴀɴᴛ ꜱʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋꜱ\n"
        "<b>➲ </b> <b>ʙᴀᴛᴄʜ ʟɪɴᴋꜱ:</b> ʙᴜɴᴅʟᴇ ᴍᴜʟᴛɪᴘʟᴇ ꜰɪʟᴇꜱ ɪɴᴛᴏ ᴀ ꜱɪɴɢʟᴇ ꜱᴇᴄᴜʀᴇ ʟɪɴᴋ\n"
        "<b>➲ </b> <b>ᴍᴜʟᴛɪ-ʙᴏᴛ ɴᴇᴛᴡᴏʀᴋ:</b> ᴄᴏɴɴᴇᴄᴛ ᴅᴇʟɪᴠᴇʀʏ ʙᴏᴛꜱ ᴛᴏ ʙʏᴘᴀꜱꜱ ꜰʟᴏᴏᴅ ᴡᴀɪᴛꜱ\n"
        "<b>➲ </b> <b>ꜱʜᴏʀᴛᴇɴᴇʀ ᴀᴘɪ:</b> ᴀʀᴏʟɪɴᴋꜱ &amp; ᴜʀʟꜱʜᴏʀᴛx ɪɴᴛᴇɢʀᴀᴛɪᴏɴ\n"
        "<b>➲ </b> <b>ꜰᴏʀᴄᴇ-ꜱᴜʙ ꜱʏꜱᴛᴇᴍ:</b> ᴍᴀɴᴅᴀᴛᴏʀʏ ᴄʜᴀɴɴᴇʟ ᴊᴏɪɴ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ\n"
        "<b>➲ </b> <b>ᴄᴏɴᴛᴇɴᴛ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ:</b> ᴘʀᴇᴠᴇɴᴛ ꜰᴏʀᴡᴀʀᴅɪɴɢ &amp; ᴄᴏᴘʏɪɴɢ ᴏꜰ ꜰɪʟᴇꜱ"
    ),
    "hi": (
        "<b><u><emoji id='6037622221625626773'>🤖</emoji> सहायता (HELP) — Smart File Store Bot</u></b>\n\n"
        "<b>»  Commands:</b>\n"
        "<code>/start</code>  — बोट शुरू करें और मुख्य मेनू देखें\n"
        "<code>/settings</code>  — बोट्स, चैनल्स और सेटिंग्स कॉन्फ़िगर करें\n"
        "<code>/stats</code>  — बोट के आंकड़े और स्टोरेज विवरण देखें\n"
        "<code>/status</code>  — सर्वर पिंग, स्पीड और अपटाइम चेक करें\n"
        "<code>/reset</code>  — सेटिंग्स को डिफ़ॉल्ट पर रीसेट करें\n\n"
        "<b>»  Features:</b>\n"
        "<b>➲ </b> <b>स्मार्ट फ़ाइल स्टोर:</b> फ़ाइलें स्थायी रूप से सेव करें और तुरंत लिंक पाएँ\n"
        "<b>➲ </b> <b>बैच लिंक्स:</b> अनेक फ़ाइलों का एक सिंगल शेयर करने योग्य लिंक बनाएँ\n"
        "<b>➲ </b> <b>मल्टी-बोट नेटवर्क:</b> डिलीवरी बोट्स कनेक्ट करें और स्पीड बढ़ाएँ\n"
        "<b>➲ </b> <b>शॉर्टनर एपीआई:</b> AroLinks और UrlShortX इंटीग्रेशन\n"
        "<b>➲ </b> <b>फ़ोर्स सब्सक्राइब:</b> चैनल जॉइन वेरिफिकेशन सिस्टम\n"
        "<b>➲ </b> <b>कंटेंट प्रोटेक्शन:</b> फ़ाइलों को फॉरवर्ड या कॉपी होने से सुरक्षित रखें"
    ),
    "hinglish": (
        "<b><u><emoji id='6037622221625626773'>🤖</emoji> HELP — Smart File Store Bot</u></b>\n\n"
        "<b>»  Commands:</b>\n"
        "<code>/start</code>  — Bot check karo aur main menu open karo\n"
        "<code>/settings</code>  — Bots, Channels aur Settings configure karo\n"
        "<code>/stats</code>  — Bot ke storage stats check karo\n"
        "<code>/status</code>  — Server speed aur uptime dekho\n"
        "<code>/reset</code>  — Settings ko default pe reset karo\n\n"
        "<b>»  Features:</b>\n"
        "<b>➲ </b> <b>Smart File Store:</b> Permanent file storage aur instant share links\n"
        "<b>➲ </b> <b>Batch Links:</b> Multiple files ka ek single shareable link banao\n"
        "<b>➲ </b> <b>Multi-Bot Delivery:</b> Connected bots se flood wait avoid karo\n"
        "<b>➲ </b> <b>Shortener APIs:</b> AroLinks aur UrlShortX support\n"
        "<b>➲ </b> <b>Force Sub:</b> Channel join verification support\n"
        "<b>➲ </b> <b>Content Protection:</b> Files forward hone se protect karo"
    ),
}

#  HOW_USE_TXT 
_S["HOW_USE_TXT"] = {
    "en": (
        "<b><u><emoji id='6037622221625626773'>🤖</emoji> ʜᴏᴡ ᴛᴏ ᴜꜱᴇ — ꜱᴍᴀʀᴛ ꜰɪʟᴇ ꜱᴛᴏʀᴇ ʙᴏᴛ</u></b>\n\n"
        "<b>1️⃣ ᴀᴅᴅ ᴀ ᴅᴇʟɪᴠᴇʀʏ ʙᴏᴛ</b>\n"
        "  ‣ ɢᴏ ᴛᴏ /ꜱᴇᴛᴛɪɴɢꜱ → <b>• ʙᴏᴛꜱ •</b>\n"
        "  ‣ ᴄʟɪᴄᴋ <b>➕ ᴀᴅᴅ ʙᴏᴛ</b> ᴀɴᴅ ꜱᴇɴᴅ ʏᴏᴜʀ ʙᴏᴛ ᴛᴏᴋᴇɴ ꜰʀᴏᴍ @BotFather\n"
        "  ‣ ʏᴏᴜ ᴄᴀɴ ᴀᴅᴅ ᴜᴘ ᴛᴏ 10 ʙᴏᴛꜱ ꜰᴏʀ ʜɪɢʜ-ꜱᴘᴇᴇᴅ ꜰɪʟᴇ ᴅᴇʟɪᴠᴇʀʏ\n\n"
        "<b>2️⃣ ᴀᴅᴅ ʏᴏᴜʀ ꜱᴛᴏʀᴀɢᴇ ᴄʜᴀɴɴᴇʟ</b>\n"
        "  ‣ ɢᴏ ᴛᴏ /ꜱᴇᴛᴛɪɴɢꜱ → <b>• ᴄʜᴀɴɴᴇʟꜱ •</b>\n"
        "  ‣ ᴍᴀᴋᴇ ꜱᴜʀᴇ ʏᴏᴜʀ ʙᴏᴛ ɪꜱ <b>ᴀᴅᴍɪɴ</b> ɪɴ ʏᴏᴜʀ ꜱᴛᴏʀᴀɢᴇ ᴄʜᴀɴɴᴇʟ\n\n"
        "<b>3️⃣ ꜱᴇᴛ ᴜᴘ ꜱʜᴏʀᴛᴇɴᴇʀꜱ (ᴏᴘᴛɪᴏɴᴀʟ)</b>\n"
        "  ‣ ɢᴏ ᴛᴏ /ꜱᴇᴛᴛɪɴɢꜱ → <b>• ꜱʜᴏʀᴛᴇɴᴇʀꜱ •</b>\n"
        "  ‣ ᴇɴᴛᴇʀ ʏᴏᴜʀ ᴀʀᴏʟɪɴᴋꜱ ᴏʀ ᴜʀʟꜱʜᴏʀᴛx ᴀᴘɪ ᴋᴇʏꜱ\n\n"
        "<b>4️⃣ ɢᴇɴᴇʀᴀᴛᴇ ʙᴀᴛᴄʜ ʟɪɴᴋꜱ</b>\n"
        "  ‣ ᴄʟɪᴄᴋ <b>• ʙᴀᴛᴄʜ ʟɪɴᴋꜱ •</b> ᴏɴ ᴛʜᴇ ᴍᴀɪɴ ᴍᴇɴᴜ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ ꜱɪɴɢʟᴇ ꜱʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ ꜰᴏʀ ᴍᴜʟᴛɪᴘʟᴇ ꜰɪʟᴇꜱ\n\n"
        "<b>5️⃣ ꜱᴛᴏʀᴇ ꜰɪʟᴇꜱ ɪɴꜱᴛᴀɴᴛʟʏ</b>\n"
        "  ‣ ꜱɪᴍᴘʟʏ ꜱᴇɴᴅ ᴀɴʏ ꜰɪʟᴇ/ᴍᴇᴅɪᴀ ᴅɪʀᴇᴄᴛʟʏ ᴛᴏ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ɢᴇᴛ ɪᴛꜱ ꜱʜᴀʀᴇᴀʙʟᴇ ꜱᴛᴏʀᴇ ʟɪɴᴋ"
    ),
    "hi": (
        "<b><u><emoji id='6037622221625626773'>🤖</emoji> इस्तमाल कैसे करें — Smart File Store Bot</u></b>\n\n"
        "<b>1️⃣ डिलीवरी बोट जोड़ें</b>\n"
        "  ‣ /settings पर जाएं → <b>• Bots •</b>\n"
        "  ‣ <b>➕ Add Bot</b> पर क्लिक करें और @BotFather से बोट टोकन भेजें\n"
        "  ‣ आप हाई-स्पीड फ़ाइल डिलीवरी के लिए 10 बोट्स तक जोड़ सकते हैं\n\n"
        "<b>2️⃣ स्टोरेज चैनल जोड़ें</b>\n"
        "  ‣ /settings पर जाएं → <b>• Channels •</b>\n"
        "  ‣ सुनिश्चित करें कि आपका बोट स्टोरेज चैनल में <b>एडमिन</b> है\n\n"
        "<b>3️⃣ शॉर्टनर सेट करें (वैकल्पिक)</b>\n"
        "  ‣ /settings → <b>• Shorteners •</b>\n"
        "  ‣ अपनी AroLinks या UrlShortX API कीज़ दर्ज करें\n\n"
        "<b>4️⃣ बैच लिंक्स बनाएँ</b>\n"
        "  ‣ मुख्य मेनू पर <b>• Batch Links •</b> बटन दबाकर कई फ़ाइलों का एक शेयर करने योग्य लिंक बनाएँ\n\n"
        "<b>5️⃣ फ़ाइलें तुरंत स्टोर करें</b>\n"
        "  ‣ कोई भी फ़ाइल सीधे बोट को भेजें और तुरंत शेयर लिंक पाएँ"
    ),
    "hinglish": (
        "<b><u><emoji id='6037622221625626773'>🤖</emoji> Kaise Use Karein — Smart File Store Bot</u></b>\n\n"
        "<b>1️⃣ Delivery Bot Add Karo</b>\n"
        "  ‣ /settings me jao → <b>• Bots •</b>\n"
        "  ‣ <b>➕ Add Bot</b> dabao aur @BotFather se Bot Token send karo\n"
        "  ‣ Maximum 10 bots add kar sakte ho fast file delivery ke liye\n\n"
        "<b>2️⃣ Storage Channel Add Karo</b>\n"
        "  ‣ /settings me jao → <b>• Channels •</b>\n"
        "  ‣ Channel me bot ka <b>Admin</b> hona zaruri hai\n\n"
        "<b>3️⃣ Shorteners Configure Karo</b>\n"
        "  ‣ /settings → <b>• Shorteners •</b>\n"
        "  ‣ AroLinks ya UrlShortX API key enter karo\n\n"
        "<b>4️⃣ Batch Links Banao</b>\n"
        "  ‣ Main menu pe <b>• Batch Links •</b> click karke multiple files ka single link banao\n\n"
        "<b>5️⃣ Files Store Karo</b>\n"
        "  ‣ Koi bhi file directly bot ko send karo aur instant share link pao"
    ),
}

#  ABOUT_TXT 
_S["ABOUT_TXT"] = {
    "en": (
        "<b><emoji id=\"6037622221625626773\">🤖</emoji> »  Bot Details \n"
        " \n"
        "  »  ᴍʏ ɴᴀᴍᴇ   : <a href='https://t.me/MeJeetX'>ᴀʀʏᴀ ʙᴏᴛ</a>\n"
        "  » ‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ : <a href='https://t.me/MeJeetX'>ᴍᴇᴊᴇᴇᴛx</a>\n"
        "  »  ᴄʜᴀɴɴᴇʟ   : <a href='https://t.me/MeJeetX'>ᴜᴘᴅᴀᴛᴇꜱ</a>\n"
        "  »  ꜱᴜᴘᴘᴏʀᴛ   : <a href='https://t.me/+1p2hcQ4ZaupjNjI1'>ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</a>\n"
        " \n"
        "  »  ᴠᴇʀꜱɪᴏɴ   : <code>{bot_version}</code> \n"
        "  »  ʟᴀɴɢᴜᴀɢᴇ  : ᴘʏᴛʜᴏɴ 3 \n"
        "  {python_version}\n"
        "  »  ʟɪʙʀᴀʀʏ   : ᴘʏʀᴏɢʀᴀᴍ  \n"
        "\n"
        "</b>"
    ),
    "hi": (
        "<b><emoji id=\"6037622221625626773\">🤖</emoji> »  Bot Details \n"
        " \n"
        "  »  मेरा नाम   : <a href='https://t.me/MeJeetX'>Aryᴀ Bᴏᴛ</a>\n"
        "  » ‍💻 डेवलपर   : <a href='https://t.me/MeJeetX'>MeJeetX</a>\n"
        "  »  चैनल      : <a href='https://t.me/MeJeetX'>Updates</a>\n"
        "  »  सपोर्ट     : <a href='https://t.me/+1p2hcQ4ZaupjNjI1'>Support Group</a>\n"
        " \n"
        "  »  वर्ज़न     : <code>{bot_version}</code> \n"
        "  »  भाषा      : ᴘʏᴛʜᴏɴ 3 \n"
        "  {python_version}\n"
        "  »  लाइब्रेरी   : ᴘʏʀᴏɢʀᴀᴍ  \n"
        "\n"
        "</b>"
    ),
    "hinglish": (
        "<b><emoji id=\"6037622221625626773\">🤖</emoji> »  Bot Details \n"
        " \n"
        "  »  Mera Naam : <a href='https://t.me/MeJeetX'>Aryᴀ Bᴏᴛ</a>\n"
        "  » ‍💻 Developer : <a href='https://t.me/MeJeetX'>MeJeetX</a>\n"
        "  »  Channel   : <a href='https://t.me/MeJeetX'>Updates</a>\n"
        "  »  Support   : <a href='https://t.me/+1p2hcQ4ZaupjNjI1'>Support Group</a>\n"
        " \n"
        "  »  Version   : <code>{bot_version}</code> \n"
        "  »  Language  : ᴘʏᴛʜᴏɴ 3 \n"
        "  {python_version}\n"
        "  »  Library   : ᴘʏʀᴏɢʀᴀᴍ  \n"
        "\n"
        "</b>"
    ),
}

#  STATUS_TXT 
_S["STATUS_TXT"] = {
    "en": (
        "<b>╔════❰ S ᴛ ᴀ ᴛ ᴜ ꜱ ❱═════❍⊱❁۪۪\n"
        "║ <u>Gᴇɴᴇʀᴀʟ Iɴғᴏ</u>\n"
        "║ ┣⪼ Uꜱᴇʀꜱ: <code>{users_count}</code>\n"
        "║ ┣⪼ Bᴏᴛꜱ: <code>{bots_count}</code>\n"
        "║ ┣⪼ Cʜᴀɴɴᴇʟꜱ: <code>{total_channels}</code>\n"
        "║ ┣⪼ Bᴀɴɴᴇᴅ: <code>{banned_users}</code> \n"
        "║\n"
        "║ <u>Sʏsᴛᴇᴍ Sᴛᴀᴛs</u>\n"
        "║ ┣⪼ Uᴘᴛɪᴍᴇ: <code>{uptime}</code>\n"
        "║ ┣⪼ DL Sᴘᴇᴇᴅ: <code>{dl_speed}</code>\n"
        "║ ┣⪼ UP Sᴘᴇᴇᴅ: <code>{ul_speed}</code>\n"
        "║\n"
        "║ <u>Dᴀᴛᴀ &ᴀᴍᴘ; Uꜱᴀɢᴇ</u>\n"
        "║ ┣⪼ Tᴏᴛᴀʟ Dᴏᴡɴʟᴏᴀᴅs: <code>{total_files_downloaded}</code>\n"
        "║ ┣⪼ Tᴏᴛᴀʟ Uᴘʟᴏᴀᴅs: <code>{total_files_uploaded}</code>\n"
        "║ ┗⪼ Tᴏᴛᴀʟ Dᴀᴛᴀ Uꜱᴇᴅ: <code>{total_data_usage_bytes}</code>\n"
        "╚═════❰ A R Y A ❱══════❍⊱❁۪۪</b>"
    ),
    "hi": (
        "<b>╔════❰ S ᴛ ᴀ ᴛ ᴜ ꜱ ❱═════❍⊱❁۪۪\n"
        "║ <u>Gᴇɴᴇʀᴀʟ Iɴғᴏ</u>\n"
        "║ ┣⪼ Uꜱᴇʀꜱ: <code>{users_count}</code>\n"
        "║ ┣⪼ Bᴏᴛꜱ: <code>{bots_count}</code>\n"
        "║ ┣⪼ Cʜᴀɴɴᴇʟꜱ: <code>{total_channels}</code>\n"
        "║ ┣⪼ Bᴀɴɴᴇᴅ: <code>{banned_users}</code> \n"
        "║\n"
        "║ <u>Sʏsᴛᴇᴍ Sᴛᴀᴛs</u>\n"
        "║ ┣⪼ Uᴘᴛɪᴍᴇ: <code>{uptime}</code>\n"
        "║ ┣⪼ DL Sᴘᴇᴇᴅ: <code>{dl_speed}</code>\n"
        "║ ┣⪼ UP Sᴘᴇᴇᴅ: <code>{ul_speed}</code>\n"
        "║\n"
        "║ <u>Dᴀᴛᴀ &ᴀᴍᴘ; Uꜱᴀɢᴇ</u>\n"
        "║ ┣⪼ Tᴏᴛᴀʟ Dᴏᴡɴʟᴏᴀᴅs: <code>{total_files_downloaded}</code>\n"
        "║ ┣⪼ Tᴏᴛᴀʟ Uᴘʟᴏᴀᴅs: <code>{total_files_uploaded}</code>\n"
        "║ ┗⪼ Tᴏᴛᴀʟ Dᴀᴛᴀ Uꜱᴇᴅ: <code>{total_data_usage_bytes}</code>\n"
        "╚═════❰ A R Y A ❱══════❍⊱❁۪۪</b>"
    ),
    "hinglish": (
        "<b>╔════❰ S ᴛ ᴀ ᴛ ᴜ ꜱ ❱═════❍⊱❁۪۪\n"
        "║ <u>Gᴇɴᴇʀᴀʟ Iɴғᴏ</u>\n"
        "║ ┣⪼ Uꜱᴇʀꜱ: <code>{users_count}</code>\n"
        "║ ┣⪼ Bᴏᴛꜱ: <code>{bots_count}</code>\n"
        "║ ┣⪼ Cʜᴀɴɴᴇʟꜱ: <code>{total_channels}</code>\n"
        "║ ┣⪼ Bᴀɴɴᴇᴅ: <code>{banned_users}</code> \n"
        "║\n"
        "║ <u>Sʏsᴛᴇᴍ Sᴛᴀᴛs</u>\n"
        "║ ┣⪼ Uᴘᴛɪᴍᴇ: <code>{uptime}</code>\n"
        "║ ┣⪼ DL Sᴘᴇᴇᴅ: <code>{dl_speed}</code>\n"
        "║ ┣⪼ UP Sᴘᴇᴇᴅ: <code>{ul_speed}</code>\n"
        "║\n"
        "║ <u>Dᴀᴛᴀ &ᴀᴍᴘ; Uꜱᴀɢᴇ</u>\n"
        "║ ┣⪼ Tᴏᴛᴀʟ Dᴏᴡɴʟᴏᴀᴅs: <code>{total_files_downloaded}</code>\n"
        "║ ┣⪼ Tᴏᴛᴀʟ Uᴘʟᴏᴀᴅs: <code>{total_files_uploaded}</code>\n"
        "║ ┗⪼ Tᴏᴛᴀʟ Dᴀᴛᴀ Uꜱᴇᴅ: <code>{total_data_usage_bytes}</code>\n"
        "╚═════❰ A R Y A ❱══════❍⊱❁۪۪</b>"
    ),
}

#  FROM_MSG 
_S["FROM_MSG"] = {
    "en": (
        "<b>❪ ꜱᴇᴛ ꜱᴏᴜʀᴄᴇ ᴄʜᴀᴛ ❫\n\n"
        "ꜰᴏʀᴡᴀʀᴅ ᴛʜᴇ ʟᴀꜱᴛ ᴍᴇꜱꜱᴀɢᴇ ᴏʀ ʟɪɴᴋ.\n"
        "ᴛʏᴘᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ (ᴇ.ɢ. <code>@ꜱᴏᴍᴇʙᴏᴛ</code> ᴏʀ <code>123456</code>) ꜰᴏʀ ʙᴏᴛ/ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.\n"
        "ᴛʏᴘᴇ <code>ᴍᴇ</code> ꜰᴏʀ ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ.\n"
        "/ᴄᴀɴᴄᴇʟ - ᴛᴏ ᴄᴀɴᴄᴇʟ</b>"
    ),
    "hi": (
        "<b>❪ स्रोत चैट सेट करें ❫\n\n"
        "अंतिम संदेश या लिंक फॉरवर्ड करें।\n"
        "बोट/प्राइवेट चैट के लिए यूज़रनेम/ID टाइप करें।\n"
        "सेव्ड मैसेज के लिए <code>me</code> टाइप करें।\n"
        "रद्द करने के लिए /cancel</b>"
    ),
    "hinglish": (
        "<b>❪ SOURCE CHAT BATAO ❫\n\n"
        "Last message ya link forward karo.\n"
        "Bot/private chat ke liye username ya ID bhejo.\n"
        "Saved messages ke liye <code>me</code> likho.\n"
        "Cancel karne ke liye /cancel</b>"
    ),
}

#  TO_MSG 
_S["TO_MSG"] = {
    "en": "<b>❪ CHOOSE TARGET CHAT ❫\n\nChoose your target chat from the given buttons.\n/cancel - Cancel this process</b>",
    "hi": "<b>❪ टारगेट चैट चुनें ❫\n\nनीचे दिए गए बटन से अपनी टारगेट चैट चुनें।\n/cancel - इस प्रक्रिया को रद्द करें</b>",
    "hinglish": "<b>❪ TARGET CHAT CHUNO ❫\n\nNeeche diye gaye buttons se target chat select karo.\n/cancel - is process ko cancel karo</b>",
}

#  SAVED_MSG_MODE 
_S["SAVED_MSG_MODE"] = {
    "en": "<b>❪ SELECT MODE ❫\n\nChoose forwarding mode:\n1. <code>batch</code> - Forward existing messages.\n2. <code>live</code> - Continuous (wait for new messages).</b>",
    "hi": "<b>❪ मोड चुनें ❫\n\nफॉरवर्डिंग मोड चुनें:\n1. <code>batch</code> - मौजूदा संदेश फॉरवर्ड करें।\n2. <code>live</code> - लाइव (नए संदेशों का इंतजार करें)।</b>",
    "hinglish": "<b>❪ MODE SELECT KARO ❫\n\nForwarding mode chuno:\n1. <code>batch</code> - Purane messages forward karo.\n2. <code>live</code> - Naye messages ka wait karega.</b>",
}

#  SAVED_MSG_LIMIT 
_S["SAVED_MSG_LIMIT"] = {
    "en": "<b>❪ NUMBER OF MESSAGES ❫\n\nHow many messages to forward?\nEnter a number or <code>all</code>.</b>",
    "hi": "<b>❪ संदेशों की संख्या ❫\n\nकितने संदेश फॉरवर्ड करने हैं?\nकोई संख्या डालें या <code>all</code> लिखें।</b>",
    "hinglish": "<b>❪ KITNE MESSAGES ❫\n\nKitne messages forward karne hain?\nNumber likho ya <code>all</code> bhejo.</b>",
}

#  SKIP_MSG 
_S["SKIP_MSG"] = {
    "en": (
        "<b>❪ ꜱᴇᴛ ᴍᴇꜱꜱᴀɢᴇ ꜱᴋɪᴘɪɴɢ ɴᴜᴍʙᴇʀ ❫</b>\n\n"
        "<b>ꜱᴋɪᴘ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ᴀꜱ ᴍᴜᴄʜ ᴀꜱ ʏᴏᴜ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴜᴍʙᴇʀ ᴀɴᴅ ᴛʜᴇ ʀᴇꜱᴛ ᴏꜰ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ꜰᴏʀᴡᴀʀᴅᴇᴅ\n"
        "ᴅᴇꜰᴀᴜʟᴛ ꜱᴋɪᴘ ɴᴜᴍʙᴇʀ =</b> <code>0</code>\n"
        "<code>ᴇɢ: ʏᴏᴜ ᴇɴᴛᴇʀ 0 = 0 ᴍᴇꜱꜱᴀɢᴇ ꜱᴋɪᴘᴇᴅ\n"
        " ʏᴏᴜ ᴇɴᴛᴇʀ 5 = 5 ᴍᴇꜱꜱᴀɢᴇ ꜱᴋɪᴘᴇᴅ</code>\n"
        "/ᴄᴀɴᴄᴇʟ <b>- ᴄᴀɴᴄᴇʟ ᴛʜɪꜱ ᴘʀᴏᴄᴇꜱꜱ</b>"
    ),
    "hi": (
        "<b>❪ संदेश छोड़ें ❫</b>\n\n"
        "<b>जितनी संख्या डालेंगे उतने संदेश छोड़कर बाकी फॉरवर्ड होंगे।\n"
        "डिफ़ॉल्ट =</b> <code>0</code>\n"
        "<code>उदा: 0 = 0 छोड़े गए\n"
        " 5 = 5 छोड़े गए</code>\n"
        "रद्द करने के लिए /cancel"
    ),
    "hinglish": (
        "<b>❪ SKIP MESSAGES ❫</b>\n\n"
        "<b>Jitna number bataoge utne shuru ke messages chutt jayenge\n"
        "Default skip =</b> <code>0</code>\n"
        "<code>eg: 0 likhne par = 0 skip honge\n"
        " 5 likhne par = 5 skip honge</code>\n"
        "Cancel ke liye /cancel"
    ),
}

#  CANCEL 
_S["CANCEL"] = {
    "en": "<b>Process Cancelled Succefully !</b>",
    "hi": "<b>प्रक्रिया सफलतापूर्वक रद्द की गई!</b>",
    "hinglish": "<b>Process Cancel ho gaya!</b>",
}

#  BOT_DETAILS 
_S["BOT_DETAILS"] = {
    "en": "<b><u>»  BOT DETAILS</u></b>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ BOT ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}",
    "hi": "<b><u>»  बोट विवरण</u></b>\n\n<b>➣ नाम:</b> <code>{}</code>\n<b>➣ बोट ID:</b> <code>{}</code>\n<b>➣ यूज़रनेम:</b> @{}",
    "hinglish": "<b><u>»  BOT DETAILS</u></b>\n\n<b>➣ NAAM:</b> <code>{}</code>\n<b>➣ BOT ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}",
}

#  USER_DETAILS 
_S["USER_DETAILS"] = {
    "en": "<b><u>»  USERBOT DETAILS</u></b>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ USER ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}",
    "hi": "<b><u>»  यूज़रबोट विवरण</u></b>\n\n<b>➣ नाम:</b> <code>{}</code>\n<b>➣ यूज़र ID:</b> <code>{}</code>\n<b>➣ यूज़रनेम:</b> @{}",
    "hinglish": "<b><u>»  USERBOT DETAILS</u></b>\n\n<b>➣ NAAM:</b> <code>{}</code>\n<b>➣ USER ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}",
}

#  TEXT (forwarding status box) 
_S["TEXT"] = {
    "en": (
        "<b>╔════❰ Forward Status ❱═❍⊱❁۪۪\n"
        "║╭━━━━━━━━━━━━━━━➣\n"
        "║┣⪼ Fetched messages: <code>{}</code>\n"
        "║┣⪼ Successfully forwarded: <code>{}</code>\n"
        "║┣⪼ Duplicate messages: <code>{}</code>\n"
        "║┣⪼ Skipped messages: <code>{}</code>\n"
        "║┣⪼ Deleted messages: <code>{}</code>\n"
        "║┣⪼ Current status: <code>{}</code>\n"
        "║┣⪼ ETA: <code>{}</code>\n"
        "║╰━━━━━━━━━━━━━━━➣\n"
        "╚═════❰ Auto Forwarder ❱══❍⊱❁۪۪</b>"
    ),
    "hi": (
        "<b>╔════❰ Forward Status ❱═❍⊱❁۪۪\n"
        "║╭━━━━━━━━━━━━━━━➣\n"
        "║┣⪼ Fetched messages: <code>{}</code>\n"
        "║┣⪼ Successfully forwarded: <code>{}</code>\n"
        "║┣⪼ Duplicate messages: <code>{}</code>\n"
        "║┣⪼ Skipped messages: <code>{}</code>\n"
        "║┣⪼ Deleted messages: <code>{}</code>\n"
        "║┣⪼ Current status: <code>{}</code>\n"
        "║┣⪼ ETA: <code>{}</code>\n"
        "║╰━━━━━━━━━━━━━━━➣\n"
        "╚═════❰ Auto Forwarder ❱══❍⊱❁۪۪</b>"
    ),
    "hinglish": (
        "<b>╔════❰ Forward Status ❱═❍⊱❁۪۪\n"
        "║╭━━━━━━━━━━━━━━━➣\n"
        "║┣⪼ Fetched messages: <code>{}</code>\n"
        "║┣⪼ Successfully forwarded: <code>{}</code>\n"
        "║┣⪼ Duplicate messages: <code>{}</code>\n"
        "║┣⪼ Skipped messages: <code>{}</code>\n"
        "║┣⪼ Deleted messages: <code>{}</code>\n"
        "║┣⪼ Current status: <code>{}</code>\n"
        "║┣⪼ ETA: <code>{}</code>\n"
        "║╰━━━━━━━━━━━━━━━➣\n"
        "╚═════❰ Auto Forwarder ❱══❍⊱❁۪۪</b>"
    ),
}

#  DUPLICATE_TEXT 
_S["DUPLICATE_TEXT"] = {
    "en": (
        "<b>╔════❰ Unequify Status ❱═❍⊱❁۪۪\n"
        "║╭━━━━━━━━━━━━━━━➣\n"
        "║┣⪼ Fetched messages: <code>{}</code>\n"
        "║┣⪼ Duplicate messages: <code>{}</code>\n"
        "║┣⪼ {} \n"
        "║╰━━━━━━━━━━━━━━━➣\n"
        "╚═════❰ Setup ❱══❍⊱❁۪۪</b>"
    ),
    "hi": (
        "<b>╔════❰ Unequify Status ❱═❍⊱❁۪۪\n"
        "║╭━━━━━━━━━━━━━━━➣\n"
        "║┣⪼ Fetched messages: <code>{}</code>\n"
        "║┣⪼ Duplicate messages: <code>{}</code>\n"
        "║┣⪼ {} \n"
        "║╰━━━━━━━━━━━━━━━➣\n"
        "╚═════❰ Setup ❱══❍⊱❁۪۪</b>"
    ),
    "hinglish": (
        "<b>╔════❰ Unequify Status ❱═❍⊱❁۪۪\n"
        "║╭━━━━━━━━━━━━━━━➣\n"
        "║┣⪼ Fetched messages: <code>{}</code>\n"
        "║┣⪼ Duplicate messages: <code>{}</code>\n"
        "║┣⪼ {} \n"
        "║╰━━━━━━━━━━━━━━━➣\n"
        "╚═════❰ Setup ❱══❍⊱❁۪۪</b>"
    ),
}

#  Simple one-liners 
_S["<i>Process Cancelled Successfully!</i>"] = {
    "en": "»  Process cancelled.",
    "hi": "»  प्रक्रिया रद्द की गई।",
    "hinglish": "»  Process cancel ho gaya.",
}
_S["btn_settings"] = {"en": "• Settings •", "hi": "• Settings •", "hinglish": "• Settings •"}
_S["btn_bots"] = {"en": "• Bots •", "hi": "• Bots •", "hinglish": "• Bots •"}
_S["btn_jobs"] = {"en": "• Live Jobs •", "hi": "• Live Jobs •", "hinglish": "• Live Jobs •"}
_S["btn_help"] = {"en": "🙋 Hᴇʟᴘ", "hi": "🙋 Hᴇʟᴘ", "hinglish": "🙋 Hᴇʟᴘ"}
_S["btn_about"] = {"en": "💁 Aʙᴏᴜᴛ", "hi": "💁 Aʙᴏᴜᴛ", "hinglish": "💁 Aʙᴏᴜᴛ"}
_S["btn_close"] = {"en": "‣  Close", "hi": "‣  बंद करें", "hinglish": "‣  Close"}
_S["settings_title"] = {
    "en": "»  Change your settings as you wish:",
    "hi": "»  अपनी सेटिंग्स बदलें:",
    "hinglish": "»  Apni settings apne hisaab se badlo:",
}
_S["select_lang"] = {
    "en": "»  Select your preferred language:",
    "hi": "»  अपनी भाषा चुनें:",
    "hinglish": "»  Apni language select karo:",
}
_S["lang_set"] = {
    "en": "»  Language set to <b>English</b>.",
    "hi": "»  भाषा <b>हिंदी</b> में सेट की गई।",
    "hinglish": "»  Language <b>Hinglish</b> mein set ho gayi!",
}
_S["no_bot"] = {
    "en": "<code>You didn't add any bot. Please add a bot using /settings !</code>",
    "hi": "<code>आपने कोई बोट नहीं जोड़ा। /settings से बोट जोड़ें!</code>",
    "hinglish": "<code>Koi bot add nahi kiya. /settings se bot add karo!</code>",
}
_S["no_channel"] = {
    "en": "Please set a target channel in /settings before forwarding.",
    "hi": "फॉरवर्ड करने से पहले /settings में टारगेट चैनल सेट करें।",
    "hinglish": "Forward karne se pehle /settings mein target channel set karo.",
}
_S["choose_account"] = {
    "en": "<b>Choose Account for Forwarding:</b>",
    "hi": "<b>फॉरवर्डिंग के लिए अकाउंट चुनें:</b>",
    "hinglish": "<b>Forwarding ke liye account chuno:</b>",
}
_S["choose_order"] = {
    "en": "<b>Choose Forwarding Order:</b>",
    "hi": "<b>फॉरवर्डिंग का क्रम चुनें:</b>",
    "hinglish": "<b>Forwarding order chuno:</b>",
}
_S["order_old_new"] = {"en": "Old to New", "hi": "पुराना से नया", "hinglish": "Old to New"}
_S["order_new_old"] = {"en": "New to Old", "hi": "नया से पुराना", "hinglish": "New to Old"}

# ══════════════════════════════════════════════════════════════════════════════
# Core helpers
# ══════════════════════════════════════════════════════════════════════════════

def _tx(lang: str, key: str, *args, **kwargs) -> str:
    """Return translated string for given lang+key. Falls back to English."""
    lang_map = _S.get(key, {})
    text = lang_map.get(lang) or lang_map.get("en", f"[{key}]")
    if args or kwargs:
        try:
            text = text.format(*args, **kwargs)
        except (KeyError, IndexError):
            pass
    return text


async def t(user_id: int, key: str, *args, **kwargs) -> str:
    """Async helper: fetch user's language from DB then return translated string."""
    lang = await db.get_language(user_id)
    return _tx(lang, key, *args, **kwargs)


def t_sync(lang: str, key: str, *args, **kwargs) -> str:
    """Sync helper when you already know the lang string."""
    return _tx(lang, key, *args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
# /lang command + callbacks
# ══════════════════════════════════════════════════════════════════════════════

def _lang_keyboard(current_lang: str) -> InlineKeyboardMarkup:
    def mark(code): return "»  " if current_lang == code else ""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{mark('en')}🇺🇸 English",       callback_data="setlang#en"),
            InlineKeyboardButton(f"{mark('hi')}🇮🇳 हिंदी",         callback_data="setlang#hi"),
        ],
        [
            InlineKeyboardButton(f"{mark('hinglish')}»  Hinglish", callback_data="setlang#hinglish"),
        ],
        [
            InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#main"),
        ]
    ])


@Client.on_message(filters.private & filters.command("lang"))
async def lang_cmd(bot, message):
    user_id = message.from_user.id
    current = await db.get_language(user_id)
    await message.reply_text(
        _tx(current, "select_lang"),
        reply_markup=_lang_keyboard(current)
    )


@Client.on_callback_query(filters.regex(r'^settings#lang$'))
async def lang_settings_cb(bot, query):
    user_id = query.from_user.id
    current = await db.get_language(user_id)
    await query.message.edit_text(
        _tx(current, "select_lang"),
        reply_markup=_lang_keyboard(current)
    )


@Client.on_callback_query(filters.regex(r'^setlang#'))
async def setlang_cb(bot, query):
    user_id = query.from_user.id
    lang    = query.data.split("#", 1)[1]
    if lang not in ("en", "hi", "hinglish"):
        return await query.answer("ɪɴᴠᴀʟɪᴅ ʟᴀɴɢᴜᴀɢᴇ!", show_alert=True)

    await db.set_language(user_id, lang)
    label_map = {"en": "English 🇺🇸", "hi": "हिंदी 🇮🇳", "hinglish": "Hinglish"}
    label = label_map.get(lang, lang)
    await query.answer(f"Language set to {label}!", show_alert=False)
    await query.message.edit_text(
        _tx(lang, "lang_set"),
        reply_markup=_lang_keyboard(lang)
    )