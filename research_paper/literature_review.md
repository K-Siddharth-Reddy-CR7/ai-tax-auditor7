# Literature Review — Strategy and Candidate Pool (Phase 6 pending)

Status: **STRATEGY ONLY.** No reference below is verified yet, and none may be cited until its row is marked VERIFIED, with author list, title, venue, year and DOI checked against the publisher or Crossref record and the full text read for the claim it supports.

## 1. Verification environment note
- From this cloud session, `api.crossref.org`, `api.openalex.org`, `export.arxiv.org`, `dblp.org` and `ieeexplore.ieee.org` are **blocked by the network policy**. Web search works.
- Plan: verify through publisher pages via the web-fetch tool. If that also fails, request an allowlist addition for `api.crossref.org` (one host, read-only), or ask an author to export the BibTeX from IEEE Xplore and Crossref.

## 2. Search strategy
- **Databases:** IEEE Xplore, ACM DL, SpringerLink, ScienceDirect (publisher of record); Google Scholar and Semantic Scholar for discovery only; Crossref for metadata.
- **Window:** 2021–2026 for applied work, plus foundational sources (reject option, TF-IDF, statistics).
- **Query blocks:**
  - ("HS code" OR "Harmonized System") AND (classification OR prediction);
  - customs AND (fraud OR risk OR "import declaration") AND (machine learning OR detection);
  - "reject option" OR "selective classification" OR abstention;
  - "behavioral testing" OR robustness AND (NLP OR classification);
  - (regulatory OR legal) AND "information retrieval";
  - "record linkage" OR "name matching" AND (string similarity);
  - "error propagation" OR "cascading errors" AND pipeline.
- **Inclusion:** peer-reviewed (or a widely cited preprint, flagged as such), directly supports a specific sentence. **Exclusion:** vendor blogs, predatory venues, papers not read beyond the abstract.

## 3. Candidate pool (UNVERIFIED — discovery leads only)
| # | Lead | Role in paper | Status |
|---|---|---|---|
| L1 | C. K. Chow, "On optimum recognition error and reject tradeoff," IEEE Trans. Inf. Theory, 16(1), 41–46, 1970 | Reject-option foundation | Search snippet only |
| L2 | R. El-Yaniv, Y. Wiener, "On the foundations of noise-free selective classification," JMLR, 2010 | Risk–coverage | To find |
| L3 | Y. Geifman, R. El-Yaniv, "Selective classification for deep neural networks," NeurIPS 2017 | Risk–coverage curve / AURC | To find |
| L4 | M. T. Ribeiro et al., "Beyond accuracy: Behavioral testing of NLP models with CheckList," ACL 2020 | Perturbation-based testing | To find |
| L5 | S. Kim et al., "DATE: Dual Attentive Tree-aware Embedding for customs fraud detection," KDD 2020 | Customs ML (risk selection) | Search snippet |
| L6 | S. Kim et al., customs import declaration datasets, arXiv 2208.02484 (2022) | Data availability in customs research | Snippet; preprint |
| L7 | arXiv 2111.01663 — deep learning HS-code prediction | HS classification | Snippet; check venue |
| L8 | arXiv 2211.04313 — ensemble HS classification (IBM) | HS classification | Snippet; check venue |
| L9 | arXiv 2602.17102 — serverless MLOps HS prediction (2026) | Recent industrial HS | Snippet; preprint |
| L10 | Sentence-BERT + contrastive HS classification (Data Technologies & Applications?) | HS classification | Snippet; check venue |
| L11 | Customs fraud under concept drift (same group as L5) | Customs ML | To find |
| L12 | Ilias Chalkidis et al., regulatory compliance doc-to-doc IR (EACL 2021) | Regulatory IR | To find |
| L13 | G. Salton, C. Buckley, "Term-weighting approaches in automatic text retrieval," IP&M, 1988 | TF-IDF | To find |
| L14 | S. Robertson, H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," 2009 | IR baseline context | To find |
| L15 | P. Lewis et al., "Retrieval-augmented generation…," NeurIPS 2020 | To *contrast*: what RAG is (not implemented here) | To find |
| L16 | W. Cohen, P. Ravikumar, S. Fienberg, string distance metrics for name matching, 2003 | Name/jurisdiction matching | To find |
| L17 | P. Christen, *Data Matching*, Springer, 2012 | Record linkage | To find |
| L18 | J. R. Finkel et al., cascading errors in NLP pipelines, EMNLP 2006 | Error propagation | To find |
| L19 | D. Sculley et al., "Hidden technical debt in ML systems," NeurIPS 2015 | Pipeline reliability | To find |
| L20 | Q. McNemar, 1947; T. G. Dietterich, 1998 (Neural Computation) | Paired tests | To find |
| L21 | E. B. Wilson, 1927 (JASA) | Score interval | To find |
| L22 | J. Cohen, 1960 (Educ. Psychol. Meas.) | Kappa | To find |
| L23 | M. Wooldridge, N. Jennings, "Intelligent agents: theory and practice," KER, 1995 | Why we do *not* call stages agents | To find |
| L24 | WCO / HS 2022 nomenclature; ISO 3166-1 | Reference data (standards, not papers) | Official pages |
| L25 | WTO Customs Valuation Agreement (Art. VII GATT) | Valuation context | Official text |
| L26+ | 2021–2026 customs-AI / trade-compliance surveys (e.g. in *World Customs Journal*, IEEE Access) | Domain motivation | To search |

## 4. Gap-assessment questions for Phase 6
1. Do HS-classification papers report abstention, coverage or silent-error rates, or only top-k accuracy?
2. Do customs decision-support papers evaluate *end-to-end* propagation into duty/tax amounts?
3. Is there prior work on jurisdiction/country-name normalisation risk in trade or tax systems?
4. Are there public customs-assistance benchmarks with human-written descriptions?

The gap statement in `research_question_and_scope.md` §6 will be revised to match what the evidence supports.
