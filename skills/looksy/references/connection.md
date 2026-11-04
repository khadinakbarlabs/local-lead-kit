# Installed dashboard

Use the dashboard for onboarding, connection settings and history. Research is led by the user's current AI assistant. Credentials belong in the private dashboard and never in conversation, source control, command arguments, recorded launch links or reports.

## Open the dashboard

Locate this skill's bundled scripts/launch.py and run it with the dashboard subcommand in the local environment. Keep the server running while the user uses it. Open the printed single-use local link privately in their browser. For a complete repository clone, the equivalent is:

```sh
python3 -m looksy dashboard --port 8765
```

Use an available loopback port if the default is occupied. The link expires and can be used once. Never embed the ticket in a public artifact. An assistant that cannot open a browser can give the owner the quoted installed command to run in their own terminal.

1. The required Apify step checks the supplied key via the authenticated account endpoint before saving it. When APIFY_TOKEN or an explicit --env-file supplies a key, verify that key. On macOS/Linux a previous owner-only apify.env file can also be verified. On Windows use the dashboard or APIFY_TOKEN; Looksy uses current-user DPAPI for locally saved settings and does not import plaintext key files. Replace an environment-supplied key in its original environment, then relaunch.
2. Choose **Use current assistant** to finish without a provider key, or select Claude (Anthropic), OpenRouter, OpenAI or Gemini and save the corresponding key. Provider setup stores the credential locally. It does not call a model.
3. Use **Settings** to update a connection or remove the optional provider. **History** lists saved briefs in the workspace's toolbox folder and recent campaigns. Hand the brief ID back to the assistant to reopen it. Local Leads remains available through the dashboard or the launcher's `serve --leads` option. A validated campaign draft also selects the Local Leads destination after onboarding.

The dashboard stores connection settings in the user's private Looksy configuration directory. Existing install names, brief IDs and campaign data remain usable. Browsing the public guide and task directory needs no key.

## Optional direct AI request

Default research and review use the active assistant. Only use a direct provider when the user specifically requests it and approves the selected provider, model, content and possible account charges. Saving a key alone does not authorize sending research or making a billed call. Prepare a small private UTF-8 prompt file containing only approved content. The installed helper accepts:

```sh
python3 "<skill-dir>/scripts/toolbox.py" ask-provider --provider <provider> --model <model-id> --prompt-file <approved-file> --confirm-send <same-provider>
```

The supported provider IDs are anthropic, openrouter, openai and gemini. The helper requires the selected provider's saved key, limits prompt size and sends one request. Treat the reply as model output and review its claims against research evidence. A failed or uncertain call should not be automatically repeated.
