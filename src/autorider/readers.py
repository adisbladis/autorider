from typing import Callable, IO
from pathlib import Path
from typing import override
import zipfile
import tarfile
import os


PRED_T = Callable[[str], bool]
CALLBACK_T = Callable[[str, IO[bytes]], None]


class Reader:
    path: Path
    pred: PRED_T
    callback: CALLBACK_T

    def __init__(self, path: Path, pred: PRED_T, callback: CALLBACK_T) -> None:
        self.path = path
        self.pred = pred
        self.callback = callback

    def run(self) -> None:
        raise NotImplementedError("Not implemented")


class ZipReader(Reader):
    @override
    def run(self):
        with zipfile.ZipFile(self.path) as zip:
            for name in zip.namelist():
                if self.pred(name):
                    with zip.open(name) as fp:
                        self.callback(name, fp)


class TarReader(Reader):
    @override
    def run(self):
        with tarfile.open(self.path) as tar:
            for member in tar.getmembers():
                if self.pred(member.name):
                    fp = tar.extractfile(member)
                    if not fp:
                        raise ValueError(f"Unable to open tar member '{member}'")
                    with fp:
                        self.callback(member.name, fp)


class DirReader(Reader):
    @override
    def run(self):
        for root, _, files in os.walk(self.path):
            for filename in files:
                member_path = os.path.join(root, filename)
                if self.pred(member_path):
                    with open(member_path, "rb") as fp:
                        self.callback(member_path, fp)
