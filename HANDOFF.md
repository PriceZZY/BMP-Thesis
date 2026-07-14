# HANDOFF — BMP-Thesis / JGLR MS# GLR-S-26-00143

**Written:** 2026-07-13 by Claude (Fable 5), for GPT-5.6 incoming as **architecture gate**.
**Role split going forward:** GPT-5.6 = architecture / decision gate. Claude = implementation.
**Author / owner:** Zhenyu Zhou (Price), UWaterloo Geospatial Data Science 2A, **sole author, first submission.**

---

## 0. HOW TO READ THIS DOCUMENT

Every substantive claim below carries an epistemic tag. **Do not treat them as equivalent.**

| Tag | Meaning |
|---|---|
| `[VERIFIED]` | Reproduced on this machine, or read directly from the source file/line. Evidence cited inline. |
| `[VERIFIED-EXT]` | Confirmed against an external source (Crossref / OpenAlex / publisher abstract), cross-checked ≥2 ways. |
| `[INFERRED]` | Follows logically from verified facts, but not directly executed/observed. Could be wrong. |
| `[UNCERTAIN]` | Genuinely open. Flagged for your judgment. **These are where I most want a second opinion.** |
| `[I-WAS-WRONG]` | I asserted this earlier in the session and later corrected it. Recorded so you don't inherit the error. |

**Bias warning about me:** I ran a 33-agent mock peer-review panel that burned ~3M tokens and produced
useful findings, but I also **overstated the severity of the central code bug** on first pass and had to
walk it back (see §5.1). Treat my severity rankings as arguments, not verdicts. That is precisely why a
gate is useful here.

---

## 1. HARD CONSTRAINTS (violate none of these without explicit owner sign-off)

1. **The submitted manuscript is FROZEN.** It is under peer review at JGLR *right now*. Nothing we do
   changes what the reviewers are reading. Do not edit `paper/jglr_submission/Zhou_JGLR_2026_manuscript.docx`
   or `draft_jglr_v1.md`. Prepare corrections as *artifacts*, not as manuscript edits.
2. **`main` is untouched and must stay untouched.** `main == origin/main == be8eee6`. All work is on
   `rr/2026-07-13-factual-corrections`.
3. **Do NOT add SWAT to this paper.** Standing decision by the owner. Rationale is now stronger, not weaker:
   the variance decomposition shows precipitation dominates and the participation constraint binds ~11×
   harder than allocation — adding hydrological fidelity would not change the strategy ranking. Coupled
   ABM–SWAT is a separate PhD chapter. *Citing* Liu/Kast/Scavia (who use SWAT) is required; *replicating*
   them is not.
4. **`git push` is blocked by the owner's own hook** (`~/.claude/hooks/block-dangerous-git.sh`). This is
   intentional. The owner pushes manually. Do not attempt to bypass.
5. **Owner is token-budget constrained** (hit a usage limit this session). Do not spawn large agent fleets
   for tasks that are linear. Local Python compute is ~free; API fan-out is not.

---

## 2. PROJECT IDENTITY

- **Paper:** *Designing cost-share subsidy allocations for agricultural phosphorus reduction: A
  spatially-explicit simulation of the Upper Thames River watershed*
- **Venue:** Journal of Great Lakes Research (Elsevier). **MS# GLR-S-26-00143.** EiC: Prof. Margaret F. Docker.
- **Model:** Spatially-explicit ABM. 8,949 field agents (AAFC Annual Crop Inventory 2024), Upper Thames
  watershed (3,482 km²). Compares 5 subsidy allocation strategies under the real UTRCA $17.41M Phosphorus
  Reduction Program constraints. 1,000 paired Monte Carlo runs per strategy.
- **Central claim:** Under realistic voluntary participation, *no* allocation redesign meaningfully
  outperforms first-come-first-served. The binding constraint is *who will participate*, not *how the
  budget is distributed*.
- **Repo:** `github.com/PriceZZY/BMP-Thesis` · **Zenodo DOI:** 10.5281/zenodo.19971792 (cited in the
  manuscript as a `[dataset]` reference)

---

## 3. TIMELINE `[VERIFIED]`

| Date | Event |
|---|---|
| — | Submitted to **Environmental Modelling & Software** → **desk-rejected on scope** (no review) |
| — | Submitted to **Ecological Modelling** → **desk-rejected on scope** (no review) |
| 2026-05-02 | `3821bf3` Initial public release (code, processed data, MC results) |
| 2026-05-02 | `be8eee6` Zenodo DOI added to README / CITATION.cff / RUN_GUIDE / manuscript |
| **2026-05-11 15:28** | **Submitted to JGLR.** MS# confirmed 05-12. |
| 2026-07-09 | Last reviewer activity (per Editorial Manager) |
| **2026-07-13** | **Status: Under Review.** 2 reviewers invited, **2 accepted, 1 review completed.** |
| 2026-07-13 | This audit + branch `rr/2026-07-13-factual-corrections` (4 commits) |

