# -*- coding:utf-8 -*-

import logging

import os
from logging.handlers import TimedRotatingFileHandler
from django.conf import settings


class cusLogger:
    def __init__(self, loggerName):
        # 创建一个logger
        self.logger = logging.getLogger(loggerName)
        self.logger.setLevel(logging.DEBUG)
        # 创建一个handler，用于写入日志文件。如果当前目录下没有logs目录，需要手动创建
        logPath = os.path.join(settings.BASE_DIR, "logs")
        if not os.path.exists(logPath):
            os.mkdir(logPath)
        # 日志文件名
        logName = os.path.join(logPath, loggerName + '.log')

        # 创建一个每日可更新的handler，用于将日志输出文件
        fileHandler = TimedRotatingFileHandler(logName, when='D', encoding='utf-8')
        fileHandler.setLevel(logging.DEBUG)

        # 创建一个handler，用于将日志输出到控制台
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.DEBUG)

        # 定义handler的输出格式
        formatter = logging.Formatter(
            '%(asctime)s-%(name)s-%(levelname)s:%(message)s')
        fileHandler.setFormatter(formatter)
        consoleHandler.setFormatter(formatter)

        self.logger.addHandler(fileHandler)
        # 如果不需要控制台，可以注释掉
        self.logger.addHandler(consoleHandler)

    def getLogger(self):
        return self.logger


if __name__ == '__main__':
    pass
