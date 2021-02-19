---
title: "`adjacent`"
document: DXXXXR0
date: today
audience:
  - LEWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: true
---

# Abstract
This paper proposes two views, `adjacent` and `adjacent_transform`, as described in section 3.2 of [@P2214R0].

# Discussion

As `adjacent` is a specialized version of `zip`, most of the discussion in
[@P2321R0] applies, _mutatis mutandis_, to this paper, and will not be repeated here.

## Naming
The wording below tentatively uses `adjacent` for the general functionality,
and `pairwise` for the `N == 2` case. [@P2214R0] section 3.2.5 suggests
an alternative (`slide_as_tuple` for the general functionality and `adjacent`
for the `N == 2` case). The author has a mild preference for the current
names due to the somewhat unwieldiness of the name `slide_as_tuple`.

## Value type
The value type of `adjacent_view` is a homogeneous `tuple` or `pair`. Since `array`
cannot hold references and is defined to be an aggregate, using it as the value
type poses significant usability issues (even if we somehow get the
`common_reference_with` requirements in `indirectly_readable` to work with even more
`tuple`/`pair` changes).

## `common_range`
One notable difference from `zip` is that since `adjacent` comes from a single underlying view,
it can be a `common_range` whenever its underlying view is.

## No input ranges
Because `adjacent` by definition holds multiple iterators to the same view,
it requires forward ranges. It is true that the `N == 1` case could theoretically
support input ranges, but that seems entirely pointless and adds extra complexity.

Plus, users could just use `zip` instead.

## `iter_swap`

Since the iterators of `adjacent_view` refer to potentially overlapping elements
of the underlying view, `iter_swap` cannot really "exchange the values" of the
range elements when the iterators overlap. However, it does not appear to be possible
to disable `ranges::iter_swap` (deleting or not providing `iter_swap` will simply
fallback to the default implementation), and swapping non-overlapping iterators
is still useful functionality. Thus, the wording below retains `iter_swap` but gives
it a precondition that there is no overlap.


# Wording

This wording is relative to [@N4878].

## Addition to `<ranges>`

Add the following to [ranges.syn]{.sref}, header `<ranges>` synopsis:

```cpp
// [...]
namespace std::ranges {
  // [...]

  // [range.adjacent], adjacent view
  template<forward_range V, size_t N>
      requires view<V> && (N > 0)
  class adjacent_view;

  template<class V, size_t N>
  inline constexpr bool enable_borrowed_range<adjacent_view<V, N>>
      = enable_borrowed_range<V>;

  namespace views {
    template<size_t N>
    inline constexpr @_unspecified_@ adjacent = @_unspecified_@;
    inline constexpr auto pairwise = adjacent<2>;
  }

  // [range.adjacent.transform], adjacent transform view
  template<forward_range V, copy_constructible F, size_t N>
    requires @_see below_@
  class adjacent_transform_view;

  namespace views {
    template<size_t N>
    inline constexpr @_unspecified_@ adjacent_transform = @_unspecified_@;
    inline constexpr auto pairwise_transform = adjacent_transform<2>;
  }
}

```

## `adjacent`

Add the following subclause to [range.adaptors]{.sref}.

### 24.7.? Adjacent view [range.adjacent] {-}

#### 24.7.?.1 Overview [range.adjacent.overview] {-}

[1]{.pnum} `adjacent_view` takes a `view` and produces a `view` whose
_M_ <sup>th</sup> element is a `tuple` or `pair` of the M <sup>th</sup> through
(_M_ + _N_ - 1)<sup>th</sup> elements of the original view. If the original
view has fewer than _N_ elements, the resulting view is empty.

[2]{.pnum} The name `views::adjacent<N>` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given a subexpression `E` and a constant expression `N`,
the expression `views::adjacent<N>(E)` is expression-equivalent to

- [2.1]{.pnum} `(void)E, @_decay-copy_@(views::empty<tuple<>>)` if `N` is equal to `0`,
- [2.2]{.pnum} otherwise, `adjacent_view<views::all_t<decltype((E))>, N>(E)`.

[3]{.pnum} Define `@_REPEAT_@(T, N)` as a pack of _N_ types, each of which denotes the same type as `T`.

#### 24.7.?.2 Class template `adjacent_view` [range.adjacent.view] {-}

