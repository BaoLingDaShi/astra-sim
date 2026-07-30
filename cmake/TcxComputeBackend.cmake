function(astra_enable_tcx_compute_backend astra_target)
    if(NOT TARGET "${astra_target}")
        message(FATAL_ERROR "ASTRA target '${astra_target}' does not exist")
    endif()

    find_package(TcxComputeBackend 0.1 CONFIG REQUIRED)
    if(NOT TARGET TcxComputeBackend::backend)
        message(FATAL_ERROR
            "TcxComputeBackend package must define TcxComputeBackend::backend")
    endif()

    target_link_libraries("${astra_target}" PUBLIC TcxComputeBackend::backend)
    target_compile_definitions(
        "${astra_target}" PUBLIC ASTRA_ENABLE_TCX_COMPUTE_BACKEND=1)
endfunction()
