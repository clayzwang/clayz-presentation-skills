"""Observed visual decisions must be clean and bound to actual final images."""
import pathlib,hashlib
CATEGORIES = ("first_impression", "hierarchy", "comparison", "spacing", "legibility", "content_expression")


def validate(review, slide_ids, render_manifest=None):
    errors = []
    pages = review.get("pages", {})
    bound={r['slide_id']:r for r in (render_manifest or {}).get('slides',[])}
    if render_manifest is not None:
        if set(bound)!=set(slide_ids) or set(pages)!=set(slide_ids):errors.append('final image/page coverage mismatch')
        if review.get('pptx_sha256')!=render_manifest.get('pptx_sha256'):errors.append('visual evidence belongs to a different PPTX')
    for sid in slide_ids:
        for category in CATEGORIES:
            item = pages.get(sid, {}).get(category, {})
            status = item.get("status", "unreviewed")
            if status=='fail':errors.append(f"{sid}.{category}: observed failure requires repair")
            if status not in {"pass", "fail", "not-applicable"}:
                errors.append(f"{sid}.{category}: unreviewed")
            if not item.get("observation", "").strip() or not item.get("evidence", []):
                errors.append(f"{sid}.{category}: needs actual observation and image evidence")
            if category in {"first_impression", "hierarchy", "spacing", "legibility"} and status == "not-applicable":
                errors.append(f"{sid}.{category}: applies to every rendered page")
            if render_manifest is not None:
                expected=bound.get(sid,{})
                for evidence in item.get('evidence',[]):
                    if not isinstance(evidence,dict):errors.append(f'{sid}.{category}: image reference needs path/hash/bytes');continue
                    path=pathlib.Path(evidence.get('path',''))
                    valid=path.is_file() and path.resolve()==pathlib.Path(expected.get('path','')).resolve()
                    if valid:valid=hashlib.sha256(path.read_bytes()).hexdigest()==evidence.get('sha256')==expected.get('sha256') and path.stat().st_size==evidence.get('bytes')==expected.get('bytes')
                    if not valid:errors.append(f'{sid}.{category}: final image identity mismatch')
    return errors
