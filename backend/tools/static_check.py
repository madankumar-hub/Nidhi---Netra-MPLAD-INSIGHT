"""Dependency-free static checks for the backend.

Verifies, without importing third-party packages:
  * every module parses;
  * every `from app...`/`from seed...` import resolves to a real module and a
    name that module actually defines;
  * no duplicate FastAPI route (method, path) pairs;
  * every admin route carries a role dependency.

Run:  python tools/static_check.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("app", "seed", "tests", "tools")

INTERNAL_GUARDS = {"require_internal", "require_reviewer", "require_elevated", "require_admin"}


def iter_python_files() -> List[Path]:
    files: List[Path] = []
    for package in PACKAGES:
        base = ROOT / package
        if base.exists():
            files.extend(sorted(base.rglob("*.py")))
    return files


def module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def module_path(name: str) -> Path | None:
    base = ROOT / Path(*name.split("."))
    if base.with_suffix(".py").exists():
        return base.with_suffix(".py")
    if (base / "__init__.py").exists():
        return base / "__init__.py"
    return None


def exported_names(tree: ast.Module) -> Set[str]:
    names: Set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.If):
            # e.g. `if TYPE_CHECKING:` blocks
            for inner in ast.walk(node):
                if isinstance(inner, (ast.Import, ast.ImportFrom)):
                    for alias in inner.names:
                        names.add(alias.asname or alias.name.split(".")[0])
                elif isinstance(inner, (ast.FunctionDef, ast.ClassDef)):
                    names.add(inner.name)
        elif isinstance(node, ast.Try):
            for inner in ast.walk(node):
                if isinstance(inner, (ast.Import, ast.ImportFrom)):
                    for alias in inner.names:
                        names.add(alias.asname or alias.name.split(".")[0])
    return names


def check_imports(trees: Dict[str, Tuple[Path, ast.Module]]) -> List[str]:
    errors: List[str] = []
    cache: Dict[str, Set[str]] = {}
    for name, (path, tree) in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if not node.module or node.level:
                    continue
                if not node.module.split(".")[0] in PACKAGES:
                    continue
                target = module_path(node.module)
                if target is None:
                    errors.append(f"{path.relative_to(ROOT)}:{node.lineno} unresolved module '{node.module}'")
                    continue
                if node.module not in cache:
                    cache[node.module] = exported_names(ast.parse(target.read_text(encoding="utf-8")))
                available = cache[node.module]
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    if alias.name in available:
                        continue
                    # Could be a submodule, e.g. `from app.routers import auth`
                    if module_path(f"{node.module}.{alias.name}") is not None:
                        continue
                    errors.append(
                        f"{path.relative_to(ROOT)}:{node.lineno} "
                        f"'{node.module}' does not define '{alias.name}'"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in PACKAGES and module_path(alias.name) is None:
                        errors.append(
                            f"{path.relative_to(ROOT)}:{node.lineno} unresolved module '{alias.name}'"
                        )
    return errors


def collect_routes(trees: Dict[str, Tuple[Path, ast.Module]]) -> List[Tuple[str, str, str, Set[str]]]:
    """Returns (method, full_path, function_name, dependency_names)."""
    routes: List[Tuple[str, str, str, Set[str]]] = []
    for name, (path, tree) in trees.items():
        if ".routers." not in name and not name.endswith(".routers"):
            continue
        prefix = ""
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Name) and func.id == "APIRouter":
                    for kw in node.value.keywords:
                        if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                            prefix = kw.value.value
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                if not (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)):
                    continue
                if func.value.id != "router" or func.attr not in {
                    "get", "post", "put", "patch", "delete",
                }:
                    continue
                route_path = ""
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    route_path = dec.args[0].value
                deps: Set[str] = set()
                for arg in list(node.args.args) + list(node.args.kwonlyargs):
                    pass
                for default in list(node.args.defaults) + list(node.args.kw_defaults):
                    if isinstance(default, ast.Call) and isinstance(default.func, ast.Name):
                        if default.func.id == "Depends" and default.args:
                            dep = default.args[0]
                            if isinstance(dep, ast.Name):
                                deps.add(dep.id)
                routes.append((func.attr.upper(), prefix + route_path, node.name, deps))
    return routes



# ---------------------------------------------------------------------------
# ORM <-> schema alignment
# ---------------------------------------------------------------------------
#: Response schema -> the ORM model it is validated from (`from_attributes`).
SCHEMA_MODEL_PAIRS = {
    "UserPublic": "User",
    "FundUpdateOut": "FundUpdate",
    "ProgressUpdateOut": "ProgressUpdate",
    "RiskFactorOut": "RiskFactor",
    "MitigationActionOut": "MitigationAction",
    "RiskAssessmentOut": "RiskAssessment",
    "ReviewOut": "Review",
    "NoteOut": "Note",
    "ActivityOut": "ActivityLog",
    "CitizenReportOut": "CitizenReport",
}


def _class_defs(trees: Dict[str, Tuple[Path, ast.Module]]) -> Dict[str, ast.ClassDef]:
    classes: Dict[str, ast.ClassDef] = {}
    for _, (_, tree) in trees.items():
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.setdefault(node.name, node)
    return classes


def _schema_fields(name: str, classes: Dict[str, ast.ClassDef], seen: Set[str] | None = None) -> Set[str]:
    seen = seen or set()
    if name in seen or name not in classes:
        return set()
    seen.add(name)
    node = classes[name]
    fields = {
        stmt.target.id
        for stmt in node.body
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
        and stmt.target.id != "model_config"
    }
    for base in node.bases:
        if isinstance(base, ast.Name):
            fields |= _schema_fields(base.id, classes, seen)
    return fields


def _model_attributes(name: str, classes: Dict[str, ast.ClassDef], seen: Set[str] | None = None) -> Set[str]:
    seen = seen or set()
    if name in seen or name not in classes:
        return set()
    seen.add(name)
    node = classes[name]
    attrs: Set[str] = set()
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            attrs.add(stmt.target.id)
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    attrs.add(target.id)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            attrs.add(stmt.name)  # @property and helpers
    for base in node.bases:
        if isinstance(base, ast.Name):
            attrs |= _model_attributes(base.id, classes, seen)
    return attrs


def check_schema_model_alignment(trees: Dict[str, Tuple[Path, ast.Module]]) -> List[str]:
    classes = _class_defs(trees)
    errors: List[str] = []
    checked = 0
    for schema, model in SCHEMA_MODEL_PAIRS.items():
        if schema not in classes or model not in classes:
            errors.append(f"schema/model pair not found: {schema} <-> {model}")
            continue
        checked += 1
        missing = _schema_fields(schema, classes) - _model_attributes(model, classes)
        for field in sorted(missing):
            errors.append(f"{schema}.{field} has no matching attribute on {model}")
    print(f"Checked {checked} response schemas against their ORM models.")
    return errors


def check_duplicate_kwargs(trees: Dict[str, Tuple[Path, ast.Module]]) -> List[str]:
    """Catch `Schema(**base.model_dump(), field=...)` where `base` already has `field`.

    This is valid syntax and only fails when the call actually runs, with
    "got multiple values for keyword argument". It shipped once: adding
    latitude/longitude to ProjectPublicSummary meant `**base.model_dump()`
    started supplying them, while the detail builders still passed them
    explicitly - so every project detail page returned a 500.

    The check resolves the schema being constructed, expands its inherited
    fields, and flags any explicit keyword that the spread would also provide.
    """
    classes = _class_defs(trees)
    problems: List[str] = []

    for module, (path, tree) in sorted(trees.items()):
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue

            schema = node.func.id
            if schema not in classes:
                continue

            # Does this call spread a model_dump() of something?
            spreads_dump = any(
                keyword.arg is None
                and isinstance(keyword.value, ast.Call)
                and isinstance(keyword.value.func, ast.Attribute)
                and keyword.value.func.attr in ("model_dump", "dict")
                for keyword in node.keywords
            )
            if not spreads_dump:
                continue

            # Fields the schema inherits are exactly what a parent's dump carries.
            inherited = _schema_fields(schema, classes) - _own_fields(schema, classes)
            explicit = {k.arg for k in node.keywords if k.arg is not None}

            for field in sorted(explicit & inherited):
                problems.append(
                    f"{path.relative_to(ROOT)}:{node.lineno}: {schema}(...) passes "
                    f"'{field}' explicitly, but **model_dump() already supplies it "
                    f"(inherited field) - duplicate keyword argument at runtime"
                )

    return problems


def _own_fields(name: str, classes: Dict[str, ast.ClassDef]) -> Set[str]:
    """Annotated fields declared directly on `name`, ignoring its bases."""
    node = classes.get(name)
    if node is None:
        return set()
    return {
        stmt.target.id
        for stmt in node.body
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
    }


def main() -> int:
    trees: Dict[str, Tuple[Path, ast.Module]] = {}
    errors: List[str] = []

    for path in iter_python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(ROOT)}:{exc.lineno} syntax error: {exc.msg}")
            continue
        trees[module_name(path)] = (path, tree)

    print(f"Parsed {len(trees)} modules.")
    errors.extend(check_imports(trees))
    errors.extend(check_schema_model_alignment(trees))
    errors.extend(check_duplicate_kwargs(trees))

    routes = collect_routes(trees)
    seen: Dict[Tuple[str, str], str] = {}
    for method, path_, fn, deps in routes:
        key = (method, path_)
        if key in seen:
            errors.append(f"duplicate route {method} {path_} ({seen[key]} and {fn})")
        seen[key] = fn
        if path_.startswith("/admin") and not (deps & INTERNAL_GUARDS):
            errors.append(f"admin route {method} {path_} ({fn}) has no role guard dependency")

    print(f"Found {len(routes)} API routes, {len(seen)} unique.")
    guarded = sum(1 for m, p, f, d in routes if d & INTERNAL_GUARDS)
    print(f"{guarded} routes are behind an explicit role guard.")

    if errors:
        print(f"\n{len(errors)} problem(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(
        "\nStatic check passed: no unresolved imports, no duplicate keyword "
        "arguments, no duplicate or unguarded admin routes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
