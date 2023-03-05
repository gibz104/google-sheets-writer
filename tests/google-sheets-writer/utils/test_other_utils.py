import pytest

from google_sheets_writer.utils.other_utils import chunk_list
from unittest.mock import MagicMock, PropertyMock, call, mock_open, patch


@pytest.fixture
def example_list_data():
    """
    Fixture is used to provide example data for testing. Can be passed
    to test functions as a parameter.
    """
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_chunk_list(benchmark, example_list_data):
    # Run benchmark test
    benchmark(chunk_list, example_list_data, 3)

    # Test normal functionality (chunking data)
    chunked_data = chunk_list(example_list_data, chunk_size=3)
    assert chunked_data == [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

    # Test chunk_size > input size (one chunk)
    chunked_data = chunk_list(example_list_data, chunk_size=12)
    assert chunked_data == [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]

    # Test chunk_size of None (no chunking)
    chunked_data = chunk_list(example_list_data, chunk_size=None)
    assert chunked_data == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
