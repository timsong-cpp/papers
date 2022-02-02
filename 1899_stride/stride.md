---
title: "`stride_view`"
document: P1899R2
date: today
audience:
  - SG9
  - LEWG
author:
  - name: Christopher Di Bella
    email: <cjdb.ns@gmail.com>
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: true
---

# Abstract

The ability to use algorithms over an evenly-spaced subset of a range has been missed in the STL for
a quarter of a century. Given that there's no way to compose a strided range adaptor in C++20, this
should be adopted for C++23.

# Revision history

## R2

* Rewrite wording to match `chunk` from [@P2442R1].

## R1

* PDF -> HTML.
* Adds a section discussing the design.
* Adds feature-test macro.
* Cleans up some stuff that was ported in from the implementation by mistake.
* Adds `iterator_concept`, and corrects `iterator_category` so it can't be contiguous.
* Fixes calls to _`compute-distace`_ so they pass in size of underlying range instead of themselves.
* Adds precondition to ensure stride is positive.
* Makes multi-arg constructors non-explicit.

## R0

Initial revision.

# Motivation

The ability to use algorithms over an evenly-spaced subset of a range has been missed in the STL for
a quarter of a century. This is, in part, due to the complexity required to use an iterator that can
safely describe such a range. It also means that the following examples cannot be transformed from
raw loops into algorithms, due to a lacking iterator.

```cpp
namespace stdr = std::ranges;
namespace stdv = std::views;

for (auto i = 0; i < ssize(v); i += 2) {
  v[i] = 42; // fill
}

for (auto i = 0; i < ssize(v); i += 3) {
  v[i] = f(); // transform
}

for (auto i = 0; i < ssize(v); i += 3) {
  for (auto j = i; j < ssize(v); i += 3) {
    if (v[j] < v[i]) {
      stdr::swap(v[i], v[j]); // selection sort, but hopefully the idea is conveyed
    }
  }
}
```

Boost.Range 2.0 introduced a range adaptor called `strided`, and range-v3's equivalent is
`stride_view`, both of which make striding far easier than when using iterators:

```cpp
stdr::fill(v | stdv::stride(2), 42);

auto strided_v = v | stdv::stride(3);
stdr::transform(strided_v, stdr::begin(strided_v) f);

stdr::stable_sort(strided_v); // order restored!
```

Given that there's no way to compose a strided range adaptor in C++20, this should be one of the
earliest range adaptors put into C++23.

## Risk of not having `stride_view`

Although it isn't possible to compose `stride_view` in C++20, someone inexperienced with the ranges
design space might mistake `filter_view` as a suitable way to "compose" `stride_view`:

```cpp
auto bad_stride = [](auto const step) {
  return views::filter([n = 0, step](auto&&) mutable {
    return n++ % step == 0;
  });
};
```

This implementation is broken for two reasons:

1. `filter_view` expects a `predicate` as its input, but the lambda we have provided does not model
   `predicate` (a call to `invoke` on a `predicate` mustn't modify the function object, yet we
   clearly are).
2. The lambda provided doesn't account for moving backward, so despite _satisfying_
   `bidirectional_iterator`, it does not model the concept, thus rendering any program containing it
   ill-formed, with no diagnostic being required.

For these reasons, the author regrets not proposing this in the C++20 design space.

# Implementation experience

Both Boost.Range 2.0 and range-v3 are popular ranges libraries that support a striding range
adaptor. The proposed wording has mostly been implemented in cmcstl2 and in a CppCon main session.

# Design notes

## Preconditions

Boost.Range 2.0's `strided` has a precondition that `0 <= n`, but this isn't strong enough: we need
`n` to be _positive_.

The stride needs to be positive since a negative stride doesn't really make sense, and a semantic
requirement of `std::weakly_incrementable` ([iterator.concept.winc]{.sref}) is that incrementing
actually moves the iterator to the next element: this means a zero-stride isn't allowed either.

LEWG unanimously agreed that this was the correct decision in Prague.

## Complex iteration model

A simple implementation of `stride_view` would be similar to what's in Boost.Range 2.0: a single-pass
range adaptor. With some effort, we can go all the way to a random-access range adaptor, which is
what this section mainly covers.

