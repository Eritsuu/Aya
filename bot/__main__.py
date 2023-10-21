#!/usr/bin/env python3
from uuid import uuid4
from signal import signal, SIGINT
from aiofiles.os import path as aiopath, remove as aioremove
from aiofiles import open as aiopen
from os import execl as osexecl
from psutil import disk_usage, cpu_percent, swap_memory, cpu_count, virtual_memory, net_io_counters, boot_time
from time import time
from sys import executable
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from asyncio import create_subprocess_exec, gather
from re import match

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from pyrogram.enums import MessageEntityType
from pyrogram.errors import QueryIdInvalid

from bot import bot, botStartTime, LOGGER, Interval, DATABASE_URL, QbInterval, INCOMPLETE_TASK_NOTIFIER, scheduler, user_data
from bot.helper.ext_utils.aya_utils import set_commands
from .helper.ext_utils.fs_utils import start_cleanup, clean_all, exit_clean_up
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time, cmd_exec, sync_to_async
from .helper.ext_utils.db_handler import DbManger
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.message_utils import sendMessage, editMessage, sendFile, delete_all_messages
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.button_build import ButtonMaker
from bot.helper.listeners.aria2_listener import start_aria2_listener
from .modules import authorize, broadcast, clone, gd_count, gd_delete, cancel_mirror, gd_search, mirror_leech, photo_upload, status, torrent_search, torrent_select, ytdlp, rss, shell, eval, users_settings, bot_settings
from bot.core.bypass_checker import direct_link_checker, is_excep_link
from bot.core.bot_utils import convert_time
from bot.core.exceptions import DDLException


async def stats(client, message):
    if await aiopath.exists('.git'):
        last_commit = await cmd_exec("git log -1 --date=short --pretty=format:'%cd <b>\nFrom:</b> %cr'", True)
        last_commit = last_commit[0]
    else:
        last_commit = 'No UPSTREAM_REPO'
    total, used, free, disk = disk_usage('/')
    swap = swap_memory()
    memory = virtual_memory()
    stats = f'<b>💬 Commit Date:</b> {last_commit}\n\n'\
            f'<b>🤖 Bot Uptime:</b> {get_readable_time(time() - botStartTime)}\n'\
            f'<b>💨 OS Uptime:</b> {get_readable_time(time() - boot_time())}\n\n'\
            f'<b>🔖 Total Disk Space:</b> {get_readable_file_size(total)}\n'\
            f'<b>🫣 Used:</b> {get_readable_file_size(used)} | <b>🤔 Free:</b> {get_readable_file_size(free)}\n\n'\
            f'<b>📤 Up:</b> {get_readable_file_size(net_io_counters().bytes_sent)} <b>|</b> '\
            f'<b>📥 Down:</b> {get_readable_file_size(net_io_counters().bytes_recv)}\n'\
            f'<b>💣 CPU:</b> {cpu_percent(interval=0.5)}% <b>|</b> '\
            f'<b>💿 RAM:</b> {memory.percent}% <b>| </b>'\
            f'<b>📀 DISK:</b> {disk}%\n'\
            f'<b>🔩 Physical Cores:</b> {cpu_count(logical=False)} <b>|</b> '\
            f'<b>🔩 Total Cores:</b> {cpu_count(logical=True)}\n\n'\
            f'<b>🔗 SWAP:</b> {get_readable_file_size(swap.total)} | <b>Used:</b> {swap.percent}%\n'\
            f'<b>🥡 Memory Total:</b> {get_readable_file_size(memory.total)}\n'\
            f'<b>🥡 Memory Free:</b> {get_readable_file_size(memory.available)}\n'\
            f'<b>🥡 Memory Used:</b> {get_readable_file_size(memory.used)}\n'
    await sendMessage(message, stats, )


