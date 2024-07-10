from ._typing import UNASSIGNED as UNASSIGNED
from .exceptions import InvalidModelError as InvalidModelError
from .field import FieldInfo as FieldInfo, ModelFieldMap as ModelFieldMap
from typing import Any

class ModelMeta(type):
    def __new__(mcs, class_name: str, bases: tuple[type, ...], namespace: dict[str, Any]): ...
    @classmethod
    def get_field_class(mcs, class_name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type[FieldInfo]: ...
