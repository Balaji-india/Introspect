import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import start_demo  # noqa: E402


def test_dependencies_are_importable():
    assert start_demo.check_imports()


def test_port_detection():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        assert not start_demo.port_free(port)
        assert not start_demo.is_introspect(port)
