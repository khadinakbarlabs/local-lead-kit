# Security

Run this app on a trusted local device. It binds to loopback only and is not an internet-facing multi-tenant service. Do not expose its port through a public proxy.

API reads require the authenticated browser session and a random local request key. Mutations also require the exact local Origin; the server checks Host, disables permissive CORS and sets a restrictive content policy. Private runtime files use owner-only permissions. The single-use browser launch link is not the Apify API token, but still grants access to the local session and must remain private.

The API client uses a fixed HTTPS origin, certificate verification and no authenticated redirects. Actor identities are allowlisted. Every paid start has an approved plan, reserved allowance, build, timeout and charge control. An uncertain start is held for inspection rather than retried. These controls do not verify every claim made by an external Actor or AI model.

Source text is treated as data, escaped in the UI, and protected against spreadsheet formulas in CSV output. The app rejects credential-bearing and literal local/private source URLs. It does not control the remote Actor's networking or every redirect a public website may perform; use sources you are permitted to process.

Report a problem through the repository's security reporting feature if available. Otherwise open a minimal issue requesting a private contact route, without exploit details, keys, runtime access files or real contact data. Include the package version and a synthetic reproduction when possible.