**Key framing fact:** the two prior rejections were **scope desk-rejects, not quality rejects.** They
carry ~zero information about paper quality. JGLR is the first venue where the paper reached actual peer
review. That is a real milestone and the owner systematically under-weights it.

---

## 4. WHAT I DID THIS SESSION

1. Read the full 16,000-word manuscript + both appendices.
2. Ran a 5-reviewer mock peer-review panel (P-biogeochemistry / ABM-methods / policy-econ / JGLR-scope-fit
   / hostile-statistics), then adjudicated all 21 "fatal" claims they raised, then generated rebuttals.
   **Result: 5/5 Major Revision, 0 Reject. 21/21 claims adjudicated FIXABLE_IN_REVISION, 0 TRULY_FATAL.**
3. Independently verified the load-bearing numbers against the code and results files.
4. Ran new simulations (bioavailable-P split; corrected variance decomposition; bug-severity test).
5. Fixed two classes of code defect on an isolated branch.

---

## 5. FINDINGS — ranked, tagged, with evidence

### 5.1 Parameter-sampling bug `[VERIFIED]` — **severity: MEDIUM (I initially said HIGH; I was wrong)**

**The defect:**
```python
# src/model/simulation.py:137  (pre-fix)
metrics = env.detailed_metrics(sample=not env.stochastic)   # stochastic=True → sample=False

# src/model/environment.py:193 (pre-fix)
if sample and self.stochastic:      # False and True → ALWAYS False
    rate = self.rng.normal(...)     # ← never executed in any reported run
else:
    rate = params['mean']
```
`BASE_P_LOSS`, `REDUCTION_A/B`, `PARTICULATE_RATIO` were **never sampled** — pinned to means in every
published result. Corroborated by the owner's own output file:
```
variance_A_params   = 3.6316714786346673   (Exp A: params + adoption)
variance_C_adoption = 3.6221504426764732   (Exp C: adoption only)
var_pure_params     = 0.0095               (A − C = floating-point noise)
```
Experiment A and Experiment C were **the same experiment**.

**`[I-WAS-WRONG]`** — I first told the owner this "overturns abstract headline #3 (99% precipitation)."
It does not, or at least not straightforwardly. I then ran the decisive test (n=400, precip fixed):

