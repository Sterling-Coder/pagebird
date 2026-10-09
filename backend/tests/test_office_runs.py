from pagebirdy.office.runs import Piece, decode, encode


def P(text, key=""):
    return Piece("text", text, key, handle=text)


def test_base_style_untagged_others_tagged():
    tagged, lay = encode([P("Click "), P("Save", "b"), P(" to continue")])
    assert tagged == "Click ⟦r1⟧Save⟦/r1⟧ to continue"
    assert [p.text for p in lay.spans[lay.base]] == ["Click "]


def test_adjacent_same_format_runs_merge():
    tagged, _ = encode([P("Hel"), P("lo "), P("wor", "i"), P("ld", "i")])
    assert tagged == "Hello ⟦r1⟧world⟦/r1⟧"


def test_single_style_paragraph_has_no_tags():
    tagged, lay = encode([P("Just "), P("text")])
    assert tagged == "Just text" and lay.tags == {}


def test_objects_and_breaks():
    tagged, lay = encode([P("Name:"), Piece("object", handle="TAB"), P("value"), Piece("break")])
    assert tagged == "Name:⟦x0⟧value⟦br⟧"
    assert lay.objects[0].handle == "TAB"


def test_decode_follows_engine_word_order():
    _, lay = encode([P("Click "), P("Save", "b"), P(" to continue")])
    out = decode("Pulsa ⟦r1⟧Guardar⟦/r1⟧ para seguir", lay)
    assert [(o.kind, o.span, o.text) for o in out] == [
        ("text", lay.base, "Pulsa "), ("text", lay.tags[1], "Guardar"),
        ("text", lay.base, " para seguir")]


def test_decode_reordered_tags_move_formatting():
    _, lay = encode([P("red", "r"), P(" and "), P("blue", "b")])
    out = decode("⟦r2⟧azul⟦/r2⟧ y ⟦r1⟧rojo⟦/r1⟧", lay)
    assert [(o.span, o.text) for o in out] == [
        (lay.tags[2], "azul"), (lay.base, " y "), (lay.tags[1], "rojo")]


def test_decode_rejects_malformed():
    _, lay = encode([P("a "), P("b", "x"), P(" c")])
    assert decode("a ⟦/r1⟧b⟦r1⟧ c", lay) is None          # closed before opened
    assert decode("a ⟦r1⟧b c", lay) is None                # never closed
    assert decode("a ⟦r1⟧⟦r1⟧b⟦/r1⟧⟦/r1⟧", lay) is None     # nested
    assert decode("a ⟦r9⟧b⟦/r9⟧", lay) is None             # unknown tag
    _, lay2 = encode([P("a"), Piece("object", handle=1)])
    assert decode("a⟦x0⟧⟦x0⟧", lay2) is None               # object duplicated
    assert decode("a⟦x3⟧", lay2) is None                   # unknown object


def test_value_tokens_stay_in_text():
    _, lay = encode([P("Add "), P("5", "b")])
    out = decode("Suma ⟦r1⟧⟦=5⟧⟦/r1⟧", lay)
    assert out[1].text == "⟦=5⟧"


def test_breaks_decode_in_place():
    _, lay = encode([P("one"), Piece("break"), P("two")])
    out = decode("uno⟦br⟧dos", lay)
    assert [o.kind for o in out] == ["text", "break", "text"]


# --- tag_problem: what the gate's token count cannot see -------------------

from pagebirdy.office.runs import tag_problem  # noqa: E402

SRC = "Sales Order ⟦r1⟧Automation⟦/r1⟧"


def test_tag_problem_accepts_a_pair_moved_with_its_words():
    assert tag_problem(SRC, "⟦r1⟧أتمتة⟦/r1⟧ أوامر البيع") is None
    assert tag_problem(SRC, "Automatización de ⟦r1⟧pedidos⟦/r1⟧") is None


def test_tag_problem_names_the_words_an_empty_pair_should_wrap():
    why = tag_problem(SRC, "أتمتة أوامر البيع ⟦r1⟧⟦/r1⟧")
    assert why and "empty" in why and '"Automation"' in why
    assert tag_problem(SRC, "a ⟦r1⟧ ⟦/r1⟧ b")  # whitespace is not words


def test_tag_problem_misordered_nested_open_and_unknown():
    assert "not open" in tag_problem(SRC, "⟦/r1⟧x⟦r1⟧")
    two = "⟦r1⟧a⟦/r1⟧ ⟦r2⟧b⟦/r2⟧"
    assert "nest" in tag_problem(two, "⟦r1⟧a ⟦r2⟧b⟦/r2⟧⟦/r1⟧")
    assert "never closed" in tag_problem(SRC, "⟦r1⟧x")
    assert "not in the source" in tag_problem(SRC, "⟦r2⟧x⟦/r2⟧")


def test_tag_problem_objects_and_breaks_are_not_words():
    src = "Press ⟦r1⟧⟦x0⟧ Save⟦/r1⟧"
    assert tag_problem(src, "Pulsa ⟦r1⟧⟦x0⟧⟦/r1⟧ Guardar")
    assert tag_problem(src, "Pulsa ⟦r1⟧⟦x0⟧ Guardar⟦/r1⟧") is None


def test_tag_problem_an_empty_source_pair_may_stay_empty():
    assert tag_problem("a ⟦r1⟧ ⟦/r1⟧b", "x ⟦r1⟧⟦/r1⟧y") is None
    assert tag_problem("no tags here", "sin etiquetas") is None


# --- placing pairs in code: alignment and the unstyled fallback -------------

from pagebirdy.office.runs import pair_words, place_pairs, unplaced, untagged  # noqa: E402