async def start(client, message):
    if len(message.command) > 1:
        userid = message.from_user.id
        input_token = message.command[1]
        if userid not in user_data:
            return await sendMessage(message, 'Who are you?')
        data = user_data[userid]
        if 'token' not in data or data['token'] != input_token:
            return await sendMessage(message, 'This token already expired')
        data['token'] = str(uuid4())
        data['time'] = time()
        user_data[userid].update(data)
        return await sendMessage(message, 'Token refreshed successfully!')
    else:
        buttons = ButtonMaker()
        buttons.ubutton("🎉 Channel", "https://t.me/Ricloudw")
        buttons.ubutton("🎓 Owner", "https://t.me/Eritsuu")
        buttons.ubutton("👋 Donate", "https://link.dana.id/qr/3vbyw7nu") 
        reply_markup = buttons.build_menu(2)
        start_string = f'''Bot ini dapat mencerminkan semua tautan|file|torrent Anda ke Google Drive atau rclone cloud atau ke telegram.\nType /{BotCommands.HelpCommand} untuk mendapatkan daftar perintah yang tersedia'''
        await sendMessage(message, start_string, reply_markup)
    await DbManger().update_pm_users(message.from_user.id)
    

async def restart(_, message):
    await delete_all_messages()
    restart_message = await sendMessage(message, "🎉Memulai Ulang...")
    if scheduler.running:
        scheduler.shutdown(wait=False)
    for interval in [QbInterval, Interval]:
        if interval:
            interval[0].cancel()
    await sync_to_async(clean_all)
    proc1 = await create_subprocess_exec('pkill', '-9', '-f', 'gunicorn|aria2c|qbittorrent-nox|ffmpeg|rclone')
    proc2 = await create_subprocess_exec('python3', 'update.py')
    await gather(proc1.wait(), proc2.wait())
    async with aiopen(".restartmsg", "w") as f:
        await f.write(f"{restart_message.chat.id}\n{restart_message.id}\n")
    osexecl(executable, executable, "-m", "bot")


async def ping(_, message):
    start_time = int(round(time() * 1000))
    reply = await sendMessage(message, "Starting Ping")
    end_time = int(round(time() * 1000))
    await editMessage(reply, f'🏓Pong {end_time - start_time} ms')


async def log(_, message):
    await sendFile(message, 'log.txt')
    
    ##logFileRead = open('log.txt', 'r')
    ##logFileLines = logFileRead.read().splitlines()
    ##ind = 1
    ##Loglines = ''
    ##try:
        ##while len(Loglines) <= 2500:
            ##Loglines = logFileLines[-ind]+'\n'+Loglines
            ##if ind == len(logFileLines):
                ##break
            ##ind += 1
        ##log_text = Loglines
        ##await client.send_message(chat_id=message.chat.id, text=log_text, disable_web_page_preview=True)
    ##except Exception as err:
        ##LOGGER.error(f"Log Display: {err}")


help_string = f'''
NOTE: Try each command without any argument to see more detalis.
/{BotCommands.MirrorCommand[0]} or /{BotCommands.MirrorCommand[1]}: Start mirroring to Google Drive.
/{BotCommands.QbMirrorCommand[0]} or /{BotCommands.QbMirrorCommand[1]}: Start Mirroring to Google Drive using qBittorrent.
/{BotCommands.YtdlCommand[0]} or /{BotCommands.YtdlCommand[1]}: Mirror yt-dlp supported link.
/{BotCommands.LeechCommand[0]} or /{BotCommands.LeechCommand[1]}: Start leeching to Telegram.
/{BotCommands.QbLeechCommand[0]} or /{BotCommands.QbLeechCommand[1]}: Start leeching using qBittorrent.
/{BotCommands.YtdlLeechCommand[0]} or /{BotCommands.YtdlLeechCommand[1]}: Leech yt-dlp supported link.
/{BotCommands.CloneCommand} [drive_url]: Copy file/folder to Google Drive.
/{BotCommands.CountCommand} [drive_url]: Count file/folder of Google Drive.
/{BotCommands.DeleteCommand} [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo).
/{BotCommands.UserSetCommand} [query]: Users settings.
/{BotCommands.BotSetCommand} [query]: Bot settings.
/{BotCommands.BtSelectCommand}: Select files from torrents by gid or reply.
/{BotCommands.CancelMirror}: Cancel task by gid or reply.
/{BotCommands.CancelAllCommand} [query]: Cancel all [status] tasks.
/{BotCommands.ListCommand} [query]: Search in Google Drive(s).
/{BotCommands.SearchCommand} [query]: Search for torrents with API.
/{BotCommands.StatusCommand}: Shows a status of all the downloads.
/{BotCommands.StatsCommand}: Show stats of the machine where the bot is hosted in.
/{BotCommands.PingCommand}: Check how long it takes to Ping the Bot (Only Owner & Sudo).
/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Only Owner & Sudo).
/{BotCommands.UnAuthorizeCommand}: Unauthorize a chat or a user to use the bot (Only Owner & Sudo).
/{BotCommands.UsersCommand}: show users settings (Only Owner & Sudo).
/{BotCommands.AddSudoCommand}: Add sudo user (Only Owner).
/{BotCommands.RmSudoCommand}: Remove sudo users (Only Owner).
/{BotCommands.RestartCommand}: Restart and update the bot (Only Owner & Sudo).
/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports (Only Owner & Sudo).
/{BotCommands.ShellCommand}: Run shell commands (Only Owner).
/{BotCommands.EvalCommand}: Run Python Code Line | Lines (Only Owner).
/{BotCommands.ExecCommand}: Run Commands In Exec (Only Owner).
/{BotCommands.ClearLocalsCommand}: Clear {BotCommands.EvalCommand} or {BotCommands.ExecCommand} locals (Only Owner).
/{BotCommands.RssCommand}: RSS Menu.
/{BotCommands.BypassCommand}: Bypass Link.
'''


