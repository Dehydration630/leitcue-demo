"""Offline public-artifact checks. Heuristic guard, not proof of no secrets."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    ".gitignore", ".nojekyll", ".github/workflows/checks.yml",
    "README.md", "NOTICE.md", "index.html",
    "assets/app.mjs", "assets/logic.mjs", "assets/style.css",
    "assets/cover.svg", "assets/icon.svg",
    "assets/product-flow.svg", "assets/product-architecture.svg",
    "examples/core.py", "examples/scenario.json", "examples/README.md",
    "tests/test_core.py", "tests/demo.test.mjs", "scripts/check_publication.py",
    *{f"docs/{name}.md" for name in (
        "CASE_STUDY", "PRD", "RESEARCH", "DECISIONS", "EVALUATION",
        "FIELD_FRAMEWORK", "ARCHITECTURE", "METRICS", "ROADMAP",
        "PUBLICATION", "TESTING")},
}
PATTERNS = {
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "github_token": r"(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{25,}",
    "api_token": r"\bsk[-_][A-Za-z0-9_-]{24,}",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "local_path": r"/(?:Users|home|opt)/[A-Za-z0-9_-]+/",
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "signed_url": r"[?&](?:X-Amz-Signature|X-Tos-Signature|Signature)=",
    "private_record_id": r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b",
}


def check():
    errors, found = [], set()
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in {".git", "__pycache__"} for part in relative.parts):
            continue
        if path.is_symlink():
            errors.append(f"symlink: {relative}")
            continue
        if not path.is_file():
            continue
        name = relative.as_posix()
        found.add(name)
        if name not in ALLOWED:
            errors.append(f"not_allowlisted: {name}")
            continue
        content = path.read_text(encoding="utf-8")
        for kind, pattern in PATTERNS.items():
            if re.search(pattern, content):
                errors.append(f"{kind}: {name}")
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", content):
                target = target.split("#")[0]
                if not target or target.startswith(("https://", "http://")):
                    continue
                linked = (path.parent / target).resolve()
                if not linked.is_relative_to(ROOT) or not linked.exists():
                    errors.append(f"broken_local_link: {name} -> {target}")
    for missing in sorted(ALLOWED - found):
        errors.append(f"missing: {missing}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"PASS: {len(found)} allowlisted public files; links and sensitive-pattern checks")
    return 0


if __name__ == "__main__":
    sys.exit(check())
