import base64

from rootnroll.constants import ServerStatus, SandboxStatus


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
    active_server = client.wait_server_status(server, ServerStatus.ACTIVE,
                                              timeout=30)
    server = client.get_server(server['id'])

    assert server['status'] == ServerStatus.ACTIVE
    assert active_server == server


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
