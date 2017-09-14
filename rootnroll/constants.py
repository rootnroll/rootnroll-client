DEFAULT_API_URL = 'https://rootnroll.com/api'
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_WAIT_TIMEOUT = 60
DEFAULT_MAX_RETRIES = 5
BACKOFF_FACTOR = 0.4


class ServerStatus(object):
    BUILD = 'BUILD'
    CREATING = 'creating'
    STARTING = 'starting'
    ACTIVE = 'ACTIVE'
    ERROR = 'ERROR'


class SandboxStatus(object):
    PENDING = 'pending'
    STARTED = 'started'
    SUCCESS = 'success'
    FAILURE = 'failure'

    terminated_set = {SUCCESS, FAILURE}


class CheckerJobStatus(object):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'

    ready_set = {COMPLETED, FAILED}


class CheckerJobResult(object):
    PASSED = 'passed'
    FAILED = 'failed'
