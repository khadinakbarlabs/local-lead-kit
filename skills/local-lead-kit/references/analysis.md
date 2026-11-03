# AI review contract

The app supplies a bounded list to the active Codex/Claude assistant. The model may assess relevance to the stated offer, identify missing evidence and recommend a specific research step. Use the existing business IDs and public website or Maps URLs supplied with each business. Sources in a note must support what it actually says.

Example using a synthetic business:

```json
[
  {
    "business_id": "example-business-id",
    "note": "The saved directory record matches the selected category and territory. A website is listed, but no website problem or buying intent has been verified.",
    "confidence": "low",
    "sources": ["https://example.org"],
    "next_step": "Inspect the public website for a specific issue relevant to the offer before prioritising this company."
  }
]
```

Do not equate low review counts, missing emails, basic email validity or a listed website with a service need. Do not fabricate current observations from an old dataset. Name the saved-data basis when no fresh site inspection was performed. Report a partial review honestly. The app validates attribution and fields; it cannot independently verify the semantic truth of a model's claim.
