"""Apply inspectable font-specific development parameters from a knowledge pack."""
import json,hashlib,pathlib
def load_policy(pack,font_path):
    policy={'minimum_footer_gap_pt':10.8,'native_width_scale':1.06}
    path=pathlib.Path(pack)/'layout-policy.json'
    if not path.exists():return policy,{'status':'runtime-default','pack_policy':False}
    data=json.loads(path.read_text())
    if data.get('contract')!='io.clayz.presentation.layout-policy/1.0':raise ValueError('Unsupported knowledge layout policy')
    if data.get('font_sha256')!=hashlib.sha256(pathlib.Path(font_path).read_bytes()).hexdigest():raise ValueError('Knowledge calibration is for another font file')
    for key in policy:
        value=data.get(key)
        if not isinstance(value,(float,int)) or isinstance(value,bool):raise ValueError('Knowledge parameter must be numeric: '+key)
        policy[key]=value
    if not 8<=policy['minimum_footer_gap_pt']<=36 or not 1<=policy['native_width_scale']<=1.2:raise ValueError('Knowledge policy outside supported measured range')
    return policy,{'status':'applied','path':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'parameters':policy,'limitation':'STKaiti/LibreOffice development observations, not a universal font or aesthetic model.'}
