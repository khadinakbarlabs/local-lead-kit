![Looksy. Web research for AI agents.](docs/brand/cover.png)

# Looksy

Ask Claude Code, Codex, or Cursor to find local businesses, research keywords, check search rankings, or see where AI answers cite your website. **Looksy is free to install and browse. Running a task requires your own Apify API key and may incur Apify charges.**

## 1. Install Looksy

Choose the agent you already use. You’ll need Python 3.11 or newer for the bundled tools.

| Agent | Install |
| --- | --- |
| **Claude Code** | In Claude Code, enter `/plugin marketplace add khadinakbarlabs/looksy`, then `/plugin install looksy@looksy-marketplace`. Open a fresh session. |
| **Codex** | In a terminal, run `codex plugin marketplace add khadinakbarlabs/looksy`, then `codex plugin add looksy@looksy-marketplace`. Open a fresh session. |
| **Cursor** | Download [Looksy for Cursor](https://github.com/khadinakbarlabs/looksy/releases/download/v0.3.0/looksy-cursor-0.3.0.zip). Extract the contents into `~/.cursor/plugins/local/looksy/`, with `.cursor-plugin/plugin.json` directly inside. Reload Cursor. |
| **Other local agents** | Download the [portable plugin](https://github.com/khadinakbarlabs/looksy/releases/download/v0.3.0/looksy-portable-0.3.0.zip) and import the complete folder into a compatible Agent Plugins client. |

[Open the interactive Task Guide](https://khadinakbarlabs.github.io/looksy/) to explore category → subcategory → task. Each task has a ready-to-copy request. Task instructions, sources and saved tasks are available without running an Actor.

Try it immediately without a key. Ask **“Use Looksy to show me three tools for keyword research.”**

## 2. Connect Apify once

1. Get your API key from [Apify Settings → API & Integrations](https://console.apify.com/settings/integrations).
2. Ask your agent **“Help me connect Looksy to Apify.”** It will give you a setup command for your own terminal.
3. Run that command, paste the key when prompted, and press Enter. The input is hidden. Return to the agent when you see **Key saved for Looksy**.

Looksy saves the key in a private file on your device. If your agent already has `APIFY_TOKEN` configured, skip this step. Keep the key out of chat.

## 3. Ask for a result

**Try this first:** “Use Looksy to find up to 25 roofing companies in Austin, Texas. Show me what data I’ll get and what it costs before you start.”

Looksy opens **Local Leads** for this request. Review the target, sources and price, then approve the run. When it finishes, inspect the businesses it actually found and download the CSV. Coverage varies by location.

| To do this | Ask Looksy |
| --- | --- |
| Research keywords | “Find US keywords for emergency roof repair. Show me the available search-volume data.” |
| Check search rankings | “Check these five keywords for my domain on US mobile and save a baseline.” |
| Measure AI visibility | “Check whether AI answers mention my brand and which sites they cite.” |
| Improve writing | “Make this introduction sound more natural and preserve its factual claims.” |

## Pick up where you left off

Ask **“Save this as a Looksy brief and include the next step.”** Later, ask **“Reopen my last Looksy brief.”** Another supported agent on the same computer can continue from the same private workspace. For repeat research, ask it to compare two saved observations. Viewing a saved result starts no new run.

[Browse the task hierarchy](docs/tasks.md) · [Browse the Actor directory](docs/directory.md) · [Download the offline Field Guide](https://github.com/khadinakbarlabs/looksy/releases/latest/download/catalog.html) · [Connection help](skills/looksy/references/connection.md)

**Already using the earlier plugin?** Install Looksy under its new name using step 1. Existing local campaigns are picked up automatically from the previous default workspace when no new Looksy workspace exists. An explicitly selected workspace can still be opened with `--workspace`.

[Privacy](PRIVACY.md) · [Support](SUPPORT.md) · [License](LICENSE)
