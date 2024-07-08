import inspect
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from ._typing import UNASSIGNED
from .exceptions import InvalidModelError
from .field import FieldInfo

if TYPE_CHECKING:
    from .model import Model


ModelFieldMap = MappingProxyType[str, FieldInfo]


class ModelMeta(type):
    __fields_map__: ModelFieldMap
    __fields_class__: type[FieldInfo] = FieldInfo

    def __new__(mcs, class_name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type["Model"]:
        if "__fields_map__" in namespace:
            raise InvalidModelError("Cannot have a '__fields_map__' attribute in a easydatamodel Model.")
        if "__annotations__" not in namespace:
            namespace["__annotations__"] = {}
        annotations: dict[str, Any] = namespace["__annotations__"]
        fields_from_annotations: dict[str, FieldInfo] = {
            name: mcs.__fields_class__(name=name, type=annotation)
            for name, annotation in annotations.items()
            if not name.startswith("_")
        }
        fields_from_namespace = {
            name: (
                value
                if isinstance(value, mcs.__fields_class__)
                else mcs.__fields_class__(name=name, default=value, type=annotations.get(name, UNASSIGNED))
            )
            for name, value in namespace.items()
            # skip private attributes
            if not (name.startswith("_") and not isinstance(value, mcs.__fields_class__))
            # skip classmethods and functions
            and not (inspect.isfunction(value) or inspect.ismethod(value) or isinstance(value, classmethod))
            # skip properties
            and not isinstance(value, property)
        }
        model_fields_map = {**fields_from_annotations, **fields_from_namespace}
        bases_classfields_map: dict[str, FieldInfo] = {}
        bases_fields_map: dict[str, FieldInfo] = {}
        for base in bases:
            if isinstance(base, mcs):
                for name, field in base.__fields_map__.items():
                    if name not in model_fields_map:
                        if field.classfield:
                            bases_classfields_map[name] = field.copy()
                        else:
                            bases_fields_map[name] = field.copy()
                            namespace["__annotations__"][name] = field.type
        namespace.update(model_fields_map)
        namespace.update(bases_fields_map)
        namespace["__fields_map__"] = ModelFieldMap({**model_fields_map, **bases_fields_map, **bases_classfields_map})
        return super().__new__(mcs, class_name, bases, namespace)
