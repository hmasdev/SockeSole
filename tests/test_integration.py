from threading import Thread
import time
import queue
import pytest
from sockesole import (
    HEARTBEAT,
    SocketConsoleClient,
    SocketConsoleServer,
)

WAIT_SEC: float = 0.1


@pytest.mark.integration
@pytest.mark.timeout(10)
def test_server_and_client_communicate() -> None:
    # setup
    result_queue: queue.Queue = queue.Queue()
    addr = ("127.0.0.1", 1234)
    clean_interval = 0.5
    server = SocketConsoleServer(*addr, clean_interval=clean_interval)  # noqa
    server.run()

    # execute and assert

    # server alive
    time.sleep(WAIT_SEC)
    assert server.alive()

    # test connection
    client = SocketConsoleClient.connect(*addr)
    time.sleep(WAIT_SEC)  # NOTE: wait for server to accept connection
    assert client.alive()
    assert server.get_keys()  # NOTE: check if server has client

    # test server.echo
    caddr = server.get_keys()[0]
    server.get_console(caddr).echo("test1")
    assert client.read(wait=0.01, delete_heartbeat=True) == "test1"

    # test server.prompt and client.write
    # NOTE: client.write() is blocking, so we need to run it in a separate thread  # noqa
    th = Thread(
        target=lambda s: result_queue.put(server.get_console(caddr).prompt(s, wait=0.01, delete_heartbeat=True)),  # noqa
        args=("test2",),
    )
    th.daemon = True
    th.start()
    time.sleep(WAIT_SEC)
    assert client.read(wait=0.01, delete_heartbeat=True) == "test2"
    client.write("test3")
    time.sleep(WAIT_SEC)
    assert result_queue.get().replace(HEARTBEAT, '') == "test3"

    # test server.close
    client.close()
    s = server.get_console(caddr)
    time.sleep(clean_interval*5)
    assert not client.alive()
    assert not s.alive()
    assert not server.get_keys()


@pytest.mark.integration
@pytest.mark.timeout(10)
def test_server_double_run(caplog) -> None:
    # setup
    addr = ("localhost", 1235)
    server = SocketConsoleServer(*addr)
    # execute
    server.run()
    time.sleep(WAIT_SEC)
    assert not caplog.text
    server.run()
    assert any([record.levelname == "WARNING" for record in caplog.records])


@pytest.mark.integration
@pytest.mark.timeout(10)
def test_server_with_context() -> None:
    # setup
    addr = ("localhost", 1236)
    with SocketConsoleServer(*addr) as server:
        # execute
        assert server.alive()
        time.sleep(WAIT_SEC)
    # assert
    assert not server.alive()
