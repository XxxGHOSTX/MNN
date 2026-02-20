"""
Control Plane - lifecycle coordination for MNN subsystems.

Manages the start / stop / health lifecycle of every subsystem registered
with the Control Plane.  Lifecycle transitions are deterministic and
idempotent: starting an already-running subsystem is a no-op, stopping a
stopped subsystem is a no-op.

Author: MNN Engine Contributors
"""

from enum import Enum, auto
from typing import Callable, Dict, List, Optional


class LifecycleState(Enum):
    """Possible lifecycle states for a managed subsystem."""

    UNREGISTERED = auto()
    REGISTERED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()


class SubsystemInfo:
    """
    Metadata and lifecycle state for a single subsystem.

    Attributes:
        name:       Unique identifier for the subsystem.
        state:      Current lifecycle state.
        start_fn:   Callable invoked when the subsystem starts.
        stop_fn:    Callable invoked when the subsystem stops.
        health_fn:  Optional callable returning True when subsystem is healthy.
        error:      Last error message if state is FAILED, else None.
    """

    def __init__(
        self,
        name: str,
        start_fn: Callable[[], None],
        stop_fn: Callable[[], None],
        health_fn: Optional[Callable[[], bool]] = None,
    ) -> None:
        self.name = name
        self.state: LifecycleState = LifecycleState.REGISTERED
        self.start_fn = start_fn
        self.stop_fn = stop_fn
        self.health_fn = health_fn
        self.error: Optional[str] = None

    def is_healthy(self) -> bool:
        """Return health status; defaults to True when no health_fn is provided."""
        if self.state != LifecycleState.RUNNING:
            return False
        if self.health_fn is not None:
            try:
                return bool(self.health_fn())
            except Exception:
                return False
        return True

    def __repr__(self) -> str:
        return f"SubsystemInfo(name={self.name!r}, state={self.state.name})"


class ControlPlane:
    """
    Central lifecycle coordinator for all MNN subsystems.

    Subsystems are registered with optional start/stop/health callbacks
    and can be started, stopped, or queried individually or in bulk.

    The Control Plane maintains a deterministic registration order so that
    ``start_all()`` and ``stop_all()`` (which stops in reverse order)
    are fully predictable.

    Attributes:
        _subsystems: Ordered mapping from name to SubsystemInfo.

    Examples:
        >>> cp = ControlPlane()
        >>> cp.register("kernel", lambda: None, lambda: None)
        >>> cp.start("kernel")
        >>> cp.status("kernel") == LifecycleState.RUNNING
        True
        >>> cp.stop("kernel")
        >>> cp.status("kernel") == LifecycleState.STOPPED
        True
    """

    def __init__(self) -> None:
        self._subsystems: Dict[str, SubsystemInfo] = {}
        self._order: List[str] = []  # registration order

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        start_fn: Callable[[], None],
        stop_fn: Callable[[], None],
        health_fn: Optional[Callable[[], bool]] = None,
    ) -> None:
        """
        Register a subsystem with the Control Plane.

        Args:
            name:      Unique subsystem name.
            start_fn:  Called when the subsystem is started.
            stop_fn:   Called when the subsystem is stopped.
            health_fn: Optional callable returning True when healthy.

        Raises:
            ValueError: If a subsystem with ``name`` is already registered.
        """
        if name in self._subsystems:
            raise ValueError(f"Subsystem '{name}' is already registered.")
        info = SubsystemInfo(name, start_fn, stop_fn, health_fn)
        self._subsystems[name] = info
        self._order.append(name)

    # ------------------------------------------------------------------
    # Lifecycle operations
    # ------------------------------------------------------------------

    def start(self, name: str) -> None:
        """
        Start a registered subsystem.

        Idempotent: starting a RUNNING subsystem is a no-op.

        Args:
            name: Subsystem name.

        Raises:
            KeyError: If subsystem is not registered.
            RuntimeError: If the start callback raises.
        """
        info = self._get(name)
        if info.state == LifecycleState.RUNNING:
            return
        info.state = LifecycleState.STARTING
        try:
            info.start_fn()
            info.state = LifecycleState.RUNNING
            info.error = None
        except Exception as exc:
            info.state = LifecycleState.FAILED
            info.error = str(exc)
            raise RuntimeError(f"Subsystem '{name}' failed to start: {exc}") from exc

    def stop(self, name: str) -> None:
        """
        Stop a running subsystem.

        Idempotent: stopping a STOPPED subsystem is a no-op.

        Args:
            name: Subsystem name.

        Raises:
            KeyError: If subsystem is not registered.
            RuntimeError: If the stop callback raises.
        """
        info = self._get(name)
        if info.state in (LifecycleState.STOPPED, LifecycleState.REGISTERED):
            return
        info.state = LifecycleState.STOPPING
        try:
            info.stop_fn()
            info.state = LifecycleState.STOPPED
            info.error = None
        except Exception as exc:
            info.state = LifecycleState.FAILED
            info.error = str(exc)
            raise RuntimeError(f"Subsystem '{name}' failed to stop: {exc}") from exc

    def start_all(self) -> None:
        """Start all registered subsystems in registration order."""
        for name in self._order:
            self.start(name)

    def stop_all(self) -> None:
        """Stop all registered subsystems in reverse registration order."""
        for name in reversed(self._order):
            self.stop(name)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def status(self, name: str) -> LifecycleState:
        """
        Return the current lifecycle state of a subsystem.

        Args:
            name: Subsystem name.

        Returns:
            Current LifecycleState.

        Raises:
            KeyError: If subsystem is not registered.
        """
        return self._get(name).state

    def is_healthy(self, name: str) -> bool:
        """
        Return True if the subsystem is running and healthy.

        Args:
            name: Subsystem name.

        Raises:
            KeyError: If subsystem is not registered.
        """
        return self._get(name).is_healthy()

    def list_subsystems(self) -> List[str]:
        """Return subsystem names in registration order."""
        return list(self._order)

    def all_healthy(self) -> bool:
        """Return True only when every registered subsystem is healthy."""
        return all(self._subsystems[n].is_healthy() for n in self._order)

    def summary(self) -> Dict[str, str]:
        """
        Return a dict mapping each subsystem name to its state name.

        Returns:
            Mapping of name → state name string.
        """
        return {n: self._subsystems[n].state.name for n in self._order}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, name: str) -> SubsystemInfo:
        try:
            return self._subsystems[name]
        except KeyError:
            raise KeyError(f"Subsystem '{name}' is not registered.") from None
