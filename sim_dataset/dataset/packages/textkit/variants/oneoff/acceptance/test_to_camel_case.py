from textkit.to_camel_case import to_camel_case


def test_from_other_conventions():
    assert to_camel_case("Content-Type") == "contentType"
    assert to_camel_case("MAX_RETRY_COUNT") == "maxretrycount"
    assert to_camel_case("xml http request", upper_first=True) == "XmlHttpRequest"


def test_leading_digits():
    assert to_camel_case("3d_model") == "_3dModel"
    assert to_camel_case("2fa-enabled", upper_first=True) == "_2faEnabled"
