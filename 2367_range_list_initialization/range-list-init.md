---
title: "Remove misuses of list-initialization from Clause 24"
document: D2367R0
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Abstract
This paper provides wording for [@LWG3524] and resolves related issues caused by
the erroneous use of list-initialization in ranges wording.

# Discussion

As discussed in [@LWG3524], the use of list-initialization in the ranges
specification implies ordering guarantees that are unintended and unimplementable
in ordinary C++, as well as narrowing checks that are unnecessary and sometimes
unimplementable.

Other issues have also been reported against the misuse of list-initialization in
ranges wording. See [@subrange] and [@take.view].

The approach taken in this paper is to remove uses of list-initialization that
are actively harmful, as well as any neighboring uses to maintain some level of
local consistency. I have not attempted to remove all uses of list-initialization
in the normative text of Clause 24.

During the drafting of this paper, two issues were discovered with `views::single`:

- The implicit deduction guides fail to remove cv-qualification for const rvalues or decay array/function types.
  This is inconsistent with range-v3 and appears to be an oversight.
- `views::single(a_single_view)` unexpectedly copies instead of wraps, similar to [@LWG3474].

The proposed wording below fixes these issues as well.

# Wording

This wording is relative to [@N4885].

::: wordinglist

- Edit [range.subrange.ctor]{.sref} p6 as indicated:

:::itemdecl

```cpp
template<@_not-same-as_@<subrange> R>
  requires borrowed_range<R> &&
           @_convertible-to-non-slicing_@<iterator_t<R>, I> &&
           convertible_to<sentinel_t<R>, S>
constexpr subrange(R&& r) requires (!@_StoreSize_@ || sized_range<R>);
```

[6]{.pnum} Effects: Equivalent to:

- [6.1]{.pnum} If _`StoreSize`_ is `true`, `subrange@[\{]{.diffdel}[\(]{.diffins}@r, ranges::size(r)@[\}]{.diffdel}[\)]{.diffins}@`.
- [6.2]{.pnum} Otherwise, `subrange@[\{]{.diffdel}[\(]{.diffins}@ranges::begin(r), ranges::end(r)@[\}]{.diffdel}[\)]{.diffins}@`.

:::

- Edit [range.single.overview]{.sref} p2 as indicated:

[2]{.pnum} The name `views::single` denotes a customization point object
([customization.point.object]{.sref}). Given a subexpression `E`,
the expression `views::single(E)` is expression-equivalent to
`single_view@[<decay_t<decltype((E))>>]{.diffins}[\{]{.diffdel}[\(]{.diffins}@E@[\}]{.diffdel}[\)]{.diffins}@`.

- Add a deduction guide to [range.single.view]{.sref}:

```diff
 namespace std::ranges {
   template<copy_constructible T>
     requires is_object_v<T>
   class single_view : public view_interface<single_view<T>> {
     // [...]
   };

+  template<class T>
+    single_view(T) -> single_view<T>;
 }
```

- Edit [range.iota.overview]{.sref} p2 as indicated:

[2]{.pnum} The name `views::iota` denotes a customization point object
([customization.point.object]{.sref}). Given subexpressions `E` and `F`,
the expressions `views::iota(E)` and `views::iota(E, F)` are expression-equivalent
to `iota_view@[\{]{.diffdel}[\(]{.diffins}@E@[\}]{.diffdel}[\)]{.diffins}@` and
`iota_view@[\{]{.diffdel}[\(]{.diffins}@E, F@[\}]{.diffdel}[\)]{.diffins}@`, respectively.

- Edit [range.filter.overview]{.sref} p2 as indicated:

[2]{.pnum} The name `views::filter` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given subexpressions `E` and `P`, the expression
`views::filter(E, P)` is expression-equivalent to
`filter_view@[\{]{.diffdel}[\(]{.diffins}@E, P@[\}]{.diffdel}[\)]{.diffins}@`.

- Edit [range.transform.overview]{.sref} p2 as indicated:

