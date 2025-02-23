from litestar.utils.deprecation import deprecated, warn_deprecation

from .helpers import get_enum_string_value, get_name, unique_name_for_scope, url_quote
from .path import join_paths, normalize_path
from .predicates import (
    is_annotated_type,
    is_any,
    is_async_callable,
    is_class_and_subclass,
    is_class_var,
    is_dataclass_class,
    is_dataclass_instance,
    is_generic,
    is_mapping,
    is_non_string_iterable,
    is_non_string_sequence,
    is_optional_union,
    is_undefined_sentinel,
    is_union,
)
from .scope import (
    get_serializer_from_scope,
)
from .sequence import find_index, unique
from .sync import AsyncIteratorWrapper, ensure_async_callable
from .typing import get_origin_or_inner_type, make_non_optional_union

__all__ = (
    "AsyncIteratorWrapper",
    "deprecated",
    "ensure_async_callable",
    "find_index",
    "get_enum_string_value",
    "get_name",
    "get_origin_or_inner_type",
    "get_serializer_from_scope",
    "is_annotated_type",
    "is_any",
    "is_async_callable",
    "is_class_and_subclass",
    "is_class_var",
    "is_dataclass_class",
    "is_dataclass_instance",
    "is_generic",
    "is_mapping",
    "is_non_string_iterable",
    "is_non_string_sequence",
    "is_optional_union",
    "is_undefined_sentinel",
    "is_union",
    "join_paths",
    "make_non_optional_union",
    "normalize_path",
    "unique",
    "unique_name_for_scope",
    "url_quote",
    "warn_deprecation",
)
