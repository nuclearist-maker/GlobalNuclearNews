"""Validate an exported local verification attestation; never claim private CI access."""
from datetime import datetime
from uuid import UUID
from project_quality_gate import digest, local

def sha(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)

def public_review_errors(proof, root, kind, required, artifacts, author):
    errors=[]
    def check(ok, message):
        if not ok: errors.append('COMMON-05: public provenance: '+message)
    try:
        check(proof.get('version')==2 and proof.get('format')=='locally-verified-public-provenance','unknown format')
        check(proof.get('kind')==kind and proof.get('author')==author,'kind/author mismatch')
        verification=proof['local_verification']
        check(verification['status']=='PASS' and verification['errors']==[],'local verification failed')
        check(sha(verification['source_record_sha256']) and sha(verification['source_manifest_sha256']),'source provenance hashes missing')
        exported=datetime.fromisoformat(verification['checked_at']);check(exported.tzinfo is not None,'verification time zone missing')
        check(proof['artifacts']==artifacts,'current public artifacts not fully bound')
        for name,h in artifacts.items():
            check(sha(h) and digest(local(root,name))==h,'missing/changed artifact '+name)
        sessions=set();last=None
        for checkpoint in required:
            r=proof['reviews'][checkpoint]
            check(r['checkpoint']==checkpoint and r['provider']=='claude-code' and r['status']=='PASS' and r['exit_code']==0,'incomplete '+checkpoint)
            check(r['findings']==[] and r['limitations']==[],'unresolved '+checkpoint)
            check('Claude Code' in r['cli_version'],'CLI identity missing')
            sid=r['session_id'];check(str(UUID(sid))==sid and sid not in sessions,'invalid/reused session');sessions.add(sid)
            start=datetime.fromisoformat(r['started_at']);end=datetime.fromisoformat(r['finished_at'])
            check(start.tzinfo is not None and end.tzinfo is not None and start<=end<=exported and (last is None or start>=last),'invalid review ordering');last=end
            for k in ('receipt_sha256','request_sha256','response_sha256','reviewed_inputs_sha256'):
                check(sha(r[k]),'missing '+k)
            check(isinstance(r['verified_input_count'],int) and r['verified_input_count']>0,'empty verified inputs')
        check(proof['reviews'][required[-1]]['public_artifacts']==artifacts,'final review coverage missing')
        check(proof['private_inputs_checked_locally'] is True and proof['private_inputs_in_ci'] is False,'incorrect verification scope')
    except (KeyError,TypeError,ValueError,OSError,AttributeError) as e:
        errors.append('COMMON-05: invalid public provenance: '+str(e))
    return errors
