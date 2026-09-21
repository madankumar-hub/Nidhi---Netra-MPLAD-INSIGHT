"""Cross-check the frontend API client against the backend route table.

Guards against the classic failure mode of a UI that calls endpoints which do
not exist. Parses `backend/app/routers/*.py` for FastAPI decorators and
`frontend/src/api/*.ts` for request paths, normalises both (path parameters
become `{}`) and reports any frontend call with no matching backend route.

Run:  python tools/check_api_contract.py
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

API_PREFIX = "/api"
PARAM = re.compile(r"\{[^}]+\}|\$\{[^}]+\}")
METHODS = {"get", "post", "put", "patch", "delete"}


def normalise(path: str) -> str:
    path = PARAM.sub("{}", path)
    path = path.split("?")[0]
    return path.rstrip("/") or "/"


def backend_routes() -> Set[Tuple[str, str]]:
    routes: Set[Tuple[str, str]] = set()
    for file in sorted((BACKEND / "app" / "routers").glob("*.py")):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        prefix = ""
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Name) and func.id == "APIRouter":
                    for keyword in node.value.keywords:
                        if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant):
                            prefix = keyword.value.value
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                func = decorator.func
                if not (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)):
                    continue
                if func.value.id != "router" or func.attr not in METHODS:
                    continue
                route = ""
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    route = decorator.args[0].value
                routes.add((func.attr.upper(), normalise(API_PREFIX + prefix + route)))
    return routes


QUERY_EXPR = re.compile(r"\$\{\s*buildQuery\([^}]*\}?\s*\)?\s*\}")
CALL = re.compile(r"(?:request|downloadFile)\s*(?:<[^(]*?>)?\s*\(\s*[`'\"]([^`'\"]+)[`'\"]")
QUERY_VAR = re.compile(r"(?:const|let)\s+(\w+)\s*=\s*buildQuery\(")
METHOD_HINT = re.compile(r"method:\s*'(GET|POST|PATCH|PUT|DELETE)'")
FUNCTION_SPLIT = re.compile(r"^export function ", re.M)


def strip_query(raw: str, query_vars: Sequence[str] = ()) -> str:
    """Remove the query-string interpolation from a template literal.

    `/admin/activity${buildQuery({ limit })}` -> `/admin/activity`
    `/admin/projects${qs}`                    -> `/admin/projects`
    """
    raw = QUERY_EXPR.sub("", raw)
    for name in query_vars:
        raw = raw.replace("${" + name + "}", "")
    return raw


def frontend_calls() -> List[Tuple[str, str, str]]:
    """Returns (method, path, source location). One entry per exported call."""
    calls: List[Tuple[str, str, str]] = []
    for file in sorted((FRONTEND / "src" / "api").glob("*.ts")):
        text = file.read_text(encoding="utf-8")
        offset = 0
        for block in FUNCTION_SPLIT.split(text):
            line_no = text[:offset].count("\n") + 1 if offset else 1
            offset += len(block) + len("export function ")
            match = CALL.search(block)
            if not match:
                continue
            raw = strip_query(match.group(1), QUERY_VAR.findall(block))
            if not raw.startswith("/"):
                continue
            method_match = METHOD_HINT.search(block)
            method = method_match.group(1) if method_match else "GET"
            name = block.split("(")[0].strip() or file.stem
            calls.append((method, normalise(API_PREFIX + raw), f"{file.name}:{name}"))
    return calls


def main() -> int:
    routes = backend_routes()
    calls = frontend_calls()
    by_path: Dict[str, Set[str]] = {}
    for method, path in routes:
        by_path.setdefault(path, set()).add(method)

    problems: List[str] = []
    for method, path, where in calls:
        if path not in by_path:
            problems.append(f"{where}: no backend route matches {method} {path}")
        elif method not in by_path[path]:
            problems.append(
                f"{where}: {path} exists but not for {method} "
                f"(backend allows {', '.join(sorted(by_path[path]))})"
            )

    print(f"Backend exposes {len(routes)} routes.")
    print(f"Frontend API client makes {len(calls)} distinct calls.")

    if problems:
        print(f"\n{len(problems)} mismatch(es):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    unused = sorted(path for path in by_path if not any(c[1] == path for c in calls))
    if unused:
        print(f"\n{len(unused)} backend route(s) not called by the web client:")
        for path in unused:
            print(f"  · {path}")
    print("\nAPI contract check passed: every frontend call resolves to a real backend route.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
