import copy
import unittest
from unittest.mock import patch
from forge_trial import assess,digest,review


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.p=dict(project_id='PROJECT-EXAMPLE',hypothesis='reduce redundant reviews',
                    scope='one local trial',baseline_revision='before',candidate_revision='after',
                    rollback='retain prior method',stop_conditions='quality regression',
                    metrics=[dict(id='quality',unit='fraction',procedure='same cases',
                                  direction='higher',max_regression=0,min_improvement=0,required=True),
                             dict(id='effort',unit='seconds',procedure='same workload',
                                  direction='lower',max_regression=0,min_improvement=5,required=True)])
        self.h=digest(self.p)
        self.o=dict(project_id=self.p['project_id'],plan_sha256=self.h,
                    baseline_revision='before',candidate_revision='after',stop_observations=[],
                    measurements=[dict(id='quality',baseline=1,candidate=1,baseline_ref='a',candidate_ref='b'),
                                  dict(id='effort',baseline=30,candidate=20,baseline_ref='c',candidate_ref='d')])

    def run_trial(self):
        return assess(self.p,self.o,expected_plan_digest=self.h)

    def test_improvement_without_adoption(self):
        r=self.run_trial()
        self.assertEqual(r['assessment'],'candidate_for_review')
        self.assertFalse(r['adopted'])
        self.assertFalse(r['measurements_verified'])

    def test_quality_regression_not_offset(self):
        self.o['measurements'][0]['candidate']=0.9
        self.assertEqual(self.run_trial()['assessment'],'stop_or_rework')

    def test_missing_required(self):
        self.o['measurements'].pop(0)
        self.assertEqual(self.run_trial()['assessment'],'insufficient_evidence')

    def test_missing_log(self):
        self.o['measurements'][0]['candidate_ref']=None
        self.assertEqual(self.run_trial()['assessment'],'insufficient_evidence')

    def test_no_improvement(self):
        self.o['measurements'][1]['candidate']=28
        self.assertEqual(self.run_trial()['assessment'],'no_demonstrated_improvement')

    def test_stop(self):
        self.o['stop_observations']=['unexpected side effect']
        self.assertEqual(self.run_trial()['assessment'],'stop_or_rework')

    def test_changed_plan(self):
        self.p['metrics'][0]['max_regression']=1
        with self.assertRaises(ValueError):
            self.run_trial()

    def test_wrong_revision(self):
        self.o['candidate_revision']='different'
        with self.assertRaises(ValueError):
            self.run_trial()

    def test_duplicate_observation(self):
        self.o['measurements'].append(copy.deepcopy(self.o['measurements'][0]))
        with self.assertRaises(ValueError):
            self.run_trial()

    def test_invalid_number(self):
        self.o['measurements'][0]['candidate']=True
        with self.assertRaises(ValueError):
            self.run_trial()

    def test_raw_observations_retained(self):
        r=self.run_trial()['metrics'][1]
        self.assertEqual((r['baseline'],r['candidate'],r['baseline_ref'],r['candidate_ref']),(30,20,'c','d'))

    @patch('forge_trial.compare')
    def test_guard_prevents_positive_assessment(self, compare):
        compare.return_value={'project_id':self.p['project_id'],'review_required':True}
        r=review(self.p,self.o,self.h,'old','manifest','new','manifest')
        self.assertEqual(r['assessment'],'protected_or_governance_review_required')
        self.assertEqual(r['metric_assessment'],'candidate_for_review')
        self.assertFalse(r['adopted'])

    @patch('forge_trial.compare')
    def test_stop_not_hidden_by_guard(self, compare):
        compare.return_value={'project_id':self.p['project_id'],'review_required':True}
        self.o['stop_observations']=['unsafe trial']
        r=review(self.p,self.o,self.h,'old','manifest','new','manifest')
        self.assertEqual(r['assessment'],'stop_or_rework')
        self.assertTrue(r['record_review_required'])
