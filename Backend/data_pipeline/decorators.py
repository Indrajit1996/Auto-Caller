# data_pipeline/decorators.py
import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast, overload

# Type variable for function
F = TypeVar("F", bound=Callable[..., Any])

# Registries to hold decorated functions
importers_registry: dict[str, Callable] = {}
seeders_registry: dict[str, Callable] = {}
scripts_registry: dict[str, Callable] = {}

# Constants for parameter names to avoid string repetition
PARAM_FILE_PATH = "file_path"
PARAM_TRUNCATE = "truncate"
PARAM_COUNT = "count"
PARAM_SRC = "src"
PARAM_OUTPUT = "output"
PARAM_SKIP_EMPTY_ROWS = "skip_empty_rows"
PARAM_UNIQUE_FIELDS = "unique_fields"


def _check_parameter_exists(func: Callable, param_name: str) -> None:
    """
    Helper function to verify a parameter exists in a function signature.

    Args:
        func: The function to check
        param_name: The parameter name to verify

    Raises:
        ValueError: If the parameter doesn't exist in the function signature
    """
    sig = inspect.signature(func)
    if param_name not in sig.parameters:
        raise ValueError(
            f"Function '{func.__name__}' must have a '{param_name}' parameter"
        )


def _check_parameter_type(
    func: Callable,
    param_name: str,
    expected_type: type | list[type],
    optional: bool = False,
) -> None:
    """
    Helper function to verify a parameter's type annotation.

    Args:
        func: The function to check
        param_name: The parameter name to verify
        expected_type: The expected type(s) for the parameter
        optional: Whether the parameter is optional (can be None)

    Raises:
        ValueError: If the parameter doesn't have the expected type
    """
    sig = inspect.signature(func)
    param = sig.parameters.get(param_name)

    if param is None:
        return

    # Parameter.empty is always allowed (no type annotation)
    if param.annotation is inspect.Parameter.empty:
        return

    # Special handling for list or None case
    if expected_type == [list] and optional:
        if param.annotation not in (list, type(None), list | None):
            raise ValueError(
                f"Parameter '{param_name}' in '{func.__name__}' must be of type list or None. Don't use list[type] in the decorator."
            )
        return

    # Convert single type to list for uniform handling
    expected_types = (
        [expected_type] if not isinstance(expected_type, list) else expected_type
    )

    # For optional parameters, None/type(None) is allowed
    valid_types = list(expected_types)
    if optional:
        valid_types.append(type(None))

    # Check if the annotation matches any valid type
    if param.annotation not in valid_types:
        type_names = " or ".join(str(t.__name__) for t in expected_types)
        if optional:
            type_names += " or None"
        raise ValueError(
            f"Parameter '{param_name}' in '{func.__name__}' must be of type {type_names}"
        )


def _validate_decorator_params(
    func: F,
    required_params: dict[str, type | list[type]],
    optional_params: dict[str, type | list[type]] | None = None,
) -> None:
    """
    Centralized validation function for decorator parameters.

    Args:
        func: The function being decorated
        required_params: Dictionary mapping required parameter names to their expected types
        optional_params: Dictionary mapping optional parameter names to their expected types

    Raises:
        ValueError: If any parameter validation fails
    """
    # Check required parameters
    for param_name, expected_type in required_params.items():
        _check_parameter_exists(func, param_name)
        _check_parameter_type(func, param_name, expected_type)

    # Check optional parameters if provided
    if optional_params:
        for param_name, expected_type in optional_params.items():
            _check_parameter_type(func, param_name, expected_type, optional=True)


@overload
def importer(func: F) -> F:
    ...


@overload
def importer(func: None = None, *, name: str | None = None) -> Callable[[F], F]:
    ...


def importer(func: F | None = None, *, name: str | None = None) -> F | Callable[[F], F]:
    """
    Decorator to register an importer function.
    Enforces that the function has a 'file_path' parameter of type str
    and a 'truncate' parameter of type bool.

    Args:
        func: The function to decorate
        name: Optional custom name for the registry (defaults to function name)

    Returns:
        Decorated function or a decorator function

    Raises:
        ValueError: If the decorated function doesn't meet the parameter requirements
    """

    def decorator(func: F) -> F:
        # Validate required and optional parameters
        _validate_decorator_params(
            func,
            required_params={
                PARAM_FILE_PATH: str,
                PARAM_TRUNCATE: bool,
            },
            optional_params={
                PARAM_SKIP_EMPTY_ROWS: bool,
                PARAM_UNIQUE_FIELDS: [list],
            },
        )

        # Register the function with custom name or function name
        registry_name = name if name is not None else func.__name__
        importers_registry[registry_name] = func

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return cast(F, wrapper)

    # Handle both @importer and @importer(name="custom_name") syntax
    if func is None:
        return decorator
    return decorator(func)


@overload
def seeder(func: F) -> F:
    ...


@overload
def seeder(func: None = None, *, name: str | None = None) -> Callable[[F], F]:
    ...


def seeder(func: F | None = None, *, name: str | None = None) -> F | Callable[[F], F]:
    """
    Decorator to register a seeder function.
    Enforces that the function has a 'count' parameter of type int.

    Args:
        func: The function to decorate
        name: Optional custom name for the registry (defaults to function name)

    Returns:
        Decorated function or a decorator function

    Raises:
        ValueError: If the decorated function doesn't meet the parameter requirements
    """

    def decorator(func: F) -> F:
        # Validate required parameters
        _validate_decorator_params(func, required_params={PARAM_COUNT: int})

        # Register the function with custom name or function name
        registry_name = name if name is not None else func.__name__
        seeders_registry[registry_name] = func

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return cast(F, wrapper)

    # Handle both @seeder and @seeder(name="custom_name") syntax
    if func is None:
        return decorator
    return decorator(func)


@overload
def script(func: F) -> F:
    ...


@overload
def script(func: None = None, *, name: str | None = None) -> Callable[[F], F]:
    ...


def script(func: F | None = None, *, name: str | None = None) -> F | Callable[[F], F]:
    """
    Decorator to register a processing script function.
    Enforces that the function has 'src' and 'output' parameters of type str.

    Args:
        func: The function to decorate
        name: Optional custom name for the registry (defaults to function name)

    Returns:
        Decorated function or a decorator function

    Raises:
        ValueError: If the decorated function doesn't meet the parameter requirements
    """

    def decorator(func: F) -> F:
        # Validate required parameters
        _validate_decorator_params(
            func,
            required_params={
                PARAM_SRC: str,
                PARAM_OUTPUT: str,
            },
        )

        registry_name = name if name is not None else func.__name__
        scripts_registry[registry_name] = func

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return cast(F, wrapper)

    # Handle both @script and @script(name="custom_name") syntax
    if func is None:
        return decorator
    return decorator(func)
