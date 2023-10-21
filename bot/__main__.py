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
from re import match, search

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
from bot.core import bypasser, freewall

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



# Handler for the "/bp" command
#@app.on_message(filters.command("bp", prefixes="/"))
async def bypass(client, message):
    urls = []
    if message.caption:
        texts = message.caption
    else:
        texts = message.text

    if not texts or texts.strip() == "":
        return

    for ele in texts.split():
        if "http://" in ele or "https://" in ele:
            urls.append(ele)

    if len(urls) == 0:
        return

    msg = None

    for ele in urls:
        if search(r"https?:\/\/(?:[\w.-]+)?\.\w+\/\d+:", ele):
            handleIndex(ele, message, msg)
            return
        elif bypasser.ispresent(bypasser.ddl.ddllist, ele):
            try:
                temp = await bypasser.ddl.direct_link_generator_async(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        elif freewall.pass_paywall(ele, check=True):
            freefile = freewall.pass_paywall(ele)
            if freefile:
                try:
                    await app.send_document(message.chat.id, freefile, reply_to_message_id=message.id)
                    remove(freefile)
                    await app.delete_messages(message.chat.id, [msg.id])
                    return
                except:
                    pass
            else:
                await app.send_message(message.chat.id, "__Failed to Jump", reply_to_message_id=message.id)
        else:
            try:
                temp = await bypasser.shorteners_async(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        print("bypassed:", temp)
        if temp is not None:
            links = links + temp + "\n"

    end = time()
    print("Took " + "{:.2f}".format(end - strt) + "sec")

    if otherss:
        try:
            await app.send_photo(message.chat.id, message.photo.file_id, f'__{links}__', reply_to_message_id=message.id)
            await app.delete_messages(message.chat.id, [msg.id])
            return
        except:
            pass

    try:
        final = []
        tmp = ""
        for ele in links.split("\n"):
            tmp += ele + "\n"
            if len(tmp) > 4000:
                final.append(tmp)
                tmp = ""
        final.append(tmp)
        await app.delete_messages(message.chat.id, msg.id)
        tmsgid = message.id
        for ele in final:
            tmsg = await app.send_message(message.chat.id, f'__{ele}__', reply_to_message_id=tmsgid, disable_web_page_preview=True)
            tmsgid = tmsg.id
    except Exception as e:
        await app.send_message(message.chat.id, f"__Failed to Bypass : {e}", reply_to_message_id=message.id)

# Handler for text messages
#@app.on_message(filters.text)
async def receive_text(client, message):
    # Put your text message handling logic here
    # For example:
    await app.send_message(message.chat.id, "Received a text message")

# Handler for document files
#@app.on_message([filters.document, filters.photo, filters.video])
async def docfile(client, message):
    try:
        if message.document.file_name.endswith("dlc"):
            await docthread(message)
    except:
        pass

# Define an async operation function
async def docthread(message):
    msg = await app.send_message(message.chat.id, "🔎 __bypassing...__", reply_to_message_id=message.id)
    print("sent DLC file")
    file = await app.download_media(message)
    dlccont = open(file, "r").read()
    links = bypasser.getlinks(dlccont)
    await app.edit_message_text(message.chat.id, msg.message_id, f'__{links}__', disable_web_page_preview=True)
    remove(file)


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
    bot.add_handler(MessageHandler(bypass, filters=command(
        BotCommands.BypassCommand) & CustomFilters.authorized))
    LOGGER.info("💥 Bot Started!")
    signal(SIGINT, exit_clean_up)

bot.loop.run_until_complete(main())
bot.loop.run_forever()
