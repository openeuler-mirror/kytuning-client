

__all__ = ['KyTuningError', 'KyTuningNoSuchDir']


class KyTuningError(Exception):
    pass


class KyTuningNoSuchDir(Exception):
    pass


class SchemeParseError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(*args, **kwargs)
