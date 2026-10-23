# Corpus sources

Every source the backend seeds, crawls or indexes. Add a row **before** crawling a new source.
Crawling rules: robots.txt respected, at most 1 request/second per host, User-Agent
`GovAssist-research/1.0 (+https://github.com/mashkhurbek-mashrabov/govassist)`.

## Reference data

| Data | URL | Publisher | Terms / status | Fetched | Notes |
|---|---|---|---|---|---|
| SOATO classifier (regions, districts, cities) | https://stat.uz/images/soato-20_04_2022.xlsx | Statistics Agency under the President of the Republic of Uzbekistan (stat.uz) | Official classifier, approved by order of the State Committee on Statistics No. 59 of 22.07.2020; linked from https://stat.uz/ru/2020-05-11-05-05-43/statisticheskie-klassifikatory. robots.txt allows `/images/` | 2026-10-22 | sha256 `9d1b0c84fdef45f5b49f1c312037d64c7ec85a0f4bbfdc979115b1f4c6cafcc1`. File dated 20.04.2022: units created later are missing. Converted verbatim to `backend/apps/geo/fixtures/soato.json` (14 regions, 206 districts/cities; group-header rows skipped). The file has no English names, so `name_en` falls back to the official Latin name |

## Sample documents (seed: `backend/apps/collector/fixtures/sample_sources.json`)

One page each, no link following (`max_pages=1`). Service IDs come from my.gov.uz's own
listing pages (`/uz/sitemap`, `/uz/spheres/N`); lex.uz IDs were checked against each
page's official title. Not found on any robots-allowed listing, so not added (IDs are never
guessed): divorce and the driving licence; links from the author are welcome. lex.uz has no
robots.txt, so it is crawled at 1 request/2 s.

