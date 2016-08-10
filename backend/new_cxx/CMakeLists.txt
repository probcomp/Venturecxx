CMAKE_MINIMUM_REQUIRED(VERSION 2.8)
PROJECT (Venture)

include_directories("inc")
add_subdirectory("src")


IF("${CMAKE_SYSTEM_NAME}" STREQUAL "Darwin")
set(CMAKE_PREFIX_PATH /opt/local ${CMAKE_PREFIX_PATH})
ENDIF()

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake/Modules) 
FIND_PACKAGE(GSL REQUIRED)
include_directories(${GSL_INCLUDE_DIRS} ${GSLCBLAS_INCLUDE_DIRS})
list(APPEND LIBS ${GSL_LIBRARIES} ${GSLCBLAS_LIBRARIES})

ADD_DEFINITIONS(-DBoost_USE_STATIC_LIBS=ON)
set(Boost_USE_STATIC_LIBS   ON)
set(Boost_USE_MULTITHREADED ON)
find_package(Boost COMPONENTS filesystem system date_time python thread REQUIRED)
message("Include dirs of boost: " ${Boost_INCLUDE_DIRS} )
message("Libs of boost: " ${Boost_LIBRARIES} )

find_package(PythonLibs REQUIRED)
message("Include dirs of Python: " ${PYTHON_INCLUDE_DIRS} )
message("Libs of Python: " ${PYTHON_LIBRARIES} )

include_directories(
  "inc"
  "inc/sps"
  ${Boost_INCLUDE_DIRS}
  ${PYTHON_INCLUDE_DIRS}
)


message(STATUS ${LIBS})

IF(CMAKE_COMPILER_IS_GNUCXX)
  message("Found g++ version " ${CMAKE_CXX_COMPILER_VERSION})
#  IF(CMAKE_CXX_COMPILER_VERSION VERSION_LESS 4.8)
#    MESSAGE(FATAL_ERROR "g++ version 4.8 is required!")
#  ENDIF()
  ADD_DEFINITIONS("-std=c++11" "-Wall" "-g" "-O0" "-fPIC")
ELSE("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
	message("Found clang++ version" ${CMAKE_CXX_COMPILER_VERSION})
	ADD_DEFINITIONS("-std=c++11" "-Wall" "-g" "-O3" "-fPIC" "-Wno-deprecated-register" "-Wno-overloaded-virtual")
ELSE()
  MESSAGE(FATAL_ERROR "CMakeLists.txt has not been tested/written for your compiler.")
ENDIF()

ADD_LIBRARY(trace SHARED
    src/pyutils.cxx
    src/args.cxx
    src/value.cxx
    src/values.cxx
    src/node.cxx
    src/env.cxx
    src/concrete_trace.cxx
    src/builtin.cxx
    src/trace.cxx
    src/regen.cxx
    src/detach.cxx
    src/lkernel.cxx
    src/utils.cxx
    src/db.cxx
    src/sp.cxx
    src/sprecord.cxx
    src/scaffold.cxx
    src/sps/csp.cxx
    src/sps/betabernoulli.cxx
    src/sps/conditional.cxx
    src/sps/continuous.cxx
    src/sps/crp.cxx
    src/sps/csp.cxx
    src/sps/deterministic.cxx
    src/sps/dir_mult.cxx
    src/sps/discrete.cxx
    src/sps/dstructure.cxx
    src/sps/hmm.cxx
    src/sps/eval.cxx
    src/sps/matrix.cxx
    src/sps/misc.cxx
    src/sps/msp.cxx
    src/sps/numerical_helpers.cxx
    src/sps/scope.cxx
    src/gkernels/egibbs.cxx
    src/gkernels/func_mh.cxx
    src/gkernels/mh.cxx
    src/gkernels/pgibbs.cxx
    src/gkernels/slice.cxx
    src/gkernels/hmc.cxx
    src/expressions.cxx
    src/gkernel.cxx
    src/indexer.cxx
    src/mixmh.cxx
    src/particle.cxx
    src/psp.cxx
    src/consistency.cxx
    src/pytrace.cxx
)

target_link_libraries(trace
  ${LIBS}
  ${Boost_LIBRARIES}
  ${PYTHON_LIBRARIES}
)

add_executable(testPMap src/test_pmap.cxx)

target_link_libraries(testPMap
  ${LIBS}
  ${Boost_LIBRARIES}
  ${PYTHON_LIBRARIES}
)

IF("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")

add_custom_command ( OUTPUT stdout.txt
					COMMAND mv libpumatrace.dylib libpumatrace.so 
					WORKING_DIRECTORY ${CMAKE_SOURCE_DIR} )

ENDIF()
