#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
:mod:`cape.geom`: Generic geometry utilities
==============================================

This module provides several methods for modifying points or performing
other geometric manipulations in a way accessible to each of the
subclasses.

The main categories are:

    * performing manipulations on sets of points, such as rotations
    * checking for intersections, polygon membership, etc.

"""

# Third-party modules
import numpy as np


# Function to rotate a triangulation about an arbitrary vector
def RotatePoints(X, v1, v2, theta):
    r"""Rotate a list of points

    :Call:
        >>> Y = RotatePoints(X, v1, v2, theta)
    :Inputs:
        *X*: :class:`numpy.ndarray`\ [:class:`float`]
            Array of node coordinates, *shape*: (N, 3)
        *v1*: :class:`numpy.ndarray`\ [:class:`float`]
            Start point of rotation vector, *shape*: (3,)
        *v2*: :class:`numpy.ndarray`\ [:class:`float`]
            End point of rotation vector, *shape*: (3,)
        *theta*: :class:`float`
            Rotation angle in degrees
    :Outputs:
        *Y*: :class:`numpy.ndarray`(:class:`float`), *shape* = (N,3)
            List of rotated node coordinates
    :Versions:
        * 2014-10-07 ``@ddalle``: Version 1.0, from :class:`TriBase`
    """
    # Convert points to NumPy.
    v1 = np.array(v1)
    v2 = np.array(v2)
    # Ensure array.
    if type(X).__name__ != 'ndarray':
        X = np.array(X)
    # Check for points.
    if X.size == 0:
        return X
    # Ensure list of points.
    if len(X.shape) == 1:
        X = np.array([X])
    # Extract the coordinates and shift origin.
    x = X[:,0] - v1[0]
    y = X[:,1] - v1[1]
    z = X[:,2] - v1[2]
    # Make the rotation vector
    v = (v2-v1) / np.linalg.linalg.norm(v2-v1)
    # Dot product of points with rotation vector
    k1 = v[0]*x + v[1]*y + v[2]*z
    # Trig functions
    c_th = np.cos(theta*np.pi/180.)
    s_th = np.sin(theta*np.pi/180.)
    # Initialize output.
    Y = X.copy()
    # Apply Rodrigues' rotation formula to get the rotated coordinates.
    Y[:,0] = x*c_th+(v[1]*z-v[2]*y)*s_th+v[0]*k1*(1-c_th)+v1[0]
    Y[:,1] = y*c_th+(v[2]*x-v[0]*z)*s_th+v[1]*k1*(1-c_th)+v1[1]
    Y[:,2] = z*c_th+(v[0]*y-v[1]*x)*s_th+v[2]*k1*(1-c_th)+v1[2]
    # Output
    return Y


# Function to rotate a triangulation about an arbitrary vector
def TranslatePoints(X, dR):
    r"""Translate the nodes of a triangulation object.

    The offset coordinates may be specified as individual inputs or a
    single vector of three coordinates.

    :Call:
        >>> TranslatePoints(X, dR)
    :Inputs:
        *X*: :class:`numpy.ndarray`\ [:class:`float`]
            List of node coordinates, *shape*: (N,3)
        *dR*: :class:`numpy.ndarray` | :class:`list`
            List of three coordinates to use for translation
    :Outputs:
        *Y*: :class:`numpy.ndarray`\ [:class:`float`]
            List of translated node coordinates, *shape*: (N,3)
    :Versions:
        * 2014-10-08 ``@ddalle``: Version 1.0
    """
    # Convert points to NumPy.
    dR = np.array(dR)
    # Ensure array.
    if not isinstance(X, np.ndarray):
        X = np.array(X)
    # Ensure list of points.
    if len(X.shape) == 1:
        X = np.array([X])
    # Initialize output.
    Y = X.copy()
    # Offset each coordinate.
    Y[:,0] += dR[0]
    Y[:,1] += dR[1]
    Y[:,2] += dR[2]
    # Output
    return Y


# Distance from a point to a line segment
def DistancePointToLine(x, x1, x2):
    r"""Get distance from a point to a line segment

    :Call:
        >>> d = DistancePointToLine(x, x1, x2)
    :Inputs:
        *x*: :class:`np.ndarray`\ [:class:`float`]
            Test point, *shape*: (3,)
        *x1*: :class:`np.ndarray`\ [:class:`float`]
            Segment start point, *shape*: (3,)
        *x2*: :class:`np.ndarray`\ [:class:`float`]
            Segment end point, *shape*: (3,)
    :Outputs:
        *d*: :class:`float`
            Distance from segment to point
    :Versions:
        * 2016-09-29 ``@ddalle``: Version 1.0
    """
    # Vector of the segment
    dx = x2 - x1
    # Vector to the point from both segment ends
    d1 = x - x1
    d2 = x - x2
    # Dot products
    c1 = dx[0]*d1[0] + dx[1]*d1[1] + dx[2]*d1[2]
    c2 = dx[0]*d2[0] + dx[1]*d2[1] + dx[2]*d2[2]
    # Test the location of the point relative to the segment
    if c1 <= 0:
        # Point is upstream of the segment; return distance to *x1*
        return np.sqrt(d1[0]**2 + d1[1]**2 + d1[2]**2)
    elif c2 >= 0:
        # Point is downstream of the segment, return distance to *x2*
        return np.sqrt(d2[0]**2 + d2[1]**2 + d2[2]**2)
    else:
        # Point is within segment
        # Length of segment
        ds = np.sqrt(dx[0]**2 + dx[1]**2 + dx[2]**2)
        # Compute cross product
        A0 = dx[1]*d1[2] - dx[2]*d1[1]
        A1 = dx[2]*d1[0] - dx[0]*d1[2]
        A2 = dx[0]*d1[1] - dx[1]*d1[0]
        # Distance = (Area of parallelogram) / (Length of base)
        return np.sqrt(A0*A0+A1*A1+A2*A2) / ds


# Distance from a point to a group of line segments
def DistancePointToCurve(x, X):
    r"""Get distance from point to segments of a piecewise linear curve

    :Call:
        >>> D = DistancePointToCurve(x, X)
    :Inputs:
        *x*: :class:`np.ndarray`\ [:class:`float`]
            Test point, *shape*: (3,)
        *X*: :class:`np.ndarray`\ [:class:`float`]
            Array of curve break points, *shape*: (n,3)
    :Outputs:
        *D*: :class:`np.ndarray`\ [:class:`float`]
            Distance from *x* to each segment, *shape*: (n-1,)
    :Versions:
        * 2016-09-29 ``@ddalle``: Version 1.0
    """
    # Vector segments
    dX = X[1:,:] - X[:-1,:]
    # Vector to the point from both segment ends
    dx = x[0] - X[:,0]
    dy = x[1] - X[:,1]
    dz = x[2] - X[:,2]
    # Dot products of end-to-end and end-to-*x* vectors
    c1 = dX[:,0]*dx[:-1] + dX[:,1]*dy[:-1] + dX[:,2]*dz[:-1]
    c2 = dX[:,0]*dx[1:]  + dX[:,1]*dy[1:]  + dX[:,2]*dz[1:]
    # Distance from *x* to each vertex
    di = np.sqrt(dx*dx + dy*dy + dz*dz)
    # Initialize with distance to first point
    D = np.fmin(di[:-1], di[1:])
    # Test for interior points
    I = np.logical_and(c1>0, c2<0)
    # Compute cross products for those segments
    A0 = dX[I,1]*dz[:-1][I] - dX[I,2]*dy[:-1][I]
    A1 = dX[I,2]*dx[:-1][I] - dX[I,0]*dz[:-1][I]
    A2 = dX[I,0]*dy[:-1][I] - dX[I,1]*dx[:-1][I]
    # Arc lengths
    ds = np.sqrt(np.sum(dX[I,:]**2, axis=1))
    # Apply interior distances
    D[I] = np.sqrt(A0*A0 + A1*A1 + A2*A2) / ds
    # Output
    return D


# Check for intersection between lines
def lines_int_line(X1, Y1, X2, Y2, x1, y1, x2, y2, **kw):
    r"""Check if a set of line segments intersects another line segment

    :Call:
        >>> Q = lines_int_line(X1, Y1, X2, Y2, x1, y1, x2, y2, **kw)
    :Inputs:
        *X1*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of start points of several line segments
        *Y1*: :class:`np.ndarray`\ [:class:`float`]
            *y*-coords of start points of several line segments
        *X2*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of end points of several line segments
        *Y2*: :class:`np.ndarray`\ [:class:`float`]
            *y*-coords of end points of several line segments
        *x1*: :class:`float` | :class:`np.ndarray`
            Start point *x*-coordinate of test segment
        *y1*: :class:`float` | :class:`np.ndarray`
            Start point *y*-coordinate of test segment
        *x2*: :class:`float` | :class:`np.ndarray`
            End point *x*-coordinate of test segment
        *y2*: :class:`float` | :class:`np.ndarray`
            End point *y*-coordinate of test segment
    :Outputs:
        *Q*: :class:`np.ndarray`\ [:class:`bool`]
            Whether or not each segment intersects test segment
    :Versions:
        * 2017-02-06 ``@ddalle``: Version 1.0
    """
    # Length of test segment
    L = np.sqrt((x2-x1)**2 + (y2-y1)**2)
    # Tangent vector
    tx = (x2 - x1) / L
    ty = (y2 - y1) / L
    # Convert the list of segments into coordinates
    XI1 = (X1-x1)*tx + (Y1-y1)*ty
    XI2 = (X2-x1)*tx + (Y2-y1)*ty
    YI1 = (Y1-y1)*tx - (X1-x1)*ty
    YI2 = (Y2-y1)*tx - (X2-x1)*ty
    # Initial test: crosses y=0 line?
    Q = (YI1*YI2 <= 0)
    # Special filter for segments parallel to test segment
    I0 = np.logical_and(YI1==0, YI2==0)
    Q[I0] = False
    # For segments that cross y==0, find coordinate
    X0 = XI1[Q] - YI1[Q]*(XI2[Q]-XI1[Q]) / (YI2[Q]-YI1[Q])
    # Test those segments
    Q[Q] = np.logical_and(X0>=0, X0<=L)
    # Come back for the segments that are parallel to the test segment
    Q[I0] = np.logical_or(
        # Check if *x1* inside [0,L]
        (XI1[I0]-L)*XI1[I0] <= 0,
        # Check if *x2* inside [0,L]
        (XI2[I0]-L)*XI2[I0] <= 0,
        # Check if [x1,x2] or [x2,x1] contains [0,L]
        XI2[I0]*XI1[I0] <=0)
    # Output
    return Q


# Check for intersection between lines
def edges_int_line(X1, Y1, X2, Y2, x1, y1, x2, y2, **kw):
    r"""Check if a set of edges intersects another line segment

    Intersections between the test segment and the start point of any
    edge are not counted as an intersection.  The test point can either
    be a single point or a collection of points with dimensions equal to
    the collection of lines.

    :Call:
        >>> Q = edges_int_line(X1, Y1, X2, Y2, x1, y1, x2, y2, **kw)
    :Inputs:
        *X1*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of start points of several line segments
        *Y1*: :class:`np.ndarray`\ [:class:`float`]
            *y*-coords of start points of several line segments
        *X2*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of end points of several line segments
        *Y2*: :class:`np.ndarray`\ [:class:`float`]
            *y*-coords of end points of several line segments
        *x1*: :class:`float` | :class:`np.ndarray`
            Start point *x*-coordinate of test segment
        *y1*: :class:`float` | :class:`np.ndarray`
            Start point *y*-coordinate of test segment
        *x2*: :class:`float` | :class:`np.ndarray`
            End point *x*-coordinate of test segment
        *y2*: :class:`float` | :class:`np.ndarray`
            End point *y*-coordinate of test segment
    :Outputs:
        *Q*: :class:`np.ndarray` (:class:`bool`, shape=*X1.shape*)
            Matrix of whether or not each segment intersects test segment
    :Versions:
        * 2017-02-06 ``@ddalle``: Version 1.0
    """
    # Length of test segment
    L = np.sqrt((x2-x1)**2 + (y2-y1)**2)
    # Tangent vector
    tx = (x2 - x1) / L
    ty = (y2 - y1) / L
    # Convert the list of segments into coordinates
    XI1 = (X1-x1)*tx + (Y1-y1)*ty
    XI2 = (X2-x1)*tx + (Y2-y1)*ty
    YI1 = (Y1-y1)*tx - (X1-x1)*ty
    YI2 = (Y2-y1)*tx - (X2-x1)*ty
    # Check for single segment
    if type(L) != "ndarray":
        L = L*np.ones_like(XI1)
    # Initial test: crosses y=0 line?
    Q = (YI1*YI2 <= 0)
    # Special filter for segments parallel to test segment
    I0 = np.logical_and(YI1==0, YI2==0)
    Q[I0] = False
    # For segments that cross y==0, find coordinate
    X0 = XI1[Q] - YI1[Q]*(XI2[Q]-XI1[Q]) / (YI2[Q]-YI1[Q])
    # Test those segments
    Q[Q] = np.logical_and(X0>=0, X0<=L[Q])
    # Filter *OUT* intersections with (XI1, YI1)
    Q[YI1==0] = False
    # Come back for the segments that are parallel to the test segment
    Q[I0] = np.logical_or(
        # Check if *x1* strictly inside (0,L)
        (XI1[I0]-L[I0])*XI1[I0] < 0,
        # Check if *x2* inside [0,L]
        (XI2[I0]-L[I0])*XI2[I0] <= 0,
        # Check if [x1,x2] or [x2,x1] contains [0,L]
        XI2[I0]*XI1[I0] <=0)
    # Output
    return Q


# Check if a triangle contains a point
def tris_have_pt(X, Y, x, y, **kw):
    r"""Check if each triangle in a list contains a specified point(s)

    :Call:
        >>> Q = tris_have_pt(X, Y, x, y, **kw)
    :Inputs:
        *X*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of vertices of *n* tris, *shape*: (n,3)
        *Y*: :class:`np.ndarray`\ [:class:`float`]
            *y*-coords of vertices of *n* tris, *shape*: (n,3)
        *x*: :class:`float` | :class:`np.ndarray`
            *x*-coord of test point(s), *shape*: (n,)
        *y*: :class:`float` | :class:`np.ndarray`
            *y*-coord of test point(s), *shape*: (n,)
    :Outputs:
        *Q*: :class:`np.ndarray`\ [:class:`bool`]
            Whether or not each tri contains the test point
    :Versions:
        * 2017-02-06 ``@ddalle``: Version 1.0
        * 2022-11-02 ``@ddalle``: Version 2.0; use tri areas
    """
    # Check input type
    if isinstance(X, list):
        X = np.array(X)
    elif not isinstance(X, np.ndarray):
        # Convert to array
        raise TypeError("Triangles must be arrays")
    if isinstance(Y, list):
        # Convert to array
        Y = np.array(Y)
    elif not isinstance(Y, np.ndarray):
        # Convert to array
        raise TypeError("Triangles must be arrays")
    # Test for single triangle
    if X.ndim == 1:
        X = np.array([X])
    if Y.ndim == 1:
        Y = np.array([Y])
    # Check dimensions
    if X.shape[1] != 3:
        # Not triangles
        raise IndexError("Triangle arrays must have at least two columns")
    elif Y.shape[1] != 3:
        # Not triangles (Y)
        raise IndexError("Triangle arrays must have at least two columns")
    elif X.shape[0] != Y.shape[0]:
        # Not matching
        raise ValueError(
            "X and Y coordinate arrays have different number of triangles")
    # Unpack
    x0, x1, x2 = X.T
    y0, y1, y2 = Y.T
    # Store deltas
    xx0 = x - x0
    xx1 = x - x1
    xx2 = x - x2
    yy0 = y - y0
    yy1 = y - y1
    yy2 = y - y2
    # Total area
    A = np.abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))
    # Three component areas
    A0 = np.abs(xx1*yy2 - xx2*yy1)
    A1 = np.abs(xx2*yy0 - xx0*yy2)
    A2 = np.abs(xx0*yy1 - xx1*yy0)
    # Test sum of areas
    return A0 + A1 + A2 <= A * (1 + 1e-6) + 2e-12


# Get distance from point to a line segment
def dist2_lines_to_pt(X1, Y1, X2, Y2, x, y, **kw):
    r"""Get square of distance from point(s) to line segment(s)

    The test point can either be a single point or a collection of
    points with dimensions equal to the collection of lines.

    :Call:
        >>> d2 = dist2_lines_to_pt(X1, Y1, X2, Y2, x, y, **kw)
    :Inputs:
        *X1*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of start points of several line segments
        *Y1*: :class:`np.ndarray`\ [:class:`float`]
            *y*-coords of start points of several line segments
        *X2*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of end points of several line segments
        *Y2*: :class:`np.ndarray`\ [:class:`float`]
            *y*-coords of end points of several line segments
        *x*: :class:`float` | :class:`np.ndarray`
            *x*-coord of test point(s)
        *y*: :class:`float` | :class:`np.ndarray`
            *y*-coord of test point(s)
    :Outputs:
        *d2*: :class:`np.ndarray`\ [:class:`float`]
            Minimum distance from each segment to point
    :Versions:
        * 2022-11-01 ``@ddalle``: Version 1.0
    """
    # Deltas
    x12 = X2 - X1
    y12 = Y2 - Y1
    x01 = X1 - x
    y01 = Y1 - y
    x02 = X2 - x
    y02 = Y2 - y
    # Square of length of segment(s)
    L2 = np.fmax(1e-6, x12*x12 + y12*y12)
    # Normal component of distance times length
    Ld1 = x01*y12 - y01*x12
    # "Behind" component of tangent distance
    Ld2 = np.fmax(0, x01*x12 + y01*y12)
    # "Beyond" component of tangent distance
    Ld3 = np.fmax(0, -x02*x12 - y02*y12)
    # Two components (only 0 or 1 of d2 and d3 is positive)
    L2d2 = Ld1*Ld1 + (Ld2 + Ld3)**2
    # Divide length of segment
    return L2d2 / L2


# Get distance from point to a line segment
def dist_lines_to_pt(X1, Y1, X2, Y2, x, y, **kw):
    r"""Get distance from a point to a collection of line segments

    The test point can either be a single point or a collection of
    points with dimensions equal to the collection of lines.

    :Call:
        >>> D = dist_lines_to_pt(X1, Y1, X2, Y2, x, y, **kw)
    :Inputs:
        *X1*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of start points of several line segments
        *Y1*: :class:`np.ndarray`\ [:class:`float`]
            *y*-coords of start points of several line segments
        *X2*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of end points of several line segments
        *Y2*: :class:`np.ndarray`\ [:class:`float`]
            *y*-coords of end points of several line segments
        *x*: :class:`float` | :class:`np.ndarray`
            *x*-coord of test point(s)
        *y*: :class:`float` | :class:`np.ndarray`
            *y*-coord of test point(s)
    :Outputs:
        *D*: :class:`np.ndarray`\ [:class:`float`]
            Minimum distance from each segment to point
    :Versions:
        * 2017-02-06 ``@ddalle``: Version 1.0
    """
    # Calculate lengths of each segment
    L = np.sqrt((X2-X1)**2 + (Y2-Y1)**2)
    # Tangent/normal vector components
    TX = (X2 - X1) / L
    TY = (Y2 - Y1) / L
    # Pick any old direction if L==0
    TX[L==0] = 1.0
    TY[L==0] = 0.0
    # Convert test point (x,y) into tangent/normal coords for each line
    T = (x-X1)*TX + (y-Y1)*TY
    N = (y-Y1)*TX - (x-X1)*TY
    # If the normal going through the point intersects the segment, the
    # shortest distance is the point-to-line distance.  Initialize
    # distance as this smallest-possible-distance
    D = np.abs(N)
    # Check for segments where that nearest point is outside the segment
    I = np.logical_or(T < 0, T > L)
    # Distance from (x,y) to segment end points
    if isinstance(x, np.ndarray):
        W1 = (x[I]-X1[I])**2 + (y[I]-Y1[I])**2
        W2 = (x[I]-X2[I])**2 + (y[I]-Y2[I])**2
    else:
        W1 = (x-X1[I])**2 + (y-Y1[I])**2
        W2 = (x-X2[I])**2 + (y-Y2[I])**2
    # For such segments, use the distance to closest vertex
    D[I] = np.sqrt(np.fmin(W1, W2))
    # Output
    return D


# Get distance from a point
def dist2_tris_to_pt(X, Y, x, y, **kw):
    r"""Get square of distance from a point to a collection of triangles

    Points that are inside the triangle return a distance of 0

    :Call:
        >>> D = dist_tris_to_pt(X, Y, x, y)
    :Inputs:
        *X*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of vertices of *n* tris, *shape*: (n,3)
        *Y*: :class:`np.ndarray`\ [:class:`float`], shape=(n,3))
            *y*-coords of vertices of *n* tris, *shape*: (n,3)
        *x*: :class:`float`
            *x*-coordinate of test point
        *y*: :class:`float`
            *y*-coordinate of test point
    :Outputs:
        *D*: :class:`np.ndarray`\ [:class:`float`]
            Matrix of minimum distance squared from each tri to point
    :Versions:
        * 2017-02-06 ``@ddalle``: Version 1.0
        * 2022-11-01 ``@ddalle``: Version 2.0; faster
    """
    # Check for membership of each triangle
    Q = tris_have_pt(X, Y, x, y, **kw)
    # Get the complementary list
    Q0 = np.logical_not(Q)
    # Number of triangles
    n = Q.size
    # Initialize distance
    D = np.zeros(n)
    # For tris that do not contain (x,y), get distance to each segment
    X1 = X[Q0, :]
    Y1 = Y[Q0, :]
    X2 = X1[:, [1, 2, 0]] 
    Y2 = Y1[:, [1, 2, 0]]
    # Check for list of points
    if isinstance(x, np.ndarray):
        # Repeat for each vertex of the triangle
        x = np.transpose(np.vstack((x, x, x)))
        # Deselect points inside triangles
        x = x[Q0, :]
    if isinstance(y, np.ndarray):
        # Repeat for each vertex of the triangle
        y = np.transpose(np.vstack((y, y, y)))
        # Deselect points inside triangles
        y = y[Q0, :]
    # Get dist to each segment of each tri that does not contain the pt
    D2 = dist2_lines_to_pt(X1, Y1, X2, Y2, x, y, **kw)
    # Save the minimum pt-to-edge distance
    D[Q0] = np.min(D2, axis=1)
    # Output
    return D


# Get distance from a point
def dist_tris_to_pt(X, Y, x, y, **kw):
    r"""Get distance from a point to a collection of triangles

    Points that are inside the triangle return a distance of 0.

    :Call:
        >>> D = dist_tris_to_pt(X, Y, x, y)
    :Inputs:
        *X*: :class:`np.ndarray`\ [:class:`float`]
            *x*-coords of vertices of *n* tris, *shape*: (n,3)
        *Y*: :class:`np.ndarray`\ [:class:`float`], shape=(n,3))
            *y*-coords of vertices of *n* tris, *shape*: (n,3)
        *x*: :class:`float`
            *x*-coordinate of test point
        *y*: :class:`float`
            *y*-coordinate of test point
    :Outputs:
        *D*: :class:`np.ndarray`\ [:class:`float`]
            Matrix of minimum distance from each tri to point
    :Versions:
        * 2017-02-06 ``@ddalle``: Version 1.0
        * 2022-11-01 ``@ddalle``: Version 2.0; faster
    """
    return np.sqrt(dist2_tris_to_pt(X, Y, x, y, **kw))

