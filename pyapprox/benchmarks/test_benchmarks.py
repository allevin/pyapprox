#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import unittest
from functools import partial
from pyapprox.benchmarks.benchmarks import *
import pyapprox as pya

class TestBenchmarks(unittest.TestCase):

    def test_ishigami_function_gradient_and_hessian(self):
        benchmark = setup_benchmark("ishigami",a=7,b=0.1)
        init_guess = benchmark['var'].get_statistics('mean')+\
            benchmark['var'].get_statistics('std')
        errors = pya.check_gradients(
            benchmark['fun'],benchmark['jac'],init_guess,disp=False)
        assert errors.min()<2e-7
        hess_matvec = lambda x,v: np.dot(benchmark['hess'](x),v)
        errors = pya.check_hessian(
            benchmark['jac'],hess_matvec,init_guess,disp=False)
        assert errors.min()<2e-7

    def test_rosenbrock_function_gradient_and_hessian_prod(self):
        benchmark = setup_benchmark("rosenbrock",nvars=2)
        init_guess = benchmark['var'].get_statistics('mean')+\
            benchmark['var'].get_statistics('std')
        errors = pya.check_gradients(
            benchmark['fun'],benchmark['jac'],init_guess,disp=True)
        assert errors.min()<1e-5
        errors = pya.check_hessian(
            benchmark['jac'],benchmark['hessp'],init_guess,disp=False)
        assert errors.min()<1e-5

    def test_missing_benchmark(self):
        self.assertRaises(Exception,setup_benchmark,"missing",a=7,b=0.1)
        

if __name__== "__main__":    
    benchmarks_test_suite = unittest.TestLoader().loadTestsFromTestCase(
         TestBenchmarks)
    unittest.TextTestRunner(verbosity=2).run(benchmarks_test_suite)