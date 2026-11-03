"""Build isolated native archives from an explicit public-source allowlist."""
from pathlib import Path
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PUBLIC_FILES=['README.md','LICENSE','PRIVACY.md','SECURITY.md','TERMS.md','SUPPORT.md','.env.example']
PUBLIC_DIRS=['local_lead_kit','skills','docs']

def public_paths():
    paths=[ROOT/name for name in PUBLIC_FILES]
    for name in PUBLIC_DIRS:
        paths.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    return sorted(paths)

def main():
    output=ROOT/'dist';output.mkdir(exist_ok=True)
    receipts=[]
    for host,manifest in [('codex','.codex-plugin/plugin.json'),('claude','.claude-plugin/plugin.json')]:
        version=json.loads((ROOT/manifest).read_text())['version'];target=output/f'local-lead-kit-{host}-{version}.zip'
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
            for path in public_paths()+[ROOT/manifest]:archive.write(path,path.relative_to(ROOT))
        receipts.append({'file':target.name,'bytes':target.stat().st_size,'host':host})
    (output/'archives.json').write_text(json.dumps(receipts,indent=2))
    print(json.dumps(receipts,indent=2))

if __name__=='__main__':main()
