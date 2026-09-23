# __APP_NAME__

This is an example vertical slice. Replace this brief with the intended product before expanding it.

- Actor: one local user. No end-user authentication has been implemented.
- Goal: create, reload and delete a text item, persisted in PostgreSQL.
- Acceptance: 1–120 non-blank characters; trim surrounding whitespace; preserve across reloads;
  delete only the selected item; report unavailable API; fit a 375px-wide display.
- API: GET /api/health; GET /api/items; POST /api/items (201); DELETE /api/items/{id} (204/404).
  Invalid input returns 422 Problem Details. `/openapi.json` describes request/response schemas.
- Before external deployment: decide public vs authenticated access, implement that decision,
  define data retention/backup and configure the target. Local Docker publishing binds to loopback.
