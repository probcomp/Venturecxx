CMAKE_MINIMUM_REQUIRED(VERSION 2.8)
PROJECT (Venture)

include_directories("inc" "inc/sps")
add_subdirectory("src" "src/sps")

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
  ADD_DEFINITIONS("-std=c++11" "-Wall" "-g" "-O0" "-fPIC")
ELSE()
  MESSAGE(FATAL_ERROR "CMakeLists.txt has not been tested/written for your compiler.")
ENDIF()

ADD_LIBRARY(trace SHARED
  src/address.cxx 
  src/node.cxx   
  src/exp.cxx

  src/trace.cxx 
  src/rcs.cxx
  src/regen.cxx
  src/detach.cxx
  
  src/flush.cxx

  src/gkernel.cxx
  src/infer.cxx

  src/check.cxx

  src/sp.cxx
  src/scaffold.cxx
  src/sps/csp.cxx
  src/sps/float.cxx
  src/sps/bool.cxx
  src/sps/continuous.cxx
  
  src/wrapper.cxx
)

target_link_libraries(trace
  ${LIBS}
  ${Boost_LIBRARIES}
  ${PYTHON_LIBRARIES}
)

