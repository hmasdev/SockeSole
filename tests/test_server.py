import socket
import threading
import pytest
from pytest_mock import MockerFixture
from sockesole import SocketConsoleServer, SocketConsole


def test_SocketConsoleServer_instantiation() -> None:
    # execute
    server = SocketConsoleServer("localhost", 1234)
    # assert
    assert server.server_address == ("localhost", 1234)
    assert server.buffer == 4096
    assert server.clean_interval == 5


@pytest.mark.parametrize(
    'keys',
    [
        [],
        [("localhost", 1234)],
        [("localhost", 1234), ("hoge", 8888)],
    ],
)
def test_SocketConsoleServer_get_keys(
    keys: list[tuple[str, int]],
    mocker: MockerFixture,
) -> None:
    # setup
    server = SocketConsoleServer("localhost", 1234)
    server._SocketConsoleServer__consoles = {  # type: ignore
        k: mocker.Mock(spec=SocketConsole)
        for k in keys
    }
    # execute
    actual = server.get_keys()
    # assert
    assert set(actual) == set(keys)


def test_SocketConsoleServer_get_console(
    mocker: MockerFixture,
) -> None:
    # setup
    server = SocketConsoleServer("localhost", 1234)
    addr = ("localhost", 1234)
    server._SocketConsoleServer__consoles = {  # type: ignore
        addr: SocketConsole(mocker.Mock(spec=socket.socket), addr)
    }
    # assert
    assert server.get_console(addr).client_address == addr


def test_SocketConsoleServer_run(
    mocker: MockerFixture,
) -> None:
    # setup
    placeholder1: str = ''
    placeholder2: str = ''

    def assign_expected_to_placeholder1() -> None:
        nonlocal placeholder1
        placeholder1 = threading.current_thread().name

    def assign_expected_to_placeholder2() -> None:
        nonlocal placeholder2
        placeholder2 = threading.current_thread().name

    server = SocketConsoleServer("localhost", 1234)
    mocker.patch.object(server, "_run", mocker.Mock(side_effect=assign_expected_to_placeholder1))  # noqa
    mocker.patch.object(server, "_periodical_clean", mocker.Mock(side_effect=assign_expected_to_placeholder2))  # noqa
    # execute
    assert not server.alive()
    server.run()
    # TODO: join is needed to ensure the threads are finished
    # assert
    assert server.alive()
    assert placeholder1
    assert placeholder2


def test_SocketConsoleServer__clean(
    mocker: MockerFixture,
) -> None:
    # setup
    server = SocketConsoleServer("localhost", 1234)
    addrs_alive_map = {
        ("hoge", 8888): True,
        ("fuga", 9999): False,
        ("piyo", 1111): True,
        ("localhost", 1234): False,
    }
    consoles = {
        addr: mocker.Mock(spec=SocketConsole)
        for addr in addrs_alive_map.keys()
    }
    for addr, alive in addrs_alive_map.items():
        consoles[addr].alive.return_value = alive
    server._SocketConsoleServer__consoles = {k: v for k, v in consoles.items()}  # type: ignore # noqa
    # execute
    server.clean()
    # assert
    for addr in addrs_alive_map.keys():
        if addrs_alive_map[addr]:
            assert addr in server._SocketConsoleServer__consoles.keys()  # type: ignore # noqa
            consoles[addr].close.assert_not_called()
        else:
            assert addr not in server._SocketConsoleServer__consoles.keys()  # type: ignore # noqa
            consoles[addr].close.assert_called_once()


def test_SocketConsoleServer_close(
    mocker: MockerFixture,
) -> None:
    # setup
    server = SocketConsoleServer("localhost", 1234)
    server._SocketConsoleServer__consoles = {  # type: ignore
        ("localhost", 1234): mocker.Mock(spec=SocketConsole),
        ("hoge", 8888): mocker.Mock(spec=SocketConsole),
    }
    server._SocketConsoleServer__running = True  # type: ignore
    # execute
    assert server.alive()
    server.close()
    # assert
    for console in server._SocketConsoleServer__consoles.values():  # type: ignore # noqa
        console.close.assert_called_once()
    assert len(server._SocketConsoleServer__consoles) == 0  # type: ignore
    assert not server.alive()


def test_SocketConsoleServer_alive():
    server = SocketConsoleServer("localhost", 1234)
    assert not server.alive()
    server._SocketConsoleServer__running = True  # type: ignore
    assert server.alive()
    server._SocketConsoleServer__running = False  # type: ignore
    assert not server.alive()
