"""Where internal QA records live.

Internal QA, approval and review records are private. They are kept outside this
public repository, in the parent project's data/qa/GlobalNuclearNews/ folder, at
the same relative path they used to have here (qa/releases/..., qa/theory/...).
Only qa/deployments/ stays in the repository because CI reads it.

The mapping applies only to this working copy (root == the repository root).
Temporary roots used by tests or historical snapshots are left untouched.
"""
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
PRIVATE_QA_BASE = SITE.parent / 'data' / 'qa' / 'GlobalNuclearNews'


def is_private_qa(name):
    n = str(name).replace('\\', '/').lstrip('./')
    return n.startswith('qa/') and not n.startswith('qa/deployments/')


def qa_base(root=None):
    """Base directory that holds qa/<...> records for the given root."""
    root = Path(root).resolve() if root else SITE
    return PRIVATE_QA_BASE if root == SITE else root