| Treatment | Parameter share of total variance |
|---|---|
| As published | **0.001%** |
| Flag fixed, **per-field** sampling (the original code's semantics) | **0.09%** |
| **Run-level** sampling (epistemic uncertainty) | **16.71%** |

**⟹ If `std` means field-to-field heterogeneity — which is exactly what per-field sampling implements —
then the parameter contribution genuinely IS ≈0, and the published 0.001% is numerically almost right.**
8,949 independent draws average away by the LLN. That is a mathematical property of the sampling
granularity, not a property of the watershed.

**So the correct severity is: real code defect + inaccurate §2.11 methods description — NOT a wrong result.**

**`[UNCERTAIN]` — DECISION FOR THE GATE:** the deeper methodological question is what `std` *should* mean.
Per-field heterogeneity (averages out, contributes ~0) and epistemic uncertainty in the true mean
(watershed-correlated, contributes 16.7%) are **different things and both are real.** The paper conflates
them. My fix implements run-level (epistemic) sampling because that is what a *variance decomposition*
should be asking. **But using the paper's existing `std` values as epistemic uncertainty on the mean is
arguably too large** (std=0.50 on mean=1.50 is a 33% CV on a watershed-wide parameter). A defensible
alternative is a smaller, literature-derived uncertainty on the mean, with field heterogeneity modelled
separately. **I did not resolve this. It needs a call.**

**What survives regardless:** precipitation dominates under *both* treatments (82.5% run-level / 99.5%
per-field). §4.3(3)'s policy recommendation ("normalize for precipitation before attributing outcomes to
program changes") is **unaffected either way.**

---

### 5.2 The 64 t/yr denominator `[VERIFIED]` — **severity: HIGH**

Hit independently by **5 of 5** mock reviewers.

**The arithmetic error:**
- §1 derives the target as `212 t/yr × 30%` = 64 t/yr, where 30% = 84/280 = the Thames' share **of the
  four priority tributaries**.
- But 212 t/yr is 40% of Canada's **total** load (⟹ Canadian baseline = 212/0.40 = 530 t/yr).
- Multiplying a *share-of-tributaries* by a *share-of-national-total* reduction is a **base mismatch**.
- Correct proportional apportionment: `84/530 × 212` = **33.6 t/yr**. Cross-check: `84 × 0.40` = **33.6 t/yr**. ✓
- **Simplest tell:** the paper's 64 t is **76% of the Thames' own stated 84 t/yr load** — but the policy
  target is a **40%** reduction.

**The load-basis contradiction:**
- §1: whole Thames = **84 t/yr**
- §2.2: **Upper** Thames = 80–670 t/yr, long-term mean **~300 t/yr**
- Model's own computed edge-of-field base load: **~381 t/yr** `[VERIFIED — ran it]`
- These cannot all be true (a sub-basin cannot carry 3.6× the whole river).

**RESOLVED by the paper's own citation `[VERIFIED]`:** §2.1 cites Kao et al. (2022, JGLR): Fanshawe
Reservoir retained 25% of incoming P in 2018 (**36 t**) and 47% in 2019 (**91 t**). Back-calculate the
inflow: 36/0.25 = **144 t/yr**; 91/0.47 = **194 t/yr**. Fanshawe is **one reservoir on one branch of the
Upper Thames.** ⟹ the whole-Thames figure of 84 t/yr is **physically impossible**. The ~300 t/yr basis is
the correct one.

**Consequence — and this is the important part:**

| | 40% target | FCFS 42.8 t | Best alternative fills |
|---|---|---|---|
| ~~84 t basis~~ | ~~34 t~~ | ~~127% — target EXCEEDED, conclusion inverts~~ | **ruled out by Fanshawe** |
| **~300 t basis (correct)** | **120 t** | **36%, gap = 77 t** | **1.1%** |
| + 3.1× calibration correction | 120 t | 12% (13.8 t), gap = **106 t** | **0.3%** |
| *as published* | *64 t* | *67%, gap 21 t* | *4.0%* |

**Fixing the denominator STRENGTHENS the central conclusion — dramatically.** Gap goes from 21 t to
77–106 t; the allocation lever's contribution drops from 4.0% to 0.3–1.1%.

**`[UNCERTAIN]` — DECISION FOR THE GATE:** what exactly *is* the ECCC 84 t/yr figure? (Spring-only load?
A specific gauge? The agricultural-nonpoint fraction?) **The owner must go back to the ECCC source and
pin down the basis of every number.** I could not resolve this from the manuscript alone. Also unresolved:
whether the target should be apportioned to the **Upper** Thames specifically (the model's domain) vs the
whole Thames (Upper + Lower; the Lower has its own $13M LTVCA program).

---

### 5.3 Missing gatekeeper literature `[VERIFIED-EXT]` — **severity: HIGH (highest ROI to fix)**

**The manuscript cites ZERO Scavia papers and ZERO Lake Erie basin ABMs.** The only ABM cited is
**Emami et al. (2024) — an irrigation ABM for Lake Urmia, Iran.** It builds an ABM of Lake Erie and cites
an Iranian ABM instead of the one from the same lake basin.

**This is the same failure mode that killed the EMS submission** (which cited zero Grimm/ODD/POM). The
ABM-methods gate has since been fixed (Grimm 2020 + Müller 2013 ODD+D cited, 4,868-word ODD+D in Appendix
S2). The **Lake Erie domain canon** has not.

**Required citations** (all cross-verified against ≥2 of Crossref / OpenAlex / Semantic Scholar):

| Paper | DOI | Why it's load-bearing |
|---|---|---|
| **Liu, Zhang, Irwin, Kast, Aloysius, Martin, Kalcic (2020)**, *Land Economics* 96(4):510–530 | `10.3368/wple.96.4.510` | ⚠️ **Kills the novelty claim.** Abstract, verbatim: *"We develop **the first spatially integrated economic-hydrologic model of the western Lake Erie basin** explicitly linking economic models of farmers' field-level BMP adoption choices with SWAT…"* |
| **Daloğlu, Nassauer, Riolo, Scavia (2014)**, *Ecology & Society* 19(3):12 | `10.5751/ES-06597-190312` | ABM of farmer conservation behaviour coupled to water quality, **Sandusky — same lake basin**. The direct ancestor. |
| **Daloğlu, Nassauer, Riolo, Scavia (2014)**, *Agricultural Systems* 129:93–102 | `10.1016/j.agsy.2014.05.007` | Farmer typology — precedent for the exact "behavioural heterogeneity" layer claimed as novel |
| **Kast, Kalcic, Wilson, Jackson-Smith, Breyfogle, Martin (2021)**, *Water Research* 201:117375 | `10.1016/j.watres.2021.117375` | Tests **targeting/allocation strategies** vs watershed P reduction in the Maumee, using **survey-derived farmer willingness**. Nearly the same question. |
| **Scavia et al. (2014)**, *JGLR* 40(2):226–246 | `10.1016/j.jglr.2014.02.004` | 609 cites. The load–response science behind the 40% target. Paper cites only the *policy PDF*, not this. |
| **Scavia et al. (2017)**, *Front Ecol Environ* 15(3):126–132 | `10.1002/fee.1472` | Multi-model ensemble on which BMP scenarios meet the 40% target. **Most conspicuous omission in a JGLR submission.** |
| **Muenich, Kalcic, Scavia (2016)**, *ES&T* 50(15):8146–8154 | `10.1021/acs.est.6b01421` | Legacy P + conservation practices, Maumee |
| **Kalcic et al. (2016)**, *ES&T* 50(15):8135–8145 | `10.1021/acs.est.6b01420` | Stakeholder-bounded *feasible adoption rates* — the behavioural-participation layer |
| **Bosch, Allan, Selegean, Scavia (2013)**, *JGLR* 39(3):429–436 | `10.1016/j.jglr.2013.06.004` | **Published in JGLR itself.** Uncited same-journal precedent. |
| **Bosch, Evans, Scavia, Allan (2014)**, *JGLR* 40(3):581–589 | `10.1016/j.jglr.2014.04.011` | Same. Paper already cites Baker et al. (2014) from the same JGLR volume-year — the omission looks selective. |
| **Baumgart-Getz, Prokopy, Floress (2012)**, *J Env Mgmt* 96(1):17–25 | `10.1016/j.jenvman.2011.10.006` | Canonical adoption meta-analysis (lowest severity — Prokopy 2019 already cited) |

**THE REFRAME — this is a gift, not a liability `[VERIFIED-EXT]`:**

- **Liu et al. (2020) conclude:** *"A hybrid policy coupling a **fertilizer tax** with cost-share payments
  … can achieve the policy goal of 40% reduction."* → **The basin's most authoritative economic-hydrologic
  model independently concludes that voluntary cost-share alone is insufficient.** That *corroborates* this
  paper's thesis via a completely different method.
- **Kast et al. (2021) conclude:** *"BMP placement should target areas of high phosphorus loading **with
  willing landowners**."* → **Targeting works only when conditioned on willingness.**

**Proposed positioning (replaces the indefensible "first integrated analysis" claim):**

> The **US side** of the basin has coupled economic-hydrologic models (Liu et al. 2020) and behaviourally-
> informed targeting studies (Kast et al. 2021), which converge on two findings: voluntary cost-share alone
> cannot meet the 40% target, and spatial targeting is effective only when conditioned on farmer willingness.
> The **Canadian side** has neither. The operating UTRCA program ($17.41M) has **no willingness data and no
> targeting**. We quantify what that costs — and find it costs nothing, because participation is an ~11×
> larger lever than allocation, and under realistic participation the targeting advantage vanishes entirely.
> This **converges with Liu et al.** (instruments beyond voluntary cost-share are required) and
> **complements Kast et al.** (targeting requires willingness information the Canadian program does not collect).

This turns the paper from "lonely contrarian" into "standing on the field's best work and filling the
Canadian gap." It also pre-answers *"why no SWAT?"* — the variance decomposition shows the participation
constraint binds far harder than hydrological resolution.

---

### 5.4 Statistical misstatement `[VERIFIED]` — **severity: MEDIUM. The paper UNDERSELLS itself.**

Table 3 / Abstract call Naive (+2.0%) and Smart (−1.6%) *"not statistically distinguishable from FCFS"*,
based on the paired difference's **95% empirical range** crossing zero. That range is the **spread** of
the difference, **not the confidence interval of its mean.**

The MC runs are **paired** (`monte_carlo.py: seed = i + 1000`, same seed passed to all 5 strategies →
shared precipitation sequence). Recomputed from `results/monte_carlo_results.json`, n=1,000 paired:

| Strategy | Mean paired diff | **95% CI of the MEAN** | Paired *t* | Win rate |
|---|---|---|---|---|
| Naive Hotspot | **+0.848 t** | [+0.746, +0.949] — excludes 0 | **p = 2.0×10⁻⁵³** | 73% |
| Smart Hotspot | **−0.634 t** | [−0.732, −0.537] — excludes 0 | **p = 1.3×10⁻³⁴** | 31% |
| Efficiency | −25.878 t | [−26.887, −24.869] | p < 10⁻²⁷⁰ | 0% |
| Moderate Eff | −22.349 t | [−23.226, −21.472] | p < 10⁻²⁷⁰ | 0% |

Both hotspot variants are **overwhelmingly significant.** "We can't tell them apart" invites the reviewer
to reply *"your model is underpowered"* — which is far more damaging than the truth. The correct and
**stronger** statement:

> With n=1,000 paired runs the Monte Carlo standard error is ~0.05 t/yr; strategy rankings are resolved
> with high precision. Naive Hotspot significantly outperforms FCFS (+0.85 t/yr) and Smart Hotspot
> significantly underperforms (−0.63 t/yr). **These effects are nonetheless policy-negligible:** the best
> alternative allocation closes ~1% of the shortfall. Residual uncertainty is structural and parametric
> (§3.6, §4.5), not Monte Carlo noise.

---

### 5.5 Cost-effectiveness reversal `[VERIFIED]` — **severity: MEDIUM. Abstract is falsified by the owner's own JSON.**

From `results/monte_carlo_results.json` (`cost_per_kg_mean`):

| Strategy | Total P | Cost | **$/kg P** |
|---|---|---|---|
| FCFS | 42.8 t | $10.87M | **$365** |
| **Naive Hotspot** | **43.6 t (+2.0%)** | **$9.48M** | **$313 (−14%)** |
| Smart Hotspot | 42.2 t (−1.6%) | $8.31M | **$284 (−22%)** |

**Naive Hotspot dominates FCFS on BOTH axes** — more phosphorus AND cheaper per kg. Smart Hotspot delivers
98.5% of the P for 76% of the cost. The abstract says all four alternatives are *"statistically equivalent
to or **worse than** FCFS."* **That is false.**

**The honest version is more useful:** *reallocating the budget buys **efficiency**, not **effectiveness**.*
Targeting lowers unit cost 14–22% but the load-reduction gain (+2.0% at best, ~1% of the gap) is
policy-negligible. If your goal is the 40% target, allocation is the wrong lever. If your goal is stretching
a fixed budget, modest targeting is worth it. That gives UTRCA a real, actionable recommendation.

---

### 5.6 Bioavailable-P was computed and then discarded `[VERIFIED]` — **now resolved, and it's GOOD news**

`environment.py:257` computes `bioavailable = pp_reduced*0.25 + drp_reduced*1.0`. §2.1 explicitly promises
*"Our model reports **both** total phosphorus reduction and bioavailable phosphorus reduction… as they can
lead to **divergent** assessments."* **But `monte_carlo.py` stored only `p_reduction_t`.** Bioavailable P is
never reported by strategy — while Efficiency Pricing, *the strategy designed around bioavailability*, was
condemned on total P alone (the very metric §2.1 argues is wrong).

**I re-ran it** (n=300 paired; harness reproduces the published seed-1000 FCFS value bit-for-bit):

| Strategy | Total P | PP | DRP | **Bioavailable P** | vs FCFS (TP) | **vs FCFS (bio)** |
|---|---|---|---|---|---|---|
| FCFS | 41.0 t | 30.9 | 10.1 | **17.9 t** | — | — |
| Naive Hotspot | 41.8 t | 32.7 | 9.1 | 17.3 t | +1.9% | −3.4% |
| Smart Hotspot | 40.3 t | 30.7 | 9.6 | 17.2 t | −1.8% | −3.4% |
| **Efficiency Pricing** | 16.3 t | 8.8 | **7.5** | **9.7 t** | −60.4% | **−45.7%** |
| Moderate Eff | 19.6 t | 10.6 | 9.0 | 11.6 t | −52.2% | −34.8% |

**Efficiency Pricing loses on the metric it was designed for**: paired diff **−8.17 t**, 95% CI
[−8.74, −7.60], **p = 2×10⁻⁸⁵, 0/300 wins.** This **closes the strongest available line of attack** and lets
the claim be stated far more forcefully. Data: `results/_RR2026-07-13_bioavailable_by_strategy.json`.

---

### 5.7 The mechanism explanation is fabricated — AND the model is price-inelastic by construction `[VERIFIED]` — **severity: HIGH. This is now the strongest surviving methodological objection.**

> **`[I-WAS-WRONG]` ×2.** I proposed two mechanisms for this and **both were wrong**. I record the failures
> because a gate should know how much to discount my mechanism reasoning.
> **Wrong guess #1:** "non-economic barriers" — that's the *paper's* story, and it's fabricated (see below).
> **Wrong guess #2:** "Type B has no independent adoption pathway; it rides on Type A." **Falsified:** under
> Efficiency Pricing, `adopted_type_b = 2857` but `adopted_both = 1746` → **1,111 fields adopt Type B alone.**
> §2.9 states Efficiency Pricing offers **Type B first**, so it *does* have an independent path.
> I then stopped guessing and measured the adoption function directly. Below is what it actually is.

**The observation.** Efficiency Pricing **doubles** the Type B subsidy ($30 → $60):

| | Type A adoptions | Type B adoptions |
|---|---|---|
| FCFS | 4272 | 2873 |
| Efficiency Pricing | 3066 (**−28%**) | 2832 (**−1%**) |

**The paper's explanation is not in the model.** §3.3 / §4.1 / §4.3(4) attribute the flat Type B response to
*"specialized equipment and process changes that subsidies alone cannot overcome"* — i.e. **non-economic
barriers.** But the adoption function is purely
`logistic(intercept + subsidy_coeff·net_benefit + area_coeff·area + peer_coeff·neighbor_rate)`
(`adoption_function.py:73–92`). **There is no equipment constraint and no process friction anywhere in the
model.** The paper explains a model output with a mechanism the model does not contain.

**The actual mechanism `[VERIFIED — measured directly from the adoption function]`:**

At the calibrated values (`intercept = −2.00`, `subsidy_coeff = 0.010`), for a typical 64-acre field with
30% of neighbours adopted:

| Type A subsidy | net benefit | P(adopt) | | Type B subsidy | net benefit | P(adopt) |
|---|---|---|---|---|---|---|
| $15 | −$5/ac | 0.187 | | $30 | −$2/ac | 0.191 |
| $30 | +$10/ac | 0.210 | | $60 | +$28/ac | 0.242 |

- Halving the Type A subsidy: P(adopt) **−11.3%**
- **Doubling** the Type B subsidy: P(adopt) **+26.5%** — *not* +100%.

**`subsidy_coeff = 0.010` is so small that doubling a subsidy moves the logit by only 0.30.
The adoption function is nearly price-inelastic by construction.** Adoption is then bounded by the
*participation filter* (55/45/30%), not by price — which is why Type B stays flat at −1% despite a doubled
subsidy: **the willing pool, not the price, is the binding constraint.**

**⚠️ THE NEW FINDING — and it is serious `[VERIFIED]`:**
§2.7 states the grid search ranged `subsidy_coeff ∈ [0.010, 0.055]` in 0.005 increments.
**The calibrated value, 0.010, sits exactly on the LOWER BOUND of the search range.**
**This is a boundary solution** — the optimizer wanted to go lower and could not.

⟹ **The price coefficient is pinned to its floor, so price-based instruments are *guaranteed* to look
ineffective.** A reviewer will say: *"you calibrated a near-zero price elasticity, therefore your finding that
price instruments fail is assumed, not discovered."* This is precisely the one mock-review objection that was
adjudicated as costing **weeks** rather than hours/days to answer, and it is the strongest surviving
methodological attack on the paper.

**Two readings, and the gate must choose `[UNCERTAIN]`:**
- **(a) The boundary solution is a genuine empirical signal.** Real UTRCA Year-1 uptake really was weakly
  price-responsive, and the calibration is telling us so. If defensible, this *supports* the paper's thesis and
  should be argued explicitly (with the range extended downward to show the optimum is interior after all).
- **(b) It is misspecification.** The model has no channel through which price can act except this one
  coefficient, so the calibrator drove it to zero to fit aggregate throughput that is actually being set by the
  participation filter. **If this is true, the Efficiency Pricing result is an artifact and §4.3(4) must go.**

**Minimum required action:** re-run the grid search with `subsidy_coeff` extended **below 0.010** and report
whether the optimum is interior. That single run distinguishes (a) from (b). It is cheap and it must be done
before any Efficiency-Pricing claim is defended.

**Also note the internal contradiction:** §4.5 already concedes *"The adoption function evaluates each subsidy
offer independently and does not model BMP-type switching behavior… The Efficiency Pricing results therefore
test farmer response to different subsidy levels, **not farmer substitution between BMP types**."*
⟹ **§4.5 says "we cannot test this"; §4.3(4) issues a policy recommendation based on it.**

---

### 5.8 Reproducibility package was completely broken `[VERIFIED]` — **FIXED on this branch**

**35 hardcoded `D:/Claude/BMP-Thesis` paths across 21 files.** The Zenodo package — cited in the manuscript
as a `[dataset]` reference, with a Data Availability statement advertising a **15-minute reproduction path**
— **could not run on any machine**, including Windows, unless the repo sat at exactly `D:/Claude/BMP-Thesis`.
**No reviewer could reproduce anything.** All 35 replaced with repo-relative paths; verified by running from
an unrelated cwd (`/tmp`) with `data_path=None`.

**`[UNCERTAIN]` — DECISION FOR THE GATE:** should the **Zenodo record be updated** mid-review? Arguments both
ways. Updating it makes the advertised reproduction path actually work; but touching a DOI-ed artifact while
under review may look odd, and the version reviewers were pointed to is the broken one either way.

---

### 5.9 Other open items (lower priority, all `[VERIFIED]` as present)

| Item | Location | Cost |
|---|---|---|
| **Sobol GSA was never done.** No SALib in the codebase — only OAT. §4.5 admits: *"remains an unverified assumption."* A methods reviewer will demand it. | `src/analysis/` | days (compute is available) |
| **Edge-of-field treated as delivered load.** The model has **no** delivery/routing/retention factor anywhere (`grep` confirms). Yet 42.8 t is compared to a lake-delivered target. Kao et al. 2022 — the paper's own citation — has Fanshawe retaining 25–47%. | model-wide | text fix = hours; delivery coefficient = days |
| **Erosion–DRP tradeoff unmodelled**, and it directly threatens recommendation §4.3(4) ("maintain Type A subsidies"). §2.12 already flags it as *"the most consequential unmodeled mechanism."* | §2.12 / §4.3(4) | scope to the TP metric + caveat |
| **Post-sigmoid noise** `N(0,0.3)` — §2.7 says *"differs from latent-logit noise conventions but was retained for consistency with the calibrated parameter set."* Reads as "we knew it was wrong and didn't fix it." | §2.7 | 1 day (re-run) |
| **P-risk score contains no phosphorus SOURCE term** — only drainage / slope / proximity / texture, i.e. all **transport** factors. Yet it is used as the loading proxy that generates the headline "25% of area → 57% of loading." | §2.4 | needs honest relabelling as *delivery risk*, or add a source term |
| **"25% of area → 57% of loading" is an input assumption reported as a finding.** | Abstract / §3.4 | wording |

---

## 6. CODE CHANGES ON THIS BRANCH `[VERIFIED]`

Branch: **`rr/2026-07-13-factual-corrections`** (4 commits, ahead of `main` by 4; `main` untouched)

| Commit | Change |
|---|---|
| `d51d79b` | **Fix the sampling bug.** New `_draw_run_params()` draws ONE parameter realization per run from a **dedicated RNG stream** (`param_rng = seed + 777_000`) — so the precipitation sequence, adoption noise and initial-adoption assignment on `self.rng` are **bit-identical** to pre-fix runs. Only the parameters now actually vary. Added `use_mean_params()` for variance-decomposition Experiments B/C. Also fixed `environment.py:84`'s hardcoded Windows path. |
| `6c3ae58` | **Remove all 35 hardcoded Windows paths** across 21 files → repo-relative `_REPO = Path(__file__).resolve().parents[2]`. |
| `ad6e9bd` | R&R prep doc + corrected results + reproduction scripts. |
| `97941fb` | Bug-severity adjudication + **correction of my own overstatement**. |

### THE REGRESSION TEST — this is the guarantee `[VERIFIED]`

```
ThamesEnvironment(seed=1000) + use_mean_params() + FCFS
  → p_reduction = 51.25869938923559
  → published   = 51.25869938923559        ← BIT-FOR-BIT IDENTICAL
```
This proves the **only** thing that changed is that parameters now actually vary. Nothing else was touched.
Every new script (`src/analysis/_RR2026-07-13_*.py`) embeds this check and **refuses to emit numbers if it
fails**.

**`[UNCERTAIN]` — the full MC suite has NOT been re-run under the fix.** Doing so will change every reported
result and every empirical range (they will **widen**: [39.3, 46.9] → [19.1, 68.8]). That is a 1–2 day job and
**should not start until the gate rules on §5.1's open question** (what `std` means / how large epistemic
parameter uncertainty should be), because the answer determines what to re-run.

---

## 7. RECOMMENDED ORDER OF WORK (my proposal — the gate should challenge it)

| # | Task | Cost | Why this order |
|---|---|---|---|
| **0** | **Re-run the calibration grid search with `subsidy_coeff` extended BELOW 0.010** (§5.7) | **hours** | **Do this first.** One cheap run decides whether the boundary solution is a real signal or misspecification — and that determines whether the entire Efficiency Pricing result (and §4.3(4)) survives. Everything downstream about price instruments is blocked on the answer. |
| 1 | **Add the 11 citations + rewrite the novelty claim** (§5.3) | hours | Highest ROI. Converts the biggest liability into the best positioning. Zero dependencies. Can run in parallel with #0. |
| 2 | **Resolve the 64 t denominator** against the ECCC source (§5.2) | days | The only thing that can *invert* the conclusion if a reviewer fixes it partially. **Owner-led** — needs the primary ECCC documents, which I could not access. |
| 3 | **Fix the statistical wording + cost-effectiveness framing** (§5.4, §5.5) | hours | Pure text. Both make the paper stronger. No open questions. |
| 4 | **Gate decision on §5.1** (what `std` means), then re-run the full MC suite | 1–2 days | Blocked on the gate. Will change every reported number and widen every empirical range. |
| 5 | **Sobol GSA** (§5.9) | days | Reviewers will demand it; §4.5 already concedes it's missing. |

**Items 1 and 3 are pure wins with no open questions and should start immediately.
Item 0 is cheap and gates the largest remaining risk.**

---

## 8. WHAT I AM MOST LIKELY WRONG ABOUT — please pressure-test these

**Track record this session: I made 3 confident claims that were wrong and had to retract all 3.** Calibrate
accordingly — my *measurements* have held up (everything tagged `[VERIFIED]` was executed and reproduces), but
my *mechanism reasoning and severity rankings* have a demonstrated failure rate.

| I claimed | Reality | How it was caught |
|---|---|---|
| The sampling bug "overturns abstract headline #3" | It doesn't. Under the paper's own per-field semantics, parameter contribution really is ≈0 (0.09%). Code defect, not wrong result. | I ran the decisive test instead of asserting |
| "Type B has no independent adoption pathway; it rides on Type A" | False. Under Efficiency Pricing, 1,111 fields adopt Type B alone. | I checked across strategies instead of generalizing from one run |
| (implicitly) that I understood the Efficiency Pricing mechanism | I did not, twice. The real answer is near-zero price elasticity + a boundary solution in the calibration. | I stopped guessing and measured the adoption function |

**Open items where I am genuinely unsure — please pressure-test:**

1. **§5.7 — the boundary solution.** `subsidy_coeff` calibrated to exactly the lower bound of its search range.
   **I do not know whether this is a real empirical signal or misspecification, and it determines whether the
   Efficiency Pricing result survives at all.** This is now the **#1 thing I want gated.** The test that
   distinguishes them is cheap (§7 item 0) — but the *interpretation* of the result is an architecture call.
2. **§5.1 — the right epistemic treatment of parameter uncertainty.** I chose run-level sampling using the
   *existing* `std` values. That may overstate epistemic uncertainty (std=0.50 on mean=1.50 is a 33% CV applied
   watershed-wide). A defensible alternative: a smaller literature-derived uncertainty on the *mean*, with field
   heterogeneity modelled separately. **I did not resolve this.**
3. **§5.2 — my reading of the ECCC numbers is a reconstruction from the manuscript's own text.** The Fanshawe
   cross-check is solid arithmetic and rules out the 84 t/yr basis, but *what the 84 t/yr figure actually
   measures* is unresolved. **The owner must check the primary ECCC source.** I could not access it.
4. **The probability estimates I gave the owner** (≈50% JGLR acceptance, ≈85% eventual publication on the ladder)
   are **judgment, not measurement.** Do not build plans on them.

---

## 9. OWNER CONTEXT THAT AFFECTS HOW YOU SHOULD WORK WITH HIM

- **Sole author, undergraduate, first real submission.** He systematically **undervalues his own work.**
- **This is not vibes — it is visible in the manuscript itself.** Every error we found runs in the direction of
  making his own findings look *weaker*: a p=10⁻⁵³ result written as "not distinguishable"; a strategy that wins
  on both axes written as "worse"; a denominator that makes his gap look 4× smaller than it is; a bioavailability
  metric computed and then not reported. **Random error goes both ways. His does not.**
- Practical implication for a gate: **when he hedges, check whether the hedge is warranted.** It often isn't.
- He asked for this split explicitly: **GPT-5.6 gates architecture, Claude implements.** Respect that. Do not
  let implementation decisions (especially §5.1) slide through without a call.
- Communication: **Chinese, concise, conclusion-first.** Give options, not essays.
