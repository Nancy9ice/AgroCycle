**AGROCYCLE**

**PRODUCT REQUIREMENTS DOCUMENT**

*Sourced product specification • Environmental analysis • Rotation exploration • Validation • Competition readiness*

| **Document field**     | **Details**                                                                      |
|------------------------|----------------------------------------------------------------------------------|
| Status                 | Revised draft for team review                                                    |
| Product                | Environmental and agricultural crop-rotation decision-support tool                |
| Initial geography      | Story and Boone Counties, Iowa, USA                                              |
| Primary users          | Farmers and agricultural advisers                                                |
| Competition objectives | Best Use of Data; Best Use of Science; Best Use of Technology; Local Impact      |
| Reference convention   | Numbered citations \[S01\]–\[S24\]; full clickable source register in Section 17 |

## Document purpose

**Revision note (13 November 2026):** This revision realigns the PRD with the full NASA Space Apps 2026 challenge. AgroCycle is framed as an environmental and agricultural rotation-exploration tool, rather than primarily a test of whether a field should diversify. The Iowa maize–soybean pilot and Marsden Farm evidence remain, but Marsden is one supporting evidence source rather than the product's sole organising principle.

This PRD defines the product to build, the evidence required to support its outputs, the validation expected before claims are made, and the internal criteria for competition readiness. It separates documented source facts from team-proposed requirements and assumptions. A citation establishes the provenance of a statement; it does not by itself validate AgroCycle's implementation.

Status note: the sources below are identified for the design and research baseline. Unless explicitly stated as retrieved and inspected, a dataset is not considered downloaded, processed, integrated or validated in the product.

# 1. Product Overview

## 1.1 Product vision

AgroCycle helps farmers and agricultural advisers explore alternative crop-rotation strategies that could improve soil health and strengthen resilience to changing weather and water conditions. By combining NASA Earth observations, local agricultural information and experimental evidence, it provides transparent, evidence-aware comparisons of rotation options, including their potential benefits, trade-offs, uncertainties and operational requirements.

## 1.2 Product description

The initial product will focus on fields currently under maize–soybean rotation in Story and Boone Counties, Iowa. It will help users understand field conditions and historical patterns, then explore at least three rotation strategies: the existing two-year maize–soybean system, a three-year diversified system and a four-year diversified system.

AgroCycle will combine relevant NASA Earth observations with local soil and agricultural information, crop characteristics, experimental findings and farmer priorities. It will compare strategies across environmental, soil-health and operational dimensions, explain why an option may be worth considering, identify potential trade-offs and show where information is insufficient or local expert review is needed.

The initial use case remains deliberately bounded. It is a pilot for exploring rotation options in an Iowa maize–soybean context, not a universal crop-selection system.

## 1.3 Product differentiator

The differentiator is an uncertainty-aware evidence engine that connects environmental conditions to transparent rotation-strategy comparisons. It must distinguish observed or retrieved products, derived indicators, classified outputs, soil-survey information, model/reanalysis outputs, experimental records, published findings, assumptions and farmer-provided inputs.

The engine must explain potential benefits and trade-offs without claiming that satellite observations directly measure soil health or prove that a proposed rotation will improve a particular field. Agricultural calculations and decision rules must be deterministic, testable and traceable. AI may help explain outputs, but must not invent evidence or independently generate agronomic conclusions.

AgroCycle is decision support, not an autonomous agronomist. It should support exploration and human judgment, including by qualifying results or abstaining when evidence is inadequate.

## 1.4 Challenge alignment

The project is being developed for NASA Space Apps Challenge 2026 challenge “Field Shift: Adapting Farms with NASA Data”. The challenge framing calls for combining NASA Earth observations with local soil information, crop characteristics and farmer priorities to explore crop-rotation strategies. The team should use the official challenge page as the authoritative statement of challenge intent \[S01\].

# 2. Problem and Initial Use Case

## 2.1 Problem statement

Farmers face increasingly complex rotation decisions as temperature, rainfall and water conditions change and soil-health pressures accumulate. A crop or rotation that offers benefits in one location may create water, disease, market, machinery or growing-season challenges elsewhere. Evaluating alternatives requires combining environmental observations, local soil information, crop characteristics, experimental evidence and farmer priorities. These sources differ in scale, time period, measurement method and evidence strength, so they must not be treated as interchangeable.

## 2.2 Initial decision question

Given a field currently under maize–soybean rotation, what can available environmental, soil, crop and experimental evidence tell a farmer or adviser about exploring the existing system and two diversified alternatives? What potential benefits, trade-offs, operational requirements and evidence gaps should be considered?

| **Strategy** | **Rotation represented in the initial comparison** |
|---|---|
| A — Existing system | Two-year maize–soybean rotation |
| B — Diversified option | Three-year system including oat and red clover phases |
| C — Diversified option | Four-year system including oat and alfalfa phases |

These scenario definitions are anchored to the systems represented in the Marsden Farm experiment. They are comparison scenarios, not universal prescriptions or proof that the same outcomes will occur on another field [S09, S10].

## 2.3 Initial geography

The MVP will focus on Story and Boone Counties, Iowa. Iowa was selected because the team identified relevant crop, soil, climate, experimental and validation resources. This is a feasibility and evidence-strength decision, not a claim that Iowa has the greatest agricultural need.

## 2.4 Core decision dimensions

AgroCycle should compare the three strategies across dimensions relevant to the challenge:

