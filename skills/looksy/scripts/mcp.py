"""Start the bundled Looksy MCP server (stdio)."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from looksy.mcp_server import serve

if __name__=='__main__':serve()
