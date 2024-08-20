#include <Python.h>
#define NPY_NO_DEPRECATED_API NPY_2_0_API_VERSION
#define PY_ARRAY_UNIQUE_SYMBOL _cape_ARRAY_API
#define NO_IMPORT_ARRAY
#include <numpy/arrayobject.h>
#include <stdio.h>
#include <byteswap.h>

// Local includes
#include "capec_NumPy.h"

// Byteswap macros
#define bs32(x) (*(unsigned *)&(x) = __bswap_32(*(unsigned *)&(x)))
#define bs64(x) (*(unsigned long *)&(x) = __bswap_64(*(unsigned long *)&(x)))

// Function to test if system is little-endian
int is_le(void)
{
    int x = 1;
    return *(char*)&x;
}

// Function get size of array (PyArray_SIZE has some issues)
int np_size(PyArrayObject *P)
{
    int j, m, nj;
    int n = 1;
    
    // Get number of dimensions
    m = (int) PyArray_NDIM(P);
    // Loop through dimensions
    for (j=0; j<m; j++) {
        // Multiply the total size
        n *= (int) PyArray_DIM(P, j);
    }
    
    // Output
    return n;
}

// Function to swap a single
float swap_single(const float f)
{
    float v;
    char *F = ( char* ) & f;
    char *V = ( char* ) & v;
    
    // swap the bytes
    V[0] = F[3];
    V[1] = F[2];
    V[2] = F[1];
    V[3] = F[0];
    
    // Output
    return v;
}

// Function to swap a single
double swap_double(const double f)
{
    double v;
    char *F = ( char* ) & f;
    char *V = ( char* ) & v;
    
    // swap the bytes
    V[0] = F[7];
    V[1] = F[6];
    V[2] = F[5];
    V[3] = F[4];
    V[4] = F[3];
    V[5] = F[2];
    V[6] = F[1];
    V[7] = F[0];
    
    // Output
    return v;
}

// ======================================================================
// INDIVIDUAL INTEGERS
// ======================================================================

// Write big-endian, single-precision integer
int capec_Write_b4_i(FILE *fid, int v)
{
    int n;
    int u;
    
    if (is_le()) {
        // Swap the byte-order
        u = __bswap_32(v);
        // Write
        n = fwrite(&u, sizeof(int), 1, fid);
    } else {
        // Write native
        n = fwrite(&v, sizeof(int), 1, fid);
    }
    if (n == 1) {
        return 0;
    } else {
        return 1;
    }
}

// Write little-endian, single-precision integer
int capec_Write_lb4_i(FILE *fid, int v)
{
    int n;
    int u;
    
    if (is_le()) {
        // Write native
        n = fwrite(&v, sizeof(int), 1, fid);
    } else {
        // Swap the byte-order
        u = __bswap_32(v);
        // Write
        n = fwrite(&u, sizeof(int), 1, fid);
    }
    if (n == 1) {
        return 0;
    } else {
        return 1;
    }
}


// ======================================================================
// INDIVIDUAL FLOATS
// ======================================================================

// Write big-endian float
int capec_Write_b4_f(FILE *fid, float v)
{
    int n;
    
    // Byte swap if necessary
    if (is_le()) {
        bs32(v);
    }
    // Write.
    n = fwrite(&v, sizeof(int), 1, fid);
    
    if (n == 1) {
        return 0;
    } else {
        return 1;
    }
}

// Write little-endian float
int capec_Write_lb4_f(FILE *fid, float v)
{
    int n;
    
    // Byte swap if necessary
    if (!is_le()) {bs32(v); }
    // Write.
    n = fwrite(&v, sizeof(int), 1, fid);
    
    if (n == 1) {
        return 0;
    } else {
        return 1;
    }
}


// ======================================================================
// INDIVIDUAL DOUBLES
// ======================================================================

// Write big-endian double
int capec_Write_b4_d(FILE *fid, double v)
{
    int n;
    
    // Byte swap if necessary
    if (is_le()) {bs64(v); }
    // Write.
    n = fwrite(&v, sizeof(int), 1, fid);
    
    if (n == 1) {
        return 0;
    } else {
        return 1;
    }
}

// Write little-endian double
int capec_Write_lb4_d(FILE *fid, double v)
{
    int n;
    
    // Byte swap if necessary
    if (!is_le()) {bs64(v); }
    // Write.
    n = fwrite(&v, sizeof(int), 1, fid);
    
    if (n == 1) {
        return 0;
    } else {
        return 1;
    }
}


