"""Build the concise twelve-page implementation handbook from verified artifacts.

Run after run_review_budget.py and review_evidence.py figures have completed:
python scripts/build_review_handbook.py --root artifacts/review-eight
Requires optional document-authoring packages reportlab and pypdf, which are
not simulator/training runtime dependencies. Input manifests/summaries/actual
PNG figures supply numeric evidence. The stable output is output/pdf/
capstone_implementation_handbook.pdf. Twelve fixed chapters, linked contents,
bookmarks and searchable embedded fonts support team reading and presentation.
Old two-agent results remain explicitly historical, not overwritten evidence.

This is document authoring, not an experiment. It never changes policies or
mechanics. After generation render EVERY page with pdftoppm and visually inspect
it; page-count validation alone cannot certify clipping or figure readability.
The code deliberately fails if the fixed twelve-page layout overflows. Source
revision and dirty state describe the measured working tree; training manifests
contain per-module hashes. Keep generated PDFs/images separate from code claims.
"""
import argparse
from html import escape
import json
from pathlib import Path
import subprocess

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, Preformatted
from pypdf import PdfReader


def build(root, output):
    """Use completed artifact evidence and preserve an exact twelve-page limit."""
    train=json.loads((root/'training/summary.json').read_text())
    comparison=json.loads((root/'comparison/summary.json').read_text())
    sensitivity=json.loads((root/'sensitivity/summary.json').read_text())
    budget=json.loads((root/'budget.json').read_text())
    for folder in ['training','comparison','sensitivity']:
        assert json.loads((root/folder/'manifest.json').read_text())['status']=='completed'
    revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    fonts=Path('/usr/share/fonts/truetype/dejavu')
    for name,file in [('D','DejaVuSans.ttf'),('DB','DejaVuSans-Bold.ttf'),('DM','DejaVuSansMono.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
    pdfmetrics.registerFontFamily('D',normal='D',bold='DB',italic='D',boldItalic='DB')
    styles={
        'body':ParagraphStyle('body',fontName='D',fontSize=9.5,leading=13,spaceAfter=7,textColor=colors.HexColor('#26384a')),
        'small':ParagraphStyle('small',fontName='D',fontSize=8.1,leading=10.7,spaceAfter=5),
        'h1':ParagraphStyle('h1',fontName='DB',fontSize=17,leading=22,spaceAfter=13,textColor=colors.HexColor('#137c78')),
        'h2':ParagraphStyle('h2',fontName='DB',fontSize=11,leading=15,spaceBefore=6,spaceAfter=6),
        'code':ParagraphStyle('code',fontName='DM',fontSize=8,leading=11,backColor=colors.HexColor('#edf2f6'),borderPadding=7,spaceAfter=10),
        'caption':ParagraphStyle('caption',fontName='D',fontSize=8,leading=10.5,spaceAfter=7,textColor=colors.HexColor('#425b70'))}
    story=[]
    titles=['Project idea and reading guide','Stigmergy: what an agent does','Environment and local inputs','One simulator step and field values','Shared PPO: interaction and training','Threat model and matched controls','Local history and timeout defense','Files, logs and what to edit','Actual simulator screenshots','Measured PPO and comparison results','Setup, commands and reproducibility','Two-slide demo and remaining work']
    class Handbook(SimpleDocTemplate):
        def afterFlowable(self, flowable):
            if getattr(flowable,'bookmark',None):
                self.canv.bookmarkPage(flowable.bookmark)
                self.canv.addOutlineEntry(flowable.getPlainText(),flowable.bookmark,level=0,closed=False)
    def p(text,style='body'):
        story.append(Paragraph(text,styles[style]))
    def h(text):p(text,'h2')
    def code(text):story.append(Preformatted(text,styles['code']))
    def table(rows,widths):
        data=[[Paragraph(escape(str(v)),styles['small']) for v in row] for row in rows]
        t=Table(data,colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcece9')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#bfd0d8')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.append(t);story.append(Spacer(1,8))
    def pic(name,width=510):
        im=Image(str(root/'figures'/name)); im.drawHeight=im.imageHeight*width/im.imageWidth;im.drawWidth=width;story.append(im);story.append(Spacer(1,4))
    def chapter(i):
        if i>1:story.append(PageBreak())
        item=Paragraph(f'{i}. {titles[i-1]}',styles['h1']);item.bookmark=f'chapter-{i}';story.append(item)
    chapter(1)
    p('<b>Robust Stigmergic Coordination</b><br/>Team edition for Aarya, Shashannk, Rohan and Tusti. Updated 9 October 2026. Readable overview of implemented behavior, measured development evidence and remaining research work.')
    h('What we are building')
    p('A simulated team searches a grid, picks up food and delivers it to a nest. Agents communicate indirectly through shared food/home pheromone fields. One parameter-shared PPO network chooses each agent\'s movement from its local view. A selected minority can add misleading food pheromone. We investigate whether a local-history defense can reduce disruption without hurting clean performance.')
    p('<b>Current demonstration:</b> corrected nest-anchored home deposits, eight agents with one selected attacker (12.5%), fresh clean PPO training, persistent injection and a fixed timeout baseline. The learned detector, other attack modes, required trained baselines and held-out robustness evaluation are still future work.')
    h('Contents and recommended order')
    for i,title in enumerate(titles,1):p(f'<link href="#chapter-{i}" color="#137c78">{i:02d}  {title}</link>','small')
    h('Evidence scope and source')
    p(f'Measured uncommitted source based on revision <b>{revision[:12]}</b>. Per-module SHA-256 hashes are in training/comparison manifests. New evidence: <b>artifacts/review-eight/</b>. Historical two-agent evidence: <b>artifacts/review-current/</b>. Decision 0005 authorizes the mechanics and diagnostic changes. No hardware validation or publication/robustness claim follows.','small')
    chapter(2)
    h('Stigmergy means leaving information in the environment')
    p('Agents do not send messages to each other. A pheromone field is a grid of nonnegative numbers that other agents can sense nearby. Deposits accumulate, are capped and evaporate. A trail contains its concentration, not the identity of whoever deposited it. Therefore this implementation cannot award trust to agent A or blame agent B from a shared trail.')
    h('An honest trip, step by step')
    p('An empty agent leaves the nest to search. While moving outside it deposits home pheromone, with an amount that weakens as its movement counter grows. At a resource cell it picks up one unit and becomes carrying. Pickup happens before deposition, so that cell gets food pheromone. As the loaded agent returns, it adds food pheromone to its actual occupied cells. At the nest it delivers, becomes empty and deposits home pheromone.')
    p('Other empty agents can see food pheromone and use it as one part of their local policy input. Carrying agents can see home pheromone and nearby nest cells. PPO must learn how to use those cues; depositing trails alone does not guarantee sensible following. There is no built-in global shortest-path guidance for PPO.')
    h('Why a false trail can mislead')
    p('A compromised agent adds extra food-channel concentration without needing to have collected food. Nearby agents see the combined field, not an authenticity flag or author ID. The attacker does not create actual food. The simulator knows which mass was injected for auditing, but that information is not available to the policy or runtime defense.')
    h('What the corrected home rule does')
    p('Each nest visit resets a movement counter. Successful outside moves increment it. Empty outside movement deposits <b>1 × .95^counter</b>; waiting or blocked movement outside deposits nothing. Empty nest occupancy deposits 1. This removes the former waiting hotspot and anchors outbound deposits to nest visits. Multiple agents, repeated routes and differently aged trails can still overlap, so a globally monotonic gradient is not guaranteed.')
    h('Research question versus evidence')
    p('The intended question concerns robust learned coordination under withheld maps and attacks. These current runs establish executable mechanics, fresh PPO updates, bounded injection and matched local timeout evaluation. They do not yet establish beneficial trail use, harmful team disruption or a successful defense. The frozen-policy input ablation changes actions but slightly improves delivery when pheromone is removed.')
    chapter(3)
    table([['Setting','Current development value'],['Grid / nest','8×8; top-left 2×2 nest; coordinates (row, column)'],['Team / selected attacker','8 agents; k=1 in disabled/attacked controls; 12.5%'],['Food / horizon','2 patches × 4 units = 8; max 500 world steps'],['Fields','(2,8,8) float64; food=0, home=1; cap=10'],['Deposit / decay','Ordinary deposit=1; home_decay=.95; evaporation=.1']], [150,360])
    h('Exactly what PPO sees')
    p('Each agent receives a copied float32 vector of length 58. The first 54 values are a flattened 3×3×6 patch, ordered row, column, channel. The final four are its own carrying, pickup, delivery and blocked flags. No global position, global resource map, attacker identity or injection label is included.')
    table([['Patch channel','Meaning'],['0: food present','Boolean; not the remaining food quantity'],['1: nest','Boolean; visible nest cells only'],['2: food pheromone','Concentration divided by cap=10'],['3: home pheromone','Concentration divided by cap=10'],['4: occupancy','Number of agents in cell divided by N=8'],['5: boundary','Out-of-grid indicator; outside cells otherwise zero']], [150,360])
    h('Movement and resource handling')
    p('Actions are <b>0 stay, 1 north, 2 east, 3 south, 4 west</b>. An off-grid proposal stays in place and sets blocked. Co-location and swaps are allowed. Resource pickup uses a seeded random contention order; several agents at the same patch cannot consume more units than remain. Each agent carries at most one unit.')
    p('The movement counter is per-agent internal simulator state, not an added observation feature. It counts successful displacement outside regardless of load and resets whenever the agent occupies the nest. Reset clears fields, carrying, events and counters. The same observation shape is preserved under the new mechanics.')
    chapter(4)
    h('Execution order matters')
    p('1. Validate the entire action dictionary before changing any state.<br/>2. Move all agents; mark blocked boundary proposals.<br/>3. Reset counters in the nest; increment successful outside movements.<br/>4. Deliver or pick up in seeded contention order.<br/>5. Deposit using the resulting carrying state.<br/>6. Add bounded adversarial food mass at selected occupied cells.<br/>7. Clip both channels to [0,10], then multiply by .9.<br/>8. Update team deliveries and step count; construct observations, reward and lifecycle flags.')
    code('if carrying[i]:\n    food_field[cell] += deposit   # unchanged\nelif nest[cell]:\n    home_field[cell] += deposit\nelif successfully_moved[i]:\n    home_field[cell] += deposit * home_decay**counter[i]\n# No empty outside stationary/blocked home deposit.\nclip(fields, 0, field_cap)\nfields *= 1 - evaporation')
    h('Worked values')
    p('For an empty agent with no overlap, the first outbound movement leaves <b>1 × .95 × .9 = .855</b> after evaporation; the second leaves <b>1 × .95² × .9 = .81225</b>. A loaded agent deposits 1 regardless of the counter. A previously deposited .9 food value becomes .81 after another step without a new deposit. Overlap adds contributions before clipping.')
    p('A cell is a historical sum of visits, not a food location, distance or trust score. Food pheromone near the nest can be strongest because carrying agents visited there most recently. Nest delivery precedes deposition, so newly emptied agents add home. A displayed 0.0 may be a nonzero residual rounded to one decimal.')
    h('Reward, conservation and stopping')
    p('The simulator supplies a shared reward equal to the number of units delivered this step to every agent. If two deliveries occur, all eight rewards are 2; the team delivered two units, not sixteen. The conservation invariant is remaining + carried + delivered = 8. Completion terminates when no food remains or is carried. The horizon otherwise truncates; completion at the horizon is still termination.')
    chapter(5)
    h('Learning is online interaction, not learning from the saved JSONL')
    p('The simulator builds the observation. PPO selects an action from it, the simulator executes it and gives reward plus the next observation. SB3 collects these transitions in an in-memory rollout buffer and optimizes the shared actor/value network. Disk logs are for evidence and analysis; the current PPO run does not train from a pre-existing labelled dataset.')
    p('SharedGridVecEnv exposes eight interacting agent slots from one world. They are not eight independent maps. Every slot uses the same 32×32 actor and local critic; only its own 58-value row enters either network. The shared simulator reward is unchanged. There is no global-state critic, reward shaping, agent identity encoding or attack training.')
    table([['Training setting','Retained value'],['Seed / maps','7; training seeds 0-15; diagnostics 100-103'],['Rollout','128 world steps × 8 slots = 1,024 transitions'],['Optimization','Batch 64; 4 epochs; learning rate .0003; gamma .99'],['Fresh budgets','4,096 smoke; requested 300,000 main'],['Actual main run',f'{train["actual_agent_transitions"]:,} transitions; {train["world_steps"]:,} world steps']], [155,355])
    p('SB3 rounds to complete rollouts. The adapter automatically resets all slots together at episode end, cycles through training map seeds and supplies final observations. TimeLimit.truncated distinguishes horizon endings for value bootstrapping. PPO computes advantage/return targets from rewards and value estimates, then applies its clipped policy objective and value updates.')
    h('Checkpoints and diagnostics')
    p('Each fresh directory stores initial.zip, policy.zip, progress.csv, manifest.json and summary.json. Initial/final parameter hashes must differ and learned tensors must be finite. The final checkpoint is reloaded, tensor hashes checked and deterministic probe actions compared. No old checkpoint was reused after changing home mechanics.')
    p('Deterministic diagnostics choose the highest-probability action. Stochastic diagnostics sample from the policy distribution using matched seeds. A zero deterministic result alongside stochastic deliveries indicates that the learned argmax controller remains poor; stochastic movement alone can help search. Four diagnostic episodes do not establish stable learning.')
    chapter(6)
    h('The attacker is a bounded field writer')
    p('At reset, a dedicated seeded RNG fixes the compromised subset. After movement and ordinary deposits, each selected agent can add only nonnegative food pheromone at its actual reachable occupied cell. It cannot erase trails, deposit negative mass, write to arbitrary distant cells, alter rewards, change PPO or modify true food. Selected agents retain productive PPO movement and collection behavior.')
    table([['Attack setting','Unchanged value'],['Selected count / fraction','k=1 of N=8; 12.5%'],['Request / per-step budget','1 per selected agent; 1 applied unit across the step'],['Episode budget','20 applied units across the episode'],['Cap / evaporation','Same 10-unit cap and .9 multiplier as honest fields']], [170,340])
    code('authorized = min(requested, remaining_step, remaining_episode)\nheadroom = max(0, cap - food_field[cell])\napplied = min(authorized, headroom)\nfood_field[cell] += applied\n# Budget spending is applied mass, BEFORE evaporation.')
    p('Example: a request of 1 with allowance .7 and headroom .2 authorizes .7 but applies .2. Logs retain all three values. Persistent mode continues requests each step even after the applied budget is exhausted. Decoy routes and intermittent bursts are planned, not implemented.')
    h('Why six matched scenarios?')
    p('Clean has no injector. Injection-disabled keeps the same selected subset but writes no extra mass. Attacked enables writes. Each also has a timeout variant. Reset/map/action seeds and frozen checkpoint match. Clean/disabled local-record hashes must be equal, including defended twins. Those controls isolate injection from merely designating a worker as compromised.')
    h('Fair accounting')
    p('Team delivery counts all eight agents. Honest delivery in disabled/attacked scenarios excludes the same selected agent in each pair. Clean has eight honest agents, so compare its team count to disabled team count, not directly to the seven-worker honest total. Labels and honest totals are simulator-only logging metadata; runtime controllers never use them.')
    chapter(7)
    h('The twelve local-history features')
    table([['Feature group','Values / meaning'],['Field statistics (4)','Food mean/max; home mean/max over the local patch'],['Field changes (2)','Food mean delta; home mean delta from prior observation'],['Own current state (4)','Carrying; pickup; delivery; blocked'],['Own history (2)','Normalized time without pickup/delivery; inferred revisit frequency']], [165,345])
    p('LocalHistoryFeatures uses the agent\'s previous executed action and blocked flag to reconstruct relative displacement. It has no absolute map or author information. Initial observation does not count as an elapsed no-progress step. History resets between episodes. Deltas may be negative because of evaporation or movement into another crop; they are not ground-truth attack labels.')
    h('What the implemented timeout does')
    p('One local timeout object per agent wraps the PPO proposal. Pickup/delivery reset its no-progress timer. After eight steps without progress it can override the proposal using visible local food/nest cues or a deterministic cycle of legal directions. The same rule applies to all agents, without checking attacker membership. Logged proposed and executed actions expose overrides.')
    p('This is a fixed heuristic baseline. It does not output an attack probability, authenticate trails, assign agent trust or implement a learned exploration score. In these measurements it disrupted retrieval even on clean maps. Timeout activations are not detector alarms; precision, recall and false-alarm rates cannot be inferred from them.')
    h('Planned learned detector and mitigation')
    p('The future detector would train logistic regression and a small random forest on local temporal features with separate simulator-generated labels. Group complete related episodes/maps before creating temporal windows; keep final maps/attack configurations withheld. A suspicious-exposure score could reduce pheromone reliance and increase exploration, but that score-based mitigation is not currently implemented.')
    h('Frozen-policy sensitivity is a different diagnostic')
    p('Zeroing only food/home observation channels preserves local food/nest/occupancy/boundaries and own progress. It tests whether fixed-network actions change. It is not detector training and not a separately trained no-pheromone baseline. Zeroing can be distribution shift, so even a delivery improvement must be interpreted cautiously.')
    chapter(8)
    table([['File / group','Responsibility and outputs'],['environment.py','GridConfig; reset/step/local crops; positions, fields, food, load, counters'],['attacks.py','AttackConfig; seeded subset; occupied-cell budget/headroom accounting'],['policies.py','Local rule-based forager for debugging; not learned evidence'],['ppo_adapter.py','One parallel world as interacting SB3 slots; map cycling and final observations'],['training.py','Fresh shared PPO; save/reload; diagnostics and source hashes'],['defense.py','Twelve features; independent local histories; fixed timeout overrides'],['evaluation.py','Frozen six-way matched rollouts, control equality, team/honest metrics'],['evaluation_plots.py','PNG/SVG means and individual points; no performance tuning'],['trajectories.py','JSONL recorder; manifests; separate simulator-only attack metadata'],['cli.py / __init__.py','Commands and human SVG demo / package environment exports'],['scripts/run_review_budget.py','Sequential smoke/main/comparison/sensitivity; common deadline'],['scripts/review_evidence.py','Exact scripted state JSON/PNGs; sensitivity; measured time-series plots'],['scripts/build_review_handbook.py','This PDF; optional reportlab/pypdf authoring dependencies']], [175,335])
    h('What to edit and read')
    p('Edit src modules for behavior, configs for declared settings, tests for contracts and docs for decisions/evidence. Read AGENTS, CONTEXT and ADRs first; then environment, cli, attacks/trajectories, policies/adapter/training, defense/evaluation. Tests isolate mechanics, local leakage boundaries, contention, accounting, resets, adapter lifecycle and matched controls. The new sensitivity test checks that only two channels are zeroed.','small')
    p('README gives entry points; FIRST_REVIEW_PLAN defines owners/handoffs; four teammate guides describe original milestones. ADRs 0001-0004 are historical mechanics/attack/PPO/comparison decisions; 0005 supersedes home deposition and review conditions. docs/reference contains canonical Word scope records. External DQN/individual-trust notes do not describe this PPO/shared-anonymous-field implementation.','small')
    p('pyproject.toml defines package/dependencies; requirements-dev.lock pins core/tests; requirements-training.lock pins the optional training stack. steps.jsonl holds local observations/features/actions/reward and separate privileged metadata; CSVs summarize episodes/paired contrasts; manifests record configs/seeds/hashes; checkpoint ZIPs contain weights. egg-info, caches and environments are generated metadata. Ignored artifacts are not uploaded by a source commit.','small')
    chapter(9)
    pic('clean-step-0.png')
    p('Figure 1. Initial eight-agent scripted fixture: eight food units, no load or deliveries, both fields zero. Nest is upper-left. Agents overlap in the four nest cells.','caption')
    pic('clean-step-20.png')
    p('Figure 2. Fixed step 20, before completion. Numbers are actual field concentrations rounded for display, not trust scores. All four fixed states (0,10,20,23) are saved for clean, disabled and attacked fixtures.','caption')
    pic('clean-step-23.png')
    p('Figure 3. Final scripted state: all eight delivered at step 23. Remaining trails decay after visits. Home at nest (1,1) rounds to 5.3; overlapping outbound trails need not decrease perfectly with distance. These routes use known coordinates and are mechanics evidence, not PPO performance.','caption')
    p('The separately labelled two-agent waiting diagnostic now decays from .66158 at step 56 to .02044 at step 89; the old 8.7 outside hotspot is not recreated. Clean/disabled state arrays match exactly; repeated seeded fixtures are identical.','small')
    chapter(10)
    pic('ppo-before-after.png',width=490)
    p('Figure 4. Four diagnostic maps, action seed 7, one fresh training seed. Main stochastic mean 6.25 → 7.00; deterministic 0 → 0. The independent smoke run changed stochastic mean 6.25 → 6.00, retaining its negative outcome.','caption')
    table([['Stochastic: 12 episodes each','Mean team','Mean honest'],['Clean / disabled / attacked','7.667 / 7.667 / 7.667','7.667 / 6.417 / 6.583'],['All three timeout variants','0 / 0 / 0','0 / 0 / 0'],['Paired honest loss / timeout gain','-.167 / -6.583 units','Not successful mitigation'],['Recovery','Undefined in 15 of 16 groups','One defined value: -6.0']], [240,130,140])
    p('Comparison: 96 episodes = 6 scenarios × (4 deterministic + 12 stochastic). Maps 100-103; stochastic action seeds 7/8/9; deterministic sampling seeds deduplicated. Every deterministic delivery count is zero. These means measure episode variation, not uncertainty across training seeds. Equal mean team delivery does not mean identical local fields/actions.','small')
    p(f'Frozen-policy sensitivity: stochastic full 7.667 versus zeroed 8.000; same-observation sampled actions differ by 21.11%, realized overlapping action sequences by 51.26%. Deterministic full/zeroed delivery is zero and same-observation actions differ by 49.75%. Input sensitivity is measured; beneficial pheromone use is not established.','small')
    h('Verification and preserved history')
    p(f'83 full-stack tests passed on Linux Python 3.12.14; compatible pinned packages, repeatable fixtures, matched controls, unchanged checkpoint and reload checks passed. Experiment wall time {budget["elapsed_seconds"]:.1f}s within 1,800s. Main actual transitions {train["actual_agent_transitions"]:,}. Requested/applied-mass and local-observation difference plots retain all outcomes.','small')
    p('Historical two-agent/50% condition: 73 tests; 4,096-transition smoke; stochastic 1.75 → 3.75; deterministic zero; 48 comparison episodes; equal team 3.75 without timeout, zero with timeout; honest loss 0, gain -2, recovery undefined. These old mechanics/results remain in review-current. New and old team sizes differ: do not attribute the difference solely to the home correction.','small')
    chapter(11)
    h('Install the verified full stack')
    p('Use Python 3.12. The declared Python 3.11 target has a demonstrated training-lock conflict: contourpy==1.4.0 requires >=3.12. Core simulator support is separate. Training uses CPU single-thread deterministic Torch operations; exact cross-platform identity is not promised.')
    code('# Linux\npython3.12 -m venv .venv\nsource .venv/bin/activate\n# Windows PowerShell: replace the two lines above with\npy -3.12 -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1\n# Both, after activation\npython -m pip install -r requirements-training.lock\npython -m pip install -e . --no-deps --no-build-isolation\npython -m pytest -q')
    h('Reproduce the bounded experiment and figures')
    code('python scripts/run_review_budget.py \\\n  --output artifacts/review-eight-new\npython scripts/review_evidence.py figures \\\n  --root artifacts/review-eight-new')
    p('In PowerShell put the command on one line instead of using Bash backslash continuation. The runner shares 30 minutes across smoke, main training, matched comparisons and sensitivity. Interrupted runs preserve incomplete manifests/partial files. Only completed, reload-validated checkpoints are compared. Every output directory/subdirectory must be fresh.')
    h('Small live demo and individual operations')
    code('python -m stigmergy.cli demo \\\n  --config configs/env/review-eight.json \\\n  --output artifacts/live-demo-new\npython -m stigmergy.cli record-fixture \\\n  --config configs/env/review-eight.json --scenario attacked \\\n  --output artifacts/fixture-new\npython -m stigmergy.cli debug-policy \\\n  --config configs/env/review-eight.json \\\n  --output artifacts/debug-new')
    p('For individual train/compare commands, artifact inspection and standalone sensitivity see docs/REVIEW_DEMO.md. Before a presentation open the saved PNGs; a new training run is not necessary. Check budget.json, each manifest status, training summary, comparison episodes/contrasts and figures/verification.json. New state JSON is the unrounded source behind screenshots.','small')
    chapter(12)
    h('Slide 1: cooperative retrieval mechanics')
    p('<b>Put on slide:</b> 8×8 grid; eight agents; local 3×3 sensing. Loaded agents leave food trails; empty moving agents leave nest-anchored home trails. Waiting outside deposits no home. Both fields evaporate 10% per step. Scripted fixture: eight units delivered in 23 steps.')
    p('<b>Images:</b> clean-step-0.png and clean-step-23.png, stacked. <b>Say:</b> “These are actual simulator states from a scripted mechanics check. Food is collected one unit at a time and returned. Trails record earlier visits, so food pheromone can remain where no food exists. The corrected home rule prevents waiting at an exhausted patch from building a false home hotspot.”')
    h('Slide 2: PPO, injection and honest negative results')
    p('<b>Put on slide:</b> fresh shared PPO; 300,032 transitions; stochastic four-map mean 6.25 → 7.00; deterministic zero. Six matched scenarios, 96 episodes. One attacker of eight (12.5%). Stochastic clean/attacked team means both 7.67; timeout zero. Field/action changes measured; robustness unproven.')
    p('<b>Image:</b> delivery_comparison.png large, or pair it with ppo-before-after.png. <b>Say:</b> “The attacker adds bounded false food pheromone at its occupied cells. The policy and defense see only local information. Injection changed observations without lowering mean team delivery here. Our fixed timeout hurt even clean retrieval, so it is a failed baseline in this diagnostic. A learned detector and final held-out study remain next steps.”')
    h('Common questions')
    p('<b>Are rewards labels?</b> Simulator rewards train PPO; attack labels would supervise a separate future detector. <b>Are trails attributed to agents?</b> No, the shared field has no author identity. <b>Does a high value prove food/home?</b> No, it reflects deposits and age. <b>Why stochastic and deterministic differ?</b> Sampling changes exploration; argmax behavior remains poor. <b>Is zeroed-input PPO the no-pheromone baseline?</b> No; that baseline requires separate training.')
    h('Remaining work and useful terms')
    p('Improve reliable deterministic cooperation and test whether trails help; multiple training seeds; decoy/intermittent modes; grouped episode/map datasets before windows; logistic/RF detector; score-based mitigation; separately trained no-pheromone and documented cautionary baseline; benign false-alarm controls; freeze unseen maps/attack settings for final evaluation.')
    p('<b>Glossary:</b> transition = one agent observation/action/reward step; world step = one simultaneous team update; rollout = collected transitions before PPO updates; checkpoint = saved model; manifest = provenance/config record; truncation = horizon cutoff; matched control = same seeds/model with only the tested intervention changed; ablation = deliberately remove an input component. Detailed speaking notes and commands: docs/REVIEW_DEMO.md.','small')
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('D',8);canvas.setFillColor(colors.HexColor('#587081'))
        canvas.drawString(40,A4[1]-24,'Robust Stigmergic Coordination | Verified development handbook')
        canvas.drawString(40,25,f'9 October 2026 | source {revision[:12]} + working-tree changes')
        canvas.drawRightString(A4[0]-40,25,f'{doc.page} / 12');canvas.restoreState()
    output.parent.mkdir(parents=True,exist_ok=True)
    doc=Handbook(str(output),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=44,bottomMargin=44,title='Capstone Implementation Handbook - Team Edition',author='Capstone team',allowSplitting=0)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(output)
    if len(reader.pages)!=12:raise RuntimeError(f'Expected 12 pages, generated {len(reader.pages)}')
    if len(reader.outline)!=12:raise RuntimeError('Missing chapter bookmarks')
    print(f'Verified structure: {len(reader.pages)} pages, {len(reader.outline)} bookmarks')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('artifacts/review-eight'))
    parser.add_argument('--output',type=Path,default=Path('output/pdf/capstone_implementation_handbook.pdf'))
    args=parser.parse_args();build(args.root,args.output)
