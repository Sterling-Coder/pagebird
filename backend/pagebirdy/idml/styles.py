"""What a run's font and weight actually resolve to.

A `<CharacterStyleRange>` rarely says what face it is set in. In the sample
books fewer than one run in a thousand carries an inline `AppliedFont`: the
face arrives from the applied character style, or failing that from the
paragraph style, each of which may in turn inherit through `BasedOn`. Reading
only the inline attribute answers "no font" for almost every run in the
document, and two stages downstream act on that answer:

* **Math protection.** `package.segments` protects a run whose face is a math
  face -- `Mathematical Pi LT Std` -- by turning it into an opaque placeholder
  and never rewriting it. In the grade-8 sample 42 such runs name that face
  inline and **69 more reach it through the `MathPi` character styles**, so
  reading the inline attribute alone sent two thirds of the document's math to
  the translation engine and let the font override rewrite it. That is the
  math-safety guarantee failing silently.

* **Font substitution.** Choosing the weight of the target face means knowing
  the weight the run had, and that comes from the style as well.

So this module resolves a property the way InDesign does: local override, then
character style and its `BasedOn` chain, then the paragraph range's own
override, then the paragraph style and its chain, then the document default.

`AppliedFont` is a child element (`<Properties><AppliedFont>`); every other
property is an attribute. Both shapes are read here so callers do not have to
know which is which.
"""

from __future__ import annotations

from lxml import etree

# `$ID/[No character style]` and `$ID/[No paragraph style]` are InDesign's
# "nothing applied" sentinels. They are real styles carrying real defaults, so
# they are followed like any other -- naming them here would drop the document
# defaults that live on them.
_CHAIN_LIMIT = 32  # a BasedOn cycle is malformed input, not a reason to hang


def _localname(el) -> str:
    if not isinstance(el.tag, str):
        return ""
    return etree.QName(el).localname


def _own(el, name: str) -> str | None:
    """The property as this element itself declares it, attribute or child."""
    if el is None:
        return None
    value = el.get(name)
    if value is not None:
        return value
    child = el.find("./{*}Properties/{*}" + name)
    if child is not None and child.text:
        return child.text
    return None


class StyleIndex:
    """`Resources/Styles.xml` indexed by `Self`, with `BasedOn` chains.

    Built once per package and handed to every lookup; an IDML with no
    `Resources/Styles.xml` yields an empty index that resolves everything to
    None rather than raising, because which optional resources a writer emits
    varies and a missing one is not an error.
    """

    def __init__(self, styles=None, text_default=None):
        self._by_self: dict[str, etree._Element] = {}
        self._text_default = text_default
        if styles is not None:
            for el in styles.iter():
                if _localname(el) in ("ParagraphStyle", "CharacterStyle"):
                    key = el.get("Self")
                    if key:
                        self._by_self[key] = el

    @classmethod
    def from_package(cls, pkg) -> "StyleIndex":
        """Index a package's styles, parsing the two entries on demand.

        Both are read through `IdmlPackage.read_document`, which parses without
        claiming the entry for writeback: looking up an inherited font must not
        be the reason an LTR job's `Resources/Styles.xml` comes out
        re-serialised. An entry the package does not have comes back as None
        and resolves to "nothing declared", which is not an error.
        """
        prefs = pkg.read_document("Resources/Preferences.xml")
        default = None
        if prefs is not None:
            for el in prefs.iter():
                if _localname(el) == "TextDefault":
                    default = el
                    break
        return cls(pkg.read_document("Resources/Styles.xml"), default)

    def _lookup(self, key: str | None, prefix: str):
        """A style by `Self`, accepting the bare name `BasedOn` writes.

        `Self` is `CharacterStyle/lead-in`; `BasedOn` names it `lead-in`. Both
        spellings are tried.

        Each miss is tested against None rather than for truth: an lxml element
        with no children is falsy, so `a or b` silently discards every style
        that declares its properties as attributes -- which is most of them.
        """
        if not key:
            return None
        found = self._by_self.get(key)
        if found is None:
            found = self._by_self.get(f"{prefix}/{key}")
        return found

    def _through_chain(self, style, prefix: str, name: str) -> str | None:
        """Follow `BasedOn` until something declares `name`."""
        seen: set[int] = set()
        for _ in range(_CHAIN_LIMIT):
            if style is None or id(style) in seen:
                return None
            seen.add(id(style))
            value = _own(style, name)
            if value:
                return value
            style = self._lookup(_own(style, "BasedOn"), prefix)
        return None

    def effective(self, psr, csr, name: str) -> str | None:
        """A run's resolved value for `name`, or None if nothing declares it.

        `psr` is the enclosing `<ParagraphStyleRange>` and `csr` the
        `<CharacterStyleRange>`; either may be None, which is what a property
        looked up outside a story means.
        """
        for source in (
            lambda: _own(csr, name),
            lambda: self._through_chain(
                self._lookup(csr.get("AppliedCharacterStyle") if csr is not None else None,
                             "CharacterStyle"), "CharacterStyle", name),
            lambda: _own(psr, name),
            lambda: self._through_chain(
                self._lookup(psr.get("AppliedParagraphStyle") if psr is not None else None,
                             "ParagraphStyle"), "ParagraphStyle", name),
            lambda: _own(self._text_default, name),
        ):
            value = source()
            if value:
                return value
        return None


