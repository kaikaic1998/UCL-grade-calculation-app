# UCL MSc Grade Calculator

Double-click **index.html** to open the prototype in a modern browser. It runs offline, with no installation or server.

## Use it

1. Enter each assessment's achieved marks and maximum marks, for example **32 out of 40**. Blank marks are unknown; an entered zero counts as zero.
2. Edit assessment weights and module credits as needed. Assessment weights within each module must total 100%.
3. Read the live module marks and overall reference classification at the top.
4. To calculate required marks, choose an overall or module target and tick **Vary** beside the assessments the solver may change. Fill all other relevant marks. Selected assessments receive the same percentage; the solver holds the rest fixed.
5. Use **Vary project only** to calculate a required dissertation mark once your taught marks are filled. **Apply required marks** copies the solution into the scenario.

The green **assessment map** groups every module's categories and weights into compact cards. It shows missing marks, fixed marks and selected variable assessments. Click a category to toggle **Vary** directly from the summary; it stays in sync with the checkboxes in the detailed module list.

Use **+ Assessment** or **+ Add module** to change the structure. Choose an assessment category from its dropdown. The left-hand checkboxes select items for bulk deletion; **Vary** checkboxes are separate. Deletions can be undone until the next data edit.

## Saving

The app autosaves in your current browser when storage is available. Use **Export JSON** for a portable backup and **Import JSON** to restore one. Import and reset ask before replacing a scenario. Browser storage for local files varies; moving the HTML file or using a different browser may not preserve it. Invalid numeric edits retain the previous recoverable autosave until corrected.

## Rules and limits

- Your eight taught modules and project are preloaded. Supplied assessment weights are editable. COMP0078's two group assessments are combined into a 14% category until their individual weights are known.
- The default 15-credit taught modules and 60-credit dissertation use the previously documented 120 + 60 structure. Direct confirmation for 2026/27 is still pending.
- Separate-pass requirements initially read **Unconfirmed**. Set **Must pass** and a minimum percentage where applicable. Set taught-module condonement independently.
- The app uses UCL's 2026/27 taught postgraduate reference scheme, including alternative Merit/Distinction credit rules, project passing, and standard condonement. Source links and assumptions are inside the app.
- Results remain conditional on unverified programme requirements. Custom credit totals and missing/multiple projects are labelled as custom scenarios.
- The solver uses a 0.01-percentage-point grid and the same decimal rounding as the displayed grades. For example, a 65% taught average and 78.49% dissertation give 69.50% overall after rounding.
- Enter effective marks after any official resit caps or penalties; this prototype does not calculate those adjustments.

## Verification

The app has no runtime dependencies. The optional development check is `python tests/browser_check.py`; it uses an existing Edge/Chrome installation and Python's `websocket-client` package. It runs calculation and real-browser interaction checks in an isolated temporary profile, and writes ignored reports/screenshots under `tests/`.

For a quick manual check: enter 65% for all taught assessments and 80% for the project. The final mark should be **70.00%**. Select **Vary project only** with target **Distinction**: the required project mark should be **78.49%**, conditional on unconfirmed requirements.
