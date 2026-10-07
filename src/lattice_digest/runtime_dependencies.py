"""Deterministic local import closure and published manifest omission checks."""
from __future__ import annotations
import ast
from pathlib import Path, PurePosixPath

MANIFEST_PATH = "config/runtime_dependencies.json"


def safe_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value:
        raise ValueError("invalid runtime dependency path")
    return path.as_posix()


def module_path(root: Path, module: str) -> str | None:
    relative = module.replace(".", "/")
    prefixes = ("src/", "") if module.startswith("lattice_digest") else ("", "src/")
    for prefix in prefixes:
        for suffix in (".py", "/__init__.py"):
            name = prefix + relative + suffix
            if (root / name).is_file():
                return name
    if module == "lattice_digest" or module.startswith(("lattice_digest.", "scripts.")):
        raise ValueError(f"unresolved local import: {module}")
    return None


def import_closure(root: Path, roots: list[str], *, function_scopes: dict | None = None,
                   branch_values: dict | None = None) -> set[str]:
    pending, visited = list(roots), set()
    while pending:
        name = safe_path(pending.pop())
        if name in visited:
            continue
        visited.add(name)
        source = root / name
        if not source.is_file() or not source.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"missing or external dependency: {name}")
        tree = ast.parse(source.read_text(encoding="utf-8-sig"), filename=name)
        values = (branch_values or {}).get(name, {})
        class EnabledBranches(ast.NodeTransformer):
            def visit_If(self, node):
                key = ast.unparse(node.test)
                if key == "__name__ == '__main__'":
                    return []
                if key in values:
                    chosen = node.body if values[key] else node.orelse
                    return [self.visit(child) for child in chosen]
                return self.generic_visit(node)
        tree = EnabledBranches().visit(tree)
        nodes = [tree]
        if name in (function_scopes or {}):
            selected = set(function_scopes[name])
            definitions = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            nodes = [node for node in tree.body if not isinstance(node, definitions)]
            nodes += [node for node in tree.body if isinstance(node, definitions) and node.name in selected]
            found = {node.name for node in nodes if isinstance(node, definitions)}
            if found != selected:
                raise ValueError(f"missing reviewed callable: {name}")
            own = {node.name for node in tree.body if isinstance(node, definitions)}
            calls = {node.func.id for part in nodes for node in ast.walk(part)
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
            if (calls & own) - selected:
                raise ValueError(f"unreviewed callable dependency: {name}: {sorted((calls & own) - selected)}")
        module = name.removeprefix("src/").removesuffix(".py").replace("/", ".")
        package = module.removesuffix(".__init__") if name.endswith("/__init__.py") else module.rpartition(".")[0]
        if module.startswith("lattice_digest."):
            pending.append("src/lattice_digest/__init__.py")
        approved_dynamic = set()
        if name == 'src/lattice_digest/public_contract.py':
            for function in tree.body:
                if isinstance(function, ast.FunctionDef) and function.name == 'trace_imports':
                    approved_dynamic = {id(node) for node in ast.walk(function)
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name) and node.func.value.id == 'importlib'
                        and node.func.attr == 'import_module' and len(node.args) == 1
                        and isinstance(node.args[0], ast.Name) and node.args[0].id == 'module'
                        and not node.keywords}
            if len(approved_dynamic) != 1:
                raise ValueError('unreviewed command import tracer')
        for part in nodes:
            for node in ast.walk(part):
                imports = []
                if isinstance(node, ast.Import):
                    imports = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    base = node.module or ""
                    if node.level:
                        components = package.split(".")
                        base = ".".join(components[:len(components) - node.level + 1] + ([base] if base else []))
                    imports = [base]
                    for alias in node.names:
                        candidate = f"{base}.{alias.name}"
                        relative = candidate.replace(".", "/")
                        if any((root / (prefix + relative + suffix)).is_file()
                               for prefix in ("", "src/") for suffix in (".py", "/__init__.py")):
                            imports.append(candidate)
                elif isinstance(node, ast.Call):
                    dynamic = (isinstance(node.func, ast.Name) and node.func.id in {"__import__", "eval", "exec"}) or (
                        isinstance(node.func, ast.Attribute) and node.func.attr == "import_module")
                    if dynamic and id(node) not in approved_dynamic:
                        raise ValueError(f"unreviewed dynamic execution: {name}")
                for imported in imports:
                    if imported:
                        local = module_path(root, imported)
                        if local:
                            pending.append(local)
    return visited


def profile_paths(root: Path, manifest: dict, profile: str) -> list[str]:
    if manifest.get("schema_version") != 1:
        raise ValueError("unknown dependency manifest version")
    selected = manifest["profiles"][profile]
    paths = {safe_path(path) for path in selected["paths"]}
    expected = import_closure(root, selected["roots"], function_scopes=selected.get("function_scopes"),
                             branch_values=selected.get("branch_values"))
    non_python = {safe_path(path) for path in selected["reviewed_non_python"]}
    required = expected | non_python | {MANIFEST_PATH}
    if paths != required:
        raise ValueError(f"dependency manifest omission or stale entry: {sorted(required ^ paths)}")
    return sorted(paths)
