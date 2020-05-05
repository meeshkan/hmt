from hmt.build.result import BuildResult
from hmt.build.writer import write_build_result

from .abstract import AbstractSink


class FileSystemSink(AbstractSink):
    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        self.result = None

    def push(self, result: BuildResult) -> None:
        self.result = result

    def flush(self) -> None:
        if self.result is None:
            return
        write_build_result(self.out_dir, result=self.result)
