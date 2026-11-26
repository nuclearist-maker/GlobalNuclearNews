"""Validate Claude review provenance and coverage, not scientific truth."""
from datetime import datetime
from uuid import UUID
import hashlib
import json
from project_quality_gate import digest, local, read
from review_identity import reviewer_errors

CHECKPOINTS = ['direction', 'plan', 'research', 'design', 'draft', 'final']


def input_manifest(inputs):
    if not isinstance(inputs, dict) or not inputs:
        raise ValueError('nonempty input map required')
    if any(not isinstance(p, str) or not p or not isinstance(h, str) or
           len(h) != 64 or any(c not in '0123456789abcdef' for c in h)
           for p, h in inputs.items()):
        raise ValueError('invalid input path/hash')
    rows = [{'id': f'I{i:04d}', 'path': p, 'sha256': inputs[p]}
            for i, p in enumerate(sorted(inputs), 1)]
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest(), rows


def response_errors(raw, request):
    errors = []
    if not isinstance(raw, dict):
        return ['invalid CLI response']
    if raw.get('is_error') is not False or not raw.get('session_id'):
        errors.append('unsuccessful CLI response or missing session')
    try:
        if str(UUID(raw.get('session_id', ''))) != raw.get('session_id'):
            errors.append('noncanonical reviewer session UUID')
    except (ValueError, TypeError, AttributeError):
        errors.append('invalid reviewer session UUID')
    result = raw.get('structured_output')
    if not isinstance(result, dict):
        return errors + ['missing structured_output']
    if result.get('verdict') != 'PASS' or result.get('findings') != [] or result.get('limitations') != []:
        errors.append('unresolved findings, limitations or non-PASS review')
    if request.get('ack_format') == 'manifest-v1':
        try:
            sha, rows = input_manifest(request.get('inputs'))
            ids = result.get('reviewed_ids')
            if (result.get('reviewed_manifest_sha256') != sha or not isinstance(ids, list)
                    or any(not isinstance(i, str) for i in ids)
                    or len(ids) != len(rows) or sorted(ids) != [r['id'] for r in rows]):
                errors.append('reviewed manifest or IDs do not match request')
        except ValueError as exc:
            errors.append(str(exc))
    elif request.get('ack_format', 'full-map-v1') != 'full-map-v1':
        errors.append('unknown acknowledgement format')
    elif result.get('reviewed_inputs') != request.get('inputs'):
        errors.append('reviewed inputs do not match request')
    if result.get('checkpoint') != request.get('checkpoint'):
        errors.append('checkpoint mismatch')
    if not isinstance(result.get('summary'), str) or not result['summary'].strip():
        errors.append('review summary missing')
    return errors


def codex_events_errors(text, raw):
    """Structural check of a `codex exec --json` event log against the normalized response (r2 F01).

    Requires exactly one thread.started whose thread_id is the response session, a turn.completed,
    no turn.failed/error event, and a final agent_message whose JSON equals structured_output.
    """
    # Ordered turn tracking (2026-11-26 Codex workflow review F01): every turn must be
    # thread.started -> turn.started -> items -> turn.completed; the adopted response is the last
    # agent_message of the LAST turn and that turn must have completed. A later unfinished turn, a
    # completion without a start, or any event after the final completion is rejected.
    errors, threads, failed, final = [], [], False, None
    open_turn, turn_msg, turns_done, after_done = False, None, 0, False
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            return ['codex events log is not valid JSONL']
        kind = ev.get('type')
        if not open_turn and kind not in ('thread.started', 'turn.started'):
            # 2026-11-26 Codex workflow review r2 F01: any item/completion outside an open turn is a permanent
            # ordering error; a later well-formed turn must not clear it.
            errors.append('codex %s event outside a started turn' % (kind or 'untyped'))
        if turns_done and not open_turn and kind != 'turn.started':
            after_done = True  # anything but a new turn after a completed turn
        if kind == 'thread.started':
            if open_turn or turns_done:
                errors.append('codex thread.started inside or after a turn')
            threads.append(ev.get('thread_id'))
        elif kind == 'turn.started':
            if open_turn or not threads:
                errors.append('codex turn.started without a thread or inside an open turn')
            open_turn, turn_msg, after_done = True, None, False
        elif kind == 'turn.completed':
            if not open_turn:
                errors.append('codex turn.completed without a started turn')
            final, open_turn, turns_done = turn_msg, False, turns_done + 1
        elif kind in ('turn.failed', 'error'):
            failed = True
        elif kind == 'item.completed' and isinstance(ev.get('item'), dict) and ev['item'].get('type') == 'agent_message':
            if not open_turn:
                errors.append('codex agent_message outside a started turn')
            turn_msg = ev['item'].get('text')
    if threads != [raw.get('session_id')] or not raw.get('session_id'):
        errors.append('codex events log does not belong to exactly this session')
    if not turns_done or open_turn or failed or after_done:
        errors.append('codex turn did not complete successfully')
    try:
        if final is None or json.loads(final) != raw.get('structured_output'):
            errors.append('codex final message differs from normalized response')
    except ValueError:
        errors.append('codex final message is not the structured response')
    return errors


