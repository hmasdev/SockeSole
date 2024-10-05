from abc import ABC, abstractmethod
from logging import getLogger, Logger
import socket
from threading import Lock, Thread
import time
from typing import Callable, Protocol, runtime_checkable, TypeVar

# const
HEARTBEAT: str = '__HB__'
Address = tuple[str, int]

# types
TSocketConsole = TypeVar('TSocketConsole', bound='SocketConsole')
TSocketConsoleServer = TypeVar('TSocketConsoleServer', bound='SocketConsoleServer')  # noqa
TSocketConsoleClient = TypeVar('TSocketConsoleClient', bound='SocketConsoleClient')  # noqa


@runtime_checkable
class ConsoleProtocol(Protocol):
    """Protocol for server-side console.
    """

    def echo(self, msg: str) -> None:
        """Echo message to client console.

        Args:
            msg (str): Message to echo.
        """
        raise NotImplementedError()

    def prompt(self, msg: str, *args, **kwargs) -> str:
        """Prompt message to client console and get input.

        Args:
            msg (str): Message to prompt.

        Returns:
            str: input from client.
        """
        raise NotImplementedError()


@runtime_checkable
class ReadWriteProtocol(Protocol):
    """Protocol for client-side console.
    """

    def read(self, *args, **kwargs) -> str:
        """Read message from server.

        Returns:
            str: message from server.
        """
        raise NotImplementedError()

    def write(self, msg: str) -> None:
        """Write message to server.

        Args:
            msg (str): message to write.
        """
        raise NotImplementedError()


class _BaseCloseAtDel(ABC):
    """Base class to call close in __del__.
    """

    @abstractmethod
    def close(self):
        """Close the object.
        """
        pass

    def __del__(self):
        self.close()


class _BaseCloseAtExit(ABC):
    """Base class to call close in __exit__.
    """

    @abstractmethod
    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class _BaseAliveCheckable(ABC):
    """Base class to check if object is alive.
    """

    @abstractmethod
    def alive(self) -> bool:
        """Check if object is alive.
        """
        pass


def _run_in_daemon_thread(func: Callable[..., None]) -> Thread:
    """Run function in a daemon thread.

    Args:
        func (Callable[..., None]): Function to run.

    Returns:
        Thread: Thread to run the function.
    """
    th = Thread(target=func)
    th.daemon = True
    th.start()
    return th


class SocketConsole(
    ConsoleProtocol,
    _BaseAliveCheckable,
    _BaseCloseAtDel,
):
    '''Wrapper for socket connection to act as a console.'''

    def __init__(
        self,
        conn: socket.socket,
        client_address: Address,
        buffer: int = 4096,
        logger: Logger = getLogger(__name__),
    ) -> None:
        self.conn = conn
        self.client_address = client_address
        self.buffer = buffer
        self.logger = logger

    def echo(self, msg: str) -> None:
        """Echo message to client console.

        Args:
            msg (str): Message to echo.
        """
        self.logger.debug("echo called")
        self.conn.sendall(msg.encode())

    def prompt(
        self,
        msg: str,
        wait: float = 0,
        timeout: float = 60,
        delete_heartbeat: bool = True,
    ) -> str:
        """Prompt message to client console and get input.

        Args:
            msg (str): Message to prompt.
            wait (float, optional): interval to wait. Defaults to 0.
            timeout (float, optional): timeout to wait. Defaults to 60.
            delete_heartbeat (bool, optional): delete heartbeat from message. Defaults to True.

        Raises:
            TimeoutError: raised when timeout.

        Returns:
            str: input from client.
        """  # noqa
        s = time.perf_counter()
        self.logger.debug("prompt called")
        # send
        if msg:
            self.conn.sendall(msg.encode())
        # receive
        rmsg = self.conn.recv(self.buffer).decode('utf-8')
        while (
            wait > 0
            and not rmsg.replace(HEARTBEAT, '')
        ):
            time.sleep(wait)
            rmsg = self.conn.recv(self.buffer).decode('utf-8')
            if time.perf_counter() - s >= timeout:
                raise TimeoutError("prompt timeout")
        return rmsg.replace(HEARTBEAT, '') if delete_heartbeat else rmsg

    def alive(self) -> bool:
        """Check if connection is alive.

        Returns:
            bool: True if alive, False otherwise.
        """
        try:
            self.conn.sendall(HEARTBEAT.encode())
            return True
        except Exception as e:
            self.logger.info(f"Connection from {self.client_address} lost: {e}")  # noqa
            return False

    def close(self):
        """Close the connection.
        """
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()
        self.logger.info(f"Connection from {self.client_address} closed")


