---
title: Repairing input range adaptors
document: D2259R0
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Abstract
This paper proposes a fix for several issues with `iterator_category` for range
and iterator adaptors. This resolves [@LWG3283], [@LWG3289], and [@LWG3408].

# The problem

This code does not compile:

```c++
    std::vector<int> vec = {42};
    auto r = vec | std::views::transform([](int c) { return std::views::single(c);})
                 | std::views::join
                 | std::views::filter([](int c) { return c > 0; });
    r.begin();
```

Not because we are breaking any concept requirements:

- the `transform` produces a range of views of `int`;
- the `join` takes that and produce an input range of `int`;
- the `filter` should then produce another input range of `int`...in theory.

The problem is that `join_view`'s iterator for this case has a postfix
`operator++` that returns `void`, making it not a valid C++17 iterator at all -
even C++17 output iterators require `*i++` to be valid. In turn, that means
that `iterator_traits<join_view::@_iterator_@>` is entirely empty, and
`filter_view` cannot cope with that as currently specified, because it expects
`iterator_category` to be always present ([range.filter.iterator]{.sref}).

[@LWG3283] and [@LWG3289] were discussed at length during during the Belfast
and Prague meetings. LWG was aware that as specified the range adaptors
do not work with non-C++17 iterators due to these issues. However, I do not believe
that it was clear to LWG that this impacts not just the one move-only iterator
we have specified in the standard library, but also virtually _every_ range
adaptor with its own iterator type when used in conditions that produce an input
range.

# The fix

We shouldn't (and can't) change postfix increment on the adaptor's iterators.
There's nothing we can meaningfully return from `operator++` for arbitrary input
iterators, especially if we are trying to adapt them. This was discussed in
&sect;3.1.2 of [@P0541R1] and there is no need to rehash that discussion here.

These iterators are, then, not C++17 iterators _at all_, and specializations of
`std::iterator_traits` for them have no members as currently specified. That seems
to be an acceptable state of affairs.

It follows that the concern noted in [@LWG3283]'s discussion is unlikely to be
materialize in practice. While _some_ C++20 input iterators might look like
C++17 output iterators, I suspect that a large majority will not look like C++17
iterators at all. The fraction of input iterators that take advantage of the
C++20 permission to not define `==` but not the permission to make postfix
increment return `void` is likely small.

The fact that the  `iterator_traits` specializations for these not-a-C++17-iterators
don't have an `iterator_category` member (or any other) means that we don't really
have a choice on the fix: we have to handle this case gracefully in the adaptors. The
`output_iterator_tag` hack proposed in [@LWG3289] is not a viable approach because
these iterators aren't C++17 output iterators either, regardless of how hard we
squint. Inventing a new `not_an_iterator_tag` defeats the purpose of C++20
`iterator_traits` as a C++17 compatibility layer: in C++17, if something is not
an iterator, then `iterator_traits` is empty. We should keep this behavior,
especially as the gain from making a new tag type is basically just somewhat
simpler metaprogramming in the library.

