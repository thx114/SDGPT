import glob
from io import BytesIO
import json
import os
import sys
import time
import re
from nonebot import get_driver
from nonebot.log import logger_id
from nonebot.log import default_format, default_filter

from nonebot import logger
import webuiapi
from revChatGPT.V1 import Chatbot as chatGPT
from revChatGPT.V3 import Chatbot as chatGPT_api
from EdgeGPT import Chatbot as bing
logger.remove(logger_id)

def formatter(record):
    record['message']
    level = record['level'].name
    add = ''
    Dir = {
        'INFO':'<cyan>',
        'ERROR':'<RED>[ERROR]</RED><red>',
        'WARNING':'<LIGHT-YELLOW><black>[WARN]</black></><light-yellow>',
        'DEBUG':'<bold>',
        'SUCCESS':'<green>',
        'FBOT':'<fg #bf0060>',
        'suc':'<GREEN>[OK]</GREEN><green>',
        'err':'<RED>[ERROR]</RED><RED><white>'
    }
    color_tag=Dir[level]
    if not color_tag:color_tag = ''
    match = re.match(r'^\s*\[([^\]]+)\]',record['message'])
    if match:
        func_name = '['+match[1]+']'
        record['message'] = record['message'].replace(func_name,'')
    else: func_name = '['+record['name']+']'
    if level == 'ERROR': add = "{exception}"
    if level == 'err': add = "</>"
    return color_tag+func_name+"</>"+'{message}'+"\n"+add
logger.add(sys.stdout, format=formatter,level=0,filter=default_filter,diagnose=True,serialize=False)
logger.level('suc',no=25)
logger.level('err',no=40)
logger.level('FBOT',no=20)

def info(app:str,text:str): logger.opt(colors=True).log('FBOT',f"[{app}] {text}")
def error(app:str,text:str): logger.opt(colors=True).error(f"[{app}] {text}")
def success(app:str,text:str): logger.opt(colors=True).success(f"[{app}] {text}")
def warn(app:str,text:str): logger.opt(colors=True).warning(f"[{app}] {text}")
def debug(app:str,text:str): logger.opt(colors=True).debug(f"[{app}] {text}")
def suc(app:str,text:str): logger.opt(colors=True).log('suc',f"[{app}] {text}")
def err(app:str,text:str): logger.opt(colors=True).log('err',f"[{app}] {text}")

from dotenv import dotenv_values, load_dotenv, set_key
cfg = {
'text2img_step':27,
'text2img_negative_prompt':"(worst quality, low quality:1.4),NSFW,r18",
'text2img_proxy':'127.0.0.1:7860',
'presets_dir':'./presets',
'Chat_stream_waitTime':2,
'Chat_stream_endStr':('？','。','?','\n'),
'defaultAI':'chatGPT',
'access_token':'',
'api_key':'',
'model':'gpt-3.5-turbo',
'cookies_file_path': "./cookies.json",
}



async def Chat(func,message:str,mode=1): 
    if not message or len(message)<1:return
    Rtime = cfg['Chat_stream_waitTime']
    endStr = cfg['Chat_stream_endStr']
    text = ''
    out_text=''
    info('ChatGPT','开始询问 (网页)')
    for data in chatbot.ask(message):
        text = data["message"] # type: ignore
        try: not now # type: ignore
        except: now = time.time()
        if time.time() - now > Rtime and text.endswith(endStr) and mode == 1: # type: ignore
            now = time.time()
            outText = text.replace(out_text,'')
            success('ChatGPT', outText)
            await func.send(outText)
            out_text = data["message"] # type: ignore
    if len(out_text) < len(text) or mode == 0:
        outText = text.replace(out_text,'')
        success('ChatGPT', outText)
        await func.send(outText)
    if mode ==2:
        return text.replace(r'.*\.AIP','')
    
async def Chat_api(func,message:str,mode=1):
    if not message or len(message)<1:return
    Rtime = cfg['Chat_stream_waitTime']
    endStr = cfg['Chat_stream_endStr']
    text = ''
    info('ChatGPT api','开始询问 api')
    for data in chatbot_api.ask_stream(message):
        text += data 
        try: not now # type: ignore
        except: now = time.time()
        if time.time() - now > Rtime and text.endswith(endStr) and mode == 1: # type: ignore
            now = time.time()
            success('ChatGPT api', text)
            await func.send(text)
            text = ''
    if len(text) > 0:
        success('ChatGPT api', text)
        await func.send(text)
    if mode ==2:
        return text.replace(r'.*\.AIP','')

