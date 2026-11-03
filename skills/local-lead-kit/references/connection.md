# Connection

The local app uses the Apify API with each user's own account. Configure `APIFY_TOKEN` securely in the environment used to start the app, or in an explicitly selected private environment file (owner-readable only). No key is bundled, sent to a publisher service, or collected through the campaign form.

Ask the assistant to prepare an empty private file, add the value yourself outside chat, and launch with `--env-file`. Keep the token out of recordings. Use Apify's [API and integrations settings](https://console.apify.com/settings/integrations) and [authentication documentation](https://docs.apify.com/platform/integrations/api). A separate MCP OAuth connection cannot be assumed to supply the app's environment variable.

The app uses HTTPS with certificate verification. It rejects redirects on authenticated API requests. It binds only to loopback and requires a private browser session plus same-origin controls. The single-use browser launch link expires after five minutes. Runtime access information and campaign data live in the private workspace, not in the installed plugin source.
