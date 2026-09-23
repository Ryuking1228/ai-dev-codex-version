# Dependency decisions

Registry verification and compatibility checks for this starter. Container execution is pending.

| Dependency | Chosen | Registry latest stable | Release / tag update | Source |
|---|---|---|---|---|
| react | 19.3.0 | 19.3.0 | 2026-09-09T17:21:30.071Z | [registry](https://registry.npmjs.org/react) |
| react-dom | 19.3.0 | 19.3.0 | 2026-09-09T17:17:39.744Z | [registry](https://registry.npmjs.org/react-dom) |
| @types/react | 19.3.0 | 19.3.0 | 2026-09-09T18:08:49.750Z | [registry](https://registry.npmjs.org/@types/react) |
| @types/react-dom | 19.3.0 | 19.3.0 | 2026-09-09T18:07:51.886Z | [registry](https://registry.npmjs.org/@types/react-dom) |
| typescript | 7.0.2 | 7.0.2 | 2026-07-08T15:55:18.431Z | [registry](https://registry.npmjs.org/typescript) |
| vite | 8.3.0 | 8.3.0 | 2026-09-10T11:30:26.283Z | [registry](https://registry.npmjs.org/vite) |
| @playwright/test | 1.63.0 | 1.63.0 | 2026-09-04T22:44:00.304Z | [registry](https://registry.npmjs.org/@playwright/test) |
| fastapi | 0.141.1 | 0.141.1 | 2026-07-29T17:18:04.364385Z | [registry](https://pypi.org/pypi/fastapi/json) |
| uvicorn | 0.53.0 | 0.53.0 | 2026-09-14T07:44:22.179111Z | [registry](https://pypi.org/pypi/uvicorn/json) |
| psycopg[binary] | 3.3.6 | 3.3.6 | 2026-09-18T13:15:29.374570Z | [registry](https://pypi.org/pypi/psycopg/json) |
| pytest | 9.1.1 | 9.1.1 | 2026-06-19T10:58:31.347074Z | [registry](https://pypi.org/pypi/pytest/json) |
| httpx | 0.28.1 | 0.28.1 | 2024-12-06T15:37:21.509172Z | [registry](https://pypi.org/pypi/httpx/json) |
| postgres | 18-alpine | Line selected; latest not claimed | 2026-09-21T01:08:20.384039Z | [registry](https://hub.docker.com/v2/repositories/library/postgres/tags/18-alpine) |
| python | 3.13-slim | Line selected; latest not claimed | 2026-09-19T08:10:14.093137Z | [registry](https://hub.docker.com/v2/repositories/library/python/tags/3.13-slim) |
| node | 24-alpine | Line selected; latest not claimed | 2026-09-18T02:39:03.984945Z | [registry](https://hub.docker.com/v2/repositories/library/node/tags/24-alpine) |
| node | 24-bookworm | Line selected; latest not claimed | 2026-09-19T14:38:58.172788Z | [registry](https://hub.docker.com/v2/repositories/library/node/tags/24-bookworm) |
| actions/checkout | v4 | Line selected; latest not claimed | Not queried | [registry](https://api.github.com/repos/actions/checkout/git/ref/tags/v4) |
| actions/upload-artifact | v4 | Line selected; latest not claimed | Not queried | [registry](https://api.github.com/repos/actions/upload-artifact/git/ref/tags/v4) |

Exact records and image digests: `version-decisions.json`. Docker tags select supported runtime lines and can move to later patches. npm uses a committed lockfile; Python direct requirements are pinned, while transitive requirements are not fully locked.
