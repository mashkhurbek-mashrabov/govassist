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

## Offices (seed: `backend/apps/collector/fixtures/directory_sources.json`)

Both sites are **third-party commercial business directories, not official sources**. Every
office they yield lands as `pending` (and `needs_review` on a fuzzy district match), and the
author approves it in the admin. Scraped pages stay on the worker's data volume and in the
database; none are committed to this repository.

| Site | Publisher | robots.txt (checked 2026-10-22) | Terms of use | What is stored |
|---|---|---|---|---|
| https://www.goldenpages.uz/uz/ | GoldenPages (goldenpages.uz) | Present. `*` group disallows among others `*.html`, `*/search/*`, `*/maps/*`, `*/rubplaces/*`, `*/mapcompany/*`, `*&region=*`, `*?Print`, `*&tab=*`, `*/sm/*`, `*/person/*`. `/uz/rubrics/?Id=N`, `&Page=N` and `/uz/company/?Id=N` are allowed. Wildcard rules are matched per RFC 9309 (`apps/collector/robots.py`) | No terms-of-use page found on the homepage | From the page's schema.org `LocalBusiness` JSON-LD: name, street address (region and district parsed from it, or the district from the name), coordinates; working hours and lunch from the schedule table; the page's "Yangilangan" date as `data_as_of`. **Phone: not stored** (masked on the page behind "Show phone number"; no reveal endpoint is called, and the unmasked FAQ JSON-LD is not used) |
| https://www.yellowpages.uz/uz/ | Yellow Pages Uzbekistan (yellowpages.uz) | Present. Disallows `*?key=`, `*pagesize=`, `/user/`, `/account/`, `/norma/`, `/content/`, `/data/`; sitemap at `/sitemap.xml`. `/uz/rubrika/…` and `/uz/korxona/…` are allowed | No terms-of-use page found on the homepage (a privacy policy exists at `/uz/privacy/privacy-policy-2`) | Second source / cross-check: name, address, coordinates from `LocalBusiness` JSON-LD. No hours (not structured), **no phone** (same rule). Its addresses sometimes label Tashkent city "Toshkent viloyati"; the district settles the region. Duplicates of goldenpages offices (same type and district, and the same address, name or a spot within 150 m) are skipped. Only the first page of each listing (15 entries) is read: further pages load through a JavaScript API, which is not called |

Rubrics crawled (scope: Tashkent city + Samarqand viloyati):

| Office type | goldenpages rubric (`/uz/rubrics/?Id=`) | Region scope | Name filter | yellowpages (`/uz/rubrika/…`) |
|---|---|---|---|---|
| public_service_center | 106916 (Toshkent), 106925 (Samarqand) | per rubric | — | `davlat-xizmatlari-markazlari/toshkent` (`DAVLAT XIZMAT`) |
| tax | 108884 (Toshkent), 108891 (Samarqand) | per rubric | `SOLIQ` | `soliq-inspeksiyasi/toshkent` |
| civil_registry | 3689 (Toshkent), 3691 (Samarqand): FHDYo offices, not wedding venues | per rubric | `F[HX]DYO\|ZAGS` | — |
| khokimiyat | 3654 (Toshkent), 108844 (Samarqand viloyati) | per rubric | `HOKIMIYAT` | `hokimiyatlar/toshkent` |
| migration | 1063 (OVIR / migratsiya, nationwide) | Toshkent shahri, Samarqand viloyati | `MIGRATSIYA\|PASPORT\|CHET ELGA CHIQISH\|KIRIB CHIQ` (old OVIR names too) | `pasport-bolimlari/toshkent` |
| cadastre | 1893 (nationwide; also lists private firms) | Toshkent shahri, Samarqand viloyati | `KADASTR` | `kadastr/toshkent` |
| notary | not found on robots-allowed rubric pages (`/search/` is disallowed) | — | — | — |

Fetched first on 2026-10-22 (rubric and company pages sampled by hand at 1 request/1.5 s to
design the parsers); each crawl's fetch time is stored per page (`RawPage.fetched_at`) and per
office (`data_as_of` = the page's own date, else the fetch date).
