idf_component_register(SRCS "bt_app_av.c" "bt_app_core.c" "main.c"
                    INCLUDE_DIRS "." "../components/fft/include" "../components/md_max72xx/include")
idf_build_set_property(COMPILE_OPTIONS "-DARCH_ESP32" APPEND)