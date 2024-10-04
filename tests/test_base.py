from pytest_mock import MockerFixture
from sockesole import (
    _BaseCloseAtDel,
    _BaseCloseAtExit,
)


def test_BaseCloseAtDel(mocker: MockerFixture) -> None:

    mock_func = mocker.Mock()

    class TestCloseAtDel(_BaseCloseAtDel):
        def close(self):
            mock_func()

    test = TestCloseAtDel()
    mock_func.assert_not_called()
    del test
    mock_func.assert_called_once()


def test_BaseCloseAtExit(mocker: MockerFixture) -> None:

    mock_func = mocker.Mock()

    class TestCloseAtExit(_BaseCloseAtExit):
        def close(self):
            mock_func()

    test = TestCloseAtExit()
    mock_func.assert_not_called()
    test.__exit__(None, None, None)
    mock_func.assert_called_once()


def test_BaseCloseAtExit_with_with_context(
    mocker: MockerFixture,
) -> None:

    mock_func = mocker.Mock()

    class TestCloseAtExit(_BaseCloseAtExit):
        def close(self):
            mock_func()

    mock_func.assert_not_called()
    with TestCloseAtExit():
        pass
    mock_func.assert_called_once()
