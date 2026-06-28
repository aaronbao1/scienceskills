import pytest
from eval.harness.frontmatter import parse_frontmatter, FrontmatterError


def test_parses_metadata_and_body():
    text = "---\nname: foo\ndescription: bar\n---\n# Title\n\nBody.\n"
    meta, body = parse_frontmatter(text)
    assert meta == {"name": "foo", "description": "bar"}
    assert body.startswith("# Title")


def test_missing_frontmatter_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("# No frontmatter here\n")


def test_unterminated_frontmatter_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("---\nname: foo\n")


def test_non_mapping_frontmatter_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("---\n- a\n- b\n---\nbody\n")


def test_handles_crlf_line_endings():
    text = "---\r\nname: foo\r\ndescription: bar\r\n---\r\n# Title\r\n\r\nBody.\r\n"
    meta, body = parse_frontmatter(text)
    assert meta == {"name": "foo", "description": "bar"}
    assert body.startswith("# Title")


def test_strips_exactly_one_leading_newline():
    text = "---\nname: foo\n---\n\n# Title\n"
    _, body = parse_frontmatter(text)
    assert body == "\n# Title\n"