- **Water resilience:** historical precipitation and soil-moisture context, seasonal water-stress indicators and crop water requirements where suitable evidence exists.
- **Climate resilience:** temperature, heat, frost, growing-season and extreme-precipitation context.
- **Soil health:** potential contributions from legumes, cover crops, residue and nutrient cycling, while distinguishing experimental findings from unmeasured field outcomes.
- **Land cover and erosion:** seasonal vegetation cover and bare-field windows; erosion risk only where appropriate terrain, soil and rainfall inputs support a defensible indicator.
- **Farm feasibility:** machinery, labour, manure access, forage use, storage, market availability and farmer priorities.

Not every dimension will be measurable at field scale in the MVP. Each output must state the scale and limitations of its supporting data.

# 3. Product Objectives and Competition Strategy

| **Target award** | **Product objective** | **Evidence the team must demonstrate** |
|---|---|---|
| Best Use of Data | Make NASA observations materially relevant to understanding environmental conditions and comparing rotation options | Reproducible integration, spatial/temporal alignment, quality handling, provenance and a clear link between observations and outputs |
| Best Use of Science | Translate Earth-observation and agricultural evidence into defensible interpretation | Appropriate methods, experimental evidence, transferability assessment, validation and transparent limitations |
| Best Use of Technology | Build a functioning evidence-processing and decision-support system | Working pipeline, modular architecture, deterministic comparison logic, uncertainty handling and end-to-end interaction |
| Local Impact | Address a specific agricultural decision with a credible route to use | User-needs evidence, practical constraints, stakeholder feedback and a plausible impact pathway |

This is the team's internal award strategy, not an official NASA judging rubric or a guarantee of winning. The official award descriptions should be consulted when preparing the final submission [S02].

## 3.1 Product success outcomes

1. Create a field profile from a defined field polygon and available supporting data.
2. Describe historical crop sequence and relevant seasonal environmental patterns.
3. Produce interpretable indicators for selected climate, water and vegetation conditions, with their scale and limitations.
4. Reproduce selected management comparisons from the retrieved Marsden records.
5. Compare the existing and diversified rotation scenarios across environmental, soil-health and operational dimensions.
6. Explain the evidence, potential benefits, trade-offs, assumptions, risks and information gaps for each strategy.
7. Incorporate farmer priorities and operational constraints.
8. Produce a qualified comparison or abstention where the evidence does not support a stronger conclusion.
9. Make the workflow reproducible, traceable and understandable to intended users.

The product is not successful merely because it displays many datasets. Its core success criterion is whether it uses relevant Earth observations and agricultural evidence to help people explore rotation possibilities responsibly.

# 4. Scope and Prioritisation

**MVP definition (revised):** The MVP comprises **both P0 and P1** capabilities. P0 items are the analytical and decision core and must be built first; P1 items are part of the MVP and are built once the P0 core works. Only P2 items are optional or stretch.

## 4.1 P0 — MVP core

- Accept and validate a field polygon or clearly labelled demonstration polygon.
- Build annual crop-history context using USDA Cropland Data Layer (CDL) [S06].
- Retrieve and interpret relevant SSURGO soil survey information [S07, S08].
- Retrieve NASA POWER climate variables and calculate documented temperature and precipitation indicators [S05].
- Acquire and process a bounded HLS sample to investigate seasonal vegetation patterns and bare-field windows; retain only features that add demonstrable value beyond CDL [S03].
- Build a field environmental profile that clearly distinguishes field-scale, grid-scale and regional observations.
- Compare the three rotation scenarios: existing two-year maize–soybean, three-year oat/red-clover and four-year oat/alfalfa systems.
- Integrate retrieved Marsden management records and reproduce documented calculations [S09, S10].
- Describe potential crop/rotation attributes such as nitrogen-fixing potential, forage value, rooting characteristics and seasonal cover only where supported by suitable sources.
- Evaluate strategy trade-offs across the dimensions for which defensible evidence is available.
- Capture farmer priorities and operational constraints, including water availability, manure access, machinery and market/use for alternative crops.
- Implement transparent evidence matching, uncertainty reporting and qualified comparison/abstention.
- Provide provenance, assumptions and limitations for important outputs.

## 4.2 P1 — MVP supporting capabilities (in MVP scope)

- Evaluate NAIP imagery for field inspection, boundary support and visual reference; do not treat it as crop ground truth without appropriate reference interpretation [S11].
- Use USDA NASS QuickStats for county-level agricultural context, not field-level yield validation [S12].
- Evaluate USDA AMS Market News for market evidence relating to alternative rotation crops [S13].
- Compare PRISM with NASA POWER to determine whether it adds useful local climate detail [S14].
- Evaluate SMAP and GPM products for soil-moisture and precipitation context, respecting their spatial scales and product semantics [S16, S17].
- Evaluate terrain-derived erosion susceptibility only if suitable elevation, soil and rainfall inputs and a defensible method are available.
- Collect farmer or agricultural-adviser feedback.
- Provide an interactive map, timelines and side-by-side scenario comparison.

## 4.3 P2 — optional or stretch

- Use CoCoRaHS observations for rainfall comparison where suitable station records are available [S15].
- Use ECOSTRESS for selected land-surface-temperature snapshots; do not infer continuous evapotranspiration monitoring [S04].
- Explore additional NASA datasets, including MODIS, GRACE/GRACE-FO or elevation products, only where they answer a defined question at an appropriate spatial scale.
- Evaluate additional regions or experimental datasets only after the Iowa workflow is validated.

## 4.4 Out of scope

