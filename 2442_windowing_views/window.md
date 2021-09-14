---
title: "Windowing range adaptors: `views::chunk` and `views::slide`"
document: P2442R0
date: today
audience:
  - LEWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: true
---

# Abstract
This paper proposes two range adaptors, `views::chunk` and `views::slide`,
as described in section 3.5 of [@P2214R0].

# Example

```cpp
std::vector v = {1, 2, 3, 4, 5};
fmt::print("{}\n", v | std::views::chunk(2));   // [[1, 2], [3, 4], [5]]
fmt::print("{}\n", v | std::views::slide(2));   // [[1, 2], [2, 3], [3, 4], [4, 5]]
```

# Design

Both of these range adaptors are well-known quantities that have been shipped in
range-v3 for years and are further discussed in section 3.5 of [@P2214R0]. The
discussion below assumes familiarity with that paper.

## `chunk`

The basic idea of `chunk` is simple: `views::chunk(R, N)` divides `R` into
non-overlapping N-sized chunks, except that the last chunk can be smaller than
`N` in size. It is a precondition that `N` is positive.

### Input range support
Matching the range-v3 implementation, the proposed `chunk` supports input ranges,
even though the algorithm necessary for such support is significantly different.

In particular, for input ranges, the underlying iterator as well as related
iteration state is tracked in the `chunk_view` object itself. This means that
this `chunk_view` can only support non-`const` iteration. As a point of departure
from range-v3, both outer and inner iterators are move-only input iterators.

Because the inner iterator and outer iterator share state, and moving from the
stored underlying iterators can invalidate both iterators, only the non-mutating
`base() const&` overload is provided for the inner iterator to avoid this sort of
spooky-action-at-a-distance invalidation:

```cpp
auto v = some_input_view | views::chunk(2);
auto outer = v.begin();
auto range = *outer;
range.begin().base(); // if this moved the underlying iterator, outer would be invalidated
```

Providing `base()` for the outer iterator would be misleading as the stored
iterator mutates when the inner range is being iterated over.

### Value type

For input ranges, `chunk` has a bespoke value type that is itself an input view.
For forward and stronger ranges, `chunk` defers to `views::take` for its
value type.

### Conditionally common

In range-v3, `chunk` is never a common range. `chunk` as proposed here is a
common range if the underlying range is forward, common, and either sized or
non-bidirectional.

For bidirectional and stronger ranges, the need to size the last chunk correctly
from the end iterator requires the underlying range to be sized.

### Conditionally borrowed

As with range-v3, this paper proposes that `chunk` is borrowed if the underlying
view is forward and borrowed.

### Implementation notes

For input ranges, `chunk_view` stores

- the current underlying iterator (`$current_$`); and
- the number of elements left in the current chunk (`$remainder_$`).

Incrementing the inner iterator increments `$current_$` and
decrements `$remainder_$`, setting it to zero if the end of the chunk is reached.

Incrementing the outer iterator increments `$current_$` `$remainder_$` times so
that we start at the next N-element chunk even if the inner view isn't iterated
to end, and then sets `$remainder_$` to the chunk size.

For forward and stronger ranges, `chunk_view`'s `$iterator$` stores an
exposition-only data member `$offset_$`. This data member can only be nonzero
when the iterator is the past-the-end iterator, in which case it represents
the difference between _N_ and the size of the last chunk.

## `slide`

`views::slide(R, N)` produces a range of ranges such that the _M_-th range is
a view into the _M_-th through (_M_+_N_-1)-th elements of `R`. It is
similar to `views::adjacent` ([@P2321R2]), except that the size of the window _N_ is
provided at runtime. It is a precondition that _N_ is positive.

### Forward ranges only

Unlike `chunk`, and similar to `adjacent`, `slide` does not support input ranges.
It might be possible to support a window size of 1 - but then users can just use
`chunk` instead. Caching elements is not considered a viable approach,
essentially for the reasons discussed in section 4.3.4 of [@P2321R2].

### Value type

`slide` defers to `views::counted` for its value type.

### Conditionally common and borrowed

`slide` is a common range if the underlying range is (or can be trivially made one),
and is a borrowed range if the underlying range is.

### Implementation notes
There are basically two strategies for `slide`. For simplicity the discussion
below ignores the case where the number of elements in the source view is less
than `N`.

- When the end iterator of the underlying range can be known in constant time
  and is at least bidirectional, `slide` can go back `N - 1` elements from that
  iterator to find the first iterator that can't start a range. In this case,
  `slide`'s iterator need only store the first iterator of the window `i` and
  the window size `N`.
- Otherwise, `slide`'s iterator must also store the iterator to the last element
  in the window (that is, `i + (N - 1)`). When that iterator compares equal to
  the end of the source range, the iterator is past-the-end (since we can no
  longer produce a range of `N` elements).

## Implementation experience

