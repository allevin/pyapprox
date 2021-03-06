r"""
Multi-level Monte Carlo
=======================
This tutorial builds upon :ref:`sphx_glr_auto_tutorials_multi_fidelity_plot_approximate_control_variate_monte_carlo.py` and describes how the pioneering work of Multi-level Monte Carlo [CGSTCVS2011]_, [GOR2008]_ can be used to estimate the mean of a high-fidelity model using multiple low fidelity models. 

Two Model MLMC
--------------
The two model MLMC estimator is very similar to the CVMC estimator and is based upon the observations that we can estimate

.. math:: \mean{f_0}=\mean{f_1}+\mean{f_0-f_1}

using the following unbiased estimator

.. math:: Q_{0,\mathcal{Z}}^\mathrm{ML}=N_1^{-1}\sum_{i=1}^{N_1} f_{1,\mathcal{Z}_1}^{(i)}+N_0^{-1}\sum_{i=1}^{N_0} \left(f_{0,\mathcal{Z}_0}^{(i)}-f_{1,\mathcal{Z}_0}^{(i)}\right)

Where samples :math:`\mathcal{Z}=\mathcal{Z}_0\bigcup\mathcal{Z}_1` with :math:`\mathcal{Z}_0\bigcap\mathcal{Z}_1=\emptyset` and :math:`f_{\alpha,\mathcal{Z}_\kappa}^{(i)}` denotes an evaluation of :math:`f_\alpha` using a sample from the set :math:`\mathcal{Z}_\kappa`. More simply to evaluate this estimator we must evaluate the low fidelity model at a set of samples  :math:`\mathcal{Z}_1` and then evaluate the difference between the two models at another independet set :math:`\mathcal{Z}_0`.

To simplify notation let

.. math:: Y_{\alpha,\mathcal{Z}_{\alpha-1}}=-N_{\alpha}^{-1}\sum_{i=1}^{N_{\alpha}} \left(f_{\alpha+1,\mathcal{Z}_{\alpha}}^{(i)}-f_{\alpha,\mathcal{Z}_{\alpha}}^{(i)}\right)

so we can write 

.. math:: Q_{0,\mathcal{Z}}^\mathrm{ML}=Y_{0,\mathcal{Z}_0}+Y_{1,\mathcal{Z}_1}

where :math:`f_{2}=0`.
The variance of this estimator is given by

.. math:: \var{Q_{0,\mathcal{Z}}^\mathrm{ML}}=\var{Y_{0,\mathcal{Z}_0}+Y_{1,\mathcal{Z}_1}}=N_0^{-1}\var{Y_{0,\mathcal{Z}_0}}+N_1^{-1}\var{Y_{1,\mathcal{Z}_1}}
  
since :math:`\mathcal{Z}_0\bigcap\mathcal{Z}_1=\emptyset.`

From the previous equation we can see that MLMC works well if the variance of the difference between models is smaller than the variance of either model. Although the variance of the low-fidelity model is likely high, we can set :math:`N_0` to be large because the cost of evaluating the low-fidelity model is low. If the variance of the discrepancy is smaller we only need a smaller number of samples so that the two sources of error (the two terms on the RHS of the previous equation) are balanced.

Note above and below we assume that :math:`f_0` is the high-fidelity model, but typical multi-level literature assumes :math:`f_M` is the high-fidelity model. We adopt the reverse ordering to be consistent with control variate estimator literature.

Many Model MLMC
---------------

MLMC can easily be extended to estimator based on :math:`M+1` models. Letting :math:`f_0,\ldots,f_M` be an ensemble of :math:`M+1` models ordered by decreasing fidelity and cost (note typically MLMC literature reverses this order),  we simply introduce estimates of the differences between the remaining models. That is

.. math :: 
   :label: eq:ml-estimator

   Q_{0,\mathcal{Z}}^\mathrm{ML} = \sum_{\alpha=0}^M Y_{\alpha,\mathcal{Z}_\alpha}, \quad f_{M+1}=0

To compute this estimator we use the following algorithm, tarting with :math:`\alpha=M`$

#. Draw  :math:`N_\alpha` samples randomly from the PDF  :math:`\pdf` of the random variables.
#. Estimate :math:`f_{\alpha}` and :math:`f_{\alpha}` at the samples :math:`\mathcal{Z}_\alpha`
#. Compute the discrepancies :math:`Y_{\alpha,\mathcal{Z}_\alpha}` at each sample.
#. Decrease :math:`\alpha` and repeat steps 1-3. until :math:`\alpha=0`.
#. Compute the ML estimator using :eq:`eq:ml-estimator`

The sampling strategy used for MLMC is shown in figure :ref:`mlmc-sample-allocation`. Here it is clear that we evaluate only the lowest fidelity model with :math:`\mathcal{Z}_M` (this follows from the assumption that :math:`f_{M+1}=0`) and to to evaluate each discrepancy we must evaluate two consecutive models at the sets :math:`\mathcal{Z}_\alpha`.

.. list-table::

   * - 
       .. _mlmc-sample-allocation:

       .. figure:: ../../figures/mlmc.png
          :width: 50%
          :align: center

          MLMC sampling strategy

Because we use independent samples to estimate the expectation of each discrepancy, the variance of the estimator is

.. math:: \var{Q_{0,\mathcal{Z}}^\mathrm{ML}} = \sum_{\alpha=0}^M N_\alpha\var{Y_{\alpha,\mathcal{Z}_\alpha}}


Lets setup a problem to compute an MLMC estimate of :math:`\mean{f_0}`
using the following ensemble of models, taken from [PWGSIAM2016]_, which simulate a short column with a rectangular cross-sectional area subject to bending and axial force.

.. math::

   f_0(z)&=(1 - 4M/(b(h^2)Y) - (P/(bhY))^2)\\
   f_1(z)&=(1 - 3.8M/(b(h^2)Y) - ((P(1 + (M-2000)/4000))/(bhY))^2)\\
   f_2(z)&=(1 - M/(b(h^2)Y) - (P/(bhY))^2)\\
   f_3(z)&=(1 - M/(b(h^2)Y) - (P(1 + M)/(bhY))^2)\\
   f_4(z)&=(1 - M/(b(h^2)Y) - (P(1 + M)/(hY))^2)

where :math:`z = (b,h,P,M,Y)^T`
"""
import pyapprox as pya
import numpy as np
import matplotlib.pyplot as plt
from pyapprox.tests.test_control_variate_monte_carlo import \
    TunableModelEnsemble, ShortColumnModelEnsemble, PolynomialModelEnsemble 
