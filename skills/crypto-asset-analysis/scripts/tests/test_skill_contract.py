"""Contract tests for the skill packaging.

Mirrors the convention used by us-stock-analysis: the frontmatter must identify
the skill, every referenced file must exist and be linked from SKILL.md, and the
prompt contract must still describe the workflow the scripts implement.

The extra checks here guard the two claims this skill makes that would be
actively harmful if they drifted out of the documentation: that on-chain data is
Bitcoin-only, and that the script produces no rating of its own.
"""

from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parents[2]
SKILL_MD = SKILL_DIR / "SKILL.md"
EXPECTED_REFERENCES = (
    "references/crypto-fundamentals.md",
    "references/onchain-metrics.md",
    "references/derivatives-positioning.md",
    "references/report-template.md",
)


def _skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def _frontmatter() -> dict:
    text = _skill_text()
    assert text.startswith("---\n")
    _prefix, raw_yaml, _body = text.split("---", 2)
    metadata = yaml.safe_load(raw_yaml)
    assert isinstance(metadata, dict)
    return metadata


def test_frontmatter_identifies_crypto_asset_analysis_skill() -> None:
    metadata = _frontmatter()

    assert metadata["name"] == "crypto-asset-analysis"
    assert "crypto asset analysis" in metadata["description"].lower()
    assert "counter-argument" in metadata["description"]


def test_required_references_are_present_and_named() -> None:
    text = _skill_text()

    for rel_path in EXPECTED_REFERENCES:
        assert (SKILL_DIR / rel_path).is_file()
        assert rel_path in text


def test_scripts_are_present() -> None:
    for name in ("crypto_asset_analysis.py", "data_sources.py", "metrics.py"):
        assert (SKILL_DIR / "scripts" / name).is_file()


def test_prompt_contract_documents_the_workflow() -> None:
    text = _skill_text()

    assert "Run the quantitative core" in text
    assert "Research narrative and catalysts by WebSearch" in text
    assert "Synthesise into a rating" in text


def test_onchain_limitation_is_documented_not_buried() -> None:
    # The skill analyses four dimensions for altcoins and six for BTC. If that
    # ever stops being stated, altcoin reports start reading as complete.
    text = _skill_text()

    assert "BTC only" in text
    assert "On-chain data covers Bitcoin only" in text


def test_script_disclaims_producing_a_rating() -> None:
    # The rating is Claude's synthesis. If the script ever starts emitting one,
    # this documented split has silently broken.
    text = _skill_text()

    assert "produces **no rating**" in text


def test_free_and_keyless_claim_is_stated() -> None:
    assert "keyless" in _skill_text()
