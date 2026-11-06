# Apify integration safeguards

Reviewed against Apify's published documentation on 7 November 2026. These are implemented controls and usage instructions. They do not establish legal certification, endorsement, source rights or marketplace acceptance.

## Connection and identity

Looksy Agent is an independent research workflow project by Khadin Akbar Labs. Its remote setup uses Apify's official hosted MCP server and OAuth. The user signs in with their own Apify account. Looksy's publisher does not operate the hosted sign-in or receive its tokens. The local plugin also supports a user-supplied key kept in private device configuration.

Looksy's catalog selects Actors published under `khadinakbar`. This is the project's scope, not a platform-wide restriction on other creators. The remote URL's tool list selects available tools. Generic helpers and the user's account permissions can allow broader access. The assistant must keep each action within the requested workflow. [Apify MCP documentation](https://docs.apify.com/mcp)

## Before execution

Inspect the selected Actor's current identity, public availability, permission level, published build, complete input schema and pricing. The local execution paths require verified limited permissions for the Actor and exact build. Missing or unsupported metadata stops execution. A full-permission Actor excluded by Apify's MCP must not be run through a local fallback to circumvent that exclusion.

For local MCP runs, the first request returns a preview. Approval binds the selected account, input, build, run options and pricing metadata. A final metadata check immediately before dispatch rejects drift. A separately requested new collection uses a new `request_id` label and approval. Confirm scope and costs before passing the approval token. Retries of that plan reuse its existing run. Unconfirmed starts remain held for inspection. Remote calls use Apify's tools and require the same user review, with limits supplied in `callOptions` according to the actual tool schema. [Apify MCP tool reference](https://docs.apify.com/mcp)

## Charges and outcomes

The event cap applies to one PPE run. Additional platform usage depends on the current pricing contract. Include startup events, minimum caps, account-tier prices and chargeable empty/error behavior in the review. Unknown prices or usage remain unknown. Runtime observations are provisional, including after a terminal status. Use the user's Apify billing records for final reconciliation. [Apify PPE documentation](https://docs.apify.com/actors/monetize/pay-per-event)

A successful status does not establish useful output. Inspect dataset rows and available OUTPUT or RUN_SUMMARY evidence. An empty dataset alone does not explain why it is empty. Preserve useful partial data and report missing coverage. Read the same run after an interrupted response before considering new collection. [Apify run API](https://docs.apify.com/api/v2/actor-run-get)

## Source access and Store integrity

Use authorized sources and respect source terms, privacy requirements, access controls and applicable data-use rules. Public availability alone does not establish permission for every downstream use. Contact enrichment does not establish consent to outreach. [Apify acceptable use policy](https://docs.apify.com/legal/acceptable-use-policy)

Looksy workflows must not manufacture reviews, accounts, usage or success metrics. Tests need a genuine engineering purpose and bounded scope. Preserve failed-run evidence. Avoid duplicate keyword listings or task pages and misleading pricing claims. Store content must follow Apify's restrictions on external products and promotion. This GitHub integration guide is not an Actor Store README template. [Apify Store Publishing Terms](https://docs.apify.com/legal/store-publishing-terms-and-conditions)

## Review boundaries

This release updates the plugin and its GitHub materials. Technical checks cover the controls documented in the validation record. Actor implementations, every source's legal permissions and public connector-directory acceptance each require their own review. The hosted endpoint and sign-in remain subject to Apify's policies. [Validation](validation.md) · [Privacy](../PRIVACY.md)
