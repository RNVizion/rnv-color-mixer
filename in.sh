QT_OPA_PLATFORM=offscreen 
python -m pytest test_rnv_color_mixer.py -q --deselect "test_rnv_color_mixer.py: :TestImageHandler::test_load_real_image_if_available"
QT_OPA_PLATFORM=offscreen 
python -m pytest tests/ -q --deselect tests/test_error_recovery_paths.py:: TestAsyncFileOpsErrorPaths