```cpp
namespace std::ranges {

template<forward_range V, size_t N>
  requires view<V> && (N > 0)
class adjacent_view : public view_interface<adjacent_view<V, N>>{
  V @_base\__@ = V();                     // exposition only

  template<bool> class @_iterator_@;     // exposition only
  template<bool> class @_sentinel_@;     // exposition only

  struct @_as\_sentinel_@{};              // exposition only

public:
  constexpr adjacent_view() = default;
  constexpr explicit adjacent_view(V base) : @_base\__@(std::move(base)) {}

  constexpr auto begin() requires (!@_simple-view_@<V>) {
    return @_iterator_@<false>(ranges::begin(@_base\__@), ranges::end(@_base\__@));
  }

  constexpr auto begin() const requires range<const V> {
    return @_iterator_@<true>(ranges::begin(@_base\__@), ranges::end(@_base\__@));
  }

  constexpr auto end() requires (!@_simple-view_@<V> && !common_range<V>) {
    return @_sentinel_@<false>(ranges::end(@_base\__@));
  }

  constexpr auto end() requires (!@_simple-view_@<V> && common_range<V>){
    return @_iterator_@<false>(@_as\_sentinel_@{}, ranges::begin(@_base\__@), ranges::end(@_base\__@));
  }

  constexpr auto end() const requires range<const V> {
    return @_sentinel_@<true>(ranges::end(@_base\__@));
  }

  constexpr auto end() const requires common_range<const V> {
    return @_iterator_@<true>(@_as\_sentinel_@{}, ranges::begin(@_base\__@), ranges::end(@_base\__@));
  }

  constexpr auto size() requires sized_range<V> {
    auto sz = ranges::size(@_base\__@);
    sz -= ranges::min<decltype(sz)>(sz, N-1);
    return sz;
  }

  constexpr auto size() const requires sized_range<const V> {
    auto sz = ranges::size(@_base\__@);
    sz -= ranges::min<decltype(sz)>(sz, N-1);
    return sz;
  }
};

}
```

#### 24.7.?.3 Class template `adjacent_view::@_iterator_@` [range.adjacent.iterator] {-}

```cpp
namespace std::ranges {
  template<forward_range V, size_t N>
    requires view<V> && (N > 0)
  template<bool Const>
  class adjacent_view<V, N>::@_iterator_@ {
    using @_Base_@ = @_maybe-const_@<Const, V>;                                             // exposition only
    array<iterator_t<@_Base_@>, N> @_current\__@ = array<iterator_t<@_Base_@>, N>();             // exposition only
    constexpr @_iterator_@(iterator_t<@_Base_@> first, sentinel_t<@_Base_@> last);              // exposition only
    constexpr @_iterator_@(as_sentinel, iterator_t<@_Base_@> first, iterator_t<@_Base_@> last); // exposition only
  public:
    using iterator_category = input_iterator_tag;
    using iterator_concept  = @_see below_@;
    using value_type = @_tuple-or-pair_@<@_REPEAT_@(range_value_t<@_Base_@>, N)...>;
    using difference_type = range_difference_t<@_Base_@>;

    @_iterator_@() = default;
    constexpr @_iterator_@(@_iterator_@<!Const> i)
      requires Const && convertible_to<iterator_t<V>, iterator_t<@_Base_@>>;

    constexpr auto operator*() const;
    constexpr @_iterator_@& operator++();
    constexpr @_iterator_@ operator++(int);

    constexpr @_iterator_@& operator--() requires bidirectional_range<@_Base_@>;
    constexpr @_iterator_@ operator--(int) requires bidirectional_range<@_Base_@>;

    constexpr @_iterator_@& operator+=(difference_type x)
      requires random_­access_­range<@_Base_@>;
    constexpr @_iterator_@& operator-=(difference_type x)
      requires random_­access_­range<@_Base_@>;

    constexpr auto operator[](difference_type n) const
      requires random_­access_­range<@_Base_@>;

    friend constexpr bool operator==(const @_iterator_@& x, const @_iterator_@& y);

    friend constexpr bool operator<(const @_iterator_@& x, const @_iterator_@& y)
      requires random_­access_­range<@_Base_@>;
    friend constexpr bool operator>(const @_iterator_@& x, const @_iterator_@& y)
      requires random_­access_­range<@_Base_@>;
    friend constexpr bool operator<=(const @_iterator_@& x, const @_iterator_@& y)
      requires random_­access_­range<@_Base_@>;
    friend constexpr bool operator>=(const @_iterator_@& x, const @_iterator_@& y)
      requires random_­access_­range<@_Base_@>;
    friend constexpr auto operator<=>(const @_iterator_@& x, const @_iterator_@& y)
      requires random_­access_­range<@_Base_@> &&
               three_­way_­comparable<iterator_t<@_Base_@>>;

    friend constexpr @_iterator_@ operator+(const @_iterator_@& i, difference_type n)
      requires random_­access_­range<@_Base_@>;
    friend constexpr @_iterator_@ operator+(difference_type n, const @_iterator_@& i)
      requires random_­access_­range<@_Base_@>;
    friend constexpr @_iterator_@ operator-(const @_iterator_@& x, difference_type y)
      requires random_­access_­range<@_Base_@>;
    friend constexpr difference_type operator-(const @_iterator_@& x, const @_iterator_@& y)
      requires sized_sentinel_for<iterator_t<@_Base_@>, iterator_t<@_Base_@>>;

    friend constexpr auto iter_move(const @_iterator_@& i) noexcept(@_see below_@);

    friend constexpr auto iter_swap(const @_iterator_@& l, const @_iterator_@& r)
      noexcept(@_see below_@)
      requires indirectly_swappable<iterator_t<@_Base_@>>;
  };
}
```

