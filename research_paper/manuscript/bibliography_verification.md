# Bibliography verification table (27 Nov 2026)

**Revision 3:** `references.bib` is unchanged. The same 33 entries are cited, with the same verification status.
`holm1979` and `iso3166` remain **AUTHOR-CHECK**. The 31 metadata-verified entries have **not** been reviewed at
the content level (questionnaire Q15–Q16).

How each entry in `references.bib` was checked from the drafting session:

- **Crossref:** `https://api.crossref.org/works/<DOI>` returned a record, and the title, authors, venue, year,
  volume, issue and pages in `references.bib` were copied from it.
- **Publisher page:** the publisher's own page (citation meta tags or BibTeX) matched the entry.
- **Page fetched:** the official page loaded and showed the cited title or content.

**Verification covers metadata only.** The drafting session did not read the full text of the cited works. Each
work is cited only for what its title, venue and well-established role support. **Author 3 (literature survey) must
confirm, against the full text, every sentence that cites a work** (`author_review_items.md`, item R1).

| Key | Reference (short) | DOI / URL | Status | How verified | Cited for |
|---|---|---|---|---|---|
| chow1970 | C. K. Chow, IEEE Trans. Inf. Theory 16(1):41–46, 1970 | 10.1109/TIT.1970.1054406 | VERIFIED (metadata) | Crossref | Error–reject trade-off |
| elyaniv2010 | R. El-Yaniv, Y. Wiener, JMLR 11(53):1605–1641, 2010 | https://jmlr.org/papers/v11/el-yaniv10a.html | VERIFIED (metadata) | Publisher page (JMLR citation tags) | Selective classification, risk–coverage |
| geifman2017 | Y. Geifman, R. El-Yaniv, NeurIPS 30, 2017 | proceedings.neurips.cc …/4a8423d5…-Abstract.html | VERIFIED (metadata) | Publisher page (NeurIPS citation tags) | Selective classification |
| kamath2020 | A. Kamath, R. Jia, P. Liang, ACL 2020, 5684–5696 | 10.18653/v1/2020.acl-main.503 | VERIFIED (metadata) | Crossref | Abstention under domain shift |
| xin2021 | J. Xin, R. Tang, Y. Yu, J. Lin, ACL-IJCNLP 2021, 1040–1051 | 10.18653/v1/2021.acl-long.84 | VERIFIED (metadata) | Crossref | Abstention in NLP |
| fellegi1969 | I. P. Fellegi, A. B. Sunter, JASA 64(328):1183–1210, 1969 | 10.1080/01621459.1969.10501049 | VERIFIED (metadata) | Crossref | Record linkage |
| elmagarmid2007 | A. K. Elmagarmid et al., IEEE TKDE 19(1):1–16, 2007 | 10.1109/TKDE.2007.250581 | VERIFIED (metadata) | Crossref | Duplicate detection |
| christen2012 | P. Christen, *Data Matching*, Springer, 2012 | 10.1007/978-3-642-31164-2 | VERIFIED (metadata) | Crossref (title, subtitle, publisher) | Record linkage, entity resolution |
| navarro2001 | G. Navarro, ACM Comput. Surv. 33(1):31–88, 2001 | 10.1145/375360.375365 | VERIFIED (metadata) | Crossref | Approximate string matching |
| damerau1964 | F. J. Damerau, CACM 7(3):171–176, 1964 | 10.1145/363958.363994 | VERIFIED (metadata) | Crossref | Edit operations for typos |
| salton1988 | G. Salton, C. Buckley, IP&M 24(5):513–523, 1988 | 10.1016/0306-4573(88)90021-0 | VERIFIED (metadata) | Crossref | TF-IDF term weighting |
| finkel2006 | J. R. Finkel, C. D. Manning, A. Y. Ng, EMNLP 2006, 618–626 | 10.3115/1610075.1610162 | VERIFIED (metadata) | Crossref (first page) and ACL Anthology BibTeX (pages 618–626) | Cascading errors in pipelines |
| sculley2015 | D. Sculley et al., NeurIPS 28, 2015 | proceedings.neurips.cc …/86df7dcf…-Abstract.html | VERIFIED (metadata) | Publisher page (NeurIPS citation tags, all 10 authors) | Hidden failure modes in ML systems |
| breck2017 | E. Breck et al., IEEE Big Data 2017, 1123–1132 | 10.1109/BigData.2017.8258038 | VERIFIED (metadata) | Crossref | ML production-readiness testing |
| ribeiro2020 | M. T. Ribeiro et al., ACL 2020, 4902–4912 | 10.18653/v1/2020.acl-main.442 | VERIFIED (metadata) | Crossref | Behavioural (perturbation) testing |
| kapoor2023 | S. Kapoor, A. Narayanan, Patterns 4(9):100804, 2023 | 10.1016/j.patter.2023.100804 | VERIFIED (metadata) | Crossref | Leakage |
| ding2015 | L. Ding, Z. Fan, D. Chen, Procedia Comput. Sci. 60:1462–1471, 2015 | 10.1016/j.procs.2015.08.224 | VERIFIED (metadata) | Crossref | Automatic HS-code categorisation |
| koch2025 | T. Koch, K. Power, IEEE HPEC 2025, 1–5 | 10.1109/HPEC67600.2025.11196693 | VERIFIED (metadata); **content not read** | Crossref (no abstract available) | LLM-based HS classification (title-level claim only) |
| wube2026 | H. D. Wube et al., Discover Computing 29(1), art. 505, 2026 | 10.1007/s10791-026-10428-y | VERIFIED (metadata); **content not read** | Crossref (no abstract available) | Review of ML/DL/LLM HS classification (title-level claim only) |
| kim2020date | S. Kim et al., KDD 2020, 2880–2890 | 10.1145/3394486.3403339 | VERIFIED (metadata) | Crossref (title + subtitle) | Customs fraud detection |
| mikuriya2020 | K. Mikuriya, T. Cantens, World Customs Journal 14(2), 2020 | 10.55596/001c.116414 | VERIFIED (metadata) | Crossref | Data mobilisation in customs |
| wooldridge1995 | M. Wooldridge, N. R. Jennings, Knowl. Eng. Rev. 10(2):115–152, 1995 | 10.1017/S0269888900008122 | VERIFIED (metadata) | Crossref | Meaning of "agent" (to say the stages are not agents) |
| field2007 | C. A. Field, A. H. Welsh, JRSS-B 69(3):369–390, 2007 | 10.1111/j.1467-9868.2007.00593.x | VERIFIED (metadata) | Crossref | Cluster bootstrap |
| efron1994 | B. Efron, R. J. Tibshirani, *An Introduction to the Bootstrap*, Chapman and Hall/CRC | 10.1201/9780429246593 | VERIFIED (metadata) | Crossref (gives 1994 for this DOI) | Bootstrap |
| good2005 | P. Good, *Permutation, Parametric and Bootstrap Tests of Hypotheses*, Springer, 2005 | 10.1007/b138696 | VERIFIED (metadata) | Crossref (title, series, publisher, year). The Crossref record has no author field; the author name is from the book's standard citation | Permutation tests |
| holm1979 | S. Holm, Scand. J. Statist. 6(2):65–70, 1979 | https://www.jstor.org/stable/4615733 | **AUTHOR-CHECK** | No Crossref DOI; the JSTOR page blocks automated access ("Client Challenge"). Metadata is the standard citation, not machine-verified | Holm correction |
| mcnemar1947 | Q. McNemar, Psychometrika 12(2):153–157, 1947 | 10.1007/BF02295996 | VERIFIED (metadata) | Crossref | McNemar test |
| wilson1927 | E. B. Wilson, JASA 22(158):209–212, 1927 | 10.1080/01621459.1927.10502953 | VERIFIED (metadata) | Crossref | Wilson interval |
| wcohs2022 | WCO, HS Nomenclature 2022 Edition | https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition.aspx | VERIFIED (page fetched) | Page shows "HS Nomenclature 2022 Edition", effective 1 January 2022 | HS definition; official vs mirror |
| hsmirror | datasets/harmonized-system (GitHub), commit b1be3f2 | https://github.com/datasets/harmonized-system | VERIFIED (data source) | `git ls-remote`: HEAD = b1be3f2531a85fb0ea17147b19c41d3641912e43, the pinned commit; licence and provenance in `../experiments/data/external/PROVENANCE.md` | HS 2022 texts used for P8 |
| iso3166 | ISO 3166-1 country codes | https://www.iso.org/iso-3166-country-codes.html | **AUTHOR-CHECK** | iso.org returns HTTP 403 to automated requests; the study used ISO 3166-1 through pycountry 26.2.16 (PyPI page verified) | Country identification standard |
| cldr | Unicode CLDR, version 47 | https://cldr.unicode.org/ | VERIFIED (page fetched); version from the project records | Page title "Unicode CLDR Project"; CLDR 47 is via Babel 2.18.0 (`RESEARCH_STATE.md` §11) | Localised country names (J5) |
| unicodeemoji | Unicode emoji-test.txt 16.0 | https://www.unicode.org/Public/emoji/16.0/emoji-test.txt | VERIFIED (file fetched) | Downloaded file SHA-256 `24f0c534…` equals the hash pinned in the frozen `config.json` | P7 out-of-catalogue names |

**Summary:** 33 entries. 31 metadata-verified (metadata, page or file); **none has had a content-level review**,
which the authors must do (`author_review_items.md` Q16). 2 need a manual check by an author (holm1979, iso3166;
Q15). For koch2025 and
wube2026 only the metadata was verified and no abstract or full text was available, so the paper makes only title-level
statements about them. Raw Crossref responses were kept in the drafting session's scratchpad and are not committed.
