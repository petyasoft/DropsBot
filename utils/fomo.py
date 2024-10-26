from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName

from urllib.parse import unquote
from utils.core import logger
from fake_useragent import UserAgent
from pyrogram import Client
from data import config
from aiohttp_socks import ProxyConnector

import aiohttp
import asyncio
import random
import json
import re
import os

class Fomo:
    def __init__(self, thread: int, account: str, proxy : str):
        self.thread = thread
        self.name = account
        if self.thread % 3 == 0:
            self.ref = 'ref_W5MFB'
        else:
            self.ref = config.REF_CODE
        if proxy:
            proxy_client = {
                "scheme": config.PROXY_TYPE,
                "hostname": proxy.split(':')[0],
                "port": int(proxy.split(':')[1]),
                "username": proxy.split(':')[2],
                "password": proxy.split(':')[3],
            }
            self.client = Client(name=account, api_id=config.API_ID, api_hash=config.API_HASH, workdir=config.WORKDIR, proxy=proxy_client)
        else:
            self.client = Client(name=account, api_id=config.API_ID, api_hash=config.API_HASH, workdir=config.WORKDIR)
                
        if proxy:
            self.proxy = f"{config.PROXY_TYPE}://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"
        else:
            self.proxy = None
        
        connector = ProxyConnector.from_url(self.proxy) if proxy else aiohttp.TCPConnector(verify_ssl=False)
        
        ua = self.set_useragent()
        headers = {
            'accept': 'application/json',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://miniapp.dropstab.com',
            'priority': 'u=1, i',
            'referer': 'https://miniapp.dropstab.com/',
            'sec-ch-ua': f'"Google Chrome";v="{self.extract_chrome_version(ua)}", "Not=A?Brand";v="8", "Chromium";v="{self.extract_chrome_version(ua)}"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua}
        
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=connector)

    async def main(self):
        await asyncio.sleep(random.uniform(*config.ACC_DELAY))
        logger.info(f"main | Thread {self.thread} | {self.name} | PROXY : {self.proxy}")
        while True:
            try:
                login = await self.login()
                if not login:
                    await self.session.close()
                    return 0
                await self.daily_bonus()
                await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
            
                ref = (await self.ref_info())
                if ref['availableToClaim']!=0:
                    await self.claim_ref_reward()
                    await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                    
                if not login['user']['welcomeBonusReceived']:
                    (await self.welcome_bonus())
                    await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                    
                quests = await self.get_quests()
                for type_quests in quests:
                    if type_quests['name'] == 'Refs':
                        continue
                    for quest in type_quests['quests']:
                        if quest['claimAllowed'] == False and quest['status'] == "NEW":
                            status = await self.veify_quest(quest_id=quest['id'])
                            await asyncio.sleep(random.uniform(*config.QUEST_SLEEP))
                        elif quest['claimAllowed'] == True and quest['status'] == "NEW":
                            status = await self.claim_quest(quest_id=quest['id'])
                            if status['status'] == 'OK':
                                logger.success(f"main | Thread {self.thread} | {self.name} | Заклеймил квест с id : {quest['id']} и получил {quest['reward']} $DPS")
                            await asyncio.sleep(random.uniform(*config.QUEST_SLEEP))
                
                orders = (await self.get_orders())
                score = orders['totalScore']
                
                for period in orders['periods']:
                    if period['period']['unlockThreshold'] <= score and period['order'] == None:
                        coins = await self.get_coins()
                        coin = random.choice(coins)
                        stats = await self.coin_stats(coin_id=coin['id'])
                        
                        long = stats['long']
                        short = stats['short']
                        if long >= short:
                            (await self.create_order(coinId = coin['id'], periodId = period['period']['id'], short = False))
                            logger.info(f"main | Thread {self.thread} | {self.name} | Создал ордер LONG по монете {coin['symbol']} на {period['period']['hours']} часов")
                        else:
                            (await self.create_order(coinId = coin['id'], periodId = period['period']['id'], short = True))
                            logger.info(f"main | Thread {self.thread} | {self.name} | Создал ордер SHORT по монете {coin['symbol']} на {period['period']['hours']} часов")
                    elif period['order'] != None and period['order']['status'] == 'NOT_WIN':
                        await self.check_order(order_id=period['order']['id'])
                        logger.info(f"main | Thread {self.thread} | {self.name} | Не выиграл в ставке на {period['period']['hours']} часов")
                    elif period['order'] != None and period['order']['status'] == 'CLAIM_AVAILABLE':
                        await self.claim_order(order_id=period['order']['id'])
                        logger.success(f"main | Thread {self.thread} | {self.name} | Выиграл в ставке : {period['order']['reward']}")
                    await asyncio.sleep(random.uniform(*config.GAME_SLEEP))

                orders = (await self.get_orders())
                score = orders['totalScore']
                
                for period in orders['periods']:
                    if period['period']['unlockThreshold'] <= score and period['order'] == None:
                        coins = await self.get_coins()
                        coin = random.choice(coins)
                        stats = await self.coin_stats(coin_id=coin['id'])
                        
                        long = stats['long']
                        short = stats['short']
                        if long >= short:
                            (await self.create_order(coinId = coin['id'], periodId = period['period']['id'], short = False))
                            logger.info(f"main | Thread {self.thread} | {self.name} | Создал ордер LONG по монете {coin['symbol']} на {period['period']['hours']} часов")
                        else:
                            (await self.create_order(coinId = coin['id'], periodId = period['period']['id'], short = True))
                            logger.info(f"main | Thread {self.thread} | {self.name} | Создал ордер SHORT по монете {coin['symbol']} на {period['period']['hours']} часов")
                        await asyncio.sleep(random.uniform(*config.GAME_SLEEP))

                logger.info(f"main | Thread {self.thread} | {self.name} | круг окончен")
                await asyncio.sleep(random.uniform(*config.BIG_SLEEP))
            except Exception as err:
                logger.error(f"main | Thread {self.thread} | {self.name} | {err}")
    
    async def daily_bonus(self):
        try:
            response = await self.session.post('https://api.miniapp.dropstab.com/api/bonus/dailyBonus')
            response = await response.json()
            if (response)['result']:
                logger.success(f"daily_bonus | Thread {self.thread} | {self.name} | Day {response['streaks']} | Claim : {response['bonus']}")
            return response
        except Exception as err:
            logger.error(f"daily_bonus | Thread {self.thread} | {self.name} | {err}")
    
    async def welcome_bonus(self):
        try:
            response = await self.session.post('https://api.miniapp.dropstab.com/api/bonus/welcomeBonus')
            if (await response.json())['result']:
                logger.success(f"welcome_bonus | Thread {self.thread} | {self.name} | Забрал стартовый бонус")
            return await response.json()
        except Exception as err:
            logger.error(f"welcome_bonus | Thread {self.thread} | {self.name} | {err}")
            
    async def get_quests(self):
        try:
            response = await self.session.get(f'https://api.miniapp.dropstab.com/api/quest')
            return await response.json()
        except Exception as err:
            logger.error(f"get_quests | Thread {self.thread} | {self.name} | {err}")
    
    async def veify_quest(self, quest_id : int):
        try:
            response = await self.session.put(f'https://api.miniapp.dropstab.com/api/quest/{quest_id}/verify')
            return await response.json()
        except Exception as err:
            logger.error(f"veify_quest | Thread {self.thread} | {self.name} | {err}")
            
    async def claim_quest(self,quest_id : int):
        try:
            response = await self.session.put(f'https://api.miniapp.dropstab.com/api/quest/{quest_id}/claim')
            return await response.json()
        except Exception as err:
            logger.error(f"claim_quest | Thread {self.thread} | {self.name} | {err}")

    async def claim_ref_reward(self):
        try:
            response = await self.session.post('https://api.miniapp.dropstab.com/api/refLink/claim')
            logger.success(f"claim_ref_rewar | Thread {self.thread} | {self.name} | Claim referral reward")
            return await response.json()
        except Exception as err:
            logger.error(f"claim_ref_reward | Thread {self.thread} | {self.name} | {err}")
    
    async def ref_info(self):
        try:
            response = await self.session.get('https://api.miniapp.dropstab.com/api/refLink')
            return await response.json()
        except Exception as err:
            logger.error(f"ref_info | Thread {self.thread} | {self.name} | {err}")
    
    async def get_orders(self):
        try:
            response = await self.session.get('https://api.miniapp.dropstab.com/api/order')
            return await response.json()
        except Exception as err:
            logger.error(f"get_orders | Thread {self.thread} | {self.name} | {err}")
    
    async def get_coins(self):
        try:
            response = await self.session.get('https://api.miniapp.dropstab.com/api/order/coins')
            return await response.json()
        except Exception as err:
            logger.error(f"get_coins | Thread {self.thread} | {self.name} | {err}")
    
    async def coin_stats(self, coin_id):
        try:
            response = await self.session.get(f'https://api.miniapp.dropstab.com/api/order/coinStats/{coin_id}')
            return await response.json()
        except Exception as err:
            logger.error(f"coin_stats | Thread {self.thread} | {self.name} | {err}")
    
    async def create_order(self, coinId, periodId, short):
        try:
            json_data = {
                'coinId': coinId,
                'short': short,
                'periodId': periodId,
            }

            response = await self.session.post('https://api.miniapp.dropstab.com/api/order', json=json_data)
            return await response.json()
        except Exception as err:
            logger.error(f"create_order | Thread {self.thread} | {self.name} | {err}")
    
    async def check_order(self, order_id):
        try:
            response = await self.session.put(f'https://api.miniapp.dropstab.com/api/order/{order_id}/markUserChecked')
            return await response.json()
        except Exception as err:
            logger.error(f"check_order | Thread {self.thread} | {self.name} | {err}")
    
    async def claim_order(self, order_id):
        try:
            response = await self.session.put(f'https://api.miniapp.dropstab.com/api/order/{order_id}/claim')
            return await response.json()
        except Exception as err:
            logger.error(f"claim_order | Thread {self.thread} | {self.name} | {err}")
        
    async def login(self):
        try:
            tg_web_data = await self.get_tg_web_data()
            if tg_web_data == False:
                return False
            json_data = {
                'webAppData': tg_web_data
            }

            response = await self.session.post('https://api.miniapp.dropstab.com/api/auth/login', json=json_data)
            response = await response.json()
            if "jwt" in response:
                token = response.get("jwt").get("access").get("token")
                self.session.headers['authorization'] = f"Bearer {token}"
                
                json_data = {
                    'code': self.ref[4:],
                }
                if response.get('user').get('usedRefLinkCode')==None:
                    await self.session.put('https://api.miniapp.dropstab.com/api/user/applyRefLink',json=json_data)
                return response
            return False
        except Exception as err:
            logger.error(f"login | Thread {self.thread} | {self.name} | {err}")
            return False

    async def get_tg_web_data(self):
        async with self.client:
            try:
                web_view = await self.client.invoke(RequestAppWebView(
                    peer=await self.client.resolve_peer('fomo'),
                    app=InputBotAppShortName(bot_id=await self.client.resolve_peer('fomo'), short_name="app"),
                    platform='android',
                    write_allowed=True,
                    start_param=self.ref
                ))

                auth_url = web_view.url
            except Exception as err:
                logger.error(f"get_tg_web_data | Thread {self.thread} | {self.name} | {err}")
                if 'USER_DEACTIVATED_BAN' in str(err):
                    logger.error(f"login | Thread {self.thread} | {self.name} | USER BANNED")
                    return False
            return unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
    
    def set_useragent(self):
        try:
            file_path = f"data/useragents.json"

            if not os.path.exists(file_path):
                data = {self.name: self.generate_user_agent()}
                with open(file_path, 'w', encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)

                return data[self.name]
            else:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        data = json.loads(content)

                    if self.name in data:
                        return data[self.name]

                    else:
                        data[self.name] = self.generate_user_agent()

                        with open(file_path, 'w', encoding='utf-8') as file:
                            file.write(json.dumps(data, ensure_ascii=False, indent=4))

                        return data[self.name]
                except json.decoder.JSONDecodeError:
                    logger.error(f"useragent | Thread {self.thread} | {self.name} | syntax error in UserAgents json file!")
                    return 'Mozilla/5.0 (Linux; Android 5.1.1; SAMSUNG SM-G920FQ Build/LRX22G) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/50.0.1819.308 Mobile Safari/601.9'

        except Exception as err:
            logger.error(f"useragent | Thread {self.thread} | {self.name} | {err}")
            return 'Mozilla/5.0 (Linux; Android 5.1.1; SAMSUNG SM-G920FQ Build/LRX22G) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/50.0.1819.308 Mobile Safari/601.9'
    

    def extract_chrome_version(self, user_agent):
        match = re.search(r'Chrome/(\d+\.\d+\.\d+\.\d+)', user_agent)
        if match:
            return match.group(1).split('.')[0]
        return 55
    
    def generate_user_agent(self):
        chrome_versions = [
            "110.0.5481.100", "110.0.5481.104", "110.0.5481.105", 
            "110.0.5481.106", "110.0.5481.107", "110.0.5481.110", 
            "110.0.5481.111", "110.0.5481.115", "110.0.5481.118", 
            "110.0.5481.120", "111.0.5563.62", "111.0.5563.64", 
            "111.0.5563.66", "111.0.5563.67", "111.0.5563.68", 
            "112.0.5615.49", "112.0.5615.51", "112.0.5615.53", 
            "112.0.5615.54", "112.0.5615.55", "113.0.5672.63", 
            "113.0.5672.64", "113.0.5672.66", "113.0.5672.67", 
            "113.0.5672.68", "114.0.5735.90", "114.0.5735.91", 
            "114.0.5735.92", "114.0.5735.93", "114.0.5735.94", 
            "115.0.5790.102", "115.0.5790.103", "115.0.5790.104", 
            "115.0.5790.105", "115.0.5790.106", "116.0.5845.97", 
            "116.0.5845.98", "116.0.5845.99", "116.0.5845.100", 
            "116.0.5845.101", "117.0.5938.62", "117.0.5938.63", 
            "117.0.5938.64", "117.0.5938.65", "117.0.5938.66", 
            "118.0.5993.90", "118.0.5993.91", "118.0.5993.92", 
            "118.0.5993.93", "118.0.5993.94", "119.0.6049.43", 
            "119.0.6049.44", "119.0.6049.45", "119.0.6049.46", 
            "119.0.6049.47", "120.0.6138.72", "120.0.6138.73", 
            "120.0.6138.74", "120.0.6138.75", "120.0.6138.76", 
            "121.0.6219.29", "121.0.6219.30", "121.0.6219.31", 
            "121.0.6219.32", "121.0.6219.33", "122.0.6308.16", 
            "122.0.6308.17", "122.0.6308.18", "122.0.6308.19", 
            "122.0.6308.20", "123.0.6374.92", "123.0.6374.93", 
            "123.0.6374.94", "123.0.6374.95", "123.0.6374.96", 
            "124.0.6425.5", "124.0.6425.6", "124.0.6425.7", 
            "124.0.6425.8", "124.0.6425.9", "125.0.6544.32", 
            "125.0.6544.33", "125.0.6544.34", "125.0.6544.35", 
            "125.0.6544.36", "126.0.6664.99", "126.0.6664.100", 
            "126.0.6664.101", "126.0.6664.102", "126.0.6664.103", 
            "127.0.6780.73", "127.0.6780.74", "127.0.6780.75", 
            "127.0.6780.76", "127.0.6780.77", "128.0.6913.45", 
            "128.0.6913.46", "128.0.6913.47", "128.0.6913.48", 
            "128.0.6913.49", "129.0.7026.88", "129.0.7026.89", 
            "129.0.7026.90", "129.0.7026.91", "129.0.7026.92"
        ]

        
        android_devices = [
            "SAMSUNG SM-N975F", "SAMSUNG SM-G973F", "SAMSUNG SM-G991B", 
            "SAMSUNG SM-G996B", "SAMSUNG SM-A325F", "SAMSUNG SM-A525F", 
            "Xiaomi Redmi Note 11", "POCO X3 Pro", "POCO F3", 
            "Xiaomi Mi 11", "Samsung Galaxy S21", "Samsung Galaxy S22", 
            "Samsung Galaxy S23", "Samsung Galaxy A52", "Samsung Galaxy A53", 
            "Samsung Galaxy M32", "Xiaomi 12", "OnePlus 9", 
            "OnePlus Nord 2", "Realme GT", "Nokia G50",
            "Huawei P40 Lite", "Honor 50"
        ]

        
        windows_versions = [
            "10.0", "11.0", "12.0"
        ]
        
        platforms = [
            f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",
            f"Mozilla/5.0 (Linux; Android {random.randint(11, 13)}; {random.choice(android_devices)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Mobile Safari/537.36"
        ]
        
        return random.choice(platforms)
    
