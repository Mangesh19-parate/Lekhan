"""Directed Acyclic Graph (DAG) & Kahn's Topological Sort.

Strict compliance with docs/PLAN.md Week 9 and docs/ARCHITECTURE.md Section 3.3:
- Kahn's algorithm orders field and derived calculation evaluation
- Cycle detection rejects cyclic templates at compile/publish time
- Deterministic topological ordering with diagnostic cycle paths
"""

from __future__ import annotations

from collections import deque


class CyclicDependencyError(ValueError):
    """Raised when circular dependencies are detected in the field graph."""

    def __init__(self, cycle_path: list[str]) -> None:
        self.cycle_path = cycle_path
        path_str = " -> ".join(cycle_path)
        super().__init__(f"Cyclic dependency detected in template fields: {path_str}")


class DependencyGraph:
    """Manages field dependency relationships and topological evaluation order."""

    def __init__(self) -> None:
        self._nodes: set[str] = set()
        # adjacency: u -> set of nodes that depend on u (u -> v)
        self._adjacency: dict[str, set[str]] = {}
        # reverse: v -> set of nodes that v depends on
        self._dependencies: dict[str, set[str]] = {}

    def add_node(self, node: str) -> None:
        """Registers a node in the graph."""
        self._nodes.add(node)
        self._adjacency.setdefault(node, set())
        self._dependencies.setdefault(node, set())

    def add_dependency(self, dependent: str, dependency: str) -> None:
        """Declares that 'dependent' depends on 'dependency'.

        Edge: dependency -> dependent (dependency must be computed before dependent).
        """
        self.add_node(dependent)
        self.add_node(dependency)

        if dependent == dependency:
            # Self-cycle
            raise CyclicDependencyError([dependent, dependent])

        self._adjacency[dependency].add(dependent)
        self._dependencies[dependent].add(dependency)

    def get_dependencies(self, node: str) -> set[str]:
        """Returns direct dependencies for a node."""
        return set(self._dependencies.get(node, set()))

    def get_dependents(self, node: str) -> set[str]:
        """Returns nodes directly depending on this node."""
        return set(self._adjacency.get(node, set()))

    def topological_sort(self, subset_nodes: set[str] | None = None) -> list[str]:
        """Executes Kahn's algorithm to determine evaluation order.

        If subset_nodes is provided, sorts only those nodes while respecting
        dependencies between them.

        Raises:
            CyclicDependencyError if the graph contains any circular reference.
        """
        target_nodes = set(self._nodes) if subset_nodes is None else set(subset_nodes)
        if not target_nodes:
            return []

        # Calculate in-degrees restricted to target_nodes
        in_degrees: dict[str, int] = {node: 0 for node in target_nodes}
        for u in target_nodes:
            for v in self._adjacency.get(u, set()):
                if v in target_nodes:
                    in_degrees[v] += 1

        # Queue nodes with in-degree 0 (sorted alphabetically for deterministic output)
        queue = deque(sorted([node for node, deg in in_degrees.items() if deg == 0]))
        order: list[str] = []

        while queue:
            u = queue.popleft()
            order.append(u)

            # Look at all dependents of u
            for v in sorted(self._adjacency.get(u, set())):
                if v in target_nodes:
                    in_degrees[v] -= 1
                    if in_degrees[v] == 0:
                        queue.append(v)

        if len(order) == len(target_nodes):
            return order

        # Cycle detected: trace the cycle path among unresolved nodes
        unresolved = {node for node, deg in in_degrees.items() if deg > 0}
        cycle_path = self._trace_cycle(unresolved, target_nodes)
        raise CyclicDependencyError(cycle_path)

    def _trace_cycle(self, unresolved_nodes: set[str], target_nodes: set[str]) -> list[str]:
        """Traces and extracts a concrete cycle path (e.g. ['A', 'B', 'C', 'A'])."""
        visited: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
        parent_path: list[str] = []

        def dfs(node: str) -> list[str] | None:
            visited[node] = 1
            parent_path.append(node)

            for neighbor in sorted(self._adjacency.get(node, set())):
                if neighbor not in target_nodes or neighbor not in unresolved_nodes:
                    continue
                if visited.get(neighbor) == 1:
                    # Found cycle: extract cycle subpath from first occurrence
                    idx = parent_path.index(neighbor)
                    return parent_path[idx:] + [neighbor]
                if visited.get(neighbor, 0) == 0:
                    result = dfs(neighbor)
                    if result is not None:
                        return result

            parent_path.pop()
            visited[node] = 2
            return None

        for start_node in sorted(unresolved_nodes):
            if visited.get(start_node, 0) == 0:
                cycle = dfs(start_node)
                if cycle:
                    return cycle

        # Fallback if no clean DFS path found
        sample = sorted(unresolved_nodes)
        return sample + [sample[0]] if sample else ["unknown_cycle"]
