"""Run fresh review training/comparisons under one 30-minute wall-clock budget.

Use the pinned Python 3.12 interpreter to run this script from the repository:
python scripts/run_review_budget.py --output artifacts/review-eight
The output directory must be new. A monotonic deadline covers smoke training,
300,000-transition training, six-scenario comparisons and frozen-policy
sensitivity. Each child writes its own provenance, logs and checkpoints; this
runner additionally writes budget.json and terminal logs. On deadline expiry
SIGINT permits an incomplete manifest; forced termination is a fallback. Only
completed training directories are passed to downstream evaluation. No old
checkpoint is reused. Defaults preserve all settings and declared maps.

This orchestration is development evidence, not final evaluation. It does not
change simulator/policy/attack/defense behavior. Figures and scripted mechanics
capture are generated separately and do not consume the experiment budget.
"""
import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
import time


def run(output, seconds=1800):
    """Execute dependencies sequentially; retain completed/partial artifacts."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    records = []
    commands = [
        ('smoke', ['-m', 'stigmergy.cli', 'train', '--config', 'configs/env/review-eight.json',
                   '--policy-config', 'configs/policy/review-smoke.json', '--output', str(output/'smoke')]),
        ('training', ['-m', 'stigmergy.cli', 'train', '--config', 'configs/env/review-eight.json',
                      '--policy-config', 'configs/policy/development.json', '--output', str(output/'training')]),
        ('comparison', ['-m', 'stigmergy.cli', 'compare-development', '--checkpoint', str(output/'training/policy.zip'),
                        '--comparison-config', 'configs/evaluation/review-eight.json', '--output', str(output/'comparison')]),
        ('sensitivity', ['scripts/review_evidence.py', 'sensitivity', '--root', str(output)])]
    for name, args in commands:
        remaining = seconds - (time.monotonic() - started)
        if remaining <= 0:
            records.append({'stage': name, 'status': 'not_run_budget_expired'})
            break
        with (output/f'{name}-terminal.log').open('w') as stream:
            process = subprocess.Popen([sys.executable, *args], stdout=stream, stderr=subprocess.STDOUT)
            try:
                code = process.wait(timeout=remaining)
                status = 'completed' if code == 0 else 'failed'
            except subprocess.TimeoutExpired:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                status = 'incomplete_budget_expired'
                manifest_path = output/name/'manifest.json'
                if manifest_path.exists():
                    manifest = json.loads(manifest_path.read_text())
                    manifest.update(status='incomplete', error='30-minute experiment budget expired')
                    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
            records.append({'stage': name, 'status': status, 'command': [sys.executable, *args],
                            'elapsed_from_start_seconds': time.monotonic()-started})
        (output/'budget.json').write_text(json.dumps({'budget_seconds':seconds,
            'elapsed_seconds':time.monotonic()-started, 'stages':records}, indent=2)+'\n')
        if status != 'completed':
            break
    (output/'budget.json').write_text(json.dumps({'budget_seconds':seconds,
        'elapsed_seconds':time.monotonic()-started, 'stages':records}, indent=2)+'\n')
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    records = run(parser.parse_args().output)
    print(json.dumps(records, indent=2))
    if len(records) != 4 or any(r["status"] != "completed" for r in records):
        sys.exit(1)