def test_pair_words_untagged_and_unplaced():
    assert pair_words(SRC) == {1: "Automation"}
    assert untagged("أتمتة أوامر البيع ⟦r1⟧⟦/r1⟧") == "أتمتة أوامر البيع"
    assert untagged("a ⟦r1⟧b⟦/r1⟧ c") == "a b c"
    assert unplaced(SRC, "أتمتة أوامر البيع") == "أتمتة أوامر البيع⟦r1⟧⟦/r1⟧"


def test_place_pairs_wraps_the_whole_word_through_a_clitic():
    plain = "التنبؤ بالطلب المدفوع بالذكاء الاصطناعي"
    src = "AI Driven Demand ⟦r1⟧Forecasting⟦/r1⟧"
    # Asked alone the engine may drop the article; the sentence has it.
    assert place_pairs(src, plain, {1: "تنبؤ"}, False) == \
        "⟦r1⟧التنبؤ⟦/r1⟧ بالطلب المدفوع بالذكاء الاصطناعي"
    assert place_pairs(src, plain, {1: "التنبؤ"}, False).startswith("⟦r1⟧التنبؤ⟦/r1⟧")


def test_place_pairs_ignores_diacritics_and_alef_forms():
    plain = "أتمتة أوامر البيع"
    assert place_pairs(SRC, plain, {1: "اتمتة"}, False) == "⟦r1⟧أتمتة⟦/r1⟧ أوامر البيع"
    assert place_pairs(SRC, "أَتْمَتَة أوامر", {1: "أتمتة"}, False) == "⟦r1⟧أَتْمَتَة⟦/r1⟧ أوامر"


def test_place_pairs_latin_and_char_wrapped_targets():
    src = "Sales Order ⟦r1⟧Automation⟦/r1⟧"
    assert place_pairs(src, "Automatización de pedidos.", {1: "automatización"}, False) == \
        "⟦r1⟧Automatización⟦/r1⟧ de pedidos."
    assert place_pairs(src, "销售订单自动化", {1: "自动化"}, True) == "销售订单⟦r1⟧自动化⟦/r1⟧"


def test_place_pairs_refuses_what_it_cannot_find_or_overlapping_pairs():
    assert place_pairs(SRC, "أتمتة أوامر البيع", {1: "الاستحواذ"}, False) is None
    assert place_pairs(SRC, "أتمتة أوامر البيع", {}, False) is None
    two = "⟦r1⟧a⟦/r1⟧ and ⟦r2⟧b⟦/r2⟧"
    assert place_pairs(two, "uno y dos", {1: "uno y", 2: "y dos"}, False) is None
    assert place_pairs(two, "uno y dos", {1: "uno", 2: "dos"}, False) == "⟦r1⟧uno⟦/r1⟧ y ⟦r2⟧dos⟦/r2⟧"


def test_place_pairs_never_styles_the_whole_sentence_unless_the_english_was():
    assert place_pairs(SRC, "أتمتة أوامر البيع", {1: "أتمتة أوامر البيع"}, False) is None
    whole = "⟦r1⟧Automation⟦/r1⟧"
    assert place_pairs(whole, "الأتمتة", {1: "الأتمتة"}, False) == "⟦r1⟧الأتمتة⟦/r1⟧"


def test_place_pairs_widens_only_a_match_that_cuts_a_word():
    assert place_pairs("Element⟦r1⟧.AI⟦/r1⟧", "Element.AI", {1: ".AI"}, False) == "Element⟦r1⟧.AI⟦/r1⟧"
    assert place_pairs(SRC, "الأَتْمَتَة أوامر", {1: "أتمتة"}, False) == "⟦r1⟧الأَتْمَتَة⟦/r1⟧ أوامر"


# --- evidence for where styling goes: verbatim, then glossed meaning ---------

from pagebirdy.office.runs import gloss_span, verbatim  # noqa: E402


def test_verbatim_finds_brands_acronyms_and_numbers_as_written():
    assert verbatim("Element.AI", ".AI") == ".AI"
    assert verbatim("CAD CAM en ⟦=3⟧D", "CAM") == "CAM"
    assert verbatim("Cliente ⟦=720⟧", "⟦=720⟧") == "⟦=720⟧"
    assert verbatim("Transformación digital", "Digital") == "digital"
    assert verbatim("Camión", "CAM") is None            # not inside another word
    assert verbatim("Pronóstico de demanda", "Demand") is None


def test_gloss_span_finds_the_words_by_meaning_not_position():
    # Seen live: asked "which words render 'Demand'?", the model said "Pronóstico".
    g = [("Pronóstico", "forecast"), ("de", "of"), ("demanda", "demand")]
    assert gloss_span("Pronóstico de demanda", g, "Demand") == "demanda"
    g = [("Rentabilidad", "profitability"), ("de", "of"), ("puntuación", "score"),
         ("de", "of"), ("leads", "leads")]
    assert gloss_span("Rentabilidad de puntuación de leads", g, "Lead Score") == "puntuación de leads"
    g = [("التنبؤ", "forecasting"), ("بالطلب", "with demand")]
    assert gloss_span("التنبؤ بالطلب", g, "Demand") == "بالطلب"


def test_gloss_span_maps_back_through_diacritics_and_refuses_what_it_cannot_find():
    g = [("أَتْمَتَة", "automation"), ("أوامر", "orders")]
    assert gloss_span("أَتْمَتَة أوامر", g, "Automation") == "أَتْمَتَة"
    g = [("أتمتة", "automation"), ("أوامر", "orders"), ("الشراء", "purchase")]
    assert gloss_span("أتمتة أوامر الشراء", g, "PO & SO") is None   # no words for it
    assert gloss_span("أتمتة", [("غير", "other")], "Automation") is None
    assert gloss_span("أتمتة", [], "Automation") is None
