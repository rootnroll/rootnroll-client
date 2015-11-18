import time
import uuid

import requests
import structlog

from . import constants as c


logger = structlog.get_logger()


class RootnRollException(Exception):
    """Base Root'n'Roll exception class."""


class RootnRollClient(object):
    def __init__(self, username, password, api_url=c.DEFAULT_API_URL,
                 timeout=c.DEFAULT_TIMEOUT_SECONDS):
        self.api_url = api_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = (username, password)

    def _url(self, path, *args, **kwargs):
        return (self.api_url + path).format(*args, **kwargs)

    def _request(self, method, url, **kwargs):
        log = logger.bind(request_id=str(uuid.uuid4())[:8])
        kwargs.setdefault('timeout', self.timeout)
        log.debug("Sending API request", method=method.upper(), url=url,
                  data=kwargs.get('json'), timeout=kwargs.get('timeout'))
        r = self.session.request(method, url, **kwargs)
        if not r:
            log.info("Received unsuccessful API response",
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

    def create_server(self, image_id, memory=64):
        server_body = {
            'image_id': image_id,
            'memory': memory,
        }
        r = self._post(self._url('/servers'), json=server_body)
        return self._result(r)

    def get_server(self, server_id):
        return self._result(self._get(self._url('/servers/{0}', server_id)))

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
        r = self._delete(self._url('/servers/{0}', server['id']))
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
