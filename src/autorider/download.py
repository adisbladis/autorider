from urllib.parse import urlparse, parse_qs
import subprocess
import pathlib
import json


class HTTPDownload:
    url: str
    sha256: None | str

    def __init__(self, url: str, hash: None | str = None):
        self.url = url
        if hash:
            if not hash.startswith("sha256:"):
                raise ValueError("Only sha256 supported for http downloads")

            hash_type, sha256 = hash.split(":")
            if hash_type != "sha256":
                raise ValueError("only sha256 supported")

            self.sha256 = sha256

    def get(self):
        args = [
            "nix-instantiate",
            "--eval",
            "--json",
            "--expr",
            "{ url, sha256 ? null }@args: builtins.fetchurl args",
            "--argstr",
            "url",
            self.url,
        ]
        if self.sha256:
            args.extend(
                [
                    "--argstr",
                    "sha256",
                    self.sha256,
                ]
            )

        p = subprocess.run(args, stdout=subprocess.PIPE, check=True)
        result = json.loads(p.stdout)  # pyright: ignore[reportAny]
        if not isinstance(result, str):
            raise ValueError("result json not string")

        return pathlib.Path(result)


class GitDownload:
    url: str

    def __init__(self, url: str):
        self.url = url

    def get(self):
        args = [
            "nix-instantiate",
            "--eval",
            "--json",
            "--expr",
            "{ url }: builtins.fetchGit url",
            "--argstr",
            "url",
            self.url,
        ]

        url_parsed = urlparse(self.url)
        query = parse_qs(url_parsed.query)

        p = subprocess.run(args, stdout=subprocess.PIPE, check=True)
        result = json.loads(p.stdout)  # pyright: ignore[reportAny]
        if not isinstance(result, str):
            raise ValueError("result json not string")

        path = pathlib.Path(result)
        for subdirectory in query.get("subdirectory", []):
            path = path.joinpath(subdirectory)

        return path
