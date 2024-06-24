---
title: "`views::cache_last`"
document: D3138R2
date: today
audience:
  - LEWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Abstract

This paper proposes the `views::cache_last` adaptor that caches the result of
the last dereference of the underlying iterator.

# Revision history

- R2: Remove the quasi-drive-by fix to [res.on.data.races]{.sref} per St. Louis SG1 feedback;
  it will be addressed as an LWG issue.
- R1: Limited the [res.on.data.races]{.sref} carve-out to this adaptor per SG1 feedback.

# Motivation

The motivation for this view is given in [@P2760R1] and quoted below for
convenience:

::: bq


One of the adaptors that we considered for C++23 but ended up not pursuing was
what range-v3 calls `cache1` and what we'd instead like to call something like
 `cache_last`. This is an adaptor which, as the name suggests, caches the last
element. The reason for this is efficiency - specifically avoiding extra work
that has to be done by iterator dereferencing.

The canonical example of this is `transform(f) | filter(g)`, where if you then
iterate over the subsequent range, `f` will be invoked twice for every element
that satisfies `g`:

::: bq
```cpp
int main()
{
    std::vector<int> v = {1, 2, 3, 4, 5};

    auto even_squares = v
        | std::views::transform([](int i){
                std::print("transform: {}\n", i);
                return i * i;
            })
        | std::views::filter([](int i){
                std::print("filter: {}\n", i);
                return i % 2 == 0;
            });

    for (int i : even_squares) {
        std::print("Got: {}\n", i);
    }
}
```
:::

prints the following (note that there are 7 invocations of `transform`):

::: bq
```
transform: 1
filter: 1
transform: 2
filter: 4
transform: 2
Got: 4
transform: 3
filter: 9
transform: 4
filter: 16
transform: 4
Got: 16
transform: 5
filter: 25
```
:::

The solution here is to add a layer of caching:

::: bq
```cpp
auto even_squares = v
    | views::transform(square)
    | views::cache_last
    | views::filter(is_even);
```
:::

Which will ensure that `square` will only be called once per element.

:::

# Design

## Caching in `operator*`

This is the only reasonable place for this caching to happen. Caching in
`operator++` would require unnecessary overhead on every traversal if the user
does not need to dereference every iterator (e.g., a striding view).

## Relaxing [res.on.data.races]

Because `operator*` is required to be a `const` member function (the cost of
relaxing that requirement would be prohibitive as it affects every iterator and range adaptor),
yet we want to have it perform a potentially-modifying operation, our options
are basically:

- Make this an exception to [res.on.data.races]{.sref} p3
- Require synchronization.

This paper proposes the former. Input-only iterators, in general, are poor
candidates for sharing across threads because, even when copyable (and they are
not required to be in C++20), they are subject to "spooky action at a distance"
where incrementing one iterator invalidates all copies thereof. This is why
parallel algorithms require at least forward iterators. Sharing
references to the same input iterator across threads seems like a fairly
contrived scenario.

Moreover, `std::istreambuf_iterator` already doesn't meet this requirement
in [every major standard library implementation](https://lists.isocpp.org/lib/2023/03/25724.php)
yet it does not seem to have appeared on any standard library maintainer's radar
in the decade since the publication of C++11. This further suggests that this
guarantee is not relied upon in practice for input-only iterators.

It is true that we could require synchronization on `operator*() const`. This probably
isn't terrible expensive in this context (we only need to protect against
`operator*` calls racing with each other, not them racing with `operator++`),
but adding synchronization to an adaptor whose primary purpose is to improve
performance seems particularly dissatisfying when that synchronization will
almost never be actually necessary.

During the Tokyo SG1 meeting, the room favored a limited carve-out to
[res.on.data.races]{.sref} for this adaptor only. As it turns out, p1 of that
subclause already has "unless otherwise specified", so we don't need to
make any additional modification there.  However, the wording is unclear how
any of the requirements apply to templated functions in the standard library; 
this will be addressed separately as an issue.

## What's the reference type?

