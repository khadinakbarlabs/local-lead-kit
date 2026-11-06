"""Check public metadata, resource closure, version parity and credential patterns."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from looksy import __version__
sys.path.insert(0,str(Path(__file__).resolve().parent))
from package_release import public_paths, HOSTS, MCP

def main():
    for host in HOSTS:
        manifest=json.loads((ROOT/HOSTS[host]).read_text())
        assert manifest['name']=='looksy' and manifest['version']==__version__
    skill=ROOT/'skills/looksy/SKILL.md';text=skill.read_text()
    assert text.startswith('---\n') and 'name: looksy' in text and 'description:' in text
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
    for host,manifest in HOSTS.items():
        path=ROOT/'dist'/f'looksy-{host}-{__version__}.zip'
        with zipfile.ZipFile(path) as archive:
            names=archive.namelist()
            assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith(('campaign.json','server-access.json','ledger.json','.env.local')) or '__pycache__' in n or n.startswith('.git/') for n in names)
            assert set(names).intersection(HOSTS.values())=={manifest}
            with tempfile.TemporaryDirectory() as folder:
                archive.extractall(folder)
                result=subprocess.run([sys.executable,str(Path(folder)/'skills/looksy/scripts/launch.py'),'--help'],capture_output=True,text=True)
                assert result.returncode==0 and 'Looksy' in result.stdout
                tool=subprocess.run([sys.executable,str(Path(folder)/'skills/looksy/scripts/toolbox.py'),'find','humanizer'],capture_output=True,text=True,check=True)
                assert 'khadinakbar/ai-text-humanizer' in tool.stdout
                areas=subprocess.run([sys.executable,str(Path(folder)/'skills/looksy/scripts/toolbox.py'),'areas'],capture_output=True,text=True,check=True)
                assert len(json.loads(areas.stdout))==36
                workflow=subprocess.run([sys.executable,str(Path(folder)/'skills/looksy/scripts/toolbox.py'),'workflow','Find roofers in Austin'],capture_output=True,text=True,check=True)
                assert json.loads(workflow.stdout)['candidates'][0]['id']=='local-lead-map'
                helper=Path(folder)/'skills/looksy/scripts/toolbox.py'
                environment=dict(os.environ, HOME=folder, USERPROFILE=folder)
                environment.pop('APIFY_TOKEN',None)
                status=subprocess.run([sys.executable,str(helper),'setup-status'],env=environment,capture_output=True,text=True,check=True)
                assert json.loads(status.stdout)==dict(apify_configured=False,apify_verified=False,apify_external=False,ai_provider=None,onboarded=False)
                assert all('looksy/static/dashboard.'+ext in names for ext in ('html','js','css'))
                hello='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"find_tools","arguments":{"job":"google maps leads"}}}\n'
                config = json.loads((Path(folder)/MCP[host]).read_text())['mcpServers']['looksy']
                variables = {'${PLUGIN_ROOT}': folder, '${CLAUDE_PLUGIN_ROOT}': folder, '${CURSOR_PLUGIN_ROOT}': folder}
                def expand(value):
                    for marker, root in variables.items():
                        value = value.replace(marker, root)
                    return value
                args = [expand(arg) for arg in config['args']]
                assert Path(args[0]).is_absolute() and Path(args[0]).is_file()
                assert len(set(names).intersection(MCP.values())) == 1
                # Start from an unrelated directory to catch accidental workspace-relative launchers.
                mcp=subprocess.run([sys.executable,*args],input=hello,env=environment,cwd=Path(folder).parent,capture_output=True,text=True,check=True)
                replies=[json.loads(line) for line in mcp.stdout.splitlines()]
                assert replies[0]['result']['serverInfo']['version']==__version__
                assert replies[1]['result']['structuredContent']['tools'][0]['tool']=='khadinakbar/google-maps-leads-scraper'
                assert MCP[host] in names
                assert not any(Path(name).name in ('connections.json','apify.env','.connections.lock','server-access.json') for name in names)
                copied=json.loads((Path(folder)/manifest).read_text());assert copied['version']==__version__
            archives.append(path.name)
    print(json.dumps({'passed':True,'version':__version__,'public_files':len(files),'native_archives_checked':archives,'credentials_or_private_paths':0},indent=2))

if __name__=='__main__':main()
