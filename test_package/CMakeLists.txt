project( CurlConanPackageTest )
cmake_minimum_required( VERSION  3.0 )
include( "${CMAKE_BINARY_DIR}/conanbuildinfo.cmake" )
conan_basic_setup( TARGETS )

add_executable( CurlPackageTest
    main.c
)
target_link_libraries( CurlPackageTest
    PRIVATE  CONAN_PKG::curl
)
