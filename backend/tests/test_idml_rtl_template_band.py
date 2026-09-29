"""What sits on a page template's side strip stays exactly where English had it.

The Family Letter master draws a full-height strip down one edge; the lesson
badge, the Math Tools box, the folio and the "use the next page" callout sit on
it. A document page often carries its own copies of those -- a master item the
page overrode, or a local callout that replaced the master's -- and a copy is
not a master item, so it used to fall through to `default.mirror`: RCM07 L04
page 59 printed its badge circle at the top-left corner with the lesson number
still on the right, and its strip (and with it the white vertical title) on the
far side of the page.

Anything on a page that reaches onto the strip its applied master draws is
template furniture: same position, same size, never mirrored. The content
beside it still mirrors, within the area the strip leaves.

Every expectation is derived from the fixture's own geometry.
"""

from lxml import etree

from pagebirdy.idml import rtl, rtl_plan

PAGE_W, PAGE_H = 612.0, 792.0
STRIP_X0 = 548.0          # the strip runs from here to the right trim and beyond
TOL = 1e-6


def _rect(self_id, x0, x1, y0, y1, tag="Rectangle", tx=0.0):
    return f"""
    <{tag} Self="{self_id}" ItemTransform="1 0 0 1 {tx:g} 0">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{x0} {y0}"/><PathPointType Anchor="{x0} {y1}"/>
        <PathPointType Anchor="{x1} {y1}"/><PathPointType Anchor="{x1} {y0}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </{tag}>"""


def _page(self_id, master=None, override_list=""):
    applied = f' AppliedMaster="{master}"' if master else ""
    return (f'<Page Self="{self_id}" GeometricBounds="0 0 {PAGE_H:g} {PAGE_W:g}" '
            f'ItemTransform="1 0 0 1 0 {-PAGE_H / 2:g}"{applied} '
            f'OverrideList="{override_list}"/>')


def _docs(page_items, override_list=""):
    top, bottom = -PAGE_H / 2, PAGE_H / 2
    master = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:MasterSpread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <MasterSpread Self="m" PageCount="1" ItemTransform="1 0 0 1 0 0">
    {_page("mp")}
    {_rect("m_strip", STRIP_X0, PAGE_W + 13.5, top - 13.5, bottom + 13.5)}
  </MasterSpread>
</idPkg:MasterSpread>"""
    spread = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="s" PageCount="1" ItemTransform="1 0 0 1 0 0">
    {_page("p", master="m", override_list=override_list)}
    {page_items}
  </Spread>
</idPkg:Spread>"""
    return {"MasterSpreads/M.xml": etree.fromstring(master.encode()),
            "Spreads/S.xml": etree.fromstring(spread.encode())}


def _l04_page():
    top, bottom = -PAGE_H / 2, PAGE_H / 2
    return "".join([
        # The page's own copy of the master strip.
        _rect("strip", STRIP_X0, PAGE_W + 13.5, top - 13.5, bottom + 13.5),
        # The badge circle, straddling the strip's edge.
        _rect("circle", 481, 581, -346, -245, tag="Oval"),
        # The Math Tools box, a few points onto the strip.
        _rect("tools", 495, 555, -280, -156),
        # The callout bar: most of it over content, its end on the strip.
        f'<Group Self="callout" ItemTransform="1 0 0 1 0 0">'
        f'{_rect("callout_bar", 337, 625, 301, 334)}'
        f'{_rect("callout_arrow", 343, 367, 305, 329, tag="Oval")}</Group>',
        # Ordinary content, clear of the strip.
        _rect("picture", 306, 487, -221, -79),
        # A backdrop spanning the whole page is not on the strip; it is behind it.
        _rect("backdrop", -9, PAGE_W + 9, top - 9, -269),
    ])


FIXED = ("strip", "circle", "tools", "callout", "callout_bar", "callout_arrow")


def _plan(docs):
    return rtl_plan.build_plan(docs, document="d", language="ar")


def _box(docs, self_id):
    el = docs["Spreads/S.xml"].find(f".//*[@Self='{self_id}']")
    t = rtl.IDENTITY
    for a in reversed([a for a in el.iterancestors()
                       if rtl._is_page_item(a) and not rtl._is(a, "Spread")]):
        t = rtl.compose(t, rtl.parse_transform(a.get("ItemTransform")))
    return rtl.item_bounds(el, t)


def test_everything_on_the_template_strip_is_furniture():
    by = _plan(_docs(_l04_page())).by_object()
    for key in FIXED:
        assert by[key].action == rtl_plan.KEEP_POSITION, key
        assert by[key].new_orientation == rtl_plan.KEEP_ORIENTATION, key
    for key in ("strip", "circle", "tools", "callout"):
        assert by[key].rule == "structure.template_band", key


def test_content_beside_the_strip_still_mirrors():
    by = _plan(_docs(_l04_page())).by_object()
    assert by["picture"].action == rtl_plan.RTL_MIRROR
    assert by["backdrop"].rule != "structure.template_band"


def test_template_band_items_keep_their_exact_geometry_and_content_mirrors_beside_them():
    docs = _docs(_l04_page())
    before = {k: _box(docs, k) for k in FIXED + ("picture",)}
    rtl.apply_plan(docs, _plan(docs))
    for key in FIXED:
        after = _box(docs, key)
        assert all(abs(a - b) <= TOL for a, b in zip(before[key], after)), key
    # The picture mirrors within the area the strip leaves, not about the
    # page's physical centre.
    axis = STRIP_X0 / 2.0
    x0, _, x1, _ = before["picture"]
    px0, _, px1, _ = _box(docs, "picture")
    assert abs(px0 - (2 * axis - x1)) <= TOL and abs(px1 - (2 * axis - x0)) <= TOL