[1]{.pnum} `@_iterator_@::iterator_concept` is defined as follows:

- [1.1]{.pnum} If `V` models `random_access_range`, then `iterator_concept` denotes `random_access_iterator_tag`.
- [1.2]{.pnum} Otherwise, if `V` models `bidirectional_­range`, then `iterator_concept` denotes `bidirectional_­iterator_­tag`.
- [1.3]{.pnum} Otherwise, `iterator_concept` denotes `forward_iterator_tag`.


::: itemdecl

```cpp
constexpr @_iterator_@(iterator_t<@_Base_@> first, sentinel_t<@_Base_@> last);
```

[2]{.pnum} _Postconditions_: `@_current\__[0]@ == first` is `true`, and
for every integer _i_ in `[1, N)`,
`@_current\__@[@_i_@] == ranges::next(@_current\__@[@_i_@-1], 1, last)` is `true`.

```cpp
constexpr @_iterator_@(as_sentinel, iterator_t<@_Base_@> first, iterator_t<@_Base_@> last);
```

[3]{.pnum} _Postconditions_: If `@_Base_@` does not model `bidirectional_range`,
each element of `@_current\__@` is equal to `last`.
Otherwise, `@_current\__[N-1]@ == last` is `true`, and
for every integer _i_ in `[0, N-1)`,
`@_current\__@[@_i_@] == ranges::prev(@_current\__@[@_i_@+1], 1, first)` is `true`.

```cpp
constexpr @_iterator_@(@_iterator_@<!Const> i)
  requires Const && (convertible_to<iterator_t<V>, iterator_t<@_Base_@>>;
```

[4]{.pnum} _Effects_: Initializes each element of `@_current\__@` with the corresponding element of `i.@_current\__@` as an xvalue.

```cpp
  constexpr auto operator*() const;
```

[5]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return @_tuple-transform_@([](auto& i) -> decltype(auto) { return *i; }, @_current\__@);
```
:::

```cpp
constexpr @_iterator_@& operator++();
```
[6]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  ranges::copy(@_current\__@ | views::drop(1), @_current\__@.begin());
  ++@_current\__@.back();
  return *this;
```
:::

```cpp
constexpr @_iterator_@ operator++(int);
```

[7]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto tmp = *this;
  ++*this;
  return tmp;
```
:::


```cpp
constexpr @_iterator_@& operator--() requires bidirectional_range<@_Base_@>;
```
[8]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  ranges::copy_backward(@_current\__@ | views::take(N - 1), @_current\__@.end());
  --@_current\__@.front();
  return *this;
```
:::


```cpp
constexpr @_iterator_@ operator--(int) requires bidirectional_range<@_Base_@>;
```
[9]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto tmp = *this;
  --*this;
  return tmp;
```
:::

```cpp
constexpr @_iterator_@& operator+=(difference_type x)
  requires random_­access_­range<@_Base_@>;
```
[10]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  for(auto& i : @_current\__@) { i += x; }
  return *this;
```
:::

```cpp
  constexpr @_iterator_@& operator-=(difference_type x)
    requires random_­access_­range<@_Base_@>;
```
[11]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  for(auto& i : @_current\__@) { i -= x; }
  return *this;
```
:::

```cpp
constexpr auto operator[](difference_type n) const
  requires random_­access_­range<@_Base_@>;
```
[12]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return @_tuple-transform_@([&](auto& i) -> decltype(auto) { return i[n]; }, @_current\__@);
```
:::

```cpp
friend constexpr bool operator==(const @_iterator_@& x, const @_iterator_@& y);
```
[13]{.pnum} _Effects_: Equivalent to: `return x.@_current\__@.back() == y.@_current\__@.back()`.

```cpp
friend constexpr bool operator<(const @_iterator_@& x, const @_iterator_@& y)
  requires random_­access_­range<@_Base_@>;
```
[14]{.pnum} _Effects_: Equivalent to: `return x.@_current\__@.back() < y.@_current\__@.back(); `

```cpp
friend constexpr bool operator>(const @_iterator_@& x, const @_iterator_@& y)
  requires random_­access_­range<@_Base_@>;
```
[15]{.pnum} _Effects_: Equivalent to: `return y < x; `

```cpp
friend constexpr bool operator<=(const @_iterator_@& x, const @_iterator_@& y)
  requires random_­access_­range<@_Base_@>;
```

