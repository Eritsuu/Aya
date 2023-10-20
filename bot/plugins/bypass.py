
from time import time
from re import match
from asyncio import create_task, gather, sleep as asleep, create_subprocess_exec
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command, private, user
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from pyrogram.enums import MessageEntityType
from pyrogram.errors import QueryIdInvalid

from bot import Bypass, BOT_START, LOGGER
from bot.core.bypass_checker import direct_link_checker, is_excep_link
from bot.helper.ext_utils.bot_utils import get_readable_time
from bot.core.exceptions import DDLException

 
async def bypass_check(client, message):
    uid = message.from_user.id
    if (reply_to := message.reply_to_message) and (reply_to.text is not None or reply_to.caption is not None):
        txt = reply_to.text or reply_to.caption
        entities = reply_to.entities or reply_to.caption_entities
    elif len(message.command) > 1:
        txt = message.text
        entities = message.entities
    else:
        return await message.reply('<i>Tidak Ada Tautan yang Disediakan!</i>')
    
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
            bp_link = f"\n➥ <b>Bypass Gagal:</b> {result}"
        elif is_excep_link(link):
            bp_link = result
        else:
            bp_link = f"\n➥ <b>Bypass Link:</b> {result}"
    
        if is_excep_link(link):
            parse_data.append(f"{bp_link}\n\n━━━━━━━✦Aya✦━━━━━━━\n\n")
        else:
            parse_data.append(f'┎ <b>Source Link:</b> {link}{bp_link}\n\n━━━━━━━✦Aya✦━━━━━━━\n\n')
            
    end = time()

    if len(parse_data) != 0:
        parse_data[-1] = parse_data[-1] + f" ➥<b>Total Links : {no}</b>\n➥ <b>Results In <code>{convert_time(end - start)}</code></b> !\n➥ <b>By </b>{message.from_user.mention} ( #ID{message.from_user.id} )"
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


@Bypass.on_inline_query()
async def inline_query(client, query):
    answers = [] 
    string = query.query.lower()
    if string.startswith("!bp "):
        link = string.strip('!bp ')
        start = time()
        try:
            bp_link = await direct_link_checker(link)
            end = time()
            
            if not is_excep_link(link):
                bp_link = f"➥ <b>Source Link:</b> {link}\n\n <b>🎉 Hasil Bypass:</b> {bp_link}"
            answers.append(InlineQueryResultArticle(
                title="🎉 Bypass Link Berhasil !",
                input_message_content=InputTextMessageContent(
                    f'{bp_link}\n\n✎﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏\n\n🧭 <b>Waktu <code>{get_readable_time(end - start)}</code></b>',
                    disable_web_page_preview=True,
                ),
                description=f"Bypass via !bp {link}",
                reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('Bypass Again', switch_inline_query_current_chat="!bp ")]
                ])
            ))
        except Exception as e:
            bp_link = f"<b>Bypass Error:</b> {e}"
            end = time()

            answers.append(InlineQueryResultArticle(
                title="❌️ Bypass Link Error !",
                input_message_content=InputTextMessageContent(
                    f'➥ <b>Source Link:</b> {link}\n\n➥ {bp_link}\n\n✎﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏\n\n🧭 <b>Waktu <code>{get_readable_time(end - start)}</code></b>',
                    disable_web_page_preview=True,
                ),
                description=f"Bypass via !bp {link}",
                reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('Bypass Lagi', switch_inline_query_current_chat="!bp ")]
                ])
            ))    
        
    else:
        answers.append(InlineQueryResultArticle(
                title="♻️ Bypass Usage: In Line",
                input_message_content=InputTextMessageContent(
                    '''<b><i>Aya Bot!</i></b>
    
    <i>.Aya bot can Bypass Various Shortener Links, Scrape links, and More ... </i>
    
🎛 <b>Inline Use :</b> !bp [Single Link]''',
                ),
                description="Bypass via !bp [link]",
                reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Channel", url="https://t.me/Ricloudw"),
                        InlineKeyboardButton('Coba Bypass Lagi', switch_inline_query_current_chat="!bp ")]
                ])
            ))
    try:
        await query.answer(
            results=answers,
            cache_time=0
        )
    except QueryIdInvalid:
        pass

bot.add_handler(MessageHandler(bypass, filters=command(
    BotCommands.BypassCommand) & CustomFilters.sudo))
