# contains additional tests for continuous distributions
#
# NOTE: one test, _est_cont_skip, that is renamed so that nose doesn't
#       run it,
#       6 distributions return nan for entropy
#       truncnorm fails by design for private method _ppf test
from __future__ import division, print_function, absolute_import

import warnings

import numpy.testing as npt
import numpy as np

from scipy import stats

from test_continuous_basic import distcont

DECIMAL = 5


@npt.dec.slow
def test_cont_extra():
    for distname, arg in distcont[:]:
        distfn = getattr(stats, distname)

        yield check_ppf_limits, distfn, arg, distname + \
              ' ppf limit test'
        yield check_isf_limits, distfn, arg, distname + \
              ' isf limit test'
        yield check_loc_scale, distfn, arg, distname + \
              ' loc, scale test'


@npt.dec.slow
def _est_cont_skip():
    for distname, arg in distcont:
        distfn = getattr(stats, distname)
        #entropy test checks only for isnan, currently 6 isnan left
        yield check_entropy, distfn, arg, distname + \
              ' entropy nan test'
        # _ppf test has 1 failure be design
        yield check_ppf_private, distfn, arg, distname + \
              ' _ppf private test'


def test_540_567():
    # test for nan returned in tickets 540, 567
    npt.assert_almost_equal(stats.norm.cdf(-1.7624320982),0.03899815971089126,
                            decimal=10, err_msg='test_540_567')
    npt.assert_almost_equal(stats.norm.cdf(-1.7624320983),0.038998159702449846,
                            decimal=10, err_msg='test_540_567')
    npt.assert_almost_equal(stats.norm.cdf(1.38629436112, loc=0.950273420309,
                            scale=0.204423758009),0.98353464004309321,
                            decimal=10, err_msg='test_540_567')


def check_ppf_limits(distfn,arg,msg):
    below,low,upp,above = distfn.ppf([-1,0,1,2], *arg)
    #print distfn.name, distfn.a, low, distfn.b, upp
    #print distfn.name,below,low,upp,above
    assert_equal_inf_nan(distfn.a,low, msg + 'ppf lower bound')
    assert_equal_inf_nan(distfn.b,upp, msg + 'ppf upper bound')
    npt.assert_(np.isnan(below), msg + 'ppf out of bounds - below')
    npt.assert_(np.isnan(above), msg + 'ppf out of bounds - above')


def check_ppf_private(distfn,arg,msg):
    #fails by design for trunk norm self.nb not defined
    ppfs = distfn._ppf(np.array([0.1,0.5,0.9]), *arg)
    npt.assert_(not np.any(np.isnan(ppfs)), msg + 'ppf private is nan')


def check_isf_limits(distfn,arg,msg):
    below,low,upp,above = distfn.isf([-1,0,1,2], *arg)
    #print distfn.name, distfn.a, low, distfn.b, upp
    #print distfn.name,below,low,upp,above
    assert_equal_inf_nan(distfn.a,upp, msg + 'isf lower bound')
    assert_equal_inf_nan(distfn.b,low, msg + 'isf upper bound')
    npt.assert_(np.isnan(below), msg + 'isf out of bounds - below')
    npt.assert_(np.isnan(above), msg + 'isf out of bounds - above')


def check_loc_scale(distfn,arg,msg):
    m,v = distfn.stats(*arg)
    loc, scale = 10.0, 10.0
    mt,vt = distfn.stats(loc=loc, scale=scale, *arg)
    assert_equal_inf_nan(m*scale+loc,mt,msg + 'mean')
    assert_equal_inf_nan(v*scale*scale,vt,msg + 'var')


def check_entropy(distfn,arg,msg):
    ent = distfn.entropy(*arg)
    #print 'Entropy =', ent
    npt.assert_(not np.isnan(ent), msg + 'test Entropy is nan')


def assert_equal_inf_nan(v1,v2,msg):
    npt.assert_(not np.isnan(v1))
    if not np.isinf(v1):
        npt.assert_almost_equal(v1, v2, decimal=DECIMAL, err_msg=msg +
                                   ' - finite')
    else:
        npt.assert_(np.isinf(v2) or np.isnan(v2),
               msg + ' - infinite, v2=%s' % str(v2))


def test_erlang_runtimewarning():
    # erlang should generate a RuntimeWarning if a non-integer
    # shape parameter is used.
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)

        # The non-integer shape parameter 1.3 should trigger a RuntimeWarning
        npt.assert_raises(RuntimeWarning,
                          stats.erlang.rvs, 1.3, loc=0, scale=1, size=4)

        # Calling the fit method with `f0` set to an integer should
        # *not* trigger a RuntimeWarning.  It should return the same
        # values as gamma.fit(...).
        data = [0.5, 1.0, 2.0, 4.0]
        result_erlang = stats.erlang.fit(data, f0=1)
        result_gamma = stats.gamma.fit(data, f0=1)
        npt.assert_allclose(result_erlang, result_gamma, rtol=1e-3)


@npt.dec.slow
def test_rdist_cdf_gh1285():
    # check workaround in rdist._cdf for issue gh-1285.
    distfn = stats.rdist
    values = [0.001, 0.5, 0.999]
    npt.assert_almost_equal(distfn.cdf(distfn.ppf(values, 541.0), 541.0),
                            values, decimal=5)


def test_rice_zero_b():
    # rice distribution should work with b=0, cf gh-2164
    x = [0.2, 1., 5.]
    npt.assert_(np.isfinite(stats.rice.pdf(x, b=0.)).all())
    npt.assert_(np.isfinite(stats.rice.logpdf(x, b=0.)).all())
    npt.assert_(np.isfinite(stats.rice.cdf(x, b=0.)).all())
    npt.assert_(np.isfinite(stats.rice.logcdf(x, b=0.)).all())

    q = [0.1, 0.1, 0.5, 0.9]
    npt.assert_(np.isfinite(stats.rice.ppf(q, b=0.)).all())

    mvsk = stats.rice.stats(0, moments='mvsk')
    npt.assert_(np.isfinite(mvsk).all())

    # furthermore, pdf is continuous as b\to 0
    # rice.pdf(x, b\to 0) = x exp(-x^2/2) + O(b^2)
    # see e.g. Abramovich & Stegun 9.6.7 & 9.6.10
    b = 1e-8
    npt.assert_allclose(stats.rice.pdf(x, 0), stats.rice.pdf(x, b),
            atol = b, rtol=0)


def test_rice_rvs():
    rvs = stats.rice.rvs
    npt.assert_equal(rvs(b=3.).size, 1)
    npt.assert_equal(rvs(b=3., size=(3, 5)).shape, (3, 5))


if __name__ == "__main__":
    npt.run_module_suite()
