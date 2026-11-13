"""Render the Phase 2B mechanism-diagnostic Markdown report as a readable PDF.

The companion source is ``docs/PHASE2B_MECHANISM_DIAGNOSTIC_CHANGELOG.md``.
This renderer intentionally uses fixed, evidence-report sections rather than
parsing arbitrary Markdown: it preserves the distinction between verified
implementation, fresh development metrics, and unmade research claims. Run
``./.venv-phase2a/bin/python scripts/build_phase2b_change_report.py`` from the
repository root. The PDF is a communication artifact; it does not run policy
training or modify experiment outputs.
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/phase2b_mechanism_diagnostic_change_report.pdf"

def main():
    """Build a two-page summary from the verified values documented in the source report."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet(); styles.add(ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8.5, leading=11))
    story = [Paragraph("Phase 2B Mechanism-Diagnostic Change Report", styles["Title"]),
             Paragraph("12 November 2026 | verified development-only implementation and run", styles["Normal"]), Spacer(1, 12)]
    def section(title, text): story.extend([Paragraph(title, styles["Heading2"]), Paragraph(text, styles["BodyText"]), Spacer(1, 7)])
    section("Purpose", "We added audit-only diagnostics to determine whether honest agents encounter false-food pheromone. This work does not alter PPO inputs, simulator physics, policy parameters, or the attack threat boundary.")
    rows=[["Implemented change","Verified boundary"],["False-food source component","Tracks applied mass through cap/evaporation; does not alter the actual field."],["Normalized 3×3 audit views","Stored only in simulator metadata, never a PPO/detector input."],["Exposure metrics","Counts honest exposed agent-steps and signal magnitude; corpus rejects leakage."],["Replicated plan","Five predeclared action seeds; frozen policies/maps and delayed-200 attack retained."]]
    t=Table([[Paragraph(c,styles["Small"]) for c in r] for r in rows], colWidths=[210,310]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#168f96")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.3,colors.lightgrey),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),5)])); story.extend([t,Spacer(1,10)])
    section("Fresh replicated diagnostic", "Three frozen Candidate J policies × four development maps × five stochastic action seeds produced 60 paired groups and 180 matched episodes. One of four agents was selected; delayed persistent injection began at transition 201 with a 200-unit cap.")
    metrics=[["Measure","Result"],["Mean injection loss","+0.17 honest food units"],["Median injection loss","0 units"],["Harmful groups","14 / 60 (23.3%)"],["Honest-exposure episodes","60 / 60"],["Mean honest exposed agent-steps","2,130.17"],["Applied false-food mass","200 units per attacked episode"]]
    mt=Table(metrics,colWidths=[280,240]); mt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#168f96")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.3,colors.lightgrey),("PADDING",(0,0),(-1,-1),5)])); story.extend([mt,Spacer(1,10)])
    section("Interpretation and verification", "Injection loss is disabled honest delivery minus attacked honest delivery. The positive mean is small, the median is zero, and the result is mixed; it does not establish reliable disruption, a detector, a defense, or robustness. Focused tests: 76 passed. Full pinned suite: 164 passed in 32.86 seconds. Fresh artifacts are under artifacts/phase2b/mechanism-diagnostics-delayed-200-run-001/.")
    section("Next boundary", "A different attack mechanism requires a separate accepted decision record. Final conclusions require unseen maps and a withheld attack configuration. Do not tune or select outcomes solely to increase mean loss.")
    SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=38,leftMargin=38,topMargin=38,bottomMargin=38,title="Phase 2B Mechanism-Diagnostic Change Report").build(story)
    print(OUT)

if __name__ == "__main__": main()
