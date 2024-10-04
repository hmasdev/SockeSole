import socket
from pytest_mock import MockerFixture
from sockesole import SocketConsole


def test_SocketConsole_instantiation(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock(spec=socket.socket)
    SocketConsole(mock_socket, ("localhost", 1234))


def test_SocketConsole_close(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock(spec=socket.socket)
    console = SocketConsole(mock_socket, ("localhost", 1234))
    console.close()
    mock_socket.shutdown.assert_called_once_with(socket.SHUT_RDWR)
    mock_socket.close.assert_called_once()


def test_SocketConsole_echo(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock(spec=socket.socket)
    console = SocketConsole(mock_socket, ("localhost", 1234))
    console.echo("test")
    mock_socket.sendall.assert_called_once_with(b"test")


def test_SocketConsole_prompt(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock(spec=socket.socket)
    console = SocketConsole(mock_socket, ("localhost", 1234))
    mock_socket.recv.return_value = b"ret"
    assert console.prompt("test") == "ret"
    mock_socket.sendall.assert_called_once_with(b"test")
    mock_socket.recv.assert_called_once_with(4096)


def test_SocketConsole_alive_is_True(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock(spec=socket.socket)
    console = SocketConsole(mock_socket, ("localhost", 1234))
    assert console.alive()


def test_SocketConsole_alive_is_False(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock(spec=socket.socket)
    mock_socket.sendall.side_effect = Exception
    console = SocketConsole(mock_socket, ("localhost", 1234))
    assert not console.alive()
