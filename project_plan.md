# UCL Grade Calculator: Prototype Scope and Implementation Plan

## Goal

Build a simple, interactive HTML website that opens directly in a browser. It should help me explore the marks needed to pass modules and obtain an overall MSc Pass, Merit, or Distinction, including the dissertation mark needed.

I can edit modules, credits, assessment categories, weights, marks, and maximum available marks. I can add or delete individual assessments or modules, select multiple items for bulk deletion, and see calculations update live.

This document records the agreed prototype scope on 23 October 2026. The first local prototype is implemented in index.html, with usage instructions in README.md and an optional browser verification script in tests/browser_check.py.

## Decisions confirmed with the user

- Provide both direct what-if simulation and calculation of marks needed across selected unfinished assessments.
- Preload the eight supplied taught modules and their supplied assessment weights.
- Start with 15 credits per taught module and a 60-credit dissertation. These values remain editable; the dissertation credit value is provisional pending direct confirmation for 2026/27.
- Support a must-pass toggle and editable minimum mark on each assessment. Initially show separate-pass requirements as unconfirmed.
- Save automatically in the browser and provide JSON export/import for backups and transfer.
- Deliver a local, offline prototype that opens by double-clicking index.html.

## Technical approach

Use one self-contained index.html with embedded CSS and plain JavaScript. No framework, package installation, backend, account, network request, CDN, or development server is needed to use the app.

Keep the code organised into distinct sections for default data, validation, pure grade calculations, the target solver, persistence, and UI rendering. The calculation engine should not depend on the DOM or browser storage.

Use ordinary script tags rather than JavaScript module imports or fetched local files so the page works under file://. Keep README.md as the short usage guide.

## Initial data

All marks start blank, not zero. Defaults below come from the user's supplied module list; assessment weights have not all been independently verified for 2026/27.

| Module | Code | Credits | Assessment categories and weights |
| --- | --- | ---: | --- |
| Supervised Learning | COMP0078 | 15 | Exam 86%; group activity 14% |
| Bayesian Deep Learning | COMP0171 | 15 | Exam 60%; coursework 40% |
| Graphical Models | COMP0080 | 15 | Exam 70%; coursework 30% |
| Reinforcement Learning | COMP0089 | 15 | Exam 50%; coursework 50% |
| Statistical Natural Language Processing | COMP0087 | 15 | Group activity 100% |
| Generative Artificial Intelligence | COMP0264 | 15 | Exam 50%; group activity 50% |
| Applied Machine Learning | COMP0081 | 15 | Exam 50%; coursework 50% |
| Emerging Topics in Machine Learning | COMP0168 | 15 | In-class activity 25%; group activity 35%; coursework 40% |
| MSc Machine Learning Project / dissertation | COMP0091 | 60, provisional | Dissertation/project 100% |

COMP0078's two group assessments are initially represented by one combined 14% category because their individual weights were not supplied. The user can split this category later without the app inventing a split.

The initial total is 180 credits: 120 taught credits plus 60 project credits. Both modules without exams still contribute to the degree calculation.

## UI and editing behaviour

Use a compact, responsive dashboard with an overall results summary, a target calculator, and editable module cards or rows. Prioritise readable numbers and clear labels over decorative graphics.

Each module has an editable name, optional code, positive credit value, and taught/project designation. Each assessment has an editable label, type, weight, achieved mark, and maximum mark. Types include exam, coursework, group activity, in-class activity, dissertation/project, and other.

- Accept marks such as 32 out of 40, with 100 as the default maximum.
- Allow multiple assessments of the same type, each with a distinct ID.
- Show each assessment percentage and contribution to its module.
- Show each module's resulting mark, pass status, and contribution to the degree.
- Add and delete modules or assessments, including the preloaded dissertation.
- Support module and assessment selection with checkboxes and bulk deletion.
- Keep deletion selection separate from the selection used by the target calculator.
- Provide a brief undo action for deletions; importing data and resetting defaults must not silently overwrite existing work.
- Update results on every valid edit while preserving typing focus.
- Label the editable marks as scenario inputs; entering a value does not imply it is an official result.

Assessment weights within a module must total 100%. Show the total and an inline error when they do not. Never silently redistribute weights or normalise an invalid module. Preserve the user's entries while explaining which results cannot currently be calculated.