def test_a_label_set_inside_a_strip_box_stays_in_it():
    # RCM08 U02 L05: the "Math Tools" label frame sits inside the Math Tools
    # box but stops 2pt short of the strip. Mirrored on its own account it
    # printed at the far page edge, out of the box that stayed.
    docs = _docs(_l04_page() + _rect("tools_label", 503, 546, -237, -164))
    by = _plan(docs).by_object()
    assert by["tools_label"].rule == "structure.template_band"
    before = _box(docs, "tools_label")
    rtl.apply_plan(docs, _plan(docs))
    assert all(abs(a - b) <= TOL for a, b in zip(before, _box(docs, "tools_label")))


def test_content_merely_touching_a_strip_item_still_mirrors():
    # A body frame whose corner runs under the badge circle in English is
    # content, not part of the badge.
    docs = _docs(_l04_page() + _rect("body", 54, 486, -269, -25))
    assert _plan(docs).by_object()["body"].action == rtl_plan.RTL_MIRROR


def test_a_full_bleed_photo_under_the_strip_is_decorative_art_not_the_template():
    # The Family Letter header photo runs from just inside the left trim off
    # the right one, under the strip. It belongs to the bleed rules.
    top = -PAGE_H / 2
    photo = (f'<Rectangle Self="photo" ItemTransform="1 0 0 1 0 0">'
             f'<Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>'
             f'<PathPointType Anchor="2 {top - 9}"/><PathPointType Anchor="2 -273"/>'
             f'<PathPointType Anchor="{PAGE_W + 14} -273"/><PathPointType Anchor="{PAGE_W + 14} {top - 9}"/>'
             f'</PathPointArray></GeometryPathType></PathGeometry></Properties>'
             f'<Image Self="photo_img" ItemTransform="1 0 0 1 0 0"/></Rectangle>')
    by = _plan(_docs(_l04_page() + photo)).by_object()
    assert by["photo"].rule not in ("structure.template_band",)
    assert by["photo"].rule.startswith("graphic.")


def test_a_strip_the_page_removed_puts_nothing_on_the_template():
    # "m_strip n": the page deleted its override of the master strip, so the
    # strip does not print there and nothing beside its old place is furniture.
    docs = _docs(_rect("circle", 481, 581, -346, -245, tag="Oval"),
                 override_list="m_strip n")
    by = _plan(docs).by_object()
    assert by["circle"].rule != "structure.template_band"
    assert by["circle"].action == rtl_plan.RTL_MIRROR


def test_a_facing_master_s_strip_belongs_only_to_the_page_it_is_drawn_on():
    # The Family Letter master is a spread: its strip is on the right-hand
    # page. A left-hand document page using that master has no strip, and a
    # page's own copy of the master's left-page backdrop is not one either.
    top, bottom = -PAGE_H / 2, PAGE_H / 2
    master = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:MasterSpread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <MasterSpread Self="m" PageCount="2" ItemTransform="1 0 0 1 0 0">
    <Page Self="ml" GeometricBounds="0 0 {PAGE_H:g} {PAGE_W:g}" ItemTransform="1 0 0 1 {-PAGE_W:g} {-PAGE_H / 2:g}"/>
    <Page Self="mr" GeometricBounds="0 0 {PAGE_H:g} {PAGE_W:g}" ItemTransform="1 0 0 1 0 {-PAGE_H / 2:g}"/>
    {_rect("m_back", -PAGE_W - 13.5, 0, top - 13.5, bottom + 13.5)}
    {_rect("m_strip", STRIP_X0, PAGE_W + 13.5, top - 13.5, bottom + 13.5)}
  </MasterSpread>
</idPkg:MasterSpread>"""
    spread = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="s" PageCount="2" ItemTransform="1 0 0 1 0 0">
    <Page Self="pl" GeometricBounds="0 0 {PAGE_H:g} {PAGE_W:g}" ItemTransform="1 0 0 1 {-PAGE_W:g} {-PAGE_H / 2:g}" AppliedMaster="m"/>
    <Page Self="pr" GeometricBounds="0 0 {PAGE_H:g} {PAGE_W:g}" ItemTransform="1 0 0 1 0 {-PAGE_H / 2:g}" AppliedMaster="u_other"/>
    {_rect("left_margin_note", -80, -20, -100, 100)}
  </Spread>
</idPkg:Spread>"""
    docs = {"MasterSpreads/M.xml": etree.fromstring(master.encode()),
            "Spreads/S.xml": etree.fromstring(spread.encode())}
    s = docs["Spreads/S.xml"].find(".//Spread")
    bands = rtl.template_bands(s, {"m": docs["MasterSpreads/M.xml"].find(".//MasterSpread")})
    assert bands == [[], []]
    by = _plan(docs).by_object()
    assert by["left_margin_note"].action == rtl_plan.RTL_MIRROR


def test_a_master_without_a_side_strip_fixes_nothing():
    docs = _docs(_rect("circle", 481, 581, -346, -245, tag="Oval"))
    docs["MasterSpreads/M.xml"].find(".//*[@Self='m_strip']").getparent().remove(
        docs["MasterSpreads/M.xml"].find(".//*[@Self='m_strip']"))
    by = _plan(docs).by_object()
    assert by["circle"].action == rtl_plan.RTL_MIRROR
