#ifndef DEBUG_H
#define DEBUG_H

#include <iostream>

//#define ADEBUG
#ifdef ADEBUG 
#define APRINT(x,y) do { cerr << x << y << endl; } while (0)
#else 
#define APRINT(x,y)
#endif

//#define BDEBUG
#ifdef BDEBUG 
#define BPRINT(x,y) do { cerr << x << y << endl; } while (0)
#else 
#define BPRINT(x,y)
#endif

//#define CDEBUG
#ifdef CDEBUG 
#define CPRINT(x,y) do { cerr << x << y << endl; } while (0)
#else 
#define CPRINT(x,y)
#endif

/* For regen/detach */
//#define DDEBUG
#ifdef DDEBUG 
#define DPRINT(x,y) do { cerr << x << y << endl; } while (0)
#else 
#define DPRINT(x,y)
#endif

/* For flushing */
//#define FDEBUG
#ifdef FDEBUG 
#define FPRINT(x,y) do { cerr << x << y << endl; } while (0)
#else 
#define FPRINT(x,y)
#endif

/* For Scaffold */
//#define SDEBUG
#ifdef SDEBUG 
#define SPRINT(x,y) do { cerr << x << y << endl; } while (0)
#else 
#define SPRINT(x,y)
#endif

/* For LKernels */
//#define LDEBUG
#ifdef LDEBUG 
#define LPRINT(x,y) do { cerr << x << y << endl; } while (0)
#else 
#define LPRINT(x,y)
#endif

/* For Warnings */
//#define WDEBUG
#ifdef WDEBUG 
#define WPRINT(x,y) do { cerr << x << y << endl; } while (0)
#else 
#define WPRINT(x,y)
#endif


#endif
