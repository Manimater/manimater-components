"""LaTeX hygiene: repair what small models and JSON round-trips do to formulas, and a readable fallback.

Typical damage this fixes:
  * ``/sigma``, ``/exp``, ``//frac``   a forward slash where the backslash belongs
  * ``\\\\sigma``                         a doubled backslash
  * a form feed + "rac"                 ``\\f`` in ``\\frac`` was read as a control character by JSON
  * ``\\sigma`` shown as the word        the plain-text fallback used to just delete the backslash
"""
from __future__ import annotations

import re

GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "varepsilon": "ε", "zeta": "ζ", "eta": "η",
    "theta": "θ", "vartheta": "ϑ", "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π",
    "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ", "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π", "Sigma": "Σ", "Phi": "Φ", "Psi": "Ψ",
    "Omega": "Ω",
}
SYMBOLS = {
    "cdot": "·", "times": "×", "div": "÷", "pm": "±", "mp": "∓", "approx": "≈", "neq": "≠", "ne": "≠", "equiv": "≡",
    "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "ll": "≪", "gg": "≫", "infty": "∞", "partial": "∂", "nabla": "∇",
    "sum": "Σ", "prod": "Π", "int": "∫", "oint": "∮", "sqrt": "√", "rightarrow": "→", "to": "→", "leftarrow": "←",
    "Rightarrow": "⇒", "Leftarrow": "⇐", "leftrightarrow": "↔", "implies": "⇒", "propto": "∝", "degree": "°",
    "circ": "°", "angle": "∠", "perp": "⊥", "parallel": "∥", "in": "∈", "forall": "∀", "exists": "∃", "ldots": "…",
    "dots": "…", "cdots": "⋯", "hbar": "ħ", "ell": "ℓ", "Re": "Re", "Im": "Im", "sim": "∼", "cap": "∩", "cup": "∪",
}
OPERATORS = (
    "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "coth", "sin", "cos", "tan", "cot", "sec", "csc", "exp", "log",
    "ln", "lg", "lim", "limsup", "liminf", "max", "min", "sup", "inf", "det", "dim", "ker", "arg", "gcd", "deg", "Pr", "mod",
)
STRUCTURE = ("frac", "dfrac", "tfrac", "sqrt", "text", "mathrm", "mathbf", "mathbb", "mathcal", "left", "right", "overline",
             "underline", "vec", "hat", "bar", "dot", "ddot", "tilde", "binom", "quad", "qquad", "begin", "end", "operatorname")
KNOWN = set(GREEK) | set(SYMBOLS) | set(OPERATORS) | set(STRUCTURE)

# A control character that JSON produced from "\f", "\t", "\b", "\r" in "\frac", "\theta", "\beta", "\rho".
_CONTROL = {"\x0c": "\\f", "\x09": "\\t", "\x08": "\\b", "\x0d": "\\r"}
_NAMES = "|".join(sorted(KNOWN, key=len, reverse=True))
# ``/sigma`` or ``//frac`` when it follows the start, a space or an operator, and the word is a real command.
_SLASHED = re.compile(r"(?:(?<=^)|(?<=[\s(\[{^_=+\-*,;:|]))[/\\]{1,3}(" + _NAMES + r")(?![A-Za-z])")
_DOUBLE = re.compile(r"\\{2,}(?=[A-Za-z])")

_TEXT_MODE_START = re.compile(r"\\(?:text|mathrm|textbf)\s*\{")


def _repair_slashed_commands(tex: str) -> str:
    """Repair malformed TeX commands outside text-mode spans."""
    parts = []
    cursor = 0

    for match in _TEXT_MODE_START.finditer(tex):
        # Repair the section before this text-mode span.
        parts.append(
            _SLASHED.sub(lambda m: "\\" + m.group(1), tex[cursor:match.start()])
        )

        # Find the matching closing brace, accounting for nested braces.
        open_brace = match.end() - 1
        depth = 1
        i = open_brace + 1

        while i < len(tex) and depth:
            if tex[i] == "\\":
                # Skip escaped characters so escaped braces don't affect depth.
                i += 2
                continue

            if tex[i] == "{":
                depth += 1
            elif tex[i] == "}":
                depth -= 1

            i += 1

        # If the span is unclosed, preserve the remainder unchanged.
        if depth:
            parts.append(tex[match.start():])
            return "".join(parts)

        # Preserve the entire text-mode span unchanged.
        parts.append(tex[match.start():i])
        cursor = i

    # Repair anything remaining after the final text-mode span.
    parts.append(
        _SLASHED.sub(lambda m: "\\" + m.group(1), tex[cursor:])
    )

    return "".join(parts)

def normalize_tex(tex: str) -> str:
    """Repair a formula so MathTex gets real commands. Idempotent, and never changes a formula that was already right."""
    if not tex:
        return tex
    s = tex
    for ch, bs in _CONTROL.items():  # before strip(): a leading form feed counts as whitespace
        s = s.replace(ch, bs)
    s = s.strip().strip("$").strip()
    s = _DOUBLE.sub(r"\\", s)
    s = _repair_slashed_commands(s)
    # \\ followed by a name is now \name; a lone "\" before a space or the end is meaningless.
    s = re.sub(r"\\(?=\s|$)", "", s) if not re.search(r"\\\\", s) else s
    # Text mode words such as "\text{ rate }" are fine. Bare operator words are not: "exp(x)" is fine too, so leave them alone.
    return s


def tex_to_plain(tex: str) -> str:
    """Readable text for a formula when LaTeX is missing or fails to compile: symbols as Unicode, no stray backslashes."""
    s = normalize_tex(tex)
    s = re.sub(r"\\(?:text|mathrm|mathbf|operatorname|mathcal|mathbb)\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\^\{([^{}]*)\}", r"^(\1)", s)
    s = re.sub(r"_\{([^{}]*)\}", r"_\1", s)
    for _ in range(3):
        s = re.sub(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"√(\1)", s)
    s = re.sub(r"\\(?:left|right)(?![A-Za-z])", "", s)
    s = re.sub(r"\\(?:quad|qquad|,|;|:|!)", " ", s)

    def name(m: re.Match) -> str:
        w = m.group(1)
        return GREEK.get(w) or SYMBOLS.get(w) or w  # operators (exp, sin, ...) keep their name, only the backslash goes

    s = re.sub(r"\\([A-Za-z]+)", name, s)
    s = s.replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r"\s+", " ", s).strip()