[16]{.pnum} _Effects_: Equivalent to: `return !(y < x); `


```cpp
friend constexpr bool operator>=(const @_iterator_@& x, const @_iterator_@& y)
  requires random_­access_­range<@_Base_@>;
```

[17]{.pnum} _Effects_: Equivalent to: `return !(x < y); `

```cpp
friend constexpr auto operator<=>(const @_iterator_@& x, const @_iterator_@& y)
  requires random_­access_­range<@_Base_@> &&
           three_­way_­comparable<iterator_t<@_Base_@>>;
```

[18]{.pnum} _Effects_: Equivalent to: `return x.@_current\__@.back() <=> y.@_current\__@.back(); `


```cpp
friend constexpr @_iterator_@ operator+(const @_iterator_@& i, difference_type n)
  requires random_­access_­range<@_Base_@>;
friend constexpr @_iterator_@ operator+(difference_type n, const @_iterator_@& i)
  requires random_­access_­range<@_Base_@>;
```

[19]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto r = i;
  r += n;
  return r;
```
:::

```cpp
friend constexpr @_iterator_@ operator-(const @_iterator_@& x, difference_type y)
  requires random_­access_­range<@_Base_@>;
```

[20]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto r = x;
  r -= y;
  return r;
```
:::

```cpp
friend constexpr difference_type operator-(const @_iterator_@& x, const @_iterator_@& y)
  requires sized_sentinel_for<iterator_t<@_Base_@>, iterator_t<@_Base_@>>;
```
[21]{.pnum} _Effects_: Equivalent to: `return x.@_current\__@.back() - y.@_current\__@.back()`.

```cpp
friend constexpr auto iter_move(const @_iterator_@& i) noexcept(@_see below_@);
```

[22]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return @_tuple-transform_@(ranges::iter_move, i.@_current\__@);
```
:::

[23]{.pnum} _Remarks:_ The expression within `noexcept` is equivalent to

::: bq
```cpp
  noexcept(ranges::iter_move(declval<iterator_t<@_Base_@>>())) &&
  is_nothrow_move_constructible_v<range_rvalue_reference_t<@_Base_@>>
```
:::

```cpp
friend constexpr auto iter_swap(const @_iterator_@& l, const @_iterator_@& r)
  noexcept(@_see below_@)
  requires indirectly_swappable<iterator_t<@_Base_@>>;
```
[24]{.pnum} _Preconditions:_ None of the iterators in `l.@_current\__@` is equal to an iterator in `r.@_current\__@`.

[25]{.pnum} _Effects_: For every integer _i_ in `[0, N)`,
performs `ranges::iter_swap(l.@_current\__@[@_i_@], r.@_current\__@[@_i_@])`.

[26]{.pnum} _Remarks:_ The expression within `noexcept` is equivalent to:

::: bq
```cpp
  noexcept(ranges::iter_swap(declval<iterator_t<@_Base_@>>(), declval<iterator_t<@_Base_@>>()))
```
:::

:::

#### 24.7.?.4 Class template `adjacent_view::@_sentinel_@` [range.adjacent.sentinel] {-}

```cpp
namespace std::ranges {
  namespace std::ranges {
  template<forward_range V, size_t N>
    requires view<V> && (N > 0)
  template<bool Const>
  class adjacent_view<V, N>::@_sentinel_@ {
    using @_Base_@ = @_maybe-const_@<Const, V>;                     // exposition only
    sentinel_t<@_Base_@> @_end\__@ = sentinel_t<@_Base_@>();            // exposition only
    constexpr explicit @_sentinel_@(sentinel_t<@_Base_@> end);      // exposition only
  public:
    @_sentinel_@() = default;
    constexpr @_sentinel_@(@_sentinel_@<!Const> i)
      requires Const && convertible_to<sentinel_t<V>, sentinel_t<@_Base_@>>;

    template<bool OtherConst>
      requires sentinel_­for<sentinel_t<@_Base_@>, iterator_t<@_maybe-const_@<OtherConst, V>>>
    friend constexpr bool operator==(const @_iterator_@<OtherConst>& x, const @_sentinel_@& y);

    template<bool OtherConst>
      requires sized_­sentinel_­for<sentinel_t<@_Base_@>, iterator_t<@_maybe-const_@<OtherConst, V>>>
    friend constexpr range_difference_t<@_maybe-const_@<OtherConst, V>>
      operator-(const @_iterator_@<OtherConst>& x, const @_sentinel_@& y);

