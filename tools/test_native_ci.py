#!/usr/bin/env python3
"""Qualification must not turn missing/foreign/failed reports into success."""
import copy
import unittest
from native_ci import TARGETS, REQUIRED_CHECKS, aggregate, inventory


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {'sourceRevision':'revision','workingTreeDirty':False,'targets': [{'target': t, 'binarySha256': 'binary', 'archiveSha256': 'archive'} for t in TARGETS]}
        self.reports = [{'target': t, 'status': 'passed', 'sourceRevision': 'revision',
                         'binarySha256': 'binary', 'packageSha256': 'archive','checks':{k:{'status':'passed'} for k in REQUIRED_CHECKS+['liveHTTPS','minimalLinux']}} for t in TARGETS]

    def test_complete_matrix(self):
        self.assertEqual(len(inventory()['include']), 6)
        self.assertTrue(all(r['status'] == 'passed' for r in aggregate(self.reports, self.manifest, 'revision')))

    def test_empty_or_partial_inventory_never_passes(self):
        for reports in [[], self.reports[:1], self.reports[:-1]]:
            rows = aggregate(reports, self.manifest, 'revision')
            self.assertEqual(len(rows), 6)
            self.assertTrue(any(r['status'] == 'unverified' for r in rows))

    def test_wrong_source_and_binary_rejected(self):
        for field in ['sourceRevision', 'binarySha256', 'packageSha256']:
            reports = copy.deepcopy(self.reports)
            reports[0][field] = 'changed'
            self.assertEqual(aggregate(reports, self.manifest, 'revision')[0]['status'], 'failed')

    def test_duplicate_or_failed_target_rejected(self):
        reports = self.reports + [self.reports[0]]
        self.assertEqual(aggregate(reports, self.manifest, 'revision')[0]['status'], 'failed')
        for status in ['failed', 'running', 'cancelled', 'skipped']:
            reports = copy.deepcopy(self.reports)
            reports[0]['status'] = status
            self.assertEqual(aggregate(reports, self.manifest, 'revision')[0]['status'], 'failed')

    def test_missing_required_check_fails(self):
        for key in REQUIRED_CHECKS + ['liveHTTPS', 'minimalLinux']:
            reports = copy.deepcopy(self.reports)
            target = next(r for r in reports if r['target'] == 'linux/amd64')
            del target['checks'][key]
            row = next(r for r in aggregate(reports, self.manifest, 'revision') if r['target']=='linux/amd64')
            self.assertEqual(row['status'], 'failed')

    def test_missing_package_provenance_unverified(self):
        self.assertTrue(all(r['status'] == 'unverified' for r in aggregate(self.reports, None, 'revision')))


if __name__ == '__main__':
    unittest.main()
