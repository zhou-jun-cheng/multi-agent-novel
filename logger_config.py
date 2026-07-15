# logger_config.py
import logging
import atexit

# 全局标志，确保只初始化一次
_initialized = False

# 自定义过滤器：控制台只输出 DEBUG 级别
class DebugOnlyFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.DEBUG


def init_logging(name='myApp', log_file='app.log', force=False):
    """手动初始化日志系统（通常在程序最开始时调用一次）"""
    global _initialized
    if _initialized and not force:
        return

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 清除已有的 handlers（防止重复）
    logger.handlers.clear()

    # 文件处理器：记录 INFO 及以上级别
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 控制台处理器：只输出 DEBUG
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.addFilter(DebugOnlyFilter())

    # 格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _initialized = True

    # 记录一条启动日志
    logger.info(f'日志系统已初始化 (日志文件: {log_file})')


def get_logger(name='myApp'):
    """获取日志记录器（如果未初始化则自动初始化）"""
    if not _initialized:
        # 自动初始化，使用默认配置
        init_logging(name)
    return logging.getLogger(name)


# 模块导入时自动初始化（如果想自动执行，取消下一行注释）
init_logging()