from scipy.stats import uniform
from functools import partial
from scipy.stats import uniform,norm,lognorm
np.random.seed(1)

short_column_model = ShortColumnModelEnsemble()
model_ensemble = pya.ModelEnsemble(
    [short_column_model.m0,short_column_model.m1,short_column_model.m2])

costs = np.asarray([100, 50, 5])
target_cost = int(1e4)
idx = [0,1,2]
cov = short_column_model.get_covariance_matrix()[np.ix_(idx,idx)]
# generate pilot samples to estimate correlation
# npilot_samples = int(1e4)
# cov = pya.estimate_model_ensemble_covariance(
#    npilot_samples,short_column_model.generate_samples,model_ensemble)[0]

# define the sample allocation
nhf_samples,nsample_ratios = pya.allocate_samples_mlmc(
    cov, costs, target_cost)[:2]
# generate sample sets
samples,values =pya.generate_samples_and_values_mlmc(
    nhf_samples,nsample_ratios,model_ensemble,
    short_column_model.generate_samples)
# compute mean using only hf data
hf_mean = values[0][0].mean()
# compute mlmc control variate weights
eta = pya.get_mlmc_control_variate_weights(cov.shape[0])
# compute MLMC mean
mlmc_mean = pya.compute_approximate_control_variate_mean_estimate(eta,values)

# get the true mean of the high-fidelity model
true_mean = short_column_model.get_means()[0]
print('MLMC error',abs(mlmc_mean-true_mean))
print('MC error',abs(hf_mean-true_mean))