[2]{.pnum} The name `views::transform` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given subexpressions `E` and `F`, the expression
`views::transform(E, F)` is expression-equivalent to
`transform_view@[\{]{.diffdel}[\(]{.diffins}@E, F@[\}]{.diffdel}[\)]{.diffins}@`.

- Edit [range.take.overview]{.sref} p2 as indicated:

::: dummy

[2]{.pnum} The name `views::take` denotes a range adaptor object ([range.adaptor.object]{.sref}).
Let `E` and `F` be expressions, let `T` be `remove_cvref_t<decltype((E))>`,
and let `D` be` range_difference_t<decltype((E))>`. If` decltype((F))` does not
model `convertible_to<D>`, `views::take(E, F)` is ill-formed. Otherwise, the
expression `views::take(E, F)` is expression-equivalent to:

- [2.1]{.pnum} If T is a specialization of `ranges::empty_view` ([range.empty.view]),
  then `((void) F, @_decay-copy_@(E))`[, except that the evaluation of `E` and `F`
  are indeterminately sequenced]{.diffins}.
- [2.2]{.pnum} Otherwise, if `T` models `random_access_range` and `sized_range` and is
  - [2.2.1]{.pnum} [...]

  then `T@[\{]{.diffdel}[\(]{.diffins}@ranges::begin(E), ranges::begin(E) + min<D>(ranges::size(E), F)@[\}]{.diffdel}[\)]{.diffins}@`, except that `E` is evaluated only once.

- [2.3]{.pnum} Otherwise, `ranges::take_view@[\{]{.diffdel}[\(]{.diffins}@E, F@[\}]{.diffdel}[\)]{.diffins}@`.

:::

- Edit [range.take.view]{.sref} as indicated:

```cpp
namespace std::ranges {
  template<view V>
  class take_view : public view_interface<take_view<V>> {

    // [...]

    constexpr auto begin() requires (!simple-view<V>) {
      if constexpr (sized_range<V>) {
        if constexpr (random_access_range<V>)
          return ranges::begin(@_base\__@);
        else {
          auto sz = size();
          return counted_iterator@[\{]{.diffdel}[\(]{.diffins}@ranges::begin(@_base\__@), sz@[\}]{.diffdel}[\)]{.diffins}@;
        }
      } else
        return counted_iterator@[\{]{.diffdel}[\(]{.diffins}@ranges::begin(@_base\__@), @_count\__[\}]{.diffdel}[\)]{.diffins}@;
    }

    constexpr auto begin() const requires range<const V> {
      if constexpr (sized_range<const V>) {
        if constexpr (random_access_range<const V>)
          return ranges::begin(@_base\__@);
        else {
          auto sz = size();
          return counted_iterator@[\{]{.diffdel}[\(]{.diffins}@ranges::begin(@_base\__@), sz@[\}]{.diffdel}[\)]{.diffins}@;
        }
      } else
        return counted_iterator@[\{]{.diffdel}[\(]{.diffins}@ranges::begin(@_base\__@), @_count\__[\}]{.diffdel}[\)]{.diffins}@;
    }

    // [...]
  };

  template<class R>
    take_view(R&&, range_difference_t<R>)
      -> take_view<views::all_t<R>>;
}
```

- Edit [range.take.while.overview]{.sref} p2 as indicated:

[2]{.pnum} The name `views::take_while` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given subexpressions `E` and `F`, the expression
`views::take_while(E, F)` is expression-equivalent to
`take_while_view@[\{]{.diffdel}[\(]{.diffins}@E, F@[\}]{.diffdel}[\)]{.diffins}@`.

- Edit [range.drop.overview]{.sref} p2 as indicated:

::: dummy

[2]{.pnum} The name `views::drop` denotes a range adaptor object ([range.adaptor.object]{.sref}).
Let `E` and `F` be expressions, let `T` be `remove_cvref_t<decltype((E))>`,
and let `D` be` range_difference_t<decltype((E))>`. If` decltype((F))` does not
model `convertible_to<D>`, `views::drop(E, F)` is ill-formed. Otherwise, the
expression `views::drop(E, F)` is expression-equivalent to:

- [2.1]{.pnum} If T is a specialization of `ranges::empty_view` ([range.empty.view]),
  then `((void) F, @_decay-copy_@(E))`[, except that the evaluation of `E` and `F`
  are indeterminately sequenced]{.diffins}.
- [2.2]{.pnum} Otherwise, if `T` models `random_access_range` and `sized_range` and is
  - [2.2.1]{.pnum} [...]

  then `T@[\{]{.diffdel}[\(]{.diffins}@ranges::begin(E) + min<D>(ranges::size(E), F), ranges::end(E)@[\}]{.diffdel}[\)]{.diffins}@`, except that `E` is evaluated only once.

- [2.3]{.pnum} Otherwise, `ranges::drop_view@[\{]{.diffdel}[\(]{.diffins}@E, F@[\}]{.diffdel}[\)]{.diffins}@`.

:::

- Edit [range.drop.while.overview]{.sref} p2 as indicated:

[2]{.pnum} The name `views::drop_while` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given subexpressions `E` and `F`, the expression
`views::drop_while(E, F)` is expression-equivalent to
`drop_while_view@[\{]{.diffdel}[\(]{.diffins}@E, F@[\}]{.diffdel}[\)]{.diffins}@`.

- Edit [range.split.overview]{.sref} p2 as indicated:

[2]{.pnum} The name `views::split` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given subexpressions `E` and `F`, the expression
`views::split(E, F)` is expression-equivalent to
`split_view@[\{]{.diffdel}[\(]{.diffins}@E, F@[\}]{.diffdel}[\)]{.diffins}@`.

- Edit [range.split.view]{.sref} p2 as indicated:

:::itemdecl
```cpp
template<input_range R>
  requires constructible_from<V, views::all_t<R>> &&
           constructible_from<Pattern, single_view<range_value_t<R>>>
constexpr split_view(R&& r, range_value_t<R> e);
```

[2]{.pnum} _Effects_: Initializes _`base_`_ with `views::all(std::forward<R>(r))`,
and _`pattern_`_ with [`single_view{std::move(e)}`]{.diffdel} [`views::single(std::move(e))`]{.diffins}.

:::

- Edit [range.counted]{.sref} p2 as indicated:

::: dummy

[2]{.pnum} The name `views::counted` denotes a customization point object ([customization.point.object]{.sref}).
Let `E` and `F` be expressions, let `T` be `decay_t<decltype((E))>`,
and let `D` be` iter_difference_t<T>`. If` decltype((F))` does not
model `convertible_to<D>`, `views::counted(E, F)` is ill-formed.

[This case can result in substitution failure when `views::counted(E, F)` appears in the immediate context of a template instantiation.]{.note1}

Otherwise, `views::counted(E, F)` is expression-equivalent to:

- [2.1]{.pnum} If `T` models `contiguous_iterator`, then `span@[\{]{.diffdel}[\(]{.diffins}@to_address(E), static_cast<D>(F)@[\}]{.diffdel}[\)]{.diffins}@`.
- [2.2]{.pnum} Otherwise, if `T` models `random_access_iterator`, then `subrange@[\{]{.diffdel}[\(]{.diffins}@E, E + static_cast<D>(F)@[\}]{.diffdel}[\)]{.diffins}@`, except that `E` is evaluated only once.
- [2.3]{.pnum} Otherwise, `subrange@[\{]{.diffdel}[\(]{.diffins}@counted_iterator@[\{]{.diffdel}[\(]{.diffins}@E, F@[\}]{.diffdel}[\)]{.diffins}@, default_sentinel@[\}]{.diffdel}[\)]{.diffins}@`.

:::

:::

---
references:
    - id: subrange
      citation-label: subrange
      title: "Yet Another Braced Init Bug"
      author:
        - family: Jonathan Wakely
      issued:
        year: 2020
      URL: https://lists.isocpp.org/lib/2020/10/17806.php
    - id: take.view
      citation-label: take.view
      title: "Fix error in `take_view::begin` by casting to the appropriate size"
      author:
        - family: Michael Schellenberger Costa
      issued:
        year: 2021
      URL: https://github.com/microsoft/STL/pull/1844
---
