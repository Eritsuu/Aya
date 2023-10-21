from time import time
from re import match
from asyncio import create_task, gather, sleep as asleep, create_subprocess_exec
from pyrogram.filters import command, private, user
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from pyrogram.enums import MessageEntityType
from pyrogram.errors import QueryIdInvalid

from bot import LOGGER
from bot.core.bypass_checker import direct_link_checker, is_excep_link
from bot.core.bot_utils import convert_time
from bot.core.exceptions import DDLException


# Handler for the "/bp" command
@bypass_message(filters.command("bp", "bypass", prefixes="/"))
async def bypass(self, message):
    uasync def bypass_check(client, message):
    uid = message.from_user.id
    if (reply_to := message.reply_to_message) and (reply_to.text is not None or reply_to.caption is not None):
        txt = reply_to.text or reply_to.caption
        entities = reply_to.entities or reply_to.caption_entities
    elif len(message.command) > 1:
        txt = message.text
        entities = message.entities
    else:
        return await message.reply('<i>No Link Provided!</i>')
    
    wait_msg = await message.reply("<i>Bypassing...</i>")
    start = time()

    link, tlinks, no = '', [], 0
    atasks = []
    for enty in entities:
        if enty.type == MessageEntityType.URL:
            link = txt[enty.offset:(enty.offset+enty.length)]
        elif enty.type == MessageEntityType.TEXT_LINK:
            link = enty.url
            
        if link:
            no += 1
            tlinks.append(link)
            atasks.append(create_task(direct_link_checker(link)))
            link = ''

    completed_tasks = await gather(*atasks, return_exceptions=True)
    
    parse_data = []
    for result, link in zip(completed_tasks, tlinks):
        if isinstance(result, Exception):
            bp_link = f"\n➢ <b>Bypass Error:</b> {result}"
        elif is_excep_link(link):
            bp_link = result
        elif isinstance(result, list):
            bp_link, ui = "", "➢"
            for ind, lplink in reversed(list(enumerate(result, start=1))):
                bp_link = f"\n{ui} <b>{ind}x Bypass Link:</b> {lplink}" + bp_link
                ui = "➢"
        else:
            bp_link = f"\n➢ <b>Bypass Link:</b> {result}"
    
        if is_excep_link(link):
            parse_data.append(f"{bp_link}\n\n━━━━━━━✦Aya✦━━━━━━━\n\n")
        else:
            parse_data.append(f'➣ <b>Source Link:</b> {link}{bp_link}\n\n━━━━━━━✦Aya✦━━━━━━━\n\n')
            
    end = time()

    if len(parse_data) != 0:
        parse_data[-1] = parse_data[-1] + f"➢ <b>Total Links : {no}</b>\n➢ <b>Results In <code>{convert_time(end - start)}</code></b> !\n➢ <b>By </b>{message.from_user.mention} ( #ID{message.from_user.id} )"
    tg_txt = "━━━━━━━✦Aya✦━━━━━━━\n\n"
    for tg_data in parse_data:
        tg_txt += tg_data
        if len(tg_txt) > 4000:
            await wait_msg.edit(tg_txt, disable_web_page_preview=True)
            wait_msg = await message.reply("<i>Fetching...</i>", reply_to_message_id=wait_msg.id)
            tg_txt = ""
            await asleep(2.5)
    
    if tg_txt != "":
        await wait_msg.edit(tg_txt, disable_web_page_preview=True)
    else:
        await wait_msg.delete()
