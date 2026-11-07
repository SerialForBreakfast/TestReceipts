"""Guard against misleading evaluation scores and partial-run savings claims."""
import json
from pathlib import Path
import tempfile
import unittest

from go_agent_study import INV, score, summarize, write
from report_go_agent_study import go_comparison_seen


class StudyChecks(unittest.TestCase):
    def test_wrapped_go_execution_and_python_fallback_are_distinct(self):
        self.assertTrue(go_comparison_seen([
            "p=subprocess.run(['./testreceipts','compare-recording',cfg['recording'],*urls])"]))
        self.assertTrue(go_comparison_seen(['./testreceipts compare-recording recording before after']))
        self.assertFalse(go_comparison_seen([
            'ls -la && ./testreceipts --help',
            'from ready_query import query; answer=query(paths)']))

    def test_incorrect_inventory_cannot_pass_on_matching_counts(self):
        run = {k: [] if k.endswith('Objects') else 1 for k in INV}
        run['artifactComplete'] = True
        gold = {'runs': [run, run], 'change': {}, 'newEvidence': []}
        answer = json.loads(json.dumps(gold))
        answer['runs'][1]['inventorySha256'] = 'wrong'
        checks, inventory, unsupported = score(answer, gold)
        self.assertFalse(checks['runs'])
        self.assertFalse(inventory)
        self.assertEqual(unsupported, 1)

    def test_no_answer_is_failure(self):
        checks, inventory, unsupported = score(None, {'runs': [{}, {}], 'change': {}})
        self.assertFalse(any(checks.values()))
        self.assertFalse(inventory)
        self.assertEqual(unsupported, 0)

    def test_partial_run_never_reports_overall_savings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'runs').mkdir()
            (root / 'protocol').mkdir()
            write(root / 'protocol/questions.json', [{'id': 'U01', 'project': 'example'}])
            row = dict(id='U01', arm='adapter', rep=1, correct=False,
                       inventoryCorrect=False, unsupportedCompletenessClaims=0,
                       usage=None, checks={}, exitCode=1, timeout=False)
            write(root / 'runs/U01-1-adapter.json', row)
            report = summarize(root)
            self.assertFalse(report['complete'])
            self.assertEqual(report['comparisons'], {})
            self.assertEqual(report['totals']['adapter']['missingUsage'], 1)
            self.assertEqual(len(report['failures']), 1)


if __name__ == '__main__':
    unittest.main()