// ======================================================================
// 1D INTEGER RECORDS
// ======================================================================

// Write native, single-precision integer record from 1D array
int capec_WriteRecord_ne4_i1(FILE *fid, PyArrayObject *P)
{
    int i;
    int v;
    int n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 1) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 1-D array.");
        return 2;
    }
    // Number of points
    n = (int) PyArray_DIM(P, 0);
    
    // Number of bytes for record marker
    nb = n * sizeof(int);
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through elements
    for (i=0; i<n; i++) {
        // Get value
        v = np1i(P,i);
        fwrite(&v, sizeof(int), 1, fid);
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write byte-swapped, single-precision integer record from 1D array
int capec_WriteRecord_bs4_i1(FILE *fid, PyArrayObject *P)
{
    int i;
    int v;
    int n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 1) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 1-D array.");
        return 2;
    }
    // Number of points
    n = (int) PyArray_DIM(P, 0);
    
    // Number of bytes for record marker
    nb = __bswap_32(n * sizeof(int));
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through elements
    for (i=0; i<n; i++) {
        // Get value
        v = __bswap_32(np1i(P,i));
        fwrite(&v, sizeof(int), 1, fid);
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write big-endian, single-precision integer record from 1D array
int capec_WriteRecord_b4_i1(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_bs4_i1(fid, P);
    } else {
        return capec_WriteRecord_ne4_i1(fid, P);
    }
}

// Write little-endian, single-precision integer record from 1D array
int capec_WriteRecord_lb4_i1(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_ne4_i1(fid, P);
    } else {
        return capec_WriteRecord_bs4_i1(fid, P);
    }
}


// ======================================================================
// 2D INTEGER RECORDS
// ======================================================================

