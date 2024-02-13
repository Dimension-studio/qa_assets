rez env qa_assets dev_env -- qa check ^
        --check check_normalized_uvs ^
        --check check_polycount ^
        --check asset_info ^
        --asset tests/tmp/test_geo/1.obj ^
        --asset tests/tmp/test_geo/2.bgeo.sc ^
        --asset tests/tmp/test_geo/3.bgeo.sc ^
        --asset tests/tmp/test_geo/4.fbx ^
        --asset tests/tmp/test_geo/missing ^
        --scene tests/tmp/check.hip
