from rootnroll.client import ServerStatus


class TestServer(object):
    def assert_server(self, server, status=ServerStatus.ACTIVE):
        assert server
        assert server['id']
        if not isinstance(status, (list, tuple)):
            status = [status]
        assert server['status'] in status

    def test_create_destroy_server(self, client, image_id):
        server = client.create_server(image_id)

        self.assert_server(server, [ServerStatus.BUILD, ServerStatus.ACTIVE])

        server_id = server['id']

        self.assert_server(client.get_server(server_id),
                           [ServerStatus.BUILD, ServerStatus.ACTIVE])

        client.destroy_server(server)

        assert client.get_server(server_id) is None

    def test_wait_server_status(self, client, server):
        active_server = client.wait_server_status(server, ServerStatus.ACTIVE,
                                                  timeout=15)
        server = client.get_server(server['id'])
        self.assert_server(server, ServerStatus.ACTIVE)
        assert active_server == server
