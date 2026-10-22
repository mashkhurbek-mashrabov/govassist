# Corpus sources

Every source the backend seeds, crawls or indexes. Add a row **before** crawling a new source.
Crawling rules: robots.txt respected, at most 1 request/second per host, User-Agent
`GovAssist-research/1.0 (+https://github.com/mashkhurbek-mashrabov/govassist)`.

## Reference data

| Data | URL | Publisher | Terms / status | Fetched | Notes |
|---|---|---|---|---|---|
| SOATO classifier (regions, districts, cities) | https://stat.uz/images/soato-20_04_2022.xlsx | Statistics Agency under the President of the Republic of Uzbekistan (stat.uz) | Official classifier, approved by order of the State Committee on Statistics No. 59 of 22.07.2020; linked from https://stat.uz/ru/2020-05-11-05-05-43/statisticheskie-klassifikatory. robots.txt allows `/images/` | 2026-10-22 | sha256 `9d1b0c84fdef45f5b49f1c312037d64c7ec85a0f4bbfdc979115b1f4c6cafcc1`. File dated 20.04.2022: units created later are missing. Converted verbatim to `backend/apps/geo/fixtures/soato.json` (14 regions, 206 districts/cities; group-header rows skipped). The file has no English names, so `name_en` falls back to the official Latin name |

## Sample documents (seed: `backend/apps/collector/fixtures/sample_sources.json`)

One page each, no link following (`max_pages=1`).

| Name | URL | Publisher | Kind | robots.txt | Terms of use | Fetched |
|---|---|---|---|---|---|---|
| ID karta olish yoki almashtirish uchun ariza yuborish (service #378) | https://my.gov.uz/uz/service/378 | my.gov.uz (Unified Portal of Interactive Public Services) | service_page | Allowed (`/uz/service/*` is not disallowed) | https://my.gov.uz/uz/static/terms-of-use: no clause on reuse; forbids unjustified load on the system | 2026-10-22 |
| Xorijga chiqish pasportini rasmiylashtirish (service #418) | https://my.gov.uz/uz/service/418 | my.gov.uz | service_page | Allowed | as above | 2026-10-22 |
| Nikohni qayd etish (service #133) | https://my.gov.uz/uz/service/133 | my.gov.uz | service_page | Allowed | as above | 2026-10-22 |
| Tugʻilganlik haqidagi guvohnomani olish (service #913) | https://my.gov.uz/uz/service/913 | my.gov.uz | service_page | Allowed | as above | 2026-10-22 |
| Tugʻilganlik haqida takroriy guvohnoma (service #865) | https://my.gov.uz/uz/service/865 | my.gov.uz | service_page | Allowed | as above | 2026-10-22 |
| VM 129-son, 06.03.2020: ID-kartalarini rasmiylashtirish va berish tizimini joriy etish chora-tadbirlari toʻgʻrisida | https://lex.uz/uz/docs/-4756929 | lex.uz (National Database of Legislation) | law | No robots.txt (404) | No terms page found; public official legal texts | 2026-10-22 |
| Oʻzbekiston Respublikasining Oila kodeksi, 30.04.1998 | https://lex.uz/uz/docs/-104720 | lex.uz | law | No robots.txt (404) | as above | 2026-10-22 |

## Offices

None yet. Office rows come only from a real public directory page (office pipeline + admin
review) or from links the author provides. Until then the office card shows `match: "none"`.
