"""
Loguru vs 标准库 logging 对比示例
"""

import sys
import time
from pathlib import Path

# 标准库 logging 示例
def demo_standard_logging():
    print("=== 标准库 logging 示例 ===")
    import logging
    from logging.handlers import RotatingFileHandler

    # 配置日志器
    logger = logging.getLogger("demo")
    logger.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（需要手动配置轮转）
    file_handler = RotatingFileHandler(
        'demo_standard.log',
        maxBytes=1024*1024,  # 1MB
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 记录日志
    logger.info("标准库 logging 消息")
    logger.warning("这是一个警告")
    logger.error("这是一个错误")

    try:
        1 / 0
    except Exception:
        logger.exception("异常信息")

    print("标准库 logging 配置完成，需要手动管理处理器\n")


# Loguru 示例
def demo_loguru():
    print("=== Loguru 示例 ===")
    from loguru import logger

    # 移除默认处理器
    logger.remove()

    # 添加控制台处理器（自动彩色）
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {function}:{line} - {message}",
        level="INFO"
    )

    # 添加文件处理器（内置轮转和压缩）
    logger.add(
        "demo_loguru.log",
        rotation="1 MB",
        retention="3 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {function}:{line} - {message}",
        level="INFO"
    )

    # 记录日志
    logger.info("Loguru 消息")
    logger.warning("这是一个警告")
    logger.error("这是一个错误")

    try:
        1 / 0
    except Exception:
        logger.exception("异常信息")  # 自动包含堆栈跟踪

    # Loguru 特有功能
    logger.debug("调试信息")
    logger.opt(lazy=True).debug("Lazy evaluation: {value}", value=lambda: time.time())

    print("Loguru 配置完成，内置轮转和压缩\n")


# 性能对比
def performance_comparison():
    print("=== 性能对比测试 ===")
    import logging
    from loguru import logger as loguru_logger

    # 配置标准库
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    std_logger = logging.getLogger("perf_test")

    # 配置 loguru
    loguru_logger.remove()
    loguru_logger.add(sys.stderr, format="{message}", level="INFO")

    # 测试数据
    test_messages = ["测试消息 {}".format(i) for i in range(1000)]

    # 标准库性能测试
    start = time.time()
    for msg in test_messages:
        std_logger.info(msg)
    std_time = time.time() - start

    # Loguru 性能测试
    start = time.time()
    for msg in test_messages:
        loguru_logger.info(msg)
    loguru_time = time.time() - start

    print(f"标准库 logging: {std_time:.4f}s")
    print(f"Loguru: {loguru_time:.4f}s")
    print(f"性能差异: {std_time/loguru_time:.2f}x\n")


if __name__ == "__main__":
    demo_standard_logging()
    demo_loguru()
    performance_comparison()