range-v3 uses `range_value_t<V>&&`, but this somewhat defeats the purpose of
caching if you can so easily invalidate it. Moreover, there doesn't seem to be
a reason to force an independent copy of the `value_type`. So long as the
underlying iterator is not modified, the reference obtained from `operator*`
should remain valid.

This paper therefore proposes `range_reference_t<V>&`. Note that even if the
reference type is a real reference, it can be an _expensive-to-compute_ reference,
so caching could still make sense.

## Properties

`cache_last` is never borrowed, input-only, never common, and not const-iterable.

## `iter_move` and `iter_swap`

`indirectly_readable` and `indirectly_swappable` requires `iter_move` and `iter_swap`
to respectively not modify `i` (in the [concepts.equality]{.sref} sense).
Moreover, `indirectly_readable` requires `*i` to be equality-preserving. So
the cache should not be invalidated by either operation. (The underlying element
might be modified, but the reference itself, obtained from dereferencing the
iterator, cannot.)

# Wording

This wording is relative to [@N4971].

## Addition to `<ranges>`

Add the following to [ranges.syn]{.sref}, header `<ranges>` synopsis:

```cpp
// [...]
namespace std::ranges {
  // [...]

  // [range.cache.last], to input view
  template<input_range V>
    requires view<V>
  class cache_last_view;

  namespace views {
    inline constexpr $unspecified$ cache_last = $unspecified$;
  }

}

```

## `cache_last`

Add the following subclause to [range.adaptors]{.sref}:

### 26.7.? Cache last view [range.cache.last] {-}

#### 26.7.?.1 Overview [range.cache.last.overview] {-}

