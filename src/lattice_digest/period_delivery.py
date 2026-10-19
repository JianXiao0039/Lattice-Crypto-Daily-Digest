"""Single-writer, create-only period publication with durable pair verification.

Two independent paths cannot be crash-atomic. JSON is linked last as commit point;
an interrupted orphan is rejected, never overwritten or silently accepted.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import os
import re
import tempfile
from uuid import uuid4


@contextmanager
def writer_lock(paths, profile: str, key: str):
    if profile not in ('DAILY','WEEKLY','MONTHLY') or not re.fullmatch(r'\d{4}-(?:\d{2}(?:-\d{2})?|W\d{2})',key):
        raise ValueError('invalid writer identity')
    directory=paths.audit_root/'writer-locks'
    if directory.is_symlink() or getattr(directory,'is_junction',lambda:False)():
        raise ValueError('writer lock redirection forbidden')
    directory.mkdir(parents=True,exist_ok=True)
    target=directory/f'{profile}-{key}.lock'
    try: stream=target.open('x',encoding='utf-8')
    except FileExistsError as exc:
        raise ValueError('ACTIVE_OR_STALE_WRITER_LOCK; inspect owner before recovery') from exc
    try:
        with stream:
            stream.write(json.dumps({'pid':os.getpid(),'period':key,'profile':profile}))
            stream.flush();os.fsync(stream.fileno())
            yield
    finally: target.unlink()


def period_qa(payload, markdown):
    quality=payload.get('coverage') or payload.get('input_quality') or {}
    issues=[]
    if not markdown.startswith('# ') or not quality.get('authority_state'):
        issues.append('missing_report_or_input_authority')
    if not isinstance(payload.get('publication_event_views'),dict):
        issues.append('missing_publication_event_views')
    if quality.get('semantic_failed_days') or quality.get('semantic_unknown_days'):
        if quality.get('authority_state') not in ('PARTIAL_VERIFY_FIRST','INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'):
            issues.append('input_failure_authority_upgrade')
    return {'status':'FAIL' if issues else 'PASS','issues':issues,
            'source_coverage_status':quality.get('authority_state','UNKNOWN')}


def verify_period_pair(json_path, markdown_path):
    payload=json.loads(Path(json_path).read_text('utf-8'))
    markdown_bytes=Path(markdown_path).read_bytes()
    markdown=markdown_bytes.decode('utf-8')
    meta=payload.get('metadata',{});generation=meta.get('generation_id')
    if not generation or '<!-- generation:'+generation+' -->' not in markdown:
        raise ValueError('period generation mismatch')
    if hashlib.sha256(markdown_bytes).hexdigest()!=meta.get('markdown_sha256'):
        raise ValueError('period Markdown hash mismatch')
    saved=meta.pop('payload_content_sha256',None)
    actual=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if saved!=actual:raise ValueError('period structured payload hash mismatch')
    qa=period_qa(payload,markdown)
    if qa['status']!='PASS':raise ValueError('period QA failed: '+json.dumps(qa))
    return qa


def publish_period(payload, paths, writer):
    with tempfile.TemporaryDirectory(prefix='period-preview-') as directory:
        base=Path(directory)
        j,m=writer(payload,base/'data',base/'digests')
        markdown=m.read_text('utf-8')
        qa=period_qa(payload,markdown)
        if qa['status']!='PASS':raise ValueError('period QA failed: '+json.dumps(qa))
        materialized=json.loads(j.read_text('utf-8'))
        generation=uuid4().hex;markdown+='\n<!-- generation:'+generation+' -->\n'
        materialized.setdefault('metadata',{}).update(generation_id=generation,
            markdown_sha256=hashlib.sha256(markdown.encode()).hexdigest(),
            structural_qa={'status':'PASS'},semantic_qa=qa,publication_state='QA_PASSED')
        materialized['metadata']['payload_content_sha256']=hashlib.sha256(
            json.dumps(materialized,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        targets=[paths.digest_root/m.relative_to(base/'digests'),paths.data_root/j.relative_to(base/'data')]
        contents=[markdown.encode(),json.dumps(materialized,ensure_ascii=False,indent=2).encode()]
        if any(p.exists() for p in targets):raise ValueError('existing period pair/orphan; overwrite forbidden')
        created=[]
        try:
            for target,content in zip(targets,contents):
                target.parent.mkdir(parents=True,exist_ok=True)
                # Same-volume complete staging then atomic no-clobber link.
                staged=None
                try:
                    with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.staged-',delete=False) as f:
                        staged=Path(f.name);f.write(content);f.flush();os.fsync(f.fileno())
                    os.link(staged,target);created.append(target)
                finally:
                    if staged is not None:staged.unlink(missing_ok=True)
            verify_period_pair(targets[1],targets[0])
        except (OSError,ValueError):
            for target in created:target.unlink(missing_ok=True)
            raise
        return targets[1],targets[0]
