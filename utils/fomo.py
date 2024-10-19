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

class Fomo:
    def __init__(self, thread: int, account: str, proxy : str):
        self.thread = thread
        self.name = account
        if self.thread % 5 == 0:
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

        headers = {
            'accept': 'application/json',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://miniapp.dropstab.com',
            'priority': 'u=1, i',
            'referer': 'https://miniapp.dropstab.com/',
            'sec-ch-ua': '"Google Chrome";v="122", "Not=A?Brand";v="8", "Chromium";v="122"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': UserAgent(os='android').random}
        
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
  
