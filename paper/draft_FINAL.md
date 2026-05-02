# Risk-Participation Inversion Limits Spatial Targeting of Agricultural Phosphorus Subsidies in the Thames River Watershed

**Zhenyu Zhou**
Geospatial Data Science, Faculty of Environment, University of Waterloo

---

## Abstract

Voluntary cost-share subsidies are the primary instrument for reducing agricultural phosphorus loading to Lake Erie, yet the 40% reduction target remains unmet. We evaluate four alternative subsidy allocation designs against a first-come-first-served (FCFS) baseline for the Upper Thames River watershed using a spatially-explicit simulation of 8,949 agricultural fields under real policy constraints ($75,000/farm cap, voluntary participation). The model incorporates a participation filter reflecting the inverse relationship between phosphorus risk and farmer engagement: high-risk fields (25% of agricultural area) contributing 57% of phosphorus loading are operated by farmers with the lowest participation rates (~30%). All four alternative designs — spatial targeting, premium pricing, bioavailability-weighted pricing, and a moderate efficiency-pricing variant — performed equal to or worse than first-come-first-served random allocation. By the program's fourth year (its mature operational stage), the model projects approximately 43 tonnes/year of phosphorus reduction (67% of the 64 t/yr target before calibration adjustment; ~22%, or 14 t/yr, after applying the 3.1× calibration adjustment to UTRCA Year 1 observations — see §3.5; in average precipitation years, 38-49 tonnes uncalibrated). A two-dimensional participation rate sweep identifies the crossover boundary: spatial targeting requires both high-risk and low-risk participation above 60%, far exceeding observed voluntary engagement. Variance decomposition confirms that precipitation accounts for 99% of outcome variability. The gap to the 40% target is structural: the phosphorus transport chain imposes physical limits, and voluntary participation creates a risk-engagement inversion that no allocation strategy can overcome.

---

## 1. Introduction

In August 2014, a toxic algal bloom in western Lake Erie contaminated the drinking water supply of Toledo, Ohio, leaving approximately 500,000 residents in the Toledo metropolitan area without safe drinking water for more than two days (Steffen et al., 2017). The crisis was not an isolated event. Harmful algal blooms (HABs) driven by excess phosphorus loading have occurred in Lake Erie with increasing frequency and severity since the mid-2000s, causing an estimated $272 million in equivalent annual costs over a 30-year period through impacts on drinking water treatment, commercial fisheries, recreational tourism, and lakefront property values (Smith et al., 2019).

The primary driver is agricultural nonpoint source phosphorus. Nonpoint sources account for approximately 72% of Canadian phosphorus loading to Lake Erie averaged over 2010–2024 (ranging from 47% in low-load years to 83% in high-load years) and up to 90% in the western basin, with over 80% of the 2008–2022 Canadian nonpoint-source load originating from four priority agricultural tributaries — of which the Thames is the largest (Environment and Climate Change Canada, 2024, *Canadian Environmental Sustainability Indicators: Phosphorus loading to Lake Erie*). Unlike point sources such as wastewater treatment plants — which can be regulated through discharge permits — nonpoint agricultural sources are diffuse, episodic, and legally resistant to direct regulation under Canadian law. This asymmetry has made voluntary best management practice (BMP) adoption, incentivized through cost-share subsidies, the dominant policy instrument for agricultural phosphorus reduction in Ontario.

In February 2016, under the Annex 4 framework of the 2012 Great Lakes Water Quality Agreement Protocol (Canada & United States, 2012), Canada and the United States formally adopted a binational target to reduce phosphorus loading to Lake Erie's western and central basins by 40% from 2008 baseline levels — a reduction of 212 tonnes per year from Canadian sources (Governments of Canada and the United States, 2016). The 2016 announcement specifies, for priority watersheds including the Thames, a 40% reduction in *spring* total phosphorus and soluble reactive phosphorus loads. The Thames River, southwestern Ontario's largest tributary to Lake Erie, contributes approximately 30% of Ontario's agricultural phosphorus load (estimated from ECCC 2024 priority-tributary reporting; Thames carries ~84 of ~280 t/yr from the four priority tributaries, ≈30%), implying a Thames-specific annual reduction responsibility of roughly 64 tonnes per year (author's derivation: 212 t/yr × 0.30 share; used here as a convenient annual-basis benchmark, not identical to the 2016 announcement's spring-season metric). To meet this target, the Upper Thames River Conservation Authority (UTRCA) received $17.41 million from the Canada Water Agency in 2024 to fund a four-year Phosphorus Reduction Program offering cost-share subsidies for cover crops ($30/acre), reduced tillage ($30/acre), subsurface phosphorus placement ($20/acre), and manure management ($50/acre) (UTRCA, 2024). A parallel $13 million program operates in the Lower Thames through the LTVCA.

Despite these investments, the 2024 Canada-Ontario Lake Erie Action Plan Evaluation Report concluded that the 40% phosphorus reduction target has not been achieved, with no clear downward trend in annual loads (ECCC & OMECP, 2024). On the Michigan side of the basin, a 2025 assessment similarly found that a decade of conservation programs and millions of dollars in spending had failed to produce measurable reductions in phosphorus loading to Lake Erie's western basin (Bridge Michigan, 2025, news report citing Michigan EGLE assessment; the underlying EGLE document was not publicly accessible at the time of submission). These outcomes raise a fundamental question: is the shortfall a matter of program design — specifically, how subsidies are allocated across the landscape — or does it reflect structural limits inherent to the voluntary subsidy framework itself?

This study addresses this question through a spatially-explicit stochastic simulation of BMP adoption in the Upper Thames watershed. Unlike previous spatial suitability assessments that identify where BMPs should be placed (Mirnasl et al., 2024) or econometric studies that estimate adoption determinants (Palm-Forster et al., 2017), our approach integrates spatial targeting, farmer adoption behavior, and phosphorus transport dynamics within a single simulation framework. We model 8,949 individual agricultural fields derived from the AAFC Annual Crop Inventory (2024), each characterized by soil properties, phosphorus loss risk, and spatial position within the watershed. Five subsidy allocation strategies are compared under the real policy constraints of the UTRCA program: first-come-first-served (the current approach, serving as the baseline), naive spatial targeting with premium subsidy rates for high-risk fields, smart spatial targeting with uniform rates but risk-based prioritization, bioavailability-weighted pricing that redirects subsidies toward dissolved phosphorus reduction, and a moderate efficiency-pricing variant with a less aggressive bioavailability ratio.

The contribution of this work is threefold. First, it provides the first spatially-explicit simulation of BMP adoption decision-making calibrated specifically to the Upper Thames watershed, incorporating a two-stage decision architecture (participation willingness followed by adoption evaluation) that captures a hypothesized inverse relationship between phosphorus risk and program engagement, supported by indirect evidence and tested via the 2D sensitivity sweep (§5.6). Second, it traces phosphorus through the full transport chain — from field application through mobilization, surface and subsurface pathways, delivery, and bioavailability — to identify precisely where subsidized BMPs lose effectiveness. Third, under the behavioral assumptions tested, it shows that four distinct allocation redesigns all fail to outperform random allocation, revealing a risk-participation inversion in which the fields contributing the most phosphorus are operated by the farmers least likely to engage with voluntary programs.

---

## 2. Phosphorus Transport Framework

Before describing the simulation framework (Section 4), we first establish the phosphorus transport chain that defines where BMP subsidies can—and cannot—intervene. This framework provides the interpretive context for understanding the model results.

Agricultural phosphorus (P) reaches Lake Erie through a multi-step transport chain (Figure 1). Each step attenuates, transforms, or redirects phosphorus, and each represents a potential — or impossible — intervention point for best management practices. This section traces a kilogram of applied phosphorus from field to lake, quantifying losses and BMP interception potential at each stage. Understanding this chain is essential for interpreting why voluntary subsidy programs achieve less than their targets suggest.

### 2.1 Sources: Current-Year Application vs. Legacy Accumulation

Phosphorus enters agricultural fields through two channels: current-year application (fertilizer and manure) and release from legacy soil phosphorus accumulated over decades of over-application.

**Current-year application losses** are modest relative to total inputs. In Ontario's intensive agricultural systems, approximately 10% of net anthropogenic phosphorus input (NAPI) is exported to rivers, averaged across multiple years (1974–1992) in Lake Erie watersheds (Han et al., 2011; 6 of 24 watersheds in that study are in the Erie basin). For the Upper Thames watershed, where approximately 233,300 ha of cropland receives annual fertilizer and manure applications (123,813 ha row crops + 109,473 ha forage; see §3.2), this translates to roughly 40-60 tonnes of current-year P reaching the river system annually — a fraction of the 80-670 tonnes observed in total annual loads.

**Legacy phosphorus** represents the larger and more intractable source. Decades of phosphorus surplus application have accumulated substantial legacy phosphorus stocks in Ontario agricultural soils, and Ontario's Phosphorus Index requires mandatory calculation whenever soil Olsen P exceeds 30 mg/kg (OMAFA, 2022). Drawdown of legacy soil phosphorus in high-STP systems occurs slowly: depending on soil test P level and crop removal, yields can be sustained for several years to more than a decade without new fertilizer application, and large global stocks of accumulated soil P are projected to persist for much longer (Rowe et al., 2016, and references therein). This legacy stock continues to release phosphorus through both surface runoff and subsurface drainage regardless of current management practices.

**Implication:** Type B BMPs can reduce current-year application losses but cannot address legacy phosphorus, setting a fundamental ceiling on fertilizer management effectiveness.

### 2.2 Mobilization: Precipitation as the Master Variable

Phosphorus is immobile without water. No rainfall, no runoff, no phosphorus transport. This makes precipitation the single most important variable governing annual phosphorus loads — and the single largest source of noise obscuring BMP effectiveness signals.

The Thames River's annual phosphorus load varies from approximately 80 tonnes in dry years to over 670 tonnes in wet years — an 8-fold range driven almost entirely by precipitation and discharge volume (Environment and Climate Change Canada, 2024). This variability is not uniformly distributed throughout the year: edge-of-field measurements at southern Ontario agricultural sites show that approximately 80% of runoff occurs during the non-growing season (October to April), with spring snowmelt dominating transport (Van Esbroeck et al., 2017). Critically, 10-15% of flow days can carry over 60% of the annual phosphorus load, concentrating transport into a small number of high-intensity events (Van Rossum & Norouzi, 2021).

This temporal concentration has two consequences for BMP programs. First, the effectiveness of surface BMPs (Type A: cover crops, reduced tillage) is seasonally constrained. Cover crops planted after fall harvest provide ground cover during autumn rains but are dormant or dead during the critical spring snowmelt period when the majority of phosphorus transport occurs. Second, the inter-annual signal of BMP adoption is structurally undetectable against precipitation noise. On the U.S. side of the basin, the River Raisin and Upper Maumee watersheds met their 40% phosphorus reduction targets only once in the five years between 2018 and 2023 — in 2021, an especially dry year — not because of BMP progress but because less water moved less phosphorus (Bridge Michigan, 2025, citing Michigan EGLE assessment).

**Implication:** BMP effectiveness is conditional on precipitation. The policy-relevant signal of adoption improvements is buried within a precipitation-driven noise range of 8x.

### 2.3 Transport Pathways: Surface Runoff vs. Tile Drainage

Phosphorus leaves agricultural fields via two distinct pathways, each carrying a different form of phosphorus and each susceptible to different — or no — BMP interventions.

**Pathway A: Surface runoff** is the dominant transport mechanism for phosphorus in Ontario's clay-rich soils. Field measurement studies reviewed by Macrae et al. (2021) consistently show particulate phosphorus dominating total field-edge losses in these soils, with surface runoff transporting primarily particulate phosphorus (PP) — soil particles with adsorbed phosphorus, including legacy phosphorus from decades of accumulation. Type A BMPs (cover crops, reduced tillage, buffer strips) target this pathway by reducing soil erosion and slowing runoff velocity. Field studies report highly variable reductions in particulate phosphorus from surface protection BMPs, with effectiveness strongly dependent on slope, soil type, storm intensity, and freeze-thaw dynamics (Liu et al., 2019).