// Write native, single-precision integer record from 2D array
int capec_WriteRecord_ne4_i2(FILE *fid, PyArrayObject *P)
{
    int i, j;
    int v;
    int m, n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 2) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 2-D array.");
        return 2;
    }
    // Number of points
    m = (int) PyArray_DIM(P, 0);
    n = (int) PyArray_DIM(P, 1);
    
    // Number of bytes for record marker
    nb = m * n * sizeof(int);
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (i=0; i<m; i++) {
        // Loop through columns as inner loop
        for (j=0; j<n; j++) {
            // Get value
            v = np2i(P,i,j);
            fwrite(&v, sizeof(int), 1, fid);
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write byte-swapped, single-precision integer record from 2D array
int capec_WriteRecord_bs4_i2(FILE *fid, PyArrayObject *P)
{
    int i, j;
    int v;
    int m, n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 2) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 2-D array.");
        return 2;
    }
    // Number of points
    m = (int) PyArray_DIM(P, 0);
    n = (int) PyArray_DIM(P, 1);
    
    // Number of bytes for record marker
    nb = __bswap_32(m * n * sizeof(int));
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (i=0; i<m; i++) {
        // Loop through columns as inner loop
        for (j=0; j<n; j++) {
            // Get value
            v = __bswap_32(np2i(P,i,j));
            fwrite(&v, sizeof(int), 1, fid);
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write big-endian, single-precision integer record from 2D array
int capec_WriteRecord_b4_i2(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_bs4_i2(fid, P);
    } else {
        return capec_WriteRecord_ne4_i2(fid, P);
    }
}

// Write little-endian, single-precision integer record from 2D array
int capec_WriteRecord_lb4_i2(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_ne4_i2(fid, P);
    } else {
        return capec_WriteRecord_bs4_i2(fid, P);
    }
}


// ======================================================================
// 3D FLOAT RECORDS
// ======================================================================

// Write native, single-precision integer record from 3D array
int capec_WriteRecord_ne4_i3(FILE *fid, PyArrayObject *P)
{
    int j, k, l;
    int v;
    int nj, nk, nl, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 3) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 3-D array.");
        return 2;
    }
    // Number of points
    nj = (int) PyArray_DIM(P, 0);
    nk = (int) PyArray_DIM(P, 1);
    nl = (int) PyArray_DIM(P, 2);
    
    // Number of bytes for record marker
    nb = nj * nk * nl * sizeof(int);
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (j=0; j<nj; j++) {
        // Loop through columns as inner loop
        for (k=0; k<nk; k++) {
            // Loop through third dimension
            for (l=0; l<nl; l++) {
                // Get value
                v = np3i(P,j,k,l);
                fwrite(&v, sizeof(int), 1, fid);
            }
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write byte-swapped, single-precision integer record from 3D array
int capec_WriteRecord_bs4_i3(FILE *fid, PyArrayObject *P)
{
    int j, k, l;
    int v;
    int nj, nk, nl, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 3) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 3-D array.");
        return 2;
    }
    // Number of points
    nj = (int) PyArray_DIM(P, 0);
    nk = (int) PyArray_DIM(P, 1);
    nl = (int) PyArray_DIM(P, 2);
    
    // Number of bytes for record marker
    nb = __bswap_32(nj*nk*nl * sizeof(int));
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (j=0; j<nj; j++) {
        // Loop through columns as inner loop
        for (k=0; k<nk; k++) {
            // Loop through third dimension
            for (l=0; l<nl; l++) {
                // Get value
                v = __bswap_32(np3i(P,j,k,l));
                fwrite(&v, sizeof(int), 1, fid);
            }
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write big-endian, single-precision float record from 3D array
int capec_WriteRecord_b4_i3(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_bs4_i3(fid, P);
    } else {
        return capec_WriteRecord_ne4_i3(fid, P);
    }
}

// Write little-endian, single-precision float record from 3D array
int capec_WriteRecord_lb4_i3(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_ne4_i3(fid, P);
    } else {
        return capec_WriteRecord_bs4_i3(fid, P);
    }
}


// ======================================================================
// 1D FLOAT RECORDS
// ======================================================================

// Write native, single-precision float record from 1D array
int capec_WriteRecord_ne4_f1(FILE *fid, PyArrayObject *P)
{
    int i;
    float v;
    int n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 1) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 1-D array.");
        return 2;
    }
    // Number of points
    n = (int) PyArray_DIM(P, 0);
    
    // Number of bytes for record marker
    nb = n * sizeof(float);
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through elements
    for (i=0; i<n; i++) {
        // Get value
        v = np1d(P,i);
        fwrite(&v, sizeof(float), 1, fid);
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write byte-swapped, single-precision float record from 1D array
int capec_WriteRecord_bs4_f1(FILE *fid, PyArrayObject *P)
{
    int i;
    float v;
    int n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 1) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 1-D array.");
        return 2;
    }
    // Number of points
    n = (int) PyArray_DIM(P, 0);
    
    // Number of bytes for record marker
    nb = __bswap_32(n * sizeof(float));
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through elements
    for (i=0; i<n; i++) {
        // Get value
        v = (float) np1d(P,i); bs32(v);
        fwrite(&v, sizeof(float), 1, fid);
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write big-endian, single-precision float record from 1D array
int capec_WriteRecord_b4_f1(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_bs4_f1(fid, P);
    } else {
        return capec_WriteRecord_ne4_f1(fid, P);
    }
}

// Write little-endian, single-precision float record from 1D array
int capec_WriteRecord_lb4_f1(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_ne4_f1(fid, P);
    } else {
        return capec_WriteRecord_bs4_f1(fid, P);
    }
}


// ======================================================================
// 2D FLOAT RECORDS
// ======================================================================

