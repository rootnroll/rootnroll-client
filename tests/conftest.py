import base64
import pytest

from rootnroll import RootnRollClient


def pytest_addoption(parser):
    parser.addoption('--username', action='store', default=None,
                     help="Username for Root'n'Roll API")
    parser.addoption('--password', action='store', default=None,
                     help="Password for Root'n'Roll API")
    parser.addoption('--api-url', action='store', default=None,
                     help="Use this url to connect to Root'n'Roll API")


@pytest.fixture
def username(request):
    return request.config.getoption('username')


@pytest.fixture
def password(request):
    return request.config.getoption('password')


@pytest.fixture
def api_url(request, username, password):
    url = request.config.getoption('api_url')
    if not all((url, username, password)):
        pytest.skip("Skip because the test requires Root'n'Roll API URL")
    return url


@pytest.fixture
def client(username, password, api_url):
    return RootnRollClient(username, password, api_url)


@pytest.fixture
def image_id():
    return 3  # Ubuntu 14.04 on au.rootnroll.com


@pytest.yield_fixture
def server(client, image_id):
    server = client.create_server(image_id)
    yield server
    client.destroy_server(server)


@pytest.fixture
def sandbox(client):
    files = [{'name': 'file.txt',
              'content': base64.b64encode(b"42\n").decode()}]
    limits = {'cputime': 1, 'realtime': 2, 'memory': 32}
    return client.create_sandbox('linux-bootstrap', 'cat /sandbox/file.txt',
                                 files=files, limits=limits)
