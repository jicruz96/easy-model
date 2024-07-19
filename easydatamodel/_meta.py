import inspect
from collections import OrderedDict
from functools import cached_property
from typing import Any, cast

from ._typing import UNASSIGNED
from .exceptions import InvalidModelError
from .field import FieldInfo, ModelFieldMap


class ModelMeta(type):

    def __new__(mcs, class_name: str, bases: tuple[type, ...], namespace: dict[str, Any]):
        field_class = mcs.get_field_class(class_name, bases, namespace)
        if "__fields_map__" in namespace:
            raise InvalidModelError("Cannot have a '__fields_map__' attribute in a easydatamodel Model.")
        if "__annotations__" not in namespace:
            namespace["__annotations__"] = {}
        annotations: dict[str, Any] = namespace["__annotations__"]
        fields_from_annotations: OrderedDict[str, FieldInfo] = OrderedDict(
            (name, field_class.from_annotation(name=name, type=annotation))
            for name, annotation in annotations.items()
            if not name.startswith("_")
        )
        fields_from_namespace = OrderedDict(
            (
                (name, value)
                if isinstance(value, field_class)
                else (
                    name,
                    field_class.from_namespace(name=name, default=value, type=annotations.get(name, UNASSIGNED)),
                )
            )
            for name, value in namespace.items()
            # skip private attributes
            if not (name.startswith("_") and not isinstance(value, field_class))
            # skip classmethods and functions
            and not (inspect.isfunction(value) or inspect.ismethod(value) or isinstance(value, classmethod))
            # skip properties
            and not isinstance(value, property)
            # skip functools.cached_property objects
            and not isinstance(value, cached_property)
        )
        model_fields_map = OrderedDict({**fields_from_annotations, **fields_from_namespace})
        bases_classfields_map: OrderedDict[str, FieldInfo] = OrderedDict()
        bases_fields_map: OrderedDict[str, FieldInfo] = OrderedDict()
        for base in bases:
            if isinstance(base, mcs):
                base_model_fields_map = cast(ModelFieldMap[FieldInfo], base.__fields_map__)  # type: ignore
                for name, field in base_model_fields_map.items():
                    if name not in model_fields_map:
                        if field.classfield:
                            bases_classfields_map[name] = field
                        else:
                            bases_fields_map[name] = field.copy()
                            namespace["__annotations__"][name] = field.type
        namespace.update(bases_fields_map)
        namespace.update(model_fields_map)
        namespace["__fields_map__"] = ModelFieldMap({**bases_classfields_map, **model_fields_map, **bases_fields_map})
        return super().__new__(mcs, class_name, bases, namespace)

    @classmethod
    def get_field_class(mcs, class_name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type[FieldInfo]:
        field_class: Any = None
        if "__field_class__" in namespace:
            field_class = namespace["__field_class__"]
        else:
            for base in bases:
                if hasattr(base, "__field_class__"):
                    field_class = base.__field_class__  # type: ignore
                    break
        if not field_class:
            raise InvalidModelError(f"{class_name} nor any of its bases has a __field_class__")
        if not issubclass(field_class, FieldInfo):
            raise InvalidModelError(f"{class_name}.__field_class__ must be a subclass of {FieldInfo.__name__}")
        return field_class
