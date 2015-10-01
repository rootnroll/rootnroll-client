DEFAULT_API_URL = 'https://au.rootnroll.com/api'
DEFAULT_TIMEOUT_SECONDS = 30


class ServerStatus(object):
    BUILD = 'BUILD'
    ACTIVE = 'ACTIVE'
    ERROR = 'ERROR'


class CheckerJobStatus(object):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class CheckerJobResult(object):
    PASSED = 'passed'
    FAILED = 'failed'
