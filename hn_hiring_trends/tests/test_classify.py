import pytest

from hn_hiring_trends.classify import classify


def test_non_hiring_background_does_not_change_advertised_role_measurements():
    advertisement = "Acme | Backend Engineer | Remote"
    baseline = classify(advertisement)
    with_background = classify(
        advertisement
        + "\nOur product serves frontend developers and data scientists. It uses React on the frontend."
    )
    assert set(with_background["role_families"]) == set(baseline["role_families"])
    assert with_background["engineering_ad"] == baseline["engineering_ad"]
    assert with_background["signals"]["technical_breadth"] == baseline["signals"]["technical_breadth"]


def test_separate_specialist_openings_and_a_fullstack_position_measure_different_breadth():
    specialists = classify("Acme | Frontend Engineer and Backend Engineer | Remote")
    fullstack = classify("Acme | Full Stack Engineer | Remote")
    assert set(specialists["role_families"]) == {"frontend", "backend"}
    assert not specialists["signals"]["technical_breadth"]
    assert "full_stack" in fullstack["role_families"]
    assert fullstack["signals"]["technical_breadth"]


def test_product_title_and_product_responsibilities_are_independent_measurements():
    advertisement = "Acme | Product Engineer | Remote"
    title_only = classify(advertisement)
    with_duties = classify(advertisement + "\nYou will talk to customers and own the product roadmap.")
    assert title_only["signals"]["product_engineer_title"]
    assert not title_only["signals"]["product_responsibility"]
    assert with_duties["signals"]["product_engineer_title"]
    assert with_duties["signals"]["product_responsibility"]


@pytest.mark.parametrize(
    ("duties", "ai_product_work", "ai_tool_use"),
    [
        ("You will build our billing service.", False, False),
        ("You will build LLM applications for customers.", True, False),
        ("You will use Cursor to develop our billing service.", False, True),
        ("You will build LLM applications.\nUse Cursor in your daily coding.", True, True),
    ],
)
def test_ai_product_work_and_assistant_use_can_vary_independently(duties, ai_product_work, ai_tool_use):
    result = classify(f"Acme | Software Engineer | Remote\n{duties}")
    assert result["signals"]["ai_product_work"] is ai_product_work
    assert result["signals"]["ai_tool_use"] is ai_tool_use


def test_positive_measurements_have_evidence_locatable_in_the_advertisement():
    text = (
        "Acme | Full Stack Product Engineer | Remote\n"
        "You will talk to customers and build LLM applications.\nUse Cursor in your daily coding."
    )
    result = classify(text)
    positive_labels = set(result["role_families"]) | {
        name for name, positive in result["signals"].items() if positive
    }
    assert positive_labels
    for label in positive_labels:
        assert result["evidence"][label]
        assert all(excerpt in text for excerpt in result["evidence"][label])


def test_explicit_negation_changes_the_corresponding_responsibility_measurement():
    advertisement = "Acme | Backend Engineer | Remote\n"
    required = classify(advertisement + "You will talk to customers.")
    excluded = classify(advertisement + "You will not talk to customers.")
    assert required["signals"]["customer_contact"]
    assert not excluded["signals"]["customer_contact"]
    assert set(required["role_families"]) == set(excluded["role_families"])
