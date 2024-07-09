from __future__ import annotations

import re
import typing
import warnings
from collections.abc import Callable, Mapping
from types import MappingProxyType

from ._typing import UNASSIGNED, UnassignedType, check_type, is_classvar, is_nested_generic_alias
from .exceptions import FieldTypeUnassignedError, InvalidFieldError

CLASSVAR_PATTERN = re.compile(r"(typing\.)?ClassVar(\[(?P<inner_type>.*)\])?")

if typing.TYPE_CHECKING:
    from typing import Self

    from .model import Model


def Field(
    default: typing.Any = UNASSIGNED,
    default_factory: Callable[[], typing.Any] | UnassignedType = UNASSIGNED,
    type: typing.Any = UNASSIGNED,
    init: typing.Optional[bool] = None,
    choices: typing.Optional[list[typing.Any]] = None,
    repr: bool = True,
    compare: bool = True,
    metadata: typing.Optional[Mapping[typing.Any, typing.Any]] = None,
) -> typing.Any:
    """Provide specific configuration information for an easydatamodel field.

    Attributes:
        default: default field value.
        default_factory: 0-argument function called to initialize a field's value.
        init: if True, the field will be a parameter to the class's __init__() function. If False, it is up to the
            caller to set a default or a default_factory.
        choices: If provided, allowed values for the field.
        repr: if True, the field will be included in the object's string representation.
        compare: if True, the field will be considered when comparing objects to the model (i.e. '==' and '!=')
        metadata: bespoke field metadata.

    Returns:
        A `FieldInfo` object. Return type is `Any` so it plays nicely with your type checker.

    Raises:
        InvalidFieldError:
            - if default and default_factory are both set.
            - if init is False and default or default_factory is not set.
            - if a field's type cannot be determined.
    """

    return FieldInfo(
        default=default,
        default_factory=default_factory,
        type=type,
        init=init,
        choices=choices,
        repr=repr,
        compare=compare,
        metadata=metadata,
    )


