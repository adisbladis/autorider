from autorider.lib import nix_locate_file


def test_nix_locate_file():
    assert nix_locate_file("thisfiledoesnotexist") is None
    assert nix_locate_file("libsane.so.1") == "sane-backends.out"
