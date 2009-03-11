from theano.sparse import *

import random
import unittest
import theano

from theano import compile
from theano import gradient
from theano import gof

from theano.sparse.basic import _is_dense, _is_sparse, _is_dense_result, _is_sparse_result
from theano.sparse.basic import _mtypes, _mtype_to_str
from theano.tests import unittest_tools


def eval_outputs(outputs):
    return compile.function([], outputs)()[0]

class T_transpose(unittest.TestCase):
    def setUp(self):
        unittest_tools.seed_rng()

    def test_transpose_csc(self):
        sp = sparse.csc_matrix(sparse.eye(5,3))
        a = as_sparse(sp)
        self.failUnless(a.data is sp)
        self.failUnless(a.data.shape == (5,3))
        self.failUnless(a.type.dtype == 'float64', a.type.dtype)
        self.failUnless(a.type.format == 'csc', a.type.format)
        ta = transpose(a)
        self.failUnless(ta.type.dtype == 'float64', ta.type.dtype)
        self.failUnless(ta.type.format == 'csr', ta.type.format)

        vta = eval_outputs([ta])
        self.failUnless(vta.shape == (3,5))
    def test_transpose_csr(self):
        a = as_sparse(sparse.csr_matrix(sparse.eye(5,3)))
        self.failUnless(a.data.shape == (5,3))
        self.failUnless(a.type.dtype == 'float64')
        self.failUnless(a.type.format == 'csr')
        ta = transpose(a)
        self.failUnless(ta.type.dtype == 'float64', ta.type.dtype)
        self.failUnless(ta.type.format == 'csc', ta.type.format)

        vta = eval_outputs([ta])
        self.failUnless(vta.shape == (3,5))

class T_Add(unittest.TestCase):
    def testSS(self):
        for mtype in _mtypes:
            a = mtype(numpy.array([[1., 0], [3, 0], [0, 6]]))
            aR = as_sparse(a)
            self.failUnless(aR.data is a)
            self.failUnless(_is_sparse(a))
            self.failUnless(_is_sparse_result(aR))

            b = mtype(numpy.asarray([[0, 2.], [0, 4], [5, 0]]))
            bR = as_sparse(b)
            self.failUnless(bR.data is b)
            self.failUnless(_is_sparse(b))
            self.failUnless(_is_sparse_result(bR))

            apb = add(aR, bR)
            self.failUnless(_is_sparse_result(apb))

            self.failUnless(apb.type.dtype == aR.type.dtype, apb.type.dtype)
            self.failUnless(apb.type.dtype == bR.type.dtype, apb.type.dtype)
            self.failUnless(apb.type.format == aR.type.format, apb.type.format)
            self.failUnless(apb.type.format == bR.type.format, apb.type.format)

            val = eval_outputs([apb])
            self.failUnless(val.shape == (3,2))
            self.failUnless(numpy.all(val.todense() == (a + b).todense()))
            self.failUnless(numpy.all(val.todense() == numpy.array([[1., 2], [3, 4], [5, 6]])))

    def testSD(self):
        for mtype in _mtypes:
            a = numpy.array([[1., 0], [3, 0], [0, 6]])
            aR = tensor.as_tensor(a)
            self.failUnless(aR.data is a)
            self.failUnless(_is_dense(a))
            self.failUnless(_is_dense_result(aR))

            b = mtype(numpy.asarray([[0, 2.], [0, 4], [5, 0]]))
            bR = as_sparse(b)
            self.failUnless(bR.data is b)
            self.failUnless(_is_sparse(b))
            self.failUnless(_is_sparse_result(bR))

            apb = add(aR, bR)
            self.failUnless(_is_dense_result(apb))

            self.failUnless(apb.type.dtype == aR.type.dtype, apb.type.dtype)
            self.failUnless(apb.type.dtype == bR.type.dtype, apb.type.dtype)

            val = eval_outputs([apb])
            self.failUnless(val.shape == (3, 2))
            self.failUnless(numpy.all(val == (a + b)))
            self.failUnless(numpy.all(val == numpy.array([[1., 2], [3, 4], [5, 6]])))

    def testDS(self):
        for mtype in _mtypes:
            a = mtype(numpy.array([[1., 0], [3, 0], [0, 6]]))
            aR = as_sparse(a)
            self.failUnless(aR.data is a)
            self.failUnless(_is_sparse(a))
            self.failUnless(_is_sparse_result(aR))

            b = numpy.asarray([[0, 2.], [0, 4], [5, 0]])
            bR = tensor.as_tensor(b)
            self.failUnless(bR.data is b)
            self.failUnless(_is_dense(b))
            self.failUnless(_is_dense_result(bR))

            apb = add(aR, bR)
            self.failUnless(_is_dense_result(apb))

            self.failUnless(apb.type.dtype == aR.type.dtype, apb.type.dtype)
            self.failUnless(apb.type.dtype == bR.type.dtype, apb.type.dtype)

            val = eval_outputs([apb])
            self.failUnless(val.shape == (3, 2))
            self.failUnless(numpy.all(val == (a + b)))
            self.failUnless(numpy.all(val == numpy.array([[1., 2], [3, 4], [5, 6]])))

