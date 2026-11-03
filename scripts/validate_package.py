"""Check public metadata, resource closure, version parity and credential patterns."""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from local_lead_kit import __version__
sys.path.insert(0,str(Path(__file__).resolve().parent))
from package_release import public_paths

def main():
    for host in ['codex','claude']:
        manifest=json.loads((ROOT/f'.{host}-plugin/plugin.json').read_text())
        assert manifest['name']=='local-lead-kit' and manifest['version']==__version__
    skill=ROOT/'skills/local-lead-kit/SKILL.md';text=skill.read_text()
    assert text.startswith('---\n') and 'name: local-lead-kit' in text and 'description:' in text
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if not target.startswith(('http:','https:')):assert (skill.parent/target).is_file(),target
    secret=re.compile(r'(sk-(?:proj-)?[A-Za-z0-9_-]{20,}|apify_api_[A-Za-z0-9]{15,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
    files=public_paths()
    for path in files:
        if path.suffix=='.png':continue
        content=path.read_text()
        assert not secret.search(content),'Credential-shaped content in '+str(path.relative_to(ROOT))
        assert '/Users/' not in content and '/private/tmp/' not in content,'Private local path in '+str(path.relative_to(ROOT))
    archives=[]
    for path in sorted((ROOT/'dist').glob('local-lead-kit-*.zip')):
        with zipfile.ZipFile(path) as archive:
            names=archive.namelist()
            assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith(('campaign.json','server-access.json','ledger.json','.env.local')) or '__pycache__' in n or n.startswith('.git/') for n in names)
            host='codex' if '-codex-' in path.name else 'claude';other='claude' if host=='codex' else 'codex'
            assert f'.{host}-plugin/plugin.json' in names and f'.{other}-plugin/plugin.json' not in names
            with tempfile.TemporaryDirectory() as folder:
                archive.extractall(folder)
                result=subprocess.run([sys.executable,str(Path(folder)/'skills/local-lead-kit/scripts/launch.py'),'--help'],capture_output=True,text=True)
                assert result.returncode==0 and 'Local Lead Kit' in result.stdout
                copied=json.loads((Path(folder)/f'.{host}-plugin/plugin.json').read_text());assert copied['version']==__version__
            archives.append(path.name)
    print(json.dumps({'passed':True,'version':__version__,'public_files':len(files),'native_archives_checked':archives,'credentials_or_private_paths':0},indent=2))

if __name__=='__main__':main()