- Guaranteeing yield, profitability or environmental outcomes.
- Predicting exact field-level yield without suitable training data and independent validation.
- Claiming measured soil-carbon gains, erosion reduction or nitrate-leaching reductions from the retrieved Marsden management records.
- Treating satellite products as direct measurements of every soil or crop property.
- Making recommendations outside the supported evidence domain.
- Claiming farmer adoption or realised impact without evidence.
- Presenting a single opaque score as a substitute for explaining the trade-offs between strategies.

# 5. Users, Journey and Functional Requirements

## 5.1 Primary users

- Farmers exploring crop-rotation options under changing environmental conditions.
- Agricultural advisers or extension professionals supporting rotation decisions.

## 5.2 Core user journey

1. Select a field by uploading or selecting a valid polygon; identify demonstration geometry explicitly.
2. Build a field profile from crop history, vegetation observations, soil survey information and climate/water context.
3. Explore environmental patterns over relevant seasons and years, including rainfall, temperature, vegetation development and bare-field windows where data support them.
4. Review what the indicators mean, their spatial/temporal resolution and what they cannot establish.
5. Compare the existing, three-year and four-year rotation strategies.
6. Enter operational constraints and priorities such as water availability, manure, machinery, forage use and market access.
7. Review potential benefits, trade-offs, risks, experimental evidence, assumptions and evidence gaps for each strategy.
8. Review a qualified comparison or abstention and identify questions requiring local expert review.

## 5.3 Functional requirements

| **ID** | **Requirement** | **Acceptance criteria** |
|---|---|---|
| FR-01 | Field input | Accept and validate polygon geometry; report invalid geometry; distinguish real field boundaries from demonstration polygons. |
| FR-02 | Crop history | Retrieve CDL classes intersecting the field and produce a year-by-year summary with product version and resolution recorded. |
| FR-03 | Environmental profile | Calculate selected temperature, precipitation and seasonal indicators from documented products; state spatial/temporal scale and units. |
| FR-04 | Vegetation and bare-field analysis | Apply documented HLS quality masks; calculate selected indices/time-series features; report valid-observation counts, seasonal windows and temporal gaps. |
| FR-05 | Soil profile | Retrieve relevant SSURGO map-unit and component properties; preserve mapped-survey context and uncertainty. |
| FR-06 | Data adequacy | Identify missing inputs, inadequate observations, low-confidence classifications and conflicting evidence. |
| FR-07 | Experimental evidence | Integrate retrieved Marsden records and reproduce selected management comparisons from source data. |
| FR-08 | Crop/rotation evidence | Document relevant crop characteristics and the source/strength of evidence for potential water, cover, forage and soil-health contributions. |
| FR-09 | Strategy comparison | Compare existing, three-year and four-year strategies across dimensions supported by evidence; show unavailable dimensions rather than silently omitting them. |
| FR-10 | Farmer constraints | Capture priorities and operational/market constraints and show how each affects feasibility. |
| FR-11 | Decision output | Present a transparent comparison, qualified assessment or abstention with reasons; do not force a universal ranking. |
| FR-12 | Traceability | Expose sources, data versions, calculations, assumptions and limitations supporting each material output. |

Acceptance criteria must be tested. A requirement is not complete merely because a screen or mock-up exists.

# 6. Data Requirements and Evidence Status

The following status refers to the team's research baseline, not to a completed production integration. A source being reachable does not mean its data have been downloaded, processed or validated.

| **Source / dataset**                  | **Intended role**                                         | **Current status in research baseline**                                | **Priority** |
|---------------------------------------|-----------------------------------------------------------|------------------------------------------------------------------------|--------------|
| NASA HLS \[S03\]                      | Vegetation time series and seasonal crop patterns         | Source assessed; processing and value test required                    | P0           |
| NASA POWER \[S05\]                    | Climate context and indicators                            | Source assessed; processing required                                   | P0           |
| USDA CDL \[S06\]                      | Annual crop-history classification                        | Source assessed; retrieval and processing required                     | P0           |
| SSURGO / Web Soil Survey \[S07, S08\] | Mapped soil properties                                    | Source assessed; retrieval and interpretation required                 | P0           |
| Marsden Farm \[S09, S10\]             | Experimental rotation management evidence                 | Supplementary management records retrieved and inspected               | P0           |
| NAIP \[S11\]                          | Aerial imagery for field inspection and reference support | Resource identified; Iowa coverage and use need verification           | P1           |
| USDA NASS QuickStats \[S12\]          | County/state acreage and production context               | Resource identified; relevant queries required                         | P1           |
| USDA AMS Market News \[S13\]          | Market price and availability context                     | Resource identified; crop/report coverage needs checking               | P1           |
| PRISM \[S14\]                         | Complementary gridded climate data                        | Resource identified; comparative value not yet established             | P1           |
| CoCoRaHS \[S15\]                      | Ground-observed precipitation for comparison              | Resource identified; station coverage and record quality need checking | P2           |
| ECOSTRESS \[S04\]                     | Land-surface-temperature snapshots                        | Optional source assessed; no MVP dependency                            | P2           |
| SMAP / GPM IMERG \[S16, S17\]         | Regional soil-moisture / precipitation context            | Products identified; scale and validation must be assessed             | P2           |

## 6.1 Data provenance requirements

For each source, record provider, product name and version, URL, variables used, spatial and temporal resolution, geographic and historical coverage, retrieval date, access/licence conditions, processing steps, quality flags and known limitations. Preserve original source metadata with processed outputs. For each derived indicator, record its formula, aggregation window, spatial support, missing-data treatment and intended interpretation.

## 6.1.1 Environmental indicator principles