However, Type A BMPs exhibit a paradox on clay soils under conservation tillage. While no-till dramatically reduces particulate phosphorus loss, it can simultaneously elevate dissolved reactive phosphorus (DRP) delivery. Jarvie et al. (2017) report a step-change increase in soluble reactive phosphorus (SRP) loads to Lake Erie tributaries since the early 2000s, attributing the change primarily to enhanced soluble P delivery (rather than runoff volume change) linked to expanded reduced-tillage practices and extensive tile drainage that elevate labile P near the soil surface and transmit soluble P through subsurface pathways. This erosion–DRP tradeoff means that the net total phosphorus benefit of Type A BMPs is smaller than the particulate fraction alone would suggest.

**Pathway B: Tile drainage** carries primarily dissolved reactive phosphorus (DRP), accounting for 10-30% of total field-edge losses but with outsized ecological significance. In the Upper Thames watershed, where clay soils and poor natural drainage are prevalent, extensive systematic tile drainage networks provide direct conduits from the root zone to waterways, bypassing any surface BMP intervention. Our soil survey data indicates that approximately 9% of agricultural fields in the Upper Thames have drainage characteristics consistent with tile drainage (drainage score >= 5 on a 6-point scale; 821 of 8,949 fields).

Surface BMPs (Type A) **cannot intercept** the tile drainage pathway. Cover crops may modestly reduce DRP leaching through nutrient uptake, but the primary mechanism of particulate trapping is irrelevant for dissolved phosphorus moving through subsurface drains. Only source reduction — Type B BMPs such as subsurface phosphorus placement, which reduces fertilizer contact with surface water — partially addresses tile drainage losses, and even then with limited effectiveness against legacy soil phosphorus.

**Implication:** The UTRCA program emphasizes Type A BMPs that target surface PP but miss tile drainage DRP entirely. Given DRP's 4x greater bioavailability, the program may reduce total phosphorus while having limited impact on the fraction driving algal blooms.

### 2.4 Delivery: From Field Edge to River

Not all phosphorus leaving a field edge reaches a waterway. Delivery depends on distance to water: fields within 500 m have near-complete delivery, while those beyond 2 km may lose 30-60% to re-deposition. Fanshawe Reservoir retained 25% of incoming phosphorus in 2018 (36 tonnes) and 47% in 2019 (91 tonnes) (Kao et al., 2022). Our P-risk score incorporates distance-to-water (weighted 0.25), but the current UTRCA program does not differentiate by field position.

### 2.5 Bioavailability: What Actually Feeds Algal Blooms

The policy target of 40% phosphorus reduction is defined in terms of total phosphorus (TP). But algal blooms are driven by bioavailable phosphorus — the fraction that algae can directly assimilate — and the two metrics can diverge substantially.

Particulate phosphorus (PP), which constitutes the majority of total field losses, is only partially bioavailable: direct NaOH-extraction measurements on Maumee, Sandusky, and Cuyahoga river PP report 26-30% biologically available P (Baker et al., 2014). The EPA Annex 4 Task Team (US EPA, 2015) uses ~50% PP bioavailability as a single-value assumption in its loading-target analysis, which sits substantially above these direct field measurements; higher estimates (up to roughly 50%) arise from algal-assay approaches on other rivers and time periods. The remainder of PP is locked in mineral structures that resist biological uptake on policy-relevant timescales. Dissolved reactive phosphorus (DRP), though a smaller fraction of total losses (10-30%), is considered essentially 100% bioavailable and immediately accessible to cyanobacteria upon reaching the lake.

Combining these fractions under conservative assumptions on the PP bioavailability (25%): for a field losing 80% PP and 20% DRP, the effective bioavailable contribution is PP(0.80) x 0.25 + DRP(0.20) x 1.0 = 0.20 + 0.20 = 0.40, or 40% of total phosphorus. Even with PP assumed at its lower-bound bioavailability, the bioavailable fractions of PP and DRP are roughly equal despite the 4:1 ratio in total mass. This means that a BMP reducing PP by 50% achieves at most half the algal bloom benefit of a BMP reducing DRP by the same absolute amount.

This distinction is not academic. Jarvie et al. (2017) document a step-change increase in soluble reactive phosphorus loads to Lake Erie tributaries since the early 2000s, attributing the change primarily to enhanced soluble P delivery (rather than runoff volume change) linked to expanded reduced-tillage practices and extensive tile drainage. The aggregate implication is that BMPs and land-use changes that improve the total phosphorus metric can simultaneously worsen the ecologically relevant one.

**Implication:** Our model reports both total phosphorus reduction and bioavailable phosphorus reduction (PP_reduced x 0.25 + DRP_reduced x 1.0) to distinguish between these metrics, as they can lead to divergent assessments of policy effectiveness.

### Summary: The Transport Chain as a Series of Leaks

Table 1 synthesizes the transport chain, quantifying each step and identifying where BMPs can — and cannot — intervene.

| Transport Step | Quantity | BMP Intervention | Effectiveness | Structural Limit |
|---|---|---|---|---|
| Source: current-year P application | ~10% of NAPI reaches waterways (Han et al., 2011) | Type B: reduce application losses | Moderate (50-88% DRP reduction) | Cannot address legacy soil P accumulated across Ontario's P-Index-regulated soils |
| Source: legacy soil P | Decades of surplus accumulation; drawdown spans years to more than a decade | None available | Zero | Fundamental ceiling on BMP effectiveness |
| Mobilization: precipitation | 8x inter-annual variation (80-670 t/yr) | None | Zero | BMP signal undetectable against precipitation noise |
| Pathway: surface runoff (PP) | 70-90% of field loss | Type A: cover crop, no-till | 30-60% PP reduction (high-risk fields) | Spring snowmelt timing; erosion-DRP tradeoff on clay soils |
| Pathway: tile drainage (DRP) | 10-30% of field loss | Type A: zero; Type B: partial | Limited | Surface BMPs cannot intercept subsurface flow |
| Delivery: field to river | Distance-dependent (25% in 2018 / 47% in 2019 retained by Fanshawe Reservoir; Kao et al., 2022) | Buffer strips (not in UTRCA program) | Variable | No spatial differentiation in current subsidy design |
| Bioavailability: PP | 25% feeds algae (conservative; Baker et al., 2014 report 26-30%) | Indirect via PP reduction | Partial | 75% of PP reduction has no algal benefit |
| Bioavailability: DRP | 100% feeds algae | Type B partially addresses | Partial | Step-change rise in riverine SRP since early 2000s despite stable TP |

This framework reveals that voluntary BMP subsidies operate on a narrow slice of the transport chain — primarily surface runoff of particulate phosphorus — while leaving legacy sources, precipitation variability, tile drainage losses, and bioavailability dynamics largely unaddressed. The model results in Section 5 quantify the aggregate consequence of these structural constraints.

---

## 3. Study Area and Data

### 3.1 Upper Thames River Watershed

The Upper Thames River watershed encompasses approximately 3,482 km2 of southwestern Ontario, draining through the City of London and discharging into Lake St. Clair, which connects to Lake Erie's western basin. The watershed is 72% agricultural, dominated by corn-soybean-winter wheat rotations on clay-rich soils, with approximately 3,600 farm operations (Statistics Canada, 2022). The Upper Thames is managed by the Upper Thames River Conservation Authority (UTRCA), which operates water quality monitoring, stewardship programs, and the Phosphorus Reduction Program analyzed in this study.

Annual phosphorus loading from the Upper Thames varies from approximately 80 to 670 tonnes depending on precipitation, with a long-term mean near 300 tonnes (Environment and Climate Change Canada, 2024). The UTRCA's 2022 Watershed Report Cards assessed 28 subwatersheds for surface water quality, with only 5 of 28 meeting phosphorus concentration targets (UTRCA, 2022). The watershed's soils are predominantly clay and clay loam (poorly drained Luvisols and Gleysols), creating conditions that favor both surface runoff and extensive tile drainage installation.

### 3.2 Spatial Data Sources

**Agricultural field boundaries.** Individual agricultural fields were delineated from the AAFC Annual Crop Inventory 2024, a national 30-meter resolution crop classification product derived from Landsat-8/9, Sentinel-2, and RADARSAT Constellation Mission imagery (AAFC, 2024). Within the Upper Thames boundary, the crop inventory identified 8,949 contiguous agricultural field polygons after filtering to crop classes only (excluding forest, urban, water, and wetland pixels) and removing fields smaller than 2 hectares. Each field retains its classified crop type across three categories: row crops (corn, soybean, wheat — 4,812 fields, 123,813 ha), forage/pasture (alfalfa, managed grassland — 4,059 fields, 109,473 ha), and minor/specialty crops (78 fields, 616 ha). The mean field size is 26.1 ha (median 14.4 ha), consistent with Ontario's field-level agricultural structure.

**Soil properties.** Soil drainage class, slope class, and texture were obtained from the Ontario Soil Survey Complex (Ontario Ministry of Agriculture, Food and Rural Affairs), a province-wide 1:50,000 vector dataset compiled from county-level soil surveys conducted since 1929. Each field polygon was assigned soil attributes through spatial join with the underlying soil survey polygons based on field centroid location. Drainage class was converted to a 1-6 numeric score (1=rapid to 6=very poorly drained); slope class was converted to approximate slope percentage using midpoint values (B=1%, C=3.5%, D=7%); and soil texture was classified as sandy (1), medium (2), or clay (3) based on USDA textural class groupings.

**Hydrographic network.** Distance from each field to the nearest watercourse was computed using the Ontario Hydro Network (OHN) Watercourse layer, a provincial vector dataset of natural and constructed surface water features (Ontario Ministry of Natural Resources and Forestry, 2019). Within the Thames study area, the OHN contains 1,904 watercourse segments. The mean distance from field centroids to the nearest waterway is 1,886 m.

**Tile drainage.** Fields with soil drainage scores of 5 or higher (poorly to very poorly drained) were flagged as likely tile-drained, consistent with Ontario agricultural practice where systematic tile drainage is installed on clay soils with inadequate natural drainage. This proxy identified 821 fields (9% of total) as tile-drained, a conservative estimate. Independent estimates indicate substantially higher actual tile drainage prevalence in the Thames system — the City of London One River Environmental Assessment (2020) reports approximately 58% artificially drained area watershed-wide, and UTRCA (2022) Watershed Report Cards show agricultural field-tile coverage ranging from roughly 33% (Pottersburg Creek, a largely urbanized subwatershed where urban drainage adds a further ~38%) to 66% (Whirl Creek, predominantly agricultural). Our proxy therefore captures only the most poorly drained fields as a lower bound; actual tile drainage extent is likely substantially higher, which would further reduce the effectiveness of surface BMPs across the watershed.

### 3.3 Phosphorus Risk Score

A composite phosphorus loss risk score was computed for each field using a weighted combination of four spatial factors:

P_risk = 0.30 x S_drainage + 0.25 x S_slope + 0.25 x S_proximity + 0.20 x S_texture

where S_drainage is the normalized drainage score (poorly drained = higher risk of surface runoff), S_slope is the normalized slope percentage (steeper = faster runoff), S_proximity is the inverse normalized distance to the nearest waterway (closer = higher delivery probability), and S_texture is the normalized clay content score (more clay = less infiltration, more runoff). Weights were assigned based on relative factor importance rankings in the Ontario Phosphorus Index (OMAFA, 2022) and the site suitability framework of Mirnasl et al. (2024). Raw scores were normalized to 0-100 and classified into three risk categories using tercile-based thresholds derived from the empirical distribution of all field scores: Low (< 34.2), Medium (34.2-40.0), and High (> 40.0). The resulting classification assigns 2,038 fields (23%) as High risk, 4,058 (45%) as Medium, and 2,853 (32%) as Low.

### 3.4 UTRCA Program Parameters

The model replicates the policy constraints of the UTRCA Thames River Phosphorus Reduction Program as documented in program guidelines (UTRCA, 2024). The complete parameter set is summarized below:

**UTRCA Phosphorus Reduction Program Parameters**

