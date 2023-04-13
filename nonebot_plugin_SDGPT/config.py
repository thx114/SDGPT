# -*- coding: utf-8 -*-
import json
import os

from .lib.cons import *
from configobj import ConfigObj
from validate import Validator
from .lib.check import check_ai, check_dir, check_proxy, check_api_key, check_command, check_file, check_ip, \
    ip_test_switch, check_token, check_model, check_id, check_any, check_preset
from revChatGPT.V1 import AsyncChatbot as chatGPT
from revChatGPT.V3 import Chatbot as chatGPT_api
from EdgeGPT import Chatbot as Bing



async def load():

    outData = {}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configspec.ini')
    config = ConfigObj('config.cfg', encoding='utf-8', default_encoding='utf-8', configspec=path,
                       indent_type=' ', write_empty_values=True)
    validator = Validator({
        'dir': check_dir,
        'ai': check_ai,
        'cmd': check_command,
        'proxy': check_proxy,
        'file': check_file,
        'apikey': check_api_key,
        'ip': check_ip,
        'ip_test_switch': ip_test_switch,
        'id': check_id,
        'any': check_any,
        'preset': check_preset,
        'token': check_token,
        'model': check_model
    })
    config.validate(validator, copy=True, preserve_errors=True)
    config.write()
    botList = []
    # check AIs
    if config['AI']['chatgpt']['access_token'] == '':
        warn('配置检查', 'chatgpt access_token 为空,无法使用chatGPT(网页模式)')
    else:
        botList.append('chatgpt')
        outData['chatgpt'] = chatGPT(config={"access_token": config['AI']['chatgpt']['access_token']})
        if config['AI']['chatgpt']['proxy'] and config['AI']['chatgpt']['proxy'] != '':
            outData['chatgpt'].config['proxy'] = config['AI']['chatgpt']['proxy']
        suc('chatgpt', 'ChatGPT(网页)已加载')
    if config['AI']['chatgpt-api']['api_key'] == '':
        warn('配置检查', 'chatgpt-api api_key 为空,无法使用chatGPT(api模式)')
    else:
        botList.append('chatgpt-api')
        outData['chatgpt-api'] = chatGPT_api(api_key=config['AI']['chatgpt-api']['api_key'])
        if config['AI']['chatgpt-api']['proxy'] and config['AI']['chatgpt-api']['proxy'] != '':
            outData['chatgpt-api'].proxy = config['AI']['chatgpt-api']['proxy']
        suc('chatgpt-api', 'ChatGPT(api)已加载')
    try:
        with open(config['AI']['bing']['cookies_file_path'], 'r') as f:
            cookies = json.load(f)
            botList.append('bing')
            outData['bing'] = Bing(cookies=cookies)
            if config['AI']['bing']['proxy'] and config['AI']['bing']['proxy'] != '':
                outData['bing'].proxy = config['AI']['bing']['proxy']
            suc('bing', '已加载')
    except:
        warn('配置检查', 'bing cookies.json 加载失败,无法使用bing')
    if len(botList) > 0:
        suc('所有AI', '已加载' + str(len(botList)) + '个AI: ' + ','.join(botList))
    else:
        error('配置检查', '没有一个AI成功被加载')
    outData['cfg'] = config
    outData['bots'] = botList
    #
    outData['cmd'] = {
        'bing': 'bing',
        'chat': 'chat',
        'ai': 'ai',
        'tag': 'tag',
    }
    for item in config['preset']:
        key = item
        val = config['Chat']['presets_dir'] + '/' + config['preset'][item]
        suc('预设加载', f'{key} : {val}')
    return outData
