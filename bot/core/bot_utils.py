from pyrogram.filters import create
from re import search
from requests import get as rget
from urllib.parse import urlparse, parse_qs


def get_gdriveid(link):
    if "folders" in link or "file" in link:
        res = search(r"https:\/\/drive\.google\.com\/(?:drive(.*?)\/folders\/|file(.*?)?\/d\/)([-\w]+)", link)
        return res.group(3)
    parsed = urlparse(link)
    return parse_qs(parsed.query)['id'][0]

def get_dl(link):
    try:
        return rget(f"{Config.DIRECT_INDEX}/generate.aspx?id={get_gdriveid(link)}").json()["link"]
    except:
        return f"{Config.DIRECT_INDEX}/direct.aspx?id={get_gdriveid(link)}"

def convert_time(seconds):
    mseconds = seconds * 1000
    periods = [('d', 86400000), ('h', 3600000), ('m', 60000), ('s', 1000), ('ms', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if mseconds >= period_seconds:
            period_value, mseconds = divmod(mseconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    if result == '':
        return '0ms'
    return result
