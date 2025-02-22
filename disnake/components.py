"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Disnake Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from .enums import ButtonStyle, ComponentType, TextInputStyle, try_enum
from .partial_emoji import PartialEmoji, _EmojiTag
from .utils import MISSING, get_slots

if TYPE_CHECKING:
    from .emoji import Emoji
    from .types.components import (
        ActionRow as ActionRowPayload,
        ButtonComponent as ButtonComponentPayload,
        Component as ComponentPayload,
        SelectMenu as SelectMenuPayload,
        SelectOption as SelectOptionPayload,
        TextInput as TextInputPayload,
    )

__all__ = (
    "Component",
    "ActionRow",
    "Button",
    "SelectMenu",
    "SelectOption",
    "TextInput",
)

C = TypeVar("C", bound="Component")

MessageComponent = Union["Button", "SelectMenu"]

if TYPE_CHECKING:  # TODO: remove when we add modal select support
    from typing_extensions import TypeAlias

# ModalComponent = Union["TextInput", "SelectMenu"]
ModalComponent: TypeAlias = "TextInput"
NestedComponent = Union[MessageComponent, ModalComponent]
ComponentT = TypeVar("ComponentT", bound=NestedComponent)


class Component:
    """Represents a Discord Bot UI Kit Component.

    Currently, the only components supported by Discord are:

    - :class:`ActionRow`
    - :class:`Button`
    - :class:`SelectMenu`
    - :class:`TextInput`

    This class is abstract and cannot be instantiated.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    """

    __slots__: Tuple[str, ...] = ("type",)

    __repr_info__: ClassVar[Tuple[str, ...]]
    type: ComponentType

    def __repr__(self) -> str:
        attrs = " ".join(f"{key}={getattr(self, key)!r}" for key in self.__repr_info__)
        return f"<{self.__class__.__name__} {attrs}>"

    @classmethod
    def _raw_construct(cls: Type[C], **kwargs) -> C:
        self: C = cls.__new__(cls)
        for slot in get_slots(cls):
            try:
                value = kwargs[slot]
            except KeyError:
                pass
            else:
                setattr(self, slot, value)
        return self

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError


class ActionRow(Component, Generic[ComponentT]):
    """Represents an action row.

    This is a component that holds up to 5 children components in a row.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    children: List[Union[:class:`Button`, :class:`SelectMenu`, :class:`TextInput`]]
        The children components that this holds, if any.
    """

    __slots__: Tuple[str, ...] = ("children",)

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ActionRowPayload):
        self.type: ComponentType = try_enum(ComponentType, data["type"])
        self.children: List[ComponentT] = [
            _component_factory(d) for d in data.get("components", [])
        ]

    def to_dict(self) -> ActionRowPayload:
        return {
            "type": int(self.type),
            "components": [child.to_dict() for child in self.children],
        }  # type: ignore


class Button(Component):
    """Represents a button from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a button is :class:`disnake.ui.Button`
        not this one.

    .. versionadded:: 2.0

    Attributes
    ----------
    style: :class:`.ButtonStyle`
        The style of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        If this button is for a URL, it does not have a custom ID.
    url: Optional[:class:`str`]
        The URL this button sends you to.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    label: Optional[:class:`str`]
        The label of the button, if any.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji of the button, if available.
    """

    __slots__: Tuple[str, ...] = (
        "style",
        "custom_id",
        "url",
        "disabled",
        "label",
        "emoji",
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ButtonComponentPayload):
        self.type: ComponentType = try_enum(ComponentType, data["type"])
        self.style: ButtonStyle = try_enum(ButtonStyle, data["style"])
        self.custom_id: Optional[str] = data.get("custom_id")
        self.url: Optional[str] = data.get("url")
        self.disabled: bool = data.get("disabled", False)
        self.label: Optional[str] = data.get("label")
        self.emoji: Optional[PartialEmoji]
        try:
            self.emoji = PartialEmoji.from_dict(data["emoji"])
        except KeyError:
            self.emoji = None

    def to_dict(self) -> ButtonComponentPayload:
        payload = {
            "type": 2,
            "style": int(self.style),
            "label": self.label,
            "disabled": self.disabled,
        }
        if self.custom_id:
            payload["custom_id"] = self.custom_id

        if self.url:
            payload["url"] = self.url

        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()

        return payload  # type: ignore


class SelectMenu(Component):
    """Represents a select menu from the Discord Bot UI Kit.

    A select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`disnake.ui.Select` not this one.

    .. versionadded:: 2.0

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    options: List[:class:`SelectOption`]
        A list of options that can be selected in this select menu.
    disabled: :class:`bool`
        Whether the select menu is disabled or not.
    """

    __slots__: Tuple[str, ...] = (
        "custom_id",
        "placeholder",
        "min_values",
        "max_values",
        "options",
        "disabled",
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: SelectMenuPayload):
        self.type = ComponentType.select
        self.custom_id: str = data["custom_id"]
        self.placeholder: Optional[str] = data.get("placeholder")
        self.min_values: int = data.get("min_values", 1)
        self.max_values: int = data.get("max_values", 1)
        self.options: List[SelectOption] = [
            SelectOption.from_dict(option) for option in data.get("options", [])
        ]
        self.disabled: bool = data.get("disabled", False)

    def to_dict(self) -> SelectMenuPayload:
        payload: SelectMenuPayload = {
            "type": self.type.value,
            "custom_id": self.custom_id,
            "min_values": self.min_values,
            "max_values": self.max_values,
            "options": [op.to_dict() for op in self.options],
            "disabled": self.disabled,
        }

        if self.placeholder:
            payload["placeholder"] = self.placeholder

        return payload


