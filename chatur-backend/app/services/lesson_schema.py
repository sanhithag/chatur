"""Lesson JSON shape + automatic validation checks (does NOT replace human review)."""
import ast
import operator
from typing import Any, Dict, List

STYLE_KEYS = ["simple", "detailed", "visual", "analogy", "worked"]
SCHEMA_HINT = """{
 "title": str, "introduction": str, "objectives": [str],
 "styles": {"simple": str, "detailed": str, "visual": str, "analogy": str, "worked": str},
 "key_terms": [str], "definitions": [{"term": str, "meaning": str}],
 "misconceptions": [{"wrong": str, "correct": str}], "summary": str,
 "comprehension": {"question": str, "options": [str,str,str,str], "correct_index": int, "explanation": str},
 "practice": [{"question": str, "options": [str,str,str,str], "correct_index": int, "hint": str, "explanation": str, "check_expr": str|null, "check_value": number|null}]
}"""

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


def _mcq_issues(q: Dict[str, Any], label: str) -> List[str]:
    out = []
    opts = q.get("options")
    if not isinstance(opts, list) or len(opts) < 2 or len({str(o).strip() for o in opts}) != len(opts):
        out.append(f"{label}: options missing or duplicated")
        return out
    ci = q.get("correct_index")
    if not isinstance(ci, int) or not 0 <= ci < len(opts):
        out.append(f"{label}: correct_index out of range")
    for k in ("question", "explanation"):
        if not str(q.get(k, "")).strip():
            out.append(f"{label}: empty {k}")
    return out


def validate_lesson(c: Dict[str, Any], concept_name: str = "") -> Dict[str, Any]:
    issues: List[str] = []
    for k in ("title", "introduction", "summary"):
        if not str(c.get(k, "")).strip():
            issues.append(f"missing {k}")
    if not c.get("objectives"):
        issues.append("missing objectives")
    st = c.get("styles") or {}
    for k in STYLE_KEYS:
        if len(str(st.get(k, "")).strip()) < 40:
            issues.append(f"style '{k}' missing/too short")
    if len({str(st.get(k, "")).strip() for k in STYLE_KEYS}) < len(STYLE_KEYS):
        issues.append("explanation styles are not distinct")
    issues += _mcq_issues(c.get("comprehension") or {}, "comprehension")
    practice = c.get("practice") or []
    if len(practice) < 3:
        issues.append("fewer than 3 practice questions")
    for i, q in enumerate(practice):
        issues += _mcq_issues(q, f"practice[{i}]")
        if not str(q.get("hint", "")).strip():
            issues.append(f"practice[{i}]: missing hint")
        expr, val = q.get("check_expr"), q.get("check_value")
        if expr is not None and val is not None:  # programmatic arithmetic verification
            try:
                if abs(_eval(ast.parse(str(expr), mode="eval").body) - float(val)) > 1e-6:
                    issues.append(f"practice[{i}]: check_expr does not equal check_value")
                elif isinstance(q.get("correct_index"), int) and q.get("options") and \
                        float(str(q["options"][q["correct_index"]]).split()[0].replace(",", "")) != float(val):
                    issues.append(f"practice[{i}]: marked answer differs from verified value")
            except Exception:
                pass
    return {"ok": not issues, "issues": issues}
