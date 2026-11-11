"""Validate Claude review provenance and coverage, not scientific truth."""
from datetime import datetime
from uuid import UUID
import hashlib
import json
from project_quality_gate import digest, local, read

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
            errors.append('noncanonical Claude session UUID')
    except (ValueError, TypeError, AttributeError):
        errors.append('invalid Claude session UUID')
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
            if receipt.get('provider') != 'claude-code' or receipt.get('exit_code') != 0 or receipt.get('status') != 'PASS':
                fail(checkpoint + ': incomplete/failed execution')
            if not isinstance(receipt.get('cli_version'), str) or 'Claude Code' not in receipt['cli_version']:
                fail(checkpoint + ': missing Claude Code CLI version')
            request = read(bound(receipt['request'], receipt['request_sha256']))
            raw = read(bound(receipt['response'], receipt['response_sha256']))
            if request.get('kind') != kind or request.get('checkpoint') != checkpoint:
                fail(checkpoint + ': wrong task/checkpoint')
            if request.get('author') != author:
                fail(checkpoint + ': author mismatch')
            for msg in response_errors(raw, request): fail(checkpoint + ': ' + msg)
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