- Precipitation indicators must state whether they come from satellite retrievals, gridded climate products or ground observations.
- Soil-moisture indicators must state product level, spatial footprint and whether the value is retrieved, assimilated or model-derived.
- Land-surface temperature must not be described as air temperature.
- Evapotranspiration estimates must be labelled according to the product's actual method; do not infer continuous field ET from irregular ECOSTRESS snapshots.
- NDVI and related vegetation indices describe spectral vegetation properties; they are not direct measurements of crop yield, soil health or water stress.
- Bare-field windows should be calculated only from adequately sampled, quality-screened observations and should report valid-observation coverage.
- A field-level display must not imply field-level measurement when the underlying product is coarser than the field.

## 6.2 Evidence-type labels

| **Label**                    | **Meaning**                                                           | **Example**                                                   |
|------------------------------|-----------------------------------------------------------------------|---------------------------------------------------------------|
| Observed / retrieved product | A value or product supplied by an instrument, agency or data provider | HLS surface reflectance; GPM precipitation retrieval          |
| Derived indicator            | A calculation made from one or more input variables                   | NDVI; growing-degree-day total                                |
| Classified output            | A class assigned by an algorithm or agency                            | CDL annual crop class; AgroCycle crop-sequence classification |
| Survey information           | Mapped or sampled soil information                                    | SSURGO map-unit/component attributes                          |
| Model / reanalysis output    | A model-derived estimate, not a direct local observation              | NASA POWER climate fields; SMAP root-zone model product       |
| Experimental record          | Data collected within a research experiment                           | Marsden nutrient and herbicide management records             |
| Published finding            | A conclusion reported in a scientific paper                           | Published Marsden yield comparisons                           |
| Assumption / user input      | A design assumption or farmer-supplied constraint                     | Manure access; local market availability                      |

## 6.3 Known limitations to preserve

- CDL is a classified crop product, not ground truth. Agreement between AgroCycle and CDL is agreement with another classification, not independent validation. The CDL product has 30-metre resolution for 2008–2023 and 10-metre resolution from 2024; longitudinal analysis must account for this change \[S06\].

- HLS observations are affected by cloud, shadow and other quality gaps. Crop-specific identification must be evaluated before it influences decisions \[S03\].

- SSURGO represents mapped soil survey units and components; it is not a laboratory measurement from the exact field \[S07, S08\].

- NASA POWER climate information is gridded data and must not be described as direct weather-station measurements at the field \[S05\].

- ECOSTRESS observations are irregular snapshots; they do not establish continuous field evapotranspiration monitoring \[S04\].

- SMAP products have kilometre-scale footprints and product-specific retrieval/model semantics; they must not be presented as direct measurements of moisture in an individual small field \[S16\].

- Field polygons for the proposed demonstration workflow have not yet been confirmed. Obtain actual boundaries or clearly label demonstration geometry.

# 7. Scientific Methodology and Experimental Evidence

## 7.1 Environmental conditions and Earth-observation interpretation

AgroCycle will use NASA and complementary datasets to describe historical environmental conditions relevant to crop-rotation exploration. Candidate indicators include temperature and heat exposure, precipitation totals and variability, dry-spell patterns, soil-moisture context, vegetation development and seasonal bare-field windows.

The selected indicator set must be driven by the question it helps answer, not by the number of available datasets. Each indicator must have a documented definition, source, spatial and temporal scale, quality treatment and limitation.

Examples of interpretation boundaries:

- NASA POWER provides gridded climate information and must not be described as direct field weather-station measurement [S05].
- SMAP products have kilometre-scale footprints and product-specific retrieval/model semantics; they cannot establish soil moisture in an individual small field [S16].
- GPM IMERG is a satellite precipitation product with product-specific retrieval and gauge-adjustment characteristics; it is not a local rain gauge [S17].
- HLS reflectance and vegetation indices can support seasonal vegetation analysis, but cloud gaps, mixed pixels and crop-specific classification uncertainty must be considered [S03].
- ECOSTRESS provides irregular land-surface-temperature observations; these are not continuous field evapotranspiration measurements [S04].
- SSURGO provides mapped soil survey information, not a field-specific laboratory sample [S07, S08].

Environmental indicators may reveal patterns and potential vulnerabilities. They do not, by themselves, prove that a particular rotation will improve yield, soil health or resilience.

## 7.2 Seasonal cover and bare-field periods

The team should investigate whether quality-screened HLS observations can identify periods with low vegetation cover, post-harvest transitions and seasonal regrowth. The analysis should use explicit seasonal windows, mask cloud/shadow/snow and other invalid observations, and report the number and distribution of valid observations.

NDVI can indicate green vegetation but may not distinguish crop species or crop residue reliably. SWIR and other spectral information may help distinguish conditions, but any bare-soil/residue classification requires validation. If observations are insufficient, report the period as unknown rather than classifying it.

## 7.3 Experimental anchor: Marsden Farm

Primary publication: Davis, A.S., Hill, J.D., Chase, C.A., Johanns, A.M. and Liebman, M. (2012), “Increasing Cropping System Diversity Balances Productivity, Profitability and Environmental Health”, PLOS ONE 7(10): e47149 [S09]. The retrieved supplementary management records include seeding, nutrient applications, herbicide applications and weather information for 2003–2011 [S10].

The experiment compares two-, three- and four-year rotation systems. Its findings are experimental evidence from a specific Iowa research setting. They must not be represented as universal field-level predictions.

## 7.4 Reproduced management comparisons

