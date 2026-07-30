from __future__ import annotations

import paramiko

from ariadne.config import SFTPConfig


class SFTPClient:
    def __init__(self, config: SFTPConfig):
        self._config = config
        self._transport: paramiko.Transport | None = None
        self._sftp: paramiko.SFTPClient | None = None

    def connect(self):
        self._transport = paramiko.Transport((self._config.host, self._config.port))
        self._transport.connect(
            username=self._config.username,
            password=self._config.password,
        )
        self._sftp = paramiko.SFTPClient.from_transport(self._transport)

    def upload_file(self, local_path: str, remote_filename: str | None = None) -> str:
        if self._sftp is None:
            self.connect()
        filename = remote_filename or local_path.split("/")[-1].split("\\")[-1]
        remote_path = f"{self._config.remote_path}/{filename}"
        self._sftp.put(local_path, remote_path)
        return remote_path

    def download_file(self, remote_path: str, local_path: str):
        if self._sftp is None:
            self.connect()
        self._sftp.get(remote_path, local_path)

    def list_dir(self, remote_dir: str | None = None) -> list[str]:
        if self._sftp is None:
            self.connect()
        path = remote_dir or self._config.remote_path
        return self._sftp.listdir(path)

    def close(self):
        if self._sftp:
            self._sftp.close()
        if self._transport:
            self._transport.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
