"""Verify source visual provenance and DOCX embedding; visual judgements remain human QA."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import xml.etree.ElementTree as ET

def raw_sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def visual_errors(manifest, root, stage):
    errors=[]
    def need(ok,message):
        if not ok: errors.append('REPORT-05: '+message)
    def located(name):
        p=Path(name)
        return p if p.is_absolute() else root/p
    def file_check(item,key,hashkey):
        try:
            p=located(item[key]);ok=p.is_file() and raw_sha(p)==item[hashkey]
            need(ok,'missing/changed '+key+': '+str(p));return p if ok else None
        except (KeyError,TypeError,ValueError,OSError) as e:
            need(False,'invalid '+key+': '+str(e));return None
    if not isinstance(manifest,dict): return ['REPORT-05: invalid visual manifest']
    need(manifest.get('version')==1,'manifest version must be 1')
    need(bool(manifest.get('report_id')),'report_id required')
    visuals=manifest.get('visuals',[])
    need(isinstance(visuals,list) and bool(visuals),'at least one relevant collected/adapted visual required')
    if not isinstance(visuals,list): return errors
    ids=set()
    for v in visuals:
        if not isinstance(v,dict):need(False,'invalid visual entry');continue
        valid_id=isinstance(v.get('id'),str) and bool(v['id'])
        need(valid_id and v['id'] not in ids,'unique visual id required')
        if valid_id:ids.add(v['id'])
        for key in ('source_id','source_url','source_location','selection_reason','insertion_anchor','caption','source_line','explanation','transformation'):
            need(isinstance(v.get(key),(str,int)) and bool(str(v.get(key,'' )).strip()),key+' required')
        need(v.get('evidence_type') in ('original_crop','translated','redrawn'),'evidence_type must distinguish original/translation/redrawing')
        file_check(v,'original_file','original_sha256');file_check(v,'image_file','image_sha256')
    if stage=='finalize':
        docx=file_check(manifest,'final_docx','final_docx_sha256');file_check(manifest,'final_pdf','final_pdf_sha256')
        qa=manifest.get('qa',{})
        need(isinstance(qa,dict),'qa object required')
        if isinstance(qa,dict):
            for key in ('source_match','word_100_150','pdf_all_pages','labels_units_legends','no_overlap_or_crop'):
                need(qa.get(key)=='PASS','actual human QA missing/FAIL: '+key)
            need(bool(qa.get('reviewer')) and bool(qa.get('checked_at')),'QA reviewer/time required')
        if docx:
            try:
                with ZipFile(docx) as z:
                    rootxml=ET.fromstring(z.read('word/document.xml'))
                    relxml=ET.fromstring(z.read('word/_rels/document.xml.rels'))
                    ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    rels={x.attrib['Id']:x.attrib.get('Target','') for x in relxml if x.attrib.get('TargetMode')!='External'}
                    embedded=set()
                    for blip in rootxml.findall('.//a:blip',ns):
                        rid=blip.get('{'+ns['r']+'}embed');target=rels.get(rid,'')
                        if target:
                            name=target.lstrip('/') if target.startswith('/') else 'word/'+target
                            if name in z.namelist():embedded.add(hashlib.sha256(z.read(name)).hexdigest())
                    text=''.join(rootxml.itertext())
                    # ElementTree itertext includes Word text values; normalize whitespace across runs.
                    compact=lambda s:''.join(str(s).split())
                    for v in visuals:
                        if not isinstance(v,dict):continue
                        need(v.get('image_sha256') in embedded,'visual not actually embedded in DOCX: '+str(v.get('id')))
                        for key in ('caption','source_line','explanation'):
                            need(bool(v.get(key)) and compact(v[key]) in compact(text),'DOCX missing '+key+': '+str(v.get('id')))
            except (OSError,KeyError,ValueError,ET.ParseError,BadZipFile) as e:need(False,'DOCX inspection failed: '+str(e))
    return errors
