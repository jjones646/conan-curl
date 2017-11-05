# CURL_INCLUDE_DIRS   - where to find curl/curl.h, etc.
# CURL_LIBRARIES      - List of libraries when using curl.
# CURL_FOUND          - True if curl found.
# CURL_VERSION_STRING - the version of curl found (since CMake 2.8.8)

find_path(CURL_INCLUDE_DIR NAMES curl/curl.h PATHS ${CONAN_INCLUDE_DIRS_LIBCURL})
find_library(CURL_LIBRARY NAMES ${CONAN_LIBS_LIBCURL} PATHS ${CONAN_LIB_DIRS_LIBCURL})

set(CURL_FOUND TRUE)
set(CURL_INCLUDE_DIRS ${CURL_INCLUDE_DIR})
set(CURL_LIBRARIES ${CURL_LIBRARY})
set(CURL_VERSION_STRING "7.56.1")

message("** LIBCURL ALREADY FOUND BY CONAN!")
message("** FOUND CURL:  ${CURL_LIBRARIES} ${CURL_VERSION_STRING}")
message("** FOUND ZLIB INCLUDE:  ${CURL_INCLUDE_DIRS}")

mark_as_advanced(CURL_LIBRARIES CURL_LIBRARY CURL_INCLUDE_DIRS CURL_INCLUDE_DIR)