| Parameter | Value | Source |
|-----------|-------|--------|
| Annual program budget | $4.35 million | $17.41M / 4 years |
| Per-farm total subsidy cap | $75,000 over program duration | UTRCA program rules |
| Type A subsidy (cover crop, reduced tillage) | $30/acre | UTRCA 2025 rates |
| Type B subsidy (subsurface P placement) | $20-30/acre | UTRCA 2025 rates |
| Manure management subsidy | $50/acre (capped at $10,000) | UTRCA 2025 rates |
| Subsurface P placement cap | $15,000 per farm | UTRCA 2025 rates |
| Combination bonus (A+B in same year) | $10/acre | UTRCA 2025 rates |
| Allocation method | First-come-first-served | Current practice |

### 3.5 Calibration Targets

The model was calibrated against UTRCA Year 1 program outcomes (2024-2025): over 595 on-the-ground projects across more than 35,000 acres, with an estimated annual phosphorus reduction of 5.7 tonnes (UTRCA, 2025). Because the model operates at field level (8,949 agents) rather than farm level (~3,600 operations), direct matching of project counts requires conversion: the observed 595+ farm-level projects correspond to approximately 1,200-1,500 field-level adoption events assuming 2-2.5 fields per farm.

The model employs a two-stage decision architecture. First, a **participation filter** determines which farmers are willing to engage with the subsidy program at all: estimated at 55% for low-risk, 45% for medium-risk, and 30% for high-risk farmers. These rates represent a working hypothesis of an inverse relationship between phosphorus risk and voluntary program engagement; supporting evidence is presented in Section 5.2, and full sensitivity to these assumptions is mapped by the two-dimensional parameter sweep in Section 5.6. Second, participating farmers evaluate specific BMP offers through the logistic **adoption function**. With intercept calibrated to -2.00 and participation filter active, the model produces approximately 1,080 field-level adoptions in Year 1 under FCFS — consistent with the expected range after field-to-farm conversion. Budget utilization (86%) falls within the observed UTRCA range (52-100%).

As an independent validation check, the calibrated model predicts Year 1 phosphorus reduction of approximately 17.6 tonnes under FCFS with participation filter, compared to UTRCA's reported 5.7 tonnes (a 3.1x overestimate). This discrepancy reflects the model's use of literature-derived BMP effectiveness rates that are higher than UTRCA's conservative field-level estimates, combined with the higher per-acre phosphorus loss rates implied by the 80:20 particulate-to-dissolved partitioning. The overestimate affects absolute values but not relative strategy comparisons, which are the study's primary output. Because the overestimate is multiplicative and applies uniformly across strategies, the relative ranking and percentage differences between strategies are preserved under rescaling. We separately validate the relative ranking by checking that strategy improvement percentages are robust to multiplicative rescaling: dividing all strategy outputs by 3.1 preserves the +2.0% / -1.6% / -60.4% / -52.2% relative differences exactly. The strategy comparison conclusion thus does not depend on the absolute calibration accuracy.

Results are interpreted at two distinct layers: a **simulation layer** (adoption dynamics, phosphorus reduction, cost) where the model directly tracks outcomes, and an **interpretation layer** (additionality correction, bioavailability weighting) where post-hoc analytical adjustments translate raw outputs into policy-relevant metrics. The sensitivity analysis (Section 5.6) confirms that interpretation-layer parameters do not affect the simulation dynamics or strategy comparison, ensuring that the core findings are independent of these analytical choices.

---

## 4. Methods

### 4.1 Simulation Design

Each of the 8,949 agricultural fields in the Upper Thames watershed is represented as a spatial unit with the following attributes: area (hectares), crop type (row crop or forage), composite P-risk score, risk classification (High/Medium/Low), soil drainage score, slope percentage, clay content score, distance to nearest waterway, tile drainage flag, and current BMP adoption state. Spatial units are initialized with 27% pre-adopted Type A BMPs (matching the 2021 Census of Agriculture cover crop adoption rate for Ontario; Statistics Canada, 2022). Initial adoption was assigned by sorting fields by P-risk score (ascending) and marking the lowest-risk 27% as pre-adopted. This assignment embeds our working hypothesis that baseline voluntary adoption concentrates in lower-risk operations where behavioral and technical barriers to conservation practices are lowest; we note that the Prokopy et al. (2019) meta-analysis reports positive associations between "vulnerable land" and adoption in some contexts, and the sensitivity of our results to this initialization assumption is tested in Section 5.6.

**Adoption decision function.** Each year, agents offered a subsidy decide whether to adopt based on a logistic adoption probability function parameterized from the agricultural economics literature:

P(adopt) = 1 / (1 + exp(-(a + b * net_benefit + c * area + e * neighbor_rate)))

where net_benefit is the subsidy minus BMP implementation cost plus long-term soil benefits ($/acre, annual undiscounted; see Appendix A), area is the field size in acres, and neighbor_rate is the fraction of spatially adjacent fields that have already adopted. The info_access term present in some adoption models (Palm-Forster et al., 2017) was omitted as it was set to a constant value in all simulations and absorbed into the intercept. The intercept (a = -2.00) and subsidy coefficient (b = 0.01) were calibrated via grid search to approximate UTRCA Year 1 participation rates under the two-stage decision architecture (participation filter followed by adoption evaluation). The grid search varied intercept ∈ [-4.00, -1.25] in 0.25 increments (12 values) and subsidy_coeff ∈ [0.010, 0.055] in 0.005 increments (10 values), totaling 120 combinations; the objective minimized a weighted sum of squared relative errors against three UTRCA Year 1 targets (new projects = 595, new acres = 35,000, P reduction = 5.7 t), with weights 2 : 1 : 2 on projects : acres : P reduction. Calibration was conducted at the lower bound of the $20-30/acre subsurface range (subsidy_b = $20/acre); the selected intercept was subsequently validated at the production setting (subsidy_b = $30/acre) via `pilot_participation.py` against the observed 86% Year 1 budget utilization. Full re-calibration against all three UTRCA Year 1 targets (595 projects, 35,000 acres, 5.7 t P) at production subsidy was not conducted; aggregate program throughput is dominated by participation-filter constraints (§5.2) rather than by subsidy-rate variation within the $20-30 subsurface placement range. See `src/model/calibrate.py` for the complete procedure. The area coefficient (c = 0.002 per acre, modeling assumption) introduces a weak farm-size effect on adoption probability. The peer effect coefficient (e = 1.5) and maximum adoption probability ceiling (0.85) are modeling assumptions informed by the general finding that social influence and practice complexity affect adoption rates (Liu et al., 2018; Prokopy et al., 2019), calibrated to produce realistic adoption dynamics under the participation filter. BMP implementation costs are $25/acre for Type A (lower midrange of the $10-50/acre range reported in OMAFA 2025 Publication 60, reflecting common cover crop / reduced-tillage practice cost) and $35/acre for Type B (midpoint of the $20-50/acre range). Long-term soil benefits are estimated at $5/acre/year for Type A, $3/acre/year for Type B, and $10/acre/year for combined (Type A + Type B) adoption (capturing the synergy bonus of complementary practices). These benefits are treated as constant annual income streams added to the subsidy in the net benefit calculation, not discounted over the 4-year program window; this approximation is consistent with the model's medium-term decision horizon.

**Adoption function coverage.** The logistic adoption function captures economic drivers (subsidy, cost, farm size) and social influence (peer effect), but these factors explain only a portion of real-world adoption decisions. The 2020 Ontario Cover Crop Feedback Report documents that non-adopters of cover crops cite multiple barriers (multi-select): additional costs (41%), lack of equipment (36%), late grain harvest preventing planting (29%), not knowing where to start (24%), and shortness of the growing season (23%) (GFO, 2021). Cost is the single most-cited barrier, which subsidies can partially address; however, the four non-economic barriers together indicate substantial uptake friction that subsidy amount and spatial allocation cannot directly resolve. The model's adoption function therefore represents an upper bound on subsidy-responsive behavior; actual adoption rates may be lower due to these non-economic constraints.

**Spatial neighbor graph.** Adjacency is defined by a 500-meter buffer around each field polygon, computed using spatial join rather than pairwise comparison for computational efficiency. Neighbors are capped at 15 per field to prevent over-connected graphs in areas of high field density. The resulting graph has a mean degree of 11.6, consistent with realistic social network density in agricultural communities.

**Temporal dynamics.** The simulation runs for four years (matching the 2024-2028 UTRCA program period). Adoption decisions are made annually, with BMP status carrying over between years — a field that adopts cover crops in Year 1 retains that status in Year 2 and is not re-offered the same subsidy. Peer effects accumulate across years as more neighbors adopt, creating potential adoption cascades in spatially clustered high-risk areas.

**Adoption noise specification.** Adoption noise is applied to the probability output post-sigmoid (N(0, 0.3)), then clipped to [0, max_adoption_prob = 0.85]. This differs from latent-logit noise conventions but was retained for consistency with the calibrated parameter set.

### 4.2 Policy Constraints

The model replicates six policy constraints from the UTRCA program: (1) an annual program budget of $4.35 million; (2) a per-farm total subsidy cap of $75,000 over the four-year program; (3) per-category caps for Type B BMPs (manure management: $10,000 per farm; subsurface phosphorus placement: $15,000 per farm); (4) a $10/acre combination bonus for fields adopting both Type A and Type B in the same year; (5) an administrative feasibility floor that rejects offers when the $75,000 per-farm cap reduces the effective per-acre subsidy below $5/acre (consistent with conservation-program practice that subsidies below a minimum threshold are not processed); and (6) first-come-first-served allocation under the baseline strategy. The model's coarse-grained Type B BMP representation does not distinguish manure management from subsurface placement, so the two per-category caps in (3) are aggregated to a single per-farm Type B cap of **$12,500** (the mean of $10,000 and $15,000) in simulation. The strategy comparison is unaffected because all strategies operate under the same averaged cap; absolute uptake of subsurface vs manure is not resolved by the model. When an offer exceeds a field's remaining cap, the subsidy is reduced proportionally, and the adoption probability is recalculated at the reduced effective rate.

The $10/acre combo bonus is paid post-adoption when a farm elects both Type A and Type B BMPs, but does not enter the adoption probability calculation ex ante. In the model, farmers decide based on the base subsidy alone and receive the combo bonus as additional compensation if they adopt both categories. This likely underestimates combined-BMP uptake relative to a specification where farmers anticipate the bonus.

### 4.3 Allocation Strategies

We compare the current UTRCA baseline (FCFS) against four alternative allocation designs, each modifying a different dimension of program design to isolate its effect:

**First-Come-First-Served (FCFS).** The current UTRCA policy. Fields are offered subsidies in random order each year. All risk levels are eligible. Subsidy rates are uniform: $30/acre for Type A, $30/acre for Type B (upper bound of the subsurface P placement range, $20-30/acre; see §4.2 for the model's aggregation of manure and subsurface caps), $60/acre for both. This strategy serves as the baseline.

**Naive Hotspot.** Fields are ordered by P-risk score (highest first). High-risk fields receive premium subsidies ($50/acre per BMP type, $100/acre for both); medium-risk fields receive standard rates; low-risk fields receive nothing. Tests whether concentrating higher payments on the riskiest fields improves outcomes.

**Smart Hotspot.** P-risk ordering identical to Naive Hotspot, but subsidy rates kept identical to FCFS ($30 A, $30 B). Low-risk fields receive nothing. Isolates the pure effect of spatial prioritization from differential pricing.

**Efficiency Pricing.** Random ordering identical to FCFS, but subsidy rates restructured by bioavailability: $15/acre for Type A (targeting 25%-bioavailable particulate P) and $60/acre for Type B (targeting 100%-bioavailable dissolved P). Type B is offered first. Isolates the effect of price signals from spatial ordering, testing whether redirecting subsidies toward more ecologically impactful BMPs improves outcomes.

**Moderate Efficiency Pricing.** Identical random ordering to FCFS, with moderated price tilt: $25/acre for Type A, $40/acre for Type B. Tests whether the efficiency-pricing result is robust to a less aggressive subsidy ratio than the baseline Efficiency Pricing variant.

These strategies are designed to span the variation possible *within* the existing UTRCA voluntary cost-share framework (random/risk ordering × uniform/premium pricing). They do not include auction mechanisms, performance-based contracts, or mandatory baseline + voluntary top-up designs, all of which would require fundamentally different model structures and are identified as future work (Section 7). Our finding therefore establishes that *within* the current UTRCA framework, allocation optimization cannot close the gap—not that *no possible policy mechanism* can.

### 4.4 Transport Chain Enhancements

The model extends standard simulation approaches with four transport chain features that capture mechanisms typically absent from adoption-focused models:

**Precipitation variability.** Annual phosphorus loads are scaled by a precipitation multiplier drawn from a log-normal distribution (mu = -0.18, sigma = 0.6), calibrated so that the expected value equals 1.0 and the 95% range (0.26-2.71) approximates the observed 3-8x variation in Thames River annual loads. Each simulation year receives an independent precipitation draw, and different Monte Carlo runs experience different four-year precipitation sequences.

**Particulate-dissolved partitioning.** Total phosphorus loss at each field is partitioned into particulate phosphorus (PP, 70-90% of total, mean 80%) and dissolved reactive phosphorus (DRP, 10-30%, mean 20%), reflecting particulate-to-dissolved ratios from Ontario edge-of-field measurements (Van Esbroeck et al., 2017) as further reviewed by Macrae et al. (2021). Type A BMPs reduce PP through erosion control; Type B BMPs reduce DRP through source management. This partitioning is critical because the two fractions have different bioavailability and respond to different BMPs.

**Tile drainage penalty.** For the 821 fields flagged as tile-drained (drainage score >= 5), Type A BMP effectiveness against particulate phosphorus is reduced by 50%. Subsurface drainage diverts a substantial fraction of water below the soil surface, reducing the volume of surface runoff that surface BMPs (cover crops, reduced tillage) can intercept; Type A therefore captures less PP on tile-drained fields. Type B effectiveness is unaffected. Note that DRP losses through tile drains are not addressed by Type A in any scenario (tile-drained or not) — they are reduced only by Type B's effect on source application losses.

**Additionality correction.** Each field has a baseline adoption probability representing the likelihood of adopting BMPs without any subsidy (Low-risk: 0.40, Medium: 0.20, High: 0.10), informed by USDA Economic Research Service estimates showing that non-additionality varies substantially by practice type — approximately 46% for conservation tillage, lower (~12%) for nutrient management, and about 20% for buffer/filter strips (Claassen et al., 2014). When a field adopts in the simulation, a secondary random draw determines whether the adoption was additional (would not have occurred without the subsidy) or a free rider (would have adopted regardless). Only additional adoption is counted toward net policy effect.

### 4.5 Monte Carlo Design

Each strategy is evaluated across 1,000 independent simulation runs. Within each run, the following parameters are stochastically sampled: base phosphorus loss rates (normal distribution with literature-derived means and standard deviations for each risk level), BMP effectiveness rates (normal, clipped to 0.05-0.95), particulate-to-dissolved ratio (uniform, 0.70-0.90), annual precipitation multiplier (log-normal, per year), adoption function noise (normal, sigma = 0.3), and additionality baseline draws (Bernoulli per adoption event). Stochastic sampling occurs at different temporal and spatial granularities: the precipitation multiplier is sampled per-year-per-run; BMP effectiveness rates and base phosphorus loss rates are per-farm-per-detailed-metrics-call; adoption function noise is per-adoption-decision; additionality draws are per-adoption-event. This heterogeneity is reflected in the variance decomposition (§5.7). Results are reported as means with **95% empirical ranges** (the 2.5th and 97.5th percentiles of the 1,000-run Monte Carlo distribution). These ranges characterize the spread of simulated outcomes rather than sampling uncertainty of the mean; the mean itself is estimated to within ± ~1.7 t/yr 95% CI under n=1,000 given the observed variance.

Random seeds are deterministic for reproducibility: the main 5-strategy comparison uses seeds 1000-1999; variance decomposition uses seeds 8000-8999; pilot calibration and sensitivity analyses use fixed seeds documented in `src/analysis/*.py`. All reported results can be regenerated from these seed ranges.

Monte Carlo runs were executed in parallel on 14 CPU cores. The main 5-strategy comparison (5,000 simulations) required approximately 2.6 hours wall-clock time; the variance decomposition (3 × 1,000 runs) required an additional ~30 minutes.

### 4.6 Model Scope Relative to Transport Chain

The simulation models a subset of the phosphorus transport chain described in Section 2. Table 2 summarizes the treatment of each transport step, distinguishing between dynamically modeled processes, static proxies, and acknowledged but unmodeled mechanisms.

**Table 2. Model treatment of phosphorus transport chain steps**

| Transport chain step | Model treatment |
|---------------------|----------------|
| Legacy P source | Acknowledged as effectiveness ceiling; not dynamically modeled |
| Precipitation mobilization | Scalar annual multiplier (LogNormal, mean=1.0) |
| Surface runoff (PP) | Type A BMP effectiveness rates from literature |
| Tile drainage (DRP) | Binary penalty on Type A for poorly drained fields; Type B unaffected |
| Erosion-DRP tradeoff | Not modeled — Type A only reduces PP, no offsetting DRP increase |
| Delivery to river | Static distance-to-water proxy in P-risk score |
| Reservoir retention | Not modeled (Fanshawe 25% in 2018 / 47% in 2019 noted in Section 2) |
| Bioavailability | Post-hoc multiplication (PP x 0.25 + DRP x 1.0) |

The erosion-DRP tradeoff (Section 2.3) is the most consequential unmodeled mechanism: conservation tillage can increase dissolved reactive phosphorus while reducing particulate phosphorus. Omitting this effect means our model may overestimate the net phosphorus benefit of Type A BMPs on clay soils.

---

## 5. Results

### 5.1 Baseline: Strategy Comparison Without Participation Constraints

We first present results without the participation filter to establish a theoretical upper bound. Under the assumption that all farmers are willing to consider subsidized BMPs — differing only in whether they ultimately adopt — Smart Hotspot outperforms FCFS in approximately 96% of OAT sensitivity runs at default parameters; across the OAT cells (full range 83-100%), this win rate remains above 80% for all tested parameters (`results/sensitivity_oat_results.json`). Smart Hotspot achieves +5.8% more phosphorus reduction at lower cost (the constrained-scenario P-reduction advantage reverses in §5.3 Table 3; see §5.4 for explanation. The lower-cost property is preserved even under constrained participation, since Smart Hotspot skips low-risk-farmer offers). However, Naive Hotspot's premium pricing ($100/acre for high-risk fields) rapidly exhausts the $75,000 per-farm cap — by Year 4, dozens of the highest-risk fields are unable to receive full intended subsidies, neutralizing the higher payments. This cap-saturation effect does not appear in the constrained scenario because low adoption among high-risk farmers prevents aggregate subsidy demand from reaching the cap in most fields. These results establish that spatial targeting has theoretical value, but the magnitude is modest even under idealized conditions.

### 5.2 The Participation Constraint

The baseline results assume universal willingness to engage with the subsidy program. In reality, voluntary programs face systematic non-participation. The following participation rates are scenario assumptions informed by indirect evidence (evidence list below), not directly estimated from Ontario program data. The two-dimensional sweep in Section 5.6 maps the sensitivity of all conclusions to these assumptions. We introduce a participation filter reflecting estimated engagement rates: 55% of low-risk farmers, 45% of medium-risk, and 30% of high-risk are designated as willing to engage with the subsidy program. This designation is fixed per simulation run and persists across all 4 years (a non-participant in Year 1 remains non-participant through Year 4), reflecting a stable behavioral disposition rather than year-by-year willingness. These rates represent a working hypothesis that phosphorus risk and voluntary program engagement are inversely related — that farmers on the highest-risk land tend to be those least likely to participate in voluntary conservation programs. We note that this direction contrasts with some U.S. findings where "vulnerable land" ownership has been positively associated with adoption (Prokopy et al., 2019); we treat the Ontario-specific direction as a hypothesis and present indirect supporting evidence below.

Multiple lines of indirect evidence inform these rates. First, the calibrated parameter set jointly produces 86% budget utilization, matching the observed UTRCA range (52-100%) across program years (UTRCA, 2025). We acknowledge this is a joint calibration constraint rather than independent evidence for the participation rates themselves; rate identifiability is addressed by the 2D sweep (§5.6) and the inversion robustness check (item 4 below). Second, the LTVCA's simpler BMP categories (dry phosphorus banding) were fully allocated by June 2025 while more demanding categories remained available, consistent with risk-stratified willingness (LTVCA, 2025, Phosphorus Reduction Program update). Third, the 2020 Ontario Cover Crop Feedback Report (GFO, 2021) documents that non-adopters cite both economic and non-economic barriers in a multi-select survey — additional costs (41%), lack of equipment (36%), late grain harvest preventing planting (29%), not knowing where to start (24%), and shortness of the growing season (23%) — indicating that even after accounting for the cost barrier, substantial non-economic friction limits participation. Fourth, our robustness check inverting rates (High=55%, Low=30%) found that FCFS still outperformed Smart Hotspot (-0.3%), confirming the conclusion is not an artifact of the specific rate estimates.

This filter transforms the results. With participation constraints, FCFS achieves 42.8 tonnes of Year 4 phosphorus reduction — approximately half the unconstrained estimate. More critically, the relative performance of strategies reverses.

### 5.3 Four Alternatives, One Winner

We tested four alternative allocation designs against the FCFS baseline, each modifying a different dimension of program design (Table 3). All four alternatives performed equal to or worse than FCFS under realistic participation constraints.

**Table 3. Strategy comparison under participation constraints (n=1,000 MC runs, 95% empirical range).** p-values in this table are not adjusted for multiple comparisons across the four pairwise tests vs FCFS; effect sizes and 95% empirical ranges are the primary inferential outputs. Under Bonferroni correction (adjusted α = 0.0125), Naive Hotspot's 73% win rate remains significant (binomial p < 0.001), and all negative-improvement strategies have empirical ranges entirely below zero regardless of α choice.

| Strategy | Design change | Total P (t/yr) | vs FCFS (%) | Paired diff (t) [95% empirical range] | Win rate | Cost |
|----------|--------------|----------------|-------------|--------------------------|----------|------|
| **FCFS** | Baseline | **42.8** [10.9, 119.2] | — | — | — | $10.9M |
| Naive Hotspot | Price + spatial | 43.6 [11.3, 119.4] | +2.0% | +0.9 [-1.7, +5.2] | 73% | $9.5M |
| Smart Hotspot | Spatial only | 42.2 [10.4, 118.6] | -1.6% | -0.6 [-4.2, +2.3] | 31% | $8.3M |
| Efficiency ($15A/$60B) | Price only | **16.9** [4.4, 46.3] | -60.4% | -25.9 [-69.3, -6.6] | 0% | $9.4M |
| Moderate Eff ($25A/$40B) | Mild price | **20.4** [5.3, 54.6] | -52.2% | -22.3 [-61.3, -5.8] | 0% | $8.3M |

**Naive Hotspot** wins more frequently than chance (73% win rate, binomial p < 0.001, n=1,000), but the magnitude of the mean advantage (+2.0%, 95% empirical range [-3.8%, +8.5%]) is not statistically distinguishable from zero. Premium pricing may partially compensate for the participation penalty by increasing adoption probability among the few high-risk participants, but the effect is modest and premium pricing rapidly exhausts the $75,000 per-farm cap, limiting scalability.

**Smart Hotspot** fails because spatial prioritization directs offers to high-risk fields first — but with only 30% participation among high-risk farmers, the majority of prioritized offers are declined. FCFS's random allocation achieves broader spatial coverage and more uniform peer effect diffusion. A systematic sweep of high-risk participation rates from 30% to 60% found no crossover point: FCFS outperformed Smart Hotspot at every tested rate (-0.4% to -2.1%), with the gap narrowing but never reversing.

**Efficiency Pricing** ($15/acre Type A, $60/acre Type B) fails catastrophically (-60.4% total P). The intent — redirecting subsidies toward the more ecologically impactful Type B BMPs (targeting 100%-bioavailable dissolved P) — does not translate into Type B adoption (+3.3%) because Type B practices require specialized equipment and process changes that subsidies alone cannot overcome. Meanwhile, the reduced Type A subsidy causes a 27% decline in cover crop adoption, eliminating the dominant source of total phosphorus reduction. A moderate variant ($25A/$40B) fares marginally better (-52.2%) but confirms that any rebalancing away from Type A subsidies reduces overall effectiveness, because the adoption barrier for Type B is non-economic.

### 5.4 Why FCFS Wins

The consistent superiority of random allocation is not an endorsement of the current policy design but a consequence of the participation constraint. Three mechanisms explain the result:

First, **spatial coverage**. FCFS distributes offers across all risk levels, reaching the 55% of low-risk farmers who are most willing to participate. While each individual low-risk adoption produces less phosphorus reduction, the aggregate effect of many small reductions exceeds the concentrated effect of the few high-risk adoptions achievable under targeting.

Second, **peer effect diffusion**. Random allocation seeds adoptions uniformly across the watershed, creating multiple nucleation points for peer-effect cascades. Targeted allocation concentrates seeds in high-risk areas where participation is lowest, producing fewer and more isolated adoption clusters.

Third, **P load concentration vs. participation inversion**. High-risk fields contribute 57% of phosphorus loading from only 25% of agricultural area — the theoretical basis for spatial targeting. But high-risk farmers participate at only 30%, creating an inversion: the fields where targeting would be most valuable are the fields where offers are most likely to be declined.

### 5.5 Gap Analysis

Under the best-performing strategy (FCFS with participation filter), the model produces a mean Year 4 total phosphorus reduction of approximately 43 tonnes — 67% of the 64 t/yr Thames River target (Figure 7), with a 95% empirical range of 11-119 tonnes. Naive Hotspot achieves marginally more (43.6 tonnes, +2.0%) but the difference is not statistically significant (95% empirical range crosses zero: [-3.8%, +8.5%]).

The wide overall empirical range reflects irreducible inter-annual precipitation variability, not model imprecision. When precipitation is fixed at the long-term mean (Section 5.7), the 95% range narrows to [38, 49] tonnes — corresponding to 60-77% of the 64 t/yr target. This conditional estimate provides a more informative assessment of program capacity in an average precipitation year, while the full range accurately represents the year-to-year unpredictability that makes progress toward the 40% target difficult to measure.

If the 3.1x calibration overestimate observed in Year 1 phosphorus reduction persists across all strategies, the calibration-adjusted program achievement would be approximately 14 tonnes/year (22% of target), substantially widening the structural gap. This reinforces rather than weakens the paper's central conclusion, but the precise gap magnitude should be interpreted with caution pending validation against UTRCA's spatial subsidy distribution data.

The gap is structural, not allocative. Four alternative allocation designs — spatial prioritization with premium pricing, spatial prioritization with uniform pricing, bioavailability-weighted pricing, and a moderate efficiency-pricing variant — all failed to improve on random allocation under realistic participation constraints. The binding constraint is not how subsidies are distributed but who is willing to receive them.

### 5.6 Sensitivity Analysis

To assess the robustness of the strategy comparison, we conducted a one-at-a-time (OAT) sensitivity analysis across nine model parameters, varying each within its plausible range while holding others at default values (100 Monte Carlo runs per parameter value; Figure 8).

**2D Participation Rate Sweep.** To map the boundary conditions under which spatial targeting becomes effective, we conducted a two-dimensional sweep across high-risk (20-70%) and low-risk (20-70%) participation rates, with medium-risk set to the midpoint (100 MC runs per combination, 36 combinations; Figure 9).

The results reveal a clear crossover boundary (Figure 9, dashed line). In the model, spatial targeting (Smart Hotspot) outperforms FCFS only when high-risk participation exceeds approximately 60% — and even then, only when combined with low-risk participation above 60%. At low-risk participation rates of 30-50% (with high-risk fixed at 30%), Smart Hotspot underperforms FCFS by 0.5-1.8%. At our central estimate (High=30%, Low=55%) — a point between sweep cells — the underperformance is approximately 1.5% (interpolating between adjacent sweep cells, since the 2D grid uses 0.10 increments and has no exact (0.30, 0.55) cell). (Note: the 2D sweep imposes Medium = (High + Low) / 2 by design. At the central estimate (H=30%, L=55%), this gives Medium = 42.5% rather than the main-simulation value of 45%; the 2.5 pp gap is below the resolution of strategy ranking changes.) The maximum Smart Hotspot advantage (+5.0%) occurs at the upper-right corner of the parameter space (High=70%, Low=70%), representing a participation regime that is inconsistent with observed voluntary program engagement.

The crossover boundary runs diagonally: spatial targeting requires both high engagement from the targeted population and broad engagement from the general population. This makes intuitive sense — targeting high-risk fields only helps if those fields participate, and peer-effect cascades only propagate if the surrounding fields also participate. Neither condition is met under realistic voluntary participation rates.

**Biophysical parameters.** Base P loss rate and Type A effectiveness each produce over 80 percentage points of variation in absolute target achievement but affect both strategies equally — the relative ranking is unchanged. Interpretation-layer parameters (additionality, bioavailability) have zero impact on simulation dynamics, confirming the two-layer architecture described in Section 3.5.

### 5.7 Variance Decomposition

To determine what drives the wide empirical ranges in model outputs (e.g., FCFS: 11-119 tonnes), we decomposed total variance into three sources through controlled experiments (1,000 runs each, FCFS only):

**Table 4. Orthogonal variance decomposition of the FCFS strategy (n=1,000 MC runs per experiment).** The three variance sources are partitioned orthogonally: Experiment B isolates precipitation variance; Experiment C isolates adoption stochasticity; pure-parameter variance is computed as (Experiment A) − (Experiment C), since Experiment A confounds parameter and adoption randomness. Percentages sum to 100% by construction.

| Source | Variance | Share |
|--------|----------|-------|
| Precipitation | 798.82 | **99.55%** |
| Pure parameters | 0.010 | 0.001% |
| Adoption stochasticity | 3.62 | 0.45% |
| **Total** | **802.45** | **100.00%** |

Precipitation dominates Year-4 phosphorus reduction variance at 99.55%, consistent with the 8-fold annual load range documented in §2.2. Pure parameter uncertainty contributes negligibly (0.001%); the small non-precipitation variance (~0.45%) is almost entirely attributable to adoption stochasticity. When precipitation is fixed at the long-term mean, the 95% range narrows from [11, 119] tonnes to [38, 49] tonnes — a 10-fold reduction in uncertainty.

This decomposition has two important implications. First, the wide empirical ranges reported throughout this study are not evidence of model imprecision but of physical reality: Thames River phosphorus transport is precipitation-dominated, and no model — regardless of calibration quality — can produce narrow empirical ranges without fixing precipitation. Second, strategy comparisons are robust precisely because precipitation affects all strategies equally. The 1-2% differences between FCFS and alternatives, while small relative to total variance, are consistent across precipitation scenarios because the management signal is additive to the precipitation signal.

---

## 6. Discussion

### 6.1 Why Every Alternative Loses to Random Allocation

The central empirical finding of this study — that four distinct allocation redesigns all failed to outperform first-come-first-served random allocation — requires explanation, as it contradicts the widespread assumption that spatially targeted conservation spending should outperform untargeted spending.

The explanation lies in a structural inversion between phosphorus risk and participation willingness. High-risk fields contribute 57% of watershed phosphorus loading from 25% of agricultural area, creating a strong theoretical case for spatial targeting. However, the farmers operating these fields participate in voluntary programs at the lowest rates (estimated 30%, compared to 55% for low-risk farmers). Spatial targeting strategies prioritize offers to fields where the probability of acceptance is lowest, systematically wasting budget capacity on declined offers.

FCFS avoids this trap through indifference. By offering subsidies in random order, FCFS naturally reaches the large pool of willing low-risk and medium-risk participants, achieving broad spatial coverage and seeding peer-effect cascades across the watershed. The aggregate phosphorus reduction from many small adoptions exceeds the concentrated reduction achievable from the few high-risk adoptions that spatial targeting can secure.

This finding contrasts with purely biophysical targeting studies. Kalcic et al. (2015) used SWAT modeling to identify optimal BMP placement in tile-drained agricultural watersheds, mapping a cost–phosphorus-reduction Pareto frontier in which well-targeted practice portfolios substantially outperformed baseline conditions at equivalent cost — a result predicated on the assumption that farmers will adopt BMPs wherever they are prescribed. Our results suggest that biophysical optimality is necessary but not sufficient: under the behavioral constraints of voluntary participation, the targeting advantage predicted by hydrological models is substantially reduced and can even become negative, because the fields identified as optimal by biophysical criteria are operated by the farmers least likely to participate.

The Efficiency Pricing strategy reveals a second constraint, consistent with the economic theory of nonpoint source pollution policy (Shortle & Horan, 2017). Within the model's single-function adoption framework, the Efficiency Pricing result reflects the mechanical effect of reducing net subsidy benefit below implementation cost: halving the Type A subsidy to $15/acre pushed net benefit negative, reducing adoption by 27%, while doubling Type B to $60/acre increased adoption by only 3.3% because the non-economic barriers to Type B (equipment, process change) are not captured by the subsidy coefficient. Whether farmers would actively switch from Type A to Type B under bioavailability-weighted pricing remains an open question requiring a model with explicit BMP-type choice (Section 7).

**Addressing the parameter-dependence concern.** One could argue our central finding is mechanically determined by the participation filter assumption. We address this concern through three robustness exercises. First, the inversion check (§5.2, fourth line of evidence) confirms the conclusion holds even if high-risk farmers participate at the highest rate (55%) and low-risk at lowest (30%). Second, the 2D sweep (§5.6) maps the full crossover boundary and shows that Smart Hotspot superiority requires both rates simultaneously above 60%—a regime not observed in any voluntary program documentation. Third, under the participation filter, the peer effect coefficient—the dominant parameter in unconstrained runs—is neutralized (documented in §5.6 and §7), so remaining biophysical parameters (base P loss, BMP effectiveness) affect FCFS and alternative strategies equally, preserving the inversion. Together these establish that the risk-participation inversion is a structural feature of the parameter range supported by Ontario program evidence, not an artifact of any single parameter choice.

### 6.2 Structural Barriers Beyond Allocation

Building on the transport chain analysis (Section 2), this section synthesizes how each barrier limits BMP subsidy effectiveness, distinguishing transport-related constraints already introduced in Section 2 from behavioral constraints specific to voluntary participation:

**Legacy phosphorus.** Decades of surplus phosphorus application have accumulated legacy phosphorus stocks across Ontario's agricultural soils — stocks large enough that soils routinely exceed the 30 mg/kg Olsen P threshold at which Ontario's P Index calculation becomes mandatory. BMPs can reduce new phosphorus losses but cannot extract phosphorus already embedded in the soil profile. Even if all current-year fertilizer application ceased, drawdown of legacy soil P would span several years to more than a decade depending on soil test P level and crop removal, with large global stocks projected to persist for much longer (Rowe et al., 2016, and references therein). This represents a phosphorus source that no BMP subsidy can address on policy-relevant timescales.

**Precipitation dominance.** The 8-fold range in Thames River annual phosphorus loads (80-670 tonnes) is driven entirely by precipitation and discharge, not by land management. Our Monte Carlo analysis confirms this: the 95% empirical range for phosphorus reduction spans from 11 to 119 tonnes under FCFS, a 10-fold range. Against this background variability, strategy differences of 1-2% are statistically undetectable in any individual year — the precipitation signal overwhelms the management signal.

**Tile drainage bypass.** Approximately 9% of Upper Thames fields are flagged as tile-drained in our conservative drainage-score proxy (drainage score ≥ 5 on a 6-point scale); actual tile drainage extent is substantially higher (33-66% per UTRCA Watershed Report Cards, 58% watershed-wide per City of London 2020), so our estimate is a lower bound on the tile-drainage mask effect (see §3.2 for proxy derivation and reconciliation). These fields provide subsurface conduits that bypass surface BMPs entirely. The dissolved reactive phosphorus carried through tile drains is 100% bioavailable, meaning that each kilogram of DRP reaching the lake has four times the algal growth impact of a kilogram of particulate phosphorus. The current UTRCA program emphasizes surface BMPs (cover crops, reduced tillage) that cannot intercept this pathway.

**Additionality.** Our model estimates that 20-25% of subsidized BMP adoption would have occurred without the subsidy, though this may understate the issue. USDA Economic Research Service studies of U.S. conservation programs estimate that approximately 46% of subsidized conservation tillage adoption is non-additional — considerably higher than rates for structural practices such as buffer/filter strips (~20%) or nutrient management (~12%) — meaning subsidies directed toward short-term profitable practices disproportionately fund adoption that would have occurred anyway (Claassen et al., 2014). If Ontario's additionality rates for cover crops and reduced tillage are closer to the U.S. tillage estimate, the net policy-attributable phosphorus reduction would be substantially lower than our model projects, and the gap to the 64 t/yr target correspondingly larger.

**Voluntary participation ceiling.** Even with generous subsidies, approximately 15-20% of farmers consistently decline to participate in conservation programs due to non-economic barriers: distrust of government programs, lack of equipment, time constraints, risk aversion toward unfamiliar practices, and age-related unwillingness to change established routines (Prokopy et al., 2019; Knowler & Bradshaw, 2007). These barriers are not addressable through higher subsidy rates, as evidenced by the UTRCA program's budget underutilization (52-100% across years) — subsidy demand falls short of supply.

**Self-selection bias.** Under voluntary programs, the farmers most likely to participate are those for whom BMP adoption requires the least behavioral change — typically lower-risk operations that already practice some conservation measures. Our model captures this through the biased initial adoption (27% pre-adopted, skewed toward low-risk fields) and the differential baseline adoption probabilities. The result is that voluntary subsidies systematically reach the farmers where marginal phosphorus reduction is smallest, while the high-risk, high-impact operations that would benefit most from BMPs are least likely to participate.

### 6.3 Policy Implications

These findings do not argue against agricultural BMPs, which demonstrably reduce phosphorus loss at the field scale. Rather, they demonstrate that voluntary cost-share subsidies — the dominant policy instrument in Ontario and across the Great Lakes basin — have a structural ceiling that spatial optimization can only modestly raise.

Meeting the 40% Lake Erie phosphorus reduction target will likely require a portfolio of instruments extending beyond voluntary subsidies. Our analysis suggests four complementary directions, without prescribing specific policy designs:

First, **addressing legacy phosphorus** through long-term soil phosphorus drawdown programs that reduce soil test phosphorus levels over 10-20 year horizons, potentially through reduced fertilizer application rates below crop removal. Second, **tile drainage interventions** such as controlled drainage, edge-of-field treatment wetlands, and phosphorus-sorbing materials in drain outlets that intercept the subsurface DRP pathway that surface BMPs miss. Third, **non-economic adoption support** including equipment-sharing cooperatives, peer mentoring networks, and technical assistance that address the non-financial barriers limiting voluntary participation. Fourth, **performance-based rather than practice-based incentives**—for example, conservation auction mechanisms and outcome-linked contracts reviewed by Latacz-Lohmann & Schilizzi (2005)—that reward measured phosphorus reduction outcomes rather than BMP adoption inputs, aligning farmer incentives directly with environmental objectives.

### 6.4 Connection to the Broader Policy Debate

Our quantitative findings align with the qualitative consensus emerging in Great Lakes policy circles. Michigan's 2025 assessment concluded that a decade of voluntary conservation programs had failed to produce measurable phosphorus reductions (Bridge Michigan, 2025). Canada's 2024 Lake Erie Action Plan Evaluation found no clear downward trend in phosphorus loads despite sustained investment (ECCC & OMECP, 2024). The UTRCA's own program data show budget underutilization — subsidies are available but not fully subscribed — suggesting that the constraint is not funding but participation.

This study provides the first integrated quantitative analysis combining spatial allocation, behavioral participation, and phosphorus transport chain attribution to explain why voluntary subsidies underperform the 40% target in the Thames watershed. The gap between program capacity and the 40% target is not a problem that better allocation can solve — it is a problem that requires different policy instruments.

---

## 7. Limitations and Future Work

This study has several limitations that should be considered when interpreting results. Limitations are listed roughly in order of impact on the strategy-comparison conclusion. Most consequential: behavioral parameter calibration and additionality (could shift absolute target achievement by 15-20%); moderately consequential: peer effect specification, hydrological simplification; least consequential for relative comparison: agent representation, single watershed, no climate change.

**Agent representation.** Agricultural fields are delineated from 30-meter satellite imagery (AAFC Annual Crop Inventory), not from legal farm parcel boundaries. A single farm operation may encompass multiple field agents in our model, and the decision to adopt a BMP is made at the field level rather than the farm level. This over-counts adoption events relative to farm-level program data, though the relative comparison between strategies is unaffected because all strategies operate on the same agent set.

**Adoption function parameterization.** The logistic adoption function uses coefficients calibrated to UTRCA Year 1 data, with functional form informed by U.S. Great Lakes adoption literature (Palm-Forster et al., 2017; Liu et al., 2018; Prokopy et al., 2019), not from Ontario-specific survey data. While the Lake Erie Western Basin farmer population shares similar characteristics with Ontario's Thames River farmers, direct transferability is uncertain. Future work should calibrate adoption parameters using Ontario Environmental Farm Plan participation data or purpose-built farmer surveys.

**Additionality estimates.** Our baseline adoption probabilities (Low-risk: 0.40, Medium: 0.20, High: 0.10) are conservatively low relative to the U.S. estimate of ~46% non-additionality for conservation tillage (Claassen et al., 2014). The additionality implementation uses a post-hoc stochastic classification — each adoption event is probabilistically labeled as additional or free-rider based on the field's baseline probability — rather than a structural behavioral model of counterfactual adoption. This approach captures the aggregate magnitude of non-additionality but does not model the mechanisms through which free-riding occurs (e.g., farmers accelerating planned adoption to capture subsidies). If actual free-rider rates in Ontario are closer to that estimate, the net policy-attributable phosphorus reduction would be 15-20% lower than our central estimates, and the structural gap to the 64 t/yr target correspondingly larger. Sensitivity analysis (Section 5.6) quantifies this uncertainty.

**BMP-type substitution.** The adoption function evaluates each subsidy offer independently and does not model BMP-type switching behavior — a farmer cannot be offered Type A, decline, and then be offered Type B within the same year. The Efficiency Pricing results therefore test farmer response to different subsidy levels, not farmer substitution between BMP types. A model with explicit BMP-type choice would be needed to fully test bioavailability-weighted pricing designs.

**BMP retention assumption.** The model treats BMP adoption as permanent within the 4-year program horizon: once a field is recorded as having adopted Type A or Type B, that status persists through the simulation. In reality, BMP types differ in their retention profiles. Cover crops are annual recommitment decisions and may lapse if seasonal conditions or post-program incentives shift; reduced-tillage and subsurface phosphorus placement are more durable due to their capital-investment or practice-change nature, but neither is certain over a 4-year horizon. The model also does not simulate post-program (Year 5+) sustainability — the BMP cohorts established under the $17.41 million program would face economic re-evaluation once subsidies end, with cover-crop adopters at the highest risk of reverting. Both effects suggest the Year 4 projection of approximately 43 tonnes is an **optimistic upper bound** on what the program will actually sustain at maturity. The 3.1× calibration overestimate noted in §3.5 implicitly absorbs some component of this retention-assumption optimism, but the model does not separately quantify the retention contribution to that overestimate.

**Future work: empirical estimation through panel data.** The participation filter assumptions, baseline adoption probabilities, and BMP effectiveness rates in this study are calibrated to aggregate Year 1 program outcomes rather than estimated from individual-level observations. Direct estimation from historical Ontario cost-share program data — Environmental Farm Plan (1993–present), the Great Lakes Agricultural Stewardship Initiative (GLASI, 2015–2018), the Canadian Agricultural Partnership (CAP, 2018–2023), and Sustainable CAP (2023–2028) — would substantially strengthen the empirical basis. Specifically, farmer-level panel data would enable: (a) direct estimation of risk-stratified participation rates via discrete choice models rather than scenario assumption; (b) out-of-sample validation by calibrating the model on early cohorts and predicting later cohorts; (c) causal identification of subsidy effects via difference-in-differences comparison of participants and matched non-participants; (d) Ontario-specific additionality estimates from pre-enrollment BMP histories rather than imports from U.S. literature; and (e) BMP retention dynamics from multi-year farmer trajectories, addressing the permanence assumption noted above. Access to such data requires research agreements with OMAFA / OSCIA or a Statistics Canada Research Data Centre application. We identify this as the highest-priority extension of the current work — the path through which the central risk-participation inversion finding can move from a robustly-tested scenario assumption to a directly estimated empirical result.

**Behavioral heterogeneity.** The adoption function does not differentiate between farm operation types. In practice, dairy operations (with manure management obligations), cash crop operations (focused on yield maximization), and mixed farming operations exhibit substantially different BMP adoption profiles (Prokopy et al., 2019). Livestock operators may face lower barriers to Type B adoption (manure management) while cash croppers may prefer Type A (cover crops for soil health). This farm-type heterogeneity could alter the risk-participation relationship — for example, if high-risk areas are disproportionately livestock operations, their participation rates may be higher than our uniform 30% estimate suggests, potentially shifting the crossover boundary identified in Figure 9.

**Peer effect specification.** The spatial neighbor graph uses a 500-meter buffer around field polygons, which captures geographic proximity but not true social networks among farm operators. Multiple fields belonging to the same farm operation appear as separate agents with "peer effects" between them, when these are more accurately intra-farm correlations. However, sensitivity analysis shows that the peer effect coefficient has minimal influence on strategy comparison when the participation filter is active (Section 5.6), because the participation constraint dominates the adoption dynamics. The peer effect finding from unconstrained runs (Section 5.1) should therefore be interpreted as a theoretical mechanism rather than a calibrated behavioral parameter.

**Hydrological simplification.** The model uses a static distance-to-water delivery proxy rather than hydrological routing, and does not explicitly model in-stream processes such as reservoir retention (Fanshawe Reservoir retained 25% in 2018 and 47% in 2019; Kao et al., 2022). Coupling the simulation with a process-based hydrological model (e.g., SWAT) would improve the accuracy of watershed-outlet phosphorus estimates.

**Single watershed.** Results are specific to the Upper Thames River watershed and may not generalize to other Lake Erie tributaries with different soil types, drainage patterns, farm structures, or program designs. Extension to the Lower Thames, Grand River, and Leamington tributaries would test the robustness of the structural ceiling finding.

**No climate change.** The precipitation distribution is calibrated to historical variability and does not account for projected changes in precipitation intensity, timing, or seasonality under climate change scenarios, which could alter both baseline phosphorus loads and BMP effectiveness.

**Parameter interactions and global sensitivity.** The sensitivity analysis in §5.6 uses one-at-a-time (OAT) variation, which characterizes each parameter's marginal effect but does not capture interactions between parameters. A full Sobol global sensitivity analysis with Saltelli sampling was identified as a planned extension but was not delivered in the current version. Under the participation filter, the OAT analysis shows that the peer effect coefficient—the dominant driver in the unconstrained regime—is neutralized, and other parameters each produce similar absolute-target-achievement shifts on both FCFS and alternative strategies. We therefore expect parameter interactions to have limited effect on strategy ranking under the constrained scenario, though this expectation remains an unverified assumption.

**Program credibility and farmer awareness.** The model assumes (1) full subsidy program credibility—that announced subsidy amounts are honored and payments are timely—and (2) full farmer awareness of available BMP options and subsidy rates. In practice, program implementation may face payment delays, mid-program rule changes, or budget reductions, and farmer awareness varies substantially (the 2020 Ontario Cover Crop Feedback Report cites "not knowing where to start" as a non-adoption reason for 24% of surveyed farmers; GFO, 2021). Relaxing these assumptions would likely reduce effective adoption rates below model predictions, widening the gap to the 40% target.

**Operator continuity.** The 4-year simulation assumes farm operator and land tenure continuity. Ontario agriculture sees approximately 1-2% annual farm exit/consolidation, so 4-8% of operators may change over the program horizon. Generational transitions, land sales, and consolidations can reshuffle the participation pattern (new operators may be more or less willing to engage with subsidies than predecessors). This turnover dynamic is not modeled.

**Future directions.** Three extensions would strengthen this work. First, obtaining UTRCA's spatial subsidy distribution data (which fields received funding in Years 1-2) would enable direct model validation against observed outcomes rather than aggregate statistics. Second, incorporating reinforcement learning to optimize the allocation strategy within the constraint space could identify non-obvious subsidy designs that outperform the heuristic strategies tested here. Third, extending the simulation to 10-20 year horizons would capture legacy phosphorus dynamics and the long-term trajectory of adoption saturation under continued voluntary programs.

---

## 8. Conclusion

Under realistic voluntary participation constraints, the model's Year-4 mature-state simulation projects that the Thames River BMP subsidy program would deliver approximately 43 tonnes per year of total phosphorus reduction (67% of the 64 t/yr target before calibration adjustment; ~22% or 14 t/yr after the 3.1× calibration adjustment from UTRCA Year 1 observations; in an average precipitation year, 38-49 tonnes uncalibrated, 60-77% of target). Four alternative allocation designs — spatial prioritization with premium pricing (+2.0%, small effect size with 95% empirical range crossing zero), spatial prioritization with uniform pricing (-1.6%), bioavailability-weighted pricing (-60.4%), and a moderate efficiency-pricing variant (-52.2%) — all performed equal to or worse than the current first-come-first-served random allocation. A sensitivity sweep across high-risk participation rates from 30% to 60% found no crossover, and a robustness check inverting participation rates (high-risk 55%, low-risk 30%) confirmed that FCFS maintains its advantage (-0.3% for Smart Hotspot).

These simulation results challenge the intuitive assumption that targeted conservation spending should outperform untargeted spending. The explanation is a structural inversion: the fields contributing the most phosphorus are operated by the farmers least likely to participate in voluntary programs. Spatial targeting directs offers to fields where acceptance probability is lowest, while random allocation naturally reaches the broad pool of willing participants whose aggregate small reductions exceed the concentrated reductions achievable through targeting.

The gap between program capacity and the 40% Lake Erie phosphorus reduction target is therefore structural at two levels: first, the phosphorus transport chain imposes physical limits through legacy soil phosphorus, precipitation variability, and tile drainage bypass; second, the voluntary participation framework imposes behavioral limits through the inversion of risk and engagement. Closing the gap to the 40% target will likely require policy instruments beyond voluntary cost-share subsidies, potentially including mandatory or performance-based mechanisms to reach high-risk non-participants, and infrastructure interventions (tile drainage management, legacy phosphorus drawdown) to address transport pathways that no field-level BMP can intercept.

---

## References


- AAFC (2024). Annual Crop Inventory 2024. Agriculture and Agri-Food Canada, Ottawa, ON.
- Baker, D. B., Confesor, R., Ewing, D. E., Johnson, L. T., Kramer, J. W., & Merryfield, B. J. (2014). Phosphorus loading to Lake Erie from the Maumee, Sandusky and Cuyahoga rivers: The importance of bioavailability. Journal of Great Lakes Research, 40(3), 502-517. https://doi.org/10.1016/j.jglr.2014.05.001
- Bridge Michigan (2025). Michigan spent millions to curb Lake Erie algae. Little has worked. Bridge Michigan news report citing Michigan Department of Environment, Great Lakes, and Energy (EGLE) assessment. https://www.bridgemi.com (accessed 2026).
- Canada & United States (2012). Great Lakes Water Quality Agreement, Annex 4: Nutrients. Amended Protocol of the 1978 Agreement.
- City of London (2020). *One River Environmental Assessment Report — Section 3*. City of London, Ontario. https://london.ca/sites/default/files/2020-10/04_Section_3_One_River_EA_Report.pdf
- Claassen, R., Horowitz, J., Duquette, E., & Ueda, K. (2014). Additionality in U.S. Agricultural Conservation and Regulatory Offset Programs (Economic Research Report No. ERR-170). U.S. Department of Agriculture, Economic Research Service.
- Environment and Climate Change Canada [ECCC] (2024). *Canadian Environmental Sustainability Indicators: Phosphorus loading to Lake Erie*. Government of Canada. https://www.canada.ca/en/environment-climate-change/services/environmental-indicators/phosphorus-loading-lake-erie.html (accessed 2026).
- Environment and Climate Change Canada [ECCC] & Ontario Ministry of the Environment, Conservation and Parks [OMECP] (2024). Canada-Ontario Lake Erie Action Plan: 2024 Evaluation and Update Report. Government of Canada.
- Governments of Canada and the United States (2016). *The United States and Canada Adopt Phosphorus Load Reduction Targets to Combat Lake Erie Algal Blooms*. Announced February 22, 2016 under the Great Lakes Water Quality Agreement Annex 4. https://binational.net/2016/02/22/finalptargets-ciblesfinalesdep/
- Grain Farmers of Ontario & Ontario Cover Crop Steering Committee (2021). 2020 Ontario Cover Crop Feedback Report. Grain Farmers of Ontario, Guelph, ON.
- Han, H., Bosch, N., & Allan, J. D. (2011). Spatial and temporal variation in phosphorus budgets for 24 watersheds in the Lake Erie and Lake Michigan basins. Biogeochemistry, 102(1-3), 45-58. https://doi.org/10.1007/s10533-010-9420-y
- Jarvie, H. P., Johnson, L. T., Sharpley, A. N., Smith, D. R., Baker, D. B., Bruulsema, T. W., & Confesor, R. (2017). Increased soluble phosphorus loads to Lake Erie: Unintended consequences of conservation practices? Journal of Environmental Quality, 46(1), 123-132. https://doi.org/10.2134/jeq2016.07.0248
- Kalcic, M. M., Frankenberger, J., & Chaubey, I. (2015). Spatial optimization of six conservation practices using SWAT in tile-drained agricultural watersheds. JAWRA Journal of the American Water Resources Association, 51(4), 956-972. https://doi.org/10.1111/1752-1688.12338
- Kao, N., Mohamed, M., Sorichetti, R. J., Niederkorn, A., Van Cappellen, P., & Parsons, C. T. (2022). Phosphorus retention and transformation in a dammed reservoir of the Thames River, Ontario: Impacts on phosphorus load and speciation. Journal of Great Lakes Research, 48(1), 84-96. https://doi.org/10.1016/j.jglr.2021.11.008
- Knowler, D., & Bradshaw, B. (2007). Farmers' adoption of conservation agriculture: A review and synthesis. Food Policy, 32(1), 25-48. https://doi.org/10.1016/j.foodpol.2006.01.003
- Latacz-Lohmann, U., & Schilizzi, S. (2005). Auctions for conservation contracts: A review of the theoretical and empirical literature. Report to the Scottish Executive Environment and Rural Affairs Department.
- Liu, J., Macrae, M. L., Elliott, J. A., Baulch, H. M., Wilson, H. F., & Kleinman, P. J. A. (2019). Impacts of cover crops and crop residues on phosphorus losses in cold climates: A review. Journal of Environmental Quality, 48(4), 850-868. https://doi.org/10.2134/jeq2019.03.0119
- Liu, T., Bruins, R. J. F., & Heberling, M. T. (2018). Factors influencing farmers' adoption of best management practices: A review and synthesis. Sustainability, 10(2), 432. https://doi.org/10.3390/su10020432
- LTVCA (2025). Phosphorus Reduction Program — Guidebook (July 28, 2025). Lower Thames Valley Conservation Authority, Chatham, ON. https://www.lowerthames-conservation.on.ca/wp-content/uploads/GUIDEBOOK-July-28-2025-WEB.pdf
- Macrae, M., Jarvie, H., Brouwer, R., Gunn, G., Reid, K., Joosse, P., King, K., Kleinman, P., Smith, D., Williams, M., & Zwonitzer, M. (2021). One size does not fit all: Toward regional conservation practice guidance to reduce phosphorus loss risk in the Lake Erie watershed. Journal of Environmental Quality, 50(3), 529-546. https://doi.org/10.1002/jeq2.20218
- Mirnasl, N., Akbari, A., Philpot, S., Hipel, K. W., & Deadman, P. (2024). An integrated spatial fuzzy-based site suitability assessment framework for agricultural BMP placement. Environmental Quality Management, 34, e22328. https://doi.org/10.1002/tqem.22328
- OMAFA (2022, May 3). *Determining the phosphorus index for a field*. Ontario Ministry of Agriculture, Food and Agribusiness (ministry renamed from OMAFRA in June 2024). Government of Ontario. https://www.ontario.ca/page/determining-phosphorus-index-field (standalone guide; URL now redirects to the AgriSuite hub).
- OMAFA (2025). Field Crop Budgets Publication 60. Ontario Ministry of Agriculture, Food and Agribusiness, Guelph, ON.
- Ontario Ministry of Agriculture, Food and Rural Affairs (OMAFRA) (various years). Ontario Detailed Soil Survey Complex. 1:50,000 vector dataset, compiled from county-level surveys from 1929.
- Ontario Ministry of Natural Resources and Forestry (2019). Ontario Hydro Network (OHN) – Watercourse. Government of Ontario (Ontario GeoHub).
- Palm-Forster, L. H., Swinton, S. M., & Shupp, R. S. (2017). Farmer preferences for conservation incentives that promote voluntary phosphorus abatement in agricultural watersheds. Journal of Soil and Water Conservation, 72(5), 493-505. https://doi.org/10.2489/jswc.72.5.493
- Prokopy, L. S., Floress, K., Arbuckle, J. G., Church, S. P., Eanes, F. R., Gao, Y., Gramig, B. M., Ranjan, P., & Singh, A. S. (2019). Adoption of agricultural conservation practices in the United States: Evidence from 35 years of quantitative literature. Journal of Soil and Water Conservation, 74(5), 520-534. https://doi.org/10.2489/jswc.74.5.520
- Rowe, H., Withers, P. J. A., Baas, P., Chan, N. I., Doody, D., Holiman, J., Jacobs, B., Li, H., MacDonald, G. K., McDowell, R., Sharpley, A. N., Shen, J., Taheri, W., Wallenstein, M., & Weintraub, M. N. (2016). Integrating legacy soil phosphorus into sustainable nutrient management strategies for future food, bioenergy and water security. Nutrient Cycling in Agroecosystems, 104(3), 393-412. https://doi.org/10.1007/s10705-015-9726-1
- Shortle, J., & Horan, R. D. (2017). Nutrient pollution: A wicked challenge for economic instruments. Water Economics and Policy, 3(2), 1650033. https://doi.org/10.1142/S2382624X16500338
- Smith, R. B., Bass, B., Sawyer, D., Depew, D., & Watson, S. B. (2019). Estimating the economic costs of algal blooms in the Canadian Lake Erie Basin. Harmful Algae, 87, 101624. https://doi.org/10.1016/j.hal.2019.101624
- Statistics Canada (2022). 2021 Census of Agriculture: Farm and Farm Operator Data. Catalogue no. 95-640-X. Government of Canada. https://www150.statcan.gc.ca/n1/en/catalogue/95-640-X
- Steffen, M. M., Davis, T. W., McKay, R. M. L., Bullerjahn, G. S., Krausfeldt, L. E., Stough, J. M. A., ... & Wilhelm, S. W. (2017). Ecophysiological examination of the Lake Erie Microcystis bloom in 2014: Linkages between biology and the water supply shutdown of Toledo, OH. Environmental Science & Technology, 51(12), 6745-6755. https://doi.org/10.1021/acs.est.7b00856
- U.S. Environmental Protection Agency (2015). Recommended Phosphorus Loading Targets for Lake Erie: Annex 4 Objectives and Targets Task Team Final Report. U.S. EPA.
- UTRCA (2022). Watershed Report Cards. Upper Thames River Conservation Authority, London, ON.
- UTRCA (2024). Thames River Phosphorus Reduction Program: Program Guidelines. Upper Thames River Conservation Authority, London, ON.
- UTRCA (2025). Local landowners lead the way in phosphorus reduction efforts. Upper Thames River Conservation Authority, London, ON.
- Van Esbroeck, C. J., Macrae, M. L., Brunke, R. R., & McKague, K. (2017). Surface and subsurface phosphorus export from agricultural fields during peak flow events over the nongrowing season in regions with cool, temperate climates. Journal of Soil and Water Conservation, 72(1), 65-76. https://doi.org/10.2489/jswc.72.1.65
- Van Rossum, T., & Norouzi, Y. J. (2021). Quantifying phosphorous loadings in the Thames River in Canada. Water Cycle, 2, 44-50. https://doi.org/10.1016/j.watcyc.2021.06.002

---

## Figure Captions

**Figure 1.** Phosphorus transport chain from agricultural field to Lake Erie, showing BMP intervention points (green dashed boxes) and structural limits where no BMP solution exists (orange boxes). Each transport step is labeled with the dominant phosphorus form and approximate quantity.

**Figure 2.** Phosphorus loss risk classification of 8,949 agricultural fields in the Upper Thames River watershed, derived from composite P-risk score (drainage, slope, proximity to waterway, soil texture). High-risk fields (red, 25% of area; 23% by field count) contribute 57% of estimated phosphorus loading.

**Figure 3.** Monte Carlo strategy comparison (n=1,000). (a) Total phosphorus reduction distributions for four of the five strategies compared in Table 3, with 64 t/yr target line; Moderate Efficiency Pricing is omitted to maintain panel layout clarity and its results ($25A/$40B, -52.2% vs FCFS) sit between FCFS and Efficiency Pricing (see Table 3). (b) Cost efficiency distributions ($/kg P reduced); (c) improvement of alternative strategies relative to FCFS baseline.

**Figure 4.** Gross versus additional (policy-attributable) phosphorus reduction under each strategy, showing the fraction of adoption that would have occurred without subsidies (free-rider effect).

**Figure 5.** BMP signal versus precipitation noise in the Thames River watershed (constrained FCFS, illustrative 20-year sequence). Total phosphorus load (black line) varies 8-fold with precipitation; the BMP reduction signal (blue shaded band; ~43 t/yr mean under the participation filter) is small relative to inter-annual variability. The red dashed line marks the residual-load target (baseline × 0.60), equivalent to the 64 t/yr reduction target.

**Figure 6.** Spatial diffusion of BMP adoption over four years under the Smart Hotspot strategy. Blue: pre-adopted fields (27%, Year 0); green: previously adopted; red: newly adopted that year; white: not adopted. Adoption spreads spatially through peer effects but is limited by participation constraints.

**Figure 7.** Gap analysis showing three independent adjustments from gross total phosphorus reduction to policy-relevant metrics (each applied separately to gross, not compounded; see methodology note in figure). The 64 t/yr target (red dashed line) is nominally approached in gross terms but a structural gap remains after additionality and bioavailability corrections.

**Figure 8.** One-at-a-time sensitivity analysis (tornado chart). The peer effect coefficient is the sole parameter with substantial influence on strategy comparison in unconstrained runs; under participation filter constraints (not shown), this influence is neutralized.

**Figure 9.** Two-dimensional participation rate sweep showing Smart Hotspot improvement over FCFS (%) across 36 combinations of high-risk and low-risk farmer participation rates (100 MC runs each). Green cells indicate Smart Hotspot superiority; red cells indicate FCFS superiority. The dashed contour marks the crossover boundary. Under estimated real-world conditions (High ~30%, Low ~55%), FCFS consistently outperforms spatial targeting.

---

## Appendix A. Table A1. Complete Model Parameter List

The following table lists every parameter of the simulation, with value, unit, and source. Values are taken directly from the code (`src/model/` and `src/analysis/`); sources are labeled *literature*, *calibrated*, *scenario*, *observed*, or *modeling assumption*.

| Parameter | Description | Value | Unit | Source |
|-----------|-------------|-------|------|--------|
| **Adoption function (`adoption_function.py`)** | | | | |
| a (intercept) | Logistic intercept | -2.00 | - | Calibrated (grid search vs UTRCA Year 1) |
| b (subsidy_coeff) | Subsidy responsiveness | 0.010 | 1/($/acre) | Calibrated |
| c (area_coeff) | Farm size effect | 0.002 | 1/acre | Modeling assumption |
| e (peer_coeff) | Neighbor-adoption coefficient | 1.5 | - | Modeling assumption (Liu et al., 2018; Prokopy et al., 2019) |
| σ (noise std) | Post-sigmoid adoption noise | 0.3 | probability | Modeling assumption |
| max_adoption_prob | Adoption ceiling (post-clip) | 0.85 | probability | Modeling assumption |
| **BMP economics (`adoption_function.py`)** | | | | |
| BMP cost Type A | Implementation cost | 25 | $/acre | OMAFA (2025) Pub 60 lower midrange of $10-50 |
| BMP cost Type B | Implementation cost | 35 | $/acre | OMAFA (2025) Pub 60 midpoint of $20-50 |
| BMP cost both | Combined implementation cost | 55 | $/acre | Type A + Type B with $5 synergy discount |
| Long-term benefit Type A | Annual soil benefit (undiscounted) | 5 | $/acre/yr | Modeling assumption |
| Long-term benefit Type B | Annual soil benefit (undiscounted) | 3 | $/acre/yr | Modeling assumption |
| Long-term benefit both | Combined synergy bonus | 10 | $/acre/yr | Modeling assumption |
| **Participation filter (`pilot_participation.py`, §5.2)** | | | | |
| PARTICIPATION_RATES Low | Low-risk willingness | 0.55 | fraction | Scenario (calibrated to UTRCA Year 1 86% utilization) |
| PARTICIPATION_RATES Medium | Medium-risk willingness | 0.45 | fraction | Scenario |
| PARTICIPATION_RATES High | High-risk willingness | 0.30 | fraction | Scenario |
| **UTRCA program (§3.4)** | | | | |
| Annual program budget | Total funding per year | 4.35 | $M | UTRCA 2024 ($17.41M / 4 yr) |
| Per-farm total subsidy cap | 4-year max per farm | 75,000 | $ | UTRCA 2025 rules |
| Type A subsidy | Cover crop / reduced tillage | 30 | $/acre | UTRCA 2025 rates |
| Type B subsidy (default) | Subsurface P placement | 30 | $/acre | UTRCA 2025 rates (upper bound of $20-30) |
| Manure management subsidy | Per-acre rate | 50 | $/acre | UTRCA 2025 rates |
| Manure management cap | Per-farm cap | 10,000 | $ | UTRCA 2025 rates |
| Subsurface P placement cap | Per-farm cap | 15,000 | $ | UTRCA 2025 rates |
| Type B cap (model) | Aggregate per-farm cap used in simulation | 12,500 | $ | Derived (mean of $10K + $15K; model does not separate subtypes) |
| Combination bonus | A+B same-year bonus | 10 | $/acre | UTRCA 2025 rates |
| Administrative feasibility floor | Minimum effective subsidy | 5 | $/acre | Conservation-program practice |
| **BMP effectiveness (`environment.py`)** | | | | |
| REDUCTION_A High | Type A on high-risk fields | 0.60 ± 0.15 | fraction | Literature |
| REDUCTION_A Medium | Type A on medium-risk fields | 0.30 ± 0.10 | fraction | Literature |
| REDUCTION_A Low | Type A on low-risk fields | 0.10 ± 0.05 | fraction | Literature |
| REDUCTION_B High | Type B on high-risk fields | 0.70 ± 0.10 | fraction | Literature |
| REDUCTION_B Medium | Type B on medium-risk fields | 0.50 ± 0.10 | fraction | Literature |
| REDUCTION_B Low | Type B on low-risk fields | 0.30 ± 0.10 | fraction | Literature |
| Effectiveness clip | Truncation bounds | [0.05, 0.95] | fraction | Modeling assumption |
| Tile drain Type A penalty | Effectiveness multiplier | 0.50 | fraction | Literature (subsurface bypass) |
| Tile drain threshold | Drainage score ≥ flag | 5 | score (1-6) | Proxy definition |
| **Base P loss (`environment.py`, kg/acre/yr at mean precipitation)** | | | | |
| BASE_P_LOSS High | High-risk P loss rate | 1.50 ± 0.50 | kg/acre/yr | Literature |
| BASE_P_LOSS Medium | Medium-risk P loss rate | 0.50 ± 0.20 | kg/acre/yr | Literature |
| BASE_P_LOSS Low | Low-risk P loss rate | 0.15 ± 0.05 | kg/acre/yr | Literature |
| **Transport chain (`environment.py`)** | | | | |
| Particulate:dissolved ratio | PP fraction mean | 0.80 | fraction | Macrae et al. (2021); Van Esbroeck et al. (2017) |
| Particulate:dissolved ratio range | Uniform distribution | [0.70, 0.90] | fraction | Same |
| Precipitation multiplier mean_log | LogNormal location | -0.18 | - | Calibrated to Thames 80-670 t/yr range |
| Precipitation multiplier sigma_log | LogNormal scale | 0.60 | - | Same |
| Fanshawe Reservoir retention (2018) | Observed | 0.25 | fraction | Kao et al. (2022) |
| Fanshawe Reservoir retention (2019) | Observed | 0.47 | fraction | Kao et al. (2022) |
| **Additionality baselines (`environment.py`)** | | | | |
| BASELINE_ADOPTION Low | Pr(adopt w/o subsidy) Low | 0.40 | probability | Claassen et al. (2014) informed |
| BASELINE_ADOPTION Medium | Pr(adopt w/o subsidy) Med | 0.20 | probability | Same |
| BASELINE_ADOPTION High | Pr(adopt w/o subsidy) High | 0.10 | probability | Same |
| **Bioavailability (§2.5)** | | | | |
| PP bioavailability | Particulate-P algal yield | 0.25 | fraction | Conservative (Baker et al., 2014 report 26-30%) |
| DRP bioavailability | Dissolved-P algal yield | 1.00 | fraction | Literature consensus |
| **Initial state (`environment.py`)** | | | | |
| INITIAL_ADOPTION_RATE | Pre-adopted Type A fraction | 0.27 | fraction | Statistics Canada 2021 Census (Ontario cover crops) |
| **Monte Carlo (`monte_carlo.py`, §4.5)** | | | | |
| N_RUNS | Simulations per strategy | 1,000 | runs | Design choice |
| Strategies | Total compared (FCFS + 4) | 5 | strategies | Design choice |
| Seeds (main MC) | Deterministic range | 1000-1999 | integer | Reproducibility |
| Seeds (variance decomp) | Deterministic range | 8000-8999 | integer | Reproducibility |
| Workers | Parallel CPU cores | 14 | cores | Compute environment |
| Years | Simulation horizon | 4 | years | Matches 2024-2028 UTRCA program |
| Thames P reduction target | Policy benchmark | 64 | tonnes/yr | Author's derivation from ECCC 212 t Canadian target × Thames 30% share |

---

## Declaration of Generative AI Use

During preparation of this work, the author used Claude (Anthropic, Opus 4.7) for the following purposes:

1. **Drafting and language editing** of English prose in the Introduction, Methods, Results, and Discussion sections.
2. **Python code generation** for figure rendering (Figures 1–9) and statistical analysis scripts, under the author's specification and review.
3. **Manuscript review** for internal consistency, citation accuracy, and methodological soundness across multiple revision rounds.

The author reviewed and verified all AI-generated content and is solely responsible for the analysis, interpretations, conclusions, and any remaining errors. The LLM did not participate in research design, data collection, scientific interpretation of results, or formulation of conclusions.

---

## Author Contribution

The single author (Z.Z.) is solely responsible for all aspects of this work, including study design, data collection and processing, simulation model development, statistical analysis, visualization, and manuscript preparation.

## Funding

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

## Conflict of Interest

The author declares no conflict of interest.

## Ethics

This study did not involve human or animal subjects. All data used are publicly available from government agencies and conservation authorities; no primary data collection involving individuals was conducted.

## Acknowledgements

The author thanks the Upper Thames River Conservation Authority (UTRCA) and the Ontario Ministry of Agriculture, Food and Agribusiness (OMAFA, formerly OMAFRA prior to June 2024) for maintaining publicly accessible program documentation and agricultural datasets that made this research possible.

## Code and Data Availability

Model code is written in Python 3.10+ using NumPy, pandas, GeoPandas, and SciPy, licensed under MIT. All spatial data are derived from publicly available sources (AAFC Annual Crop Inventory 2024, Ontario Detailed Soil Survey, Ontario Hydro Network, UTRCA Watershed Report Cards). Code, processed data, and exact parameter values (Appendix A) will be made available at a public GitHub repository with an archival DOI via Zenodo upon publication; commit hash corresponding to the results reported in this manuscript will be specified at that time. The author commits to maintaining this code for a minimum of five years following publication.