    template<bool OtherConst>
      requires sized_­sentinel_­for<sentinel_t<@_Base_@>, iterator_t<@_maybe-const_@<OtherConst, V>>>
    friend constexpr range_difference_t<@_maybe-const_@<OtherConst, V>>
      operator-(const @_sentinel_@& y, const @_iterator_@<OtherConst>& x);
  };
}
```
::: itemdecl

```cpp
constexpr explicit @_sentinel_@(sentinel_t<@_Base_@> end);
```

[1]{.pnum} _Effects_: Initializes `@_end\__@` with `end`.

```cpp
constexpr @_sentinel_@(@_sentinel_@<!Const> i)
  requires Const && convertible_to<sentinel_t<V>, sentinel_t<@_Base_@>>;
```

[2]{.pnum} _Effects_: Initializes `@_end\__@` with `std::move(i.@_end\__@)`.

```cpp
template<bool OtherConst>
  requires sentinel_­for<sentinel_t<@_Base_@>, iterator_t<@_maybe-const_@<OtherConst, V>>>
friend constexpr bool operator==(const @_iterator_@<OtherConst>& x, const @_sentinel_@& y);
```

[3]{.pnum} _Effects_: Equivalent to: `return x.@_current\__@.back() == y.@_end\__@;`.


```cpp
template<bool OtherConst>
  requires sized_­sentinel_­for<sentinel_t<@_Base_@>, iterator_t<@_maybe-const_@<OtherConst, V>>>
friend constexpr range_difference_t<@_maybe-const_@<OtherConst, V>>
  operator-(const @_iterator_@<OtherConst>& x, const @_sentinel_@& y);
```
[4]{.pnum} _Effects_: Equivalent to: `return x.@_current\__@.back() - y.@_end\__@;`.

```cpp
template<bool OtherConst>
  requires sized_­sentinel_­for<sentinel_t<@_Base_@>, iterator_t<@_maybe-const_@<OtherConst, V>>>
friend constexpr range_difference_t<@_maybe-const_@<OtherConst, V>>
  operator-(const @_sentinel_@& y, const @_iterator_@<OtherConst>& x);
```
[5]{.pnum} _Effects_: Equivalent to: `return y.@_end\__@ - x.@_current\__@.back();`.

:::

## `adjacent_transform`


Add the following subclause to [range.adaptors]{.sref}.

### 24.7.? Adjacent transform view [range.adjacent.transform] {-}

#### 24.7.?.1 Overview [range.adjacent.transform.overview] {-}

[1]{.pnum} `adjacent_transform_view` takes an invocable object and a `view`
and produces a `view` whose _M <sup>th</sup>_ element is the result of applying
the invocable object to the _M_ <sup>th</sup> through (_M_ + _N_ - 1)<sup>th</sup>
elements of the original view. If the original view has fewer than _N_ elements,
the resulting view is empty.

[2]{.pnum} The name `views::adjacent_transform<N>` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given subexpressions `E` and `F`,

- [2.1]{.pnum} if `N` is equal to 0, `views::adjacent_transform<N>(E, F)` is expression-equivalent to `(void)E, views::zip_transform(F)`, except that the evaluations of `E` and `F` are indeterminately sequenced.
- [2.2]{.pnum} Otherwise, the expression `views::adjacent_transform<N>(E, F)` is expression-equivalent to `adjacent_transform_view<views::all_t<decltype((E))>, decay_t<F>, N>(E, F)`.

#### 24.7.?.2 Class template `adjacent_transform_view` [range.adjacent.transform.view] {-}

```cpp
namespace std::ranges {
  template<forward_range V, copy_constructible F, size_t N>
   requires view<V> && (N > 0) && is_object_v<F> &&
            regular_invocable<F&, @_REPEAT_@(range_reference_t<V>, N)...> &&
            @_can-reference_@<invoke_result_t<F&, @_REPEAT_@(range_reference_t<V>, N)...>>
  class adjacent_transform_view : public view_interface<adjacent_transform_view<V, F, N>> {
  @_semiregular-box_@<F> @_fun\__@;                  // exposition only
  adjacent_view<V, N> @_inner\__@;               // exposition only

  using @_InnerView_@ = adjacent_view<V, N>;    // exposition only
  template<bool Const>
  using @_inner-iterator_@ = iterator_t<@_maybe-const_@<Const, @_InnerView_@>>;  // exposition only
  template<bool Const>
  using @_inner-sentinel_@ = sentinel_t<@_maybe-const_@<Const, @_InnerView_@>>;  // exposition only

  template<bool> class @_iterator_@;         // exposition only
  template<bool> class @_sentinel_@;         // exposition only

public:
  constexpr adjacent_transform_view() = default;

  constexpr explicit adjacent_transform_view(V base, F fun)
    : @_fun\__@(std::move(fun)), @_inner\__@(std::move(base)) {}

  constexpr auto begin() {
    return @_iterator_@<false>(*this, @_inner\__@.begin());
  }

