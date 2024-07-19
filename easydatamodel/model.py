from __future__ import annotations

import json
from typing import Any, Generic

from ._meta import ModelMeta
from ._typing import UNASSIGNED, UnassignedType
from .exceptions import InvalidModelError
from .field import FieldInfo, FieldType, ModelFieldMap


class _GenericModel(Generic[FieldType], metaclass=ModelMeta):
    """Base class for easydatamodel models.

    ### Usage

    ```python
    from easydatamodel import Model

    class Person(Model):
        name: str
        age: int

    person = Person(name="Alice", age=30)
    print(person.dict()) # {'name': 'Alice', 'age': 30}
    person.age = "timeless"  # Raises TypeError
    ```

    You can also use Field instances to configure fields further:

    ```python

    class Wizard(Model):
        name: str
        house: str = Field(choices=["Gryffindor", "Hufflepuff", "Ravenclaw", "Slytherin"])
    ```
    """

    __field_class__: type[FieldType] = FieldInfo  # type: ignore
    __fields_map__: ModelFieldMap[FieldType]

    def __init__(self, **kwargs: Any):
        self.__init_kwargs__(kwargs)
        self.__init_defaults__(exclude=set(kwargs))
        self.__post_init__()

    def __post_init__(self) -> None:
        pass

    def __init_kwargs__(self, init_kwargs: dict[str, Any]) -> None:
        errors = {}
        for kw, value in init_kwargs.items():
            field = self.__fields_map__.get(kw)
            try:
                assert field is not None, f"{kw} is not a field in {self.__class__.__name__}."
                assert field.classfield is False, f"'{field.name}' is a class variable. It can't be overwritten."
                assert field.init is not False, f"'{field.name}' field has init=False"
                setattr(self, field.name, value)
            except (AssertionError, TypeError) as e:
                errors[kw] = str(e)

        if errors:
            raise InvalidModelError("\n" + json.dumps(errors, indent=4))

    def __init_defaults__(self, exclude: set[str] | None = None) -> None:
        exclude = exclude or set()
        fields = {f for f in self.__fields_map__.values() if f.name not in exclude and not f.classfield}
        fields_with_default_factories = {f for f in fields if f.default_factory is not UNASSIGNED}
        fields_with_defaults = {f for f in fields if f.default is not UNASSIGNED}
        missing_fields = fields - fields_with_default_factories - fields_with_defaults
        if missing_fields:
            raise InvalidModelError(f"Missing fields: {', '.join(map(lambda f: repr(f.name), missing_fields))}")
        for field in fields_with_defaults:
            setattr(self, field.name, field.default)

        for field in fields_with_default_factories:
            assert not isinstance(field.default_factory, UnassignedType)
            setattr(self, field.name, field.default_factory())

    def dict(self, *, include: list[str] | None = None, exclude: list[str] | None = None) -> dict[str, Any]:
        include = include or []
        exclude = exclude or []
        for name in include:
            if not hasattr(self, name):
                raise ValueError(f"Attribute {name!r} in include list not found in {self.__class__.__name__}.")
        fields = {
            field_name: getattr(self, field_name)
            for field_name in self.__fields_map__.keys()
            if field_name not in exclude
        }
        extras = {name: getattr(self, name) for name in include if name not in exclude}
        return {**fields, **extras}

    def __repr__(self) -> str:
        exclude = [field.name for field in self.__fields_map__.values() if field.repr is False]
        return f"{self.__class__.__name__}({', '.join(f'{k}={v!r}' for k, v in self.dict(exclude=exclude).items())})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        exclude = [field.name for field in self.__fields_map__.values() if field.compare is False]
        return self.dict(exclude=exclude) == other.dict(exclude=exclude)


class Model(_GenericModel[FieldInfo]):
    __field_class__ = FieldInfo
