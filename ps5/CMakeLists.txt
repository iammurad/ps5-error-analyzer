cmake_minimum_required(VERSION 3.20)
project(ps5_error_analyzer C)

if(NOT DEFINED PS5_PAYLOAD_SDK)
  message(FATAL_ERROR "Set PS5_PAYLOAD_SDK to the installed PS5 payload SDK")
endif()
if(NOT DEFINED ETAHEN_PLUGINS)
  message(FATAL_ERROR "Set ETAHEN_PLUGINS to an etaHEN-Plugins SDK checkout")
endif()

set(PLUGIN_TITLE_ID "EANL00001")
set(PLUGIN_VERSION "0.20")
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/bin")

add_executable(ps5_error_analyzer source/main.c)
set_target_properties(ps5_error_analyzer PROPERTIES OUTPUT_NAME "ps5_error_analyzer.elf")
target_compile_options(ps5_error_analyzer PRIVATE -fPIC -fPIE -march=znver2 -Wall -Wextra -O2)
target_include_directories(ps5_error_analyzer PRIVATE
  "${PS5_PAYLOAD_SDK}/target/include"
  "${ETAHEN_PLUGINS}/include")
target_link_directories(ps5_error_analyzer PRIVATE
  "${PS5_PAYLOAD_SDK}/target/lib"
  "${ETAHEN_PLUGINS}/lib")
target_link_libraries(ps5_error_analyzer PRIVATE SceLibcInternal)
add_custom_command(TARGET ps5_error_analyzer POST_BUILD
  COMMAND python "${ETAHEN_PLUGINS}/lib/make_plugin.py"
          "$<TARGET_FILE:ps5_error_analyzer>" "${PLUGIN_TITLE_ID}" "${PLUGIN_VERSION}"
  COMMENT "Packaging etaHEN plugin")
