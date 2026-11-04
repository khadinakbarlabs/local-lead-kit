# Connect Looksy to Apify

When a user asks to connect, give them the exact command for their installed plugin. Resolve the absolute path to this skill’s `scripts/launch.py` and quote it for their shell. The user runs this in their own interactive terminal:

```sh
python3 "<absolute path to the installed skill>/scripts/launch.py" connect
```

For someone working in a full repository clone, the equivalent command from its root is `python3 -m looksy connect`. The hidden prompt saves the key under `~/.config/looksy/apify.env` with owner-only permissions. This step stores the key locally. Apify checks it on the first live request. They can run the same command to replace it or remove that file to forget it. A key already set in the agent’s `APIFY_TOKEN` environment takes precedence.

Get a key in [Apify settings](https://console.apify.com/settings/integrations). Never ask for it in chat, command arguments, or a recording. If an explicitly selected owner-readable file is already available, pass `--env-file <path>` before the toolbox or app command. An Apify MCP login does not automatically supply the separate local credential.

After setup, ask Looksy for a preview. It reads the Actor’s published inputs and current prices. Collection starts only after the user approves the specific run.
