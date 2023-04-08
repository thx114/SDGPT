import setuptools



setuptools.setup(
    name="nonebot-plugin-SDGPT",  # 项目名称，保证它的唯一性，不要跟已存在的包名冲突即可
    version="0.0.8",  # 程序版本
    author="F_thx",  # 项目作者
    author_email="thx1140093097@gmail.com",  # 作者邮件
    url="https://github.com/thx114/SDGPT",  # 项目地址
    packages=setuptools.find_packages(),  # 无需修改
    license="MIT Licence",
    install_requires=[
        'nonebot2',
        'python-dotenv',
        'revChatGPT',
        'EdgeGPT',
        'webuiapi',
        'nonebot-adapter-onebot',
        'nonebot-plugin-guild-patch'
    ],
)