Blank marks mean unknown. A typed zero is a real score. Show incomplete results explicitly and optionally a possible mark range; never silently treat blanks as zero in a final grade or claim a classification from incomplete data.

## Calculation rules and evidence

Use the UCL 2026/27 taught postgraduate classification scheme as the default reference rules. Keep thresholds together in the code and show their sources in a small expandable explanation.

1. Convert an assessment mark to a percentage using achieved / maximum * 100.
2. Apply assessment weights to calculate its module mark, following UCL's two-decimal percentage and module-mean rounding requirements.
3. Calculate the degree mark as the credit-weighted mean of all module marks, rounded to two decimal places.
4. With the provisional 120/60 structure, degree mark = (120 * taught average + 60 * project mark) / 180. If credits change, always use the actual entered credit values.
5. The standard Level 7 module pass mark is 50.00%. Also check configured assessment-level must-pass requirements.
6. Distinction: final weighted mark >= 69.50%, or >= 68.50% with module marks >= 70.00% in at least 50% of all credits.
7. Merit: final weighted mark >= 59.50%, or >= 58.50% with module marks >= 60.00% in at least 50% of all credits.
8. Pass: meet the Masters award requirements. A high overall average alone is insufficient.
9. The dissertation/project must be passed. Do not impose a separate dissertation mark of 70% for Distinction under the taught MSc scheme.
10. Count credits, including dissertation credits, for the alternative Merit and Distinction routes. Do not count numbers of modules.

For award eligibility, track whether a taught module's condonement status is unknown, condonable, or must-pass. Standard Masters condonement allows no more than 30 taught credits in the 40.00-49.99% range, with all non-condonable modules and the dissertation passed, no marks below the applicable range, and a credit-weighted mean of at least 50.00%. If eligibility depends on an unknown designation, show a conditional outcome rather than claiming an award.

Assessment separate-pass settings should distinguish unconfirmed, no separate requirement, and must-pass with a configurable threshold. Unknown requirements remain visible and calculated outcomes are conditional on them. Do not assume every exam requires 50% or that none does.

Changing the total away from 180 credits, deleting the project, or introducing multiple projects makes the setup a custom scenario. Continue valid numerical calculations, but distinguish a reference classification from verified eligibility for this UCL MSc. A matching total of 180 credits alone does not verify programme compliance.

Use decimal-safe rounding consistent with the rules; specifically verify boundary cases rather than relying on uncorrected floating-point arithmetic.

### Official sources and verification limits

- 2026/27 Machine Learning MSc programme page: confirms 180 total credits and the compulsory project. https://www.ucl.ac.uk/prospective-students/graduate/taught-degrees/machine-learning-msc-2026
- Academic Manual, Chapter 4, Section 4.5: taught postgraduate weighting and classification. https://www.ucl.ac.uk/study/current-students/academic-manual/chapters/chapter-4-assessment-framework-taught-programmes/section-4-classification
- Chapter 4, Sections 2.3, 2.5, and 2.6: pass marks, component calculations, and module pass requirements. https://www.ucl.ac.uk/study/current-students/academic-manual/chapters/chapter-4-assessment-framework-taught-programmes/section-2-module-assessment
- Chapter 4, Sections 3.2 and 3.10: condonement and Masters award requirements. https://www.ucl.ac.uk/study/current-students/academic-manual/chapters/chapter-4-assessment-framework-taught-programmes/section-3-progression-award
- Older official UCL programme presentation: eight 15-credit modules and a 60-credit dissertation. This is supporting historical evidence, not direct 2026/27 confirmation. https://www.ucl.ac.uk/prospective-students/open-days/sites/prospective-students_open-days/files/machine-learning.pdf

The current project catalogue entry could not be retrieved during research. Its 60-credit value and individual module/component designations must not be presented as fully verified for 2026/27. Do not fetch regulations automatically at runtime.

## Simulation and target solving

### Direct what-if mode

The user enters or changes hypothetical assessment marks, including project marks. Update module results, the degree average, qualifying credits, and conditional Pass/Merit/Distinction status live.

### Required-mark mode

