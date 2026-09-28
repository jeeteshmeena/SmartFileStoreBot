import os
from config import Config

class Translation(object):
  START_TXT = """<b>Welcome <a href='tg://user?id={}'>{}</a>!</b>

Send me any file to store it, or use the buttons below."""

  HELP_TXT = """<b><u><emoji id="6037622221625626773">🤖</emoji> ʜᴇʟᴘ — ꜱᴍᴀʀᴛ ꜰɪʟᴇ ꜱᴛᴏʀᴇ ʙᴏᴛ</u></b>

<b>»  ᴄᴏᴍᴍᴀɴᴅꜱ:</b>
<code>/start</code>  — ᴄʜᴇᴄᴋ ɪꜰ ɪ'ᴍ ᴀʟɪᴠᴇ &amp; ᴏᴘᴇɴ ᴍᴀɪɴ ᴍᴇɴᴜ
<code>/settings</code>  — ᴄᴏɴꜰɪɢᴜʀᴇ ʙᴏᴛꜱ, ᴄʜᴀɴɴᴇʟꜱ &amp; ꜰɪʟᴛᴇʀꜱ
<code>/stats</code>  — ᴠɪᴇᴡ ʙᴏᴛ ꜱᴛᴏʀᴀɢᴇ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ
<code>/status</code>  — ᴄʜᴇᴄᴋ ꜱᴇʀᴠᴇʀ ᴘɪɴɢ, ꜱᴘᴇᴇᴅ &amp; ᴜᴘᴛɪᴍᴇ
<code>/reset</code>  — ʀᴇꜱᴇᴛ ꜱᴇᴛᴛɪɴɢꜱ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ

<b>»  ꜰᴇᴀᴛᴜʀᴇꜱ:</b>
<b>➲ </b> <b>ꜱᴍᴀʀᴛ ꜰɪʟᴇ ꜱᴛᴏʀᴇ:</b> ᴘᴇʀᴍᴀɴᴇɴᴛ ꜱᴛᴏʀᴀɢᴇ ᴡɪᴛʜ ɪɴꜱᴛᴀɴᴛ ꜱʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋꜱ
<b>➲ </b> <b>ʙᴀᴛᴄʜ ʟɪɴᴋꜱ:</b> ʙᴜɴᴅʟᴇ ᴍᴜʟᴛɪᴘʟᴇ ꜰɪʟᴇꜱ ɪɴᴛᴏ ᴀ ꜱɪɴɢʟᴇ ꜱᴇᴄᴜʀᴇ ʟɪɴᴋ
<b>➲ </b> <b>ᴍᴜʟᴛɪ-ʙᴏᴛ ɴᴇᴛᴡᴏʀᴋ:</b> ᴄᴏɴɴᴇᴄᴛ ᴅᴇʟɪᴠᴇʀʏ ʙᴏᴛꜱ ᴛᴏ ʙʏᴘᴀꜱꜱ ꜰʟᴏᴏᴅ ᴡᴀɪᴛꜱ
<b>➲ </b> <b>ꜱʜᴏʀᴛᴇɴᴇʀ ᴀᴘɪ:</b> ᴀʀᴏʟɪɴᴋꜱ &amp; ᴜʀʟꜱʜᴏʀᴛx ɪɴᴛᴇɢʀᴀᴛɪᴏɴ
<b>➲ </b> <b>ꜰᴏʀᴄᴇ-ꜱᴜʙ ꜱʏꜱᴛᴇᴍ:</b> ᴍᴀɴᴅᴀᴛᴏʀʏ ᴄʜᴀɴɴᴇʟ ᴊᴏɪɴ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ
<b>➲ </b> <b>ᴄᴏɴᴛᴇɴᴛ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ:</b> ᴘʀᴇᴠᴇɴᴛ ꜰᴏʀᴡᴀʀᴅɪɴɢ &amp; ᴄᴏᴘʏɪɴɢ ᴏꜰ ꜰɪʟᴇꜱ
"""
  
  HOW_USE_TXT = """<b><u><emoji id="6037622221625626773">🤖</emoji> ʜᴏᴡ ᴛᴏ ᴜꜱᴇ — ꜱᴍᴀʀᴛ ꜰɪʟᴇ ꜱᴛᴏʀᴇ ʙᴏᴛ</u></b>

<b>1️⃣ ᴀᴅᴅ ᴀ ᴅᴇʟɪᴠᴇʀʏ ʙᴏᴛ</b>
  ‣ ɢᴏ ᴛᴏ /ꜱᴇᴛᴛɪɴɢꜱ → <b>• ʙᴏᴛꜱ •</b>
  ‣ ᴄʟɪᴄᴋ <b>➕ ᴀᴅᴅ ʙᴏᴛ</b> ᴀɴᴅ ꜱᴇɴᴅ ʏᴏᴜʀ ʙᴏᴛ ᴛᴏᴋᴇɴ ꜰʀᴏᴍ @BotFather
  ‣ ʏᴏᴜ ᴄᴀɴ ᴀᴅᴅ ᴜᴘ ᴛᴏ 10 ʙᴏᴛꜱ ꜰᴏʀ ʜɪɢʜ-ꜱᴘᴇᴇᴅ ꜰɪʟᴇ ᴅᴇʟɪᴠᴇʀʏ

<b>2️⃣ ᴀᴅᴅ ʏᴏᴜʀ ꜱᴛᴏʀᴀɢᴇ ᴄʜᴀɴɴᴇʟ</b>
  ‣ ɢᴏ ᴛᴏ /ꜱᴇᴛᴛɪɴɢꜱ → <b>• ᴄʜᴀɴɴᴇʟꜱ •</b>
  ‣ ᴍᴀᴋᴇ ꜱᴜʀᴇ ʏᴏᴜʀ ʙᴏᴛ ɪꜱ <b>ᴀᴅᴍɪɴ</b> ɪɴ ʏᴏᴜʀ ꜱᴛᴏʀᴀɢᴇ ᴄʜᴀɴɴᴇʟ

<b>3️⃣ ꜱᴇᴛ ᴜᴘ ꜱʜᴏʀᴛᴇɴᴇʀꜱ (ᴏᴘᴛɪᴏɴᴀʟ)</b>
  ‣ ɢᴏ ᴛᴏ /ꜱᴇᴛᴛɪɴɢꜱ → <b>• ꜱʜᴏʀᴛᴇɴᴇʀꜱ •</b>
  ‣ ᴇɴᴛᴇʀ ʏᴏᴜʀ ᴀʀᴏʟɪɴᴋꜱ ᴏʀ ᴜʀʟꜱʜᴏʀᴛx ᴀᴘɪ ᴋᴇʏꜱ

<b>4️⃣ ɢᴇɴᴇʀᴀᴛᴇ ʙᴀᴛᴄʜ ʟɪɴᴋꜱ</b>
  ‣ ᴄʟɪᴄᴋ <b>• ʙᴀᴛᴄʜ ʟɪɴᴋꜱ •</b> ᴏɴ ᴛʜᴇ ᴍᴀɪɴ ᴍᴇɴᴜ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ ꜱɪɴɢʟᴇ ꜱʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ ꜰᴏʀ ᴍᴜʟᴛɪᴘʟᴇ ꜰɪʟᴇꜱ

<b>5️⃣ ꜱᴛᴏʀᴇ ꜰɪʟᴇꜱ ɪɴꜱᴛᴀɴᴛʟʏ</b>
  ‣ ꜱɪᴍᴘʟʏ ꜱᴇɴᴅ ᴀɴʏ ꜰɪʟᴇ/ᴍᴇᴅɪᴀ ᴅɪʀᴇᴄᴛʟʏ ᴛᴏ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ɢᴇᴛ ɪᴛꜱ ꜱʜᴀʀᴇᴀʙʟᴇ ꜱᴛᴏʀᴇ ʟɪɴᴋ
"""
  
  ABOUT_TXT = """<b>╭──────❰ 🤖 𝐁𝐨𝐭 𝐃𝐞𝐭𝐚𝐢𝐥𝐬 ❱──────╮
┃ 
┣⊸ 🤖 Mʏ Nᴀᴍᴇ   : <a href=https://t.me/MeJeetX>Aryᴀ Bᴏᴛ</a>
┣⊸ 👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ : <a href=https://t.me/MeJeetX>MeJeetX</a>
┣⊸ 📢 ᴄʜᴀɴɴᴇʟ   : <a href=https://t.me/MeJeetX>Updates</a>
┣⊸ 💬 sᴜᴘᴘᴏʀᴛ   : <a href=https://t.me/+1p2hcQ4ZaupjNjI1>Support Group</a>
┃ 
┣⊸ 🗣️ ʟᴀɴɢᴜᴀɢᴇ  : ᴘʏᴛʜᴏɴ 3 
┃  {python_version}
┣⊸ 📚 ʟɪʙʀᴀʀʏ   : ᴘʏʀᴏɢʀᴀᴍ  
┃
╰─────────────────────────────╯</b>"""
  
  STATUS_TXT = """<b>╭──────❰ 🤖 𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐮𝐬 ❱──────╮
┃
┣⊸ 👨 ᴜsᴇʀs   : <code>{}</code>
┣⊸ 🤖 ʙᴏᴛs    : <code>{}</code>
┣⊸ 📣 ᴄʜᴀɴɴᴇʟ : <code>{}</code>
┣⊸ 🚫 ʙᴀɴɴᴇᴅ  : <code>{}</code>
┃
╰─────────────────────────────╯</b>""" 
  
  FROM_MSG = "<b>❪ SET SOURCE CHAT ❫\n\nForward the last message or link.\nType username/ID (e.g. <code>@somebot</code> or <code>123456</code>) for bot/private chat.\nType <code>me</code> for Saved Messages.\n/cancel - to cancel</b>"
  TO_MSG = "<b>❪ CHOOSE TARGET CHAT ❫\n\nChoose your target chat from the given buttons.\n/cancel - Cancel this process</b>"
  SAVED_MSG_MODE = "<b>❪ SELECT MODE ❫\n\nChoose forwarding mode:\n1. <code>batch</code> - Forward existing messages.\n2. <code>live</code> - Continuous (wait for new messages).</b>"
  SAVED_MSG_LIMIT = "<b>❪ NUMBER OF MESSAGES ❫\n\nHow many messages to forward?\nEnter a number or <code>all</code>.</b>"
  SKIP_MSG = "<b>❪ SET MESSAGE SKIPING NUMBER ❫</b>\n\n<b>Skip the message as much as you enter the number and the rest of the message will be forwarded\nDefault Skip Number =</b> <code>0</code>\n<code>eg: You enter 0 = 0 message skiped\n You enter 5 = 5 message skiped</code>\n/cancel <b>- cancel this process</b>"
  CANCEL = "<b>Process Cancelled Succefully !</b>"
  BOT_DETAILS = "<b><u>📄 BOT DETAILS</b></u>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ BOT ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}"
  USER_DETAILS = "<b><u>📄 USERBOT DETAILS</b></u>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ USER ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}"  
         
  TEXT_BATCH = """<b>╭──────❰ ✦ 𝐀𝐮𝐭𝐨 𝐅𝐨𝐫𝐰𝐚𝐫𝐝𝐞𝐫 ✦ ❱──────╮
┃
┣⊸ ◈ Fᴇᴛᴄʜᴇᴅ     : <code>{}</code>
┣⊸ ◈ Fᴏʀᴡᴀʀᴅᴇᴅ   : <code>{}</code>
┣⊸ ◈ Dᴜᴘʟɪᴄᴀᴛᴇ   : <code>{}</code>
┣⊸ ◈ Sᴋɪᴘᴘᴇᴅ     : <code>{}</code>
┣⊸ ◈ Dᴇʟᴇᴛᴇᴅ     : <code>{}</code>
┃
┣⊸ ◈ Sᴛᴀᴛᴜs      : <code>{}</code>
┣⊸ ◈ ETA         : <code>{}</code>
┃
╰────────────────────────────────╯</b>"""

  TEXT_LIVE = """<b>╭──────❰ ✦ 𝐀𝐮𝐭𝐨 𝐅𝐨𝐫𝐰𝐚𝐫𝐝𝐞𝐫 ✦ ❱──────╮
┃
┣⊸ ◈ Fᴇᴛᴄʜᴇᴅ     : <code>{}</code>
┣⊸ ◈ Fᴏʀᴡᴀʀᴅᴇᴅ   : <code>{}</code>
┣⊸ ◈ Dᴜᴘʟɪᴄᴀᴛᴇ   : <code>{}</code>
┣⊸ ◈ Sᴋɪᴘᴘᴇᴅ     : <code>{}</code>
┣⊸ ◈ Dᴇʟᴇᴛᴇᴅ     : <code>{}</code>
┃
┣⊸ ◈ Sᴛᴀᴛᴜs      : <code>{}</code>
┃
╰────────────────────────────────╯</b>"""

  TEXT1 = TEXT_BATCH

  DUPLICATE_TEXT = """<b>╭──────❰ ✦ 𝐔𝐧𝐞𝐪𝐮𝐢𝐟𝐲 𝐒𝐭𝐚𝐭𝐮𝐬 ✦ ❱──────╮
┃
┣⊸ ◈ 𝐅𝐞𝐭𝐜𝐡𝐞𝐝     : <code>{}</code>
┣⊸ ◈ 𝐃𝐮𝐩𝐥𝐢𝐜𝐚𝐭𝐞𝐬  : <code>{}</code>
┃
╰───────────────── {} ────╯</b>"""
