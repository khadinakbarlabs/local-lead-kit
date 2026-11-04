from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from local_lead_kit.toolbox import cli

if __name__=='__main__':cli()
