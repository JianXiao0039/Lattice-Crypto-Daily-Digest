# Phase 10B Top 3 Obsidian Notes

生成日期：2026-06-03

本报告记录 Phase 10B 的 Top 3 paper note scaffold。所有 notes 都是 private research scaffolds，不是博客、论文结论或已核验证据。它们基于 digest metadata、Phase 10A reading pipeline、weekly synthesis、daily JSON、reading queue state 和 research progress draft 的只读检查。

## 1. Top 3 selected papers

| Order | Paper | Why selected | Generated note |
| --- | --- | --- | --- |
| 1 | Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE | W23 reading_priority_score 95，A / 100；最贴近 LWE / dual attack / ML-KEM security estimation / AI4Lattice attack-cost proxy | `notes/papers/2026-1048-unified-dual-attack-analyses-covariance-based-score-distribution-prediction-for-lwe.md` |
| 2 | Module Lattice Security (Part IV): Probabilistic Polynomial Quantum Attack on Module-LWE over 2-Power Cyclotomics | W23 reading_priority_score 92，A / 100；强 MLWE / ML-KEM / module lattice security claim，需要优先 TODO_VERIFY | `notes/papers/2605-17412-module-lattice-security-part-iv-probabilistic-polynomial-quantum-attack-on-module-lwe.md` |
| 3 | On the Secrecy of the Encapsulation Coin in ML-KEM | 6 月 3 日强 positive，A / 100；Phase 10B explicitly requires this known IACR ML-KEM paper unless excluded by stronger reason | `notes/papers/2026-1117-on-the-secrecy-of-the-encapsulation-coin-in-ml-kem.md` |

Selection note：Phase 10A 的第三篇 must-read 是 `Improved Dual Attack and Trapdoor Sampling via Quantum Rejection Sampling`。Phase 10B 额外要求 ML-KEM encapsulation coin paper should be generated unless stronger Top 3 selection excludes it。这里将 `Improved Dual Attack` 暂时降为 next secondary scaffold，因为 ML-KEM paper 更适合立即服务 PQC implementation security / advisor update。

## 2. Evidence source used

- `docs/reports/phase-10a-research-reading-pipeline.md`
- `data/weekly/2026-W23.json`
- `data/2026-06-03.json`
- `state/reading-queue.json`（只读）
- `exports/research-progress/2026-W23/advisor-update-draft.md`（只读）
- `exports/research-progress/2026-W23/verification-backlog.md`（只读）

No Semantic Scholar API key was read, printed, stored, or referenced by value. If Semantic Scholar metadata appears in future runs, it remains advisory only.

## 3. Gaps / TODO_VERIFY

所有 note 都保留 TODO_VERIFY，因为当前只基于 digest metadata：

- Verify authors.
- Verify abstract.
- Verify main theorem / construction / attack / experiment.
- Verify parameters.
- Verify security assumptions.
- Verify implementation details.
- Verify relation to my research idea.

特别注意：

- `Module Lattice Security (Part IV)` 包含强 quantum attack claim，应先核验 Parts I-III、assumptions、parameter scope 和社区反馈。
- `On the Secrecy of the Encapsulation Coin in ML-KEM` 涉及具体 libraries 和 implementation behavior，应区分 test-only path、build-time substitution、production API exposure 和 validated configuration。
- `Unified Dual Attack Analyses` 应核验 score distribution / covariance derivation，而不是只引用 digest ranking。

## 4. Recommended reading order

1. `Unified Dual Attack Analyses`：先建立 attack score distribution baseline。
2. `On the Secrecy of the Encapsulation Coin in ML-KEM`：快速读，适合 advisor update 和 implementation security 讨论。
3. `Module Lattice Security (Part IV)`：深读与核验，避免过早接受强安全结论。

## 5. Best use by purpose

| Purpose | Best paper | Reason |
| --- | --- | --- |
| advisor update | On the Secrecy of the Encapsulation Coin in ML-KEM | 主题清楚、PQC implementation impact 明显、容易形成导师问题 |
| quick reading | On the Secrecy of the Encapsulation Coin in ML-KEM | 可先读 threat model 和 library table |
| deep technical reading | Unified Dual Attack Analyses | 需要理解 score distribution、variance、dual attack model |
| PhD narrative | Unified Dual Attack Analyses + ML-KEM coin paper | 一条连接 AI4Lattice attack modeling，另一条连接 deployable PQC implementation security |
| Module-SIS chameleon hash relevance | Module Lattice Security (Part IV) | 只作 module lattice assumption background；不要把 MLWE 结论直接迁移到 SIS |
| AI4Lattice relevance | Unified Dual Attack Analyses | 可作为 learned attack-cost proxy / candidate ranking 的理论背景 |

## 6. Manual reviewer checklist

- Open each original paper before using any technical claim.
- Mark paper facts, background supplement, and my inference separately.
- Do not cite Semantic Scholar citation counts as ranking authority.
- For ML-KEM coin paper, verify each library and configuration claim.
- For Module-LWE quantum attack paper, verify assumptions and parameter scope before discussing with advisor.
- For Unified Dual Attack, verify formulas and experiment tables before turning them into AI4Lattice features.
- Do not write generated notes into public blog or README without manual cleanup.
- Do not commit secrets, `.env`, `papers.db`, `exports/`, `audits/`, or generated digest artifacts.

## 7. Deferred secondary notes

The next three note scaffolds, if created manually later:

1. `Improved Dual Attack and Trapdoor Sampling via Quantum Rejection Sampling`
2. `From Perfect to Approximate Hints: Efficient LWE Secret Recovery Leveraging Low Hamming Weight`
3. `BRaccoon: Concurrently Secure Blind Lattice Signatures from Raccoon`

These remain valuable, but Phase 10B prioritized the known ML-KEM implementation-security paper for immediate note generation.
