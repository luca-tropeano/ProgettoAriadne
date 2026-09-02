from __future__ import annotations

import pytest

from ariadne.config import SFTPConfig
from ariadne.sftp_client import SFTPClient


class FakeTransport:
    def __init__(self, addr):
        self.addr = addr
        self.closed = False

    def connect(self, **kwargs):
        self.kwargs = kwargs

    def close(self):
        self.closed = True


class FakeSFTP:
    def __init__(self):
        self.put_calls = []
        self.get_calls = []
        self.listdir_calls = []
        self.closed = False

    def put(self, local, remote):
        self.put_calls.append((local, remote))

    def get(self, remote, local):
        self.get_calls.append((remote, local))

    def listdir(self, path):
        self.listdir_calls.append(path)
        return ["a.csv", "b.csv"]

    def close(self):
        self.closed = True


@pytest.fixture
def fake_sftp(monkeypatch):
    transport = FakeTransport(("host", 22))
    sftp = FakeSFTP()
    monkeypatch.setattr("ariadne.sftp_client.paramiko.Transport", lambda addr: transport)
    monkeypatch.setattr("ariadne.sftp_client.paramiko.SFTPClient.from_transport", lambda t: sftp)
    return transport, sftp


def test_connect_sets_transport_and_sftp(fake_sftp):
    transport, sftp = fake_sftp
    client = SFTPClient(SFTPConfig(host="host", username="u", password="p"))
    client.connect()
    assert client._transport is transport
    assert client._sftp is sftp
    assert transport.kwargs["username"] == "u"
    assert transport.kwargs["password"] == "p"


def test_upload_file_returns_remote_path(fake_sftp):
    _, sftp = fake_sftp
    client = SFTPClient(SFTPConfig(host="host", remote_path="/uploads"))
    client.connect()
    remote = client.upload_file(r"C:\data\board.csv")
    assert remote == "/uploads/board.csv"
    assert sftp.put_calls == [(r"C:\data\board.csv", "/uploads/board.csv")]


def test_upload_file_auto_connects(fake_sftp):
    transport, sftp = fake_sftp
    client = SFTPClient(SFTPConfig(host="host", remote_path="/uploads"))
    remote = client.upload_file("local/bom.xlsx")
    assert transport is not None
    assert remote == "/uploads/bom.xlsx"
    assert len(sftp.put_calls) == 1


def test_upload_with_custom_remote_name(fake_sftp):
    _, sftp = fake_sftp
    client = SFTPClient(SFTPConfig(host="host", remote_path="/uploads"))
    client.connect()
    remote = client.upload_file("local.csv", remote_filename="renamed.csv")
    assert remote == "/uploads/renamed.csv"


def test_download_file(fake_sftp):
    _, sftp = fake_sftp
    client = SFTPClient(SFTPConfig(host="host"))
    client.connect()
    client.download_file("/uploads/a.csv", "./a.csv")
    assert sftp.get_calls == [("/uploads/a.csv", "./a.csv")]


def test_list_dir(fake_sftp):
    _, sftp = fake_sftp
    client = SFTPClient(SFTPConfig(host="host", remote_path="/uploads"))
    client.connect()
    assert client.list_dir() == ["a.csv", "b.csv"]
    assert client.list_dir("/other") == ["a.csv", "b.csv"]
    assert sftp.listdir_calls == ["/uploads", "/other"]


def test_close_without_connect_no_error():
    client = SFTPClient(SFTPConfig(host=""))
    client.close()


def test_close_closes_sftp_and_transport(fake_sftp):
    transport, sftp = fake_sftp
    client = SFTPClient(SFTPConfig(host="host"))
    client.connect()
    client.close()
    assert sftp.closed is True
    assert transport.closed is True


def test_context_manager_connects_and_closes(fake_sftp):
    transport, sftp = fake_sftp
    with SFTPClient(SFTPConfig(host="host")) as client:
        assert client._transport is transport
    assert sftp.closed is True