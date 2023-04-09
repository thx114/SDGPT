from nonebot import get_driver, require


from .bot import info,error,warn
from nonebot.plugin import on_command , on_message , on
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters import Message
from nonebot.plugin import PluginMetadata

from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.params import CommandArg
from nonebot.rule import to_me
from .bot import Chat,Bing,text2image,startup,Chat_api

from dotenv import dotenv_values, load_dotenv
config =dotenv_values(".cfg")

__plugin_meta__ = PluginMetadata(
    name="ChatBot",
    description="ChatBot for NoneBot : 链接 ChatGPT / Bing / Stable-Diffusion",
    usage="ChatGPT Bing聊天, gpt解析自然语言转Stable-Diffusion生成图像",
    extra={},
)

GuildMessageEvent = require('nonebot_plugin_guild_patch').GuildMessageEvent

driver = get_driver()

@driver.on_startup
async def do_something():
    global Presets
    global botList  
    global cfg
    info('fthxbot','startup')
    CFGdata = await startup()
    Presets = CFGdata['Presets']
    botList = CFGdata['botList']
    cfg = CFGdata['cfg']
    

chat = on_command('chat')
@chat.handle()
async def _(event:GuildMessageEvent|GroupMessageEvent,args: Message = CommandArg()):
    message = args.extract_plain_text()
    await Chat(chat,message)
    if type(event) == GuildMessageEvent:await Bing(bing,message)
    elif type(event) == GroupMessageEvent:await Bing(bing,message,0)

bing = on_command('bing')
@bing.handle()
async def _(event:GuildMessageEvent|GroupMessageEvent,args: Message = CommandArg()):
    message = args.extract_plain_text()
    if type(event) == GuildMessageEvent:await Bing(bing,message)
    elif type(event) == GroupMessageEvent:await Bing(bing,message,0)
        


msg = on_message(rule=to_me())
@msg.handle()
async def _(event:GuildMessageEvent|GroupMessageEvent):
    global ChatUse
    message = str(event.message)
    All = {
        'ChatGPT' : Chat,
        'Bing' : Bing,
        'ChatGPT_api' : Chat_api,
    }
    if cfg['defaultAI'] and type(cfg['defaultAI'])==str:  
        if cfg.defaultAI in botList:
            try : not ChatUse # type: ignore
            except : ChatUse  = All[cfg['defaultAI']]
        else: 
            return error('Config','你配置的 defaultAI 没有被接入')
    else: 
        return error('Config','你没有配置 defaultAI')

    if type(event) == GuildMessageEvent:await ChatUse(msg,message) # type: ignore
    elif type(event) == GroupMessageEvent:await ChatUse(msg,message,0) # type: ignore


tag = on_command('tag')
@tag.handle()
async def _(args: Message = CommandArg()):
    message = args.extract_plain_text()
    await Chat(tag,Presets['PromptGenerator'] + message,0)


ai = on_command('ai')
@ai.handle()
async def _(args: Message = CommandArg()):
    message = args.extract_plain_text()
    text = await Chat(tag,Presets['PromptGenerator'] + message,2)
    img_bytes = await text2image(ai,text)
    await ai.reject(MessageSegment.image(file=img_bytes,cache=False))

test = on_command('test')
@test.handle()
async def _():
    await test.send('test')

chatC = on_command('切换AI')
@chatC.handle()
async def _(args: Message = CommandArg()):
    All = {
        'ChatGPT' : Chat,
        'Bing' : Bing,
        'ChatGPT_api' : Chat_api,
    }
    global chatUse
    message = args.extract_plain_text()
    if message in botList:
        chatUse = All[message]
        await chatC.send(f'已切换到 {message}')
    else: 
        await chatC.send('AI没有配置 或 AI不存在')

