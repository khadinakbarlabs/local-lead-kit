# Privacy

Looksy runs on your device. It has no publisher-hosted data service, analytics, telemetry or automatic outreach.

Your niche, territories and approved limits are sent to the configured Apify Actors when you approve collection. Business website URLs go to the contact extractor; extracted addresses go to the validator. Apify processes and bills these requests under your own account and its policies.

The app reads `APIFY_TOKEN` from a configured environment, the owner-readable file created by the connect command, or an explicitly selected private file. It sends the token in an HTTPS authorization header to Apify, never in a request URL, campaign form, export or repository. The local browser uses a separate private session and same-origin controls. A launch link is sensitive and expires after use.

Campaign inputs, results, source context, run IDs, allowance reservations and optional notes are saved in the private local workspace. They remain until you deliberately remove that workspace. Closing the app does not delete results or stop a cloud run that already started. Keep workspace files out of shared repositories.

Optional AI review uses the active assistant you selected. The assistant may process the bounded business sample, your offer and permitted source pages under that host's settings and policies. No additional model API service is hidden in this app. Without an active capable assistant, AI review stays pending.

CSV exports can contain business contact details and source URLs. Review them before sharing. Do not post real contact datasets, runtime access files, launch links or credentials in GitHub issues. Source code and synthetic tests are public; your live workspace is not uploaded by the app.

For other toolbox tasks, discovery searches the bundled catalog locally. A live preview sends read-only metadata requests; exact Actor inputs (such as a domain, keywords or writing sample) go to that Actor only on an approved start. Private plan and result files may contain the full input and output. Use only material you are authorized to share with the selected Actor and its providers.
