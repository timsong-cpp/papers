---
title: "`views::to_input`"
document: P3137R1
date: today
audience:
  - SG9
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Abstract

This paper proposes the `views::to_input` adaptor that downgrades a source
range to an input-only, non-common range.

# Revision history

- R1: Added `operator-` for `sized_sentinel_for` cases per SG9 feedback. Added
  additional discussion on the feasibility of splitting this adaptor.

# Motivation

The motivation for this view is given in [@P2760R1] and quoted below for
convenience (with the name changed from `as_input` to `to_input`; see the naming
discussion below):

::: bq

Why would anybody want such a thing? Performance.

Range adaptors typically provide the maximum possible iterator category -
in order to maximize functionality. But sometimes it takes work to do so.
A few examples:

* `views::join(r)` is common when `r` is, which means it provides two iterators.
The iterator comparison for `join` does [two iterator comparisons](https://eel.is/c++draft/range.join#iterator-18),
for both the outer and the inner iterator, which is definitely necessary when
comparing two iterators. But if all you want to do is compare `it == end`, you
could've gotten away with [one iterator comparison](https://eel.is/c++draft/range.join#sentinel-3).
As such, iterating over a common `join_view` is more expensive than an uncommon one.
* `views::chunk(r, n)` has a different algorithm for input vs forward. For
forward+, you get a range of `views::take(n)` - if you iterate through every
element, then advancing from one chunk to the next chunk requires iterating
through all the elements of that chunk again. For input, you can only advance
element at a time.

The added cost that `views::chunk` adds when consuming all elements for forward+
can be necessary if you need the forward iterator guarantees. But if you don't
need it, like if you're just going to consume all the elements in order one time.
Or, worse, the next adaptor in the chain reduces you down to input anyway, this
is unnecessary.

In this way, `r | views::chunk(n) | views::join` can be particularly bad,
since you're paying additional cost for `chunk` that you can't use anyway,
since `views::join` here would always be an input range.
`r | views::to_input | views::chunk(n) | views::join` would alleviate this
problem. It would be a particularly nice way to alleviate this problem if users
didn't have to write the `views::to_input` part!

This situation was originally noted in [@range-v3#704].

:::

During the SG9 discussion, it was also pointed out that adaptors on
input-only views never need to cache `begin()` as that can be called only
once, which can reduce the space overhead of view pipelines in certain
constrained environments when that is not needed.

# Design

## One adaptor, not two

During the 2024-03-19 SG9 review, the room voted 1/5/7/0/0 in favor of suggestion
to split this adaptor into two pieces: one for demoting-to-input and one for
make-uncommon, principally on the basis that uses of the two can have distinct
rationales and so can benefit from separate annotations.

This direction does not appear viable, however, because the demote-to-input adaptor
should have a move-only iterator to discourage misuse. That means that it _cannot_
be common because sentinels are required to be semiregular. Losing the opportuntity
to diagnose misuses at compile-time does not appear to this author to be worth
the marginal benefit in encouraging annotation.

While a separate make-uncommon adaptor is possible, this paper doesn't propose it;
the performance benefit from that change alone may not justify a separate adaptor in
in the standard.

## Naming

P2760R1 proposes `as_input`, but the two `as_@_meow_@` views we have (`as_const`
and `as_rvalue`) are element-wise operations rather than operations on the view
itself. So this paper proposes the name `to_input`.

## Properties

`to_input` is conditionally borrowed, input-only (that's its whole point),
non-common, and conditionally const-iterable. As usual, wrapping is avoided if
possible. The iterator only provides the minimal interface needed for an input
iterator.

## Additional operations?
In theory, we could provide all the operations supported by the underlying
iterator, and limit our change to the iterator concept. Such operations would be
unlikely to see much use: `to_input` is a facility for influencing generic
algorithms, and generic algorithms generally have to rely on the concept to
determine if an operation can be used. So we do not try to do so here.

# Wording

This wording is relative to [@N4971].

## Addition to `<ranges>`

Add the following to [ranges.syn]{.sref}, header `<ranges>` synopsis:

```cpp
// [...]
namespace std::ranges {
  // [...]

  // [range.to.input], to input view
  template<input_range V>
    requires view<V>
  class to_input_view;

  template<class V>
  constexpr bool enable_borrowed_range<to_input_view<V>> =
      enable_borrowed_range<V>;

  namespace views {
    inline constexpr $unspecified$ to_input = $unspecified$;
  }

}

```

## `to_input`

Add the following subclause to [range.adaptors]{.sref}:

### 26.7.? To input view [range.to.input] {-}

#### 26.7.?.1 Overview [range.to.input.overview] {-}

[#]{.pnum} `to_input_view` presents a view of an underlying sequence as an
input-only non-common range. [This is useful to avoid overhead that may
be necessary to provide support for the operations needed for greater iterator
strength.]{.note}

[#]{.pnum} The name `views::to_input` denotes a range adaptor object ([range.adaptor.object]{.sref}).
Let `E` be an expression and let `T` be `decltype((E))`.
The expression `views​::to_input(E)` is expression-equivalent to:

- [#.#]{.pnum} `views​::​all(E)` if `T` models `input_range`, does not model `common_range`, and does not model `forward_range`;
- [#.#]{.pnum} Otherwise, `to_input_view(E)`.

#### 26.7.?.2 Class template `to_input_view` [range.to.input.view] {-}

```cpp
template<input_range V>
  requires view<V>
class to_input_view : public view_interface<to_input_view<V>>{
  V $base_$ = V();                          // exposition only

  template<bool Const>
  class $iterator$;                         // exposition only

public:
  to_input_view() requires default_initializable<V> = default;
  constexpr explicit to_input_view(V base);

  constexpr V base() const & requires copy_constructible<V> { return $base_$; }
  constexpr V base() && { return std::move($base_$); }

  constexpr auto begin() requires (!$simple-view$<V>);
  constexpr auto begin() const requires range<const V>;

  constexpr auto end() requires (!$simple-view$<V>);
  constexpr auto end() const requires range<const V>;

  constexpr auto size() requires sized_range<V>;
  constexpr auto size() const requires sized_range<const V>;
};

template<class R>
  to_input_view(R&&) -> to_input_view<views::all_t<R>>;

```

::: itemdecl

```cpp
constexpr explicit to_input_view(V base);
```

[#]{.pnum} _Effects_: Initializes `$base_$` with  `std::move(base)`.

```cpp
constexpr auto begin() requires (!$simple-view$<V>);
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
return $iterator$<false>(ranges::begin($base_$));
```
:::

```cpp
constexpr auto begin() const requires range<const V>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
return $iterator$<true>(ranges::begin($base_$));
```
:::

```cpp
constexpr auto end() requires (!$simple-view$<V>);
constexpr auto end() const requires range<const V>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
return ranges::end($base_$);
```
:::


```cpp
constexpr auto size() requires sized_range<V>;
constexpr auto size() const requires sized_range<const V>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
return ranges::size($base_$);
```
:::

:::

#### 26.7.?.3 Class template `to_input_view::$iterator$` [range.to.input.iterator] {-}

```cpp
namespace std::ranges {
  template<input_range V>
    requires view<V>
  template<bool Const>
  class to_input_view<V>::$iterator$ {
    using $Base$ = $maybe-const$<Const, V>;                           // exposition only

    iterator_t<$Base$> $current_$ = iterator_t<$Base$>();               // exposition only

    constexpr explicit $iterator$(iterator_t<$Base$> current);        // exposition only

  public:
    using difference_type = range_difference_t<$Base$>;
    using value_type = range_value_t<$Base$>;
    using iterator_concept = input_iterator_tag;

    $iterator$() requires default_initializable<iterator_t<$Base$>> = default;

    $iterator$($iterator$&&) = default;
    $iterator$& operator=($iterator$&&) = default;

    constexpr $iterator$($iterator$<!Const> i)
      requires Const && convertible_to<iterator_t<V>, iterator_t<$Base$>>;

    constexpr iterator_t<$Base$> base() &&;
    constexpr const iterator_t<$Base$>& base() const & noexcept;

    constexpr decltype(auto) operator*() const { return *$current_$; }

    constexpr $iterator$& operator++();
    constexpr void operator++(int);

    friend constexpr bool operator==(const $iterator$& x, const sentinel_t<$Base$>& y);

    friend constexpr difference_type operator-(const sentinel_t<$Base$>& y, const $iterator$& x)
      requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;
    friend constexpr difference_type operator-(const $iterator$& x, const sentinel_t<$Base$>& y)
      requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;

    friend constexpr range_rvalue_reference_t<$Base$> iter_move(const $iterator$& i)
      noexcept(noexcept(ranges::iter_move(i.$current_$)));

    friend constexpr void iter_swap(const $iterator$& x, const $iterator$& y)
      noexcept(noexcept(ranges::iter_swap(x.$current_$, y.$current_$)))
      requires indirectly_swappable<iterator_t<$Base$>>;
  };
}
```

::: itemdecl

```cpp
constexpr explicit $iterator$(iterator_t<$Base$> current);
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `std::move(current)`.

```cpp
constexpr $iterator$($iterator$<!Const> i)
  requires Const && convertible_to<iterator_t<V>, iterator_t<$Base$>>;
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `std::move(i.$current_$)`.

```cpp
constexpr iterator_t<$Base$> base() &&;
```
[#]{.pnum} _Returns_: `std::move($current_$)`.

```cpp
constexpr const iterator_t<$Base$>& base() const & noexcept;
```
[#]{.pnum} _Returns_: `$current_$`.

```cpp
constexpr $iterator$& operator++();
```

[#]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
   ++$current_$;
   return *this;
```
:::

```cpp
constexpr void operator++(int);
```

[#]{.pnum} _Effects_: Equivalent to: `++*this;`


```cpp
friend constexpr bool operator==(const $iterator$& x, const sentinel_t<$Base$>& y);
```

[#]{.pnum} _Returns:_ `x.$current_$ == y`.

```cpp
friend constexpr difference_type operator-(const sentinel_t<$Base$>& y, const $iterator$& x)
  requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;
```

[#]{.pnum} _Returns:_ `y - x.$current_$`.

```cpp
friend constexpr difference_type operator-(const $iterator$& x, const sentinel_t<$Base$>& y)
      requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;
```

[#]{.pnum} _Returns:_ `x.$current_$ - y`.

```cpp
friend constexpr range_rvalue_reference_t<$Base$> iter_move(const $iterator$& i)
  noexcept(noexcept(ranges::iter_move(i.$current_$)));
```

[#]{.pnum} _Effects_: Equivalent to: `return ranges::iter_move(i.$current_$);`

```cpp
friend constexpr void iter_swap(const $iterator$& x, const $iterator$& y)
  noexcept(noexcept(ranges::iter_swap(x.$current_$, y.$current_$)))
  requires indirectly_swappable<iterator_t<$Base$>>;
```

[#]{.pnum} _Effects_: Equivalent to: `ranges::iter_swap(x.$current_$, y.$current_$);`

:::

## Feature-test macro

Add the following macro definition to [version.syn]{.sref}, header `<version>`
synopsis, with the value selected by the editor to reflect the date of adoption
of this paper:

```cpp
#define __cpp_lib_ranges_to_input 20XXXXL // also in <ranges>
```

---
references:
    - id: range-v3#704
      citation-label: range-v3#704
      title: Demand-driven view strength weakening
      author:
        - family: Eric Niebler
      issued:
        year: 2017
      URL: https://github.com/ericniebler/range-v3/issues/704
---
