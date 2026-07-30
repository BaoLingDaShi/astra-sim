cmake_minimum_required(VERSION 3.22)
project(TcxComputeBackend VERSION 0.1.0 LANGUAGES CXX)

include(CMakePackageConfigHelpers)
include(GNUInstallDirs)

add_library(tcx_fake_compute_backend STATIC src/tcx_fake_compute_backend.cc)
add_library(TcxComputeBackend::backend ALIAS tcx_fake_compute_backend)
target_include_directories(
    tcx_fake_compute_backend
    PUBLIC
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>"
)
set_target_properties(
    tcx_fake_compute_backend
    PROPERTIES EXPORT_NAME backend
)

install(
    TARGETS tcx_fake_compute_backend
    EXPORT TcxComputeBackendTargets
    ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}"
)
install(
    DIRECTORY include/
    DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
)
install(
    EXPORT TcxComputeBackendTargets
    NAMESPACE TcxComputeBackend::
    DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/TcxComputeBackend"
)

configure_package_config_file(
    cmake/TcxComputeBackendConfig.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/TcxComputeBackendConfig.cmake"
    INSTALL_DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/TcxComputeBackend"
)
write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/TcxComputeBackendConfigVersion.cmake"
    VERSION "${PROJECT_VERSION}"
    COMPATIBILITY SameMajorVersion
)
install(
    FILES
        "${CMAKE_CURRENT_BINARY_DIR}/TcxComputeBackendConfig.cmake"
        "${CMAKE_CURRENT_BINARY_DIR}/TcxComputeBackendConfigVersion.cmake"
    DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/TcxComputeBackend"
)
