---
title: "`views::chunk_by`"
document: P2443R0
date: today
audience:
  - LEWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: true
---

# Abstract
This paper proposes the range adaptor `views::chunk_by` as described in
section 4.3 of [@P2214R1].

# Example

```cpp
std::vector v = {1, 2, 2, 3, 0, 4, 5, 2};
fmt::print("{}\n", v | std::views::chunk_by(ranges::less_equal{}));   // [[1, 2, 2, 3], [0, 4, 5], [2]]
```

# Design
Section 4.3 of [@P2214R1] contains an extensive discussion of `chunk_by` and
similar range algorithms in numerous other languages. The discussion here
assumes familiarity with that paper.

## Predicate, not equivalence
D's `chunkBy` [requires](https://dlang.org/library/std/algorithm/iteration/chunk_by.html)
the predicate to be an equivalence relation. The initial implementation of
range-v3's `group_by` appeared to tacitly assume this as well, as it was not
functional [if `pred(*first, *first)` returns `false`](https://github.com/ericniebler/range-v3/issues/1393).

There does not appear to be a compelling reason to require an equivalence relation.
Indeed, D provides virtually the same functionality for general predicates
under the name `splitWhen`. The `chunk_by` proposed in this paper therefore
does not require equivalence.

## No input ranges

Since `chunk_by` needs to evaluate the predicate on adjacent elements, it
requires forward ranges. Caching elements is not considered a viable approach,
essentially for the reasons discussed in section 4.3.4 of [@P2321R2].

## Properties

`chunk_by` is bidirectional if the underlying range is; otherwise, it is forward.
It is common if the underlying range is. It's never borrowed or sized.

## Caching
Similar to `split`, `chunk_by` calculates the end of the first range in its
`begin` and caches it to meet the amortized `O(1)` requirement. That means that
it does not support const-iteration.

## Implementation experience

`views::group_by` has long been implemented in range-v3, with the difference that
it compares against the first element of the group instead of the previous element.
A [`views::chunk_by`](https://github.com/ericniebler/range-v3/pull/1648) with
the semantics proposed in this paper (except for bidirectional iteration support) has
recently been added to range-v3. I also have implemented a version that directly
follows the proposed wording below without issue.

# Wording

## Addition to `<ranges>`

Add the following to [ranges.syn]{.sref}, header `<ranges>` synopsis:

```cpp
// [...]
namespace std::ranges {
  // [...]

  // [range.chunk.by], chunk by view
  template<forward_range V, indirect_binary_predicate<iterator_t<V>, iterator_t<V>> Pred>
    requires view<V> && is_object_v<Pred>
  class chunk_by_view;

  namespace views {
    inline constexpr $unspecified$ chunk_by = $unspecified$;
  }

}

```

## `chunk_by`

Add the following subclause to [range.adaptors]{.sref}.

### 24.7.? Chunk by view [range.chunk.by] {-}

#### 24.7.?.1 Overview [range.chunk.by.overview] {-}

[#]{.pnum} `chunk_by_view` takes a `view` and a predicate, and splits the view
into `subrange`s between each pair of adjacent elements for which the predicate
returns `false`.

[#]{.pnum} The name `views::chunk_by` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given subexpressions `E` and `F`,
the expression `views::chunk_by(E, F)` is expression-equivalent to
`chunk_by_view(E, F)`.

::: example

```cpp
vector v = {1, 2, 2, 3, 0, 4, 5, 2};

for (auto r : v | views::chunk_by(ranges::less_equal{})) {
  cout << '[';
  auto sep = "";
  for(auto i : r) {
    cout << sep << i;
    sep = ", ";
  }
  cout << "] ";
}
// prints: [1, 2, 2, 3] [0, 4, 5] [2]

```
:::

#### 24.7.?.2 Class template `chunk_by_view` [range.chunk.by.view] {-}

```cpp
namespace std::ranges {

template<forward_range V, indirect_binary_predicate<iterator_t<V>, iterator_t<V>> Pred>
  requires view<V> && is_object_v<Pred>
class chunk_by_view : public view_interface<chunk_by_view<V, Pred>>{
  V $base_$ = V();                          // exposition only
  $copyable-box$<Pred> $pred_$ = Pred();      // exposition only

  class $iterator$;                         // exposition only

public:
  chunk_by_view() requires default_initializable<V> && default_initializable<Pred> = default;
  constexpr explicit chunk_by_view(V base, Pred pred);

  constexpr V base() const & requires copy_constructible<V> { return $base_$; }
  constexpr V base() && { return std::move($base_$); }

  constexpr const Pred& pred() const;

  constexpr $iterator$ begin();
  constexpr auto end();

  constexpr iterator_t<V> $find-next$(iterator_t<V>); // exposition only
  constexpr iterator_t<V> $find-prev$(iterator_t<V>) requires bidirectional_range<V>; // exposition only
};

template<class R, class Pred>
  chunk_by_view(R&&, Pred) -> chunk_by_view<views::all_t<R>, Pred>;

}
```

::: itemdecl

```cpp
constexpr explicit chunk_by_view(V base, Pred pred);
```

[#]{.pnum} _Effects_: Initializes `$base_$` with `std::move(base)`
and `$pred_$` with `std::move(pred)`.

```cpp
constexpr const Pred& pred() const;
```

[#]{.pnum} _Effects_: Equivalent to `return *$pred_$;`

```cpp
constexpr $iterator$ begin();
```

[#]{.pnum} _Preconditions:_ `$pred_$.has_value()` is `true`.

[#]{.pnum} _Returns_: `$iterator$(*this, ranges::begin($base_$), $find-next$(ranges::begin($base_$)))`.

[#]{.pnum} _Remarks_: In order to provide the amortized constant-time complexity
required by the `range` concept, this function caches the result within the
`chunk_by_view` for use on subsequent calls.

```cpp
constexpr auto end();
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
if constexpr (common_range<V>) {
  return $iterator$(*this, ranges::end($base_$), ranges::end($base_$));
}
else {
  return default_sentinel;
}
```
:::

```cpp
constexpr iterator_t<V> $find-next$(iterator_t<V> cur); // exposition only
```

[#]{.pnum} _Preconditions:_ `$pred_$.has_value()` is `true`.

[#]{.pnum} _Returns_: `ranges::next(ranges::adjacent_find(cur, ranges::end($base_$), not_fn(ref(*$pred_$))), 1, ranges::end($base_$))`.


```cpp
constexpr iterator_t<V> $find-prev$(iterator_t<V> cur) requires bidirectional_range<V>; // exposition only
```
[#]{.pnum} _Preconditions:_ `cur` is not equal to `ranges::begin($base_$)`. `$pred_$.has_value()` is `true`.

[#]{.pnum} _Returns_: An iterator `i` in the range `[ranges::begin($base_$), cur)` such that:

- [#.#]{.pnum} `ranges::adjacent_find(i, cur, not_fn(ref(*$pred_$)))` is equal to `cur`; and
- [#.#]{.pnum} if `i` is not equal to `ranges::begin($base_$)`, then `bool((*$pred_$)(*ranges::prev(i), *i))` is `false`.

::: draftnote

Reference implementation:

```cpp
  using namespace std::placeholders;
  reverse_view rv(subrange(ranges::begin(base_), cur));
  return ranges::prev(ranges::adjacent_find(rv, not_fn(bind(ref(*pred_), _2, _1))).base(),
                      1, ranges::begin(base_));
```
:::

:::

#### 24.7.?.3 Class `chunk_by_view::$iterator$` [range.chunk.by.iter] {-}

```cpp
namespace std::ranges {
  template<forward_range V, indirect_binary_predicate<iterator_t<V>, iterator_t<V>> Pred>
    requires view<V> && is_object_v<Pred>
  class chunk_by_view<V, Pred>::$iterator$ {
    chunk_by_view* $parent_$ = nullptr;                       // exposition only
    iterator_t<V> $current_$ = iterator_t<V>();               // exposition only
    iterator_t<V> $next_$    = iterator_t<V>();               // exposition only

    constexpr $iterator$(chunk_by_view& parent, iterator_t<V> current, iterator_t<V> next);  // exposition only

  public:
    using value_type = subrange<iterator_t<V>>;
    using difference_type  = range_difference_t<V>;
    using iterator_category = input_iterator_tag;
    using iterator_concept = $see below$;

    $iterator$() = default;

    constexpr value_type operator*() const;
    constexpr $iterator$& operator++();
    constexpr $iterator$ operator++(int);

    constexpr $iterator$& operator--() requires bidirectional_range<V>;
    constexpr $iterator$ operator--(int) requires bidirectional_range<V>;

    friend constexpr bool operator==(const $iterator$& x, const $iterator$& y);
    friend constexpr bool operator==(const $iterator$& x, default_sentinel_t);
  };
}
```

[#]{.pnum} `$iterator$::iterator_concept` is defined as follows:

- [#.#]{.pnum} If `V` models `bidirectional_range`, then `iterator_concept` denotes `bidirectional_iterator_tag`.
- [#.#]{.pnum} Otherwise, `iterator_concept` denotes `forward_iterator_tag`.

::: itemdecl

```cpp
constexpr $iterator$(chunk_by_view& parent, iterator_t<V> current, iterator_t<V> next);
```

[#]{.pnum} _Effects_: Initializes `$parent_$` with `addressof(parent)`,
`$current_$` with `current`, and `$next_$` with `next`.

```cpp
constexpr value_type operator*() const;
```

[#]{.pnum} _Preconditions_: `$current_$` is not equal to `$next_$`.

[#]{.pnum} _Returns_: `subrange($current_$, $next_$)`.

```cpp
constexpr $iterator$& operator++();
```

[#]{.pnum} _Preconditions_: `$current_$` is not equal to `$next_$`.

[#]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
   $current_$ = $next_$;
   $next_$ = $parent_$->$find-next$($current_$);
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
constexpr $iterator$& operator--() requires bidirectional_range<V>;
```

[#]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
   $next_$ = $current_$;
   $current_$ = $parent_$->$find-prev$($next_$);
   return *this;
```
:::

```cpp
constexpr $iterator$ operator--(int) requires bidirectional_range<V>;
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
friend constexpr bool operator==(const $iterator$& x, const $iterator$& y);
```

[#]{.pnum} _Returns:_ `x.$current_$ == y.$current_$`.

```cpp
friend constexpr bool operator==(const $iterator$& x, default_sentinel_t);
```

[#]{.pnum} _Returns:_ `x.$current_$ == x.$next_$`.

:::

## Feature-test macro

Add the following macro definition to [version.syn]{.sref}, header `<version>`
synopsis, with the value selected by the editor to reflect the date of adoption
of this paper:

```cpp
#define __cpp_lib_ranges_chunk_by 20XXXXL // also in <ranges>
```

---
references:
    - id: P2214R1
      citation-label: P2214R1
      title: A Plan for C++23 Ranges
      author:
        - family: Barry Revzin, Conor Hoekstra, Tim Song
      issued:
        year: 2021
      URL: https://wg21.link/p2214r1
---
