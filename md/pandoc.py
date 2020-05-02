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


if __name__ == '__main__':
    pf.run_filters([h1hr, wordinglist, itemdecl, bq])
