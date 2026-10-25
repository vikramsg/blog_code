from hn_hiring_trends.classify import classify


def test_four_advertised_roles_can_overlap_without_being_mutually_exclusive():
    result = classify("Acme | Frontend Engineer, Backend Engineer, Full Stack Product Engineer | Remote")
    assert set(result["role_families"]) == {"frontend", "backend", "full_stack", "product"}


def test_separate_specialist_openings_do_not_establish_a_fullstack_position():
    result = classify("Acme | Frontend Engineer and Backend Engineer | Remote")
    assert set(result["role_families"]) == {"frontend", "backend"}


def test_ordinary_product_work_is_not_an_advertised_product_engineer_role():
    result = classify(
        "Acme | Backend Engineer | Remote\nYou will build product APIs and work with product managers."
    )
    assert "backend" in result["role_families"]
    assert "product" not in result["role_families"]


def test_explicit_product_role_description_is_not_limited_to_the_header_title():
    result = classify(
        "Acme | Software Engineer | Remote\nWe're hiring engineers. We view each engineer as a true product engineer."
    )
    assert "product" in result["role_families"]


def test_non_hiring_background_does_not_change_advertised_role_measurements():
    advertisement = "Acme | Backend Engineer | Remote"
    baseline = classify(advertisement)
    background = classify(advertisement + "\nOur product serves frontend developers and product engineers.")
    assert set(background["role_families"]) == set(baseline["role_families"])


def test_each_detected_role_has_source_locatable_evidence_and_a_detection_reason():
    text = "Acme | Frontend Engineer, Backend Engineer, Full Stack Product Engineer | Remote"
    result = classify(text)
    assert result["role_families"]
    for role in result["role_families"]:
        assert result["match_reasons"][role]
        assert result["evidence"][role]
        assert all(excerpt in text for excerpt in result["evidence"][role])


def test_separate_product_design_opening_is_not_an_engineering_specialty_suffix():
    result = classify("Acme | Backend Engineer, Product Design | Remote")
    assert "backend" in result["role_families"]
    assert "product" not in result["role_families"]


def test_company_role_definition_is_independent_of_its_order_relative_to_recruitment():
    heading = "Acme | Remote | Full-time\n"
    identity = "Our engineers are true product engineers.\n"
    recruitment = "We are hiring backend engineers.\n"
    before = classify(heading + identity + recruitment)
    after = classify(heading + recruitment + identity)
    assert "product" in before["role_families"]
    assert set(before["role_families"]) == set(after["role_families"])


def test_vacancy_link_does_not_override_explicit_negative_product_recruitment():
    result = classify(
        "Acme | Backend Engineer | Remote\nWe are not hiring product engineers; see https://example.com/jobs/product-engineer"
    )
    assert "product" not in result["role_families"]
