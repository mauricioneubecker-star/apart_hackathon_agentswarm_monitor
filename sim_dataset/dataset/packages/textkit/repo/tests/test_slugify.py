from textkit.slugify import slugify


def test_basic_slugs():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("Crème Brûlée Recipes") == "creme-brulee-recipes"
    assert slugify("50% off: Summer Sale") == "50-off-summer-sale"


def test_already_short():
    assert slugify("Hello World", max_length=20) == "hello-world"
