# llm_agent_platform/utils/logger.py

import logging
from logging.handlers import RotatingFileHandler
import os
import sys

# --- 1. 配置日志文件和目录 ---
# 定义日志目录相对于项目根目录的路径
# 确保这个路径是正确的，它将在您运行应用程序时创建
LOG_DIR = "logs"
LOG_FILE_NAME = "app.log"
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)

# --- 2. 创建日志目录 (如果不存在) ---
# os.makedirs(LOG_DIR, exist_ok=True) 的作用是：
# 如果 'logs' 目录不存在，则创建它。
# 如果 'logs' 目录已存在，则什么也不做，不会报错。
os.makedirs(LOG_DIR, exist_ok=True)

# --- 3. 获取或创建 Logger 实例 ---
# logging.getLogger() 方法获取一个 Logger 对象。
# 如果传入的名称已经存在，则返回现有的 Logger；否则，创建一个新的。
# 通常，我们会给 Logger 起一个能代表其来源的名称，这里使用项目名称。
logger = logging.getLogger("llm_agent_platform")

# --- 4. 设置 Logger 的总日志级别 ---
# 只有当日志消息的级别高于或等于 Logger 的级别时，消息才会被处理器处理。
# DEBUG: 最详细的日志信息，常用于调试。
# INFO: 确认程序按预期运行。
# WARNING: 表示发生了一些意外，或指示未来可能发生问题（但程序仍在正常运行）。
# ERROR: 程序因为某些问题，未能执行某项功能。
# CRITICAL: 严重错误，程序可能无法继续运行。
logger.setLevel(logging.INFO) # 在这里可以根据环境（开发/生产）调整默认级别

# --- 5. 配置日志处理器 (Handlers) ---
# 处理器决定日志消息的去向（如文件、控制台、网络等）。

# 5.1 文件处理器 (RotatingFileHandler)
# RotatingFileHandler 用于将日志写入文件，并支持文件轮转，防止日志文件过大。
# filename: 日志文件的路径。
# maxBytes: 单个日志文件的最大大小（字节）。这里设置为 10MB。
# backupCount: 保留的旧日志文件数量。这里设置为 5，即 app.log.1, app.log.2 等。
file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
file_handler.setLevel(logging.INFO) # 文件处理器只处理 INFO 级别及以上的消息

# 5.2 控制台处理器 (StreamHandler)
# StreamHandler 用于将日志消息输出到控制台（标准输出或标准错误）。
# sys.stdout 代表标准输出流，sys.stderr 代表标准错误流。
# 通常 INFO 及 DEBUG 消息到 stdout，WARNING 及以上到 stderr。
# 这里我们简化为所有控制台日志都到 stdout。
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO) # 控制台处理器只处理 INFO 级别及以上的消息

# --- 6. 定义日志格式 (Formatter) ---
# 格式化器定义日志消息的输出格式。
# %(asctime)s: 日志记录时间。
# %(name)s: Logger 的名称。
# %(levelname)s: 日志级别（如 INFO, ERROR）。
# %(filename)s: 记录日志的代码所在的文件名。
# %(lineno)d: 记录日志的代码所在的行号。
# %(message)s: 日志消息内容。
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

# 将格式化器应用到各个处理器
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# --- 7. 将处理器添加到 Logger ---
# 一个 Logger 可以有多个处理器，日志消息会通过每个处理器发送出去。
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# --- 8. (可选) 防止重复日志输出 ---
# 如果一个 Logger 实例被多次添加到根 Logger 或其父 Logger，可能会导致重复输出。
# 通常，最好不要将 Logger 的 propagate 属性设置为 True，以防止其消息传播到父 Logger。
# 这里我们假设此 Logger 是独立的或被正确管理。
# 如果您发现日志重复，可以尝试取消注释下一行。
# logger.propagate = False

# --- 示例用法 (您可以删除这些行，它们仅用于演示) ---
if __name__ == "__main__":
    logger.debug("This is a DEBUG message.") # 不会显示，因为级别是 INFO
    logger.info("This is an INFO message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message. Something went wrong.")
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("An exception occurred during division.") # exception 会自动包含堆栈信息
    logger.critical("This is a CRITICAL message. The application might stop.")