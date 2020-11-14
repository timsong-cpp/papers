#!/usr/bin/env python3
import panflute as pf
import sys;

def h1hr(elem, doc):
    """
    Add a bottom border to all the <h1>s
    """
    if not isinstance(elem, pf.Header):
        return None

    if elem.level != 1:
        return None

    elem.attributes['style'] = 'border-bottom:1px solid #cccccc'
    return elem

def bq(elem, doc):
    """
    Add a ::: bq div to make a <blockquote>
    """
    if not isinstance(elem, pf.Div):
        return None

    if elem.classes == ['bq']:
        return pf.BlockQuote(*elem.content)

def itemdecl(elem, doc):
    """
    Item decls.

    Top-level code blocks specify the declaration of an item.

    Everything in-between top-level code blocks are indented by wrapping
    in a <blockquote>.
    """

    if not isinstance(elem, pf.Div):
        return None

    if not 'itemdecl' in elem.classes:
        return None

    content = []
    current_bq = []

    for e in elem.content:
        if isinstance(e, pf.CodeBlock) or isinstance(e, pf.RawBlock):
            if current_bq:
                content.append(pf.BlockQuote(*current_bq))
                current_bq = []
            content.append(e)
        else:
            current_bq.append(e)

    if current_bq:
        content.append(pf.BlockQuote(*current_bq))
        current_bq = []

    if 'bq' in elem.classes:
        return pf.BlockQuote(*content)
    else:
        return pf.Div(*content)


def wordinglist(elem, doc):
    """
    A "wording list", in the form of alternating list and wording:

    - Edit foo as indicated:
    wording
    - whatever
    wording

    The wording is automatically indented by wrapping into a blockquote.

    The lists are converted into ordered lists and adjusted to have continuous
    numbering.

    """

    if not isinstance(elem, pf.Div):
        return None

    if not 'wordinglist' in elem.classes:
        return None

    content = []
    current_bq = []
    current_start = 1

    for e in elem.content:
        if isinstance(e, pf.BulletList) or isinstance(e, pf.OrderedList):
            if current_bq:
                content.append(pf.BlockQuote(*current_bq))
                current_bq = []
            content.append(pf.OrderedList(*e.content, start=current_start))
            current_start += len(e.content)
        else:
            current_bq.append(e)

    if current_bq:
        content.append(pf.BlockQuote(*current_bq))
        current_bq = []

    return pf.Div(*content)


def longtable(table, doc):
    """
    Long tables: Like cmptable, but the first-class entities are
    'ltcell' divs rather than code blocks.
    Each 'ltcell' div is pushed onto the current row.
    A horizontal rule (`---`) is used to move to the next row.

    In the first row, the last header (if any) leading upto the i'th
    div is the header for the i'th column of the table.

    The last block quote (if any) is used as the caption.

    # Example

    ::: longtable

    > compare inspect of unconstrained and constrained types

    ### Before
    ::: ltcell
    ```cpp
    std::visit([&](auto&& x) {
      strm << "got auto: " << x;
    }, v);
    ```
    :::

    ### After
    ::: ltcell
    ```cpp
    inspect (v) {
      <auto> x: strm << "got auto: " << x;
    }
    ```
    :::

    ---
    ::: ltcell
    ```cpp
    std::visit([&](auto&& x) {
      using X = std::remove_cvref_t<decltype(x)>;
      if constexpr (C1<X>()) {
        strm << "got C1: " << x;
      } else if constexpr (C2<X>()) {
        strm << "got C2: " << x;
      }
    }, v);
    ```
    :::

    ::: ltcell

    ```cpp
    inspect (v) {
      <C1> c1: strm << "got C1: " << c1;
      <C2> c2: strm << "got C2: " << c2;
    }
    ```
    :::

    :::

    # Generates

    Table: compare inspect of unconstrained and constrained types

    +------------------------------------------------+---------------------------------------------+
    | __Before__                                     | __After__                                   |
    +================================================+=============================================+
    | ```cpp                                         | ```cpp                                      |
    | std::visit([&](auto&& x) {                     | inspect (v) {                               |
    |   strm << "got auto: " << x;                   |   <auto> x: strm << "got auto: " << x;      |
    | }, v);                                         | }                                           |
    |                                                | ```                                         |
    +------------------------------------------------+---------------------------------------------+
    | std::visit([&](auto&& x) {                     | ```cpp                                      |
    |   using X = std::remove_cvref_t<decltype(x)>;  | inspect (v) {                               |
    |   if constexpr (C1<X>()) {                     |   <C1> c1: strm << "got C1: " << c1;        |
    |     strm << "got C1: " << x;                   |   <C2> c2: strm << "got C2: " << c2;        |
    |   } else if constexpr (C2<X>()) {              | }                                           |
    |     strm << "got C2: " << x;                   | ```                                         |
    |   }                                            |                                             |
    | }, v);                                         |                                             |
    +------------------------------------------------+---------------------------------------------+
    """

    if not isinstance(table, pf.Div):
        return None

    if 'longtable' not in table.classes:
        return None

    rows = []
    kwargs = {}

    headers = []
    widths = []
    examples = []

    header = pf.Null()
    caption = None
    width = 0

    first_row = True
    table.content.append(pf.HorizontalRule())

    def warn(elem):
        pf.debug('mpark/wg21:', type(elem), pf.stringify(elem, newlines=False),
                 'in a long table is ignored')

    for elem in table.content:
        if isinstance(elem, pf.Header):
            if not isinstance(header, pf.Null):
                warn(header)

            if first_row:
                header = pf.Plain(*elem.content)
                width = float(elem.attributes['width']) if 'width' in elem.attributes else 0
            else:
                warn(elem)
        elif isinstance(elem, pf.BlockQuote):
            if caption is not None:
                warn(caption)

            caption = elem
        elif isinstance(elem, pf.Div):
            if 'ltcell' not in elem.classes:
                warm(elem)

            if first_row:
                headers.append(header)
                widths.append(width)

                header = pf.Null()
                width = 0

            examples.append(elem)
        elif isinstance(elem, pf.HorizontalRule) and examples:
            first_row = False

            rows.append(pf.TableRow(*[pf.TableCell(example) for example in examples]))
            examples = []
        else:
            warn(elem)

    if not all(isinstance(header, pf.Null) for header in headers):
        kwargs['header'] = pf.TableRow(*[pf.TableCell(header) for header in headers])

    if caption is not None:
        kwargs['caption'] = caption.content[0].content

    kwargs['width'] = widths

    return pf.Table(*rows, **kwargs)


if __name__ == '__main__':
    pf.run_filters([h1hr, wordinglist, itemdecl, bq, longtable])
