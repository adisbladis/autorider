from autorider.scanners import ScanResult
from autorider.uv import lock1


def scan_fixture(fixture: str) -> ScanResult:
    lock = lock1.loads(fixture)
    assert len(lock["package"]) == 1
    return lock1.scan_pkg(lock["package"][0])


def test_sdist_url():
    scan_result = scan_fixture("""
    version = 1
    requires-python = ">=3.12"

    [[package]]
    name = "packaging"
    version = "24.2"
    source = { registry = "https://pypi.org/simple" }
    sdist = { url = "https://files.pythonhosted.org/packages/d0/63/68dbb6eb2de9cb10ee4c9c14a0148804425e13c4fb20d61cce69f53106da/packaging-24.2.tar.gz", hash = "sha256:c228a6dc5e932d346bc5739379109d49e8853dd8223571c7c5b55260edc0b97f", size = 163950 }
    wheels = [
        { url = "https://files.pythonhosted.org/packages/88/ef/eb23f262cca3c0c4eb7ab1933c3b1f03d021f2c48f54763065b6f0e321be/packaging-24.2-py3-none-any.whl", hash = "sha256:09abb1bccd265c01f4a3aa3f7a7db064b36514d2cba19a2f694fe6150451a759", size = 65451 },
    ]
    """)
    assert scan_result.wheel == None
    assert scan_result.sdist.build_systems == ["flit_core >=3.3"]


def test_sdist_path():
    scan_result = scan_fixture("""
    version = 1
    requires-python = ">=3.12"

    [[package]]
    name = "attrs"
    version = "23.1.0"
    source = { path = "./fixtures/attrs-23.1.0.tar.gz" }
    sdist = { hash = "sha256:6279836d581513a26f1bf235f9acd333bc9115683f14f7e8fae46c98fc50e015" }
    """)
    assert scan_result.wheel == None
    assert scan_result.sdist.build_systems == [
        "hatchling",
        "hatch-vcs",
        "hatch-fancy-pypi-readme",
    ]


def test_git():
    scan_result = scan_fixture("""
    version = 1
    requires-python = ">=3.12"

    [[package]]
    name = "hatchling"
    version = "1.27.0"
    source = { git = "https://github.com/pypa/hatch.git?subdirectory=backend&rev=hatchling-v1.27.0#cbf6598e5cbce3ba9097023c5bf783001ebbcbcb" }
    """)
    assert scan_result.wheel == None
    assert scan_result.sdist.build_systems == ["setuptools"]


def test_wheel():
    # Note: Not a manylinux wheel
    scan_result = scan_fixture("""
    [[package]]
    name = "attrs"
    version = "23.1.0"
    source = { registry = "https://pypi.org/simple" }
    wheels = [
        { url = "https://files.pythonhosted.org/packages/f0/eb/fcb708c7bf5056045e9e98f62b93bd7467eb718b0202e7698eb11d66416c/attrs-23.1.0-py3-none-any.whl", hash = "sha256:1f28b4522cdc2fb4256ac1a020c78acf9cba2c6b461ccd2c126f3aa8e8335d04", size = 61160 },
    ]
    """)
    assert scan_result.wheel == None
    assert scan_result.sdist == None


def test_manylinux_wheel():
    scan_result = scan_fixture("""
    [[package]]
    name = "pyzmq"
    version = "26.2.1"
    source = { registry = "https://pypi.org/simple" }
    dependencies = [
        { name = "cffi", marker = "(implementation_name == 'pypy' and platform_machine == 'aarch64' and sys_platform == 'linux') or (implementation_name == 'pypy' and platform_machine == 'x86_64' and sys_platform == 'linux')" },
    ]
    sdist = { url = "https://files.pythonhosted.org/packages/5a/e3/8d0382cb59feb111c252b54e8728257416a38ffcb2243c4e4775a3c990fe/pyzmq-26.2.1.tar.gz", hash = "sha256:17d72a74e5e9ff3829deb72897a175333d3ef5b5413948cae3cf7ebf0b02ecca", size = 278433 }
    wheels = [
      { url = "https://files.pythonhosted.org/packages/c3/25/0b4824596f261a3cc512ab152448b383047ff5f143a6906a36876415981c/pyzmq-26.2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:786dd8a81b969c2081b31b17b326d3a499ddd1856e06d6d79ad41011a25148da", size = 865416 },
    ]
    """)

    assert scan_result.sdist.build_systems == [
        "cffi; implementation_name == 'pypy'",
        "cython>=3.0.0; implementation_name != 'pypy'",
        "packaging",
        "scikit-build-core",
    ]

    assert scan_result.wheel.native_depends == {
        "libsodium-53576c4c.so.26.2.0",
        "libgcc_s.so.1",
        "libpthread.so.0",
        "libstdc++.so.6",
        "ld-linux-x86-64.so.2",
        "librt.so.1",
        "libc.so.6",
        "libzmq-47dc3393.so.5.2.5",
        "libm.so.6",
    }
    assert scan_result.wheel.native_provides == {
        "libzmq-47dc3393.so.5.2.5",
        "_zmq.cpython-312-x86_64-linux-gnu.so",
        "libsodium-53576c4c.so.26.2.0",
    }