As it turns out, the iterators of the range adaptors are only valid C++17
iterators (with a postfix increment that doesn't return `void`) when they are
at least C++20 forward iterators or stronger. As all valid C++20 forward iterators
meet the C++17 input iterator requirements, we can simply restrict the provision
of `iterator_category` members to C++20 forward iterators. In those cases, the
adapted iterators must also be C++20 forward iterators, so `iterator_category`
should always be present in their `iterator_traits`, ignoring pathological
program-defined specializations. That simplifies the wording considerably
by removing the need to separately consider whether `iterator_category` is
present.

# Wording

This wording is relative to [@N4868].

::: wordinglist

- Add an example to [iterator.traits]{.sref} p4 as indicated:

[4]{.pnum} Explicit or partial specializations of `iterator_traits` may have a
member type `iterator_concept` that is used to indicate conformance to
the iterator concepts ([iterator.concepts]{.sref}). [[To indicate conformance to
the `input_iterator` concept but a lack of conformance to the _Cpp17InputIterator_
requirements ([input.iterators]{.sref}), an `iterator_traits` specialization
might have `iterator_concept` denote `input_iterator_tag` but not define
`iterator_category`.]{.example}]{.diffins}


- Edit [move.iterator]{.sref} as indicated:

```c++
namespace std {
  template<class Iterator>
  class move_iterator {
  public:
    using iterator_type     = Iterator;
    using iterator_concept  = input_iterator_tag;
    using iterator_category = see below;    @[// not always present]{.diffins}@
    using value_type        = iter_value_t<Iterator>;
    using difference_type   = iter_difference_t<Iterator>;
    using pointer           = Iterator;
    using reference         = iter_rvalue_reference_t<Iterator>;

    // [...]
  };
}
```

::: dummy

[1]{.pnum} The member _typedef-name_ `iterator_­category` [is defined if and only
if the _qualified-id_ `iterator_­traits<​Iterator>​::​iterator_­category` is valid
and denotes a type. In that case, `iterator_­category`]{.diffins} denotes

- [1.1]{.pnum} `random_­access_­iterator_­tag` if the type `iterator_­traits<​Iterator>​::​iterator_­category`
  models `derived_­from<random_­access_­iterator_­tag>`, and
- [1.2]{.pnum} `iterator_­traits<​Iterator>​::​iterator_­category` otherwise.

:::

- Edit [common.iter.types]{.sref}:

::: draftnote

`common_iterator` is a C++17 compatibility layer, and that's reflected in its
synthesis of an `operator==` even when the underlying type does not support it.
The proposed wording here follows that design by similarly providing a
C++17-conforming postfix `operator++` even if the underlying type doesn't.

:::

::: dummy

[1]{.pnum} The nested *typedef-name*s of the specialization of `iterator_traits`
for `common_iterator<I, S>` are defined as follows.

- [1.1]{.pnum} `iterator_concept` denotes `forward_iterator_tag` if `I` models
  `forward_iterator`; otherwise it denotes `input_iterator_tag`.
- [1.2]{.pnum} `iterator_category` denotes `forward_iterator_tag` if
  [the _qualified-id_]{.diffins} `iterator_traits<I>::iterator_category`
  [is valid and denotes a type that]{.diffins} models
  `derived_from<forward_iterator_tag>`; otherwise it denotes `input_iterator_tag`.
- [1.3]{.pnum} If the expression `a.operator->()` is well-formed,
  where `a` is an lvalue of type `const common_iterator<I, S>`,
  then `pointer` denotes the type of that expression.
  Otherwise, `pointer` denotes `void`.

:::

- Edit [common.iter.nav]{.sref} p5 as indicated:

::: itemdecl

```c++
decltype(auto) operator++(int);
```
[4]{.pnum} _Preconditions:_ `holds_­alternative<I>(v_­)`.

[5]{.pnum} _Effects:_ If `I` models `forward_­iterator`, equivalent to:

::: bq
```c++
common_iterator tmp = *this;
++*this;
return tmp;
```
:::

Otherwise, [if `requires (I& i) { { *i++ } -> @_can-reference_@; }` is `true` or
`constructible_from<iter_value_t<I>, iter_reference_t<I>>` is `false`, ]{.diffins} equivalent to: `return get<I>(v_­)++;`

::: add

Otherwise, equivalent to:

::: bq
```c++
@_postfix-proxy_@ p(**this);
++*this;
return p;
```
:::

where _`postfix-proxy`_ is the exposition-only class:

::: bq
```c++
class @_postfix-proxy_@  {
  iter_value_t<I> keep_;
  @_postfix-proxy_@(iter_reference_t<I>&& x)
    : keep_(std::move(x)) {}
public:
  const iter_value_t<I>& operator*() const {
    return keep_;
  }
};

```
:::
:::
:::

- Edit [iterator.synopsis]{.sref}, Header `<iterator>` synopsis, as indicated:

```c++
#include <compare>              // see [compare.syn]
#include <concepts>             // see [concepts.syn]

namespace std {

  // [...]

  template<input_­iterator I>
    @[requires _see below_]{.diffins}@
  struct iterator_traits<counted_iterator<I>>;

  // [...]
}
```

- Edit the definition of  `iterator_traits<counted_iterator<I>>` in
  [counted.iterator]{.sref} as indicated:

::: draftnote
This resolves [@LWG3408] by only providing an `iterator_traits` specialization
for `counted_iterator` when the underlying iterator does not use the specialization
generated from the primary template. In other words, we should only use the
"custom `iterator_traits`" path when the underlying iterator actually customized
`iterator_traits`.
:::

```c++
   template<input_­iterator I>
     @[requires same_as<*ITER_TRAITS*(I), iterator_traits&lt;I>>   // see [iterator.concepts.general]{.sref}]{.diffins}@
   struct iterator_traits<counted_iterator<I>> : iterator_traits<I> {
     using pointer = void;
   };
```

- Edit [range.iota.iterator]{.sref} as indicated:

::: draftnote

While this member typedef is arguably harmless, we should avoid providing
misleading tags for something that is, in fact, not a C++17 iterator.

:::


```c++
namespace std::ranges {
  template<weakly_­incrementable W, semiregular Bound>
    requires @_weakly-equality-comparable-with_@<W, Bound>
  struct iota_view<W, Bound>::@_iterator_@ {
  private:
    W @*value_*@ = W();             // exposition only
  public:
    using iterator_concept = @_see below_@;
    using iterator_category = input_iterator_tag; @[// present only if W models incrementable]{.diffins}@
    using value_type = W;
    using difference_type = @_IOTA-DIFF-T_(W)@;

    // [...]
  };
}
```

- Edit [range.filter.iterator]{.sref} as indicated:

::: draftnote

All C++20 forward iterators should qualify as C++17 input iterators, and so the
wording expects `​iterator_­category` to be present. It seems unnecessary to
accommodate hypothetical types that artificially define away C++17 iterator-ness.

:::

```c++
namespace std::ranges {
  template<input_­range V, indirect_­unary_­predicate<iterator_t<V>> Pred>
    requires view<V> && is_object_v<Pred>
  class filter_view<V, Pred>::@_iterator_@ {
  private:
    iterator_t<V> @*current_*@ = iterator_t<V>();   // exposition only
    filter_view* @*parent_*@ = nullptr;             // exposition only
  public:
    using iterator_concept  = @_see below_@;
    using iterator_category = @_see below_@;        @[// not always present]{.diffins}@
    using value_type        = range_value_t<V>;
    using difference_type   = range_difference_t<V>;

    // [...]
  };
}
```

[...]

::: dummy

[3]{.pnum} [The member _typedef-name_ `iterator_category` is defined if and only
if `V` models `forward_range`. In that case,]{.diffins}
`@_iterator_@​::​iterator_­category` is defined as follows:

- [3.1]{.pnum} Let `C` denote the type `iterator_­traits<iterator_­t<V>>​::​iterator_­category`.
- [3.2]{.pnum} If `C` models `derived_­from<bidirectional_­iterator_­tag>`, then `iterator_­category` denotes `bidirectional_­iterator_­tag`.
- [3.3]{.pnum} Otherwise, if `C` models `derived_­from<forward_­iterator_­tag>`, then `iterator_­category` denotes `forward_­iterator_­tag`.
- [3.4]{.pnum} Otherwise, `iterator_­category` denotes `C`.

:::

- Edit [range.transform.iterator]{.sref} as indicated:

```c++
namespace std::ranges {
  template<input_­range V, copy_­constructible F>
    requires view<V> && is_object_v<F> &&
             regular_invocable<F&, range_reference_t<V>> &&
             can-reference<invoke_result_t<F&, range_reference_t<V>>>
  template<bool Const>
  class transform_view<V, F>::@_iterator_@ {
  private:
    using @_Parent_@ =                              // exposition only
      conditional_t<Const, const transform_view, transform_view>;
    using @_Base_@   =                              // exposition only
      conditional_t<Const, const V, V>;
    iterator_t<@_Base_@> current_ =                 // exposition only
      iterator_t<@_Base_@>();
    Parent* parent_ = nullptr;                  // exposition only
  public:
    using iterator_concept  = @_see below_@;
    using iterator_category = @_see below_@;        @[// not always present]{.diffins}@
    using value_type        =
      remove_cvref_t<invoke_result_t<F&, range_reference_t<@_Base_@>>>;
    using difference_type   = range_difference_t<@_Base_@>;

    // [...]
  };
}
```

[...]

::: dummy

[2]{.pnum} [The member _typedef-name_ `iterator_category` is defined if and only
if _`Base`_ models `forward_range`. In that case,]{.diffins}
`iterator​::​iterator_­category` is defined as follows:
Let `C` denote the type `iterator_­traits<iterator_­t<@_Base_@>>​::​iterator_­category`.

- [2.1]{.pnum} If `is_­lvalue_­reference_­v<invoke_­result_­t<F&, range_­reference_­t<Base>>>` is `true`, then
  - [2.1.1]{.pnum} if `C` models `derived_­from<contiguous_­iterator_­tag>`, iterator_­category denotes `random_­access_­iterator_­tag`;
  - [2.1.2]{.pnum} otherwise, `iterator_­category` denotes `C`.
- [2.2]{.pnum} Otherwise, `iterator_­category` denotes `input_­iterator_­tag`.

:::


- Edit [range.join.iterator]{.sref} as indicated:

```c++
namespace std::ranges {
  template<input_­range V>
    requires view<V> && input_­range<range_reference_t<V>> &&
             (is_reference_v<range_reference_t<V>> ||
              view<range_value_t<V>>)
  template<bool Const>
  struct join_view<V>::@_iterator_@ {
  private:
    using @_Parent_@ =                                              // exposition only
      conditional_t<Const, const join_view, join_view>;
    using @_Base_@   = conditional_t<Const, const V, V>;            // exposition only

    static constexpr bool ref-is-glvalue =                      // exposition only
      is_reference_v<range_reference_t<@_Base_@>>;

    // [...]

  public:
    using iterator_concept  = @_see below_@;
    using iterator_category = @_see below_@;        @[// not always present]{.diffins}@
    using value_type        = range_value_t<range_reference_t<@_Base_@>>;
    using difference_type   = @_see below_@;

    // [...]
  };
}
```

[...]

::: dummy

[2]{.pnum} [The member _typedef-name_ `iterator_category` is defined if and only
if _`ref-is-glvalue`_ is `true`, _`Base`_ models `forward_range`, and
`range_reference_t<@_Base_@>` models `forward_range`. In that case,]{.diffins}
`iterator​::​iterator_­category` is defined as follows:

- [2.1]{.pnum} Let _OUTERC_ denote `iterator_­traits<iterator_­t<@_Base_@>>​::​iterator_­category`,
  and let _INNERC_ denote `iterator_­traits<iterator_­t<range_­reference_­t<@_Base_@>>>​::​iterator_­category`.
- [2.2]{.pnum} If [_`ref-is-glvalue`_ is `true` and]{.diffdel} _OUTERC_ and _INNERC_ each model `derived_­from<bidirectional_­iterator_­tag>`, `iterator_­category` denotes `bidirectional_­iterator_­tag`.
- [2.3]{.pnum} Otherwise, if [_`ref-is-glvalue`_ is `true` and]{.diffdel} _OUTERC_ and _INNERC_ each model `derived_­from<forward_­iterator_­tag>`, `iterator_­category` denotes `forward_­iterator_­tag`.
- [2.4]{.pnum} Otherwise, [if _OUTERC_ and _INNERC_ each model `derived_­from<input_­iterator_­tag>`,]{.diffdel} `iterator_­category` denotes `input_­iterator_­tag`.
- [2.5]{.pnum} [Otherwise, `iterator_­category` denotes `output_­iterator_­tag`.]{.diffdel}

:::

- Edit [range.split.outer]{.sref} as indicated:

```c++
namespace std::ranges {
  template<input_­range V, forward_­range Pattern>
    requires view<V> && view<Pattern> &&
             indirectly_­comparable<iterator_t<V>, iterator_t<Pattern>, ranges::equal_to> &&
             (forward_­range<V> || @_tiny-range_@<Pattern>)
  template<bool Const>
  struct split_view<V, Pattern>::@_outer-iterator_@ {
  private:
    using @_Parent_@ =                          // exposition only
      conditional_t<Const, const split_view, split_view>;
    using @_Base_@   =                          // exposition only
      conditional_t<Const, const V, V>;

      // [...]
  public:
    using iterator_concept  =
      conditional_t<forward_­range<@_Base_@>, forward_iterator_tag, input_iterator_tag>;
    using iterator_category = input_iterator_tag; @[// present only if _Base_ models forward_range]{.diffins}@

    // [...]
  };
}
```

- Edit [range.split.inner]{.sref} as indicated:

```c++
namespace std::ranges {
  template<input_­range V, forward_­range Pattern>
    requires view<V> && view<Pattern> &&
             indirectly_­comparable<iterator_t<V>, iterator_t<Pattern>, ranges::equal_to> &&
             (forward_­range<V> || @_tiny-range_@<Pattern>)
  template<bool Const>
  struct split_view<V, Pattern>::@_inner-iterator_@ {
  private:
    using @_Base_@ = conditional_t<Const, const V, V>;      // exposition only

    // [...]

  public:
    using iterator_concept  = typename @_outer-iterator_@<Const>::iterator_concept;
    using iterator_category = @_see below_@;               @[// present only if _Base_ models forward_range]{.diffins}@

    // [...]
  };
}
```

[1]{.pnum} The _typedef-name_ `iterator_­category` denotes:

::: dummy

- [1.1]{.pnum} `forward_­iterator_­tag` if `iterator_­traits<iterator_­t<@_Base_@>>​::​iterator_­category` models
`derived_­from<forward_­iterator_­tag>`;
- [1.2]{.pnum} otherwise, `iterator_­traits<iterator_­t<<@_Base_@>>​::​iterator_­category`.

:::

- Edit [range.elements.iterator]{.sref} as indicated:

```c++
namespace std::ranges {
  template<input_range V, size_t N>
    requires view<V> && @_has-tuple-element_@<range_value_t<V>, N> &&
             @_has-tuple-element_@<remove_reference_t<range_reference_t<V>>, N>
  template<bool Const>
  class elements_view<V, N>::@_iterator_@ {                 // exposition only
    using @_Base_@ = conditional_t<Const, const V, V>;      // exposition only

    iterator_t<@_Base_@> current_ = iterator_t<@_Base_@>();
  public:
    using iterator_category = @[typename iterator_traits<iterator_t<_Base_>>::iterator_category]{.diffdel}[_see below_]{.diffins};  [// not always present]{.diffins}@
    using value_type = remove_cvref_t<tuple_element_t<N, range_value_t<@_Base_@>>>;
    using difference_type = range_difference_t<@_Base_@>;

    // [...]
  };
}
```

::: add

[?]{.pnum} The member _typedef-name_ `iterator_category` is defined if and only
if _`Base`_ models `forward_range`. In that case, `iterator_category` denotes:

- [?.1]{.pnum} `input_iterator_tag` if `get<N>(*@*current_*@)` is an rvalue;
- [?.2]{.pnum} otherwise, `iterator_traits<iterator_t<@_Base_@>>::iterator_category`.
:::

:::
