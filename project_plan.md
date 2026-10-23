# UCL Grade Calculator: Prototype Scope and Implementation Plan

## Goal

Build a simple, interactive HTML website that opens directly in a browser. It should help me explore module and overall MSc grades by entering hypothetical assessment marks, including dissertation marks, and estimate the marks needed for a selected overall MSc target.

I can edit modules, credits, assessment categories, weights, marks, and maximum available marks. I can add or delete individual assessments or modules, select multiple items for bulk deletion, and see calculations update live.

This document records the agreed prototype scope on 23 October 2026. The first local prototype is implemented in index.html, with usage instructions in README.md and an optional browser verification script in tests/browser_check.py.

## Decisions confirmed with the user

- Provide direct simulation plus automatic, independent per-module estimates for an overall MSc Pass, Merit, or Distinction target. No Vary controls or generated-mark Apply action.
- Estimate blank marks automatically while preserving entered marks. Use the same required percentage for all blanks within the module being estimated.
- The user chooses the percentage assumed for blanks in OTHER modules. Every module card is a separate what-if; its estimates cannot be combined with the estimates in other cards as one forecast.
- For a fully entered module, estimate the exam mark needed instead. Show the difference from the entered exam mark. A completed project estimates its project mark; a completed module with no exam remains fixed.
- Show all three overall classification indicators, including lower levels already met. Clearly distinguish actual entered-scenario results from projections based on assumed marks.
- Preload the eight supplied taught modules and their supplied assessment weights.
- Provide a shared editable category library: users can add, rename, and remove categories. Remove the preset Other option. Categories can be marked as exams independently of their names, so renaming does not break completed-exam estimates.
- Start with 15 credits per taught module and a 60-credit dissertation. These values remain editable; the dissertation credit value is provisional pending direct confirmation for 2026/27.
- Support a must-pass toggle and editable minimum mark on each assessment. Initially show separate-pass requirements as unconfirmed.
- Save automatically in the browser and provide JSON export/import for backups and transfer.
- Deliver a local, offline prototype that opens by double-clicking index.html.

## Technical approach

Use one self-contained index.html with embedded CSS and plain JavaScript. No framework, package installation, backend, account, network request, CDN, or development server is needed to use the app.

Keep the code organised into distinct sections for default data, validation, pure grade calculations, independent target estimates, persistence, and UI rendering. The calculation engine should not depend on the DOM or browser storage.

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

Use a compact, responsive dashboard with overall results, a green visual Module overview, and editable module cards or rows. The overview has an overall target selector and a percentage assumption for blanks in other modules. It groups categories and weights by module, shows entered/estimated/missing marks and per-module what-if results, and has no internal scrolling. Estimates are read-only; assessment inputs remain in the module editor below. Prioritise readable numbers and clear labels over decorative graphics.

Each module has an editable name, optional code, positive credit value, and taught/project designation. Each assessment has an editable label, category, weight, achieved mark, and maximum mark. The category dropdown comes from a shared user-editable library, initially Exam, Coursework, Group activity, In-class activity, and Dissertation/project.

Manage categories in an expandable section between the overview and the module editor. Adding a category makes it available in every assessment dropdown. Renaming updates all uses, preserving separately written assessment labels. Removing an in-use category requires reassignment to another category; it must preserve assessments, weights and marks. Unused categories can be removed directly, and removals support undo. Category names must be nonempty and unique ignoring case. A Treat as exam setting controls completed-module exam estimates independently of the category name.

- Accept marks such as 32 out of 40, with 100 as the default maximum.
- Allow multiple assessments of the same type, each with a distinct ID.
- Show each assessment percentage and contribution to its module.
- Show each module's resulting mark, pass status, and contribution to the degree.
- Add and delete modules or assessments, including the preloaded dissertation.
- Support module and assessment selection with checkboxes and bulk deletion.
- Checkboxes select modules and assessments for deletion only.
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

## Simulation and independent target estimates

### Direct what-if mode

The user enters or changes hypothetical assessment marks, including project marks. Update module results, the degree average, qualifying credits, and conditional Pass/Merit/Distinction status live.

The user controls all entered marks directly. Estimates are display-only; blanks remain blank in saved academic data.

### Overall target estimates

- Choose the overall MSc target: Pass, Merit, or Distinction, using the full credit-weighted classification and award rules. Do not substitute 50/60/70% module targets.
- Set an assumed percentage for unfinished assessments in OTHER modules, initially 70%.
- For each module independently, keep its entered marks fixed and solve for a common percentage across its blanks. Keep other modules' entered marks fixed and fill only their blanks with the user's assumption.
- For a fully entered taught module, the adjustable what-if is its exam assessment(s), using the same percentage if there are multiple exams. Hold all non-exam marks fixed. A completed project varies its project assessment(s). A completed taught module without an exam reports that it is fixed.
- Find the minimum on a 0.01-percentage-point grid through the same decimal rounding, credit-preponderance and award-check pipeline used by the main calculator.
- Display required percentages and approximate raw marks out of the assessment's entered maximum, projected module/MSc grades, and the assumption used. Show comparison with entered exam marks for completed modules.
- Mark impossible targets when even 100% in the adjustable assessments cannot meet the target under the other entered/assumed marks. Explain known blockers, including failed must-pass requirements or a failed fixed project.
- Clearly label condonement, unconfirmed requirements, and custom programme structures. Invalid inputs and missing/invalid assumptions block affected estimates.
- Each card is an independent alternative. Do not combine estimates from separate cards, and never overwrite entered marks automatically.
- The overall Pass/Merit/Distinction badges use entered marks when complete, otherwise a separately labelled baseline projection with every blank at the assumption. A projected result must not be called already achieved.
- Updates to marks, maximum marks, assessment/module additions/deletions, weights, credits, target, or assumption refresh the results immediately.