| **Rotation** | **Manufactured N (kg/ha/year)** | **Manure N (kg/ha/year)** | **Total N (kg/ha/year)** | **Herbicide active ingredient (kg/ha/year)** |
|---|---:|---:|---:|---:|
| Two-year | 74.5 | 0.0 | 74.5 | 1.925 |
| Three-year | 16.7 | 39.9 | 56.6 | 0.261 |
| Four-year | 10.9 | 29.9 | 40.8 | 0.195 |

- These are nine-year, rotation-area-weighted annual averages calculated from the retrieved management records; they are not field-level predictions.
- Manufactured nitrogen was approximately 78–85% lower in the diversified systems. This is not equivalent to an 78–85% reduction in total nitrogen input: manure contributed nitrogen to the diversified systems.
- Herbicide active ingredient was approximately 86–90% lower per hectare per year in the diversified systems.
- The publication reports maize and soybean yields in diversified systems that matched or exceeded the two-year system. The retrieved management supplement does not contain the plot-level yield tables needed for AgroCycle to reproduce those yield comparisons independently [S09, S10].
- Do not claim that the retrieved records demonstrate soil-carbon gains, measured erosion reductions or measured nitrate-leaching reductions.

## 7.5 Crop characteristics and potential mechanisms

AgroCycle may explain why crops or rotation phases are considered, but it must cite suitable agronomic sources and distinguish general crop characteristics from locally demonstrated outcomes. For example, legumes may contribute biologically fixed nitrogen under suitable conditions; cover crops may provide living cover during otherwise bare periods; forage crops may provide feed value; and different rooting patterns may affect soil structure. The magnitude and realisation of these benefits depend on species, establishment, management, soil, climate and rotation context.

Do not assume that the Marsden rotation labels or results establish every mechanism or outcome for every field. If suitable crop-characteristic sources are not yet identified, mark the relevant explanation as a research requirement rather than inventing values.

## 7.6 Transferability assessment

AgroCycle must not automatically transfer Marsden findings to every field. It must compare relevant field context with the experimental context, including soil characteristics, climate, crop history, manure access, machinery, market/use and management conditions.

Applicability must be outcome-specific. Lack of manure access limits transfer of manure-dependent nitrogen comparisons but does not automatically invalidate all other experimental findings. Initial applicability rules are conservative team-proposed guardrails and require agricultural expert review; they are not universal agronomic thresholds.

## 7.7 Scientific method requirements

- Document the scientific question, hypotheses and intended interpretation of each indicator.
- Document spatial and temporal alignment between datasets.
- Apply quality masks and report valid-observation denominators.
- Separate direct observations, retrievals, derived indicators, classifications, model outputs, experimental records and published findings.
- Report uncertainty and data gaps alongside outputs.
- Do not infer causality from spatial or temporal association alone.
- Retain source references and reproducible calculations for experimental comparisons.
- Distinguish potential mechanisms from measured outcomes.

# 8. Scenario and Decision Engine

## 8.1 Processing sequence

1. Validate field geometry and identify its source.
2. Assess availability, quality, scale and temporal coverage of required datasets.
3. Build crop-history, soil, climate, water and vegetation profiles.
4. Identify seasonal patterns and potential environmental constraints without overstating what the indicators establish.
5. Evaluate crop/rotation characteristics and the evidence supporting potential mechanisms.
6. Evaluate experimental applicability separately for each outcome.
7. Apply farmer priorities and constraints, including water availability, manure, machinery, forage use and market feasibility.
8. Compare the existing, three-year and four-year rotation strategies across the dimensions supported by evidence.
9. Generate a transparent comparison, qualified assessment or abstention.

## 8.2 Comparison framework

For each strategy, AgroCycle should present:

- **Why it is included:** the crop sequence and the decision objective it may address.
- **Environmental fit:** relevant climate, water and seasonal vegetation context, with scale limitations.
- **Potential soil-health contributions:** mechanisms and experimental findings that are supported by sources.
- **Potential benefits:** evidence-backed outcomes, clearly labelled as experimental, published, inferred or potential.
- **Trade-offs and risks:** water demand, growing-season fit, operational complexity, disease/pest considerations or other relevant issues where evidence exists.
- **Operational feasibility:** machinery, labour, manure, forage use, storage and market access.
- **Evidence gaps:** what cannot be established from available data.

Unavailable or unsupported dimensions must be labelled as unknown or not assessed. They must not be silently treated as neutral or favourable.

## 8.3 Permitted decision outcomes

| **Outcome** | **When it is appropriate** |
|---|---|
| Strategy worth exploring | Available evidence and user priorities make the option a reasonable candidate for further local evaluation; this is not a prescription. |
| Qualified comparison | Evidence supports comparing strategies but is insufficient to identify a preferred option. |
| Abstention | Evidence is missing, inadequate, contradictory or outside the supported applicability domain. |

## 8.4 Required decision output

Each output must identify the field and boundary source; crop-history summary; relevant vegetation, soil, climate and water indicators; data-quality assessment; strategies compared; potential benefits and trade-offs; experimental evidence; farmer constraints; applicability assessment; assumptions and uncertainty; outcome; and explanation of limitations.

The engine must not force a ranking simply because a user expects one. It must be possible to return a comparison without a winner or to abstain.

## 8.5 Decision logic principles

- Use deterministic, documented rules for calculations and comparisons.
- Do not create a composite score unless its components, weights, evidence basis and sensitivity are explicit and justified.
- Do not use missing data as evidence of no risk or no benefit.
- Do not infer field-level crop water use, yield or soil-health change from coarse environmental indicators alone.
- Keep user priorities visible; a strategy may be attractive for one objective and unsuitable for another.

