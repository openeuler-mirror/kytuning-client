import logging



def log_init(path='kytuning.log', levelname='info'):
    if path is None or len(path) == 0:
        path = 'kytuning.log'
    level = logging.INFO
    if levelname == 'error':
        level = logging.ERROR
    elif levelname == 'warning':
        level = logging.WARN
    elif levelname == 'debug':
        level = logging.DEBUG
    Format = '[%(levelname)s][%(asctime)s,%(module)s,%(lineno)d,%(funcName)s] %(message)s'
    logging.addLevelName(logging.DEBUG, 'D')
    logging.addLevelName(logging.INFO, 'I')
    logging.addLevelName(logging.WARNING, 'W')
    logging.addLevelName(logging.ERROR, 'E')
    #logging.basicConfig(filename=path, level=level , format=Format, filemode='w')

    # 创建日志器
    logger = logging.getLogger()
    logger.setLevel(level)

    # 文件日志处理器
    file_handler = logging.FileHandler(path, mode='w')
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(Format))
    
    # 控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(Format))
    
    # 添加处理器到日志器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

if __name__ == '__main__':

    log_init()

    logging.error('Hello')
