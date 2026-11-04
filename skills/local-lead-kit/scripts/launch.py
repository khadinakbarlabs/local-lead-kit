"""Run the app bundled with this installed skill; no global installation hooks."""
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[3]
if not (root/'local_lead_kit').is_dir():
    raise SystemExit('The complete Looksy package is required. Reinstall the full repository or native plugin archive.')
sys.path.insert(0,str(root))
from local_lead_kit.__main__ import main

if __name__=='__main__':main()