# 9. Market and Operational Feasibility

A rotation can be environmentally or agronomically interesting but operationally impractical if a farmer lacks suitable equipment, labour, manure, storage, buyers or access to a viable market. AgroCycle should therefore treat farmer constraints as first-class inputs, not optional explanatory text.

- Capture farmer priorities, including water availability, soil-health objectives, forage needs and income diversification.
- Capture manure availability and relevant handling constraints.
- Capture machinery, labour and operational constraints relevant to oats, red clover and alfalfa.
- Capture whether a buyer, on-farm use or market channel exists for alternative crops.
- Where appropriate, display USDA AMS market reports as market context, with commodity, location, date, unit and report type clearly identified [S13].
- Use NASS statistics for county-level production context, not field-level yield validation [S12].
- Do not calculate profitability unless suitable yield, input-cost, machinery, labour, transport and price data are available and their assumptions are explicit.
- Treat market price as one input to feasibility, not proof that a crop is profitable or that a buyer is accessible.

# 10. Non-Functional Requirements

| **ID** | **Requirement**                                                                                         |
|--------|---------------------------------------------------------------------------------------------------------|
| NFR-01 | Reproducibility: identical inputs, data versions and configuration must produce consistent outputs.     |
| NFR-02 | Explainability: users can understand the evidence supporting each material output.                      |
| NFR-03 | Auditability: sources, transformations, calculations and decision rules are traceable.                  |
| NFR-04 | Performance: retrieve and process relevant geographic and temporal subsets rather than entire archives. |
| NFR-05 | Reliability: source failures or missing data must not silently create misleading outputs.               |
| NFR-06 | Maintainability: ingestion, processing, evidence evaluation and decision logic are modular.             |
| NFR-07 | Resource efficiency: processing is designed for constrained development hardware.                       |
| NFR-08 | Usability: outputs are understandable to farmers and agricultural advisers.                             |

# 11. Validation and Testing

| **Component**        | **Validation requirement**                                                                     | **Evidence to retain**                                     |
|----------------------|------------------------------------------------------------------------------------------------|------------------------------------------------------------|
| Field geometry       | Geometry validity, spatial intersection and boundary provenance checks                         | Input polygon, validation log, source/owner                |
| CDL crop history     | Compare with suitable independent crop reference data where available                          | Confusion matrix, class-wise metrics, reference provenance |
| HLS processing       | Test quality masks, observation adequacy and whether features add value beyond CDL             | Valid-date counts, gap summaries, comparison results       |
| Soil profile         | Verify map-unit/component interpretation and units                                             | Query, map-unit/component metadata, transformation log     |
| Climate indicators   | Check completeness, units, aggregation and plausibility; compare PRISM/CoCoRaHS only if useful | Source metadata, validation summary                        |
| Marsden calculations | Reproduce management summaries from source supplementary records                               | Code, inputs, outputs and reconciliation to paper          |
| Applicability engine | Test in-domain, out-of-domain and outcome-specific mismatch cases                              | Scenario test matrix and expert review                     |
| Decision engine      | Unit tests for recommendation, qualified comparison and abstention                             | Test reports and example outputs                           |
| User experience      | Review with farmers or agricultural advisers                                                   | Interview notes, feedback and resulting changes            |

A single overall crop-classification accuracy is insufficient; report a confusion matrix and class-specific performance. Clearly distinguish internal tests, agreement with another classified product, independent reference validation and expert review.

# 12. Internal Award-Readiness Rubrics

The following five-point scale is an internal project-management rubric. It is not represented as NASA's official judging scale.

| **Score** | **Meaning**                                                                                                |
|-----------|------------------------------------------------------------------------------------------------------------|
| 1         | Missing: capability is not present.                                                                        |
| 2         | Concept only: described but not implemented.                                                               |
| 3         | Implemented: works, but validation or evidence is limited.                                                 |
| 4         | Validated: implementation and supporting evidence are documented.                                          |
| 5         | Strongly demonstrated: independently reviewable evidence and a clear, compelling end-to-end demonstration. |

## 12.1 Best Use of Data

- NASA data is central to the product's decision, not decorative.

- Relevant datasets are integrated with appropriate spatial/temporal alignment.

- Processing is reproducible and quality-aware.

- Missingness and uncertainty are handled explicitly.

- Field-level outputs are analytically useful.

- Data provenance and versions are visible.

Readiness standard: Demonstrate a traceable path from NASA observations to an indicator and show how that indicator affects the field analysis or decision.

## 12.2 Best Use of Science

- Scientific question is focused and explicit.

- Remote-sensing and agricultural methods are appropriate.

- Experimental evidence is used accurately.

- Calculations are reproducible.

- Transferability is assessed rather than assumed.

- Uncertainty and limitations are disclosed.

Readiness standard: Explain why the evidence supports the output, what it does not support and how the team tested the method.

## 12.3 Best Use of Technology

- Architecture is coherent and modular.

- Data ingestion and processing work reliably.

- Evidence engine is functional and deterministic.

- Uncertainty and abstention are implemented.

- The user can complete the core journey.

- End-to-end behaviour can be demonstrated.

Readiness standard: Show a working system transforming multiple sources into a defensible decision-support result.

## 12.4 Local Impact

- The user problem is specific and evidenced.

- Intended users and their constraints are understood.

- Outputs are relevant to a real decision.

- Operational and market feasibility are considered.

- Impact pathway is credible.

- Stakeholder feedback or measured outcomes are documented.

Readiness standard: Show evidence that the problem matters to intended users and explain how the product could support their decision. Do not claim adoption or realised benefits without evidence.