def ranges_of(content):
    """The `(ParagraphStyleRange, CharacterStyleRange)` a `<Content>` sits in.

    Either comes back None when the run is not inside one -- a `<Content>` in a
    resource fragment rather than a story.
    """
    psr = csr = None
    el = content.getparent()
    while el is not None:
        tag = _localname(el)
        if csr is None and tag == "CharacterStyleRange":
            csr = el
        elif tag == "ParagraphStyleRange":
            psr = el
            break
        el = el.getparent()
    return psr, csr


# ---- choosing the target face's weight --------------------------------------

# Weight and slant as they are actually written in these documents. Museo Sans
# names its weights numerically ("300", "500", "900"), Myriad Pro names them
# ("Semibold Italic"), and `Mathematical Pi LT Std` calls its only face "3" --
# which is why a numeric style is read as a weight on the 100..900 axis rather
# than as an index, and why anything under 600 stays regular.
_BOLD_WORDS = ("bold", "black", "heavy", "semibold", "demi", "extrabold",
               "ultra", "extra bold", "semi bold")
_ITALIC_WORDS = ("italic", "oblique", "kursiv")
# `ultra`, `demi` and `extra` only qualify the word after them: "Ultra Light"
# is thinner than Regular. A light word therefore wins over them, and loses
# only to a name that also says outright that it is heavy.
_LIGHT_WORDS = ("light", "thin", "hairline")
_HEAVY_WORDS = ("bold", "black", "heavy")
_BOLD_WEIGHT = 600


def is_bold(style: str | None) -> bool:
    """True when a font style name means a bold-ish weight."""
    name = (style or "").strip().lower()
    if not name:
        return False
    if name.replace(" ", "").isdigit():
        return int(name.replace(" ", "")) >= _BOLD_WEIGHT
    if any(word in name for word in _LIGHT_WORDS):
        return any(word in name for word in _HEAVY_WORDS)
    return any(word in name for word in _BOLD_WORDS)


def is_italic(style: str | None) -> bool:
    name = (style or "").strip().lower()
    return any(word in name for word in _ITALIC_WORDS)


def target_font_style(style: str | None, available) -> str:
    """The closest face the target family actually ships to `style`.

    Substituting the family without substituting the style is what loses every
    heading's weight. The source names its weights on its own terms -- Museo
    Sans "900", Myriad Pro "Semibold Italic" -- and naming those against an
    Arabic family InDesign resolves them in gives a missing *style* warning and
    a substituted face, so a bold heading opens regular.

    `available` is the list of faces the target family is registered with, so a
    family shipping no italic never has one named at it: the request degrades
    bold-italic to bold to regular rather than inventing a face.
    """
    faces = [f for f in (available or ()) if f]
    if not faces:
        return "Regular"
    bold, italic = is_bold(style), is_italic(style)
    for want in (
        "Bold Italic" if bold and italic else None,
        "Bold" if bold else None,
        "Italic" if italic else None,
        "Regular",
    ):
        if want and want in faces:
            return want
    return faces[0]
