from typing import Any, Generic, Iterator, Optional, Tuple, TypeVar, Union

_K = TypeVar('_K', bound=str)
_T = TypeVar('_T')


class Record(Generic[_K, _T]):
    """A read-only, dict-like representation of a PostgreSQL row.

    This class cannot be instantiated and was only provided for type
    hinting and introspection purposes as the `asyncpg` module does not
    expose type hints.

    """

    def __init__(self) -> None:
        """Dummy initialiser.

        This always raises a `NotImplementedError` to disallow
        instantiating this class. See the class docstring as to why
        this is not permitted.

        """
        raise NotImplementedError('This class cannot be instantiated directly')

    def __len__(self) -> int:
        """Return the number of columns in the row.

        Returns:
            int: The number of columns.

        """
        ...

    def __getattribute__(self, key: Union[int, _K]) -> _T:
        """Return the value stored for a given column.

        Args:
            key (Union[int, _K]): The column name to access, or the
                index of the column to access.

        Returns:
            _T: The value of the item accessed.

        Raises:
            KeyError: Raised if the column name is not found.
            IndexError: Raised if the column index is out of bounds.

        """
        ...

    def __contains__(self, element: Any) -> bool:
        """Return whether the given element is in the list of keys.

        Args:
            element (Any): The element to check for containment.

        Returns:
            bool: Whether the element is contained.

        """
        ...

    def __iter__(self) -> Iterator[_T]:
        """Return an iterator over the values of the row.

        Note that this iterates over the values, not the keys. This is
        different to dictionaries where a plain iterator would iterate
        over the keys instead.

        Returns:
            Iterator[_T]: An iterator over the row values.

        """
        ...

    def get(self, key: _K, default: Optional[_T] = None) -> _T:
        """Return the rojw's value for a given column.

        If the given key cannot be found, a `KeyError` will be raised
        if no `default` value has been specified.

        Args:
            key (_K): The name of the column whos value to access.
            default (_T, optional): A default value to return instead
                of raising a `KeyError` when an invalid key has been
                specified. Defaults to None.

        Returns:
            _T: The value of the row for the given column, or `default`
                if one has been provided.

        """
        ...

    def values(self) -> Iterator[_T]:
        """Return an iterator over the row values.

        Returns:
            Iterator[_T]: Iterator over the row values.

        """
        ...

    def keys(self) -> Iterator[_K]:
        """Return an iterator over the record field names."

        Returns:
            Iterator[_K]: Iterator over the columns.

        """
        ...

    def items(self) -> Iterator[Tuple[_K, _T]]:
        """Return an iterator over the key/value pairs.

        Returns:
            Tuple[_K, _T]: A column/value pair for this row.

        """
        ...
