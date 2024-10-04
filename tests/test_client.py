import socket
from pytest_mock import MockerFixture
from sockesole import SocketConsoleClient


def test_SocketConsoleClient_instantiation(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock()
    client = SocketConsoleClient(mock_socket)
    assert client.buffer == 4096


def test_SocketConsoleClient_close(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock()
    client = SocketConsoleClient(mock_socket)
    client.close()
    mock_socket.shutdown.assert_called_once_with(socket.SHUT_RDWR)
    mock_socket.close.assert_called_once()


def test_SocketConsoleClient_alive_is_True(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock()
    client = SocketConsoleClient(mock_socket)
    assert client.alive()


def test_SocketConsoleClient_alive_is_False(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock()
    mock_socket.sendall.side_effect = Exception
    client = SocketConsoleClient(mock_socket)
    assert not client.alive()


def test_SocketConsoleClient_read(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock()
    client = SocketConsoleClient(mock_socket)
    mock_socket.recv.return_value = b"ret"
    assert client.read() == "ret"
    mock_socket.recv.assert_called_once_with(4096)


def test_SocketConsoleClient_write(
    mocker: MockerFixture,
) -> None:
    mock_socket = mocker.Mock()
    client = SocketConsoleClient(mock_socket)
    client.write("test")
    mock_socket.sendall.assert_called_once_with(b"test")