class FieldInfo:
    """Represents a field in a easydatamodel model.

    Attributes:
        default: default field value.
        default_factory: 0-argument function called to initialize a field's value.
        init: if True, the field will be a parameter to the class's __init__() function. If False, it is up to the
            caller to set a default or a default_factory.
        choices: If provided, allowed values for the field.
        repr: if True, the field will be included in the object's string representation.
        compare: if True, the field will be considered when comparing objects to the model (i.e. '==' and '!=')
        metadata: bespoke field metadata.

    Raises:
        InvalidFieldError:
            - if default and default_factory are both set.
            - if init is False and default or default_factory is not set.
            - if a field's type cannot be determined.
    """

    def __init__(
        self,
        *,
        name: str | UnassignedType[str] = UNASSIGNED,
        default: typing.Any = UNASSIGNED,
        default_factory: Callable[[], typing.Any] | UnassignedType = UNASSIGNED,
        type: typing.Any = UNASSIGNED,
        const: bool = False,
        init: typing.Optional[bool] = None,
        choices: typing.Optional[typing.Iterable[typing.Any]] = None,
        repr: bool = True,
        compare: bool = True,
        metadata: typing.Optional[Mapping[typing.Any, typing.Any]] = None,
    ) -> None:
        if default_factory is not UNASSIGNED and not callable(default_factory):
            raise InvalidFieldError("default_factory must be callable")
        if default is not UNASSIGNED and default_factory is not UNASSIGNED:
            raise InvalidFieldError("Cannot specify both default and default_factory")
        if init is False and default is UNASSIGNED and default_factory is UNASSIGNED:
            raise InvalidFieldError("Field with init=False must specify a default or default_factory")
        self.__name = name
        self.__default = default
        self.__default_factory = default_factory
        self.__const = const
        self.__repr = repr
        self.__compare = compare
        self.__metadata = metadata or {}
        self.__init = init
        self.__choices = list(choices or [])
        self.__type = type if type is not None else None.__class__
        self.__owner: type["Model[Self]"] | None = None

    def __repr__(self) -> str:
        if self.owner:
            field_name = f"{self.__class__.__name__} {self.owner.__name__}.{self.__name}"
        else:
            field_name = f"{self.__class__.__name__} {self.__name}"
        return (
            f"<{field_name} type={self.__type} default={self.default} default_factory={self.default_factory} "
            f"init={self.init} repr={self.repr} compare={self.compare} metadata={self.metadata} choices={self.choices}>"
        )

    @classmethod
    def from_annotation(cls, name: str, type: typing.Any) -> Self:
        return cls(name=name, type=type)

    @classmethod
    def from_namespace(cls, name: str, default: typing.Any, type: typing.Any) -> Self:
        return cls(name=name, default=default, type=type)

    @property
    def owner(self) -> type["Model[Self]"] | None:
        return self.__owner

    @property
    def name(self) -> str:
        if isinstance(self.__name, UnassignedType):
            raise InvalidFieldError("Field name has not been set")
        return self.__name

    @property
    def type(self) -> type:
        if isinstance(self.__type, UnassignedType):
            raise FieldTypeUnassignedError("Field type has not been set")
        return self.__type

    @property
    def default(self) -> typing.Any:
        return self.__default

    @property
    def default_factory(self) -> Callable[[], typing.Any] | UnassignedType:
        return self.__default_factory

    @property
    def const(self) -> bool:
        return self.__const

    @property
    def init(self) -> bool | None:
        return self.__init

    @property
    def repr(self) -> bool:
        return self.__repr

    @property
    def compare(self) -> bool:
        return self.__compare

    @property
    def metadata(self) -> Mapping[typing.Any, typing.Any]:
        return self.__metadata

    @property
    def choices(self) -> list[typing.Any]:
        # return a copy to prevent modification
        return self.__choices.copy()

    @property
    def classfield(self) -> bool:
        return is_classvar(self.__type) or (
            # I will grant this is a huge hack. It's the only way to make things work if
            # `from __future__ import annotations` is used.
            isinstance(self.__type, str)
            and CLASSVAR_PATTERN.match(self.__type) is not None
        )

    def __get__(self, instance: typing.Union["Model[Self]", None], owner: type["Model[Self]"]) -> typing.Any:
        if instance is None:
            if not self.classfield:
                raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {self.name!r}")
            assert self.__owner is not None, f"owner has not been set for field {self}"
            assert issubclass(owner, self.__owner), f"{self.__owner.__name__} is not a subclass of {owner.__name__}"
            assert self.default is not UNASSIGNED, f"no default set for {self}"
            return self.default
        if self.classfield:
            return self.default
        return instance.__dict__[self.name]

    def __set__(self, instance: "Model[Self]", value: typing.Any) -> None:
        if self.const and self.name in instance.__dict__:
            raise ValueError(f"Cannot set const field {self.name!r}")
        if self.choices and value not in self.choices:
            raise ValueError(f"Value must be one of {', '.join(map(repr,self.choices))} but value was {value}")
        if isinstance(self.type, str):
            type_ = typing.get_type_hints(self.__owner)[self.name]
        else:
            type_ = self.type
        check_type(value, type_)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner: type["Model[Self]"], name: str) -> None:
        if self.__owner:
            raise InvalidFieldError(f"Field {name!r} on {owner.__name__} has already been set to {self.__owner}")

        if self.__name is not UNASSIGNED and self.__name != name:
            raise InvalidFieldError(f"Field '{name}' has conflicting names: {self.__name} != {name}")

        annotation = owner.__annotations__.get(name, UNASSIGNED)
        if self.__type is UNASSIGNED:
            if annotation is UNASSIGNED:
                field_repr = name if self.default is UNASSIGNED else f"{name} = {self.default}"
                raise InvalidFieldError(
                    f"Non-annotated attribute: `{field_repr}`. All model fields need a type annotation. If `{name}` "
                    f"is not meant to be a field, you can resolve this error by annotating it as a `ClassVar` or "
                    f"renaming it to a private attribute (e.g. `_{name}`)."
                )
            self.__type = annotation
        elif annotation is not UNASSIGNED and self.__type != annotation:
            raise InvalidFieldError(f"Field '{name}' has conflicting type annotations: {self.__type} != {annotation}")

        self.__name = name
        self.__owner = owner

        if self.classfield:
            self._validate_and_set_classvar_field()
        else:
            self._validate_field()

    def copy(self) -> FieldInfo:
        """Return a copy of the field without its owner and name values set so it can be used in another class."""
        return self.__class__(
            type=self.__type,
            default=self.default,
            default_factory=self.default_factory,
            const=self.const,
            init=self.init,
            repr=self.repr,
            compare=self.compare,
            metadata=self.metadata,
            choices=self.choices,
        )

    def _validate_and_set_classvar_field(self):
        if self.__init is True:
            raise InvalidFieldError(f"Field '{self.name}' cannot be init and a class field.")
        self.__init = False  # explicitly set to False
        self._validate_field()
        if not isinstance(self.default_factory, UnassignedType):
            self.__default = self.default_factory()
        inner_type: typing.Any = _get_inner_type_from_classvar(self.__type)
        if inner_type is None:
            return

        if isinstance(inner_type, str):
            warnings.warn(
                "Class variables can't be checked during runtime if using string representations of types or if "
                "using 'from __future__ import annotations' to resolve forward references.",
                RuntimeWarning,
            )
        else:
            check_type(self.__default, type_=inner_type)

    def _validate_field(self):
        if self.default_factory is not UNASSIGNED and self.default is not UNASSIGNED:
            raise InvalidFieldError(f"Field '{self.name}' can't have both a 'default' and 'default_factory'")

        if self.init is False and self.default is UNASSIGNED and self.default_factory is UNASSIGNED:
            raise InvalidFieldError(f"Field '{self.name}' must have a 'default' or 'default_factory'")


def _get_inner_type_from_classvar(type_: typing.Any) -> typing.Any:
    if isinstance(type_, str):
        if match := CLASSVAR_PATTERN.match(type_):
            return match.group("inner_type")
        return None
    if is_nested_generic_alias(type_):
        return type_.__args__[0]
    return None


FieldType = typing.TypeVar("FieldType", bound=FieldInfo)
ModelFieldMap = MappingProxyType[str, FieldType]
