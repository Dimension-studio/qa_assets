rez env qa_assets dev_env -- ^
    qa check ^
        --check check_normalized_uvs ^
        --check check_polycount ^
        --check asset_info ^
        --asset tests/tmp/test_geo/1.obj ^
        --asset tests/tmp/test_geo/2.bgeo.sc ^
        --asset tests/tmp/test_geo/3.bgeo.sc ^
        --asset tests/tmp/test_geo/4.fbx ^
        --asset tests/tmp/test_geo/missing ^
        --scene tests/tmp/check.hip

rez env check_jsonschema -- ^
    check-jsonschema ^
        --schemafile qa_assets\data\schemas\report_v1.0.schema.json ^
        tests\tmp\test_geo\reports\1.obj.json ^
        tests\tmp\test_geo\reports\2.bgeo.sc.json ^
        tests\tmp\test_geo\reports\3.bgeo.sc.json ^
        tests\tmp\test_geo\reports\4.fbx.json ^
        tests\tmp\test_geo\reports\missing.json
