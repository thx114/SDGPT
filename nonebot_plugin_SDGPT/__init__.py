from nonebot import get_driver, require


from .bot import info,error,warn,err
from nonebot.plugin import on_command , on_message , on
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters import Message
from nonebot.plugin import PluginMetadata

from nonebot.adapters.onebot.v11.event import GroupMessageEvent,PrivateMessageEvent
from nonebot.params import CommandArg
from nonebot.rule import to_me
from .bot import Chat,Bing,text2image,startup,Chat_api,AIcheck

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
    global ChatUse
    info('fthxbot','startup')
    CFGdata = await startup()
    Presets = CFGdata['Presets']
    botList = CFGdata['botList']
    cfg = CFGdata['cfg']
    ChatUse = CFGdata['ChatUse']

    

chat = on_command('chat', priority=1, block=True)
@chat.handle()
async def _(event:GuildMessageEvent | GroupMessageEvent | PrivateMessageEvent,args: Message = CommandArg()):
    global ChatUse
    message = args.extract_plain_text()
    if ChatUse == Bing:
        if await AIcheck(Chat_api):
            ChatUse = Chat_api
        elif await AIcheck(Chat):
            ChatUse = Chat
    if type(event) == GuildMessageEvent:await ChatUse(bing,message) # type: ignore
    else: await ChatUse(bing,message,0) # type: ignore

bing = on_command('bing', priority=1, block=True)
@bing.handle()
async def _(event:GuildMessageEvent|GroupMessageEvent|PrivateMessageEvent,args: Message = CommandArg()):
    message = args.extract_plain_text()
    if type(event) == GuildMessageEvent:await Bing(bing,message)
    else:await Bing(bing,message,0)
        

msg = on_message(rule=to_me(), priority=2, block=True)
@msg.handle()
async def _(event:GuildMessageEvent|GroupMessageEvent|PrivateMessageEvent):
    global ChatUse
    message = str(event.message)
    if type(event) == GuildMessageEvent:await ChatUse(msg,message) # type: ignore
    else:await ChatUse(msg,message,0) # type: ignore


tag = on_command('tag', priority=1, block=True)
@tag.handle()
async def _(args: Message = CommandArg()):
    message = args.extract_plain_text()
    global ChatUse
    await ChatUse(tag,Presets['PromptGenerator'] + message,0) # type: ignore


ai = on_command('ai', priority=1, block=True)
@ai.handle()
async def _(args: Message = CommandArg()):
    message = args.extract_plain_text()
    global ChatUse
    text = await ChatUse(tag,Presets['PromptGenerator'] + message,2) # type: ignore
    img_bytes = await text2image(ai,text)
    await ai.reject(MessageSegment.image(file=img_bytes,cache=False))

chatC = on_command('切换AI', priority=1, block=True)
@chatC.handle()
async def _(args: Message = CommandArg()):
    All = {
        'ChatGPT' : Chat,
        'Bing' : Bing,
        'ChatGPT_api' : Chat_api,
    }
    message = args.extract_plain_text()
    global ChatUse
    ChatUse = All[message]
    if not await AIcheck(ChatUse) :
        err('ChatUse','AI不存在')
        return await chatC.send('AI不存在')
    await chatC.send(f'已切换到 {message}')

