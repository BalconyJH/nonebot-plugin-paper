from functools import wraps
from importlib import metadata
import sys
from types import ModuleType
from typing import Any, Callable, ClassVar, Optional, TypedDict, TypeVar

from nonebot.log import logger
from packaging import version

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class DependencyInfo(TypedDict):
    """Information about a dependency.

    Attributes:
        min_version: The minimum required version of the dependency.
        required: Whether the dependency is required.
        available: Whether the dependency is available in the environment.
        loaded: Whether the dependency module has been loaded.
    """

    min_version: Optional[str]
    required: bool
    available: bool
    loaded: bool


ComponentDeps = dict[str, set[str]]
ModuleCache = dict[str, ModuleType]
T = TypeVar("T")


class DependencyManager:
    """A singleton class to manage optional dependencies.

    Provides functionality to register, check and load optional dependencies
    for different components of the application.

    Attributes:
        _instance: The singleton instance of dependency manager.
        _initialized: Whether the instance has been initialized.
        _dependencies: Dict storing dependency configurations.
        _modules: Dict storing loaded module instances.
        _component_deps: Dict mapping components to their dependencies.
    """

    _instance: ClassVar[Optional[Self]] = None
    _initialized: bool = False

    def __new__(cls) -> Self:
        """Creates a singleton instance.

        Returns:
            Self: The singleton instance of DependencyManager.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initializes the dependency manager if not already initialized."""
        if self._initialized:
            return

        self._dependencies: dict[str, DependencyInfo] = {}
        self._modules: ModuleCache = {}
        self._component_deps: ComponentDeps = {}
        self._initialized = True

    def register_dependency(
        self,
        name: str,
        min_version: Optional[str] = None,
        component: Optional[str] = None,
        *,
        required: bool = True,
    ) -> None:
        """Registers a new dependency.

        Args:
            name: Name of the dependency.
            min_version: Minimum version requirement.
            required: Whether the dependency is required.
            component: Name of component this dependency belongs to.

        Example:
            >>> dependency_manager = DependencyManager()
            >>> dependency_manager.register_dependency(
            ...     "numpy",
            ...     min_version="1.20.0",
            ...     component="math"
            ... )
        """
        if name in self._dependencies:
            dep = self._dependencies[name]
            if min_version:
                dep["min_version"] = min_version
            dep["required"] |= required
        else:
            self._dependencies[name] = {
                "min_version": min_version,
                "required": required,
                "available": False,
                "loaded": False,
            }

        if component:
            self._component_deps.setdefault(component, set()).add(name)

    def check_dependency(self, name: str) -> bool:
        """Checks if a dependency is available.

        Args:
            name: Name of dependency to check.

        Returns:
            bool: True if dependency is available, False otherwise.

        Raises:
            ValueError: If dependency name is unknown.
        """
        logger.debug(f"Checking dependency: {name}")
        if name not in self._dependencies:
            raise ValueError(
                f"Dependency '{name}' not registered. Call register_dependency() first."
            )

        dep = self._dependencies[name]
        if dep["available"]:
            return True

        try:
            pkg_version = metadata.version(name)
        except metadata.PackageNotFoundError:
            return False

        if dep["min_version"] and version.parse(pkg_version) < version.parse(
            dep["min_version"]
        ):
            return False

        dep["available"] = True
        return True

    def load_dependency(self, name: str) -> Optional[ModuleType]:
        """Loads a dependency module.

        Args:
            name: Name of dependency to load.

        Returns:
            Optional[ModuleType]: Loaded module or None if not available.

        Raises:
            ValueError: If dependency name is unknown.
            ImportError: If required dependency cannot be loaded.
        """
        if name not in self._dependencies:
            raise ValueError(f"Unknown dependency: {name}")

        if name in self._modules:
            return self._modules[name]

        dep = self._dependencies[name]
        if not self.check_dependency(name):
            if dep["required"]:
                raise ImportError(f"Required dependency {name} is not available")
            return None

        try:
            module = __import__(name, fromlist=["*"])
        except ImportError as e:
            logger.debug(f"Failed to load {name}: {e}")
            if dep["required"]:
                raise
            return None

        self._modules[name] = module
        dep["loaded"] = True
        return module

    def get_module(self, name: str) -> Optional[ModuleType]:
        """Gets a loaded module by name.

        Args:
            name: Name of module to get.

        Returns:
            Optional[ModuleType]: Requested module or None if not available.
        """
        if name not in self._modules:
            return self.load_dependency(name)
        return self._modules[name]

    def check_component(self, component: str) -> bool:
        """Checks if all dependencies of a component are available.

        Args:
            component: Name of component to check.

        Returns:
            bool: True if all dependencies are available, False otherwise.
        """
        if component not in self._component_deps:
            return False

        deps = self._component_deps[component]
        return all(self.check_dependency(dep) for dep in deps)

    def load_component(self, component: str) -> dict[str, Optional[ModuleType]]:
        """Loads all dependencies of a component.

        Args:
            component: Name of component to load dependencies for.

        Returns:
            dict[str, Optional[ModuleType]]: Dict of loaded modules.

        Raises:
            ValueError: If component name is unknown.
        """
        if component not in self._component_deps:
            raise ValueError(f"Unknown component: {component}")

        return {
            name: self.load_dependency(name) for name in self._component_deps[component]
        }

    def requires(
        self, *dependencies: str, component: Optional[str] = None
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator to mark function dependencies.

        Args:
            *dependencies: Names of required dependencies.
            component: Optional component name.

        Returns:
            Callable: Decorator function that checks dependencies before execution.

        Example:
            >>> @dependency_manager.requires("numpy", "pandas", component="data")
            ... def process_data(df):
            ...     pass
        """
        if component:
            for dep in dependencies:
                if dep not in self._dependencies:
                    self.register_dependency(dep, component=component)
                elif component not in self._component_deps:
                    self._component_deps[component] = {dep}
                else:
                    self._component_deps[component].add(dep)

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                missing = [
                    dep for dep in dependencies if not self.check_dependency(dep)
                ]
                if missing:
                    raise RuntimeError(
                        f"Missing required dependencies for {func.__name__}: {', '.join(missing)}"
                    )
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def clear(self) -> None:
        """Clears all dependency states and caches."""
        self._dependencies.clear()
        self._modules.clear()
        self._component_deps.clear()

    @staticmethod
    def get_version(name: str) -> Optional[str]:
        """Gets installed version of a package.

        Args:
            name: Name of package.

        Returns:
            Optional[str]: Package version or None if not found.
        """
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return None


dependency_manager = DependencyManager()