A naive random-access range adaptor would be implemented by simply moving the iterator forward or
backward by `n` positions (where `n` is the stride length). While this produce a correct iterator
when moving forward, its `operator--` will be incorrect whenever `n` doesn't evenly divide the
underlying range's length. For example:

```cpp
auto x = std::vector{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11};

// prints 0 3 6 9
stdr::copy(stdv::stride(x, 3), std::ostream_iterator<int>(std::cout, " "));

// prints 9 6 3 0
stdr::copy(stdv::stride(x, 3) | stdv::reverse, std::ostream_iterator<int>(std::cout, " "));

auto y = std::vector{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

// prints 0 3 6 9
stdr::copy(stdv::stride(y, 3), std::ostream_iterator<int>(std::cout, " "));

// prints 8 5 2: not the same range in reverse!?
stdr::copy(stdv::stride(y, 3) | stdv::reverse, std::ostream_iterator<int>(std::cout, " "));
```

The problem here is that going from the one-before-past-the-end iterator to the
past-the-end iterator may involve iterating fewer than `stride` steps, so to
correctly iterate backwards, we need to know that distance.

This is the same problem as `chunk` ([@P2442R1]) and can be solved in the same
way. After all, `stride(n)` is basically a more efficient version of
`chunk(n) | transform(ranges::front)` (if we actually had a `ranges::front`).

## Properties

`stride_view` is borrowed if the underlying view is. It is a common range if
the underlying range is common and either sized or non-bidirectional.

# Proposed wording

## Addition to `<ranges>`

Add the following to [ranges.syn]{.sref}, header `<ranges>` synopsis:

```cpp

// [...]
namespace std::ranges {
  // [...]

  // [range.stride], stride view
  template<input_range V>
    requires view<V>
  class stride_view;

  template<class V>
    inline constexpr bool enable_borrowed_range<stride_view<V>> =
      enable_borrowed_range<V>;

  namespace views { inline constexpr $unspecified$ stride = $unspecified$; }

  // [...]
}
```

## `stride`

Add the following subclause to [range.adaptors]{.sref}.

[This wording assumes the exposition-only `$div-ceil$` function template introduced in
[@P2442R1].]{.ednote}

### 24.7.? Stride view [range.stride] {-}

#### 24.7.?.1 Overview [range.stride.overview] {-}