#%%
#These errors are comparable. However these errors are only for one realization of the samples sets. To obtain a clearer picture on the benefits of MLMC we need to look at the variance of the estimator.
#
#By viewing MLMC as a control variate we can derive its variance reduction [GGEJJCP2020]_
#
#.. math::  \gamma+1 = - \eta_1^2 \tau_{1}^2 - 2 \eta_1 \rho_{1} \tau_{1} - \eta_M^2 \frac{\tau_{M}}{\hat{r}_{M}} - \sum_{i=2}^M \frac{1}{\hat{r}_{i-1}}\left( \eta_i^2 \tau_{i}^2 + \tau_{i-1}^2 \tau_{i-1}^2 - 2 \eta_i \eta_{i-1} \rho_{i,i-1} \tau_{i} \tau_{i-1} \right),
#   :label: mlmc-variance-reduction
#
#where  :math:`\tau_\alpha=\left(\frac{\var{Q_\alpha}}{\var{Q_0}}\right)^{\frac{1}{2}}`. Recall that and :math:`\hat{r}_\alpha=\lvert\mathcal{Z}_{\alpha,2}\rvert/N` is the ratio of the cardinality of the sets :math:`\mathcal{Z}_{\alpha,2}` and :math:`\mathcal{Z}_{0,2}`. 
#
#The following code computes the variance reduction of the MLMC estimator, using the 2 models :math:`f_0,f_1`. The variance reduction is estimated numerically by  running MLMC repeatedly with different realizations of the sample sets. The function ``get_rsquared_mlmc`` is used to return the theoretical variance reduction.
ntrials=1e1
get_cv_weights_mlmc = pya.get_mlmc_control_variate_weights_pool_wrapper
means1, numerical_var_reduction1, true_var_reduction1 = \
    pya.estimate_variance_reduction(
        model_ensemble, cov[:2,:2], short_column_model.generate_samples,
        pya.allocate_samples_mlmc,
        pya.generate_samples_and_values_mlmc, get_cv_weights_mlmc,
        pya.get_rsquared_mlmc,ntrials=ntrials,max_eval_concurrency=1,
        costs=costs[:2],target_cost=target_cost)
print("Theoretical 2 model MLMC variance reduction",true_var_reduction1)
print("Achieved 2 model MLMC variance reduction",numerical_var_reduction1)


#%%
# The numerical estimate of the variance reduction is consistent with the theory.
# Now let us compute the theoretical variance reduction using 3 models

true_var_reduction2 = 1-pya.get_rsquared_mlmc(cov,nsample_ratios)
print("Theoretical 3 model MLMC variance reduction",true_var_reduction2)

#%%
#The variance reduction obtained using three models is only slightly better than when using two models. The difference in variance reduction is dependent on the correlations between the models and the number of samples assigned to each model.
#
#MLMC works extremely well when the variance between the model discrepancies decays with increaseing fidelity. However one needs to be careful that the variance between discrepancies does indeed decay. Sometimes when the models correspond to different mesh discretizations. Increasing the mesh resolution does not always produce a smaller discrepancy. The following example shows that, for this example, adding a third model actually increases the variance of the MLMC estimator. 

model_ensemble = pya.ModelEnsemble(
    [short_column_model.m0,short_column_model.m3,short_column_model.m4])
idx = [0,3,4]
cov3 = short_column_model.get_covariance_matrix()[np.ix_(idx,idx)]
true_var_reduction3 = 1-pya.get_rsquared_mlmc(cov3,nsample_ratios)
print("Theoretical 3 model MLMC variance reduction for a pathalogical example",true_var_reduction3)

#%%
#Using MLMC for this ensemble of models creates an estimate with a variance orders of magnitude larger than just using the high-fidelity model. When using models that do not admit a hierarchical structure, alternative approaches are needed. We will introduce such estimators in future tutorials.
#

