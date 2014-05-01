CMAKE_MINIMUM_REQUIRED(VERSION 2.8)
PROJECT (Venture)

include_directories("inc")
add_subdirectory("src")

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake/Modules) 
FIND_PACKAGE(GSL REQUIRED)
include_directories(${GSL_INCLUDE_DIRS} ${GSLCBLAS_INCLUDE_DIRS})
list(APPEND LIBS ${GSL_LIBRARIES} ${GSLCBLAS_LIBRARIES})

find_package(Boost COMPONENTS filesystem system date_time python REQUIRED)
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
	ADD_DEFINITIONS("-std=c++11" "-Wall" "-g" "-O3" "-fPIC")
ELSE()
  MESSAGE(FATAL_ERROR "CMakeLists.txt has not been tested/written for your compiler.")
ENDIF()

ADD_LIBRARY(trace SHARED
    src/value.cxx
    src/node.cxx
    src/env.cxx
    src/builtin.cxx
    src/trace.cxx
    src/rcs.cxx
    src/regen.cxx
    src/detach.cxx
    src/flush.cxx
    src/lkernel.cxx
    src/infer/gkernel.cxx
    src/infer/mh.cxx
    src/infer/gibbs.cxx
    src/infer/pgibbs.cxx
    src/infer/meanfield.cxx
    src/utils.cxx
    src/check.cxx
    src/omegadb.cxx
    src/sp.cxx
    src/spaux.cxx
    src/scaffold.cxx
    src/sps/csp.cxx
    src/sps/mem.cxx
    src/sps/number.cxx
    src/sps/trig.cxx
    #src/sps/real.cxx
    #src/sps/count.cxx
    src/sps/bool.cxx
    src/sps/continuous.cxx
    src/sps/discrete.cxx
    src/sps/cond.cxx
    src/sps/sym.cxx
    src/sps/vector.cxx
	src/sps/matrix.cxx
    src/sps/list.cxx
    src/sps/map.cxx
    src/sps/envs.cxx
    src/sps/eval.cxx
    src/sps/pycrp.cxx
    src/sps/makesymdirmult.cxx
    src/sps/makedirmult.cxx
    src/sps/makebetabernoulli.cxx
    src/sps/makeucsymdirmult.cxx
    src/sps/makelazyhmm.cxx
	src/render.cxx
    src/pytrace.cxx
)

target_link_libraries(trace
  ${LIBS}
  ${Boost_LIBRARIES}
  ${PYTHON_LIBRARIES}
)

add_executable(testEigen src/testEigen.cxx)

add_executable(testMemHash src/testMemHash.cxx)
target_link_libraries(testMemHash
  ${LIBS}
  ${Boost_LIBRARIES}
  ${PYTHON_LIBRARIES}
)
