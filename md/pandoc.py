#!/usr/bin/env python3
import panflute as pf

def code_cpp(elem, doc):
    """
    add cpp to the classes of empty code blocks so you can just write
    `operator==` instead of `operator==`{.cpp}
    """
    if not isinstance(elem, pf.Code):
        return None

    if not elem.classes:
        elem.classes.append('cpp')
    return elem

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

def printer(elem, doc):
    import sys
    print('{}\n'.format(elem), file=sys.stderr)
    return None

def bq(elem, doc):
    """
    Add a ::: bq div to make a <blockquote>
    """
    if not isinstance(elem, pf.Div):
        return None

    if elem.classes == ['bq']:
        return pf.BlockQuote(*elem.content)

stable_name_map = {}

def wg21(elem, doc):
    """
    Turn wg21 pseudo-class into a link
    """
    if not isinstance(elem, pf.Span):
        return None

    global stable_name_map
    if not stable_name_map:
        annexf_path = doc.get_metadata('annexf')
        with open(annexf_path, 'r') as f:
            lines = f.readlines()
            stable_name_map = dict(map(lambda s: s.split(), lines))

    if elem.classes == ['wg21']:
        target = pf.stringify(elem)
        targetlink = pf.Link(pf.Str('[{}]'.format(target)), url='https://wg21.link/{}'.format(target))
        if target in stable_name_map:
            return pf.Span(pf.Str(stable_name_map[target]), pf.Space(), targetlink)
        else:
            return targetlink

def cpp2language(elem, doc):
    """
    Change all the cpp to language-cpp for prism
    """
    if not isinstance(elem, (pf.Code, pf.CodeBlock)):
        return None

    elem.classes = ['language-cpp' if c == 'cpp' else c for c in elem.classes]
    return elem

if __name__ == '__main__':
    pf.run_filters([code_cpp, h1hr, bq, wg21])