# 13. Demonstration and Storytelling

**Revision note:** the submission format is a **7-slide deck** (the alternative was a video of 30 seconds or less). The earlier 5-minute timed demo is replaced by the slide plan below.

| **Slide** | **Content** | **What it should prove** |
|---|---|---|
| 1 | The farmer's rotation decision and the changing environmental context | Specific problem and relevance |
| 2 | Field profile: crop history, seasonal vegetation and environmental indicators, from NASA and other data (real screenshots) | Best Use of Data |
| 3 | What the indicators can and cannot establish; Marsden experimental evidence and method | Best Use of Science |
| 4 | Architecture and data lineage: sources to indicators to decision | Best Use of Technology |
| 5 | Comparison of the existing, three-year and four-year strategies against farmer priorities and constraints | Best Use of Technology |
| 6 | Benefits, trade-offs, uncertainties, a qualified assessment or abstention, and validation results | Farmer-centred decision support |
| 7 | Limitations, stakeholder-feedback gap, impact pathway and next steps | Local Impact, honest claims |

Prepare a functioning end-to-end product (the source of the slide screenshots), the 7-slide deck, system architecture, data-lineage diagram, scientific-method explanation, validation examples and cached data in case live retrieval fails. Clearly distinguish implemented functionality from mock-ups and future work. The slides should show NASA observations materially informing the environmental assessment, rather than appearing as decorative map layers.

# 14. Implementation Roadmap

| **Phase** | **Deliverable** | **Exit criteria** |
|---|---|---|
| 1. Project foundation | Repository, environment, PRD and source register | Reproducible project setup and agreed MVP scope |
| 2. Data foundation | Field polygon, CDL baseline and initial supporting data | Data retrieved, inspected and documented; boundary provenance known |
| 3. Environmental and field analytics | Crop history, soil/climate profile, HLS seasonal analysis | Reproducible indicators with quality, scale and limitation reporting |
| 4. Experimental evidence | Marsden calculations and evidence records | Calculations reproduced and source limitations documented |
| 5. Rotation comparison | Three strategy profiles and evidence/trade-off matrix | Each strategy compared consistently; unknowns are explicit |
| 6. Evidence and decision engine | Applicability, farmer constraints and qualified outcomes | Decision tests pass and rules are reviewable |
| 7. Product experience | Integrated user interface | Core user journey works end to end |
| 8. Validation | Technical testing and stakeholder feedback | Results, gaps and corrective actions documented |
| 9. Competition readiness | Demo and submission package | Priority requirements evidenced and claims checked |

Each task must have an owner, contributors, dependencies, target date, status and acceptance criteria. Build the environmental and analytical foundation before investing heavily in interface polish.

# 15. Risks and Dependencies

| **Risk / dependency**               | **Consequence**                                              | **Mitigation**                                                                 |
|-------------------------------------|--------------------------------------------------------------|--------------------------------------------------------------------------------|
| Field polygons not available        | No genuine field-level demonstration                         | Obtain field boundaries or clearly label demonstration geometry                |
| HLS adds little beyond CDL          | Unnecessary processing and unsupported classification claims | Build CDL baseline first; retain HLS only where measured value is demonstrated |
| Independent crop labels unavailable | Weak validation claims                                       | Seek independent records; label CDL agreement accurately                       |
| Marsden evidence does not transfer  | Unsupported field recommendations                            | Use outcome-specific applicability and agricultural expert review              |
| Market information is incomplete    | Cannot assess economic feasibility                           | Show missingness; do not infer profitability from prices alone                 |
| Farmer/adviser feedback unavailable | Weak Local Impact evidence                                   | Conduct and document stakeholder engagement                                    |
| Yield tables unavailable            | Cannot independently reproduce yield comparison              | Attribute published findings and seek additional experimental data             |
| Data access or service failure      | Incomplete analysis or demo                                  | Cache permitted source data and retain reproducible processing outputs         |
| Scope expansion                     | Core product remains unfinished                              | Protect P0; defer optional datasets and features                               |

# 16. Definition of Done and Competition Gate

A capability is complete only when it is implemented, acceptance criteria pass, relevant tests are documented, sources and versions are recorded, calculations and assumptions are traceable, limitations are disclosed, outputs are reproducible and the capability can be demonstrated where required.

☐ The problem and intended user are defined and supported by evidence.

☐ The selected field or demonstration geometry is identified and its provenance recorded.

☐ NASA data plays a meaningful, demonstrable role in understanding environmental conditions.

☐ At least three rotation strategies, including the existing rotation, are compared.

☐ Comparison covers relevant environmental, soil-health and operational dimensions, with unsupported dimensions marked unknown.

☐ Data sources, versions and processing methods are documented.

☐ Crop-history outputs have been evaluated with the correct validation terminology.

☐ Marsden calculations are reproducible from retrieved source records.

☐ Scientific limitations and evidence types are disclosed.

☐ Transferability is assessed rather than assumed.

☐ Farmer operational and market constraints are represented where relevant.

☐ The decision engine can qualify its output or abstain.

☐ The end-to-end product works.

☐ Stakeholder engagement is documented or the gap is explicitly acknowledged.

☐ The slides show actual functionality (real screenshots from the working app, not mock-ups).

☐ Every competition claim is supported by evidence.

# 17. Source Register

The references below provide the source basis for the product framing, dataset descriptions and experimental evidence. Links should be checked again before final submission because data portals, product versions and access conditions can change. A source's inclusion does not mean its data have been ingested into AgroCycle.