// Write native, single-precision float record from 2D array
int capec_WriteRecord_ne4_f2(FILE *fid, PyArrayObject *P)
{
    int i, j;
    float v;
    int m, n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 2) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 2-D array.");
        return 2;
    }
    // Number of points
    m = (int) PyArray_DIM(P, 0);
    n = (int) PyArray_DIM(P, 1);
    
    // Number of bytes for record marker
    nb = m * n * sizeof(float);
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (i=0; i<m; i++) {
        // Loop through columns as inner loop
        for (j=0; j<n; j++) {
            // Get value
            v = np2d(P,i,j);
            fwrite(&v, sizeof(int), 1, fid);
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write byte-swapped, single-precision float record from 2D array
int capec_WriteRecord_bs4_f2(FILE *fid, PyArrayObject *P)
{
    int i, j;
    float v;
    int m, n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 2) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 2-D array.");
        return 2;
    }
    // Number of points
    m = (int) PyArray_DIM(P, 0);
    n = (int) PyArray_DIM(P, 1);
    
    // Number of bytes for record marker
    nb = __bswap_32(m * n * sizeof(float));
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (i=0; i<m; i++) {
        // Loop through columns as inner loop
        for (j=0; j<n; j++) {
            // Get value
            v = (float) np2d(P,i,j);
            bs32(v);
            fwrite(&v, sizeof(float), 1, fid);
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write big-endian, single-precision float record from 2D array
int capec_WriteRecord_b4_f2(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_bs4_f2(fid, P);
    } else {
        return capec_WriteRecord_ne4_f2(fid, P);
    }
}

// Write little-endian, single-precision float record from 2D array
int capec_WriteRecord_lb4_f2(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_ne4_f2(fid, P);
    } else {
        return capec_WriteRecord_bs4_f2(fid, P);
    }
}


// ======================================================================
// 3D FLOAT RECORDS
// ======================================================================

// Write native, single-precision float record from 3D array
int capec_WriteRecord_ne4_f3(FILE *fid, PyArrayObject *P)
{
    int j, k, l;
    float v;
    int nj, nk, nl, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 3) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 3-D array.");
        return 2;
    }
    // Number of points
    nj = (int) PyArray_DIM(P, 0);
    nk = (int) PyArray_DIM(P, 1);
    nl = (int) PyArray_DIM(P, 2);
    
    // Number of bytes for record marker
    nb = nj * nk * nl * sizeof(float);
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (j=0; j<nj; j++) {
        // Loop through columns as inner loop
        for (k=0; k<nk; k++) {
            // Loop through third dimension
            for (l=0; l<nl; l++) {
                // Get value
                v = np3d(P,j,k,l);
                fwrite(&v, sizeof(float), 1, fid);
            }
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write byte-swapped, single-precision float record from 3D array
int capec_WriteRecord_bs4_f3(FILE *fid, PyArrayObject *P)
{
    int j, k, l;
    float v;
    int nj, nk, nl, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 3) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 3-D array.");
        return 2;
    }
    // Number of points
    nj = (int) PyArray_DIM(P, 0);
    nk = (int) PyArray_DIM(P, 1);
    nl = (int) PyArray_DIM(P, 2);
    
    // Number of bytes for record marker
    nb = __bswap_32(nj*nk*nl * sizeof(float));
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (j=0; j<nj; j++) {
        // Loop through columns as inner loop
        for (k=0; k<nk; k++) {
            // Loop through third dimension
            for (l=0; l<nl; l++) {
                // Get value
                v = (float) np3d(P,j,k,l); bs32(v);
                fwrite(&v, sizeof(float), 1, fid);
            }
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write big-endian, single-precision float record from 3D array
int capec_WriteRecord_b4_f3(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_bs4_f3(fid, P);
    } else {
        return capec_WriteRecord_ne4_f3(fid, P);
    }
}

// Write little-endian, single-precision float record from 3D array
int capec_WriteRecord_lb4_f3(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_ne4_f3(fid, P);
    } else {
        return capec_WriteRecord_bs4_f3(fid, P);
    }
}


// ======================================================================
// 1D DOUBLE RECORDS
// ======================================================================

// Write native, single-precision float record from 1D array
int capec_WriteRecord_ne8_f1(FILE *fid, PyArrayObject *P)
{
    int i;
    double v;
    int n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 1) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 1-D array.");
        return 2;
    }
    // Number of points
    n = (int) PyArray_DIM(P, 0);
    
    // Number of bytes for record marker
    nb = n * sizeof(double);
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through elements
    for (i=0; i<n; i++) {
        // Get value
        v = np1d(P,i);
        fwrite(&v, sizeof(double), 1, fid);
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write byte-swapped, single-precision float record from 1D array
int capec_WriteRecord_bs8_f1(FILE *fid, PyArrayObject *P)
{
    int i;
    double v;
    int n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 1) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 1-D array.");
        return 2;
    }
    // Number of points
    n = (int) PyArray_DIM(P, 0);
    
    // Number of bytes for record marker
    nb = __bswap_32(n * sizeof(double));
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through elements
    for (i=0; i<n; i++) {
        // Get value
        v = np1d(P,i);
        bs64(v);
        fwrite(&v, sizeof(double), 1, fid);
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write big-endian, single-precision float record from 1D array
int capec_WriteRecord_b8_f1(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_bs8_f1(fid, P);
    } else {
        return capec_WriteRecord_ne8_f1(fid, P);
    }
}

// Write little-endian, single-precision float record from 1D array
int capec_WriteRecord_lb8_f1(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_ne8_f1(fid, P);
    } else {
        return capec_WriteRecord_bs8_f1(fid, P);
    }
}


// ======================================================================
// 2D DOUBLE RECORDS
// ======================================================================

