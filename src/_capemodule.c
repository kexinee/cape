#define PY_SSIZE_T_CLEAN
#include <Python.h>

// Need this to start NumPy C-API
#if PY_MINOR_VERSION >= 10
    #define NPY_NO_DEPRECATED_API NPY_2_0_API_VERSION
#else
    #define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#endif
#define PY_ARRAY_UNIQUE_SYMBOL _cape_ARRAY_API
#include <numpy/arrayobject.h>

// Local includes
#include "capec_NumPy.h"
#include "capec_io.h"
#include "capec_Tri.h"
#include "cape_Tri.h"

static PyMethodDef CapeMethods[] = {
    // pc_Tri methods
    {"WriteTri",     cape_WriteTri,     METH_VARARGS, doc_WriteTri},
    {"WriteCompID",  cape_WriteCompID,  METH_VARARGS, doc_WriteCompID},
    {"WriteTriQ",    cape_WriteTriQ,    METH_VARARGS, doc_WriteTriQ},
    {"WriteSurf",    cape_WriteSurf,    METH_VARARGS, doc_WriteSurf},
    {"WriteTriSTL",  cape_WriteTriSTL,  METH_VARARGS, doc_WriteTriSTL},
    {"WriteTri_b4",  cape_WriteTri_b4,  METH_VARARGS, doc_WriteTri_b4},
    {"WriteTri_lb4", cape_WriteTri_lb4, METH_VARARGS, doc_WriteTri_lb4},
    {"WriteTri_b8",  cape_WriteTri_b8,  METH_VARARGS, doc_WriteTri_b8},
    {"WriteTri_lb8", cape_WriteTri_lb8, METH_VARARGS, doc_WriteTri_lb8},
    {NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3
    static struct PyModuleDef capemodule = {
        PyModuleDef_HEAD_INIT,
        "_cape3",                         // Name of module
        "Extensions for cape module\n",   // Module documentation
        -1,                               // -1 if module keeps state in globals
        CapeMethods
    };

    PyMODINIT_FUNC
    PyInit__cape3(void)
    {
        // This must be called before using the NumPy API.
        import_array();
        // Initialization command
        return PyModule_Create(&capemodule);
    }

#else
    PyMODINIT_FUNC
    init_cape2(void)
    {
        // This must be called before using the NumPy API.
        import_array();
        // Initialization command
        (void) Py_InitModule("_cape2", CapeMethods);
    }

#endif
