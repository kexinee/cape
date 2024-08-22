#define PY_SSIZE_T_CLEAN

#include <Python.h>

// This is required to start the NumPy C-API
#define NPY_NO_DEPRECATED_API NPY_2_0_API_VERSION
#define PY_ARRAY_UNIQUE_SYMBOL _cape_ARRAY_API
#include <numpy/arrayobject.h>

#include "capec_NumPy.h"
#include "capec_BaseFile.h"
#include "cape_CSVFile.h"

// Declare each module function
static PyMethodDef FTypesMethods[] = {
    // CSV file utilities
    {
        "CSVFileCountLines",
        cape_CSVFileCountLines,
        METH_VARARGS,
        doc_CSVFileCountLines
    },
    {
        "CSVFileReadData",
        cape_CSVFileReadData,
        METH_VARARGS,
        doc_CSVFileReadData
    },
    // Sentinel
    {NULL, NULL, 0, NULL}
};

// Declare the module
#if PY_MAJOR_VERSION >= 3
    // Descriptions for Python 3 extension
    static struct PyModuleDef ftypesmodule = {
        PyModuleDef_HEAD_INIT,
        "_ftypes3",                        // Name of module
        "CAPE data file types module\n",   // Documentation
        -1,                                // -1 if module keeps state in globals
        FTypesMethods
    };

    // Function to define the module
    PyMODINIT_FUNC
    PyInit__ftypes3(void)
    {
        // The module
        PyObject *m;

        // This must be called before using the NumPy API
        import_array();
        // Initialize module
        m = PyModule_Create(&ftypesmodule);
        // Check for errors
        if (m == NULL)
            return;

        // Add attributes
        capec_AddDTypes(m);
        // Output
        return m;
    }

#else
    // Function to define the module for Python 2
    PyMODINIT_FUNC
    init_ftypes2(void)
    {
        // The module
        PyObject *m;

        // This must be called before using the NumPy API
        import_array();
        // Python 2 module creation
        m = Py_InitModule("_ftypes2", FTypesMethods);
        // Check for errors
        if (m == NULL)
            return;

        // Add attributes
        capec_AddDTypes(m);
    }

#endif
