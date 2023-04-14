import asyncio
import os
import re
import time
from io import BytesIO

from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from .bot import bot_start, msg_end, Chat
from .lib.cons import *
from .lib.utils import load_preset, rules, getThis
from webuiapi import webuiapi

cfg = asyncio.run(bot_start())
config = cfg['cfg']

BotUse = config['Chat']['defaultAI']


@event_postprocessor
async def postprocessor():
    await msg_end()


L_webuiapi = asyncio.Lock()
chat = on_command(config['Command']['chat'][1:], priority=1, block=True)
bing = on_command(config['Command']['bing'][1:], priority=1, block=True)
switchAI = on_command(config['Command']['switchAI'][1:], priority=1, block=True)
switch = on_command(config['Command']['switch'][1:], priority=1, block=True)
switchPreset = on_command(config['Command']['switchPreset'][1:], priority=1, block=True)
tag = on_command(config['Command']['tag'][1:], priority=1, block=True)
SD_webui = on_command(config['Command']['SD_webui'][1:], priority=1, block=True)
MSG = on_message(rule=to_me(), priority=2, block=True)


@MSG.handle()
async def _(foo: Bot, event: GuildMessageEvent | GroupMessageEvent | PrivateMessageEvent):
    if not rules('msg', config, event): return

    def asChat():
        global BotUse
        if BotUse in cfg:
            return BotUse
        else:
            if 'chatgpt-api' in cfg: return 'chatgpt-api'
            if 'chatgpt' in cfg: return 'chatgpt'
            if 'bing' in cfg: return 'bing'
            error('/chat', '你没有任何chatgpt接入')
            return False

    message = str(event.message)
    BOT = asChat()
    if len(message) == 0: return
    if BOT:
        info(BOT, '对话: ' + message)
        await Chat(event, foo, BOT, message)


@chat.handle()
async def _(foo: Bot, event: GuildMessageEvent | GroupMessageEvent | PrivateMessageEvent, args: Message = CommandArg()):
    if not rules('chat', config, event): return

    def asChatGPT():
        global BotUse
        if 'chatgpt' in BotUse:
            return BotUse
        else:
            if 'chatgpt-api' in cfg:
                return 'chatgpt-api'
            elif 'chatgpt' in cfg:
                return 'chatgpt'
            else:
                error('/chat', '你没有任何chatgpt接入')
        return False

    message = args.extract_plain_text()
    if len(message) == 0: return
    BOT = asChatGPT()
    if BOT:
        info(BOT, '对话: ' + message)
        await Chat(event, foo, BOT, message)


@bing.handle()
async def _(foo: Bot, event: GuildMessageEvent | GroupMessageEvent | PrivateMessageEvent, args: Message = CommandArg()):
    if not rules('bing', config, event): return

    def asBing():
        if 'bing' not in cfg:
            error('bing', '你没有接入bing')
            return True
        return 'bing'

    if asBing():
        message = args.extract_plain_text()
        if len(message) == 0: return
        info('bing', '对话: ' + message)
        await Chat(event, foo, 'bing', message)


@tag.handle()
async def _(foo: Bot, event: GuildMessageEvent | GroupMessageEvent | PrivateMessageEvent, args: Message = CommandArg()):
    if not rules('tag', config, event): return
    def asChat():
        global BotUse
        if BotUse in cfg:
            return BotUse
        else:
            if 'chatgpt-api' in cfg: return 'chatgpt-api'
            if 'chatgpt' in cfg: return 'chatgpt'
            if 'bing' in cfg: return 'bing'
            error('/chat', '你没有任何chatgpt接入')
            return False

    BOT = asChat()
    message = args.extract_plain_text()
    if len(message) == 0: return
    if BOT:
        info(BOT, '对话: ' + message)
        await Chat(event, foo, BOT, message, noStream=True, p='tag')


