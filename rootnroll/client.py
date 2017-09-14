import time
import urllib.parse
import uuid

import requests
import structlog
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from . import constants as c

logger = structlog.get_logger()


class RootnRollException(Exception):
    """Base Root'n'Roll exception class."""


class RootnRollClient(object):
    def __init__(self, username, password, api_url=c.DEFAULT_API_URL,
                 timeout=c.DEFAULT_TIMEOUT_SECONDS,
                 max_retries=c.DEFAULT_MAX_RETRIES):
        self.api_url = api_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = (username, password)
        retries = Retry(total=max_retries,
                        method_whitelist=False,
                        status_forcelist=[502],
                        backoff_factor=c.BACKOFF_FACTOR,
                        raise_on_status=False)
        http_adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('http://', http_adapter)
        self.session.mount('https://', http_adapter)

    def _url(self, path, *args, **kwargs):
        query_str = '?' + urllib.parse.urlencode(kwargs) if kwargs else ''
        return (self.api_url + path + query_str).format(*args)

    def _request(self, method, url, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        log = logger.bind(request_id=str(uuid.uuid4())[:8],
                          method=method.upper(), url=url,
                          data=kwargs.get('json'),
                          timeout=kwargs.get('timeout'))
        log.debug("Sending API request")
        r = self.session.request(method, url, **kwargs)
        if not r:
            log.info("Received API response",
                     status_code=r.status_code, data=r.content)
        else:
            log.debug("Received API response",
                      status_code=r.status_code, data=r.content)
        return r

    def _get(self, url, **kwargs):
        return self._request('get', url, **kwargs)

    def _post(self, url, **kwargs):
        return self._request('post', url, **kwargs)

    def _patch(self, url, **kwargs):
        return self._request('patch', url, **kwargs)

    def _delete(self, url, **kwargs):
        return self._request('delete', url, **kwargs)

    def _result(self, response):
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def get_image(self, image_id):
        return self._result(self._get(self._url('/images/{0}', image_id)))

    def create_server(self, image_id, memory=64):
        server_body = {
            'image_id': image_id,
            'memory': memory,
        }
        r = self._post(self._url('/servers'), json=server_body)
        return self._result(r)

    def get_server(self, server):
        server_id = server['id'] if isinstance(server, dict) else server
        return self._result(self._get(self._url('/servers/{0}', server_id)))

    def list_servers(self, page=1):
        """Get a paginated list of servers.

        :param page: page number (default: 1)

        """
        return self._result(self._get(self._url('/servers', page=page)))

    def wait_server_status(self, server, until_status, timeout=180):
        """Wait for server status to become `until_status`."""

        start_time = time.time()
        while time.time() - start_time < timeout:
            server = self.get_server(server['id'])
            if server['status'] == until_status:
                return server
            if server['status'] == c.ServerStatus.ERROR:
                raise RootnRollException("Failed waiting for server status")
            time.sleep(1)
        else:
            raise TimeoutError("Timed out waiting for server status")

    def destroy_server(self, server):
        server_id = server['id'] if isinstance(server, dict) else server
        r = self._delete(self._url('/servers/{0}', server_id))
        r.raise_for_status()

    def create_terminal(self, server):
        """Create a terminal for the given ACTIVE server."""

        terminal_body = {
            'server_id': server['id'],
        }
        r = self._post(self._url('/terminals'), json=terminal_body)
        return self._result(r)

    def get_terminal(self, terminal_id):
        return self._result(
            self._get(self._url('/terminals/{0}', terminal_id)))

    def destroy_terminal(self, terminal):
        r = self._delete(self._url('/terminals/{0}', terminal['id']))
        r.raise_for_status()

    def create_sandbox(self, profile, command=None, files=None, limits=None):
        sandbox_body = {
            'profile': profile,
            'command': command,
            "files": files or [],
            "limits": limits or {},
        }
        r = self._post(self._url('/sandboxes'), json=sandbox_body)
        return self._result(r)

    def get_sandbox(self, sandbox_id):
        return self._result(self._get(self._url('/sandboxes/{0}', sandbox_id)))

    def wait_sandbox_terminated(self, sandbox, timeout=c.DEFAULT_WAIT_TIMEOUT):
        start_time = time.time()
        while time.time() - start_time < timeout:
            sandbox = self.get_sandbox(sandbox['id'])
            if (sandbox['status'] in c.SandboxStatus.terminated_set or
                    sandbox['timeout']):
                return sandbox
            time.sleep(0.5)
        raise TimeoutError("Timed out waiting for sandbox to be terminated")

    def create_checker_job(self, server, test_scenario):
        job_body = {
            'server': server['id'],
            'test_scenario': test_scenario,
        }
        r = self._post(self._url('/checker-jobs'), json=job_body)
        return self._result(r)

    def get_checker_job(self, job_id):
        return self._result(self._get(self._url('/checker-jobs/{0}', job_id)))

    def wait_checker_job_ready(self, job, timeout=c.DEFAULT_WAIT_TIMEOUT):
        start_time = time.time()
        while time.time() - start_time < timeout:
            job = self.get_checker_job(job['id'])
            if job['status'] in c.CheckerJobStatus.ready_set:
                return job
            time.sleep(0.5)
        raise TimeoutError("Timed out waiting for checker job readiness")
