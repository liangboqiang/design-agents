from __future__ import annotations

import importlib
import inspect
import pkgutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

from schemas.action import ActionSpec
from schemas.tool import ToolboxDescriptor


class Toolbox(ABC):
    toolbox_name: str
    discoverable: bool = True
    tags: tuple[str, ...] = ()
    workspace_root: Path | None

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.engine = None

    def bind_engine(self, engine) -> None:  # noqa: ANN001
        self.engine = engine

    @abstractmethod
    def action_specs(self) -> Iterable[ActionSpec]:
        raise NotImplementedError

    @abstractmethod
    def spawn(self, workspace_root: Path) -> "Toolbox":
        raise NotImplementedError


class ToolboxRegistry:
    def __init__(self, package_names: tuple[str, ...] = ("tools.builtin", "tools.governance", "tools.mcp")):
        self.package_names = package_names
        self._classes: dict[str, type[Toolbox]] = {}

    def discover(self) -> dict[str, ToolboxDescriptor]:
        descriptors: dict[str, ToolboxDescriptor] = {}
        for package_name in self.package_names:
            package = importlib.import_module(package_name)
            modules = [package]
            if hasattr(package, "__path__"):
                for module_info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
                    modules.append(importlib.import_module(module_info.name))
            for module in modules:
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if not issubclass(obj, Toolbox) or obj is Toolbox:
                        continue
                    if obj.__module__ != module.__name__:
                        continue
                    toolbox_name = getattr(obj, "toolbox_name", obj.__name__.lower())
                    self._classes[toolbox_name] = obj
                    descriptors[toolbox_name] = ToolboxDescriptor(
                        toolbox_name=toolbox_name,
                        module=obj.__module__,
                        class_name=obj.__name__,
                        discoverable=bool(getattr(obj, "discoverable", True)),
                        tags=list(getattr(obj, "tags", ())),
                    )
        return descriptors

    def get_class(self, toolbox_name: str) -> type[Toolbox]:
        if not self._classes:
            self.discover()
        return self._classes[toolbox_name]

    def create(self, toolbox_name: str, workspace_root: Path, **kwargs) -> Toolbox:
        toolbox_cls = self.get_class(toolbox_name)
        instance = toolbox_cls(**kwargs)
        return instance.spawn(workspace_root)

    def create_many(self, toolbox_names: Iterable[str], workspace_root: Path) -> list[Toolbox]:
        return [self.create(name, workspace_root) for name in toolbox_names]