## Data and persistence

Represent each module with a stable ID, name/code, credits, taught/project type, condonement designation, and assessment list. Each assessment has a stable ID, category/label, derived exam designation, weight, nullable achieved mark, maximum mark, and separate-pass setting. Store category records with stable IDs, unique editable names, and exam designations; all assessment category references must resolve to that library.

Store a versioned JSON document containing modules, marks, categories and exam designations, and forecast target/assumption settings. Keep transient delete selections out of saved academic data. Existing version 1 backups remain compatible; absent forecast settings use Distinction/70% defaults, while obsolete Vary settings are ignored without losing marks or modules. Legacy backups without a category library infer their used categories and migrate Other to an editable Custom assessment category without losing marks.

Save to localStorage after valid state changes. Preserve incomplete edits where safe without replacing the last recoverable saved state with corrupt data. Catch unavailable storage, quota errors, and malformed saved data, and show an understandable message.

Browser storage under file:// can vary by browser and file location. JSON export/import is the portable backup mechanism. Validate imports before replacing state, including schema/version, unique IDs, numeric bounds, and supported values. Render imported labels as text, not HTML.

## Implementation sequence

1. Create the default data and pure calculation/validation functions; establish precision and eligibility states.
2. Build the editable module and assessment UI, live summary, addition/deletion, bulk selection, and undo.
3. Add direct simulation and the visual module overview, including dissertation marks, independent target estimates, and overall classification progress indicators.
4. Add browser autosave, JSON export/import, reset behaviour, and recovery messages.
5. Check meaningful calculation boundaries and core browser interactions; write brief opening and backup instructions in README.md.

## Acceptance checks

- Double-clicking index.html opens a fully usable app offline with no server or installation.
- All nine default entries and their supplied assessment weights appear correctly.
- With taught average 65% and project 80% under the default credits, the final mark is 70.00%.
- With taught average 75% and project 60%, the final mark is 70.00%; the taught MSc rules add no separate 70% project condition.
- In a 50/50 module, non-exam 60% plus exam 40% gives a 50.00% module average; adding a must-pass exam threshold of 50% changes its eligibility.
- Degree boundary checks cover 69.50%, 68.50% with/without 90 qualifying credits, and the corresponding Merit routes.
- A 70% 60-credit project contributes 60 qualifying credits; another 30 credits at 70% reach the 90-credit condition.
- A failed project blocks an MSc award regardless of the overall average; condonement limits and unknown designations produce the appropriate states.
- Editing the project from 80% to 60% with a taught average of 65% updates the final mark from 70.00% to 63.33%.
- With all taught marks at 65%, the independent project estimate for Distinction is 78.49%, after final rounding; another module's estimates must not change entered marks.
- Changing the assumed score in other modules changes individual estimates/reachability. Multiple blanks within the estimated module receive the same required percentage.
- Completed modules show exam comparisons; no-exam completed modules remain fixed. Actual Merit results show both Pass and Merit met while Distinction is not met.
- Blank scenarios show projected classification indicators, not achieved classifications. Invalid weights or known award blockers prevent incorrect target claims.
- Blank/zero differences, non-100% weights, rounding boundaries, custom credit totals, missing projects, and empty module lists are handled clearly.
- Single and bulk deletion update calculations immediately; undo restores the affected data.
- Custom categories appear in dropdowns, survive reload and JSON round-trips, and support rename/reassignment without losing assessment data. Renaming an exam category preserves its forecast role. Reject duplicate/blank category names and dangling category references.
- Reload restores saved data when storage is available; export/import round-trips marks and structure, and invalid imports do not destroy the active scenario.
- Inputs and selection controls are keyboard accessible and usable on a narrow screen.

Use a small dependency-free calculation test harness where practical, plus a focused browser smoke check. If browser automation is unavailable, record that limitation and provide manual verification steps.

## Outside this prototype

No backend, login, cloud synchronisation, hosting/deployment, transcript import, PDF generation, external integrations, or automatic retrieval of university regulations. No Vary-selection workflow, automatic application of generated marks, combined optimisation across modules, detailed reassessment/penalty workflow, or verification of module selection permissions. Existing effective/capped marks can be entered manually.

The first prototype is a self-contained local HTML file. Keep further changes focused on feedback from using it.