def provider_evidence_errors(receipt, raw, read_bound):
    """Bind the recorded provider to the provider-specific raw evidence (2026-11-25 independent review F01).

    read_bound(path, sha) must return file text only when the hash matches, else raise ValueError.
    """
    errors = []
    provider = receipt.get('provider')
    if provider == 'claude-code':
        if raw.get('type') != 'result' or 'provider' in raw:
            errors.append('raw response is not a Claude Code CLI result')
    elif provider == 'codex':
        if raw.get('provider') != 'codex':
            errors.append('raw response provider is not codex')
        events = receipt.get('events')
        if not isinstance(events, str):
            errors.append('codex events log not bound in receipt')
        else:
            errors += codex_events_errors(read_bound(events, receipt.get('events_sha256')), raw)
    else:
        errors.append('unknown reviewer provider')
    return errors


def review_errors(manifest, root, kind, required, artifacts, author, *, public_site=False):
    if manifest.get('version') == 2:
        if not public_site:
            return ['COMMON-05: exported provenance cannot replace local original review evidence']
        from public_review_gate import public_review_errors
        return public_review_errors(manifest,root,kind,required,artifacts,author)
    errors = []
    def fail(msg): errors.append('COMMON-05: ' + msg)
    def bound(name, sha):
        p = local(root, name)
        if not p.is_file() or digest(p) != sha:
            raise ValueError('missing/changed review evidence: ' + name)
        return p
    try:
        if manifest.get('version') != 1 or manifest.get('kind') != kind:
            fail('manifest version/kind mismatch')
        reviews = manifest.get('reviews', {})
        last_time = None
        sessions = set()
        for checkpoint in required:
            entry = reviews.get(checkpoint, {})
            receipt = read(bound(entry['receipt'], entry['sha256']))
            if receipt.get('exit_code') != 0 or receipt.get('status') != 'PASS':
                fail(checkpoint + ': incomplete/failed execution')
            # Cross-family independence: Codex-authored -> Claude Code, Claude-authored -> Codex.
            for msg in reviewer_errors(receipt.get('provider'), receipt.get('cli_version'), author):
                fail(checkpoint + ': ' + msg)
            request = read(bound(receipt['request'], receipt['request_sha256']))
            raw = read(bound(receipt['response'], receipt['response_sha256']))
            if request.get('kind') != kind or request.get('checkpoint') != checkpoint:
                fail(checkpoint + ': wrong task/checkpoint')
            if request.get('author') != author:
                fail(checkpoint + ': author mismatch')
            for msg in response_errors(raw, request): fail(checkpoint + ': ' + msg)
            for msg in provider_evidence_errors(receipt, raw, lambda n, h: bound(n, h).read_text(encoding='utf-8')):
                fail(checkpoint + ': ' + msg)
            session = raw.get('session_id')
            if session in sessions or session != receipt.get('session_id'):
                fail(checkpoint + ': reused/mismatched reviewer session')
            sessions.add(session)
            started = datetime.fromisoformat(receipt['started_at'])
            ended = datetime.fromisoformat(receipt['finished_at'])
            if started.tzinfo is None or ended.tzinfo is None or ended < started or (last_time and started < last_time):
                fail(checkpoint + ': invalid checkpoint order/time')
            last_time = ended
            inputs = request.get('inputs', {})
            if not isinstance(inputs, dict) or not inputs:
                fail(checkpoint + ': no reviewed inputs')
            else:
                for name, sha in inputs.items(): bound(name, sha)
                if checkpoint == required[-1] and any(inputs.get(p) != h for p, h in artifacts.items()):
                    fail(checkpoint + ': current artifacts not fully reviewed')
    except (KeyError, TypeError, ValueError, OSError, AttributeError) as exc:
        fail('invalid/missing review evidence: ' + str(exc))
    return errors
