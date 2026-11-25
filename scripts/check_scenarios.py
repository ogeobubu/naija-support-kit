"""Run the demo's customer acceptance examples without Docker or network calls."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pilot_bot', ROOT / 'bot/app.py')
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenarios', type=Path, default=ROOT / 'tests/customer-scenarios.json')
    parser.add_argument('--report', type=Path, default=ROOT / 'data/customer-scenario-report.json')
    args = parser.parse_args()
    cases = json.loads(args.scenarios.read_text(encoding='utf-8'))
    results = []
    for case in cases:
        actual = bot.answer(case['message'], mode='faq')
        expected_text = case.get('answer_contains', '')
        passed = actual['action'] == case['expected_action'] and expected_text in actual['content']
        results.append({**case, 'passed': passed, 'actual': actual})
        print(f"{'PASS' if passed else 'FAIL'} {case['id']}: {case['message']}")
    passed_count = sum(r['passed'] for r in results)
    report = {
        'mode': 'faq', 'business': bot.knowledge()['business'],
        'scope': 'Offline text answers only; not Chatwoot delivery, staff takeover or WhatsApp.',
        'passed': passed_count, 'total': len(results), 'results': results
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'\n{passed_count}/{len(results)} scenarios passed. Report: {args.report}')
    return 0 if passed_count == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())