  constexpr auto begin() const
    requires range<const @_InnerView_@> &&
             regular_invocable<const F&, @_REPEAT_@(range_reference_t<const V>, N)...>
  {
    return @_iterator_@<true>(*this, @_inner\__@.begin());
  }

  constexpr auto end() {
    return @_sentinel_@<false>(@_inner\__@.end());
  }

  constexpr auto end() requires common_range<@_InnerView_@> {
    return @_iterator_@<false>(*this, @_inner\__@.end());
  }

  constexpr auto end() const
    requires range<const @_InnerView_@> &&
             regular_invocable<const F&, @_REPEAT_@(range_reference_t<const V>, N)...>
  {
    return @_sentinel_@<true>(@_inner\__@.end());
  }

  constexpr auto end() const
    requires common_range<const @_InnerView_@> &&
             regular_invocable<const F&, @_REPEAT_@(range_reference_t<const V>, N)...>
  {
    return @_iterator_@<true>(*this, @_inner\__@.end());
  }

  constexpr auto size() requires sized_range<@_InnerView_@> {
    return @_inner\__@.size();
  }

  constexpr auto size() const requires sized_range<const @_InnerView_@> {
    return @_inner\__@.size();
  }
};

}
```

#### 24.7.?.3 Class template `adjacent_transform_view::@_iterator_@` [range.adjacent.transform.iterator] {-}

```cpp
namespace std::ranges {
  template<forward_range V, copy_constructible F, size_t N>
    requires view<V> && (N > 0) && is_object_v<F> &&
             regular_invocable<F&, @_REPEAT_@(range_reference_t<V>, N)...> &&
             @_can-reference_@<invoke_result_t<F&, @_REPEAT_@(range_reference_t<V>, N)...>>
  template<bool Const>
  class adjacent_transform_view<F, V...>::@_iterator_@ {
    using @_Parent_@ = @_maybe-const_@<Const, adjacent_transform_view>;      // exposition only
    using @_Base_@ = @_maybe-const_@<Const, V>;                 // exposition only
    @_Parent_@* parent = nullptr;                                   // exposition only
    @_inner-iterator_@<Const> @_inner\__@;                                    // exposition only

    constexpr @_iterator_@(@_Parent_@& parent, @_inner-iterator_@<Const> inner); // exposition only

  public:
    using iterator_category = @_see below_@;
    using iterator_concept  = typename @_inner-iterator_@<Const>::iterator_concept;
    using value_type =
      remove_cvref_t<invoke_result_t<@_maybe-const_@<Const, F>&, @_REPEAT_@(range_reference_t<@_Base_@>, N)...>>;
    using difference_type = range_difference_t<@_Base_@>;

    @_iterator_@() = default;
    constexpr @_iterator_@(@_iterator_@<!Const> i)
      requires Const && convertible_to<@_inner-iterator_@<false>, @_inner-iterator_@<Const>>;

    constexpr decltype(auto) operator*() const noexcept(@_see below_@);
    constexpr @_iterator_@& operator++();
    constexpr @_iterator_@ operator++(int);

    constexpr @_iterator_@& operator--() requires bidirectional_range<@_Base_@>;
    constexpr @_iterator_@ operator--(int) requires bidirectional_range<@_Base_@>;

    constexpr @_iterator_@& operator+=(difference_type x) requires random_access_range<@_Base_@>;
    constexpr @_iterator_@& operator-=(difference_type x) requires random_access_range<@_Base_@>;

    constexpr auto operator[](difference_type n) const requires random_access_range<@_Base_@>;

    friend constexpr bool operator==(const @_iterator_@& x, const @_iterator_@& y);

    friend constexpr bool operator<(const @_iterator_@& x, const @_iterator_@& y)
      requires random_access_range<@_Base_@>;
    friend constexpr bool operator>(const @_iterator_@& x, const @_iterator_@& y)
      requires random_access_range<@_Base_@>;
    friend constexpr bool operator<=(const @_iterator_@& x, const @_iterator_@& y)
      requires random_access_range<@_Base_@>;
    friend constexpr bool operator>=(const @_iterator_@& x, const @_iterator_@& y)
      requires random_access_range<@_Base_@>;
    friend constexpr auto operator<=>(const @_iterator_@& x, const @_iterator_@& y)
      requires random_access_range<@_Base_@> && three_­way_­comparable<@_inner-iterator_@<Const>>;