#%%
#Optimal Sample Allocation
#-------------------------
#Up to this point we have assumed that the number of samples allocated to each model was fixed. However one major advantage of MLMC is that we can analytically determine the optimal number of samples assigned to each model used in a MLMC estimator. This section follows closely the exposition in [GAN2015]_.
#
#Let :math:`C_\alpha` be the cost of evaluating the function :math:`f_\alpha` at a single sample, then the total cost of the MLMC estimator is
#
#.. math::
#
#   C_{\mathrm{tot}}=\sum_{l=0}^M C_\alpha N_\alpha
#  
#Now recall that the variance of the estimator is
#
#.. math:: \var{Q_0^\mathrm{ML}}=\sum_{\alpha=0}^M \var{Y_\alpha}N_\alpha,
#
#where :math:`Y_\alpha` is the disrepancy between two consecutive models, e.g. :math:`f_{\alpha-1}-f_\alpha` and :math:`N_\alpha` be the number of samples allocated to resolving the discrepancy, i.e. :math:`N_\alpha=\lvert\hat{\mathcal{Z}}_\alpha\rvert`. Then For a fixed variance :math:`\epsilon^2` the cost of the MLMC estimator can be minimized, by solving
#
#.. math::
#
#  \min_{N_0,\ldots,N_M} & \sum_{\alpha=0}^M\left(N_\alpha C_\alpha\right)\\
#  \mathrm{subject}\; \mathrm{to} &\sum_{\alpha=0}^M\left(N_\alpha^{-1}\var{Y_\alpha}\right)=\epsilon^2
#
#or alternatively by introducing the lagrange multiplier :math:`\lambda^2` we can minimize
#
#.. math:: 
#
#   \mathcal{J}(N_0,\ldots,N_M,\lambda)&=\sum_{\alpha=0}^M\left(N_\alpha C_\alpha\right)+\lambda^2\left(\sum_{\alpha=0}^M\left(N_\alpha^{-1}\var{Y_\alpha}\right)-\epsilon^2\right)\\
#   &=\sum_{\alpha=0}^M\left(N_\alpha C_\alpha+\lambda^2N_\alpha^{-1}\var{Y_\alpha}\right)-\lambda^2\epsilon^2
#
#To find the minimum we set the gradient of this expression to zero:
#
#.. math::
#
#  \frac{\partial \mathcal{J}^\mathrm{ML}}{N_\alpha}&=C_\alpha-\lambda^2N_\alpha^{-2}\var{Y_\alpha}=0\\
#  \implies C_\alpha&=\lambda^2N_\alpha^{-2}\var{Y_\alpha}\\
#  \implies N_\alpha&=\lambda\sqrt{\var{Y_\alpha}C_\alpha^{-1}}
#
#The constraint is satisifed by noting 
#
#.. math:: \frac{\partial \mathcal{J}}{\lambda^2}=\sum_{\alpha=0}^M N_\alpha^{-1}\var{Y_\alpha}-\epsilon^2=0
#
#Recalling that we can write the total variance as
#
#.. math::
#
#  \var{Q_{0,\mathcal{Z}}^\mathrm{ML}}&=\sum_{\alpha=0}^M N_\alpha^{-1} \var{Y_\alpha}\\
#  &=\sum_{\alpha=0}^M \lambda^{-1}\var{Y_\alpha}^{-\frac{1}{2}}C_\alpha^{\frac{1}{2}}\var{Y_\alpha}\\
#  &=\lambda^{-1}\sum_{\alpha=0}^M\sqrt{\var{Y_\alpha}C_\alpha}=\epsilon^2\\
#  \implies \lambda &= \epsilon^{-2}\sum_{\alpha=0}^M\sqrt{\var{Y_\alpha}C_\alpha}
#
#Then substituting :math:`\lambda` into the following
#
#.. math::
#
#  N_\alpha C_\alpha&=\lambda\sqrt{\var{Y_\alpha}C_\alpha^{-1}}C_\alpha\\
#  &=\lambda\sqrt{\var{Y_\alpha}C_\alpha}\\
#  &=\epsilon^{-2}\left(\sum_{\alpha=0}^M\sqrt{\var{Y_\alpha}C_\alpha}\right)\sqrt{\var{Y_\alpha}C_\alpha}
#  
#allows us to determine the smallest total cost that generates and estimator with the desired variance.
#
#.. math::
#
#  C_\mathrm{tot}&=\sum_{\alpha=0}^M N_\alpha C_\alpha\\
#  &=\sum_{\alpha=0}^M \epsilon^{-2}\left(\sum_{\alpha=0}^M\sqrt{\var{Y_\alpha}C_\alpha}\right)\sqrt{\var{Y_\alpha}C_\alpha}\\
#  &=\epsilon^{-2}\left(\sum_{\alpha=0}^M\sqrt{\var{Y_\alpha}C_\alpha}\right)^2
#
#To demonstrate the effectiveness of MLMC consider the model ensemble
#
#.. math:: f_\alpha(\rv)=\rv^{5-\alpha}, \quad \alpha=0,\ldots,4
#
#where each model is the function of a single uniform random variable defined on the unit interval :math:`[0,1]`. The following code computes the variance of the MLMC estimator for different target costs using the optimal sample allocation using an exact estimate of the covariance between models and an approximation.


import numpy as np
import pyapprox as pya
import matplotlib.pyplot as plt
from pyapprox.tests.test_control_variate_monte_carlo import \
    PolynomialModelEnsemble
np.random.seed(1)

poly_model = PolynomialModelEnsemble()
model_ensemble = pya.ModelEnsemble(poly_model.models)
cov = poly_model.get_covariance_matrix()
target_costs = np.array([1e1,1e2,1e3,1e4],dtype=int)
costs = np.asarray([10**-ii for ii in range(cov.shape[0])])
model_labels=[r'$f_0$',r'$f_1$',r'$f_2$',r'$f_3$',r'$f_4$']

