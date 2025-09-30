import os
import aiohttp
import asyncio
import tasksio
import random
from colorama import Fore, Style
from dateutil import parser
import datetime

claimed_count = 0
valid_count = 0
total_count = 0
duplicate_count = 0

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def sort_(file, item):
    with open(file, "r") as f:
        beamed = f.read().split("\n")
        try:
            beamed.remove("")
        except:
            pass
        return item in beamed

def save(file, data):
    if not sort_(file, data):
        with open(file, "a+") as f:
            f.write(data + "\n")
    else:
        print(f"Duplicate Found -> {data}")

def remove_code(file, code):
    try:
        with open(file, "r") as f:
            lines = f.read().splitlines()
        with open(file, "w") as f:
            for line in lines:
                if code not in line:
                    f.write(line + "\n")
    except Exception as e:
        print(f"Error removing used code: {e}")

async def check(promocode, index, total, timeout):
    global claimed_count, valid_count
    print(f"{Fore.CYAN}Checking link {index} of {total}{Style.RESET_ALL}")

    connector = aiohttp.TCPConnector(ssl=False)
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout), connector=connector) as cs:
            async with cs.get(
                f"https://ptb.discord.com/api/v10/entitlements/gift-codes/{promocode}"
            ) as rs:
                if rs.status in [200, 201, 204]:
                    data = await rs.json()
                    if data["uses"] == data["max_uses"]:
                        print(f"{Fore.RED}Already Claimed -> {promocode}{Style.RESET_ALL}")
                        save("claimed.txt", f"https://discord.com/billing/promotions/{promocode}")
                        claimed_count += 1
                    else:
                        try:
                            now = datetime.datetime.utcnow()
                            exp_at = data["expires_at"].split(".")[0]
                            parsed = parser.parse(exp_at)
                            days = abs((now - parsed).days)
                            title = data["promotion"]["inbound_header_text"]
                        except:
                            exp_at = days = title = "Unknown"
                        print(f"{Fore.GREEN}Valid -> {promocode} | Days Left: {days} | Title: {title}{Style.RESET_ALL}")
                        save("valid.txt", f"https://discord.com/billing/promotions/{promocode}")
                        valid_count += 1
                elif rs.status == 429:
                    deta = await rs.json()
                    timetosleep = deta.get("retry_after", 5)
                    print(f"{Fore.YELLOW}Rate Limited ({timetosleep}s)...{Style.RESET_ALL}")
                    await asyncio.sleep(timetosleep)
                    await check(promocode, index, total, timeout)
                else:
                    print(f"{Fore.MAGENTA}Invalid Code -> {promocode}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.LIGHTBLACK_EX}Failed to check code {promocode} -> {e}{Style.RESET_ALL}")
    finally:
        remove_code("promotions.txt", promocode)

async def start():
    global total_count, valid_count, claimed_count, duplicate_count

    clear()

    try:
        timeout = float(input("Enter timeout for each request (e.g., 10): "))
    except ValueError:
        timeout = 10.0

    try:
        workers = int(input("Enter number of links to check simultaneously: "))
        if workers < 1:
            workers = 5
    except ValueError:
        workers = 5

    try:
        raw_codes = open("promotions.txt", "r").read().split("\n")
        raw_codes = [x for x in raw_codes if x.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}promotions.txt not found!{Style.RESET_ALL}")
        return

    seen = set()
    unique_codes = []
    for code in raw_codes:
        cleaned = code.replace('https://discord.com/billing/promotions/', '').replace('https://promos.discord.gg/', '').replace('/', '').strip()
        if cleaned not in seen and cleaned:
            seen.add(cleaned)
            unique_codes.append(cleaned)
        else:
            duplicate_count += 1

    if duplicate_count > 0:
        print(f"{Fore.YELLOW}Found {duplicate_count} duplicate links, checking each unique link only once.{Style.RESET_ALL}")

    total = len(unique_codes)

    async with tasksio.TaskPool(workers) as pool:
        for i, code in enumerate(unique_codes, start=1):
            await pool.put(check(code, i, total, timeout))
            total_count += 1
            await asyncio.sleep(random.uniform(1, 2))

if __name__ == "__main__":
    asyncio.run(start())
    print(f"{Fore.BLUE}[-] Total Codes Checked -> {total_count}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[+] Valid Codes -> {valid_count}{Style.RESET_ALL}")
    print(f"{Fore.RED}[!] Claimed Codes -> {claimed_count}{Style.RESET_ALL}")