| Name | URL | Publisher | Kind | robots.txt | Terms of use | Fetched |
|---|---|---|---|---|---|---|
| ID karta olish yoki almashtirish uchun ariza yuborish (service #378) | https://my.gov.uz/uz/service/378 | my.gov.uz (Unified Portal of Interactive Public Services) | service_page | Allowed (`/uz/service/*` is not disallowed) | https://my.gov.uz/uz/static/terms-of-use: no clause on reuse; forbids unjustified load on the system | 2026-10-22 |
| Xorijga chiqish pasportini rasmiylashtirish (service #418) | https://my.gov.uz/uz/service/418 | my.gov.uz | service_page | Allowed | as above | 2026-10-22 |
| Nikohni qayd etish (service #133) | https://my.gov.uz/uz/service/133 | my.gov.uz | service_page | Allowed | as above | 2026-10-22 |
| Tugʻilganlik haqidagi guvohnomani olish (service #913) | https://my.gov.uz/uz/service/913 | my.gov.uz | service_page | Allowed | as above | 2026-10-22 |
| Tugʻilganlik haqida takroriy guvohnoma (service #865) | https://my.gov.uz/uz/service/865 | my.gov.uz | service_page | Allowed | as above | 2026-10-22 |
| VM 129-son, 06.03.2020: ID-kartalarini rasmiylashtirish va berish tizimini joriy etish chora-tadbirlari toʻgʻrisida | https://lex.uz/uz/docs/-4756929 | lex.uz (National Database of Legislation) | law | No robots.txt (404) | No terms page found; public official legal texts | 2026-10-22 |
| Oʻzbekiston Respublikasining Oila kodeksi, 30.04.1998 | https://lex.uz/uz/docs/-104720 | lex.uz | law | No robots.txt (404) | as above | 2026-10-22 |
| Yashash joyi bo‘yicha ro‘yxatdan o‘tkazish (service #363) | https://my.gov.uz/uz/service/363 | my.gov.uz | service_page | Allowed (`/uz/service/*`; only `/kaa` and `/en` service pages are disallowed) | as above | 2026-10-23 |
| Turar-joy kadastr pasportini shakllantirish va davlat ro‘yxatidan o‘tkazish (service #939) | https://my.gov.uz/uz/service/939 | my.gov.uz | service_page | Allowed (`/uz/service/*`; only `/kaa` and `/en` service pages are disallowed) | as above | 2026-10-23 |
| Biznesni ro'yxatdan o'tkazish (service #57) | https://my.gov.uz/uz/service/57 | my.gov.uz | service_page | Allowed (`/uz/service/*`; only `/kaa` and `/en` service pages are disallowed) | as above | 2026-10-23 |
| Bolalar nafaqasi yoki moddiy yordam tayinlash (service #1017) | https://my.gov.uz/uz/service/1017 | my.gov.uz | service_page | Allowed (`/uz/service/*`; only `/kaa` and `/en` service pages are disallowed) | as above | 2026-10-23 |
| Jamg‘arib boriladigan pensiya tizimiga hisobga qo‘yish (service #177) | https://my.gov.uz/uz/service/177 | my.gov.uz | service_page | Allowed (`/uz/service/*`; only `/kaa` and `/en` service pages are disallowed) | as above | 2026-10-23 |
| Elektr tarmoqlariga ulanish uchun texnik shart, 20 kVtgacha (service #172) | https://my.gov.uz/uz/service/172 | my.gov.uz | service_page | Allowed (`/uz/service/*`; only `/kaa` and `/en` service pages are disallowed) | as above | 2026-10-23 |
| Gaz tarmoqlariga ulanish uchun texnik shartlarni olish, 1,2 MPa bosimgacha (service #173) | https://my.gov.uz/uz/service/173 | my.gov.uz | service_page | Allowed (`/uz/service/*`; only `/kaa` and `/en` service pages are disallowed) | as above | 2026-10-23 |
| Oʻzbekiston Respublikasining Mehnat kodeksi, 28.10.2022 | https://lex.uz/uz/docs/-6257288 | lex.uz | law | No robots.txt (404) | No terms page found; public official legal texts | 2026-10-23 |
| Oʻzbekiston Respublikasining Fuqarolik kodeksi (birinchi qism), 21.12.1995 | https://lex.uz/uz/docs/-111189 | lex.uz | law | No robots.txt (404) | as above | 2026-10-23 |
| Oʻzbekiston Respublikasining Fuqarolik kodeksi (ikkinchi qism), 29.08.1996 | https://lex.uz/uz/docs/-180552 | lex.uz | law | No robots.txt (404) | as above | 2026-10-23 |
| Oʻzbekiston Respublikasining Maʼmuriy javobgarlik toʻgʻrisidagi kodeksi, 22.09.1994 | https://lex.uz/uz/docs/-97664 | lex.uz | law | No robots.txt (404) | as above | 2026-10-23 |
| “Jismoniy va yuridik shaxslarning murojaatlari toʻgʻrisida” Qonun, new edition (O‘RQ-445, 11.09.2017; the page carries the full law, articles 1 onward) | https://lex.uz/uz/docs/-3336169 | lex.uz | law | No robots.txt (404) | as above | 2026-10-23 |

## Offices (seed: `backend/apps/collector/fixtures/directory_sources.json`)

**Phones (author decision 2026-10-23):** a phone is stored only when the page publishes it in
its own structured data, in HTML we already received: yellowpages' LocalBusiness `telephone`,
and goldenpages' FAQ JSON-LD answer to "phone number?" (read from the saved pages only,
`manage backfill_phones`; no new request). No "show phone" click, script or reveal endpoint is
ever used. Numbers are stored as `+998XXXXXXXXX` (only the country code is added); short
numbers such as `1148` alone are not stored.

Both sites are **third-party commercial business directories, not official sources**. Every
office they yield lands as `pending` (and `needs_review` on a fuzzy district match), and the
author approves it in the admin. Scraped pages stay on the worker's data volume and in the
database; none are committed to this repository.

| Site | Publisher | robots.txt (checked 2026-10-22) | Terms of use | What is stored |
|---|---|---|---|---|
| https://www.goldenpages.uz/uz/ | GoldenPages (goldenpages.uz) | Present. `*` group disallows among others `*.html`, `*/search/*`, `*/maps/*`, `*/rubplaces/*`, `*/mapcompany/*`, `*&region=*`, `*?Print`, `*&tab=*`, `*/sm/*`, `*/person/*`. `/uz/rubrics/?Id=N`, `&Page=N` and `/uz/company/?Id=N` are allowed. Wildcard rules are matched per RFC 9309 (`apps/collector/robots.py`) | No terms-of-use page found on the homepage | From the page's schema.org `LocalBusiness` JSON-LD: name, street address (region and district parsed from it, or the district from the name), coordinates; working hours and lunch from the schedule table; the page's "Yangilangan" date as `data_as_of`. **Phone:** the visible number is masked behind "Show phone number" and no reveal is used; since 2026-10-23 the number from the page's own FAQ JSON-LD is stored, read from the saved pages only |
| https://www.yellowpages.uz/uz/ | Yellow Pages Uzbekistan (yellowpages.uz) | Present. Disallows `*?key=`, `*pagesize=`, `/user/`, `/account/`, `/norma/`, `/content/`, `/data/`; sitemap at `/sitemap.xml`. `/uz/rubrika/…` and `/uz/korxona/…` are allowed | No terms-of-use page found on the homepage (a privacy policy exists at `/uz/privacy/privacy-policy-2`) | Second source / cross-check: name, address, coordinates from `LocalBusiness` JSON-LD. No hours (not structured), the phone from its LocalBusiness `telephone` (published in the page HTML). Its addresses sometimes label Tashkent city "Toshkent viloyati"; the district settles the region. Duplicates of goldenpages offices (same type and district, and the same address, name or a spot within 150 m) are skipped. Only the first page of each listing (15 entries) is read: further pages load through a JavaScript API, which is not called |

**goldenpages.uz blocked automated access; it is no longer crawled.**

| Date (UTC) | Status | What happened |
|---|---|---|
| 2026-10-22 13:26 | HTTP 403 | After about 45 requests that day (about 30 of them hand sampling at 1 request/1.5 s, then a crawl at 1 request/s), four company pages and then the listing itself answered 403. Crawling stopped. |
| 2026-10-22 15:14 | HTTP 200 | One probe after a pause of almost 2 hours; crawling resumed at 1 request/10 s. |
| 2026-10-23 04:42 | HTTP 403 | Blocked automated access again during the Samarqand tax rubric, after the Samarqand khokimiyat rubric (18 pages) at 1 request/10 s. The job stopped at the first 403 (`HostBlockedError`). |

goldenpages is not retried: no other User-Agent, headers, IP, proxy, browser or session is
used to get around the block. Offices already stored from it stay pending for review. What it
did not yield (tax in Samarqand, FHDYo, migration, cadastre in Samarqand) needs another
source, preferably an official one.

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
