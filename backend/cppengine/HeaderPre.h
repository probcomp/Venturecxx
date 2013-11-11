
#ifndef VENTURE___HEADER_PRE_H
#define VENTURE___HEADER_PRE_H

#include <Python.h> // Must be the here. See details: http://docs.python.org/2/extending/extending.html.
#include <algorithm>
#include <iostream>
#include <vector>
#include <list>
#include <string>
#include <map>
#include <set>
#include <limits>
#include <queue>
#include <stack>
#include <utility>
#include <fstream>
#include <deque>
#include <iterator>
#include "boost/weak_ptr.hpp"
#include "boost/shared_ptr.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/algorithm/string.hpp"
#include "boost/enable_shared_from_this.hpp"

#ifdef VENTURE__FLAG__COMPILE_WITH_ZMQ
#include "cppzmq/zmq.hpp"
#include <zmq.h>
#endif

#ifdef _MSC_VER
  // Memory leaks control, see here: http://msdn.microsoft.com/en-us/library/x98tx3cf(v=vs.100).aspx
  #define _CRTDBG_MAP_ALLOC
  #include <stdlib.h>
  #include <crtdbg.h>
#endif

using std::vector;
using boost::weak_ptr;
using boost::shared_ptr;
using boost::dynamic_pointer_cast;
using std::string;
using std::list;
using std::set;
using std::map;
using std::queue;
using std::stack;
using std::priority_queue;
using std::pair; using std::make_pair;

// For basic output.
using std::cout;
using std::cin;
using std::endl;

#ifdef VENTURE__FLAG__COMPILE_WITH_ZMQ
using zmq::message_t;
using zmq::context_t;
using zmq::socket_t;
#endif

typedef double real;
const real REAL_MINUS_INFINITY = std::numeric_limits<double>::min();

const real comparison_epsilon = 0.00000001;

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_vector.h>
#include <gsl/gsl_matrix.h>
#include <gsl/gsl_sf_gamma.h>
extern gsl_rng* random_generator;

#include <ctime>

// Using for Windows: http://sourceware.org/pthreads-win32/
// (So requires the pthreadVC2.dll)
#include <pthread.h>

#include <boost/thread.hpp>

// #include "avl_array/avl_array.hpp"
// using namespace mkr;

#ifdef _VENTURE_USE_GOOGLE_PROFILER
#include "google/profiler.h"
#endif

#endif
