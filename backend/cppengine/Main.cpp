
#include "HeaderPre.h"
#include "Header.h"

#include "VentureValues.h"
#include "VentureParser.h"
#include "Analyzer.h"
#include "Evaluator.h"
#include "XRPCore.h"
#include "XRPs.h"
#include "RIPL.h"
#include "ERPs.h"
#include "Primitives.h"
#include "PythonProxy.h"

int difference_of_CRPs_operations;

/*
   NOTICES:
   1) Booleans should be as NIL!
   2) When some C++ function throws exception,
      we should firstly delete Python objects.
*/

shared_ptr<VentureList> const NIL_INSTANCE = shared_ptr<VentureList>(new VentureNil());
gsl_rng* random_generator = 0;
int VENTURE_GLOBAL__current_random_seed;
set< weak_ptr<NodeXRPApplication> > random_choices;
vector< set< weak_ptr<NodeXRPApplication> >::iterator > random_choices_vector;
size_t DIRECTIVE_COUNTER = 0;

shared_ptr<NodeEnvironment> global_environment;
size_t last_directive_id;
map<size_t, directive_entry> directives;

// unsigned char digits[10][50][28][28];

int continuous_inference_status = 0; // NOT THREAD SAFE!

int next_gensym_atom = 0; // Should become better for the multithread version.
                          // Also check for "limits::max"

bool need_to_return_inference;

void InitGSL() {
  random_generator = gsl_rng_alloc(gsl_rng_mt19937);
  unsigned long seed = static_cast<unsigned long>(time(NULL)); // time(NULL)
  if (false) {
    seed = 1362378859;
    cout << "WARNING: RANDOM SEED is not random!" << endl;
  }
  cout << "Current seed: " << seed << endl;
  gsl_rng_set(random_generator, seed);
  VENTURE_GLOBAL__current_random_seed = seed;
}

void ShowAnnouncement() {
  cout << endl;
  cout << "***********************************************************************" << endl;
  cout << " TESTING AGREEMENT: This is a pre-alpha, testing binary of Venture," << endl;
  cout << " to be used only with express written permission for specific," << endl;
  cout << " pre-agreed purposes; permission can be obtained from Vikash" << endl;
  cout << " Mansinghka (vkm@mit.edu) or Joshua Tenenbaum (jbt@mit.edu)." << endl;
  cout << " Publication of results obtained using Venture is also not" << endl;
  cout << " permitted without written permission." << endl;
  cout << "***********************************************************************" << endl << endl;
}

PyMODINIT_FUNC init_engine(void) {
  ShowAnnouncement();
  InitGSL();
  InitRIPL();
  // PyRun_SimpleString("import os.path"); // FIXME: absolute path.
  // PyRun_SimpleString("from venture.sugars_processor import process_sugars");
  PyRun_SimpleString("import venture.sugars_processor");
  Py_InitModule("_engine", MethodsForPythons);
}

// This one is for the new python stack
PyMODINIT_FUNC init_cpp_engine_extension(void) {
  ShowAnnouncement();
  InitGSL();
  InitRIPL();
  Py_InitModule("_cpp_engine_extension", MethodsForPythons);
} 

int main(int argc, char *argv[])
{
  ShowAnnouncement();
#ifdef _MSC_VER
  _CrtSetDbgFlag ( _CRTDBG_ALLOC_MEM_DF | _CRTDBG_LEAK_CHECK_DF );
#endif
#ifndef NDEBUG
  cout << "Venture is compiled with compiler debug flag" << endl;
#else
  cout << "Venture is compiled without compiler debug flag" << endl;
#endif

  /*
  for (size_t digit_id = 0; digit_id < 5; digit_id++) {
    FILE* fp = fopen(("C:/HWD/data/data" + boost::lexical_cast<string>(digit_id)).c_str(), "rb");
    for (size_t instance_id = 0; instance_id < 100; instance_id++) {
      //cout << "New char:" << endl;
      for (size_t pixel_x = 0; pixel_x < 28; pixel_x++) {
        for (size_t pixel_y = 0; pixel_y < 28; pixel_y++) {
          fscanf(fp, "%c", &digits[digit_id][instance_id][pixel_x][pixel_y]);
          if (digits[digit_id][instance_id][pixel_x][pixel_y] < 20) {
            //cout << " ";
          } else {
            //cout << "*";
          }
          //cout << digits[digit_id][instance_id][pixel_x][pixel_y] / 26;
          //if (digits[digit_id][instance_id][pixel_x][pixel_y] != 0) {
          //  cout << "!!!" << endl;
          //}
        }
        //cout << endl;
      }
      //getchar();
    }
    fclose(fp);
  }
  */

  InitGSL();
  InitRIPL();
  
  // cout << "See why: Or just NULL? does not work!" << endl;
  // cout << "Notice: There should not be the 'NIL' type! Only the 'LIST' type!" << endl;
  
  int port = 8082;
  cout << argv[0] << endl;
  if (argc > 1) {
    port = boost::lexical_cast<int>(argv[1]);
  }

  Py_SetProgramName(argv[0]); // Optional but recommended.
  Py_Initialize();
  Py_InitModule("venture_engine", MethodsForPythons);

  // PyRun_SimpleFile(...) does not work in Release configuration (works in debug).
  // Read here: http://docs.python.org/2/faq/windows.html#pyrun-simplefile-crashes-on-windows-but-not-on-unix-why
  // It seems it is necessary to recompile pythonXY.lib and *.dll.
  // Now using this variant:
//#ifdef _MSC_VER
//  PyRun_SimpleString("execfile(\"C:/Users/Yura Perov/workspace/VentureAlpha/src/RESTPython.py\")");
//#else
  PyRun_SimpleString("import os.path");
  PyRun_SimpleString((string("if os.path.exists(\"RESTPython.py\"):\n") +
                             "  execfile(\"RESTPython.py\")\n" +
                             "elif os.path.exists(\"C:/pcp/20November2012/VentureAlphaOld/SourceCode/Venture/src/RESTPython.py\"):\n" +
                             "  execfile(\"C:/pcp/20November2012/VentureAlphaOld/SourceCode/Venture/src/RESTPython.py\")\n" +
                             "elif os.path.exists(\"/usr/venture/RESTPython.py\"):\n" +
                             "  execfile(\"/usr/venture/RESTPython.py\")\n" +
                             "else:\n" +
                             "  print(\"Cannot find RESTPython.py!\")\n" +
                             "").c_str());
//#endif

  PyRun_SimpleString(("app.run(port=" + boost::lexical_cast<string>(port) + ", host='0.0.0.0')").c_str());

  Py_Finalize();
  return 0;
}
