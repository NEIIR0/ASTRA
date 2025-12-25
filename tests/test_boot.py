from airi import __version__


def test_imports():
    assert isinstance(__version__, str)
