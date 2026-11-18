import pytest

from manimate.tex import normalize_tex, tex_to_plain


@pytest.mark.parametrize("raw, fixed", [
    (r"/sigma^2", r"\sigma^2"),
    (r"x = /exp(-t)", r"x = \exp(-t)"),
    (r"y = //frac{a}{b}", r"y = \frac{a}{b}"),
    (r"\\sigma + \\alpha", r"\sigma + \alpha"),
    ("\x0crac{1}{2}", r"\frac{1}{2}"),            # JSON turned \f into a form feed
    ("\\sin\\theta + \x08eta", r"\sin\theta + \beta"),
    (r"N_s = \frac{120\,f}{P}", r"N_s = \frac{120\,f}{P}"),  # already right: unchanged
    (r"a/sigma", r"a/sigma"),                      # a division, not a command
    (r"$E = mc^2$", r"E = mc^2"),
])
def test_normalize_tex(raw, fixed):
    assert normalize_tex(raw) == fixed



@pytest.mark.parametrize(
    "raw",
    [
        r"\text{breaths /min}",
        r"\mathrm{speed /min}",
        r"\textbf{rate /min}",
    ],
)
def test_normalize_tex_preserves_text_mode_spans(raw):
    assert normalize_tex(raw) == raw


def test_normalize_tex_repairs_commands_outside_text_mode():
    assert normalize_tex(r"\text{breaths /min} + /sigma") == (
        r"\text{breaths /min} + \sigma"
    )


def test_normalize_tex_preserves_nested_text_mode_content():
    raw = r"\text{rate {per /min}} + //frac{1}{2}"
    expected = r"\text{rate {per /min}} + \frac{1}{2}"

    assert normalize_tex(raw) == expected


def test_normalize_is_idempotent():
    once = normalize_tex(r"/sigma = //frac{1}{2}")
    assert normalize_tex(once) == once


@pytest.mark.parametrize("raw, plain", [
    (r"/sigma", "σ"),
    (r"\exp(-t)", "exp(-t)"),                       # no stray backslash or slash
    (r"\sum_{i=1}^{n} x_i", "Σ_i=1^(n) x_i"),
    (r"\frac{V_{in}}{R}", "(V_in)/(R)"),
    (r"\text{rate} \times \pi", "rate × π"),
])
def test_plain_text_never_shows_command_names(raw, plain):
    assert tex_to_plain(raw) == plain
    assert "\\" not in tex_to_plain(raw)