class T_conversion(unittest.TestCase):
    def setUp(self):
        unittest_tools.seed_rng()

    def test0(self):
        a = tensor.as_tensor(numpy.random.rand(5))
        s = csc_from_dense(a)
        val = eval_outputs([s])
        self.failUnless(str(val.dtype)=='float64')
        self.failUnless(val.format == 'csc')

    def test1(self):
        a = tensor.as_tensor(numpy.random.rand(5))
        s = csr_from_dense(a)
        val = eval_outputs([s])
        self.failUnless(str(val.dtype)=='float64')
        self.failUnless(val.format == 'csr')

    def test2(self):
        for t in _mtypes:
            s = t((2,5))
            d = dense_from_sparse(s)
            s[0,0] = 1.0
            val = eval_outputs([d])
            self.failUnless(str(val.dtype)=='float64')
            self.failUnless(numpy.all(val[0] == [1,0,0,0,0]))


import scipy.sparse as sp
class test_structureddot(unittest.TestCase):

    def test_structuredot(self):

        #bsize = 5
        #spmat = sp.csc_matrix((8,15))
        #spmat[1,2] = 3
        #spmat[4,7] = 6
        #spmat[2,7] = 72
        #spmat[1,9] = 2
        #spmat[7,12] = 1
        #spmat[4,2] = 7
 
        bsize = 2
        spmat = sp.csc_matrix((5,5))
        spmat[1,2] = 1
        spmat[0,1] = 2
        spmat[0,2] = 3

      
        kerns = tensor.dvector()
        images = tensor.dmatrix()

        def buildgraphCSC(kerns,images):
            csc = CSC(kerns, spmat.indices[:spmat.size], spmat.indptr, spmat.shape)
            return structured_dot(csc, images.T)
        out = buildgraphCSC(kerns,images)

        f = theano.function([kerns,images], out)
        kernvals = spmat.data[:spmat.size]
        imvals = 1.0 * numpy.arange(bsize*spmat.shape[1]).reshape(bsize,spmat.shape[1])
        outvals = f(kernvals,imvals)
        print type(spmat.dot(imvals.T))
        print spmat.dot(imvals.T)
        print dir(spmat.dot(imvals.T))

#       scipy 0.7.0 should already make the output dense
#       assert numpy.all(outvals == spmat.dot(imvals.T).todense())
        c = spmat.dot(imvals.T)
        assert _is_dense(c)
        assert numpy.all(outvals == c)

        tensor.verify_grad(None, buildgraphCSC, [kernvals,imvals])

        spmat = spmat.tocsr()
        def buildgraphCSR(kerns,images):
            csr = CSR(kerns, spmat.indices[:spmat.size], spmat.indptr, spmat.shape)
            return structured_dot(csr, images.T)
        out = buildgraphCSR(kerns,images)

        f = theano.function([kerns,images], out)
        kernvals = spmat.data[:spmat.size]
        imvals = 1.0 * numpy.arange(bsize*spmat.shape[1]).reshape(bsize,spmat.shape[1])
        outvals = f(kernvals,imvals)

#       scipy 0.7.0 should already make the output dense
#       assert numpy.all(outvals == spmat.dot(imvals.T).todense())
        c = spmat.dot(imvals.T)
        assert _is_dense(c)
        assert numpy.all(outvals == c)

        tensor.verify_grad(None, buildgraphCSR, [kernvals,imvals])


if __name__ == '__main__':
    unittest.main()
