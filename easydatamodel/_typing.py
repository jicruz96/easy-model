"""Module with type checking helpers."""

from __future__ import annotations

import inspect
import types
import typing
from typing import GenericAlias  # type: ignore
from typing import _GenericAlias  # type: ignore
from typing import _SpecialGenericAlias  # type: ignore
from typing import _UnionGenericAlias  # type: ignore


class UnassignedType:
    """Used to represent unassigned values.

    This is preferable over using `None` since it's possible a user may ntend to explicitly assign `None` to a value.
    """

    def __repr__(self) -> str:
        return "UNASSIGNED"

    __class_getitem__ = classmethod(typing.GenericAlias)  # type: ignore


UNASSIGNED = UnassignedType()


def check_type(
    value: typing.Any,
    type_: typing.Any,
    check_class: bool = False,
    namespace: dict[str, typing.Any] | None = None,
    suppress_exceptions: bool = False,
) -> bool:
    """
    Check if a value matches a specified type.

    Args:
        value: The value to be checked.
        type_: The type to check against.
        check_class: Optional. Whether to check if the value is a subclass of the specified type. Defaults to False.
        namespace: Optional. The namespace to use to evaluate the type if the type is a string. Defaults to None.
        suppress_exceptions: Optional. Whether to suppress exceptions when the value does not match the type.
            Defaults to False.

    Returns:
        bool: True if the value matches the type, False otherwise.

    Raises:
        TypeError: If the value does not match the type and suppress_exceptions is False.

    """
    if isinstance(type_, str):
        type_ = eval(type_, namespace)

    if type_ is typing.Any:
        return True

    if type_ is None:
        is_correct = value is None
        if not is_correct and not suppress_exceptions:
            raise TypeError(f"Got value {value!r}. Expected None")
        return is_correct

    if is_literal_type(type_):
        is_correct = value in type_.__args__
        if not is_correct and not suppress_exceptions:
            raise TypeError(f"Got value {value!r}. Expected one of: {', '.join(f'{arg!r}' for arg in type_.__args__)}")

    if is_union_type(type_):
        return _validate_nested_types(value, type_.__args__, check_class, namespace, suppress_exceptions)

    if isinstance(type_, typing.ForwardRef):
        return check_type(value, type_.__forward_arg__, check_class, namespace, suppress_exceptions)

    if is_alias(type_):
        return check_type(value, type_.__origin__, check_class, namespace, suppress_exceptions)

    if is_classvar(type_) or is_optional_type(type_) or is_Type(type_):
        if len(type_.__args__) != 1:
            raise TypeError("ClassVar, Optional, and Type should have exactly one argument")
        check_class = is_Type(type_)
        return check_type(value, type_.__args__[0], check_class, namespace, suppress_exceptions)

    if check_class:
        is_correct_type = inspect.isclass(value) and issubclass(value, type_)
    else:
        is_correct_type = isinstance(value, type_)
    if not is_correct_type and not suppress_exceptions:
        expected_type = (type_.__class__ if check_class else type_).__name__  # type: ignore
        raise TypeError(
            f"Got value {value!r} (of type {type(value).__name__}). Expected a value of type {expected_type}"
        )
    return is_correct_type


def is_literal_type(t: typing.Any) -> bool:
    return is_nested_generic_alias(t) and t.__origin__ is typing.Literal


def is_nested_generic_alias(t: typing.Any) -> bool:
    return isinstance(t, (GenericAlias, _GenericAlias)) and hasattr(t, "__origin__") and hasattr(t, "__args__")


def is_classvar(t: typing.Any) -> bool:
    return t is typing.ClassVar or (is_nested_generic_alias(t) and t.__origin__ is typing.ClassVar)


def is_optional_type(t: typing.Any) -> bool:
    return (
        isinstance(t, _UnionGenericAlias)
        and t._name == "typing.Optional"
        or (is_union_type(t) and type(None) in t.__args__)
    )


def is_union_type(t: typing.Any) -> bool:
    return isinstance(t, types.UnionType) or isinstance(t, _UnionGenericAlias)


def is_alias(t: typing.Any) -> bool:
    return is_nested_generic_alias(t) or isinstance(t, _SpecialGenericAlias)


def is_Type(t: typing.Any) -> bool:
    return is_nested_generic_alias(t) and t.__name__ == "Type"


def _validate_nested_types(
    value: typing.Any,
    types: tuple[type, ...],
    check_class: bool,
    namespace: dict[str, typing.Any] | None,
    suppress_exceptions: bool,
) -> bool:
    for type_ in types:
        try:
            if check_type(value, type_, check_class, namespace, suppress_exceptions) is True:
                return True
        except TypeError:
            continue
    if suppress_exceptions is False:
        error_message = f"Invalid value {value!r} of type {type(value)} must be "
        if check_class:
            error_message += "a subclass of "
        error_message += f"one of: {', '.join(map(str, types))}"
        raise TypeError(error_message)
    return False


if __name__ == "__main__":
    from typing import List, Tuple

    int_or_str = int | str

    class Foo:
        pass

    class InheritedFoo(Foo):
        pass

    test_cases = [
        check_type(None, None),
        check_type(None, typing.Optional[int]),
        check_type(1, int_or_str),
        check_type([], list),
        check_type([], List),
        check_type([], list[int]),
        check_type([], List[int]),
        check_type(tuple(), tuple),
        check_type(tuple(), Tuple),
        check_type(tuple(), Tuple[int | str, ...]),
        check_type(True, bool),
        check_type({}, dict),
        check_type({}, dict[str, str]),
        check_type(1, typing.ForwardRef("int")),
        check_type("not an int", typing.ForwardRef("int"), suppress_exceptions=True) is False,
        check_type(InheritedFoo, typing.Type[Foo]),
    ]
    assert all(test_cases)
