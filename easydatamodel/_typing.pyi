import typing
from _typeshed import Incomplete

class UnassignedType:
    __class_getitem__: Incomplete

UNASSIGNED: Incomplete

def check_type(value: typing.Any, type_: typing.Any, check_class: bool = False, namespace: dict[str, typing.Any] | None = None, suppress_exceptions: bool = False) -> bool: ...
def is_literal_type(t: typing.Any) -> bool: ...
def is_nested_generic_alias(t: typing.Any) -> bool: ...
def is_classvar(t: typing.Any) -> bool: ...
def is_optional_type(t: typing.Any) -> bool: ...
def is_union_type(t: typing.Any) -> bool: ...
def is_alias(t: typing.Any) -> bool: ...
def is_Type(t: typing.Any) -> bool: ...
