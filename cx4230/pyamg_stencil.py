"""
Construct sparse matrix from a local stencil

Adapted from: http://pyamg.googlecode.com/svn/trunk/pyamg/gallery/stencil.py
"""

__docformat__ = "restructuredtext en"

import numpy
import scipy

__all__ = ['stencil_grid']

def stencil_grid(S, grid, dtype=None, format=None):
    """Construct a sparse matrix form a local matrix stencil 
    
    Parameters
    ----------
    S : ndarray
        matrix stencil stored in rank N array
    grid : tuple
        tuple containing the N grid dimensions
    dtype :
        data type of the result
    format : string
        sparse matrix format to return, e.g. "csr", "coo", etc.

    Returns
    -------
    A : sparse matrix
        Sparse matrix which represents the operator given by applying
        stencil S at each vertex of a regular grid with given dimensions.

    Notes
    -----
    The grid vertices are enumerated as arange(prod(grid)).reshape(grid).
    This implies that the last grid dimension cycles fastest, while the 
    first dimension cycles slowest.  For example, if grid=(2,3) then the
    grid vertices are ordered as (0,0), (0,1), (0,2), (1,0), (1,1), (1,2).

    This coincides with the ordering used by the NumPy functions 
    ndenumerate() and mgrid().

    Examples
    --------
    >>> stencil = [-1,2,-1]  # 1D Poisson stencil
    >>> grid = (5,)          # 1D grid with 5 vertices
    >>> A = stencil_grid(stencil, grid, dtype=float, format='csr')   
    >>> A.todense()
    matrix([[ 2., -1.,  0.,  0.,  0.],
            [-1.,  2., -1.,  0.,  0.],
            [ 0., -1.,  2., -1.,  0.],
            [ 0.,  0., -1.,  2., -1.],
            [ 0.,  0.,  0., -1.,  2.]])
    
    >>> stencil = [[0,-1,0],[-1,4,-1],[0,-1,0]] # 2D Poisson stencil
    >>> grid = (3,3)                            # 2D grid with shape 3x3
    >>> A = stencil_grid(stencil, grid, dtype=float, format='csr')   
    >>> A.todense()
    matrix([[ 4., -1.,  0., -1.,  0.,  0.,  0.,  0.,  0.],
            [-1.,  4., -1.,  0., -1.,  0.,  0.,  0.,  0.],
            [ 0., -1.,  4.,  0.,  0., -1.,  0.,  0.,  0.],
            [-1.,  0.,  0.,  4., -1.,  0., -1.,  0.,  0.],
            [ 0., -1.,  0., -1.,  4., -1.,  0., -1.,  0.],
            [ 0.,  0., -1.,  0., -1.,  4.,  0.,  0., -1.],
            [ 0.,  0.,  0., -1.,  0.,  0.,  4., -1.,  0.],
            [ 0.,  0.,  0.,  0., -1.,  0., -1.,  4., -1.],
            [ 0.,  0.,  0.,  0.,  0., -1.,  0., -1.,  4.]])
    
    """

    S = numpy.asarray(S, dtype=dtype)
    grid = tuple(grid)

    if not (numpy.asarray(S.shape) % 2 == 1).all():
        raise ValueError('all stencil dimensions must be odd')
    
#    if len(grid) != numpy.rank(S):
    if len(grid) != S.ndim:
        raise ValueError('stencil rank must equal number of grid dimensions')
    
    if min(grid) < 1:
        raise ValueError('grid dimensions must be positive')
    
    N_v = numpy.prod(grid)  # number of vertices in the mesh
    N_s = (S != 0).sum()    # number of nonzero stencil entries

    # diagonal offsets 
    diags = numpy.zeros(N_s, dtype=int)  

    # compute index offset of each dof within the stencil
    strides = numpy.cumprod( [1] + list(reversed(grid)) )[:-1]
    indices = tuple(i.copy() for i in S.nonzero())
    for i,s in zip(indices,S.shape):
        i -= s // 2
    for stride,coords in zip(strides, reversed(indices)):
        diags += stride * coords

    data = S[ S != 0 ].repeat(N_v).reshape(N_s,N_v)

    indices = numpy.vstack(indices).T

    # zero boundary connections
    for index,diag in zip(indices,data):
        diag = diag.reshape(grid)
        for n,i in enumerate(index):
            if i > 0:
                s = [ slice(None) ]*len(grid)
                s[n] = slice(0,i)
                diag[s] = 0
            elif i < 0:
                s = [ slice(None) ]*len(grid)
                s[n] = slice(i,None)
                diag[s] = 0

    # remove diagonals that lie outside matrix
    mask = abs(diags) < N_v
    if not mask.all():
        diags = diags[mask]
        data  = data[mask]
    
    # sum duplicate diagonals
    if len(numpy.unique(diags)) != len(diags):
        new_diags = numpy.unique(diags)
        new_data  = numpy.zeros( (len(new_diags),data.shape[1]), dtype=data.dtype)

        for dia,dat in zip(diags,data):
            n = numpy.searchsorted(new_diags,dia)
            new_data[n,:] += dat
        
        diags = new_diags
        data  = new_data

    return scipy.sparse.dia_matrix((data,diags), shape=(N_v,N_v)).asformat(format)


if __name__ == '__main__':
    D = 2
    
    if D == 1:
        # 1D Laplacian
        S = array([-1,2,-1])
        grid = (4,)
    
    if D == 2:
        # 2D Laplacian
        S = array([[ 0,-1, 0],
                   [-1, 4,-1],
                   [ 0,-1, 0]])
        #S = array([[-1,-1,-1],
        #           [-1, 8,-1],
        #           [-1,-1,-1]])
        grid = (2,1)
    
    if D == 3:
        S = array([[[ 0, 0, 0],
                    [ 0,-1, 0],
                    [ 0, 0, 0]],
                   [[ 0,-1, 0],
                    [-1, 6,-1],
                    [ 0,-1, 0]],
                   [[ 0, 0, 0],  
                    [ 0,-1, 0],
                    [ 0, 0, 0]]])
        grid = (3,4,5)               
    
    A = stencil_grid( S, grid )
    
    print (A.todense())