[#]{.pnum} `cache_last_view` caches the last element of its underlying sequence
so that the element does not have to be recomputed on repeated access.
[This is useful if computation of the element to produce is expensive.]{.note}

[#]{.pnum} The name `views::cache_last` denotes a range adaptor object ([range.adaptor.object]{.sref}).
Let `E` be an expression. The expression `views​::cache_last(E)` is expression-equivalent to
`cache_last_view(E)`. [Intentional CTAD to avoid double wrapping if `E` is
already a `cache_last_view`.]{.draftnote}

#### 26.7.?.2 Class template `cache_last_view` [range.cache.last.view] {-}

```cpp
template<input_range V>
  requires view<V>
class cache_last_view : public view_interface<cache_last_view<V>>{
  V $base_$ = V();                                                       // exposition only
  using $cache_t$ = conditional_t<is_reference_v<range_reference_t<V>>,  // exposition only
                                add_pointer_t<range_reference_t<V>>,
                                range_reference_t<V>>;

  $non-propagating-cache$<$cache_t$> $cache_$;                               // exposition only

  class $iterator$;                                                      // exposition only
  class $sentinel$;                                                      // exposition only

public:
  cache_last_view() requires default_initializable<V> = default;
  constexpr explicit cache_last_view(V base);

  constexpr V base() const & requires copy_constructible<V> { return $base_$; }
  constexpr V base() && { return std::move($base_$); }

  constexpr auto begin();
  constexpr auto end();

  constexpr auto size() requires sized_range<V>;
  constexpr auto size() const requires sized_range<const V>;
};

template<class R>
  cache_last_view(R&&) -> cache_last_view<views::all_t<R>>;

```

::: itemdecl

```cpp
constexpr explicit cache_last_view(V base);
```

[#]{.pnum} _Effects_: Initializes `$base_$` with  `std::move(base)`.

```cpp
constexpr auto begin();
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
return $iterator$(*this);
```
:::

```cpp
constexpr auto end();
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
return $sentinel$(*this);
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

#### 26.7.?.3 Class `cache_last_view::$iterator$` [range.cache.last.iterator] {-}

```cpp
namespace std::ranges {
  template<input_range V>
    requires view<V>
  class cache_last_view<V>::$iterator$ {
    cache_last_view* $parent_$;                                 // exposition only
    iterator_t<V> $current_$;                                   // exposition only

    constexpr explicit $iterator$(cache_last_view& parent);     // exposition only

  public:
    using difference_type = range_difference_t<V>;
    using value_type = range_value_t<V>;
    using iterator_concept = input_iterator_tag;

    $iterator$($iterator$&&) = default;
    $iterator$& operator=($iterator$&&) = default;

    constexpr iterator_t<V> base() &&;
    constexpr const iterator_t<V>& base() const & noexcept;

    constexpr range_reference_t<V>& operator*() const;

    constexpr $iterator$& operator++();
    constexpr void operator++(int);

    friend constexpr range_rvalue_reference_t<V> iter_move(const $iterator$& i)
      noexcept(noexcept(ranges::iter_move(i.$current_$)));

    friend constexpr void iter_swap(const $iterator$& x, const $iterator$& y)
      noexcept(noexcept(ranges::iter_swap(x.$current_$, y.$current_$)))
      requires indirectly_swappable<iterator_t<V>>;
  };
}
```

::: itemdecl

```cpp
constexpr explicit $iterator$(cache_last_view& parent);
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `ranges::begin(parent.$base_$)`
and `$parent_$` with `addressof(parent)`.

```cpp
constexpr iterator_t<V> base() &&;
```
[#]{.pnum} _Returns_: `std::move($current_$)`.

```cpp
constexpr const iterator_t<V>& base() const & noexcept;
```
[#]{.pnum} _Returns_: `$current_$`.

```cpp
constexpr $iterator$& operator++();
```

[#]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
   ++$current_$;
   $parent_$->$cache_$.reset();
   return *this;
```
:::

```cpp
constexpr void operator++(int);
```

[#]{.pnum} _Effects_: Equivalent to: `++*this;`

```cpp
constexpr range_reference_t<V>& operator*() const;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  if constexpr (is_reference_v<range_reference_t<V>>) {
    if (!$parent_$->$cache_$) {
      $parent_$->$cache_$ = addressof($as-lvalue$(*$current_$));
    }
    return **$parent_$->$cache_$;
  }
  else {
    if (!$parent_$->$cache_$) {
      $parent_$->$cache_$.$emplace-deref$($current_$);
    }
    return *$parent_$->$cache_$;
  }
```
:::

[#]{.pnum} [Evaluations of `operator*` on the same iterator object may conflict ([intro.races]{.sref}).]{.note}

```cpp
friend constexpr range_rvalue_reference_t<V> iter_move(const $iterator$& i)
  noexcept(noexcept(ranges::iter_move(i.$current_$)));
```

[#]{.pnum} _Effects_: Equivalent to: `return ranges::iter_move(i.$current_$);`


```cpp
friend constexpr void iter_swap(const $iterator$& x, const $iterator$& y)
  noexcept(noexcept(ranges::iter_swap(x.$current_$, y.$current_$)))
  requires indirectly_swappable<iterator_t<V>>;
```

[#]{.pnum} _Effects_: Equivalent to: `ranges::iter_swap(x.$current_$, y.$current_$);`

:::

#### 26.7.?.3 Class `cache_last_view::$sentinel$` [range.cache.last.sentinel] {-}

```cpp
namespace std::ranges {
  template<input_range V>
    requires view<V>
  class cache_last_view<V>::$sentinel$ {
    sentinel_t<V> $end_$ = sentinel_t<V>();               // exposition only

    constexpr explicit $sentinel$(cache_last_view& parent);   // exposition only

  public:
    $sentinel$() = default;

    constexpr sentinel_t<V> base() const;

    friend constexpr bool operator==(const $iterator$& x, const $sentinel$& y);
  };
}
```

::: itemdecl

```cpp
constexpr explicit $sentinel$(cache_last_view& parent);
```

[#]{.pnum} _Effects_: Initializes `$end_$` with `ranges::end(parent.$base_$)`.

```cpp
constexpr sentinel_t<V> base() const;
```

[#]{.pnum} _Returns:_ `$end_$`.

```cpp
friend constexpr bool operator==(const $iterator$& x, const $sentinel$& y);
```

[#]{.pnum} _Returns:_ `x.$current_$ == y.$end_$;`

:::

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
