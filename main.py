import os
import aiohttp
import asyncio
import tasksio
from colorama import Fore, Style
import random
from dateutil import parser
import datetime
import requests
import sys
import pyfiglet
import ctypes

def set_window_title(title):
    ctypes.windll.kernel32.SetConsoleTitleW(title)

def clear():
    os.system("clear||cls")

def title(t):
    os.system(f"title {t}")

class colors:
    @staticmethod
    def ask(qus):
        print(f"[?] {qus}")

    @staticmethod
    def what(txt):
        print(f"[?]{txt}")

    @staticmethod
    def banner(txt):
        print(f"{txt}")

    @staticmethod
    def error(txt):
        print(f"[{random.choice(['-', '!'])}]{txt}")

    @staticmethod
    def success(txt):
        print(f"[+] {txt}")

    @staticmethod
    def warning(txt):
        print(f"[!] {txt}")

    @staticmethod
    def log(txt):
        print(f"[!] {txt}")

    @staticmethod
    def msg(txt, idx):
        return f"[{idx+1}] {txt}"
        
    @staticmethod
    def ask2(qus):
        print(f"[+] {qus}")

    @staticmethod
    def ask3(qus):
        print(f"[+] {qus}")

clear()
title("Promotion Checker ")

bnr = pyfiglet.figlet_format("Pluto")
colors.banner(bnr + "\n")

def sort_(file, item):
    with open(file, "r") as f:
        beamed = f.read().split("\n")
        try:
            beamed.remove("")
        except ValueError:
            pass
    return item in beamed

def save(file, data):
    with open(file, "a+") as f:
        if not sort_(file, data):
            f.write(data + "\n")
        else:
            colors.warning(f"Duplicate Found -> {data}")

async def check(promocode):
    global claimed_count, valid_count
    async with aiohttp.ClientSession(headers=auth) as cs:
        async with cs.get(f"https://ptb.discord.com/api/v10/entitlements/gift-codes/{promocode}") as rs:
            if rs.status in [200, 204, 201]:
                data = await rs.json()
                if data["uses"] == data["max_uses"]:
                    colors.warning(f"Already Claimed -> {promocode}")
                    save("output/claimed.txt", f"https://discord.com/billing/promotions/{promocode}")
                    claimed_count += 1
                else:
                    try:
                        now = datetime.datetime.utcnow()
                        exp_at = data["expires_at"].split(".")[0]
                        parsed = parser.parse(exp_at)
                        days = abs((now - parsed).days)
                        title = data["promotion"]["inbound_header_text"]
                    except Exception as e:
                        print(e)
                        exp_at = "Failed To Fetch!"
                        days = "Failed To Parse!"
                        title = "Failed To Fetch!"
                    colors.success(f"Valid -> {promocode} | Days Left: {days} | Expires At: {exp_at} | Title: {title}")
                    save("output/valid.txt", f"https://discord.com/billing/promotions/{promocode}")
                    valid_count += 1
            elif rs.status == 429:
                try:
                    deta = await rs.json()
                except Exception:
                    colors.warning("IP Banned.")
                    return
                timetosleep = deta["retry_after"]
                colors.warning(f"Rate Limited For {timetosleep} Seconds!")
                await asyncio.sleep(timetosleep)
                await check(promocode)
            else:
                colors.error(f"Invalid Code -> {promocode}")

async def start():
    global total_count, valid_count, claimed_count
    total_count = 0
    valid_count = 0
    claimed_count = 0
    with open("input/links.txt", "r+") as f:
        codes = f.readlines()
        f.seek(0)
        f.truncate()
        for promo in codes:
            code = promo.strip().replace('https://discord.com/billing/promotions/', '').replace('https://promos.discord.gg/', '').replace('/', '')
            await check(code)
            total_count += 1
            await asyncio.sleep(delay)

if __name__ == "__main__":
    delay = 1
    token = "" 

    if not token:
        colors.error("Token is missing. Please set the token.")
        sys.exit(1)

    if not os.path.exists("input/links.txt"):
        colors.error("File 'links.txt' not found!")
        sys.exit(1)

    auth = {"Authorization": token}

    loop = asyncio.new_event_loop()
    loop.run_until_complete(start())
    print(f"[-] Total Codes Checked -> {total_count}")
    print(f"[+] Valid Codes -> {valid_count}")
    print(f"[!] Claimed Codes -> {claimed_count}")

    new_title = f"Promotion Checker - Total: {total_count} | Valid: {valid_count} | Claimed: {claimed_count}"
    set_window_title(new_title)
