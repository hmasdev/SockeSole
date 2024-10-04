import threading
from sockesole import _run_in_daemon_thread


def test_run_in_daemon_thread() -> None:

    placeholder: str = ''

    def assign_expected_to_placeholder() -> None:
        nonlocal placeholder
        placeholder = threading.current_thread().name

    th = _run_in_daemon_thread(assign_expected_to_placeholder)
    th.join()
    assert placeholder
    assert placeholder == th.name