class SelectOption:
    """Represents a select menu's option.

    These can be created by users.

    .. versionadded:: 2.0

    Attributes
    ----------
    label: :class:`str`
        The label of the option. This is displayed to users.
        Can only be up to 100 characters.
    value: :class:`str`
        The value of the option. This is not displayed to users.
        If not provided when constructed then it defaults to the
        label. Can only be up to 100 characters.
    description: Optional[:class:`str`]
        An additional description of the option, if any.
        Can only be up to 100 characters.
    emoji: Optional[Union[:class:`str`, :class:`Emoji`, :class:`PartialEmoji`]]
        The emoji of the option, if available.
    default: :class:`bool`
        Whether this option is selected by default.
    """

    __slots__: Tuple[str, ...] = (
        "label",
        "value",
        "description",
        "emoji",
        "default",
    )

    def __init__(
        self,
        *,
        label: str,
        value: str = MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        default: bool = False,
    ) -> None:
        self.label = label
        self.value = label if value is MISSING else value
        self.description = description

        if emoji is not None:
            if isinstance(emoji, str):
                emoji = PartialEmoji.from_str(emoji)
            elif isinstance(emoji, _EmojiTag):
                emoji = emoji._to_partial()
            else:
                raise TypeError(
                    f"expected emoji to be str, Emoji, or PartialEmoji not {emoji.__class__}"
                )

        self.emoji = emoji
        self.default = default

    def __repr__(self) -> str:
        return (
            f"<SelectOption label={self.label!r} value={self.value!r} description={self.description!r} "
            f"emoji={self.emoji!r} default={self.default!r}>"
        )

    def __str__(self) -> str:
        if self.emoji:
            base = f"{self.emoji} {self.label}"
        else:
            base = self.label

        if self.description:
            return f"{base}\n{self.description}"
        return base

    @classmethod
    def from_dict(cls, data: SelectOptionPayload) -> SelectOption:
        try:
            emoji = PartialEmoji.from_dict(data["emoji"])
        except KeyError:
            emoji = None

        return cls(
            label=data["label"],
            value=data["value"],
            description=data.get("description"),
            emoji=emoji,
            default=data.get("default", False),
        )

    def to_dict(self) -> SelectOptionPayload:
        payload: SelectOptionPayload = {
            "label": self.label,
            "value": self.value,
            "default": self.default,
        }

        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()  # type: ignore

        if self.description:
            payload["description"] = self.description

        return payload


class TextInput(Component):
    """Represents a text input from the Discord Bot UI Kit.

    .. versionadded:: 2.4

    .. note::

        The user constructible and usable type to create a text input is
        :class:`disnake.ui.TextInput`, not this one.

    Attributes
    ----------
    style: :class:`TextInputStyle`
        The style of the text input.
    label: Optional[:class:`str`]
        The label of the text input.
    custom_id: :class:`str`
        The ID of the text input that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is entered.
    value: Optional[:class:`str`]
        The pre-filled text of the text input.
    required: :class:`bool`
        Whether the text input is required. Defaults to ``True``.
    min_length: Optional[:class:`int`]
        The minimum length of the text input.
    max_length: Optional[:class:`int`]
        The maximum length of the text input.
    """

    __slots__: Tuple[str, ...] = (
        "style",
        "custom_id",
        "label",
        "placeholder",
        "value",
        "required",
        "max_length",
        "min_length",
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: TextInputPayload) -> None:
        style = data.get("style", TextInputStyle.short.value)

        self.type: ComponentType = try_enum(ComponentType, data["type"])
        self.custom_id: str = data["custom_id"]
        self.style: TextInputStyle = try_enum(TextInputStyle, style)
        self.label: Optional[str] = data.get("label")
        self.placeholder: Optional[str] = data.get("placeholder")
        self.value: Optional[str] = data.get("value")
        self.required: bool = data.get("required", True)
        self.min_length: Optional[int] = data.get("min_length")
        self.max_length: Optional[int] = data.get("max_length")

    def to_dict(self) -> TextInputPayload:
        payload: TextInputPayload = {
            "type": self.type.value,
            "style": self.style.value,
            "label": cast(str, self.label),
            "custom_id": self.custom_id,
            "required": self.required,
        }

        if self.placeholder is not None:
            payload["placeholder"] = self.placeholder

        if self.value is not None:
            payload["value"] = self.value

        if self.min_length is not None:
            payload["min_length"] = self.min_length

        if self.max_length is not None:
            payload["max_length"] = self.max_length

        return payload


def _component_factory(data: ComponentPayload, *, type: Type[C] = Component) -> C:
    # NOTE: due to speed, this method does not use the ComponentType enum
    #       as this runs every single time a component is received from the api
    # NOTE: The type param is purely for type-checking, it has no implications on runtime behavior.
    component_type = data["type"]
    if component_type == 1:
        return ActionRow(data)  # type: ignore
    elif component_type == 2:
        return Button(data)  # type: ignore
    elif component_type == 3:
        return SelectMenu(data)  # type: ignore
    elif component_type == 4:
        return TextInput(data)  # type: ignore
    else:
        as_enum = try_enum(ComponentType, component_type)
        return Component._raw_construct(type=as_enum)  # type: ignore