// Write native, double-precision float record from 2D array
int capec_WriteRecord_ne8_f2(FILE *fid, PyArrayObject *P)
{
    int i, j;
    double v;
    int m, n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 2) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 2-D array.");
        return 2;
    }
    // Number of points
    m = (int) PyArray_DIM(P, 0);
    n = (int) PyArray_DIM(P, 1);
    
    // Number of bytes for record marker
    nb = m * n * sizeof(double);
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (i=0; i<m; i++) {
        // Loop through columns as inner loop
        for (j=0; j<n; j++) {
            // Get value
            v = np2d(P,i,j);
            fwrite(&v, sizeof(double), 1, fid);
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write byte-swapped, double-precision float record from 2D array
int capec_WriteRecord_bs8_f2(FILE *fid, PyArrayObject *P)
{
    int i, j;
    double v;
    int m, n, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 2) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 2-D array.");
        return 2;
    }
    // Number of points
    m = (int) PyArray_DIM(P, 0);
    n = (int) PyArray_DIM(P, 1);
    
    // Number of bytes for record marker
    nb = __bswap_32(m * n * sizeof(double));
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (i=0; i<m; i++) {
        // Loop through columns as inner loop
        for (j=0; j<n; j++) {
            // Get value
            v = np2d(P,i,j);
            bs64(v);
            fwrite(&v, sizeof(double), 1, fid);
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write big-endian, double-precision float record from 2D array
int capec_WriteRecord_b8_f2(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_bs8_f2(fid, P);
    } else {
        return capec_WriteRecord_ne8_f2(fid, P);
    }
}

// Write little-endian, double-precision float record from 2D array
int capec_WriteRecord_lb8_f2(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_ne8_f2(fid, P);
    } else {
        return capec_WriteRecord_bs8_f2(fid, P);
    }
}


// ======================================================================
// 3D DOUBLE RECORDS
// ======================================================================

// Write native, single-precision float record from 3D array
int capec_WriteRecord_ne8_f3(FILE *fid, PyArrayObject *P)
{
    int j, k, l;
    double v;
    int nj, nk, nl, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 3) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 3-D array.");
        return 2;
    }
    // Number of points
    nj = (int) PyArray_DIM(P, 0);
    nk = (int) PyArray_DIM(P, 1);
    nl = (int) PyArray_DIM(P, 2);
    
    // Number of bytes for record marker
    nb = nj * nk * nl * sizeof(double);
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (j=0; j<nj; j++) {
        // Loop through columns as inner loop
        for (k=0; k<nk; k++) {
            // Loop through third dimension
            for (l=0; l<nl; l++) {
                // Get value
                v = np3d(P,j,k,l);
                fwrite(&v, sizeof(double), 1, fid);
            }
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write byte-swapped, single-precision float record from 3D array
int capec_WriteRecord_bs8_f3(FILE *fid, PyArrayObject *P)
{
    int j, k, l;
    double v;
    int nj, nk, nl, nb;
    
    // Check dims
    if (PyArray_NDIM(P) != 3) {
        PyErr_SetString(PyExc_ValueError, "Object must be a 3-D array.");
        return 2;
    }
    // Number of points
    nj = (int) PyArray_DIM(P, 0);
    nk = (int) PyArray_DIM(P, 1);
    nl = (int) PyArray_DIM(P, 2);
    
    // Number of bytes for record marker
    nb = __bswap_32(nj*nk*nl * sizeof(double));
    // Record marker
    fwrite(&nb, sizeof(int), 1, fid);
    
    // Loop through rows as outer loop
    for (j=0; j<nj; j++) {
        // Loop through columns as inner loop
        for (k=0; k<nk; k++) {
            // Loop through third dimension
            for (l=0; l<nl; l++) {
                // Get value
                v = np3d(P,j,k,l); bs64(v);
                fwrite(&v, sizeof(double), 1, fid);
            }
        }
    }
    // End-of-record marker
    fwrite(&nb, sizeof(int), 1, fid);
    // Success
    return 0;
}

// Write big-endian, single-precision float record from 3D array
int capec_WriteRecord_b8_f3(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_bs4_f3(fid, P);
    } else {
        return capec_WriteRecord_ne4_f3(fid, P);
    }
}

// Write little-endian, single-precision float record from 3D array
int capec_WriteRecord_lb8_f3(FILE *fid, PyArrayObject *P)
{
    if (is_le()) {
        return capec_WriteRecord_ne4_f3(fid, P);
    } else {
        return capec_WriteRecord_bs4_f3(fid, P);
    }
}

    