    friend constexpr @_iterator_@ operator+(const @_iterator_@& i, difference_type n)
      requires random_access_range<@_Base_@>;
    friend constexpr @_iterator_@ operator+(difference_type n, const @_iterator_@& i)
      requires random_access_range<@_Base_@>;
    friend constexpr @_iterator_@ operator-(const @_iterator_@& x, difference_type y)
      requires random_access_range<@_Base_@>;
    friend constexpr difference_type operator-(const @_iterator_@& x, const @_iterator_@& y)
      requires sized_sentinel_for<@_inner-iterator_@<Const>, @_inner-iterator_@<Const>>;
  };
}
```

[1]{.pnum} The member _typedef-name_ `@_iterator_@::iterator_category` is defined as follows:

- If `invoke_result_t<@_maybe-const_@<Const, F>&, @_REPEAT_@(range_reference_t<@_Base_@>, N)...>` is not an lvalue reference,
  `iterator_category` denotes `input_iterator_tag`.
- Otherwise, let `C` denote the type `iterator_traits<@_Base_@>::iterator_category`.
  - If `derived_from<C, random_access_iterator_tag>` is `true`, `iterator_category` denotes `random_access_iterator_tag`;
  - Otherwise, if `derived_from<C, bidirectional_iterator_tag>` is `true`, `iterator_category` denotes `bidirectional_iterator_tag`;
  - Otherwise, if `derived_from<C, forward_iterator_tag>` is `true`, `iterator_category` denotes `forward_iterator_tag`;
  - Otherwise, `iterator_category` denotes `input_iterator_tag`.


::: itemdecl

```cpp
constexpr @_iterator_@(@_Parent_@& parent, @_inner-iterator_@<Const> inner);
```

[2]{.pnum} _Effects_: Initializes `@_parent\__@` with `addressof(parent)` and `@_inner\__@` with `std::move(inner)`.

```cpp
constexpr @_iterator_@(@_iterator_@<!Const> i)
  requires Const && convertible_to<@_inner-iterator_@<false>, @_inner-iterator_@<Const>>;
```

[3]{.pnum} _Effects_: Initializes `@_parent\__@` with `i.@_parent\__@` and `@_inner\__@` with `std::move(i.@_inner\__@)`.

```cpp
constexpr decltype(auto) operator*() const noexcept(@_see below_@);
```

[4]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return apply([&](const auto&... iters) -> decltype(auto) {
    return invoke(*@_parent\__@->@_fun\__@, *iters...);
  }, @_inner\__@.@_current\__@);
```
:::

[5]{.pnum} _Remarks:_
The expression within `noexcept` is equivalent to
`is_nothrow_invocable_v<@_maybe-const_@<Const, F>&,  @_REPEAT_@(range_reference_t<@_Base_@>, N)...>`.

```cpp
constexpr @_iterator_@& operator++();
```
[6]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  ++@_inner\__@;
  return *this;
```
:::

```cpp
constexpr @_iterator_@ operator++(int);
```

[7]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto tmp = *this;
  ++*this;
  return tmp;
```
:::


```cpp
constexpr @_iterator_@& operator--() requires bidirectional_range<@_Base_@>;
```
[8]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  --@_inner\__@;
  return *this;
```
:::


```cpp
constexpr @_iterator_@ operator--(int) requires bidirectional_range<@_Base_@>;
```
[9]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  auto tmp = *this;
  --*this;
  return tmp;
```
:::

```cpp
constexpr @_iterator_@& operator+=(difference_type x)
  requires random_­access_­range<@_Base_@>;
```
[10]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  @_inner\__@ += x;
  return *this;
```
:::

```cpp
constexpr @_iterator_@& operator-=(difference_type x)
  requires random_­access_­range<@_Base_@>;
```
[11]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  @_inner\__@ -= x;
  return *this;
```
:::

```cpp
constexpr decltype(auto) operator[](difference_type n) const
  requires random_­access_­range<@_Base_@>;
```
[12]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return apply([&](const auto&... iters) -> decltype(auto) {
    return invoke(*@_parent\__@->@_fun\__@, iters[n]...);
  }, @_inner\__@.@_current\__@);
```
:::

```cpp
friend constexpr bool operator==(const @_iterator_@& x, const @_iterator_@& y);
friend constexpr bool operator<(const @_iterator_@& x, const @_iterator_@& y)
  requires random_­access_­range<@_Base_@>;
friend constexpr bool operator>(const @_iterator_@& x, const @_iterator_@& y)
  requires random_­access_­range<@_Base_@>;
friend constexpr bool operator<=(const @_iterator_@& x, const @_iterator_@& y)
  requires random_­access_­range<@_Base_@>;
friend constexpr bool operator>=(const @_iterator_@& x, const @_iterator_@& y)
  requires random_­access_­range<@_Base_@>;
friend constexpr auto operator<=>(const @_iterator_@& x, const @_iterator_@& y)
  requires random_access_range<@_Base_@> && three_­way_­comparable<@_inner-iterator_@<Const>>;
```
[13]{.pnum} Let _`op`_ be the operator.

[14]{.pnum} _Effects_: Equivalent to: `return x.@_inner\__@ @_op_@ y.@_inner\__@; `


```cpp
friend constexpr @_iterator_@ operator+(const @_iterator_@& i, difference_type n)
  requires random_­access_­range<@_Base_@>;
friend constexpr @_iterator_@ operator+(difference_type n, const @_iterator_@& i)
  requires random_­access_­range<@_Base_@>;
```

[15]{.pnum} _Effects_: Equivalent to: `return @_iterator_@(*i.@_parent\__@, i.@_inner\__@ + n);`

```cpp
friend constexpr @_iterator_@ operator-(const @_iterator_@& x, difference_type y)
  requires random_­access_­range<@_Base_@>;
```

[16]{.pnum} _Effects_: Equivalent to: `return @_iterator_@(*x.@_parent\__@, x.@_inner\__@ - y);`

```cpp
friend constexpr difference_type operator-(const @_iterator_@& x, const @_iterator_@& y)
  requires sized_sentinel_for<@_inner-iterator_@<Const>, @_inner-iterator_@<Const>>;
```

[17]{.pnum} _Effects_: Equivalent to: `return x.@_inner\__@ - y.@_inner\__@;`

:::

#### 24.7.?.4 Class template `adjacent_transform_view::@_sentinel_@` [range.adjacent.transform.sentinel] {-}

```cpp
namespace std::ranges {
  template<forward_range V, copy_constructible F, size_t N>
    requires view<V> && (N > 0) && is_object_v<F> &&
             regular_invocable<F&, @_REPEAT_@(range_reference_t<V>, N)...> &&
             @_can-reference_@<invoke_result_t<F&, @_REPEAT_@(range_reference_t<V>, N)...>>
  template<bool Const>
  class adjacent_transform_view<V, F, N>::@_sentinel_@ {
    @_inner-sentinel_@<Const> @_inner\__@;                             // exposition only
    constexpr explicit @_sentinel_@(@_inner-sentinel_@<Const> inner);  // exposition only
  public:
    @_sentinel_@() = default;
    constexpr @_sentinel_@(@_sentinel_@<!Const> i)
      requires Const && convertible_to<@_inner-sentinel_@<false>, @_inner-sentinel_@<Const>>;