**\[S01\] NASA Space Apps Challenge 2026 — Field Shift: Adapting Farms with NASA Data.** Official challenge description and resources. [<u>https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/</u>](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)

**\[S02\] NASA Space Apps Challenge — Awards and Categories.** Official award descriptions; use the 2026 edition when available. [<u>https://www.spaceappschallenge.org/</u>](https://www.spaceappschallenge.org/)

**\[S03\] NASA Harmonized Landsat and Sentinel-2 (HLS).** Product documentation, surface reflectance and quality information. [<u>https://hls.gsfc.nasa.gov/</u>](https://hls.gsfc.nasa.gov/)

**\[S04\] NASA ECOSTRESS Data.** Mission and data-product documentation. [<u>https://ecostress.jpl.nasa.gov/data</u>](https://ecostress.jpl.nasa.gov/data)

**\[S05\] NASA POWER.** Data access, variables and methodology. [<u>https://power.larc.nasa.gov/</u>](https://power.larc.nasa.gov/)

**\[S06\] USDA NASS Cropland Data Layer.** Annual crop classification, product metadata and accuracy documentation. [<u>https://www.nass.usda.gov/Research_and_Science/Cropland/</u>](https://www.nass.usda.gov/Research_and_Science/Cropland/)

**\[S07\] USDA NRCS Web Soil Survey.** Soil survey mapping and soil information access. [<u>https://websoilsurvey.nrcs.usda.gov/app/</u>](https://websoilsurvey.nrcs.usda.gov/app/)

**\[S08\] USDA NRCS Soils Data.** Soil data and SSURGO resources. [<u>https://www.nrcs.usda.gov/resources/data-and-reports/soils</u>](https://www.nrcs.usda.gov/resources/data-and-reports/soils)

**\[S09\] Davis et al. (2012), Increasing Cropping System Diversity Balances Productivity, Profitability and Environmental Health.** Marsden Farm scientific publication; PLOS ONE 7(10): e47149. [<u>https://doi.org/10.1371/journal.pone.0047149</u>](https://doi.org/10.1371/journal.pone.0047149)

**\[S10\] Marsden Farm supplementary data associated with Davis et al. (2012).** Retrieved supplementary management records; preserve original files and licence/provenance. [<u>https://pmc.ncbi.nlm.nih.gov/articles/PMC3468434/</u>](https://pmc.ncbi.nlm.nih.gov/articles/PMC3468434/)

**\[S11\] USDA National Agriculture Imagery Program (NAIP).** Aerial imagery programme and access information. [<u>https://naip-usdaonline.hub.arcgis.com/</u>](https://naip-usdaonline.hub.arcgis.com/)

**\[S12\] USDA NASS QuickStats.** County/state agricultural statistics. [<u>https://quickstats.nass.usda.gov/</u>](https://quickstats.nass.usda.gov/)

**\[S13\] USDA Agricultural Marketing Service — Market News.** Agricultural commodity market reports. [<u>https://www.ams.usda.gov/market-news</u>](https://www.ams.usda.gov/market-news)

**\[S14\] PRISM Climate Group.** Gridded climate data and documentation. [<u>https://prism.oregonstate.edu/</u>](https://prism.oregonstate.edu/)

**\[S15\] Community Collaborative Rain, Hail & Snow Network (CoCoRaHS).** Community precipitation observations and maps. [<u>https://www.cocorahs.org/Maps</u>](https://www.cocorahs.org/Maps)

**\[S16\] NASA Soil Moisture Active Passive (SMAP).** Mission and soil-moisture product documentation. [<u>https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/smap</u>](https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/smap)

**\[S17\] NASA Global Precipitation Measurement (GPM).** GPM and IMERG data access and documentation. [<u>https://gpm.nasa.gov/data</u>](https://gpm.nasa.gov/data)

**\[S18\] USGS EarthExplorer.** Access to selected USGS/NASA Earth observation archives. [<u>https://earthexplorer.usgs.gov/</u>](https://earthexplorer.usgs.gov/)

**\[S19\] Copernicus Data Space Ecosystem.** Sentinel data access; HLS already harmonises Landsat and Sentinel-2 inputs. [<u>https://dataspace.copernicus.eu/</u>](https://dataspace.copernicus.eu/)

**\[S20\] Copernicus Climate Data Store — ERA5 Single Levels.** Alternative climate reanalysis; not an MVP dependency. [<u>https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels</u>](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels)

**\[S21\] FAO Global Agro-Ecological Zones (GAEZ).** Optional crop-suitability and agroecological context. [<u>https://gaez.fao.org/</u>](https://gaez.fao.org/)

**\[S22\] USDA Ag Data Commons.** Repository for discovering agricultural datasets and research data. [<u>https://www.nal.usda.gov/services/agdatacommons</u>](https://www.nal.usda.gov/services/agdatacommons)

**\[S23\] OpenET.** Evapotranspiration data and geographic coverage; not selected for Iowa MVP. [<u>https://etdata.org/</u>](https://etdata.org/)

**\[S24\] USGS National Land Cover Database (NLCD).** Optional land-cover context; not a replacement for CDL crop history. [<u>https://www.usgs.gov/centers/eros/science/national-land-cover-database</u>](https://www.usgs.gov/centers/eros/science/national-land-cover-database)

# Final Product Principle

**AgroCycle should help people explore crop-rotation possibilities by connecting environmental conditions with agricultural evidence and farmer priorities. It must prioritise transparent trade-offs, scientific defensibility and honest uncertainty over the number of datasets, features or recommendations it can display.**
