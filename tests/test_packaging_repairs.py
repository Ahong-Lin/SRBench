import tempfile
import unittest
from pathlib import Path
import json
import numpy as np
from srbench.common.metrics import regression_metrics
from srbench.common.polynomial_equilibrium import compile_equilibrium
from srbench.generation.data_generator import _sample_axes, mixed_integer_geometry
from srbench.packaging.pipeline import build_package

class PackagingRepairTests(unittest.TestCase):
    def test_metric_unit_invariance(self):
        y=np.array([1.,3.,7.,10.]); p=np.array([2.,2.,8.,9.])
        baseline=regression_metrics(p,y)['raw_r2']
        for scale in [1e-19,1,1e19]:
            self.assertAlmostEqual(regression_metrics(p*scale,y*scale)['raw_r2'],baseline)
        self.assertEqual(regression_metrics([1,1],[1,1])['status'],'undefined_target_variance')
        self.assertEqual(regression_metrics([0,0],[0,0])['status'],'undefined_target_variance')

    def test_equilibrium_global_branch_and_residual(self):
        f=compile_equilibrium('M**3-M-H','M',['H'])
        for h in [.01, -.01, 2, -2]:
            m=f(h)
            self.assertGreater(m*h,0)
            self.assertAlmostEqual(m**3-m-h,0,places=10)
            self.assertGreater(3*m*m-1,0)
        with self.assertRaisesRegex(ValueError,'Degenerate'):
            f(0)

    def test_integer_split_preserves_partition_and_mass(self):
        axes=[{'symbol':'n','range':[1,8],'type':'integer'}]+[{'symbol':x,'range':[0,1]} for x in ['x','y','z']]
        bounds=mixed_integer_geometry(axes)
        frac=sum(n>bounds['n'] for n in range(1,9))/8
        for x in ['x','y','z']: frac*=1-bounds[x]
        self.assertAlmostEqual(frac,.1)
        for part in ['train','hidden']:
            values=_sample_axes(axes,500,42,part)
            self.assertTrue(np.all(values[0]==np.floor(values[0])))
            membership=np.logical_and.reduce([v>bounds[a['symbol']] for a,v in zip(axes,values)])
            self.assertTrue(np.all(membership if part=='hidden' else ~membership))

    def test_implicit_package_oracle(self):
        spec={'integrator':'root_solve_implicit','equation_type':'implicit','dependent_variable':'M',
              'independent_variables':[{'symbol':'H','range':[.01,1.]}], 'parameters':[],
              'rhs_for_integrator':'M**3-M-H','implicit_branch':'global_minimum_polynomial_potential'}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'spec.json').write_text(json.dumps(spec))
            out=build_package(root/'spec.json',root/'pkg',n_total=30,test_points=5)
            m=json.loads((out/'manifest.json').read_text())
            self.assertEqual(m['oracle_self_test']['test']['versus_clean_truth']['raw_r2'],1)
            source=(out/'task/solution/reference_law.py').read_text()
            self.assertNotIn('from srbench',source)
