"""Run from any working directory; all paths below are project-relative."""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['check', 'run'])
    p.add_argument('--scenarios', default='data/public_scenarios.jsonl')
    p.add_argument('--policy')
    p.add_argument('--out', default='runs/current')
    a = p.parse_args()
    if a.command == 'check':
        for folder in ['tests', 'evals/candidate']:
            subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', folder], check=True)
    else:
        args = [sys.executable, '-m', 'voice_agent.cli', '--scenarios', a.scenarios, '--out', a.out]
        if a.policy: args += ['--policy', a.policy]
        subprocess.run(args, check=True)


if __name__ == '__main__': main()
