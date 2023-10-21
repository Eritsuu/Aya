import pyrogram
from pyrogram import Client,filters
from pyrogram.types import InlineKeyboardMarkup,InlineKeyboardButton
from os import environ, remove
from threading import Thread
from json import load
from re import search

from texts import HELP_TEXT
from bot.core import bypasser
from bot.core import freewall
from time import time


# Handler for the "/bp" command
@app.on_message(filters.command("bp", prefixes="/"))
async def bypass_command(client, message):
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
@app.on_message(filters.text)
async def receive_text(client, message):
    # Put your text message handling logic here
    # For example:
    await app.send_message(message.chat.id, "Received a text message")

# Handler for document files
@app.on_message([filters.document, filters.photo, filters.video])
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