- Let the user choose a module target of 50%, 60%, 70%, or a custom percentage, or an overall degree target of Pass, Merit, or Distinction.
- Let the user explicitly select assessments whose marks may vary. Hold every other entered mark fixed, even if it is hypothetical.
- For multiple selected assessments, solve for the lowest common percentage required across them. Explain this assumption next to the result: other combinations of different marks may also work.
- For a dissertation-only calculation, select its assessment and hold all taught marks fixed.
- If an unselected assessment required for the calculation is blank, identify the missing input instead of assuming its mark.
- Evaluate overall classification targets through the complete classification and award logic, including qualifying credits, project passes, known must-pass requirements, and applicable condonement.
- Unknown pass/condonement requirements make solver results conditional; show the relevant assumption.
- Return the minimum feasible common percentage on a 0.01-percentage-point grid using the same rounding pipeline as the main calculator. A bounded monotonic search can locate the first feasible grid value.
- Show the achieved module/degree result after applying the proposed marks. Offer an explicit Apply action instead of changing inputs while merely displaying a solution.
- Distinguish already achieved, achievable, missing information, invalid setup, and impossible within 0-100%. Explain a fixed failed requirement or insufficient available marks.
- A computed requirement of 0% does not imply permission to skip an assessment. A module target of 70% is distinct from an overall MSc Distinction.

## Data and persistence

Represent each module with a stable ID, name/code, credits, taught/project type, condonement designation, and assessment list. Each assessment has a stable ID, type/label, weight, nullable achieved mark, maximum mark, and separate-pass setting.

Store a versioned JSON document containing modules and relevant scenario settings. Keep transient delete selections out of saved academic data.

Save to localStorage after valid state changes. Preserve incomplete edits where safe without replacing the last recoverable saved state with corrupt data. Catch unavailable storage, quota errors, and malformed saved data, and show an understandable message.

Browser storage under file:// can vary by browser and file location. JSON export/import is the portable backup mechanism. Validate imports before replacing state, including schema/version, unique IDs, numeric bounds, and supported values. Render imported labels as text, not HTML.

## Implementation sequence

1. Create the default data and pure calculation/validation functions; establish precision and eligibility states.
2. Build the editable module and assessment UI, live summary, addition/deletion, bulk selection, and undo.
3. Add direct simulation and the target solver, including dissertation-only and multiple-assessment calculations.
4. Add browser autosave, JSON export/import, reset behaviour, and recovery messages.
5. Check meaningful calculation boundaries and core browser interactions; write brief opening and backup instructions in README.md.

## Acceptance checks

- Double-clicking index.html opens a fully usable app offline with no server or installation.
- All nine default entries and their supplied assessment weights appear correctly.
- With taught average 65% and project 80% under the default credits, the final mark is 70.00%.
- With taught average 75% and project 60%, the final mark is 70.00%; the taught MSc rules add no separate 70% project condition.
- In a 50/50 module, non-exam 60% plus exam 40% gives a 50.00% module average; adding a must-pass exam threshold of 50% changes its eligibility and solver requirement.
- Degree boundary checks cover 69.50%, 68.50% with/without 90 qualifying credits, and the corresponding Merit routes.
- A 70% 60-credit project contributes 60 qualifying credits; another 30 credits at 70% reach the 90-credit condition.
- A failed project blocks an MSc award regardless of the overall average; condonement limits and unknown designations produce the appropriate states.
- A dissertation-only solver with taught average 65% returns 78.49% for the 69.50% Distinction route when the alternative credit route is unavailable. This is the minimum on the 0.01% grid after the final mean is rounded to two decimals; 78.50% remains a conservative target.
- Blank/zero differences, non-100% weights, impossible targets, rounding boundaries, custom credit totals, missing projects, and empty module lists are handled clearly.
- Single and bulk deletion update calculations immediately; undo restores the affected data.
- Reload restores saved data when storage is available; export/import round-trips marks and structure, and invalid imports do not destroy the active scenario.
- Inputs and selection controls are keyboard accessible and usable on a narrow screen.

Use a small dependency-free calculation test harness where practical, plus a focused browser smoke check. If browser automation is unavailable, record that limitation and provide manual verification steps.

## Outside this prototype

No backend, login, cloud synchronisation, hosting/deployment, transcript import, PDF generation, external integrations, or automatic retrieval of university regulations. No general optimisation that assigns a different score to every unknown assessment, detailed reassessment/penalty workflow, or verification of module selection permissions. Existing effective/capped marks can be entered manually.

The first prototype is a self-contained local HTML file. Keep further changes focused on feedback from using it.
