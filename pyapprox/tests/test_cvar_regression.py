import unittest
from pyapprox.cvar_regression import *

def get_lognormal_example_exact_quantities(mu,sigma):
    f= lambda x: np.exp(x).T

    mean = np.exp(mu+sigma**2/2)
    
    def f_cdf(y):
        y = np.atleast_1d(y)
        vals = np.zeros_like(y)
        II = np.where(y>0)[0]
        vals[II]=normal_rv.cdf((np.log(y[II])-mu)/sigma)
        return vals
    
    # PDF of output variable (lognormal PDF)
    def f_pdf(y):
        vals = np.zeros_like(y)
        II = np.where(y>0)[0]
        vals[II] = np.exp(-(np.log(y[II])-mu)**2/(2*sigma**2))/(
            sigma*np.sqrt(2*np.pi)*y[II])
        return vals
    
    # Analytic VaR of model output
    VaR  = lambda p: np.exp(mu+sigma*np.sqrt(2)*erfinv(2*p-1))
    
    # Analytic VaR of model output
    CVaR = lambda p: mean*normal_rv.cdf(
        (mu+sigma**2-np.log(VaR(p)))/sigma)/(1-p)
    
    def cond_exp_le_eta(y):
        vals = np.zeros_like(y)
        II = np.where(y>0)[0]
        vals[II]=mean*normal_rv.cdf((np.log(y[II])-mu-sigma**2)/sigma)/f_cdf(
            y[II])
        return vals
        
    ssd  =  lambda y: f_cdf(y)*(y-cond_exp_le_eta(y))
    
    def cond_exp_y_ge_eta(y):
        vals = np.ones_like(y)*mean
        II = np.where(y>0)[0]
        vals[II] = mean*normal_rv.cdf(
            (mu+sigma**2-np.log(y[II]))/sigma)/(1-f_cdf(y[II]))
        return vals

    ssd_disutil  =  lambda eta: (1-f_cdf(-eta))*(eta+cond_exp_y_ge_eta(-eta))
    return f, f_cdf, f_pdf, VaR, CVaR, ssd, ssd_disutil

def get_log_truncated_normal_example_exact_quantities(lb,ub,mu,sigma):
    f = lambda x: np.exp(x).T

    #lb,ub passed to truncnorm_rv are defined for standard normal.
    #Adjust for mu and sigma using
    alpha, beta = (lb-mu)/sigma, (ub-mu)/sigma
    
    denom = normal_rv.cdf(beta)-normal_rv.cdf(alpha)
    #truncated_normal_cdf = lambda x: (
    #    normal_rv.cdf((x-mu)/sigma)-normal_rv.cdf(alpha))/denom
    truncated_normal_cdf=lambda x: truncnorm_rv.cdf(
        x,alpha,beta,loc=mu,scale=sigma)
    truncated_normal_pdf=lambda x: truncnorm_rv.pdf(
        x,alpha,beta,loc=mu,scale=sigma)
    truncated_normal_ppf=lambda p: truncnorm_rv.ppf(
        p,alpha,beta,loc=mu,scale=sigma)

    # CDF of output variable (log truncated normal PDF)
    def f_cdf(y):
        vals = np.zeros_like(y)
        II = np.where((y>np.exp(lb))&(y<np.exp(ub)))[0]
        vals[II]=truncated_normal_cdf(np.log(y[II]))
        JJ = np.where((y>=np.exp(ub)))[0]
        vals[JJ]=1.
        return vals
    
    # PDF of output variable (log truncated normal PDF)
    def f_pdf(y):
        vals = np.zeros_like(y)
        II = np.where((y>np.exp(lb))&(y<np.exp(ub)))[0]
        vals[II]=truncated_normal_pdf(np.log(y[II]))/y[II]
        return vals
    
    # Analytic VaR of model output
    VaR  = lambda p: np.exp(truncated_normal_ppf(p))
    
    const = np.exp(mu+sigma**2/2)
   
    # Analytic VaR of model output
    CVaR = lambda p: -0.5/denom*const/(1-p)*(
        erf((mu+sigma**2-ub)/(np.sqrt(2)*sigma))
        -erf((mu+sigma**2-np.log(VaR(p)))/(np.sqrt(2)*sigma)))
    
    def cond_exp_le_eta(y):
        vals = np.zeros_like(y)
        II = np.where((y>np.exp(lb))&(y<np.exp(ub)))[0]
        vals[II]=-0.5/denom*const*(
            erf((mu+sigma**2-np.log(y[II]))/(np.sqrt(2)*sigma))
            -erf((mu+sigma**2-lb)/(np.sqrt(2)*sigma)))/f_cdf(y[II])
        JJ = np.where((y>=np.exp(ub)))[0]
        vals[JJ]=mean
        return vals
    ssd  =  lambda y: f_cdf(y)*(y-cond_exp_le_eta(y))

    mean = CVaR(np.zeros(1))
    def cond_exp_y_ge_eta(y):
        vals = np.ones_like(y)*mean
        II = np.where((y>np.exp(lb))&(y<np.exp(ub)))[0]
        vals[II] = -0.5/denom*const*(
            erf((mu+sigma**2-ub)/(np.sqrt(2)*sigma))
            -erf((mu+sigma**2-np.log(y[II]))/(np.sqrt(2)*sigma)))/(
                1-f_cdf(y[II]))
        JJ = np.where((y>np.exp(ub)))[0]
        vals[JJ]=0
        return vals
    ssd_disutil = lambda eta: (1-f_cdf(-eta))*(eta+cond_exp_y_ge_eta(-eta))

    return f, f_cdf, f_pdf, VaR, CVaR, ssd, ssd_disutil