def plot_mlmc_error():
    """
    Define function to create plot so we can create it later and add
    other estimator error curves.

    Note this is only necessary for sphinx-gallery docs. If just using the 
    jupyter notebooks they create then we do not need this function definition 
    and simply need to call fig at end of next cell to regenerate plot.
    """
    variances, nsamples_history = [],[]
    npilot_samples = 5
    estimator = pya.MLMC
    for target_cost in target_costs:
        # compute variance  using exact covariance for sample allocation
        est = estimator(cov,costs)
        nhf_samples,nsample_ratios = est.allocate_samples(target_cost)[:2]
        variances.append(est.get_variance(nhf_samples,nsample_ratios))
        nsamples_history.append(est.get_nsamples(nhf_samples,nsample_ratios))
        # compute single fidelity Monte Carlo variance
        total_cost = nsamples_history[-1].dot(costs)
        variances.append(cov[0,0]/int(total_cost/costs[0]))
        nsamples_history.append(int(total_cost/costs[0]))
        # compute variance using approx covariance for sample allocation
        # use nhf_samples from previous target_cost as npilot_samples.
        # This way the pilot samples are only an additional cost at the first
        # step. This code does not do this though for simplicity
        cov_approx = pya.estimate_model_ensemble_covariance(
            npilot_samples,poly_model.generate_samples,model_ensemble)[0]
        est = estimator(cov_approx,costs)
        nhf_samples,nsample_ratios = est.allocate_samples(target_cost)[:2]
        variances.append(est.get_variance(nhf_samples,nsample_ratios))
        nsamples_history.append(est.get_nsamples(nhf_samples,nsample_ratios))
        npilot_samples = nhf_samples

    fig,axs=plt.subplots(1,2,figsize=(2*8,6))
    pya.plot_acv_sample_allocation(nsamples_history[::3],costs,model_labels,axs[1])
    total_costs = np.array(nsamples_history[::3]).dot(costs)
    axs[0].loglog(total_costs,variances[::3],label=r'$\mathrm{MLMC}$')
    mc_line = axs[0].loglog(total_costs,variances[1::3],label=r'$\mathrm{MC}$')
    total_costs = np.array(nsamples_history[2::3]).dot(costs)
    axs[0].loglog(total_costs,variances[2::3],'--',
                  label=r'$\mathrm{MLMC^\dagger}$')
    axs[0].set_xlabel(r'$\mathrm{Total}\;\mathrm{Cost}$')
    axs[0].set_ylabel(r'$\mathrm{Variance}$')
    _ = axs[0].legend()
    return fig,axs

fig,axs = plot_mlmc_error()
plt.show()
    
#%%
#The left plot shows that the variance of the MLMC estimator is over and order of magnitude smaller than the variance of the single fidelity MC estimator for a fixed cost. The impact of using the approximate covariance is more significant for small samples sizes.
#
#The right plot depicts the percentage of the computational cost due to evaluating each model. The numbers in the bars represent the number of samples allocated to each model. Relative to the low fidelity models only a small number of samples are allocated to the high-fidelity model, however evaluating these samples represents approximately 50\% of the total cost.

#%%
#Multi-index Monte Carlo
#-----------------------
#Multi-Level Monte Carlo utilizes a sequence of models controlled by a single hyper-parameter, specifying the level of discretization for example, in a manner that balances computational cost with increasing accuracy. In many applications, however, multiple hyper-parameters may control the model discretization, such as the mesh and time step sizes. In these situations, it may not be clear how to construct a one-dimensional hierarchy represented by a scalar hyper-parameter. To overcome this limitation, a generalization of multi-level Monte Carlo, referred to as multi-index stochastic collocation (MIMC), was developed to deal with multivariate hierarchies with multiple refinement hyper-parameters [HNTNM2016]_.  PyApprox does not implement MIMC but a surrogate based version called Multi-index stochastic collocation (MISC) is presented in this tutorial :ref:`sphx_glr_auto_tutorials_multi_fidelity_plot_multi_index_collocation.py`.

#%%
#References
#^^^^^^^^^^
#.. [CGSTCVS2011] `K.A. Cliffe, M.B. Giles, R. Scheichl, A.L. Teckentrup, Multilevel Monte Carlo methods and applications to elliptic PDEs with random coefficients, Comput. Vis. Sci., 14, 3-15, 2011. <https://doi.org/10.1007/s00791-011-0160-x>`_0
#
#.. [GOR2008] `M.B. Giles, Multilevel Monte Carlo path simulation, Oper. Res., 56(3), 607-617, 2008. <https://doi.org/10.1287/opre.1070.0496>`_
#
#.. [GAN2015] `M. Giles, Multilevel Monte Carlo methods, Acta Numerica, 24, 259-328, 2015. <https://doi.org/10.1017/S096249291500001X>`_
#
#.. [HNTNM2016] `A. Haji-Ali, F. Nobile and R. Tempone. Multi-index Monte Carlo: when sparsity meets sampling. Numerische Mathematik, 132(4), 767-806, 2016. <https://doi.org/10.1007/s00211-015-0734-5>`_