    template<bool OtherConst>
      requires sentinel_­for<@_inner-sentinel_@<Const>, @_inner-iterator_@<OtherConst>>
    friend constexpr bool operator==(const @_iterator_@<OtherConst>& x, const @_sentinel_@& y);

    template<bool OtherConst>
      requires sized_­sentinel_­for<@_inner-sentinel_@<Const>, @_inner-iterator_@<OtherConst>>
    friend constexpr range_difference_t<@_maybe-const_@<OtherConst, @_InnerView_@>>
      operator-(const @_iterator_@<OtherConst>& x, const @_sentinel_@& y);

    template<bool OtherConst>
      requires sized_­sentinel_­for<@_inner-sentinel_@<Const>, @_inner-iterator_@<OtherConst>>
    friend constexpr range_difference_t<@_maybe-const_@<OtherConst, @_InnerView_@>>
      operator-(const @_sentinel_@& x, const @_iterator_@<OtherConst>& y);
  };
}
```
::: itemdecl

```cpp
constexpr explicit @_sentinel_@(@_inner-sentinel_@<Const> inner);
```

[1]{.pnum} _Effects_: Initializes `@_inner\__@` with `inner`.

```cpp
constexpr @_sentinel_@(@_sentinel_@<!Const> i)
  requires Const && convertible_to<@_inner-sentinel_@<false>, @_inner-sentinel_@<Const>>;
```

[2]{.pnum} _Effects_: Initializes `@_inner\__@` with `std::move(i.@_inner\__@)`.

```cpp
template<bool OtherConst>
  requires sentinel_­for<@_inner-sentinel_@<Const>, @_inner-iterator_@<OtherConst>>
friend constexpr bool operator==(const @_iterator_@<OtherConst>& x, const @_sentinel_@& y);
```

[3]{.pnum} _Effects_: Equivalent to `return x.@_inner\__@ == y.@_inner\__@;`


```cpp
template<bool OtherConst>
  requires sized_­sentinel_­for<@_inner-sentinel_@<Const>, @_inner-iterator_@<OtherConst>>
friend constexpr range_difference_t<@_maybe-const_@<OtherConst, @_InnerView_@>>
  operator-(const @_iterator_@<OtherConst>& x, const @_sentinel_@& y);

template<bool OtherConst>
  requires sized_­sentinel_­for<@_inner-sentinel_@<Const>, @_inner-iterator_@<OtherConst>>
friend constexpr range_difference_t<@_maybe-const_@<OtherConst, @_InnerView_@>>
  operator-(const @_sentinel_@& x, const @_iterator_@<OtherConst>& y);
```
[4]{.pnum} _Effects_: Equivalent to `return x.@_inner\__@ - y.@_inner\__@;`

:::
