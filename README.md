# UCL MSc Grade Calculator

Double-click **index.html** to open the prototype in a modern browser. It runs offline, with no installation or server.

## Use it

1. Enter each assessment's achieved marks and maximum marks, for example **32 out of 40**. Blank marks are unknown; an entered zero counts as zero.
2. Edit assessment weights and module credits as needed. Assessment weights within each module must total 100%.
3. Read the live module marks and overall reference classification at the top.
4. Change any exam, coursework, or dissertation mark to explore different outcomes. The grades and summary update automatically.

The green **Module overview** groups every module's categories and weights into compact cards. It shows entered percentages, missing marks, and resulting module grades. Edit assessment inputs in the detailed module list below.

## Estimate marks for an overall MSc target

Choose **Pass**, **Merit**, or **Distinction** in the overview and enter a percentage for **blanks in OTHER modules** (initially 70%). Every module card is a separate what-if for that overall MSc target:

- Its entered marks stay fixed, and the calculator finds the same required percentage for all its blank assessments.
- Other modules keep their entered marks; their blank assessments use your chosen assumption.
- If the module is fully entered, the card instead shows the required exam mark and how its entered exam mark compares. For multiple exams, the what-if uses one common percentage for those exams. A completed project shows the required project mark. A completed module without an exam stays fixed.
- Cards show required percentages, approximate raw marks out of each assessment's maximum, the resulting module/MSc marks, and unmet requirements or unreachable targets.

**These are independent alternatives. Do not combine the suggested marks from different cards into one forecast.** Estimates never overwrite your entered marks, and no Vary selection is needed. Adding/deleting assessments or changing marks, weights, credits, or maximum marks recalculates the cards live. Invalid weight totals appear inside the affected card and block estimates until corrected.

Pass/Merit/Distinction badges show which levels your entered scenario meets when complete. While marks are blank, the badges show a **baseline projection** using your assumed percentage for every blank; these are labelled **Projected**, not already achieved. Unconfirmed requirements and custom programme structures remain clearly labelled.

Use **+ Assessment** or **+ Add module** to change the structure. Choose an assessment category from its dropdown. The checkboxes select items for bulk deletion. Deletions can be undone until the next data edit.

## Manage assessment categories

Open **Manage assessment categories**, between the overview and the module editor.

- **Add** any category name you need, such as Lab report, Presentation, or Participation. It becomes available in every assessment dropdown.
- **Rename** a category and click **Save** to update all assessments using it. Individually written assessment labels are preserved; labels that matched the old category name update automatically.
- Enable **Treat as exam** for categories used by completed-module exam estimates. Renaming Exam to Written test therefore preserves its exam behaviour.
- **Remove** unused categories directly. If a category is in use, choose a replacement first; assessments, weights and marks are kept. You can undo the removal until your next data edit.

The defaults include Exam, Coursework, Group activity, In-class activity, and Dissertation/project. There is no preset Other option. Older backups using Other migrate those assessments to an editable **Custom assessment** category. Categories and exam settings are included in autosave and JSON backups. If all categories are removed, add one before adding assessments.

## Saving

The app autosaves marks, categories, the target and the assumed percentage in your current browser when storage is available. Use **Export JSON** for a portable backup and **Import JSON** to restore one. Older backups without forecast settings load with a Distinction target and 70% assumption. Import and reset ask before replacing a scenario. Browser storage for local files varies; moving the HTML file or using a different browser may not preserve it. Invalid numeric edits retain the previous recoverable autosave until corrected.

## Rules and limits

- Your eight taught modules and project are preloaded. Supplied assessment weights are editable. COMP0078's two group assessments are combined into a 14% category until their individual weights are known.
- The default 15-credit taught modules and 60-credit dissertation use the previously documented 120 + 60 structure. Direct confirmation for 2026/27 is still pending.
- Separate-pass requirements initially read **Unconfirmed**. Set **Must pass** and a minimum percentage where applicable. Set taught-module condonement independently.
- The app uses UCL's 2026/27 taught postgraduate reference scheme, including alternative Merit/Distinction credit rules, project passing, and standard condonement. Source links and assumptions are inside the app.
- Results remain conditional on unverified programme requirements. Custom credit totals and missing/multiple projects are labelled as custom scenarios.
- Component percentages, module marks, and the final mean are rounded to two decimal places.
- Enter effective marks after any official resit caps or penalties; this prototype does not calculate those adjustments.

## Verification

The app has no runtime dependencies. The optional development check is `python tests/browser_check.py`; it uses an existing Edge/Chrome installation and Python's `websocket-client` package. It runs calculation and real-browser interaction checks in an isolated temporary profile, and writes ignored reports/screenshots under `tests/`.

For a quick manual check: enter 65% for all taught assessments and 80% for the project. The final mark should be **70.00%**. Change the project to 60%; the final mark should update to **63.33%**.

With a 65% taught average and the target set to Distinction, the project estimate should show **78.49%**, including UCL's final rounding. With project 60% entered, the badges should show Pass and Merit met, and Distinction not met, conditional on any unconfirmed requirements.
