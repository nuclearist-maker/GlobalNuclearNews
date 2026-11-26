"""Cross-family independent reviewer identity (2026-11-25 user instruction).

The producing agent family and the reviewing CLI provider must differ:
- author ``codex``/``gpt*``  -> reviewer provider ``claude-code`` (legacy flow, unchanged)
- author ``claude*``         -> reviewer provider ``codex`` (Claude-produced flow)
Validates recorded identity only; it does not authenticate a CLI log or judge content.
"""

PROVIDERS = {
    'claude-code': 'Claude Code',  # `claude --version` -> "2.x (Claude Code)"
    'codex': 'codex-cli',          # `codex --version`  -> "codex-cli 0.x"
}


def author_family(author):
    """Map a quality-record author to the producing agent family, or None."""
    a = (author or '').strip().lower() if isinstance(author, str) else ''
    if a.startswith('claude'):
        return 'claude-code'
    if a.startswith(('codex', 'gpt')):
        return 'codex'
    return None


def required_provider(author):
    """Reviewer provider required for this author. Unknown/human authors keep the legacy Claude reviewer."""
    return 'codex' if author_family(author) == 'claude-code' else 'claude-code'


def reviewer_errors(provider, cli_version, author):
    """Return identity errors for one review receipt (empty list when acceptable)."""
    errors = []
    if provider not in PROVIDERS:
        return ['unknown reviewer provider: ' + str(provider)]
    if not isinstance(cli_version, str) or PROVIDERS[provider] not in cli_version:
        errors.append('missing %s CLI version' % PROVIDERS[provider])
    if provider != required_provider(author):
        errors.append('reviewer provider %s is not independent of author family %s (required: %s)'
                      % (provider, author_family(author) or 'legacy', required_provider(author)))
    return errors
