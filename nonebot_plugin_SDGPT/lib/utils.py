import aiofiles
from .logger import err
async def load_preset(dir,filename):
    try:
        async with aiofiles.open(dir+"/"+filename, mode="r",encoding='utf-8') as f:
            text = await f.read()
        return text
    except Exception as ERR:
        print(ERR)
        return err('load_preset',f'读取预设文件{dir+"/"+filename}失败')