[#]{.pnum} `stride_view` presents a view of an underlying sequence, advancing over `n` elements at a
time, as opposed to the usual single-step succession.

[#]{.pnum} The name `views::stride` denotes a range adaptor object [range.adaptor.object]{.sref}.
Given subexpressions `E` and `N`, the expression `views::stride(E, N)` is expression-equivalent to
`stride_view(E, N)`.

[#]{.pnum} [_Example_:
```cpp
auto input = views::iota(0, 12) | views::stride(3);
ranges::copy(input, ostream_iterator<int>(cout, " ")); // prints 0 3 6 9
ranges::copy(input | views::reverse, ostream_iterator<int>(cout, " ")); // prints 9 6 3 0
```
--- _end example_]

#### 24.7.?.2 Class template `stride_view` [range.stride.view]  {-}

```cpp
namespace std::ranges {
  template<input_range V>
    requires view<V>
  class stride_view : public view_interface<stride_view<V>> {
    V $base_$ = V();                           // exposition only
    range_difference_t<V> $stride_$ = 1;       // exposition only
    template<bool> class $iterator$;           // exposition only
  public:
    stride_view() requires default_initializable<V> = default;
    constexpr explicit stride_view(V base, range_difference_t<V> stride);

    constexpr V base() const& requires copy_constructible<V> { return $base_$; }
    constexpr V base() && { return std::move($base_$); }

    constexpr range_difference_t<V> stride() const noexcept;

    constexpr auto begin() requires (!$simple-view$<V>) {
      return $iterator$<false>(this, ranges::begin($base_$));
    }

    constexpr auto begin() const requires range<const V> {
      return $iterator$<true>(this, ranges::begin($base_$));
    }

    constexpr auto end() requires (!$simple-view$<V>) {
      if constexpr (common_range<V> && sized_range<V> && forward_range<V>) {
        auto missing = ($stride_$ - ranges::distance($base_$) % $stride_$) % $stride_$;
        return $iterator$<false>(this, ranges::end($base_$), missing);
      }
      else if constexpr (common_range<V> && !bidirectional_range<V>) {
        return $iterator$<false>(this, ranges::end($base_$));
      }
      else {
        return default_sentinel;
      }
    }

    constexpr auto end() const requires range<const V> {
      if constexpr (common_range<const V> && sized_range<const V> && forward_range<const V>) {
        auto missing = ($stride_$ - ranges::distance($base_$) % $stride_$) % $stride_$;
        return $iterator$<true>(this, ranges::end($base_$), missing);
      }
      else if constexpr (common_range<const V> && !bidirectional_range<const V>) {
        return $iterator$<true>(this, ranges::end($base_$));
      }
      else {
        return default_sentinel;
      }
    }

    constexpr auto size() requires sized_range<V>;
    constexpr auto size() const requires sized_range<const V>;
  };

  template<class R>
    stride_view(R&&, range_difference_t<R>) -> stride_view<views::all_t<R>>;
}
```

[`end()` cannot compute `missing` for input-only ranges because `ranges::size`
(and `ranges::distance` by extension) is not required to be valid after `ranges::begin`
is called, but `end()` must remain callable.]{.draftnote}

::: itemdecl

```cpp
constexpr stride_view(V base, range_difference_t<V> stride);
```

[#]{.pnum} _Preconditions_: `stride > 0` is `true`.

[#]{.pnum} _Effects_: Initializes `$base_$` with  `std::move(base)` and `$stride_$` with `stride`.

```cpp
constexpr range_difference_t<V> stride() const;
```

[#]{.pnum} _Returns_: `$stride_$`.

```cpp
constexpr auto size() requires sized_range<V>;
constexpr auto size() const requires sized_range<const V>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
return $to-unsigned-like$($div-ceil$(ranges::distance($base_$), $stride_$));
```
:::
:::

#### 24.7.?.3 Class template `stride_view::$iterator$` [range.stride.iterator] {-}

```cpp
namespace std::ranges {
  template<input_range V>
    requires view<V>
  template<bool Const>
  class stride_view<V>::$iterator$ {
    using $Parent$ = $maybe-const$<Const, chunk_view>;                // exposition only
    using $Base$ = $maybe-const$<Const, V>;                           // exposition only

    iterator_t<$Base$> $current_$ = iterator_t<$Base$>();               // exposition only
    sentinel_t<$Base$> $end_$ = sentinel_t<$Base$>();                   // exposition only
    range_difference_t<$Base$> $stride_$ = 0;                         // exposition only
    range_difference_t<$Base$> $missing_$ = 0;                        // exposition only

    constexpr $iterator$($Parent$* parent, iterator_t<$Base$> current,  // exposition only
                       range_difference_t<$Base$> missing = 0);
  public:
    using difference_type = range_difference_t<$Base$>;
    using value_type = range_value_t<$Base$>;
    using iterator_concept = $see below$;
    using iterator_category = $see below$; // not always present

    $iterator$() requires default_initializable<iterator_t<$Base$>>= default;

    constexpr $iterator$($iterator$<!Const> other)
      requires Const && convertible_to<iterator_t<V>, iterator_t<$Base$>>
                     && convertible_to<sentinel_t<V>, sentinel_t<$Base$>>;

    constexpr iterator_t<$Base$> base() &&;
    constexpr const iterator_t<$Base$>& base() const & noexcept;

    constexpr decltype(auto) operator*() const { return *$current_$; }

    constexpr $iterator$& operator++();

    constexpr void operator++(int);
    constexpr $iterator$ operator++(int) requires forward_range<$Base$>;

    constexpr $iterator$& operator--() requires bidirectional_range<$Base$>;
    constexpr $iterator$ operator--(int) requires bidirectional_range<$Base$>;

    constexpr $iterator$& operator+=(difference_type n) requires random_access_range<$Base$>;
    constexpr $iterator$& operator-=(difference_type n) requires random_access_range<$Base$>;

    constexpr decltype(auto) operator[](difference_type n) const
      requires random_access_range<$Base$>
    { return *(*this + n); }

    friend constexpr bool operator==(const $iterator$& x, default_sentinel);

    friend constexpr bool operator==(const $iterator$& x, const $iterator$& y)
      requires equality_comparable<iterator_t<$Base$>>;

    friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;

    friend constexpr bool operator>(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;

    friend constexpr bool operator<=(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;

    friend constexpr bool operator>=(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;

    friend constexpr auto operator<=>(const $iterator$& x, const $iterator$& y)
        requires random_access_range<$Base$> && three_way_comparable<iterator_t<$Base$>>;

    friend constexpr $iterator$& operator+(const $iterator$& x, difference_type n)
      requires random_access_range<$Base$>;
    friend constexpr $iterator$& operator+(difference_type n, const $iterator$& x)
      requires random_access_range<$Base$>;
    friend constexpr $iterator$& operator-(const $iterator$& x, difference_type n)
      requires random_access_range<$Base$>;
    friend constexpr difference_type operator-(const $iterator$& x, const $iterator$& y)
      requires sized_sentinel_for<iterator_t<$Base$>, iterator_t<$Base$>>;

    friend constexpr difference_type operator-(default_sentinel_t y, const $iterator$& x)
      requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;
    friend constexpr difference_type operator-(const $iterator$& x, default_sentinel_t y)
      requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;

    friend constexpr range_rvalue_reference_t<$Base$> iter_move(const $iterator$& i)
      noexcept(noexcept(ranges::iter_move(i.$current_$)));

    friend constexpr void iter_swap(const $iterator$& x, const $iterator$& y)
      noexcept(noexcept(ranges::iter_swap(x.$current_$, y.$current_$)))
      requires indirectly_swappable<iterator_t<$Base$>>;
  };
}
```

[#]{.pnum} `$iterator$::iterator_concept` is defined as follows:

- [#.#]{.pnum} If `$Base$` models `random_access_range`, then `iterator_concept` denotes `random_access_iterator_tag`.

- [#.#]{.pnum} Otherwise, if `$Base$` models `bidirectional_range`, then `iterator_concept` denotes `bidirectional_iterator_tag`.

- [#.#]{.pnum} Otherwise, if `$Base$` models `forward_range`, then `iterator_concept` denotes `forward_iterator_tag`.

- [#.#]{.pnum} Otherwise, `iterator_concept` denotes `input_iterator_tag`.

[#]{.pnum} The member _typedef-name_ `iterator_category` is defined if and only if `$Base$` models `forward_range`.
In that case, `$iterator$::iterator_category` is defined as follows:

- [#.#]{.pnum} Let `C` denote the type `iterator_traits<iterator_t<$Base$>>::iterator_category`.

- [#.#]{.pnum} If `C` models `derived_from<random_access_iterator_tag>`, then `iterator_category` denotes `random_access_iterator_tag`.

- [#.#]{.pnum} Otherwise, `iterator_category` denotes `C`.

::: itemdecl

```cpp
constexpr $iterator$($Parent$* parent, iterator_t<$Base$> current,
                   range_difference_t<$Base$> missing = 0);
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `std::move(current)`,
`$end_$` with `ranges::end(parent->$base_$)`,
`$stride_$` with `parent->$stride_$`,
and `$missing_$` with `missing`.

```cpp
constexpr $iterator$($iterator$<!Const> i)
  requires Const && convertible_to<iterator_t<V>, iterator_t<$Base$>>
                 && convertible_to<sentinel_t<V>, sentinel_t<$Base$>>;
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `std::move(i.$current_$)`,
`$end_$` with `std::move(i.$end_$)`, `$stride_$` with `i.$stride_$`, and `$missing_$` with `i.$missing_$`.

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

[#]{.pnum} _Preconditions:_ `$current_$ != $end_$` is `true`.

[#]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
   $missing_$ = ranges::advance($current_$, $stride_$, $end_$);
   return *this;
```
:::

```cpp
constexpr void operator++(int);
```

[#]{.pnum} _Effects_: Equivalent to: `++*this;`

```cpp
constexpr $iterator$ operator++(int) requires forward_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto tmp = *this;
  ++*this;
  return tmp;
```
:::

```cpp
constexpr $iterator$& operator--() requires bidirectional_range<$Base$>;
```

[#]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
   ranges::advance($current_$, $missing_$ - $stride_$);
   $missing_$ = 0;
   return *this;
```
:::

```cpp
constexpr $iterator$ operator--(int) requires bidirectional_range<$Base$>;
```

::: bq
```cpp
  auto tmp = *this;
  --*this;
  return tmp;
```
:::

```cpp
constexpr $iterator$& operator+=(difference_type n) requires random_access_range<$Base$>;
```

[#]{.pnum} _Preconditions_: If `n` is positive,
`ranges::distance($current_$, $end_$) > $stride_$ * (n - 1)` is `true`.
[If `n` is negative, the _Effects:_ paragraph implies a precondition.]{.note}

[#]{.pnum} _Effects:_ Equivalent to:

:::bq
```cpp
if (n > 0) {
  $missing_$ = ranges::advance($current_$, $stride_$ * n, $end_$);
}
else if (n < 0) {
  ranges::advance($current_$, $stride_$ * n + $missing_$);
  $missing_$ = 0;
}
return *this;
```
:::

```cpp
constexpr $iterator$& operator-=(difference_type x)
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Effects:_ Equivalent to: `return *this += -x;`

```cpp
friend constexpr bool operator==(const $iterator$& x, default_sentinel);
```

[#]{.pnum} _Returns:_ `x.$current_$ == x.$end_$;`

```cpp
friend constexpr bool operator==(const $iterator$& x, const $iterator$& y)
      requires equality_comparable<iterator_t<$Base$>>;
```

[#]{.pnum} _Returns:_ `x.$current_$ == y.$current_$`.

```cpp
friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Returns_: `x.$current_$ < y.$current_$`.

```cpp
friend constexpr bool operator>(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return y < x;`

```cpp
friend constexpr bool operator<=(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return !(y < x);`

```cpp
friend constexpr bool operator>=(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return !(x < y);`

```cpp
friend constexpr auto operator<=>(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$> &&
           three_way_comparable<iterator_t<$Base$>>;
```

[#]{.pnum} _Returns_: `x.$current_$ <=> y.$current_$`.


```cpp
friend constexpr $iterator$ operator+(const $iterator$& i, difference_type n)
  requires random_access_range<$Base$>;
friend constexpr $iterator$ operator+(difference_type n, const $iterator$& i)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto r = i;
  r += n;
  return r;
```
:::

```cpp
friend constexpr $iterator$ operator-(const $iterator$& i, difference_type n)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto r = i;
  r -= n;
  return r;
```
:::

```cpp
friend constexpr difference_type operator-(const $iterator$& x, const $iterator$& y)
  requires sized_sentinel_for<iterator_t<$Base$>, iterator_t<$Base$>>;
```

[#]{.pnum} _Returns:_ Let `N` be `x.$current_$ - y.$current_$`.

- [#.#]{.pnum} If `$Base$` models `forward_range`, `(N + x.$missing_$ - y.$missing_$) / x.$stride_$`.
- [#.#]{.pnum} Otherwise, if `N` is negative, `-$div-ceil$(-N, x.$stride_$)`.
- [#.#]{.pnum} Otherwise, `$div-ceil$(N, x.$stride_$)`.

[When `$Base$` is input-only, the value of `$missing_$` is unreliable.]{.draftnote}

```cpp
friend constexpr difference_type operator-(default_sentinel_t y, const $iterator$& x)
  requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;
```
[#]{.pnum} _Returns_: `$div-ceil$(x.$end_$ - x.$current_$, x.$stride_$)`.

```cpp
friend constexpr difference_type operator-(const $iterator$& x, default_sentinel_t y)
  requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;
```
[#]{.pnum} _Effects_: Equivalent to: `return -(y - x);`

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

Add the following macro definition to [version.syn]{.sref}, header `<version>` synopsis, with the
value selected by the editor to reflect the date of adoption of this paper:

```cpp
#define __cpp_lib_ranges_stride 20XXXXL // also in <ranges>
```

# Acknowledgements

The author would like to thank Tristan Brindle for providing editorial commentary on P1899, and also
those who reviewed material for, or attended the aforementioned CppCon session or post-conference
class, for their input on the design of the proposed `stride_view`.

---
references:
    - id: P2442R1
      citation-label: P2442R1
      title: "Windowing range adaptors: `views::chunk` and `views::slide`"
      author:
        - family: Tim Song
      issued:
        year: 2021
      URL: https://wg21.link/P2442R1
---
