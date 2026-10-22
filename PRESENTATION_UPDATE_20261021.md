# Presentation-only follow-up - 21 October 2026

## Local path redaction

Five published text records contained machine-specific absolute workspace paths.
Their original workspace prefix is now displayed as the explicit `<WORKSPACE>`
placeholder. The remaining relative suffix and original slash style are retained.
This placeholder is not a real filesystem location and is not an execution claim.

The affected records are the three corrected reference terminal logs, the release
verification text log and `corrected_v110/release_verification.json`. Only the path
prefix changes: original timestamps, software versions, hashes, result values and
the dated scope of each record are retained. Unredacted originals are backed up
outside the Git repository and are not part of the public update. New independent
runs may record their actual local paths again.

## Rolling-coverage chart correction

`_plot_rolling_coverage` previously fixed the lower axis limit at .45. The saved
baseline raw curve reaches 3/7 (about .428571), leaving two points outside that
display range. The axis now spans 0-1.02. A regression calls the real plotting
function and verifies that every finite point in every plotted curve is visible.

Five current `figure_3_rolling_coverage.png` files were redrawn from the unchanged
saved forecast CSVs for baseline, gamma .030, gamma .050 and seeds 20260818/19.
No models were refitted, and no forecasts, interval metrics or downstream P2 input
were changed. Historical and earlier personal-run figures remain untouched. The
active report does not embed this figure, so neither PDF was regenerated.

The latest suite has 28 tests. Earlier logs and the report's 27-test description
remain dated evidence of the preceding update, not a claim about this follow-up.