class SocketConsoleServer(
    _BaseAliveCheckable,
    _BaseCloseAtDel,
    _BaseCloseAtExit,
):
    def __init__(
        self,
        host: str,
        port: int,
        buffer: int = 4096,
        queue_size: int = 5,
        clean_interval: float = 5,
        console_cls: type[SocketConsole] = SocketConsole,
        logger: Logger = getLogger(__name__),
    ) -> None:
        self._host = host
        self._port = port
        self._queue_size = queue_size
        self._console_cls = console_cls
        self.buffer = buffer
        self.clean_interval = clean_interval
        self.logger = logger

        self.__running: bool = False

        self.__consoles: dict[Address, SocketConsole] = {}
        self.__lock: Lock = Lock()

    @property
    def server_address(self) -> Address:
        return (self._host, self._port)

    def get_console(self, addr: Address) -> SocketConsole:
        """Get console by address.

        Args:
            addr (Address): address of the console.

        Returns:
            SocketConsole: console object.
        """
        with self.__lock:
            return self.__consoles[addr]

    def get_keys(self) -> list[Address]:
        """Get keys of consoles.

        Returns:
            list[Address]: list of addresses of consoles.
        """
        with self.__lock:
            return list(self.__consoles.keys())

    def run(self) -> None:
        """Run the server. If already running, do nothing.
        """
        if self.__running:
            self.logger.warning("Server already running")
            return
        with self.__lock:
            self.__running = True
        _run_in_daemon_thread(self._run)
        self.logger.info(f"Server started at {self.server_address}")
        _run_in_daemon_thread(self._periodical_clean)
        self.logger.info("Cleaner started")

    def _run(self) -> None:
        """Run the server. Keep listening for connections.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(self.server_address)
            server.listen(self._queue_size)
            self.logger.info(f"Listening on {self.server_address}")
            while True:
                try:
                    conn, addr = server.accept()
                    self.logger.info(f"Connection from {addr}")
                    console = self._console_cls(
                        conn=conn,
                        client_address=addr,
                        buffer=self.buffer,
                    )
                    with self.__lock:
                        self.__consoles[tuple(addr)] = console
                except Exception as e:
                    self.logger.error(f"Error in server: {e}")

    def clean(self) -> None:
        """Clean dead connections.
        """
        with self.__lock:
            removed_addrs: list[Address] = []
            for addr, console in self.__consoles.items():
                if not console.alive():
                    self.logger.info(f"Connection from {addr} lost")
                    console.close()
                    removed_addrs.append(addr)
            for removed_addr in removed_addrs:
                self.logger.info(f"Connection from {removed_addr} removed")
                del self.__consoles[removed_addr]

    def _periodical_clean(self) -> None:
        """Periodically clean dead connections.
        """
        while self.__running:
            time.sleep(self.clean_interval)
            self.clean()

    def close(self) -> None:
        """Close the server.
        """
        with self.__lock:
            self.__running = False
            for console in self.__consoles.values():
                console.close()
        self.logger.info("Server closed")
        self.__consoles.clear()

    def alive(self) -> bool:
        """Check if server is alive.

        Returns:
            bool: True if alive, False otherwise.
        """
        with self.__lock:
            return self.__running

    def __enter__(self):
        self.run()
        return super().__enter__()


class SocketConsoleClient(
    ReadWriteProtocol,
    _BaseAliveCheckable,
    _BaseCloseAtDel,
    _BaseCloseAtExit,
):

    def __init__(
        self,
        conn: socket.socket,
        *,
        buffer: int = 4096,
        logger: Logger = getLogger(__name__),
    ) -> None:
        self.__conn = conn
        self.buffer = buffer
        self.logger = logger

    @classmethod
    def connect(
        cls: type[TSocketConsoleClient],
        host: str,
        port: int,
        **kwargs,
    ) -> TSocketConsoleClient:
        """Connect to server.

        Args:
            host (str): server host.
            port (int): server port.

        Returns:
            SocketConsoleClient: client object.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return cls(sock, **kwargs)

    def read(
        self,
        wait: float = 0,
        timeout: float = 60,
        delete_heartbeat: bool = True,
    ) -> str:
        """Read message from server.

        Args:
            wait (float, optional): interval to wait. Defaults to 0.
            timeout (float, optional): timeout to wait. Defaults to 60.
            delete_heartbeat (bool, optional): delete heartbeat from message. Defaults to True.

        Raises:
            TimeoutError: raised when timeout.

        Returns:
            str: message from server.
        """  # noqa
        s = time.perf_counter()
        msg = self.__conn.recv(self.buffer).decode('utf-8')
        while (
            wait > 0
            and not msg.replace(HEARTBEAT, '')
        ):
            time.sleep(wait)
            msg = self.read(wait, timeout, delete_heartbeat)
            if time.perf_counter() - s >= timeout:
                raise TimeoutError("read timeout")
        return msg.replace(HEARTBEAT, '') if delete_heartbeat else msg

    def write(self, msg: str) -> None:
        """Write message to server.

        Args:
            msg (str): message to write.
        """
        self.__conn.sendall(msg.encode())

    def alive(self) -> bool:
        """Check if connection is alive.

        Returns:
            bool: True if alive, False otherwise.
        """
        try:
            self.__conn.sendall(HEARTBEAT.encode())
            return True
        except Exception as e:
            self.logger.info(f"Connection lost: {e}")
            return False

    def close(self):
        """Close the connection.
        """
        self.__conn.shutdown(socket.SHUT_RDWR)
        self.__conn.close()
        self.logger.info("Connection closed")
