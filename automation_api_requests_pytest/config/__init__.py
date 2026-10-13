# config/__init__.py
# 这一行的作用：把 config.py 里的配置"转发"到包这一层，
# 让外面用统一的老写法导入：
#     from config import BASE_URL, TIMEOUT, TEST_USER, DB
#
# 好处：你把 config.py 从根目录挪进 config/ 文件夹之后，
# 其它文件里的 import 一行都不用改。少改一处，就少一处报错。
#
# 新增配置项时，记得在这里也加上名字，否则 `from config import XXX` 会报 ImportError。
#
# ⚠️ 这一行必须**保持启用**：common/logger.py 的 short_url() 用的就是
#    `from config import BASE_URL`。它一旦被注释掉，那个 import 会静默失败
#    （short_url 里有 except 兜底），后果是日志里的请求行**打回完整 URL**——
#    不报错、不崩溃，只是悄悄变难看了（踩过一次）。

from .config import BASE_URL, TIMEOUT, TEST_USER, DB
