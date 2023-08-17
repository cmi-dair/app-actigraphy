""" Tests for the IO module. """
import pathlib

from actigraphy.io import metadata, ms4, utils


def test_snakecase_all_uppercase() -> None:
    """Test snakecase with an all uppercase string."""
    expected = "alluppercase"

    actual = utils.snakecase("ALLUPPERCASE")

    assert actual == expected


def test_snakecase_all_uppercase_with_nonletter() -> None:
    """Test snakecase with an all uppercase string."""
    expected = "alluppercase4"

    actual = utils.snakecase("ALLUPPERCASE4")

    assert actual == expected


def test_snakecase_from_camelcase() -> None:
    """Test snakecase with a camelcase string."""
    expected = "camel_case"

    actual = utils.snakecase("camelCase")

    assert actual == expected


def test_snakecase_from_snakecase() -> None:
    """Test snakecase with a snakecase string."""
    expected = "snake_case"

    actual = utils.snakecase("snake_case")

    assert actual == expected


def test_snakecase_from_pascalcase() -> None:
    """Test snakecase with a pascalcase string."""
    expected = "pascal_case"

    actual = utils.snakecase("PascalCase")

    assert actual == expected


def test_snakecase_from_consecutive_uppercase() -> None:
    """Test snakecase with a string with consecutive uppercase letters."""
    expected = "consecutive_uppercase"

    actual = utils.snakecase("COnsecutiveUppercase")

    assert actual == expected


def test_ms4(data_dir: pathlib.Path) -> None:
    """Test the MS4 class."""
    ms4_data = ms4.MS4.from_file(data_dir / "ms4.RData")

    assert ms4_data[0].night == 1


def test_metadata(data_dir: pathlib.Path) -> None:
    """Test the Metadata class."""
    metadata_data = metadata.MetaData.from_file(data_dir / "metadata.RData")

    assert metadata_data.filefoldername == "raw_data"
