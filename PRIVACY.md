# Privacy

Looksy runs on your device. It has no publisher-hosted data service, analytics, telemetry or automatic outreach.

Your niche, territories and approved limits are sent to the configured Apify Actors when you approve collection. Business website URLs go to the contact extractor; extracted addresses go to the validator. Apify processes and bills these requests under your own account and its policies.

The private dashboard sends keys only to its local loopback server. An Apify key is checked using a read-only account request and is sent to Apify in an HTTPS authorization header. Looksy keeps saved keys on your device. It uses owner-only files on POSIX systems and encrypts saved settings for the current Windows user with DPAPI. They are separate from research files and do not appear in browser storage, HTML, history or status responses. An explicit private environment file or APIFY_TOKEN can supply Apify access instead. A single-use launch ticket establishes the private browser session.

Campaign inputs, results, source context, run IDs, allowance reservations and optional notes are saved in the private local workspace. They remain until you deliberately remove that workspace. Closing the app does not delete results or stop a cloud run that already started. Keep workspace files out of shared repositories.

Research ordinarily uses your active assistant and that host's policies. Saving an optional provider key makes no inference request. An explicitly approved direct provider call sends the selected prompt and model to the chosen provider using its official HTTPS endpoint. The provider may charge for processing and applies its own retention policy. No customer data is automatically attached. Settings can remove the saved provider connection.

CSV exports can contain business contact details and source URLs. Review them before sharing. Do not post real contact datasets, runtime access files, launch links or credentials in GitHub issues. Source code and synthetic tests are public; your live workspace is not uploaded by the app.

For other toolbox tasks, discovery searches the bundled catalog locally. A live preview sends read-only metadata requests; exact Actor inputs (such as a domain, keywords or writing sample) go to that Actor only on an approved start. Private plan and result files may contain the full input and output. Use only material you are authorized to share with the selected Actor and its providers.