class TestCVaR(unittest.TestCase):

    def test_value_at_risk_normal(self):
        weights=None
        alpha=0.8
        num_samples = int(1e2)
        samples = np.random.normal(0,1,num_samples)
        xx = np.sort(samples)
        VaR,VaR_index = value_at_risk(xx,alpha,weights,samples_sorted=True)
        index = int(np.ceil(alpha*num_samples)-1)
        assert np.allclose(VaR_index,index)
        assert np.allclose(VaR,xx[index])

    def test_value_at_risk_lognormal(self):
        mu,sigma=0,1

        f = lambda x: np.exp(x).T
        VaR  = lambda p: np.exp(mu+sigma*np.sqrt(2)*erfinv(2*p-1))
        mean = np.exp(mu+sigma**2/2)
        CVaR = lambda p: mean*normal_rv.cdf(
            (mu+sigma**2-np.log(VaR(p)))/sigma)/(1-p)

        weights=None
        alpha=0.8
        num_samples = int(1e6)
        samples = f(np.random.normal(0,1,num_samples))
        xx = np.sort(samples)
        empirical_VaR,__ = value_at_risk(xx,alpha,weights,samples_sorted=True)
        #print(VaR(alpha),empirical_VaR)
        assert np.allclose(VaR(alpha),empirical_VaR,1e-2)

    def test_weighted_value_at_risk_normal(self):
        mu,sigma=1,1
        #bias_mu,bias_sigma=1.0,1
        bias_mu,bias_sigma=mu,sigma

        from scipy.special import erf
        VaR = lambda alpha: normal_rv.ppf(alpha,loc=mu,scale=sigma)
        def CVaR(alpha):
            vals =  0.5*mu
            vals -= 0.5*mu*erf((VaR(alpha)-mu)/(np.sqrt(2)*sigma))-\
                sigma*np.exp(-(mu-VaR(alpha))**2/(2*sigma**2))/np.sqrt(2*np.pi)
            vals /= (1-alpha)
            return vals

        alpha=0.8
        num_samples = int(1e5)
        samples = np.random.normal(bias_mu,bias_sigma,num_samples)
        target_pdf_vals = normal_rv.pdf(samples,loc=mu,scale=sigma)
        bias_pdf_vals   = normal_rv.pdf(samples,loc=bias_mu,scale=bias_sigma)
        I = np.where(bias_pdf_vals<np.finfo(float).eps)[0]
        assert np.all(target_pdf_vals[I]<np.finfo(float).eps)
        J = np.where(bias_pdf_vals>=np.finfo(float).eps)[0]
        weights = np.zeros_like(target_pdf_vals)
        weights[J] = target_pdf_vals[J]/bias_pdf_vals[J]
        
        empirical_VaR,__ = value_at_risk(
            samples,alpha,weights,samples_sorted=False)
        #print('VaR',VaR(alpha),empirical_VaR)
        assert np.allclose(VaR(alpha),empirical_VaR,rtol=1e-2)

        empirical_CVaR = conditional_value_at_risk(
            samples,alpha,weights)
        #print('CVaR',CVaR(alpha),empirical_CVaR)
        assert np.allclose(CVaR(alpha),empirical_CVaR,rtol=1e-2)

    def test_equivalent_formulations_of_cvar(self):
        mu,sigma=0,1
        f, f_cdf, f_pdf, VaR, CVaR, ssd, ssd_disutil = \
            get_lognormal_example_exact_quantities(mu,sigma)

        eps=1e-15
        lbx,ubx=normal_rv.ppf([eps,1-eps],loc=mu,scale=sigma)
        lbx,ubx = -np.inf,np.inf
        tol= 4*np.finfo(float).eps
        alpha=.8
        t = VaR(alpha)
        #fun1 = lambda x: np.maximum(f(x)-t,0)*normal_rv.pdf(x,loc=mu,scale=sigma)
        def fun1(x):
            x = np.atleast_1d(x)
            pdf_vals = normal_rv.pdf(x,loc=mu,scale=sigma)
            # Next line avoids problems caused by f(x) being to large or nan        
            I = np.where(pdf_vals>0)[0]
            vals = np.zeros_like(x)
            vals[I] = np.maximum(f(x[I])-t,0)*pdf_vals[I]
            return vals
        cvar1=t+1./(1.-alpha)*integrate.quad(
            fun1,lbx,ubx,epsabs=tol,epsrel=tol,full_output=True)[0]

        #fun2 = lambda x: f(x)*normal_rv.pdf(x,loc=mu,scale=sigma)
        def fun2(x):
            x = np.atleast_1d(x)
            pdf_vals = normal_rv.pdf(x,loc=mu,scale=sigma)
            # Next line avoids problems caused by f(x) being to large or nan
            I = np.where(pdf_vals>0)[0]
            vals = np.zeros_like(x)
            vals[I] = f(x[I])*pdf_vals[I]
            return vals
        x_cdf = partial(normal_rv.cdf,loc=mu,scale=sigma)
        integral = integrate.quad(
            fun2,np.log(t),ubx,epsabs=tol,epsrel=tol,full_output=True)[0]
        cvar2 = t+1./(1.-alpha)*(integral-t*(1-x_cdf(np.log(t))))
        #fun3 = lambda x: np.absolute(f(x)-t)*normal_rv.pdf(x,loc=mu,scale=sigma)
        def fun3(x):
            x = np.atleast_1d(x)
            pdf_vals = normal_rv.pdf(x,loc=mu,scale=sigma)
            # Next line avoids problems caused by f(x) being to large or nan
            I = np.where(pdf_vals>0)[0]
            vals = np.zeros_like(x)
            vals[I] = np.absolute(f(x[I])-t)*pdf_vals[I]
            return vals

        mean = CVaR(0)
        integral = integrate.quad(
            fun3,lbx,ubx,epsabs=tol,epsrel=tol,full_output=True)[0]
        cvar3 = t+0.5/(1.-alpha)*(integral+mean-t)

        lbx,ubx=-np.inf,np.inf
        value_at_risk4,cvar4 = compute_cvar_from_univariate_function(
            f,partial(normal_rv.pdf,loc=mu,scale=sigma),lbx,ubx,alpha,5,tol=1e-7)

        #print(abs(cvar1-CVaR(alpha)))
        #print(abs(cvar2-CVaR(alpha)))
        #print(abs(cvar3-CVaR(alpha)))
        #print(abs(cvar4-CVaR(alpha)))
        assert np.allclose(cvar1,CVaR(alpha))
        assert np.allclose(cvar2,CVaR(alpha))
        assert np.allclose(cvar3,CVaR(alpha))
        assert np.allclose(cvar4,CVaR(alpha))


if __name__== "__main__":    
    cvar_test_suite = unittest.TestLoader().loadTestsFromTestCase(
         TestCVaR)
    unittest.TextTestRunner(verbosity=2).run(cvar_test_suite)
