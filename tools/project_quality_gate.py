"""Fail-closed evidence/approval gate. No third-party runtime dependencies.

Human judgements are attestations, never inferred from a successful command.
The gate verifies their presence, reviewer separation and exact byte bindings.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

SITE = Path(__file__).resolve().parents[1]
POLICY = SITE / 'policies/quality_gates.json'

def digest(path):
    data=path.read_bytes()
    if path.suffix.lower() in ('.html','.css','.js','.json','.md','.txt','.xml'):
        data=data.replace(b'\r\n',b'\n')
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def local(root, name):
    p = (root / name).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError('Path escapes declared root: ' + str(name))
    return p


def report_basis_errors(basis):
    """Validate coverage/provenance shape; semantic depth remains an inspected judgement."""
    problems = []
    def require(condition, message):
        if not condition: problems.append('NEWS-06: ' + message)
    def text(value): return isinstance(value,str) and bool(value.strip())
    def sha(value): return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)
    def urls(value): return isinstance(value,list) and bool(value) and all(isinstance(u,str) and u.startswith(('https://','http://')) for u in value)
    if not isinstance(basis,dict): return ['NEWS-06: invalid report basis object']
    require(basis.get('version')==1 and basis.get('status')=='READY', 'basis missing/not READY; rework required')
    reports=basis.get('primary_reports',[])
    require(isinstance(reports,list) and bool(reports),'completed primary report required')
    ids={}
    for report in reports if isinstance(reports,list) else []:
        if not isinstance(report,dict): require(False,'invalid primary report'); continue
        rid=report.get('id')
        require(text(rid) and rid not in ids,'unique report ID required')
        if text(rid): ids[rid]=report
        require(text(report.get('title')) and text(report.get('report_date')),'report title/date required')
        require(report.get('qa_status')=='PASS' and sha(report.get('report_sha256')) and sha(report.get('qa_sha256')),'report version and completed QA provenance required')
        require(isinstance(report.get('section_ids'),list) and bool(report['section_ids']),'report section IDs required')
    for expected_key, map_key, fields in [
        ('body_sections','section_map',('finding','explanation_gain')),
        ('images','image_map',('learning_point','visual_encoding','caveat'))]:
        expected=basis.get(expected_key,[]); mapping=basis.get(map_key,{})
        require(isinstance(expected,list) and bool(expected) and all(text(s) for s in expected),expected_key+' required')
        require(isinstance(mapping,dict),'invalid '+map_key)
        if not isinstance(expected,list) or not isinstance(mapping,dict): continue
        require(len(expected)==len(set(expected)) if all(isinstance(s,str) for s in expected) else False,'duplicate/invalid planned entries')
        require(set(mapping)==set(expected) if all(isinstance(s,str) for s in expected) else False,map_key+' must cover every planned section/image')
        for name,item in mapping.items():
            if not isinstance(item,dict): require(False,'invalid mapping '+name); continue
            report=ids.get(item.get('report_id'),{})
            require(bool(report) and item.get('report_section') in report.get('section_ids',[]),'unresolved report/section for '+name)
            require(all(text(item.get(field)) for field in fields),'missing explanation/visual content for '+name)
            require(urls(item.get('source_urls')),'public primary source URLs required for '+name)
    coverage=basis.get('depth_coverage',{})
    require(isinstance(coverage,dict),'depth coverage required')
    if isinstance(coverage,dict):
        for field in ['mechanism_or_process','evidence','case_or_comparison','limits']:
            require(isinstance(coverage.get(field),list) and bool(coverage[field]) and all(s in basis.get('body_sections',[]) for s in coverage[field]),'missing depth coverage: '+field)
    return problems

def validate(record, root, kind, stage, required_paths=()):
    policy = read(POLICY)
    errors = []
    if record.get('version') != 1 or record.get('kind') != kind:
        errors.append('COMMON-01: record version/kind mismatch')
    rules = policy.get(kind, {}).get(stage)
    if not rules:
        return ['COMMON-01: unknown kind/stage']
    artifacts = record.get('artifacts', {})
    if not isinstance(artifacts, dict) or not artifacts:
        return ['COMMON-02: missing artifact hashes']
    def check_file(name, sha, label):
        try:
            p = local(root, name)
            if not isinstance(sha,str) or len(sha)!=64 or not p.is_file() or digest(p)!=sha:
                errors.append(label + ': missing/changed file ' + name)
        except (ValueError, TypeError, OSError) as e:
            errors.append(label + ': ' + str(e))
    for path, sha in artifacts.items():
        check_file(path, sha, 'COMMON-02')
    for path in required_paths:
        try:
            name = Path(path).resolve().relative_to(root.resolve()).as_posix()
            if name not in artifacts:
                errors.append('COMMON-02: required input/output not bound: ' + name)
        except ValueError:
            errors.append('COMMON-02: required file is outside root')
    author = record.get('author')
    if not isinstance(author,str) or not author.strip():
        errors.append('COMMON-03: author missing')
    checks = record.get('checks', {})
    for rule in rules['checks']:
        c = checks.get(rule, {})
        if c.get('status') != 'PASS':
            errors.append(rule + ': missing/FAIL; perform inspection and rework')
            continue
        if c.get('artifacts') != artifacts:
            errors.append(rule + ': check does not bind this complete artifact set')
        if not c.get('reviewer') or not c.get('checked_at'):
            errors.append(rule + ': reviewer/time missing')
        if rule in policy['independent'] and c.get('reviewer') == author:
            errors.append(rule + ': independent reviewer must differ from author')
        evidence = c.get('evidence', {})
        if not isinstance(evidence,dict) or not evidence:
            errors.append(rule + ': evidence files missing')
        else:
            for name, sha in evidence.items():
                check_file(name, sha, rule)
        if rule == 'NEWS-07':
            from news_spacing_gate import html_errors
            for name in artifacts:
                if name.endswith('.html') and 'posts/news/' in name:
                    errors.extend('NEWS-07: '+name+': '+json.dumps(e,ensure_ascii=False) for e in html_errors(local(root,name)))
        if rule == 'NEWS-06':
            basis_name=c.get('report_basis')
            if not isinstance(basis_name,str) or basis_name not in evidence:
                errors.append('NEWS-06: report_basis must identify a hash-bound evidence JSON')
            else:
                try:
                    errors.extend(report_basis_errors(read(local(root,basis_name))))
                except (ValueError,TypeError,OSError) as e:
                    errors.append('NEWS-06: invalid report basis: '+str(e))
        if rule == 'REPORT-05':
            visual_name=c.get('visual_manifest')
            if not isinstance(visual_name,str) or visual_name not in evidence:
                errors.append('REPORT-05: visual_manifest must identify a hash-bound evidence JSON')
            else:
                try:
                    from report_visual_gate import visual_errors
                    vm=read(local(root,visual_name))
                    errors.extend(visual_errors(vm,root,stage))
                    if stage=='finalize':
                        for key in ('final_docx','final_pdf'):
                            p=local(root,vm.get(key,''))
                            name=p.relative_to(root.resolve()).as_posix()
                            if name not in artifacts:
                                errors.append('REPORT-05: final document not bound to artifact set: '+name)
                except (ValueError,TypeError,OSError) as e:
                    errors.append('REPORT-05: invalid visual manifest: '+str(e))
    approvals = record.get('approvals', [])
    for scope in rules['approvals']:
        accepted = False
        for a in approvals:
            if a.get('scope') != scope or a.get('by') != 'user' or not a.get('text','').strip() or not a.get('at'):
                continue
            bindings = a.get('artifacts', {})
            if scope == 'publish' and a.get('mode') == 'conditional':
                # Scope approval binds the unchanged direction; final independent QA binds outputs.
                if not a.get('direction') or a['direction'] not in bindings:
                    continue
            elif scope == 'publish' and bindings != artifacts:
                continue
            if not bindings or any(artifacts.get(p) != h for p,h in bindings.items()):
                continue
            accepted = True
        if not accepted:
            errors.append('COMMON-01: missing valid user approval for ' + scope)
    return errors

def site_errors(site):
    baseline = read(site / 'policies/published_baseline.json')
    errors = []
    from news_spacing_gate import site_errors as news_spacing_errors
    errors.extend('NEWS-07: '+json.dumps(e,ensure_ascii=False) for e in news_spacing_errors(site))
    covered = {}
    for f in (site/'qa/releases').glob('*.json'):
        r=read(f)
        kind=r.get('kind')
        if kind not in ('theory','news'):
            errors.append('Unexpected release kind: '+f.name); continue
        err=validate(r, site, kind, 'publish')
        if err:
            errors.extend([f.name+': '+e for e in err]); continue
        covered.update(r['artifacts'])
    # The baseline is restricted to unchanged files from the already-published commit.
    # Any altered baseline file or newly added public source needs a fresh release record.
    from public_files import collect
    public = set(baseline['files'])
    public.update(p.relative_to(site.resolve()).as_posix() for p in collect(site))
    for name in sorted(public):
        p=local(site,name)
        if not p.is_file():
            errors.append('Missing published dependency: '+name); continue
        sha=digest(p)
        if baseline['files'].get(name)==sha: continue
        if covered.get(name)!=sha:
            errors.append('Unapproved new/changed public file: '+name)
    return errors

def require(record_path, root, kind, stage, required_paths=()):
    if not record_path:
        raise ValueError('Quality gate BLOCKED: --quality-record is required; see docs/QUALITY_GATES.md')
    errors=validate(read(Path(record_path)), Path(root), kind, stage, required_paths)
    if errors:
        raise ValueError('Quality gate BLOCKED; rework and rerun:\n'+'\n'.join(errors))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--record',type=Path)
    ap.add_argument('--root',type=Path,default=Path.cwd())
    ap.add_argument('--kind',choices=['brief','report','theory','news'])
    ap.add_argument('--stage',choices=['research','generate','draft','finalize','publish'])
    ap.add_argument('--require-file',type=Path,action='append',default=[])
    ap.add_argument('--site',action='store_true')
    ap.add_argument('--receipt',type=Path)
    args=ap.parse_args()
    try:
        if args.site: errors=site_errors(SITE)
        elif args.record and args.kind and args.stage:
            errors=validate(read(args.record),args.root,args.kind,args.stage,args.require_file)
        else: errors=['Missing --record/--kind/--stage (or --site)']
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as e:
        errors=['Invalid/missing evidence: '+str(e)]
    result={'status':'FAIL' if errors else 'PASS','errors':errors,'next_action':'REWORK_AND_RECHECK' if errors else 'PROCEED_WITHIN_APPROVED_SCOPE'}
    if args.receipt:
        args.receipt.parent.mkdir(parents=True,exist_ok=True)
        args.receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True,indent=2))
    return 1 if errors else 0

if __name__=='__main__': sys.exit(main())