async def Bing(func,message,mode=1):
    if not message or len(message)<1:return
    Rtime = cfg['Chat_stream_waitTime']
    endStr = cfg['Chat_stream_endStr']
    text = ''
    out_text=''
    info('Bing','开始询问 api')
    async for data in bingbot.ask_stream(message):
        istrue , string = data
        if type(string) == str : text = string
        try: not now # type: ignore
        except: now = time.time()
        if time.time() - now > Rtime and text.endswith(endStr) and mode == 1 : # type: ignore
            now = time.time()
            outText = text.replace(out_text,'')
            success('Bing', outText)
            if len(outText.replace(' ','')) > 0:
                await func.send(outText)
            out_text = text # type: ignore
    if len(out_text) < len(text) or mode == 0:
        outText = text.replace(out_text,'')
        success('Bing', outText)
        await func.send(outText)
    if mode ==2:
        return text.replace(r'.*\.AIP','')

async def text2image(func,prompt):
    ip = cfg['text2img_proxy'].split(':')
    info('Stable-Diffusion','开始询问 api'+cfg['text2img_proxy'])
    api = webuiapi.WebUIApi(host=ip[0], port=ip[1]) # type: ignore
    result1 = api.txt2img(
        prompt=prompt,
        negative_prompt=cfg['text2img_negative_prompt'],
        steps=cfg['text2img_step'],
    )
    image = result1.image
    success('Stable-Diffusion','返回图片')
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    return img_bytes

async def startup():
    global bingbot
    global chatbot
    global chatbot_api
    global botList 
    if not os.path.exists('./config.cfg'):
        with open('config.cfg', 'w',encoding='utf-8') as f:
            text = """
text2img_step=27
text2img_negative_prompt="(worst quality, low quality:1.4),NSFW,r18"
text2img_proxy='127.0.0.1:7860'

presets_dir='./presets'
Chat_stream_waitTime=2
Chat_stream_endStr=('？','。','?','\\n')
defaultAI='chatGPT'

chatGPT # ChatGPT 配置:
access_token=""

chatGPT_api # ChatGPT api 配置:
api_key=""
model="gpt-3.5-turbo"

bing # Bing api 配置:
cookies_file_path="./cookies.json"
            """
            f.write(text)


    cfg_ =dotenv_values("config.cfg")

    try : 
        if len(cfg_['access_token']) >0:suc('Config','配置文件 有效') # type: ignore
        elif len(cfg_['api_key']) >0:suc('Config','配置文件 有效') # type: ignore
        elif len(cfg_['cookies_file_path'])>0: # type: ignore
            with open(cfg_['cookies_file_path'], 'r') as f: # type: ignore
                cookies = json.load(f)
                suc('Config','配置文件 有效')
        else:raise Exception()
        cfg.update(cfg_)
    except:
        err('Config','配置文件 config.cfg 未配置')
        raise Exception('配置文件 config.cfg 未配置')


    botList  = []

    info('Presets Load','开始加载预设')
    Presets = {}
    for file_path in glob.glob(os.path.join(cfg['presets_dir'], '*.txt')):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        fileName = os.path.basename(file_path).replace('.txt', '')
        Presets[fileName] = content
        success('Presets Load','加载预设: '+fileName)
    CFGdata = {}
    CFGdata['Presets'] = Presets
    try: 
        cfg['cookies_file_path']
        if os.path.exists(cfg['cookies_file_path']):
            info('Bing',"发现cookies.json")
            with open(cfg['cookies_file_path'], 'r') as f:
                cookies = json.load(f)
                bingbot = bing(cookies=cookies)
            botList.append('Bing')
            suc('Bing','接入 Bing 成功')
        else:warn('Bing','cookies.json 不存在,将无法使用bing')
    except:pass
    try: 
        cfg['access_token']
        if len(cfg['access_token']) < 4 : 
            warn('ChatGPT','access_token 无效,将无法使用ChatGPT 网页模式')
            raise Exception
        chatbot = chatGPT(config={"access_token": cfg['access_token']})
        botList.append('ChatGPT')
        suc('chatGPT','接入 ChatGPT 成功')
    except:pass
    try:
        cfg['api_key']
        if(len(cfg['api_key']) < 4 or 'sk-' not in cfg['api_key']): 
            warn('ChatGPT api','apikey 无效,将无法使用ChatGPT api模式')
            raise Exception
        chatbot_api = chatGPT_api(cfg['api_key'])
        botList.append('ChatGPT_api')
        suc('ChatGPT api','接入 ChatGPT_api 成功')
    except:pass
    CFGdata['botList']=botList
    CFGdata['cfg']=cfg
    return CFGdata