@SD_webui.handle()
async def _(foo: Bot, event: GuildMessageEvent | GroupMessageEvent | PrivateMessageEvent, args: Message = CommandArg()):
    if not rules('SD_webui', config, event): return
    def asChat():
        global BotUse
        if BotUse in cfg:
            return BotUse
        else:
            if 'chatgpt-api' in cfg: return 'chatgpt-api'
            if 'chatgpt' in cfg: return 'chatgpt'
            if 'bing' in cfg: return 'bing'
            error('/chat', '你没有任何chatgpt接入')
            return False

    BOT = asChat()
    message = args.extract_plain_text()
    if len(message) == 0: return
    if BOT:
        info(BOT, '对话: ' + message)
        prompt = await Chat(event, foo, BOT, message, p='tag', noOut=True)
        sd = config['Stable-Diffusion']
        ip = sd['api_host']
        DIR = sd['save_path']
        info('Stable-Diffusion', '开始询问 api : ' + ip)
        ip = ip.split(':')

        api = webuiapi.WebUIApi(host=ip[0], port=ip[1])  # type: ignore

        task = asyncio.to_thread(api.txt2img(
            prompt=prompt,
            negative_prompt=sd['negative_prompt'],
            steps=sd['step'],
        ))
        async with L_webuiapi:
            result = await task
        image = result.image
        success('Stable-Diffusion', '返回图片')
        buffered = BytesIO()
        if DIR == '':
            DIR = '.'
            ID = 'OUT'
        else:
            lt = time.localtime(time.time())
            ID = time.strftime("%Y_%m_%d_%H%M%S", lt)
        image.save(f"{DIR}/{ID}.png", "PNG")
        image.save(buffered, format="PNG")
        await foo.send(event, MessageSegment.image(buffered), reply_message=config['Chat']['reply'])
        return


@switchAI.handle()
async def _(foo: Bot, event: Event, args: Message = CommandArg()):
    if not rules('switchAI', config, event): return
    use = args.extract_plain_text()
    if len(args) == 0: return
    if use in config:
        global BotUse
        BotUse = use
        await switchAI.send('已切换到 ' + BotUse)
        suc('切换AI', BotUse)
    else:
        await switchAI.send('AI不存在')
        warn("切换AI", f'AI不存在 , {use} is not in: {cfg}')


@switch.handle()
async def _(event: Event, args: Message = CommandArg()):
    global config
    if not rules('switch', config, event): return
    args = args.extract_plain_text().split(' ')
    if len(args) == 0: return
    if args[0] == '群聊': args = ['Function','Group','groups',args[-1]]
    if args[0] == '私聊': args = ['Function','Private','member',args[-1]]
    if args[0] == '频道': args = ['Function', 'Guild', 'guilds', args[-1]]
    path = args[:-2]
    isOwner = (config['Bot']['owner'] == event.get_user_id())
    if config['Bot']['switchConfigEval'] is False and not isOwner:
        return warn('/switch', '无权限更改')
    if args[0] == 'Bot' and not isOwner:
        return warn('/switch', '无权限更改 Bot')
    now = config
    for i in path:
        now = now[i]
    if args[-1] in ['True', 'true', '1', 'on']:
        data = True
    elif args[-1] in ['False', 'false', '0', 'off']:
        data = False
    elif args[-1] == '=this':
        data = [getThis(event)]
    elif args[-1] == '*':
        data = ['*']
    elif args[-1] == '+this':
        if '*' in now[args[-2]]:
            now[args[-2]].remove('*')
        now[args[-2]].append(getThis(event))
        data = now[args[-2]]
    elif args[-1] == '-this':
        try:
            now[args[-2]].remove(getThis(event))
        except:
            return await switch.send('.'.join(args[:-1]) + '中没有' + str(getThis(event)))
        data = now[args[-2]]
    else:
        data = args[-1]
    if not isinstance(now[args[-2]], (int, float, str, bool, list)):
        rep = {"'(access_token)': '[^’]*'": r"[$1]",
               "'(api_key)': '[^']*'": r"[$2]",
               "'(api_host)': '[^']*'": r"[$3]",
        }
        result = re.sub("|".join(rep.keys()), '[隐藏]', str(now[args[-2]]))
        return await switch.send(result)
    now[args[-2]] = data
    config.write()
    print(config['Chat'])
    await switch.send('.'.join(args[:-1]) + '已改为' + str(data))


@switchPreset.handle()
async def _(event: Event, args: Message = CommandArg()):
    global config
    if not rules('switchPreset', config, event): return
    args = args.extract_plain_text()
    if len(args) == 0: return
    isOwner = (config['Bot']['owner'] == event.get_user_id())
    if config['Bot']['switchConfigEval'] is False and not isOwner:
        return warn('/switch', '无权限更改')
    if args in config['preset']:
        config['runtime']['preset'] = config['preset'][args]
        path = config['Chat']['presets_dir'] + '/' + config['preset'][args]
        # config['runtime']['preset'] = await load_preset(config['Chat']['presets_dir'], config['preset'][args])
        await switchPreset.send(f'已切换到{path}')
        config.write()
    elif args in ['None', 'none', '0', 'false', 'False', 'default']:
        config['runtime']['preset'] = ''
        config.write()
    else:
        await switchPreset.send('预设不存在，请在配置中注册')
        return error('/switchPreset', '预设不存在，请在配置中注册')