Both `chunk` and `slide` (under the name `sliding`) have been implemented in
range-v3, and much of the subtler aspects of the implementation logic in the
wording below are taken from there (any errors are mine, of course, though
hopefully there isn't any).

I also have implemented a version that directly follows the proposed wording below
without issue.

# Wording

## Addition to `<ranges>`

Add the following to [ranges.syn]{.sref}, header `<ranges>` synopsis:

```cpp
// [...]
namespace std::ranges {
  // [...]

  // [range.chunk], chunk view
  template<view V>
    requires input_range<V>
  class chunk_view;

  template<view V>
    requires forward_range<V>
  class chunk_view<V>;

  template<class V>
    inline constexpr bool enable_borrowed_range<chunk_view<V>> =
      forward_range<V> && enable_borrowed_range<V>;

  namespace views {
    inline constexpr $unspecified$ chunk = $unspecified$;
  }

  // [range.slide], slide view
  template<view V>
    requires forward_range<V>
  class slide_view;

  template<class V>
    inline constexpr bool enable_borrowed_range<slide_view<V>> =
      enable_borrowed_range<V>;

  namespace views {
    inline constexpr $unspecified$ slide = $unspecified$;
  }
}

```

## `chunk`

Add the following subclause to [range.adaptors]{.sref}.

### 24.7.? Chunk view [range.chunk] {-}

#### 24.7.?.1 Overview [range.chunk.overview] {-}

[#]{.pnum} `chunk_view` takes a `view` and a number _N_ and produces a range of views
that are _N_-sized non-overlapping contiguous chunks of the elements of the
original view, in order. The last view in the range can have fewer than _N_ elements.

[#]{.pnum} The name `views::chunk` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given subexpressions `E` and `N`,
the expression `views::chunk(E, N)` is expression-equivalent to
`chunk_view(E, N)`.

::: example

```cpp
vector v = {1, 2, 3, 4, 5};

for (auto r : v | views::chunk(2)) {
  cout << '[';
  auto sep = "";
  for(auto i : r) {
    cout << sep << i;
    sep = ", ";
  }
  cout << "] ";
}
// prints: [1, 2] [3, 4] [5]

```
:::

#### 24.7.?.2 `chunk_view` for input ranges [range.chunk.view.input] {-}

```cpp
namespace std::ranges {

template<view V>
  requires input_range<V>
class chunk_view : public view_interface<chunk_view<V>>{
  V $base_$ = V();                        // exposition only
  range_difference_t<V> $n_$ = 0;         // exposition only
  range_difference_t<V> $remainder_$ = 0; // exposition only

  $non-propagating-cache$<iterator_t<V>> $current_$; // exposition only

  // [range.chunk.outer.iter], class chunk_view::$outer-iterator$
  class $outer-iterator$;                 // exposition only
  // [range.chunk.inner.iter], class chunk_view::$inner-iterator$
  class $inner-iterator$;                 // exposition only

public:
  chunk_view() requires default_initializable<V> = default;
  constexpr explicit chunk_view(V base, range_difference_t<V> n);

  constexpr V base() const & requires copy_constructible<V> { return $base_$; }
  constexpr V base() && { return std::move($base_$); }

  constexpr $outer-iterator$ begin();
  constexpr default_sentinel_t end();

  constexpr auto size() requires sized_range<V>;
  constexpr auto size() const requires sized_range<const V>;
};

template<class R>
  chunk_view(R&& r, range_difference_t<R>) -> chunk_view<views::all_t<R>>;

}
```

::: itemdecl

```cpp
constexpr explicit chunk_view(V base, range_difference_t<V> n);
```
[#]{.pnum} _Preconditions_: `n > 0` is `true`.

[#]{.pnum} _Effects_: Initializes `$base_$` with `std::move(base)`
and `$n_$` with `n`.

```cpp
constexpr $outer-iterator$ begin();
```

[#]{.pnum} _Effects_: Equivalent to:

:::bq
```cpp
$current_$ = ranges::begin($base_$);
$remainder_$ = $n_$;
return $outer-iterator$(*this);
```
:::

```cpp
constexpr default_sentinel_t end();
```

[#]{.pnum} _Returns_: `default_sentinel`.

```cpp
constexpr auto size() requires sized_range<V>;
constexpr auto size() const requires sized_range<const V>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
auto sz = (ranges::distance($base_$) + $n_$ - 1) / $n_$;
return $to-unsigned-like$(sz);
```
:::
:::

#### 24.7.?.3 Class `chunk_view::$outer-iterator$` [range.chunk.outer.iter] {-}

```cpp
namespace std::ranges {
  template<view V>
    requires input_range<V>
  class chunk_view<V>::$outer-iterator$ {
    chunk_view* $parent_$;                                    // exposition only

    constexpr explicit $outer-iterator$(chunk_view& parent);  // exposition only
  public:
    using iterator_concept = input_iterator_tag;
    using difference_type  = range_difference_t<V>;

    // [range.chunk.outer.value], class chunk_view::$outer-iterator$::value_type
    struct value_type;

    $outer-iterator$($outer-iterator$&&) = default;
    $outer-iterator$& operator=($outer-iterator$&&) = default;

    constexpr value_type operator*() const;
    constexpr $outer-iterator$& operator++();
    constexpr void operator++(int);

    friend constexpr bool operator==(const $outer-iterator$& x, default_sentinel_t);

    friend constexpr difference_type operator-(default_sentinel_t y, const $outer-iterator$& x)
      requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
    friend constexpr difference_type operator-(const $outer-iterator$& x, default_sentinel_t y)
      requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
  };
}
```

::: itemdecl

```cpp
constexpr $outer-iterator$(chunk_view& parent);
```

[#]{.pnum} _Effects_: Initializes `$parent_$` with `addressof(parent)`.

```cpp
constexpr value_type operator*() const;
```

[#]{.pnum} _Preconditions_: `*this == default_sentinel` is `false`.

[#]{.pnum} _Returns_: `value_type(*$parent_$)`.

```cpp
constexpr $outer-iterator$& operator++();
```

[#]{.pnum} _Preconditions_: `*this == default_sentinel` is `false`.

[#]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
   ranges::advance(*$parent_$->$current_$, $parent_$->$remainder_$, ranges::end($parent_$->$base_$));
   $parent_$->$remainder_$ = $parent_$->$n_$;
   return *this;
```
:::

```cpp
constexpr void operator++(int);
```

[#]{.pnum} _Effects_: Equivalent to `++*this`.


```cpp
friend constexpr bool operator==(const $outer-iterator$& x, default_sentinel_t);
```

[#]{.pnum} _Returns:_ `*x.$parent_$->$current_$ == ranges::end(x.$parent_$->$base_$) && x.$parent_$->$remainder_$ != 0`.

```cpp
friend constexpr difference_type operator-(default_sentinel_t y, const $outer-iterator$& x)
  requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
```
[#]{.pnum} _Effects_: Equivalent to:

:::bq
```cpp
const auto dist = ranges::end(x.$parent_$->$base_$) - *x.$parent_$->$current_$;

if (dist < x.$parent_$->$remainder_$) {
  return dist == 0 ? 0 : 1;
}

return (dist - x.$parent_$->$remainder_$ + x.$parent_$->$n_$ - 1) / x.$parent_$->$n_$ + 1;
```
:::

```cpp
friend constexpr difference_type operator-(const $outer-iterator$& x, default_sentinel_t y)
  requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
```
[#]{.pnum} _Effects_: Equivalent to: `return -(y - x);`

:::

#### 24.7.?.4 Class `chunk_view::$outer-iterator$::value_type` [range.chunk.outer.value] {-}

```cpp
namespace std::ranges {
  template<view V>
    requires input_range<V>
  struct chunk_view<V>::$outer-iterator$::value_type : view_interface<value_type> {
    chunk_view* $parent_$;                                // exposition only

    constexpr explicit value_type(chunk_view& parent);    // exposition only
  public:
    constexpr $inner-iterator$ begin() const;
    constexpr default_sentinel_t end() const;

    constexpr auto size() const
      requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
  };
}
```

::: itemdecl

```cpp
constexpr value_type(chunk_view& parent);
```

[#]{.pnum} _Effects_: Initializes `$parent_$` with `addressof(parent)`.

```cpp
constexpr $inner-iterator$ begin() const;
```

[#]{.pnum} _Returns_: `$inner-iterator$(*$parent_$)`.

```cpp
constexpr default_sentinel_t end() const;
```

[#]{.pnum} _Returns_: `default_sentinel`.

```cpp
constexpr auto size() const
  requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
```

[#]{.pnum} _Returns_: `ranges::min($parent_$->$remainder_$, ranges::end($parent_$->$base_$) - *$parent_$->$current_$)`.

:::

#### 24.7.?.5 Class `chunk_view::$inner-iterator$` [range.chunk.inner.iter] {-}

```cpp
namespace std::ranges {
  template<view V>
    requires input_range<V>
  class chunk_view<V>::$inner-iterator$ {
    chunk_view* $parent_$;                                // exposition only

    constexpr explicit $inner-iterator$(chunk_view& parent);    // exposition only
  public:
    using iterator_concept  = input_iterator_tag;
    using difference_type = range_difference_t<V>;
    using value_type = range_value_t<V>;

    $inner-iterator$($inner-iterator$&&) = default;
    $inner-iterator$& operator=($inner-iterator$&&) = default;

    constexpr const iterator_t<V>& base() const &;

    constexpr range_reference_t<V> operator*() const;
    constexpr $inner-iterator$& operator++();
    constexpr void operator++(int);

    friend constexpr bool operator==(const $inner-iterator$& x, default_sentinel_t);

    friend constexpr difference_type operator-(default_sentinel_t y, const $inner-iterator$& x)
      requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
    friend constexpr difference_type operator-(const $inner-iterator$& x, default_sentinel_t y)
      requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
  };
}
```

::: itemdecl

```cpp
constexpr $inner-iterator$(chunk_view& parent);
```

[#]{.pnum} _Effects_: Initializes `$parent_$` with `addressof(parent)`.

```cpp
const iterator_t<V>& base() const &;
```

[#]{.pnum} _Returns_: `*$parent_$->$current_$`.

```cpp
constexpr range_reference_t<V> operator*() const;
```

[#]{.pnum} _Preconditions_: `*this == default_sentinel` is `false`.

[#]{.pnum} _Effects_: Equivalent to: `return **$parent_$->$current_$;`

```cpp
constexpr $iterator$& operator++();
```

[#]{.pnum} _Preconditions_: `*this == default_sentinel` is `false`.

[#]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
  ++*$parent_$->$current_$;
  if (*$parent_$->$current_$ == ranges::end($parent_$->$base_$)) {
    $parent_$->$remainder_$ = 0;
  }
  else {
    --$parent_$->$remainder_$;
  }
  return *this;
```
:::

```cpp
constexpr void operator++(int);
```

[#]{.pnum} _Effects_: Equivalent to `++*this`.


```cpp
friend constexpr bool operator==(const $inner-iterator$& x, default_sentinel_t);
```

[#]{.pnum} _Returns:_ `x.$parent_$->$remainder_$ == 0`.

```cpp
friend constexpr difference_type operator-(default_sentinel_t y, const $inner-iterator$& x)
  requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
```
[#]{.pnum} _Returns:_ `ranges::min(x.parent_->remainder_, ranges::end(x.$parent_$->$base_$) - *x.$parent_$->$current_$)`.


```cpp
friend constexpr difference_type operator-(const $inner-iterator$& x, default_sentinel_t y)
  requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
```
[#]{.pnum} _Effects_: Equivalent to: `return -(y - x);`

:::


#### 24.7.?.6 `chunk_view` for forward ranges [range.chunk.view.fwd] {-}

```cpp
namespace std::ranges {

template<view V>
  requires forward_range<V>
class chunk_view<V> : public view_interface<chunk_view<V>>{
  V $base_$ = V();                     // exposition only
  range_difference_t<V> $n_$ = 0;      // exposition only
  template<bool> class $iterator$;     // exposition only

public:
  chunk_view() requires default_initializable<V> = default;
  constexpr explicit chunk_view(V base, range_difference_t<V> n);

  constexpr V base() const & requires copy_constructible<V> { return $base_$; }
  constexpr V base() && { return std::move($base_$); }

  constexpr auto begin() requires (!$simple-view$<V>) {
    return $iterator$<false>(this, ranges::begin($base_$));
  }

  constexpr auto begin() const requires forward_range<const V> {
    return $iterator$<true>(this, ranges::begin($base_$));
  }

  constexpr auto end() requires (!$simple-view$<V>) {
    if constexpr (common_range<V> && sized_range<V>) {
      auto offset = ($n_$ - ranges::distance($base_$) % $n_$) % $n_$;
      return $iterator$<false>(this, ranges::end($base_$), offset);
    }
    else if constexpr (common_range<V> && !bidirectional_range<V>) {
      return $iterator$<false>(this, ranges::end($base_$));
    }
    else {
      return default_sentinel;
    }
  }

  constexpr auto end() const requires forward_range<const V> {
    if constexpr (common_range<const V> && sized_range<const V>) {
      auto offset = ($n_$ - ranges::distance($base_$) % $n_$) % $n_$;
      return $iterator$<true>(this, ranges::end($base_$), offset);
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

}
```

::: itemdecl

```cpp
constexpr explicit chunk_view(V base, range_difference_t<V> n);
```
[#]{.pnum} _Preconditions_: `n > 0` is `true`.

[#]{.pnum} _Effects_: Initializes `$base_$` with `std::move(base)` and `$n_$` with `n`.

```cpp
constexpr auto size() requires sized_range<V>;
constexpr auto size() const requires sized_range<const V>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
auto sz = (ranges::distance($base_$) + $n_$ - 1) / $n_$;
return to-unsigned-like(sz);
```
:::
:::

#### 24.7.?.7 Class template `chunk_view<V>::$iterator$` for forward ranges [range.chunk.fwd.iter] {-}

```cpp
namespace std::ranges {
  template<view V>
    requires forward_range<V>
  template<bool Const>
  class chunk_view<V>::$iterator$ {
    using $Parent$ = $maybe-const$<Const, chunk_view>;              // exposition only
    using $Base$ = $maybe-const$<Const, V>;                         // exposition only

    iterator_t<$Base$> $current_$ = iterator_t<$Base$>();             // exposition only
    sentinel_t<$Base$> $end_$ = sentinel_t<$Base$>();                 // exposition only
    range_difference_t<$Base$> $n_$ = 0;                            // exposition only
    range_difference_t<$Base$> $offset_$ = 0;                       // exposition only

    constexpr $iterator$($Parent$* parent, iterator_t<$Base$> current,  // exposition only
                       range_difference_t<$Base$> offset = 0);
  public:
    using iterator_category = input_iterator_tag;
    using iterator_concept  = $see below$;
    using value_type = decltype(views::take(subrange($current_$, $end_$), $n_$));
    using difference_type = range_difference_t<$Base$>;

    $iterator$() = default;
    constexpr $iterator$($iterator$<!Const> i)
      requires Const && convertible_to<iterator_t<V>, iterator_t<$Base$>>
                     && convertible_to<sentinel_t<V>, sentinel_t<$Base$>>;

    constexpr iterator_t<$Base$> base() const;

    constexpr value_type operator*() const;
    constexpr $iterator$& operator++();
    constexpr $iterator$ operator++(int);

    constexpr $iterator$& operator--() requires bidirectional_range<$Base$>;
    constexpr $iterator$ operator--(int) requires bidirectional_range<$Base$>;

    constexpr $iterator$& operator+=(difference_type x)
      requires random_access_range<$Base$>;
    constexpr $iterator$& operator-=(difference_type x)
      requires random_access_range<$Base$>;

    constexpr value_type operator[](difference_type n) const
      requires random_access_range<$Base$>;

    friend constexpr bool operator==(const $iterator$& x, const $iterator$& y);
    friend constexpr bool operator==(const $iterator$& x, default_sentinel_t);

    friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr bool operator>(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr bool operator<=(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr bool operator>=(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr auto operator<=>(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$> &&
               three_way_comparable<iterator_t<$Base$>>;

    friend constexpr $iterator$ operator+(const $iterator$& i, difference_type n)
      requires random_access_range<$Base$>;
    friend constexpr $iterator$ operator+(difference_type n, const $iterator$& i)
      requires random_access_range<$Base$>;
    friend constexpr $iterator$ operator-(const $iterator$& i, difference_type n)
      requires random_access_range<$Base$>;
    friend constexpr difference_type operator-(const $iterator$& x, const $iterator$& y)
      requires sized_sentinel_for<iterator_t<$Base$>, iterator_t<$Base$>>;

    friend constexpr difference_type operator-(default_sentinel_t y, const $iterator$& x)
      requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;
    friend constexpr difference_type operator-(const $iterator$& x, default_sentinel_t y)
      requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;
  };
}
```

[#]{.pnum} `$iterator$::iterator_concept` is defined as follows:

- [#.#]{.pnum} If `$Base$` models `random_access_range`, then `iterator_concept` denotes `random_access_iterator_tag`.
- [#.#]{.pnum} Otherwise, if `$Base$` models `bidirectional_range`, then `iterator_concept` denotes `bidirectional_iterator_tag`.
- [#.#]{.pnum} Otherwise, `iterator_concept` denotes `forward_iterator_tag`.

::: itemdecl

```cpp
constexpr $iterator$($Parent$* parent, iterator_t<$Base$> current,
                     range_difference_t<$Base$> offset = 0);
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `current`,
`$end_$` with `ranges::end(parent->$base_$)`,
`$n_$` with `parent->$n_$`,
and `$offset_$` with `offset`.

```cpp
constexpr $iterator$($iterator$<!Const> i)
  requires Const && convertible_to<iterator_t<V>, iterator_t<$Base$>>
                 && convertible_to<sentinel_t<V>, sentinel_t<$Base$>>;
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `std::move(i.$current_$)`,
`$end_$` with `std::move(i.$end_$)`, `$n_$` with `i.$n_$`, and `$offset_$` with `i.$offset_$`.

```cpp
constexpr iterator_t<$Base$> base() const;
```
[#]{.pnum} _Returns_: `$current_$`.

```cpp
constexpr value_type operator*() const;
```
[#]{.pnum} _Preconditions:_ `$current_$ != $end_$` is `true`.

[#]{.pnum} _Returns_: `views::take(subrange($current_$, $end_$), $n_$)`

```cpp
constexpr $iterator$& operator++();
```
[#]{.pnum} _Preconditions:_ `$current_$ != $end_$` is `true`.

[#]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
   $offset_$ = ranges::advance($current_$, $n_$, $end_$);
   return *this;
```
:::

```cpp
constexpr $iterator$ operator++(int);
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
   ranges::advance($current_$, $offset_$ - $n_$);
   $offset_$ = 0;
   return *this;
```
:::

```cpp
constexpr $iterator$ operator--(int) requires bidirectional_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto tmp = *this;
  --*this;
  return tmp;
```
:::

```cpp
constexpr $iterator$& operator+=(difference_type x)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Preconditions_: If `x` is positive,
`ranges::distance($current_$, $end_$) > $n_$ * (x - 1)` is `true`.

[#]{.pnum} _Effects:_ Equivalent to:

:::bq
```cpp
if (x > 0) {
  offset_ = ranges::advance($current_$, $n_$ * x, $end_$);
}
else if (x < 0) {
  ranges::advance($current_$, $n_$ * x + $offset_$);
  offset_ = 0;
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
constexpr value_type operator[](difference_type n) const
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Returns_: `*(*this + n)`.

```cpp
friend constexpr bool operator==(const $iterator$& x, const $iterator$& y);
```
[#]{.pnum} _Returns:_ `x.$current_$ == y.$current_$`.

```cpp
friend constexpr bool operator==(const $iterator$& x, default_sentinel_t);
```

[#]{.pnum} _Returns:_ `x.$current_$ == x.$end_$;`

```cpp
friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Returns_: `x.$current_$ < y.$current_$`.

```cpp
friend constexpr bool operator>(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to: `return y < x; `

```cpp
friend constexpr bool operator<=(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return !(y < x); `


```cpp
friend constexpr bool operator>=(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return !(x < y); `

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
[#]{.pnum} _Returns:_ `(x.$current_$ - y.$current_$ + x.$offset_$ - y.$offset_$) / x.$n_$`.

```cpp
friend constexpr difference_type operator-(default_sentinel_t y, const $iterator$& x)
  requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;
```
[#]{.pnum} _Returns_: `(x.$end_$ - x.$current_$ + x.$n_$ - 1)  / x.$n_$`.

```cpp
friend constexpr difference_type operator-(const $iterator$& x, default_sentinel_t y)
  requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$Base$>>;
```
[#]{.pnum} _Effects_: Equivalent to: `return -(y - x);`

:::

## `slide`

Add the following subclause to [range.adaptors]{.sref}.

### 24.7.? Slide view [range.slide] {-}

#### 24.7.?.1 Overview [range.slide.overview] {-}

[#]{.pnum} `slide_view` takes a `view` and a number _N_ and produces a `view` whose
_M_ <sup>th</sup> element is a view over the M <sup>th</sup> through
(_M_ + _N_ - 1)<sup>th</sup> elements of the original view. If the original
view has fewer than _N_ elements, the resulting view is empty.

[#]{.pnum} The name `views::slide` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given subexpressions `E` and `N`,
the expression `views::slide(E, N)` is expression-equivalent to `slide_view(E, N)`.

::: example

```cpp
vector v = {1, 2, 3, 4};

for (auto i : v | views::slide(2)) {
  cout << '[' << i[0] << ', ' << i[1] << "] "; // prints: [1, 2] [2, 3] [3, 4]
}

```
:::

#### 24.7.?.2 Class template `slide_view` [range.slide.view] {-}

```cpp
namespace std::ranges {

template<class V>
  concept $slide-caches-nothing$ = random_access_range<V> && sized_range<V>; // exposition only

template<class V>
  concept $slide-caches-last$ = !$slide-caches-nothing$<V> && bidirectional_range<V> && common_range<V>; // exposition only

template<class V>
  concept $slide-caches-first$ = !$slide-caches-nothing$<V> && !$slide-caches-last$<V>; // exposition only

template<forward_range V>
  requires view<V>
class slide_view : public view_interface<slide_view<V>>{
  V $base_$ = V();                     // exposition only
  range_difference_t<V> $n_$ = 0;      // exposition only

  template<bool> class $iterator$;     // exposition only
  class $sentinel$;                    // exposition only

public:
  slide_view() requires default_initializable<V> = default;
  constexpr explicit slide_view(V base, range_difference_t<V> n);

  constexpr auto begin()
    requires (!($simple-view$<V> && $slide-caches-nothing$<const V>));
  constexpr auto begin() const requires $slide-caches-nothing$<const V>;

  constexpr auto end()
    requires (!($simple-view$<V> && $slide-caches-nothing$<const V>));
  constexpr auto end() const requires $slide-caches-nothing$<const V>;

  constexpr auto size() requires sized_range<V>;
  constexpr auto size() const requires sized_range<const V>;
};

template<class R>
  slide_view(R&& r, range_difference_t<R>) -> slide_view<views::all_t<R>>;

}
```

::: itemdecl

```cpp
constexpr explicit slide_view(V base, range_difference_t<V> n);
```

[#]{.pnum} _Effects_: Initializes `$base_$` with `std::move(base)` and `$n_$` with `n`.

```cpp
constexpr auto begin()
  requires (!($simple-view$<V> && $slide-caches-nothing$<const V>));
```

[#]{.pnum} _Returns_:

- [#.#]{.pnum} If `V` models `$slide-caches-first$`,
`$iterator$<false>(ranges::begin($base_$), ranges::next(ranges::begin($base_$), $n_$ - 1, ranges::end($base_$)), $n_$)`.
- [#.#]{.pnum} Otherwise, `$iterator$<false>(ranges::begin($base_$), $n_$)`.

[#]{.pnum} _Remarks_: In order to provide the amortized constant-time complexity
required by the `range` concept, this function caches the result within the
`slide_view` for use on subsequent calls when `V` models `$slide-caches-first$`.

```cpp
constexpr auto begin() const requires $slide-caches-nothing$<const V>;
```

[#]{.pnum} _Returns_: `$iterator$<true>(ranges::begin($base_$), $n_$)`.

```cpp
constexpr auto end()
  requires (!($simple-view$<V> && $slide-caches-nothing$<const V>));
```

[#]{.pnum} _Returns_:

- [#.#]{.pnum} If `V` models `$slide-caches-nothing$`,
`$iterator$<false>(ranges::begin($base_$) + range_difference_t<V>(size()), $n_$)`;
- [#.#]{.pnum} Otherwise, if `V` models `$slide-caches-last$`,
`$iterator$<false>(ranges::prev(ranges::end($base_$), $n_$ - 1, ranges::begin($base_$)), $n_$)`;
- [#.#]{.pnum} Otherwise, if `V` models `common_range`, `iterator<false>(ranges::end($base_$), ranges::end($base_$), $n_$)`;
- [#.#]{.pnum} Otherwise, `$sentinel$(ranges::end($base_$))`.

[#]{.pnum} _Remarks_: In order to provide the amortized constant-time complexity
required by the `range` concept, this function caches the result within the
`slide_view` for use on subsequent calls when `V` models `$slide-caches-last$`.

```cpp
constexpr auto end() const requires $slide-caches-nothing$<const V>;
```

[#]{.pnum} _Returns_: `begin() + range_difference_t<const V>(size())`.

```cpp
constexpr auto size() requires sized_range<V>;
constexpr auto size() const requires sized_range<const V>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
auto sz = ranges::distance($base_$) - $n_$ + 1;
if (sz < 0) sz = 0;
return $to-unsigned-like$(sz);
```
:::

:::


#### 24.7.?.3 Class template `slide_view::$iterator$` [range.slide.iterator] {-}

```cpp
namespace std::ranges {
  template<forward_range V>
    requires view<V>
  template<bool Const>
  class slide_view<V>::$iterator$ {
    using $Base$ = $maybe-const$<Const, V>;                     // exposition only
    iterator_t<$Base$> $current_$   = iterator_t<$Base$>();       // exposition only
    iterator_t<$Base$> $last_ele_$  = iterator_t<$Base$>();       // exposition only, present only if $Base$ models $slide-caches-first$
    range_difference_t<$Base$> $n_$ = 0;                        // exposition only

    constexpr $iterator$(iterator_t<$Base$> current, range_difference_t<$Base$> n) // exposition only
      requires (!$slide-caches-first$<$Base$>);

    constexpr $iterator$(iterator_t<$Base$> current, iterator_t<$Base$> last_ele, range_difference_t<$Base$> n) // exposition only
      requires $slide-caches-first$<$Base$>;
  public:
    using iterator_category = input_iterator_tag;
    using iterator_concept  = $see below$;
    using value_type = decltype(views::counted($current_$, $n_$));
    using difference_type = range_difference_t<$Base$>;

    $iterator$() = default;
    constexpr $iterator$($iterator$<!Const> i)
      requires Const && convertible_to<iterator_t<V>, iterator_t<$Base$>>;

    constexpr auto operator*() const;
    constexpr $iterator$& operator++();
    constexpr $iterator$ operator++(int);

    constexpr $iterator$& operator--() requires bidirectional_range<$Base$>;
    constexpr $iterator$ operator--(int) requires bidirectional_range<$Base$>;

    constexpr $iterator$& operator+=(difference_type x)
      requires random_access_range<$Base$>;
    constexpr $iterator$& operator-=(difference_type x)
      requires random_access_range<$Base$>;

    constexpr auto operator[](difference_type n) const
      requires random_access_range<$Base$>;

    friend constexpr bool operator==(const $iterator$& x, const $iterator$& y);

    friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr bool operator>(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr bool operator<=(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr bool operator>=(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr auto operator<=>(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$> &&
               three_way_comparable<iterator_t<$Base$>>;

    friend constexpr $iterator$ operator+(const $iterator$& i, difference_type n)
      requires random_access_range<$Base$>;
    friend constexpr $iterator$ operator+(difference_type n, const $iterator$& i)
      requires random_access_range<$Base$>;
    friend constexpr $iterator$ operator-(const $iterator$& i, difference_type n)
      requires random_access_range<$Base$>;
    friend constexpr difference_type operator-(const $iterator$& x, const $iterator$& y)
      requires sized_sentinel_for<iterator_t<$Base$>, iterator_t<$Base$>>;
  };
}
```

[#]{.pnum} `$iterator$::iterator_concept` is defined as follows:

- [#.#]{.pnum} If `$Base$` models `random_access_range`, then `iterator_concept` denotes `random_access_iterator_tag`.
- [#.#]{.pnum} Otherwise, if `$Base$` models `bidirectional_range`, then `iterator_concept` denotes `bidirectional_iterator_tag`.
- [#.#]{.pnum} Otherwise, `iterator_concept` denotes `forward_iterator_tag`.

[#]{.pnum} If the invocation of any non-const member function of _`iterator`_ exits via an exception,
the iterator acquires a singular value.

::: itemdecl

```cpp
constexpr $iterator$(iterator_t<$Base$> current, range_difference_t<$Base$> n)
  requires (!$slide-caches-first$<$Base$>);
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `current` and `$n_$` with `n`.

```cpp
constexpr $iterator$(iterator_t<$Base$> current, iterator_t<$Base$> last_ele, range_difference_t<$Base$> n); // exposition only
  requires $slide-caches-first$<$Base$>;
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `current`, `$last_ele_$` with `last_ele`, and `$n_$` with `n`.


```cpp
constexpr $iterator$($iterator$<!Const> i)
  requires Const && (convertible_to<iterator_t<V>, iterator_t<$Base$>>;
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `std::move(i.$current_$)` and
`$n_$` with `i.$n_$`. [`iterator<true>` can only be formed when `$Base$` models
`$slide-caches-nothing$`, in which case `$last_ele_$` is not present.]{.note}


```cpp
constexpr auto operator*() const;
```

[#]{.pnum} _Returns_: `views::counted($current_$, $n_$)`.

```cpp
constexpr $iterator$& operator++();
```

[#]{.pnum} _Preconditions:_ `$current_$` and `$last_ele_$` (if present) are incrementable.

[#]{.pnum} _Postconditions_: `$current_$` and `$last_ele_$` (if present) are each
equal to `ranges::next($i$)`, where $i$ is the value of that data member before the call.

[#]{.pnum} _Returns_: `*this`.


```cpp
constexpr $iterator$ operator++(int);
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
[#]{.pnum} _Preconditions:_ `$current_$` and `$last_ele_$` (if present) are decrementable.

[#]{.pnum} _Postconditions_: `$current_$` and `$last_ele_$` (if present) are each
equal to `ranges::prev($i$)`, where $i$ is the value of that data member before the call.

[#]{.pnum} _Returns_: `*this`.


```cpp
constexpr $iterator$ operator--(int) requires bidirectional_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto tmp = *this;
  --*this;
  return tmp;
```
:::

```cpp
constexpr $iterator$& operator+=(difference_type x)
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Preconditions:_ `$current_$ + x` and `$last_ele_$ + x` (if present) has well-defined behavior.

[#]{.pnum} _Postconditions_:  `$current_$` and `$last_ele_$` (if present) are each
equal to `$i$ + x`, where $i$ is the value of that data member before the call.

[#]{.pnum} _Returns_: `*this`.

```cpp
  constexpr $iterator$& operator-=(difference_type x)
    requires random_access_range<$Base$>;
```

[#]{.pnum} _Preconditions:_ `$current_$ - x` and `$last_ele_$ - x` (if present) has well-defined behavior.

[#]{.pnum} _Postconditions_:  `$current_$` and `$last_ele_$` (if present) are each
equal to `$i$ - x`, where $i$ is the value of that data member before the call.

[#]{.pnum} _Returns_: `*this`.

```cpp
constexpr auto operator[](difference_type n) const
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to: `return views::counted($current_$ + n, $n_$);`

```cpp
friend constexpr bool operator==(const $iterator$& x, const $iterator$& y);
```
[#]{.pnum} _Returns:_ If `$last_ele_$` is present, `x.$last_ele_$ == y.$last_ele_$`;
otherwise, `x.$current_$ == y.$current_$`.

```cpp
friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Returns_: `x.$current_$ < y.$current_$`.

```cpp
friend constexpr bool operator>(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to: `return y < x; `

```cpp
friend constexpr bool operator<=(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return !(y < x); `


```cpp
friend constexpr bool operator>=(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return !(x < y); `

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
[#]{.pnum} _Returns_: If `$last_ele_$` is present, `x.$last_ele_$ - y.$last_ele_$`;
otherwise, `x.$current_$ - y.$current_$`.

:::

#### 24.7.?.4 Class `slide_view::$sentinel$` [range.slide.sentinel] {-}

```cpp
namespace std::ranges {
  template<forward_range V>
    requires view<V>
  class slide_view<V>::$sentinel$ {
    sentinel_t<V> $end_$ = sentinel_t<V>();             // exposition only
    constexpr explicit $sentinel$(sentinel_t<V> end);   // exposition only
  public:
    $sentinel$() = default;

    friend constexpr bool operator==(const $iterator$<false>& x, const $sentinel$& y);

    friend constexpr range_difference_t<V>
      operator-(const $iterator$<false>& x, const $sentinel$& y)
        requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;

    friend constexpr range_difference_t<V>
      operator-(const $sentinel$& y, const $iterator$<false>& x)
        requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
  };
}
```

[#]{.pnum} [`$sentinel$` is only used when `$slide-caches-first$<V>` is `true`.]{.note}

::: itemdecl

```cpp
constexpr explicit $sentinel$(sentinel_t<V> end);
```

[#]{.pnum} _Effects_: Initializes `$end_$` with `end`.

```cpp
friend constexpr bool operator==(const $iterator$<false>& x, const $sentinel$& y);
```

[#]{.pnum} _Returns_: `x.$last_ele_$ == y.$end_$`.

```cpp
friend constexpr range_difference_t<V>
  operator-(const $iterator$<false>& x, const $sentinel$& y)
    requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
```
[#]{.pnum} _Returns_: `x.$last_ele_$ - y.$end_$`.

```cpp
friend constexpr range_difference_t<V>
  operator-(const $sentinel$& y, const $iterator$<false>& x)
    requires sized_sentinel_for<sentinel_t<V>, iterator_t<V>>;
```
[#]{.pnum} _Returns_: `y.$end_$ - x.$last_ele_$`.

:::

## Feature-test macro

Add the following macro definition to [version.syn]{.sref}, header `<version>`
synopsis, with the value selected by the editor to reflect the date of adoption
of this paper:

```cpp
#define __cpp_lib_ranges_chunk_slide 20XXXXL // also in <ranges>
```
