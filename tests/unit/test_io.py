""" Tests for the IO module. """
# pylint: disable=protected-access
import pathlib

from actigraphy.io import metadata


def test_snakecase_all_uppercase() -> None:
    """Test snakecase with an all uppercase string."""
    expected = "alluppercase"

    actual = metadata._snakecase("ALLUPPERCASE")

    assert actual == expected


def test_snakecase_all_uppercase_with_nonletter() -> None:
    """Test snakecase with an all uppercase string."""
    expected = "alluppercase4"

    actual = metadata._snakecase("ALLUPPERCASE4")

    assert actual == expected


def test_snakecase_from_camelcase() -> None:
    """Test snakecase with a camelcase string."""
    expected = "camel_case"

    actual = metadata._snakecase("camelCase")

    assert actual == expected


def test_snakecase_from_snakecase() -> None:
    """Test snakecase with a snakecase string."""
    expected = "snake_case"

    actual = metadata._snakecase("snake_case")

    assert actual == expected


def test_snakecase_from_pascalcase() -> None:
    """Test snakecase with a pascalcase string."""
    expected = "pascal_case"

    actual = metadata._snakecase("PascalCase")

    assert actual == expected


def test_snakecase_from_consecutive_uppercase() -> None:
    """Test snakecase with a string with consecutive uppercase letters."""
    expected = "consecutive_uppercase"

    actual = metadata._snakecase("COnsecutiveUppercase")

    assert actual == expected


def test_metadata(data_dir: pathlib.Path) -> None:
    """Test the Metadata class."""
    metadata_data = metadata.MetaData.from_file(data_dir / "metadata.RData")

    assert metadata_data.filefoldername == "raw_data"
