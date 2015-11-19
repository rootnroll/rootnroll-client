import base64
import textwrap

from rootnroll.constants import (CheckerJobStatus, CheckerJobResult,
                                 ServerStatus, SandboxStatus)


def test_create_destroy_server(client, image_id):
    server = client.create_server(image_id)

    assert server['id']
    assert server['status'] in [ServerStatus.BUILD, ServerStatus.ACTIVE]

    server_id = server['id']
    server = client.get_server(server_id)

    assert server['id']
    assert server['status'] in [ServerStatus.BUILD, ServerStatus.ACTIVE]

    client.destroy_server(server)

    assert client.get_server(server_id) is None


def test_wait_server_status(client, server):
    active_server = client.wait_server_status(server, ServerStatus.ACTIVE)
    server = client.get_server(server['id'])

    assert server['status'] == ServerStatus.ACTIVE
    assert active_server == server


def test_create_destroy_terminal(client, server_perm):
    server = client.wait_server_status(server_perm, ServerStatus.ACTIVE)

    terminal = client.create_terminal(server)
    print("### TERMINAL:", terminal)

    assert terminal['id']
    assert terminal['server_id'] == server['id']
    assert terminal['config']['kaylee_url']

    terminal = client.get_terminal(terminal['id'])

    assert terminal['id']
    assert terminal['server_id'] == server['id']
    assert terminal['config']['kaylee_url']

    client.destroy_terminal(terminal)

    assert client.get_terminal(terminal['id']) is None


def test_create_sandbox(client):
    sandbox = client.create_sandbox('linux-bootstrap', 'true')

    assert sandbox['id']
    assert sandbox['status'] == SandboxStatus.PENDING


def test_create_sandbox_with_files_and_limits(client):
    files = [{'name': 'file.txt',
              'content': base64.b64encode(b"42\n").decode()}]
    limits = {'cputime': 1, 'realtime': 2, 'memory': 32}

    sandbox = client.create_sandbox('linux-bootstrap', 'cat /sandbox/file.txt',
                                    files=files, limits=limits)

    assert sandbox['id']
    assert sandbox['status'] == SandboxStatus.PENDING


def test_get_sandbox(client, sandbox):
    _sandbox = client.get_sandbox(sandbox['id'])

    assert _sandbox['id'] == sandbox['id']


def test_wait_sandbox_terminated(client, sandbox):
    sandbox = client.wait_sandbox_terminated(sandbox)

    assert sandbox['status'] == SandboxStatus.SUCCESS
    assert sandbox['exit_code'] == 0
    assert base64.b64decode(sandbox['stdout']) == b"42\n"


def test_create_get_checker_job(client, server_perm):
    server = client.wait_server_status(server_perm, ServerStatus.ACTIVE,
                                       timeout=30)
    test_scenario = textwrap.dedent("""
        def test_true():
            assert True
        """).strip()

    job = client.create_checker_job(server, test_scenario)

    assert job['id']
    assert job['server'] == server['id']
    assert job['test_scenario'] == test_scenario
    assert job['status'] == CheckerJobStatus.RUNNING
    assert job['finished_at'] is None
    assert not job['result']

    job = client.get_checker_job(job['id'])

    assert job['id']
    assert job['server'] == server['id']
    assert job['test_scenario'] == test_scenario
    assert job['status'] in [CheckerJobStatus.RUNNING,
                             CheckerJobStatus.COMPLETED]


def test_wait_checker_job_ready(client, server_perm):
    test_scenario = textwrap.dedent("""
        def test_true():
            assert True
        """).strip()
    job = client.create_checker_job(server_perm, test_scenario)

    job = client.wait_checker_job_ready(job, timeout=30)

    assert job['status'] == CheckerJobStatus.COMPLETED
    assert job['result'] == CheckerJobResult.PASSED
    assert job['finished_at']
