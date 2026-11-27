# AI-use disclosure (draft for author confirmation, 27 Nov 2026)

IEEE requires authors to disclose AI-generated content (text, figures, images, code) in the acknowledgments, naming the
AI system and the sections and extent concerned. Each venue may add its own rules. **The authors must check the target
venue's current policy and confirm or correct the wording below before submission.** Disclosing AI use for language
editing only would be inaccurate.

## Text used in `main.tex` (Acknowledgment)
> **Use of AI tools.** An AI assistant (Claude, Anthropic, used through Claude Code) was used extensively in this work:
> analysing the original repository; supporting research planning and the evaluation design; writing the S1 code, the
> benchmark generators, the evaluation, statistics and run-control code and their tests; executing the authorised
> build, freeze, tuning, DEV and TEST stages; searching for and verifying literature metadata; and drafting this
> manuscript, including its tables and figure. The authors defined the research question and scope, made the review,
> exclusion, freeze and evaluation decisions, and are responsible for all content.

## Factual basis (from the project records)

| Activity | AI involvement | Human involvement | Record |
|---|---|---|---|
| Repository analysis | Performed by the assistant | Authors confirmed the findings and scope | `../repository_investigation.md` |
| Research question and scope | Assistant proposed options | Authors chose Option A and approved the question | `../research_question_and_scope.md`; `../author_review_checklist.md` §A–B |
| S1 implementation | Code written by the assistant | Author 2 reviewed `backend/lexitax_v2/` and accepted S1 (27 Nov 2026) | `../freeze_approval_record.md` §2.2 |
| Benchmark generators and labelling rules | Code and rules drafted by the assistant | Author 1 ran the labelling-rule pilot and the P7 review; all authors approved the exclusions | `../phase8_pilot_record_and_integrity.md`; `../experiments/pilot/` |
| Evaluation, statistics and run-control code | Written by the assistant | Authors approved the design and the tuning rule | `../experimental_evaluation_plan.md`; `../experiments/config.json` |
| Running freeze, tuning, DEV and TEST | Commands executed by the assistant | Each stage was separately authorised; Authors 1 and 2 jointly approved the freeze | `../freeze_approval_record.md`; `../experiments/results/*_stage_record.json` |
| Literature | Search and metadata verification by the assistant | **Pending:** Author 3 to read the cited works and confirm the cited statements | `bibliography_verification.md` |
| Manuscript text, tables and figure | Drafted by the assistant | **Pending:** all authors to read, verify, revise and approve | this folder |

No AI system is listed as an author. If the venue requires the exact model or version, the authors should add it as
the venue's form requests.