async def bot_help(_, message):
    await sendMessage(message, help_string)


async def restart_notification():
    if await aiopath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
    else:
        chat_id, msg_id = 0, 0

    async def send_incompelete_task_message(cid, msg):
        try:
            if msg.startswith('Berhasil Dimulai Ulang!'):
                await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=msg)
                await aioremove(".restartmsg")
            else:
                await bot.send_message(chat_id=cid, text=msg, disable_web_page_preview=True,
                                       disable_notification=True)
        except Exception as e:
            LOGGER.error(e)

    if INCOMPLETE_TASK_NOTIFIER and DATABASE_URL:
        if notifier_dict := await DbManger().get_incomplete_tasks():
            for cid, data in notifier_dict.items():
                msg = 'Berhasil Dimulai Ulang!' if cid == chat_id else 'Bot Dimulai Ulang!'
                for tag, links in data.items():
                    msg += f"\n\n{tag}: "
                    for index, link in enumerate(links, start=1):
                        msg += f" <a href='{link}'>{index}</a> |"
                        if len(msg.encode()) > 4000:
                            await send_incompelete_task_message(cid, msg)
                            msg = ''
                if msg:
                    await send_incompelete_task_message(cid, msg)

    if await aiopath.isfile(".restartmsg"):
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text='🎉 Memulai Ulang Berhasil!')
        except:
            pass
        await aioremove(".restartmsg")



##Handler for the "/bp" command
@bot.on_message(command(["bp", "bypass"]))
async def bypass_check(_, message):
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


async def main():
    await gather(start_cleanup(), torrent_search.initiate_search_tools(), restart_notification(), set_commands(bot))
    await sync_to_async(start_aria2_listener, wait=False)

    bot.add_handler(MessageHandler(
        start, filters=command(BotCommands.StartCommand)))
    bot.add_handler(MessageHandler(log, filters=command(
        BotCommands.LogCommand) & CustomFilters.sudo))
    bot.add_handler(MessageHandler(restart, filters=command(
        BotCommands.RestartCommand) & CustomFilters.sudo))
    bot.add_handler(MessageHandler(ping, filters=command(
        BotCommands.PingCommand) & CustomFilters.authorized))
    bot.add_handler(MessageHandler(bot_help, filters=command(
        BotCommands.HelpCommand) & CustomFilters.authorized))
    bot.add_handler(MessageHandler(stats, filters=command(
        BotCommands.StatsCommand) & CustomFilters.authorized))
    LOGGER.info("💥 Bot Started!")
    signal(SIGINT, exit_clean_up)

bot.loop.run_until_complete(main())
bot.loop.run_forever()
