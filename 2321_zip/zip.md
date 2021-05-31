---
title: "`zip`"
document: D2321R2
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: true
---

# Abstract
This paper proposes

- four views, `zip`, `zip_transform`, `adjacent`, and `adjacent_transform`,
- changes to `tuple` and `pair` necessary to make them usable as proxy references (necessary for `zip` and `adjacent`), and
- changes to `vector<bool>::reference` to make it usable as a proxy reference for writing,

all as described in section 3.2 of [@P2214R0].

# Revision history

- R2: Typo fixes. Incorporated LWG review feedback on 2021-05-21 and 2021-05-28.
  Account for integer-class types in the handling of `difference_type` and `size_type`.
- R1: Added feature test macro. Expanded discussion regarding 1) `operator==` for
  forward-or-weaker `zip` iterators and 2) `adjacent` on input ranges.
  Miscellaneous wording fixes (thanks to Barry Revzin and Tomasz Kamiński).
  Added a short example.

# Examples

```cpp
std::vector v1 = {1, 2};
std::vector v2 = {'a', 'b', 'c'};
std::vector v3 = {3, 4, 5};

fmt::print("{}\n", std::views::zip(v1, v2));                               // {(1, 'a'), (2, 'b')}
fmt::print("{}\n", std::views::zip_transform(std::multiplies(), v1, v3));  // {3, 8}
fmt::print("{}\n", v2 | std::views::pairwise);                             // {('a', 'b'), ('b', 'c')}
fmt::print("{}\n", v3 | std::views::pairwise_transform(std::plus()));      // {7, 9}
```

# Discussion

The proposed wording below generally follows the design described in section 3.2 of [@P2214R0], and the discussion
in this paper assumes familiarity with that paper. This section focuses on deviations from and additions to that
paper, as well as certain details in the design of the views that should be called out.

## Proxy reference changes

The basic rationale for changes to `tuple` and `pair` are described in exhaustive detail in [@P2214R0]
sections 3.2.1 and 3.2.2 and will not be repeated here. Several additions are worth noting:

- `common_type` and `basic_common_reference` specializations are added for `tuple` and `pair`. These are also required
  for `tuple` and `pair` to be usable as proxy references.
- `swap` for `const tuple` and `const pair`. Once tuples of references are made const-assignable, the default `std::swap`
  can be called for const tuples of references. However, that triple-move `swap` does the wrong thing:
  ```cpp
    int i = 1, j = 2;
    const auto t1 = std::tie(i), t2 = std::tie(j);

    // If std::swap(t1, t2); called the default triple-move std::swap then
    // this would do
    auto tmp = std::move(t1);
    t1 = std::move(t2);
    t2 = std::move(tmp);

    // i == 2, j == 2
  ```
  This paper therefore proposes adding overloads of `swap` for `const` tuples and pairs to correctly perform
  element-wise swap.
- Consistent with the scoped allocator protocol, allocator-extended constructors that correspond
  to the new `tuple` constructors have been added to `tuple`, and new overloads of
  `uses_allocator_construction_args` corresponding to the new `pair` constructors have been added as well.

## `zip` and `zip_transform`

### No common exposition-only base view

[@P2214R0] proposes implementing `zip` and `zip_transform` to produce specializations of an
exposition-only _`iter-zip-transform-view`_, which is roughly how they are implemented
in range-v3. In the process of writing wording for these views, however, it has become apparent
that the two views have enough differences that a common underlying view would need
to have additional knobs to control the behavior (beyond the `value_type` issue
already noted in the paper). The extra complexity required would likely negate
any potential benefit from having a single underlying view.

Instead, the wording below specifies `zip_transform` largely in terms of `zip`.
This significantly reduces specification duplication without sacrificing efficiency.

### `tuple` or `pair`?

In range-v3, zipping two views produced a range of `pair`s, while zipping any
other number of ranges produce a range of `tuple`s. This paper maintains that
design for several reasons:

- Since `pair` is tuple-like, most common uses of the result (`get`, `apply`,
  structured bindings, etc.) would work just as well.
- Certain parts of the standard library, notably `map` and friends, are dependent on `pair`.
- `pair` implicitly converts to `tuple` if one is really needed, whereas
  constructing a `pair` from a `tuple` is more difficult.

### Zipping nothing?

As in range-v3, zipping nothing produces an `empty_view` of the appropriate type.

### When is `zip_view` a `common_range`?

A `common_range` is a range whose iterator and sentinel types are the same.

Obviously, when zipping a single range, the `zip_view` can be a `common_range`
if the underlying range is.

When the `zip_view` is not bidirectional, it can be a `common_range` when every
underlying view is a `common_range`. To handle differently-sized ranges,
iterator `==` is a logical OR: two iterators compare equal if one of the
sub-iterators compare equal. Note that the domain of `==` only extends to
iterators over the same underlying sequence; the use of logical OR is valid
within that domain because the only valid operands to `==` are
iterators obtained from incrementing `begin()` zero or more times and
the iterator returned by `end()`.

When the `zip_view` is bidirectional (or stronger), however, it is now possible
to iterate backwards from the end iterator (if it is indeed an iterator). As a
result, we cannot simply construct the end iterator out of the end iterators of
the views: if the views are different in size, iterating backwards from the end
will give us elements that are not in the view at all (see [@range-v3.1592]).
Instead, we need to produce a "proper" end iterator by advancing from `begin`;
to be able compute `end` in constant time, we need all views to be random access
and sized.

As `end` is only required to be amortized constant time, it is in theory possible
to do a linear time traversal and cache the result. The additional benefit from
such a design appears remote, and it has significant costs.

#### Does that mean `views::enumerate(a_std_list)` isn't a `common_range`?

It's still an open question whether `enumerate` should be implemented in terms
of `zip_view` or not. If it is specified in terms of `zip_view` (and produces
a `pair`), as proposed in [@P2214R0], it is easy to specify an separate
`enumerate_view` that is implemented with `zip_view` but still produces a common
range for this case.

#### What about infinite ranges in general?

If `zip_view` can recognize when a range is infinite, then it is theoretically
possible for it to be a `common_range` in the following two cases:

- Every range but one is an infinite random-access range, while the one finite
  range is a sized and common range (of any iterator strength).
  This is the general case of `enumerate` above.
- Every range is either random-access and sized, or random-access and infinite,
  and at least one range is sized.

The standard, however, generally does not recognize infinite ranges (despite
providing `unreachable_sentinel`). It goes without saying that a complete design
for infinite ranges support is outside the scope of this paper.

### `difference_type`

The `difference_type` of `zip_view` is the common type of the difference types
of its constituent views. During LWG wording review, Casey Carter pointed out
that we don't currently require integer-class types to have such a common type,
or to be convertible to other integer-class types, which appears to be a defect
in the specification of those types. This paper therefore adds wording to
address the issue.

## `adjacent` and `adjacent_transform`

As `adjacent` is a specialized version of `zip`, most of the discussion in
above applies, _mutatis mutandis_, to `adjacent` as well, and will not be repeated here.

### Naming
The wording below tentatively uses `adjacent` for the general functionality,
and `pairwise` for the `N == 2` case. [@P2214R0] section 3.2.5 suggests
an alternative (`slide_as_tuple` for the general functionality and `adjacent`
for the `N == 2` case). The author has a mild preference for the current
names due to the somewhat unwieldiness of the name `slide_as_tuple`.

### Value type
The value type of `adjacent_view` is a homogeneous `tuple` or `pair`. Since `array`
cannot hold references and is defined to be an aggregate, using it as the value
type poses significant usability issues (even if we somehow get the
`common_reference_with` requirements in `indirectly_readable` to work with even more
`tuple`/`pair` changes).

### `common_range`
One notable difference from `zip` is that since `adjacent` comes from a single underlying view,
it can be a `common_range` whenever its underlying view is.

### No input ranges
Because `adjacent` by definition holds multiple iterators to the same view,
it requires forward ranges. It is true that the `N == 1` case could theoretically
support input ranges, but that adds extra complexity and seems entirely pointless.
Besides, someone desperate to wrap their input range in a single element `tuple`
can just use `zip` instead.

During LEWG review of R0 of this paper it was suggested that `adjacent<N>` could
support input views by caching the elements referred to by the last `N` iterators.
Such a view would have significant differences from what is being proposed in
this paper. For instance, because the reference obtained from an input iterator
is invalidated on increment, the range will have to cache by value type, and so
the reference type will have to be something like `tuple<range_value_t<V>&...>`
(or perhaps even `tuple<range_value_t<V>...>&`?) instead of
`tuple<range_reference_t<V>...>`. To be able to construct and update
the cached values, the view would have to require underlying range's value type
to be constructible and assignable from its reference type. And because we don't
know what elements the user may desire to access, iterating through the view
necessarily requires copying every element of the underlying view into the cache,
which can be wasteful if not all elements need to be accessed. By comparison,
iterating through the proposed `adjacent` copies exactly zero of the underlying
range's elements.

Additionally, because input views provide much fewer operations and guarantees,
they can often be implemented more efficiently than forward views. There has
been an open range-v3 issue [@range-v3.704] since 2017 (see also
[this comment](https://old.reddit.com/r/cpp/comments/8ytrnb/what_i_dont_like_about_ranges/e82rk5a/)
from Eric Niebler on /r/cpp) to provide an API that downgrades a
forward-or-stronger range to input for efficiency when the forward
range's guarantees are not needed. Having a view adaptor that is significantly more
expensive when given an input range would significantly damage the usability
and teachability of such a design.

The author believes that the behavioral and performance characteristics of such
a view is different enough from the `adjacent` proposed in this paper
that it would be inappropriate to put them under the same name. It can be
proposed separately if desired.

### `iter_swap`

Since the iterators of `adjacent_view` refer to potentially overlapping elements
of the underlying view, `iter_swap` cannot really "exchange the values" of the
range elements when the iterators overlap. However, it does not appear to be possible
to disable `ranges::iter_swap` (deleting or not providing `iter_swap` will simply
fallback to the default implementation), and swapping non-overlapping iterators
is still useful functionality. Thus, the wording below retains `iter_swap` but gives
it a precondition that there is no overlap.

# Wording

This wording is relative to [@N4878].

## `tuple`

::: wordinglist

- Edit [tuple.syn]{.sref}, header `<tuple>` synopsis, as indicated:

```diff

 #include <compare>              // see [compare.syn]

 namespace std {
   // [tuple.tuple], class template tuple
   template<class... Types>
     class tuple;

+  template<class... TTypes, class... UTypes, template<class> class TQual, template<class> class UQual>
+    requires requires { typename tuple<common_reference_t<TQual<TTypes>, UQual<UTypes>>...>; }
+  struct basic_common_reference<tuple<TTypes...>, tuple<UTypes...>, TQual, UQual> {
+    using type = tuple<common_reference_t<TQual<TTypes>, UQual<UTypes>>...>;
+  };
+
+  template<class... TTypes, class... UTypes>
+    requires requires { typename tuple<common_type_t<TTypes, UTypes>...>; }
+  struct common_type<tuple<TTypes...>, tuple<UTypes...>> {
+    using type = tuple<common_type_t<TTypes, UTypes>...>;
+  };


   // [...]

   // [tuple.special], specialized algorithms
   template<class... Types>
     constexpr void swap(tuple<Types...>& x, tuple<Types...>& y) noexcept($see below$);
+  template<class... Types>
+    constexpr void swap(const tuple<Types...>& x, const tuple<Types...>& y) noexcept($see below$);
 }

```

- Edit [tuple.tuple]{.sref}, class template `tuple` synopsis, as indicated:

```diff
 namespace std {
   template<class... Types>
   class tuple {
   public:
     // [tuple.cnstr], tuple construction
     constexpr explicit($see below$) tuple();
     constexpr explicit($see below$) tuple(const Types&...);         // only if sizeof...(Types) >= 1
     template<class... UTypes>
       constexpr explicit($see below$) tuple(UTypes&&...);           // only if sizeof...(Types) >= 1

     tuple(const tuple&) = default;
     tuple(tuple&&) = default;

+    template<class... UTypes>
+      constexpr explicit($see below$) tuple(tuple<UTypes...>&);
     template<class... UTypes>
       constexpr explicit($see below$) tuple(const tuple<UTypes...>&);
     template<class... UTypes>
       constexpr explicit($see below$) tuple(tuple<UTypes...>&&);
+    template<class... UTypes>
+      constexpr explicit($see below$) tuple(const tuple<UTypes...>&&);

+    template<class U1, class U2>
+      constexpr explicit($see below$) tuple(pair<U1, U2>&);         // only if sizeof...(Types) == 2
     template<class U1, class U2>
       constexpr explicit($see below$) tuple(const pair<U1, U2>&);   // only if sizeof...(Types) == 2
     template<class U1, class U2>
       constexpr explicit($see below$) tuple(pair<U1, U2>&&);        // only if sizeof...(Types) == 2
+    template<class U1, class U2>
+      constexpr explicit($see below$) tuple(const pair<U1, U2>&&);  // only if sizeof...(Types) == 2

     // allocator-extended constructors
     template<class Alloc>
       constexpr explicit($see below$)
         tuple(allocator_arg_t, const Alloc& a);
     template<class Alloc>
       constexpr explicit($see below$)
         tuple(allocator_arg_t, const Alloc& a, const Types&...);
     template<class Alloc, class... UTypes>
       constexpr explicit($see below$)
         tuple(allocator_arg_t, const Alloc& a, UTypes&&...);
     template<class Alloc>
       constexpr tuple(allocator_arg_t, const Alloc& a, const tuple&);
     template<class Alloc>
       constexpr tuple(allocator_arg_t, const Alloc& a, tuple&&);
+    template<class Alloc, class... UTypes>
+      constexpr explicit($see below$)
+        tuple(allocator_arg_t, const Alloc& a, tuple<UTypes...>&);
     template<class Alloc, class... UTypes>
       constexpr explicit($see below$)
         tuple(allocator_arg_t, const Alloc& a, const tuple<UTypes...>&);
     template<class Alloc, class... UTypes>
       constexpr explicit($see below$)
         tuple(allocator_arg_t, const Alloc& a, tuple<UTypes...>&&);
+    template<class Alloc, class... UTypes>
+      constexpr explicit($see below$)
+        tuple(allocator_arg_t, const Alloc& a, const tuple<UTypes...>&&);
+    template<class Alloc, class U1, class U2>
+      constexpr explicit($see below$)
+        tuple(allocator_arg_t, const Alloc& a, pair<U1, U2>&);
     template<class Alloc, class U1, class U2>
       constexpr explicit($see below$)
         tuple(allocator_arg_t, const Alloc& a, const pair<U1, U2>&);
     template<class Alloc, class U1, class U2>
       constexpr explicit($see below$)
         tuple(allocator_arg_t, const Alloc& a, pair<U1, U2>&&);
+    template<class Alloc, class U1, class U2>
+      constexpr explicit($see below$)
+        tuple(allocator_arg_t, const Alloc& a, const pair<U1, U2>&&);

     // [tuple.assign], tuple assignment
     constexpr tuple& operator=(const tuple&);
+    constexpr const tuple& operator=(const tuple&) const;
     constexpr tuple& operator=(tuple&&) noexcept($see below$);
+    constexpr const tuple& operator=(tuple&&) const;

     template<class... UTypes>
       constexpr tuple& operator=(const tuple<UTypes...>&);
+    template<class... UTypes>
+      constexpr const tuple& operator=(const tuple<UTypes...>&) const;
     template<class... UTypes>
       constexpr tuple& operator=(tuple<UTypes...>&&);
+    template<class... UTypes>
+      constexpr const tuple& operator=(tuple<UTypes...>&&) const;

     template<class U1, class U2>
       constexpr tuple& operator=(const pair<U1, U2>&);          // only if sizeof...(Types) == 2
+    template<class U1, class U2>
+      constexpr const tuple& operator=(const pair<U1, U2>&) const;    // only if sizeof...(Types) == 2
     template<class U1, class U2>
       constexpr tuple& operator=(pair<U1, U2>&&);               // only if sizeof...(Types) == 2
+    template<class U1, class U2>
+      constexpr const tuple& operator=(pair<U1, U2>&&) const;         // only if sizeof...(Types) == 2

     // [tuple.swap], tuple swap
     constexpr void swap(tuple&) noexcept($see below$);
+    constexpr void swap(const tuple&) const noexcept($see below$);
   };

   // [...]
 }
```

- Edit [tuple.cnstr]{.sref} as indicated:

::: add

::: itemdecl

```c++
template<class... UTypes> constexpr explicit($see below$) tuple(tuple<UTypes...>& u);
template<class... UTypes> constexpr explicit($see below$) tuple(const tuple<UTypes...>& u);
template<class... UTypes> constexpr explicit($see below$) tuple(tuple<UTypes...>&& u);
template<class... UTypes> constexpr explicit($see below$) tuple(const tuple<UTypes...>&& u);
```

[?]{.pnum} Let `I` be the pack `0, 1, ..., (sizeof...(Types) - 1)`. Let `FWD(u)` be `static_cast<decltype(u)>(u)`.

[?]{.pnum} _Constraints_:

- [?.#]{.pnum} `sizeof...(Types)` equals `sizeof...(UTypes)`, and
- [?.#]{.pnum} `(is_constructible_v<Types, decltype(get<I>(FWD(u)))> && ...)` is `true`, and
- [?.#]{.pnum} either `sizeof...(Types)` is not `1`, or (when `Types...` expands to `T` and
  `UTypes...` expands to `U`) `is_convertible_v<decltype(u), T>`,
   `is_constructible_v<T, decltype(u)>`, and `is_same_v<T, U>` are all `false`.

[?]{.pnum} _Effects:_ For all _i_, initializes the _i_<sup>th</sup> element of `*this` with `get<$i$>(FWD(u))`.

[?]{.pnum} _Remarks:_ The expression inside `explicit` is equivalent to:
`!(is_convertible_v<decltype(get<I>(FWD(u))), Types> && ...)`

```c++
template<class... UTypes> constexpr explicit($see below$) tuple(pair<U1, U2>& u);
template<class... UTypes> constexpr explicit($see below$) tuple(const pair<U1, U2>& u);
template<class... UTypes> constexpr explicit($see below$) tuple(pair<U1, U2>&& u);
template<class... UTypes> constexpr explicit($see below$) tuple(const pair<U1, U2>&& u);
```

[?]{.pnum} Let `FWD(u)` be `static_cast<decltype(u)>(u)`.

[?]{.pnum} _Constraints_:

- [?.#]{.pnum} `sizeof...(Types)` is 2 and
- [?.#]{.pnum} `is_constructible_v<T@<sub>0</sub>@, decltype(get<0>(FWD(u)))>` is `true` and
- [?.#]{.pnum} `is_constructible_v<T@<sub>1</sub>@, decltype(get<1>(FWD(u)))>` is `true`.

[?]{.pnum} _Effects:_ Initializes the first element with `get<0>(FWD(u))` and the second element with `get<1>(FWD(u))`.

[?]{.pnum} _Remarks:_ The expression inside `explicit` is equivalent to:
`!is_convertible_v<decltype(get<0>(FWD(u))), T@<sub>0</sub>@> || !is_convertible_v<decltype(get<1>(FWD(u))), T@<sub>1</sub>@>`

:::

:::

::: rm

::: itemdecl

```c++
template<class... UTypes> constexpr explicit($see below$) tuple(const tuple<UTypes...>& u);
```

[18]{.pnum} _Constraints:_

- [18.1]{.pnum} `sizeof...(Types)` equals `sizeof...(UTypes`) and
- [18.2]{.pnum}`is_constructible_v<T@_<sub>i</sub>_@, const U@_<sub>i</sub>_@&>` is `true` for all _i_, and
- [18.3]{.pnum} either `sizeof...(Types)` is not 1, or (when `Types...` expands to `T` and `UTypes...` expands to `U`)
  `is_convertible_v<const tuple<U>&, T>`, `is_constructible_v<T, const tuple<U>&>`, and `is_same_v<T, U>` are all `false`.

[19]{.pnum} _Effects:_ Initializes each element of `*this` with the corresponding element of `u`.

[20]{.pnum} _Remarks:_ The expression inside `explicit` is equivalent to:
`!conjunction_v<is_convertible<const UTypes&, Types>...>`

```c++
template<class... UTypes> constexpr explicit($see below$) tuple(tuple<UTypes...>&& u);
```
[21]{.pnum} _Constraints:_

- [21.1]{.pnum} `sizeof...(Types)` equals `sizeof...(UTypes`), and
- [21.2]{.pnum}`is_constructible_v<T@_<sub>i</sub>_@, U@_<sub>i</sub>_@>` is `true` for all _i_, and
- [21.3]{.pnum} either `sizeof...(Types)` is not 1, or (when `Types...` expands to `T` and `UTypes...` expands to `U`)
  `is_convertible_v<tuple<U>, T>`, `is_constructible_v<T, tuple<U>>`, and `is_same_v<T, U>` are all `false`.

[22]{.pnum} _Effects:_ For all _i_, initializes the _i_<sup>th</sup> element of `*this` with `std::forward<U@_<sub>i</sub>_@>(get<$i$>(u))`.

[23]{.pnum} _Remarks:_ The expression inside `explicit` is equivalent to:
`!conjunction_v<is_convertible<UTypes, Types>...>`

```c++
template<class U1, class U2> constexpr explicit($see below$) tuple(const pair<U1, U2>& u);
```

[24]{.pnum} _Constraints:_

- [24.1]{.pnum} `sizeof...(Types)` is 2,
- [24.2]{.pnum} `is_constructible_v<T@<sub>0</sub>@, const U1&>` is `true`, and
- [24.3]{.pnum} `is_constructible_v<T@<sub>1</sub>@, const U2&>` is `true`

[25]{.pnum} _Effects:_ Initializes the first element with `u.first` and the second element with `u.second`.

[26]{.pnum} _Remarks:_ The expression inside `explicit` is equivalent to:
`!is_convertible_v<const U1&, T@<sub>0</sub>@> || !is_convertible_v<const U2&, T@<sub>1</sub>@>`

```c++
template<class U1, class U2> constexpr explicit($see below$) tuple(pair<U1, U2>&& u);
```

[27]{.pnum} _Constraints:_

- [27.1]{.pnum} `sizeof...(Types)` is 2,
- [27.2]{.pnum} `is_constructible_v<T@<sub>0</sub>@, U1>` is `true`, and
- [27.3]{.pnum} `is_constructible_v<T@<sub>1</sub>@, U2>` is `true`

[28]{.pnum} _Effects:_ Initializes the first element with `std::forward<U1>(u.first)` and the second element with `std::forward<U2>(u.second)`.

[29]{.pnum} _Remarks:_ The expression inside `explicit` is equivalent to:
`!is_convertible_v<U1, T@<sub>0</sub>@> || !is_convertible_v<U2, T@<sub>1</sub>@>`

:::

:::

::: itemdecl

```diff
  template<class Alloc>
    constexpr explicit($see below$)
      tuple(allocator_arg_t, const Alloc& a);
  template<class Alloc>
    constexpr explicit($see below$)
      tuple(allocator_arg_t, const Alloc& a, const Types&...);
  template<class Alloc, class... UTypes>
    constexpr explicit($see below$)
      tuple(allocator_arg_t, const Alloc& a, UTypes&&...);
  template<class Alloc>
    constexpr tuple(allocator_arg_t, const Alloc& a, const tuple&);
  template<class Alloc>
    constexpr tuple(allocator_arg_t, const Alloc& a, tuple&&);
+ template<class Alloc, class... UTypes>
+   constexpr explicit($see below$)
+     tuple(allocator_arg_t, const Alloc& a, tuple<UTypes...>&);
  template<class Alloc, class... UTypes>
    constexpr explicit($see below$)
      tuple(allocator_arg_t, const Alloc& a, const tuple<UTypes...>&);
  template<class Alloc, class... UTypes>
    constexpr explicit($see below$)
      tuple(allocator_arg_t, const Alloc& a, tuple<UTypes...>&&);
+ template<class Alloc, class... UTypes>
+   constexpr explicit($see below$)
+     tuple(allocator_arg_t, const Alloc& a, const tuple<UTypes...>&&);
+ template<class Alloc, class U1, class U2>
+   constexpr explicit($see below$)
+     tuple(allocator_arg_t, const Alloc& a, pair<U1, U2>&);
  template<class Alloc, class U1, class U2>
    constexpr explicit($see below$)
      tuple(allocator_arg_t, const Alloc& a, const pair<U1, U2>&);
  template<class Alloc, class U1, class U2>
    constexpr explicit($see below$)
      tuple(allocator_arg_t, const Alloc& a, pair<U1, U2>&&);
+ template<class Alloc, class U1, class U2>
+   constexpr explicit($see below$)
+     tuple(allocator_arg_t, const Alloc& a, const pair<U1, U2>&&);
```

[31]{.pnum} _Preconditions:_ `Alloc` meets the _Cpp17Allocator_ requirements (Table 38).

[32]{.pnum} _Effects_: Equivalent to the preceding constructors except that each element is constructed with uses-allocator construction.
:::

- Add the following to [tuple.assign]{.sref}:

::: add
::: itemdecl

```cpp
constexpr const tuple& operator=(const tuple& u) const;
```

[?]{.pnum} _Constraints_: `(is_copy_assignable_v<const Types> && ...)` is `true`.

[?]{.pnum} _Effects_: Assigns each element of `u` to the corresponding element of `*this`.

[?]{.pnum} _Returns_: `*this`.


```cpp
constexpr const tuple& operator=(tuple&& u) const;
```

[?]{.pnum} _Constraints_: `(is_assignable_v<const Types&, Types> && ...)` is `true`.

[?]{.pnum} _Effects_: For all _i_, assigns `std::forward<T@_<sub>i</sub>_@>(get<$i$>(u))` to `get<$i$>(*this)`.

[?]{.pnum} _Returns_: `*this`.


```cpp
template<class... UTypes> constexpr const tuple& operator=(const tuple<UTypes...>& u) const;
```

[?]{.pnum} Constraints:

- [?.#]{.pnum} `sizeof...(Types)` equals ` sizeof...(UTypes)` and
- [?.#]{.pnum} `(is_assignable_v<const Types&, const UTypes&> && ...)` is `true`.

[?]{.pnum} _Effects_: Assigns each element of `u` to the corresponding element of `*this`.

[?]{.pnum} _Returns_: `*this`.

```cpp
template<class... UTypes> constexpr const tuple& operator=(tuple<UTypes...>&& u) const;
```

[?]{.pnum} Constraints:

- [?.#]{.pnum} `sizeof...(Types)` equals ` sizeof...(UTypes)` and
- [?.#]{.pnum} `(is_assignable_v<const Types&, UTypes> && ...)` is `true`.

[?]{.pnum} _Effects_: For all _i_, assigns `std::forward<U@_<sub>i</sub>_@>(get<$i$>(u))` to `get<$i$>(*this)`.

[?]{.pnum} _Returns_: `*this`.

```c++
template<class U1, class U2> constexpr const tuple& operator=(const pair<U1, U2>& u) const;
```

[?]{.pnum} _Constraints:_

- [?.#]{.pnum} `sizeof...(Types)` is 2,
- [?.#]{.pnum} `is_assignable_v<const T@<sub>0</sub>@&, const U1&>` is `true`, and
- [?.#]{.pnum} `is_assignable_v<const T@<sub>1</sub>@&, const U2&>` is `true`

[?]{.pnum} _Effects:_ Assigns `u.first` to the first element and `u.second` to the second element.

[?]{.pnum} _Returns_: `*this`.

```c++
template<class U1, class U2> constexpr const tuple& operator=(pair<U1, U2>&& u) const;
```

[?]{.pnum} _Constraints:_

- [?.#]{.pnum} `sizeof...(Types)` is 2,
- [?.#]{.pnum} `is_assignable_v<const T@<sub>0</sub>@&, U1>` is `true`, and
- [?.#]{.pnum} `is_assignable_v<const T@<sub>1</sub>@&, U2>` is `true`

[?]{.pnum} _Effects:_ Assigns `std::forward<U1>(u.first)` to the first element and `std::forward<U2>(u.second)` to the second element.

[?]{.pnum} _Returns_: `*this`.

:::

:::

- Edit [tuple.swap]{.sref} as indicated:

::: itemdecl
```diff
  constexpr void swap(tuple& rhs) noexcept($see below$);
+ constexpr void swap(const tuple& rhs) const noexcept($see below$);
```

[?]{.pnum} [_Mandates:_]{.diffins}

- [?.#]{.pnum} [For the first overload, `(is_swappable_v<Types> && ...)` is `true`.]{.diffins}
- [?.#]{.pnum} [For the second overload, `(is_swappable_v<const Types> && ...)` is `true`.]{.diffins}

[1]{.pnum} _Preconditions_: Each element in `*this` is swappable with ([swappable.requirements]{.sref}) the corresponding element in `rhs`.

[2]{.pnum} _Effects_: Calls `swap` for each element in `*this` and its corresponding element in `rhs`.

[3]{.pnum} _Throws_: Nothing unless one of the element-wise `swap` calls throws an exception.

[4]{.pnum} _Remarks_: The expression inside `noexcept` is equivalent to
[the logical AND of the following expressions: `is_nothrow_swappable_v<T@_<sub>i</sub>_@>`, where `T@_<sub>i</sub>_@` is the _i_<sup>th</sup> type in `Types`.]{.diffdel}

- [#.#]{.pnum} [`(is_nothrow_swappable_v<Types> && ...)` for the first overload.]{.diffins}
- [#.#]{.pnum} [`(is_nothrow_swappable_v<const Types> && ...)` for the second overload.]{.diffins}

:::

- Edit [tuple.special]{.sref} as indicated:

::: itemdecl

```diff
  template<class... Types>
    constexpr void swap(tuple<Types...>& x, tuple<Types...>& y) noexcept($see below$);
+ template<class... Types>
+   constexpr void swap(const tuple<Types...>& x, const tuple<Types...>& y) noexcept($see below$);
```

[1]{.pnum} _Constraints_: [`is_swappable_v<T>` is true for every type `T` in `Types`.]{.diffdel}

- [#.#]{.pnum} [For the first overload, `(is_swappable_v<Types> && ...)` is `true`.]{.diffins}
- [#.#]{.pnum} [For the second overload, `(is_swappable_v<const Types> && ...)` is `true`.]{.diffins}

[2]{.pnum} _Effects_: As if by `x.swap(y)`.

[3]{.pnum} _Remarks_: The expression inside `noexcept` is equivalent to: `noexcept(x.swap(y))`.

:::

:::

## `pair`

::: wordinglist

- Edit [utility.syn]{.sref}, header `<utility>` synopsis, as indicated:

```diff

 #include <compare>              // see [compare.syn]
 #include <initializer_list>     // see [initializer.list.syn]

 namespace std {
   // [...]

   // [pairs], class template pair
   template<class T1, class T2>
     struct pair;

+  template<class T1, class T2, class U1, class U2, template<class> class TQual, template<class> class UQual>
+    requires requires { typename pair<common_reference_t<TQual<T1>, UQual<U1>>,
+                                      common_reference_t<TQual<T2>, UQual<U2>>>; }
+  struct basic_common_reference<pair<T1, T2>, pair<U1, U2>, TQual, UQual> {
+    using type = pair<common_reference_t<TQual<T1>, UQual<U1>>,
+                      common_reference_t<TQual<T2>, UQual<U2>>>;
+  };
+
+  template<class T1, class T2, class U1, class U2>
+    requires requires { typename pair<common_type_t<T1, U1>, common_type_t<T2, U2>>; }
+  struct common_type<pair<T1, T2>, pair<U1, U2>> {
+    using type = pair<common_type_t<T1, U1>, common_type_t<T2, U2>>;
+  };

   // [pairs.spec], pair specialized algorithms
   template<class T1, class T2>
     constexpr bool operator==(const pair<T1, T2>&, const pair<T1, T2>&);
   template<class T1, class T2>
     constexpr common_comparison_category_t<$synth-three-way-result$<T1>,
                                            $synth-three-way-result$<T2>>
       operator<=>(const pair<T1, T2>&, const pair<T1, T2>&);

   template<class T1, class T2>
     constexpr void swap(pair<T1, T2>& x, pair<T1, T2>& y) noexcept(noexcept(x.swap(y)));
+  template<class T1, class T2>
+    constexpr void swap(const pair<T1, T2>& x, const pair<T1, T2>& y) noexcept(noexcept(x.swap(y)));
 }

```

- Edit [pairs.pair]{.sref} as indicated:

```diff
 namespace std {
   template<class T1, class T2>
   struct pair {
     using first_type  = T1;
     using second_type = T2;

     T1 first;
     T2 second;

     pair(const pair&) = default;
     pair(pair&&) = default;
     constexpr explicit($see below$) pair();
     constexpr explicit($see below$) pair(const T1& x, const T2& y);
     template<class U1, class U2>
       constexpr explicit($see below$) pair(U1&& x, U2&& y);
+    template<class U1, class U2>
+      constexpr explicit($see below$) pair(pair<U1, U2>& p);
     template<class U1, class U2>
       constexpr explicit($see below$) pair(const pair<U1, U2>& p);
     template<class U1, class U2>
       constexpr explicit($see below$) pair(pair<U1, U2>&& p);
+    template<class U1, class U2>
+      constexpr explicit($see below$) pair(const pair<U1, U2>&& p);
     template<class... Args1, class... Args2>
       constexpr pair(piecewise_construct_t,
                      tuple<Args1...> first_args, tuple<Args2...> second_args);

     constexpr pair& operator=(const pair& p);
+    constexpr const pair& operator=(const pair& p) const;
     template<class U1, class U2>
       constexpr pair& operator=(const pair<U1, U2>& p);
+    template<class U1, class U2>
+      constexpr const pair& operator=(const pair<U1, U2>& p) const;
     constexpr pair& operator=(pair&& p) noexcept($see below$);
+    constexpr const pair& operator=(pair&& p) const;
     template<class U1, class U2>
       constexpr pair& operator=(pair<U1, U2>&& p);
+    template<class U1, class U2>
+      constexpr const pair& operator=(pair<U1, U2>&& p) const;

     constexpr void swap(pair& p) noexcept($see below$);
+    constexpr void swap(const pair& p) const noexcept($see below$);
   };

   template<class T1, class T2>
     pair(T1, T2) -> pair<T1, T2>;
 }
```

[...]

::: add

::: itemdecl

```c++
template<class U1, class U2> constexpr explicit($see below$) pair(pair<U1, U2>& p);
template<class U1, class U2> constexpr explicit($see below$) pair(const pair<U1, U2>& p);
template<class U1, class U2> constexpr explicit($see below$) pair(pair<U1, U2>&& p);
template<class U1, class U2> constexpr explicit($see below$) pair(const pair<U1, U2>&& p);
```

[?]{.pnum} Let `FWD(u)` be `static_cast<decltype(u)>(u)`.

[?]{.pnum} _Constraints_:

- [?.#]{.pnum} `is_constructible_v<first_type, decltype(get<0>(FWD(p)))>` is `true` and
- [?.#]{.pnum} `is_constructible_v<second_type, decltype(get<1>(FWD(p)))>` is `true`.

[?]{.pnum} _Effects:_  Initializes `first` with `get<0>(FWD(p))` and `second` with `get<1>(FWD(p))`.

[?]{.pnum} _Remarks:_ The expression inside `explicit` is equivalent to:
`!is_convertible_v<decltype(get<0>(FWD(p))), first_type> || !is_convertible_v<decltype(get<1>(FWD(p))), second_type>`.

:::
:::


::: rm

::: itemdecl

```c++
template<class U1, class U2> constexpr explicit($see below$) pair(const pair<U1, U2>& p);
```
[14]{.pnum} _Constraints:_

- [14.1]{.pnum} `is_constructible_v<first_type, const U1&>` is `true` and
- [14.2]{.pnum} `is_constructible_v<second_type, const U2&>` is `true`.

[15]{.pnum} _Effects:_  Initializes members from the corresponding members of the argument.

[16]{.pnum} _Remarks:_ The expression inside `explicit` is equivalent to:
`!is_convertible_v<const U1&, first_type> || !is_convertible_v<const U2&, second_type>`


```c++
template<class U1, class U2> constexpr explicit($see below$) pair(pair<U1, U2>&& p);
```

[17]{.pnum} _Constraints:_

- [17.1]{.pnum} `is_constructible_v<first_type, U1>` is `true` and
- [17.2]{.pnum} `is_constructible_v<second_type, U2>` is `true`.

[18]{.pnum} _Effects:_ Initializes `first` with `std::forward<U1>(p.first)` and `second` with `std::forward<U2>(p.second)`.

[19]{.pnum} _Remarks:_ The expression inside `explicit` is equivalent to:
`!is_convertible_v<U1, first_type> || !is_convertible_v<U2, second_type>`

:::

:::

::: add
::: itemdecl

```cpp
constexpr const pair& operator=(const pair& p) const;
```

[?]{.pnum} _Constraints_:

- [?.#]{.pnum} `is_copy_assignable<const first_type>` is `true` and
- [?.#]{.pnum} `is_copy_assignable<const second_type>` is `true`.

[?]{.pnum} _Effects_: Assigns `p.first` to `first` and `p.second` to `second`.

[?]{.pnum} _Returns_: `*this`.


```c++
template<class U1, class U2> constexpr const pair& operator=(const pair<U1, U2>& p) const;
```

[?]{.pnum} _Constraints:_

- [?.#]{.pnum} `is_assignable_v<const first_type&, const U1&>` is `true`, and
- [?.#]{.pnum} `is_assignable_v<const second_type&, const U2&>` is `true`.

[?]{.pnum} _Effects:_ Assigns `p.first` to `first` and `p.second` to `second`.

[?]{.pnum} _Returns_: `*this`.

```cpp
constexpr const pair& operator=(pair&& p) const;
```

[?]{.pnum} _Constraints_:

- [?.#]{.pnum} `is_assignable<const first_type&, first_type>` is `true` and
- [?.#]{.pnum} `is_assignable<const second_type&, second_type>` is `true`.

[?]{.pnum} _Effects_: Assigns `std::forward<first_type>(p.first)` to `first` and `std::forward<second_type>(p.second)` to `second`.

[?]{.pnum} _Returns_: `*this`.

```c++
template<class U1, class U2> constexpr const pair& operator=(pair<U1, U2>&& p) const;
```

[?]{.pnum} _Constraints:_

- [?.#]{.pnum} `is_assignable_v<const first_type&, U1>` is `true`, and
- [?.#]{.pnum} `is_assignable_v<const second_type&, U2>` is `true`.

[?]{.pnum} _Effects:_ Assigns `std::forward<U1>(p.first)` to `first` and `std::forward<U2>(u.second)` to `second`.

[?]{.pnum} _Returns_: `*this`.

:::

:::

::: itemdecl
```diff
  constexpr void swap(pair& p) noexcept($see below$);
+ constexpr void swap(const pair& p) const noexcept($see below$);
```

[?]{.pnum} [_Mandates:_]{.diffins}

- [?.#]{.pnum} [For the first overload, `is_swappable_v<T1>` is `true` and `is_swappable_v<T2>` is `true`.]{.diffins}
- [?.#]{.pnum} [For the second overload, `is_swappable_v<const T1>` is `true` and `is_swappable_v<const T2>` is `true`.]{.diffins}

[35]{.pnum} _Preconditions_: `first` is swappable with ([swappable.requirements]{.sref}) `p.first` and `second` is swappable with `p.second`.

[36]{.pnum} _Effects_: Swaps `first` with `p.first` and `second` with `p.second`.

[37]{.pnum} _Remarks_: The expression inside `noexcept` is equivalent to

- [37.#]{.pnum} `is_nothrow_swappable_v<first_type> && is_nothrow_swappable_v<second_type>` [for the first overload.]{.diffins}
- [37.#]{.pnum} [`is_nothrow_swappable_v<const first_type> && is_nothrow_swappable_v<const second_type>` for the second overload.]{.diffins}

:::

- Edit [pairs.spec]{.sref} as indicated:

::: itemdecl

```diff
  template<class T1, class T2>
    constexpr void swap(pair<T1, T2>& x, pair<T1, T2>& y) noexcept(noexcept(x.swap(y)));
+ template<class T1, class T2>
+   constexpr void swap(const pair<T1, T2>& x, const pair<T1, T2>& y) noexcept(noexcept(x.swap(y)));
```

[3]{.pnum} _Constraints_:

- [3.#]{.pnum} [For the first overload,]{.diffins} `is_swappable_v<T1>` is `true` and `is_swappable_v<T2>` is `true`.
- [3.#]{.pnum} [For the second overload, `is_swappable_v<const T1>` is `true` and `is_swappable_v<const T2>` is `true`.]{.diffins}

[4]{.pnum} _Effects_: Equivalent to `x.swap(y)`.

:::

- Edit [memory.syn]{.sref}, header `<memory>` synopsis, as indicated:

```diff
 #include <compare>              // see [compare.syn]

 namespace std {
   // [...]

   // [allocator.uses.construction], uses-allocator construction
   template<class T, class Alloc, class... Args>
     constexpr auto uses_allocator_construction_args(const Alloc& alloc,
                                                     Args&&... args) noexcept -> $see below$;
   template<class T, class Alloc, class Tuple1, class Tuple2>
     constexpr auto uses_allocator_construction_args(const Alloc& alloc, piecewise_construct_t,
                                                     Tuple1&& x, Tuple2&& y)
                                                     noexcept -> $see below$;
   template<class T, class Alloc>
     constexpr auto uses_allocator_construction_args(const Alloc& alloc) noexcept -> $see below$;
   template<class T, class Alloc, class U, class V>
     constexpr auto uses_allocator_construction_args(const Alloc& alloc,
                                                     U&& u, V&& v) noexcept -> $see below$;
+  template<class T, class Alloc, class U, class V>
+    constexpr auto uses_allocator_construction_args(const Alloc& alloc,
+                                                    pair<U,V>& pr) noexcept -> $see below$;
   template<class T, class Alloc, class U, class V>
     constexpr auto uses_allocator_construction_args(const Alloc& alloc,
                                                     const pair<U,V>& pr) noexcept -> $see below$;
   template<class T, class Alloc, class U, class V>
     constexpr auto uses_allocator_construction_args(const Alloc& alloc,
                                                     pair<U,V>&& pr) noexcept -> $see below$;
+  template<class T, class Alloc, class U, class V>
+    constexpr auto uses_allocator_construction_args(const Alloc& alloc,
+                                                    const pair<U,V>&& pr) noexcept -> $see below$;
   template<class T, class Alloc, class... Args>
     constexpr T make_obj_using_allocator(const Alloc& alloc, Args&&... args);
   template<class T, class Alloc, class... Args>
     constexpr T* uninitialized_construct_using_allocator(T* p, const Alloc& alloc,
                                                          Args&&... args);

   // [...]
 }
```

- Edit [allocator.uses.construction]{.sref} as indicated (the wording below
incorporates the proposed resolution of [@LWG3527]):

::: itemdecl

```diff
+ template<class T, class Alloc, class U, class V>
+   constexpr auto uses_allocator_construction_args(const Alloc& alloc,
+                                                   pair<U,V>& pr) noexcept -> $see below$;
  template<class T, class Alloc, class U, class V>
    constexpr auto uses_allocator_construction_args(const Alloc& alloc,
                                                    const pair<U,V>& pr) noexcept -> $see below$;
```

[12]{.pnum} _Constraints_: `T` is a specialization of `pair`.

[13]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
return uses_allocator_construction_args<T>(alloc, piecewise_construct,
                                           forward_as_tuple(pr.first),
                                           forward_as_tuple(pr.second));
```
:::

```diff
  template<class T, class Alloc, class U, class V>
    constexpr auto uses_allocator_construction_args(const Alloc& alloc,
                                                    pair<U,V>&& pr) noexcept -> $see below$;
+ template<class T, class Alloc, class U, class V>
+   constexpr auto uses_allocator_construction_args(const Alloc& alloc,
+                                                   const pair<U,V>&& pr) noexcept -> $see below$;
```

[14]{.pnum} _Constraints_: `T` is a specialization of `pair`.

[15]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
return uses_allocator_construction_args<T>(alloc, piecewise_construct,
                                           forward_as_tuple(@[std::move(pr).first]{.diffdel}[get<0>(std::move(pr))]{.diffins}@),
                                           forward_as_tuple(@[std::move(pr).second]{.diffdel}[get<1>(std::move(pr))]{.diffins}@));
```
:::
:::
:::

## `vector<bool>::reference`

Edit [vector.bool]{.sref}, class template partial specialization `vector<bool, Allocator>` synopsis, as indicated:

```diff
 namespace std {
   template<class Allocator>
   class vector<bool, Allocator> {
   public:
     // [...]

     // bit reference
     class reference {
       friend class vector;
       constexpr reference() noexcept;
     public:
       constexpr reference(const reference&) = default;
       constexpr ~reference();
       constexpr operator bool() const noexcept;
       constexpr reference& operator=(const bool x) noexcept;
       constexpr reference& operator=(const reference& x) noexcept;
+      constexpr const reference& operator=(bool x) const noexcept;
       constexpr void flip() noexcept;   // flips the bit
     };

     // [...]
   };
 }
```

## Conversion and common type for integer-class types

Edit [iterator.concept.winc]{.sref} as indicated:

::: bq

[6]{.pnum} Expressions of integer-class type are explicitly convertible to
any integral type [as well as any integer-class type]{.diffins}. Expressions of integral
type are both implicitly and explicitly convertible to any integer-class type.
Conversions between integral and integer-class types
[and between two integer class types]{.diffins}
do not exit via an exception.

[&hellip;]

[11]{.pnum} A type `I` other than _cv_ `bool` is _integer-like_ if it models `integral<I>`
or if it is an integer-class type. An integer-like type `I` is _signed-integer-like_
if it models `signed_­integral<I>` or if it is a signed-integer-class type.
An integer-like type `I` is _unsigned-integer-like_ if it models
`unsigned_­integral<I>` or if it is an unsigned-integer-class type.

::: add

[?]{.pnum} For any two integer-like types `I1` and `I2`, at least one of which is
an integer-class type, `common_type_t<I1, I2>` denotes an integer-like
type whose width is not less than that of `I1` or `I2`. If both `I1` and `I2` are
signed-integer-like types, then `common_type_t<I1, I2>` is also a
signed-integer-like type.

:::

:::

## Addition to `<ranges>`

Add the following to [ranges.syn]{.sref}, header `<ranges>` synopsis:

```cpp
// [...]
namespace std::ranges {
  // [...]

  // [range.zip], zip view
  template<input_range... Views>
    requires (view<Views> && ...) && (sizeof...(Views) > 0)
  class zip_view;

  template<class... Views>
    inline constexpr bool enable_borrowed_range<zip_view<Views...>> =
      (enable_borrowed_range<Views> && ...);

  namespace views { inline constexpr $unspecified$ zip = $unspecified$; }

  // [range.zip.transform], zip transform view
  template<copy_constructible F, input_range... Views>
    requires (view<Views> && ...) && (sizeof...(Views) > 0) && is_object_v<F> &&
             regular_invocable<F&, range_reference_t<Views>...> &&
             $can-reference$<invoke_result_t<F&, range_reference_t<Views>...>>
  class zip_transform_view;

  namespace views { inline constexpr $unspecified$ zip_transform = $unspecified$; }

  // [range.adjacent], adjacent view
  template<forward_range V, size_t N>
    requires view<V> && (N > 0)
  class adjacent_view;

  template<class V, size_t N>
    inline constexpr bool enable_borrowed_range<adjacent_view<V, N>> =
      enable_borrowed_range<V>;

  namespace views {
    template<size_t N>
      inline constexpr $unspecified$ adjacent = $unspecified$;
    inline constexpr auto pairwise = adjacent<2>;
  }

  // [range.adjacent.transform], adjacent transform view
  template<forward_range V, copy_constructible F, size_t N>
    requires $see below$
  class adjacent_transform_view;

  namespace views {
    template<size_t N>
      inline constexpr $unspecified$ adjacent_transform = $unspecified$;
    inline constexpr auto pairwise_transform = adjacent_transform<2>;
  }
}

```

## `zip`

Add the following subclause to [range.adaptors]{.sref}.

### 24.7.? Zip view [range.zip] {-}

#### 24.7.?.1 Overview [range.zip.overview] {-}

[#]{.pnum} `zip_view` takes any number of `view`s and produces a `view` of
tuples of references to the corresponding elements of the constituent views.

[#]{.pnum} The name `views::zip` denotes a customization point object
([customization.point.object]{.sref}). Given a pack of subexpressions `Es...`,
the expression `views::zip(Es...)` is expression-equivalent to

- [#.#]{.pnum} `$decay-copy$(views::empty<tuple<>>)` if `Es` is an empty pack,
- [#.#]{.pnum} otherwise, `zip_view<views::all_t<decltype((Es))>...>(Es...)`.

::: example

```cpp
vector v = {1, 2};
list l = {'a', 'b', 'c'};

auto z = views::zip(v, l);
range_reference_t<decltype(z)> f = z.front();    // f is a pair<int&, char&> that refers to the first element of v and l

for (auto&& [x, y] : z) {
  cout << '(' << x << ", " << y << ") "; // prints: (1, a) (2, b)
}

```
:::

#### 24.7.?.2 Class template `zip_view` [range.zip.view] {-}

```cpp
namespace std::ranges {

template<class... Rs>
concept $zip-is-common$ =             // exposition only
  (sizeof...(Rs) == 1 && (common_range<Rs> && ...)) ||
  (!(bidirectional_range<Rs> && ...) && (common_range<Rs> && ...)) ||
  ((random_access_range<Rs> && ...) && (sized_range<Rs> && ...));

template<class... Ts>
using $tuple-or-pair$ = $see below$;  // exposition only

template<class F, class Tuple>
constexpr auto $tuple-transform$(F&& f, Tuple&& tuple) // exposition only
{
  return apply([&]<class... Ts>(Ts&&... elements){
    return $tuple-or-pair$<invoke_result_t<F&, Ts>...>(
      invoke(f, std::forward<Ts>(elements))...
    );
  }, std::forward<Tuple>(tuple));
}

template<class F, class Tuple>
constexpr void $tuple-for-each$(F&& f, Tuple&& tuple) // exposition only
{
  apply([&]<class... Ts>(Ts&&... elements){
    (invoke(f, std::forward<Ts>(elements)), ...);
  }, std::forward<Tuple>(tuple));
}

template<input_range... Views>
  requires (view<Views> && ...) && (sizeof...(Views) > 0)
class zip_view : public view_interface<zip_view<Views...>>{
  tuple<Views...> $views_$;                // exposition only

  template<bool> class $iterator$;         // exposition only
  template<bool> class $sentinel$;         // exposition only

public:
  constexpr zip_view() = default;
  constexpr explicit zip_view(Views... views);

  constexpr auto begin() requires (!($simple-view$<Views> && ...)) {
    return $iterator$<false>($tuple-transform$(ranges::begin, $views_$));
  }
  constexpr auto begin() const requires (range<const Views> && ...) {
    return $iterator$<true>($tuple-transform$(ranges::begin, $views_$));
  }

  constexpr auto end() requires (!($simple-view$<Views> && ...)) {
    if constexpr (!$zip-is-common$<Views...>) {
      return $sentinel$<false>($tuple-transform$(ranges::end, $views_$));
    }
    else if constexpr ((random_access_range<Views> && ...)) {
      return begin() + iter_difference_t<$iterator$<false>>(size());
    }
    else {
      return $iterator$<false>($tuple-transform$(ranges::end, $views_$));
    }
  }

  constexpr auto end() const requires (range<const Views> && ...) {
    if constexpr (!$zip-is-common$<const Views...>) {
      return $sentinel$<true>($tuple-transform$(ranges::end, $views_$));
    }
    else if constexpr ((random_access_range<const Views> && ...)) {
      return begin() + iter_difference_t<$iterator$<true>>(size());
    }
    else {
      return $iterator$<true>($tuple-transform$(ranges::end, $views_$));
    }
  }

  constexpr auto size() requires (sized_range<Views> && ...);
  constexpr auto size() const requires (sized_range<const Views> && ...);
};

template<class... Rs>
  zip_view(Rs&&...) -> zip_view<views::all_t<Rs>...>;

}
```

[#]{.pnum} Given some pack of types `Ts`, the alias template `$tuple-or-pair$` is defined as follows:

- [#.#]{.pnum} If `sizeof...(Ts)` is 2, `$tuple-or-pair$<Ts...>` denotes `pair<Ts...>`.
- [#.#]{.pnum} Otherwise, `$tuple-or-pair$<Ts...>` denotes `tuple<Ts...>`.

[#]{.pnum} Two `zip_view` objects have the same underlying sequence if
and only if the corresponding elements of `$views_$` are equal
([concepts.equality]{.sref}) and have the same underlying sequence. [In particular,
comparison of iterators obtained from `zip_view` objects that do not have
the same underlying sequence is not required to produce meaningful results
([iterator.concept.forward]{.sref}).]{.note}

::: itemdecl

```cpp
constexpr explicit zip_view(Views... views);
```

[#]{.pnum} _Effects_: Initializes `$views_$` with `std::move(views)...`.

```cpp
constexpr auto size() requires (sized_range<Views> && ...);
constexpr auto size() const requires (sized_range<const Views> && ...);
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq

```cpp
return apply([](auto... sizes){
  using CT = $make-unsigned-like-t$<common_type_t<decltype(sizes)...>>;
  return ranges::min({CT(sizes)...});
}, $tuple-transform$(ranges::size, $views_$));
```
:::
:::

#### 24.7.?.3 Class template `zip_view::$iterator$` [range.zip.iterator] {-}

```cpp
namespace std::ranges {
  template<bool Const, class... Views>
    concept $all-random-access$ = (random_access_range<$maybe-const$<Const, Views>> && ...);    // exposition only
  template<bool Const, class... Views>
    concept $all-bidirectional$ = (bidirectional_range<$maybe-const$<Const, Views>> && ...);    // exposition only
  template<bool Const, class... Views>
    concept $all-forward$ = (forward_range<$maybe-const$<Const, Views>> && ...);                // exposition only

  template<input_range... Views>
    requires (view<Views> && ...) && (sizeof...(Views) > 0)
  template<bool Const>
  class zip_view<Views...>::$iterator$ {
    $tuple-or-pair$<iterator_t<$maybe-const$<Const, Views>>...> $current_$;                             // exposition only
    constexpr explicit $iterator$($tuple-or-pair$<iterator_t<$maybe-const$<Const, Views>>...> current); // exposition only
  public:
    using iterator_category = input_iterator_tag; // not always present
    using iterator_concept  = $see below$;
    using value_type = $tuple-or-pair$<range_value_t<$maybe-const$<Const, Views>>...>;
    using difference_type = common_type_t<range_difference_t<$maybe-const$<Const, Views>>...>;

    $iterator$() = default;
    constexpr $iterator$($iterator$<!Const> i)
      requires Const && (convertible_to<iterator_t<Views>, iterator_t<$maybe-const$<Const, Views>>> && ...);

    constexpr auto operator*() const;
    constexpr $iterator$& operator++();
    constexpr void operator++(int);
    constexpr $iterator$ operator++(int) requires $all-forward$<Const, Views...>;

    constexpr $iterator$& operator--() requires $all-bidirectional$<Const, Views...>;
    constexpr $iterator$ operator--(int) requires $all-bidirectional$<Const, Views...>;

    constexpr $iterator$& operator+=(difference_type x)
      requires $all-random-access$<Const, Views...>;
    constexpr $iterator$& operator-=(difference_type x)
      requires $all-random-access$<Const, Views...>;

    constexpr auto operator[](difference_type n) const
      requires $all-random-access$<Const, Views...>;

    friend constexpr bool operator==(const $iterator$& x, const $iterator$& y)
      requires (equality_comparable<iterator_t<$maybe-const$<Const, Views>>> && ...);

    friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
      requires $all-random-access$<Const, Views...>;
    friend constexpr bool operator>(const $iterator$& x, const $iterator$& y)
      requires $all-random-access$<Const, Views...>;
    friend constexpr bool operator<=(const $iterator$& x, const $iterator$& y)
      requires $all-random-access$<Const, Views...>;
    friend constexpr bool operator>=(const $iterator$& x, const $iterator$& y)
      requires $all-random-access$<Const, Views...>;
    friend constexpr auto operator<=>(const $iterator$& x, const $iterator$& y)
      requires $all-random-access$<Const, Views...> &&
               (three_way_comparable<iterator_t<$maybe-const$<Const, Views>>> && ...);

    friend constexpr $iterator$ operator+(const $iterator$& i, difference_type n)
      requires $all-random-access$<Const, Views...>;
    friend constexpr $iterator$ operator+(difference_type n, const $iterator$& i)
      requires $all-random-access$<Const, Views...>;
    friend constexpr $iterator$ operator-(const $iterator$& i, difference_type n)
      requires $all-random-access$<Const, Views...>;
    friend constexpr difference_type operator-(const $iterator$& x, const $iterator$& y)
      requires (sized_sentinel_for<iterator_t<$maybe-const$<Const, Views>>, iterator_t<$maybe-const$<Const, Views>>> && ...);

    friend constexpr auto iter_move(const $iterator$& i)
      noexcept($see below$);

    friend constexpr void iter_swap(const $iterator$& l, const $iterator$& r)
      noexcept($see below$)
      requires (indirectly_swappable<iterator_t<$maybe-const$<Const, Views>>> && ...);
  };
}
```

[#]{.pnum} `$iterator$::iterator_concept` is defined as follows:

- [#.#]{.pnum} If `$all-random-access$<Const, Views...>` is modeled, then `iterator_concept` denotes `random_access_iterator_tag`.
- [#.#]{.pnum} Otherwise, if `$all-bidirectional$<Const, Views...>` is modeled, then `iterator_concept` denotes `bidirectional_iterator_tag`.
- [#.#]{.pnum} Otherwise, if `$all-forward$<Const, Views...>` is modeled, then `iterator_concept` denotes `forward_iterator_tag`.
- [#.#]{.pnum} Otherwise, `iterator_concept` denotes `input_iterator_tag`.

[#]{.pnum} `$iterator$::iterator_category` is present if and only if `$all-forward$<Const, Views...>` is modeled.

[#]{.pnum} If the invocation of any non-const member function of _`iterator`_ exits via an exception,
the iterator acquires a singular value.

::: itemdecl

```cpp
constexpr explicit $iterator$($tuple-or-pair$<iterator_t<$maybe-const$<Const, Views>>...> current);
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `std::move(current)`.

```cpp
constexpr $iterator$($iterator$<!Const> i)
  requires Const && (convertible_to<iterator_t<Views>, iterator_t<$maybe-const$<Const, Views>>> && ...);
```

[#]{.pnum} _Effects_: Initializes `$current_$` with `std::move(i.$current_$)`.

```cpp
constexpr auto operator*() const;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return $tuple-transform$([](auto& i) -> decltype(auto) { return *i; }, $current_$);
```
:::

```cpp
constexpr $iterator$& operator++();
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  $tuple-for-each$([](auto& i) { ++i; }, $current_$);
  return *this;
```
:::

```cpp
constexpr void operator++(int);
```

[#]{.pnum} _Effects_: Equivalent to `++*this`.

```cpp
constexpr $iterator$ operator++(int) requires $all-forward$<Const, Views...>;
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
constexpr $iterator$& operator--() requires $all-bidirectional$<Const, Views...>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  $tuple-for-each$([](auto& i) { --i; }, $current_$);
  return *this;
```
:::


```cpp
constexpr $iterator$ operator--(int) requires $all-bidirectional$<Const, Views...>;
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
  requires $all-random-access$<Const, Views...>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  $tuple-for-each$([&]<class I>(I& i) { i += iter_difference_t<I>(x); }, $current_$);
  return *this;
```
:::

```cpp
  constexpr $iterator$& operator-=(difference_type x)
    requires $all-random-access$<Const, Views...>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  $tuple-for-each$([&]<class I>(I& i) { i -= iter_difference_t<I>(x); }, $current_$);
  return *this;
```
:::

```cpp
constexpr auto operator[](difference_type n) const
  requires $all-random-access$<Const, Views...>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return $tuple-transform$([&]<class I>(I& i) -> decltype(auto) {
    return i[iter_difference_t<I>(n)];
  }, $current_$);
```
:::

```cpp
friend constexpr bool operator==(const $iterator$& x, const $iterator$& y)
  requires (equality_comparable<iterator_t<$maybe-const$<Const, Views>>> && ...);
```
[#]{.pnum} _Returns_:

- [#.#]{.pnum} `x.$current_$ == y.$current_$` if `$all-bidirectional$<Const, Views...>` is `true`.
- [#.#]{.pnum} Otherwise, `true` if there exists an integer 0 &le; _i_ &lt; `sizeof...(Views)`
  such that `bool(std::get<$i$>(x.$current_$) == std::get<$i$>(y.$current_$))` is `true`.
  [This allows `zip_view` to model `common_range` when all constituent views model `common_range`.]{.note}
- [#.#]{.pnum} Otherwise, `false`.


```cpp
friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
  requires $all-random-access$<Const, Views...>;
```
[#]{.pnum} _Returns_: `x.$current_$ < y.$current_$`.

```cpp
friend constexpr bool operator>(const $iterator$& x, const $iterator$& y)
  requires $all-random-access$<Const, Views...>;
```
[#]{.pnum} _Effects_: Equivalent to: `return y < x; `

```cpp
friend constexpr bool operator<=(const $iterator$& x, const $iterator$& y)
  requires $all-random-access$<Const, Views...>;
```

[#]{.pnum} _Effects_: Equivalent to: `return !(y < x); `


```cpp
friend constexpr bool operator>=(const $iterator$& x, const $iterator$& y)
  requires $all-random-access$<Const, Views...>;
```

[#]{.pnum} _Effects_: Equivalent to: `return !(x < y); `

```cpp
friend constexpr auto operator<=>(const $iterator$& x, const $iterator$& y)
  requires $all-random-access$<Const, Views...> &&
            (three_way_comparable<iterator_t<$maybe-const$<Const, Views>>> && ...);
```

[#]{.pnum} _Returns_: `x.$current_$ <=> y.$current_$`.


```cpp
friend constexpr $iterator$ operator+(const $iterator$& i, difference_type n)
  requires $all-random-access$<Const, Views...>;
friend constexpr $iterator$ operator+(difference_type n, const $iterator$& i)
  requires $all-random-access$<Const, Views...>;
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
  requires $all-random-access$<Const, Views...>;
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
  requires (sized_sentinel_for<iterator_t<$maybe-const$<Const, Views>>, iterator_t<$maybe-const$<Const, Views>>> && ...);
```
[#]{.pnum} Let _DIST(i)_ be `difference_type(std::get<$i$>(x.$current_$) - std::get<$i$>(y.$current_$))`.

[#]{.pnum} _Returns:_ The value with the smallest absolute value among _DIST(n)_ for all integers 0 &le; _n_ &lt; `sizeof...(Views)`.

```cpp
friend constexpr auto iter_move(const $iterator$& i)
  noexcept($see below$);
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return $tuple-transform$(ranges::iter_move, i.$current_$);
```
:::

[#]{.pnum} _Remarks:_ The expression within `noexcept` is equivalent to

::: bq
```cpp
  (noexcept(ranges::iter_move(declval<iterator_t<$maybe-const$<Const, Views>> const&>())) && ...) &&
  (is_nothrow_move_constructible_v<range_rvalue_reference_t<$maybe-const$<Const, Views>>> && ...)
```
:::

```cpp
friend constexpr void iter_swap(const $iterator$& l, const $iterator$& r)
  noexcept($see below$)
  requires (indirectly_swappable<iterator_t<$maybe-const$<Const, Views>>> && ...);
```

[#]{.pnum} _Effects_: For every integer 0 &le; _i_ &lt; `sizeof...(Views)`,
performs `ranges::iter_swap(std::get<$i$>(l.$current_$), std::get<$i$>(r.$current_$))`.

[#]{.pnum} _Remarks:_ The expression within `noexcept` is equivalent to the logical AND of the following expressions:

::: bq
```cpp
  noexcept(ranges::iter_swap(std::get<$i$>(l.$current_$), std::get<$i$>(r.$current_$)))
```
:::

for every integer 0 &le; _i_ &lt; `sizeof...(Views)`.

:::

#### 24.7.?.4 Class template `zip_view::$sentinel$` [range.zip.sentinel] {-}

```cpp
namespace std::ranges {
  template<input_range... Views>
    requires (view<Views> && ...) && (sizeof...(Views) > 0)
  template<bool Const>
  class zip_view<Views...>::$sentinel$ {
    $tuple-or-pair$<sentinel_t<$maybe-const$<Const, Views>>...> $end_$;                                // exposition only
    constexpr explicit $sentinel$($tuple-or-pair$<sentinel_t<$maybe-const$<Const, Views>>...> end);    // exposition only
  public:
    $sentinel$() = default;
    constexpr $sentinel$($sentinel$<!Const> i)
      requires Const && (convertible_to<sentinel_t<Views>, sentinel_t<$maybe-const$<Const, Views>>> && ...);

    template<bool OtherConst>
      requires (sentinel_for<sentinel_t<$maybe-const$<Const, Views>>, iterator_t<$maybe-const$<OtherConst, Views>>> && ...)
    friend constexpr bool operator==(const $iterator$<OtherConst>& x, const $sentinel$& y);

    template<bool OtherConst>
      requires (sized_sentinel_for<sentinel_t<$maybe-const$<Const, Views>>, iterator_t<$maybe-const$<OtherConst, Views>>> && ...)
    friend constexpr common_type_t<range_difference_t<$maybe-const$<OtherConst, Views>>...>
      operator-(const $iterator$<OtherConst>& x, const $sentinel$& y);

    template<bool OtherConst>
      requires (sized_sentinel_for<sentinel_t<$maybe-const$<Const, Views>>, iterator_t<$maybe-const$<OtherConst, Views>>> && ...)
    friend constexpr common_type_t<range_difference_t<$maybe-const$<OtherConst, Views>>...>
      operator-(const $sentinel$& y, const $iterator$<OtherConst>& x);
  };
}
```
::: itemdecl

```cpp
constexpr explicit $sentinel$($tuple-or-pair$<sentinel_t<$maybe-const$<Const, Views>>...> end);
```

[#]{.pnum} _Effects_: Initializes `$end_$` with `end`.

```cpp
constexpr $sentinel$($sentinel$<!Const> i)
  requires Const && (convertible_to<sentinel_t<Views>, sentinel_t<$maybe-const$<Const, Views>>> && ...);
```

[#]{.pnum} _Effects_: Initializes `$end_$` with `std::move(i.$end_$)`.

```cpp
template<bool OtherConst>
  requires (sentinel_for<sentinel_t<$maybe-const$<Const, Views>>, iterator_t<$maybe-const$<OtherConst, Views>>> && ...)
friend constexpr bool operator==(const $iterator$<OtherConst>& x, const $sentinel$& y);
```

[#]{.pnum} _Returns_: `true` if there exists an integer 0 &le; _i_ &lt; `sizeof...(Views)`
such that `bool(std::get<$i$>(x.$current_$) == std::get<$i$>(y.$end_$))` is `true`. Otherwise, `false`.


```cpp
template<bool OtherConst>
  requires (sized_sentinel_for<sentinel_t<$maybe-const$<Const, Views>>, iterator_t<$maybe-const$<OtherConst, Views>>> && ...)
friend constexpr common_type_t<range_difference_t<$maybe-const$<OtherConst, Views>>...>
  operator-(const $iterator$<OtherConst>& x, const $sentinel$& y);
```

[#]{.pnum} Let `D` be the return type. Let _DIST(i)_ be `D(std::get<$i$>(x.$current_$) - std::get<$i$>(y.$end_$))`.

[#]{.pnum} _Returns:_ The value with the smallest absolute value among _DIST(n)_ for all integers 0 &le; _n_ &lt; `sizeof...(Views)`.

```cpp
template<bool OtherConst>
  requires (sized_sentinel_for<sentinel_t<$maybe-const$<Const, Views>>, iterator_t<$maybe-const$<OtherConst, Views>>> && ...)
friend constexpr common_type_t<range_difference_t<$maybe-const$<OtherConst, Views>>...>
  operator-(const $sentinel$& y, const $iterator$<OtherConst>& x);
```
[#]{.pnum} _Effects_: Equivalent to `return -(x - y);`

:::

## `zip_transform`


Add the following subclause to [range.adaptors]{.sref}.

### 24.7.? Zip transform view [range.zip.transform] {-}

#### 24.7.?.1 Overview [range.zip.transform.overview] {-}

[#]{.pnum} `zip_transform_view` takes an invocable object and any number of `view`s
and produces a `view` whose _M <sup>th</sup>_ element is the result of applying
the invocable object to the _M <sup>th</sup>_ elements of all views.

[#]{.pnum} The name `views::zip_transform` denotes a customization point object
([customization.point.object]{.sref}). Given a subexpression `F` and a pack of subexpressions `Es...`,

- [#.#]{.pnum} if `Es` is an empty pack, let `FD` be `decay_t<decltype((F))>`.
  - [#.#.#]{.pnum} if `copy_constructible<FD> && regular_invocable<FD&>` is `false`, `views::zip_transform(F, Es...)` is ill-formed.
  - [#.#.#]{.pnum} Otherwise, the expression `views::zip_transform(F, Es...)` is expression-equivalent to `(void)F, $decay-copy$(views::empty<decay_t<invoke_result_t<FD&>>>)`.
- [#.#]{.pnum} Otherwise, the expression `views::zip_transform(F, Es...)` is expression-equivalent to `zip_transform_view(F, Es...)`.

::: example

```cpp
vector v1 = {1, 2};
vector v2 = {4, 5, 6};

for (auto i : views::zip_transform(plus(), v1, v2)) {
  cout << i << ' '; // prints: 5 7
}

```
:::

#### 24.7.?.2 Class template `zip_transform_view` [range.zip.transform.view] {-}

```cpp
namespace std::ranges {

template<copy_constructible F, input_range... Views>
  requires (view<Views> && ...) && (sizeof...(Views) > 0) && is_object_v<F> &&
            regular_invocable<F&, range_reference_t<Views>...> &&
            $can-reference$<invoke_result_t<F&, range_reference_t<Views>...>>
class zip_transform_view : public view_interface<zip_transform_view<F, Views...>> {
  $semiregular-box$<F> $fun_$;               // exposition only
  zip_view<Views...> $zip_$;               // exposition only

  using $InnerView$ = zip_view<Views...>;  // exposition only
  template<bool Const>
  using $ziperator$ = iterator_t<$maybe-const$<Const, $InnerView$>>;  // exposition only
  template<bool Const>
  using $zentinel$ = sentinel_t<$maybe-const$<Const, $InnerView$>>;   // exposition only

  template<bool> class $iterator$;         // exposition only
  template<bool> class $sentinel$;         // exposition only

public:
  constexpr zip_transform_view() = default;

  constexpr explicit zip_transform_view(F fun, Views... views);

  constexpr auto begin() {
    return $iterator$<false>(*this, $zip_$.begin());
  }

  constexpr auto begin() const
    requires range<const $InnerView$> &&
             regular_invocable<const F&, range_reference_t<const Views>...>
  {
    return $iterator$<true>(*this, $zip_$.begin());
  }

  constexpr auto end() {
    return $sentinel$<false>($zip_$.end());
  }

  constexpr auto end() requires common_range<$InnerView$> {
    return $iterator$<false>(*this, $zip_$.end());
  }

  constexpr auto end() const
    requires range<const $InnerView$> &&
             regular_invocable<const F&, range_reference_t<const Views>...>
  {
    return $sentinel$<true>($zip_$.end());
  }

  constexpr auto end() const
    requires common_range<const $InnerView$> &&
             regular_invocable<const F&, range_reference_t<const Views>...>
  {
    return $iterator$<true>(*this, $zip_$.end());
  }

  constexpr auto size() requires sized_range<$InnerView$> {
    return $zip_$.size();
  }

  constexpr auto size() const requires sized_range<const $InnerView$> {
    return $zip_$.size();
  }
};

template<class F, class... Rs>
  zip_transform_view(F, Rs&&...) -> zip_transform_view<F, views::all_t<Rs>...>;

}
```

::: itemdecl

```cpp
constexpr explicit zip_transform_view(F fun, Views... views);
```

[#]{.pnum} _Effects_: Initializes `$fun_$` with `std::move(fun)` and
`$zip_$` with `std::move(views)...`.

:::

#### 24.7.?.3 Class template `zip_transform_view::$iterator$` [range.zip.transform.iterator] {-}

```cpp
namespace std::ranges {
  template<copy_constructible F, input_range... Views>
    requires (view<Views> && ...) && (sizeof...(Views) > 0) && is_object_v<F> &&
              regular_invocable<F&, range_reference_t<Views>...> &&
              $can-reference$<invoke_result_t<F&, range_reference_t<Views>...>>
  template<bool Const>
  class zip_transform_view<F, Views...>::$iterator$ {
    using $Parent$ = $maybe-const$<Const, zip_transform_view>;      // exposition only
    using $Base$ = $maybe-const$<Const, $InnerView$>;                 // exposition only
    $Parent$* $parent_$ = nullptr;                                  // exposition only
    $ziperator$<Const> $inner_$ = $ziperator$<Const>();               // exposition only

    constexpr $iterator$($Parent$& parent, $ziperator$<Const> inner); // exposition only

  public:
    using iterator_category = $see below$;                        // not always present
    using iterator_concept  = typename $ziperator$<Const>::iterator_concept;
    using value_type =
      remove_cvref_t<invoke_result_t<$maybe-const$<Const, F>&, range_reference_t<$maybe-const$<Const, Views>>...>>;
    using difference_type = range_difference_t<$Base$>;

    $iterator$() = default;
    constexpr $iterator$($iterator$<!Const> i)
      requires Const && convertible_to<$ziperator$<false>, $ziperator$<Const>>;

    constexpr decltype(auto) operator*() const noexcept($see below$);
    constexpr $iterator$& operator++();
    constexpr void operator++(int);
    constexpr $iterator$ operator++(int) requires forward_range<$Base$>;

    constexpr $iterator$& operator--() requires bidirectional_range<$Base$>;
    constexpr $iterator$ operator--(int) requires bidirectional_range<$Base$>;

    constexpr $iterator$& operator+=(difference_type x) requires random_access_range<$Base$>;
    constexpr $iterator$& operator-=(difference_type x) requires random_access_range<$Base$>;

    constexpr decltype(auto) operator[](difference_type n) const requires random_access_range<$Base$>;

    friend constexpr bool operator==(const $iterator$& x, const $iterator$& y)
      requires equality_comparable<$ziperator$<Const>>;

    friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr bool operator>(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr bool operator<=(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr bool operator>=(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$>;
    friend constexpr auto operator<=>(const $iterator$& x, const $iterator$& y)
      requires random_access_range<$Base$> && three_way_comparable<$ziperator$<Const>>;

    friend constexpr $iterator$ operator+(const $iterator$& i, difference_type n)
      requires random_access_range<$Base$>;
    friend constexpr $iterator$ operator+(difference_type n, const $iterator$& i)
      requires random_access_range<$Base$>;
    friend constexpr $iterator$ operator-(const $iterator$& i, difference_type n)
      requires random_access_range<$Base$>;
    friend constexpr difference_type operator-(const $iterator$& x, const $iterator$& y)
      requires sized_sentinel_for<$ziperator$<Const>, $ziperator$<Const>>;
  };
}
```

[#]{.pnum} The member _typedef-name_ `$iterator$::iterator_category` is defined if and only if `$Base$` models `forward_range`.
In that case, `$iterator$::iterator_category` is defined as follows:

- If `invoke_result_t<$maybe-const$<Const, F>&, range_reference_t<$maybe-const$<Const, Views>>...>` is not an lvalue reference,
  `iterator_category` denotes `input_iterator_tag`.
- Otherwise, let `Cs...` denote the pack of types `iterator_traits<iterator_t<$maybe-const$<Const, Views>>>::iterator_category...`.
  - If `(derived_from<Cs, random_access_iterator_tag> && ...)` is `true`, `iterator_category` denotes `random_access_iterator_tag`;
  - Otherwise, if `(derived_from<Cs, bidirectional_iterator_tag> && ...)` is `true`, `iterator_category` denotes `bidirectional_iterator_tag`;
  - Otherwise, if `(derived_from<Cs, forward_iterator_tag> && ...)` is `true`, `iterator_category` denotes `forward_iterator_tag`;
  - Otherwise, `iterator_category` denotes `input_iterator_tag`.


::: itemdecl

```cpp
constexpr $iterator$($Parent$& parent, $ziperator$<Const> inner);
```

[#]{.pnum} _Effects_: Initializes `$parent_$` with `addressof(parent)` and `$inner_$` with `std::move(inner)`.

```cpp
constexpr $iterator$($iterator$<!Const> i)
  requires Const && convertible_to<$ziperator$<false>, $ziperator$<Const>>;
```

[#]{.pnum} _Effects_: Initializes `$parent_$` with `i.$parent_$` and `$inner_$` with `std::move(i.$inner_$)`.

```cpp
constexpr decltype(auto) operator*() const noexcept($see below$);
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return apply([&](const auto&... iters) -> decltype(auto) {
    return invoke(*$parent_$->$fun_$, *iters...);
  }, $inner_$.$current_$);
```
:::

[#]{.pnum} _Remarks:_
Let `Is` be the pack `0, 1, ..., (sizeof...(Views)-1)`.
The expression within `noexcept` is equivalent to
`noexcept(invoke(*$parent_$->$fun_$, *std::get<Is>($inner_$.$current_$)...))`.

```cpp
constexpr $iterator$& operator++();
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  ++$inner_$;
  return *this;
```
:::

```cpp
constexpr void operator++(int);
```

[#]{.pnum} _Effects_: Equivalent to `++*this;`.

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
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  --$inner_$;
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
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  $inner_$ += x;
  return *this;
```
:::

```cpp
constexpr $iterator$& operator-=(difference_type x)
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  $inner_$ -= x;
  return *this;
```
:::

```cpp
constexpr decltype(auto) operator[](difference_type n) const
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return apply([&]<class...Is>(const Is&... iters) -> decltype(auto) {
    return invoke(*$parent_$->$fun_$, iters[iter_difference_t<Is>(n)]...);
  }, $inner_$.$current_$);
```
:::

```cpp
friend constexpr bool operator==(const $iterator$& x, const $iterator$& y)
  requires equality_comparable<$ziperator$<Const>>;
friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
friend constexpr bool operator>(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
friend constexpr bool operator<=(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
friend constexpr bool operator>=(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
friend constexpr auto operator<=>(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$> && three_way_comparable<$ziperator$<Const>>;
```
[#]{.pnum} Let _`op`_ be the operator.

[#]{.pnum} _Effects_: Equivalent to: `return x.$inner_$ $op$ y.$inner_$; `


```cpp
friend constexpr $iterator$ operator+(const $iterator$& i, difference_type n)
  requires random_access_range<$Base$>;
friend constexpr $iterator$ operator+(difference_type n, const $iterator$& i)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return $iterator$(*i.$parent_$, i.$inner_$ + n);`

```cpp
friend constexpr $iterator$ operator-(const $iterator$& i, difference_type n)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return $iterator$(*i.$parent_$, i.$inner_$ - n);`

```cpp
friend constexpr difference_type operator-(const $iterator$& x, const $iterator$& y)
  requires sized_sentinel_for<$ziperator$<Const>, $ziperator$<Const>>;
```

[#]{.pnum} _Effects_: Equivalent to: `return x.$inner_$ - y.$inner_$;`

:::

#### 24.7.?.4 Class template `zip_transform_view::$sentinel$` [range.zip.transform.sentinel] {-}

```cpp
namespace std::ranges {
  template<copy_constructible F, input_range... Views>
    requires (view<Views> && ...) && (sizeof...(Views) > 0) && is_object_v<F> &&
              regular_invocable<F&, range_reference_t<Views>...> &&
              $can-reference$<invoke_result_t<F&, range_reference_t<Views>...>>
  template<bool Const>
  class zip_transform_view<F, Views...>::$sentinel$ {
    $zentinel$<Const> $inner_$;                             // exposition only
    constexpr explicit $sentinel$($zentinel$<Const> inner); // exposition only
  public:
    $sentinel$() = default;
    constexpr $sentinel$($sentinel$<!Const> i)
      requires Const && convertible_to<$zentinel$<false>, $zentinel$<Const>>;

    template<bool OtherConst>
      requires sentinel_for<$zentinel$<Const>, $ziperator$<OtherConst>>
    friend constexpr bool operator==(const $iterator$<OtherConst>& x, const $sentinel$& y);

    template<bool OtherConst>
      requires sized_sentinel_for<$zentinel$<Const>, $ziperator$<OtherConst>>
    friend constexpr range_difference_t<$maybe-const$<OtherConst, $InnerView$>>
      operator-(const $iterator$<OtherConst>& x, const $sentinel$& y);

    template<bool OtherConst>
      requires sized_sentinel_for<$zentinel$<Const>, $ziperator$<OtherConst>>
    friend constexpr range_difference_t<$maybe-const$<OtherConst, $InnerView$>>
      operator-(const $sentinel$& x, const $iterator$<OtherConst>& y);
  };
}
```
::: itemdecl

```cpp
constexpr explicit $sentinel$($zentinel$<Const> inner);
```

[#]{.pnum} _Effects_: Initializes `$inner_$` with `inner`.

```cpp
constexpr $sentinel$($sentinel$<!Const> i)
  requires Const && convertible_to<$zentinel$<false>, $zentinel$<Const>>;
```

[#]{.pnum} _Effects_: Initializes `$inner_$` with `std::move(i.$inner_$)`.

```cpp
template<bool OtherConst>
  requires sentinel_for<$zentinel$<Const>, $ziperator$<OtherConst>>
friend constexpr bool operator==(const $iterator$<OtherConst>& x, const $sentinel$& y);
```

[#]{.pnum} _Effects_: Equivalent to `return x.$inner_$ == y.$inner_$;`


```cpp
template<bool OtherConst>
  requires sized_sentinel_for<$zentinel$<Const>, $ziperator$<OtherConst>>
friend constexpr range_difference_t<$maybe-const$<OtherConst, $InnerView$>>
  operator-(const $iterator$<OtherConst>& x, const $sentinel$& y);

template<bool OtherConst>
  requires sized_sentinel_for<$zentinel$<Const>, $ziperator$<OtherConst>>
friend constexpr range_difference_t<$maybe-const$<OtherConst, $InnerView$>>
  operator-(const $sentinel$& x, const $iterator$<OtherConst>& y);
```
[#]{.pnum} _Effects_: Equivalent to `return x.$inner_$ - y.$inner_$;`

:::


## `adjacent`

Add the following subclause to [range.adaptors]{.sref}.

### 24.7.? Adjacent view [range.adjacent] {-}

#### 24.7.?.1 Overview [range.adjacent.overview] {-}

[#]{.pnum} `adjacent_view` takes a `view` and produces a `view` whose
_M_ <sup>th</sup> element is a tuple of references to the M <sup>th</sup> through
(_M_ + _N_ - 1)<sup>th</sup> elements of the original view. If the original
view has fewer than _N_ elements, the resulting view is empty.

[#]{.pnum} The name `views::adjacent<N>` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given a subexpression `E` and a constant expression `N`,
the expression `views::adjacent<N>(E)` is expression-equivalent to

- [#.#]{.pnum} `(void)E, $decay-copy$(views::empty<tuple<>>)` if `N` is equal to `0`,
- [#.#]{.pnum} otherwise, `adjacent_view<views::all_t<decltype((E))>, N>(E)`.

::: example

```cpp
vector v = {1, 2, 3, 4};

for (auto i : v | views::adjacent<2>) {
  cout << '(' << i.first << ', ' << i.second << ") "; // prints: (1, 2) (2, 3) (3, 4)
}

```
:::

[#]{.pnum} Define `$REPEAT$(T, N)` as a pack of _N_ types, each of which denotes the same type as `T`.

#### 24.7.?.2 Class template `adjacent_view` [range.adjacent.view] {-}

```cpp
namespace std::ranges {

template<forward_range V, size_t N>
  requires view<V> && (N > 0)
class adjacent_view : public view_interface<adjacent_view<V, N>>{
  V $base_$ = V();                     // exposition only

  template<bool> class $iterator$;     // exposition only
  template<bool> class $sentinel$;     // exposition only

  struct $as-sentinel${};              // exposition only

public:
  constexpr adjacent_view() = default;
  constexpr explicit adjacent_view(V base);

  constexpr auto begin() requires (!$simple-view$<V>) {
    return $iterator$<false>(ranges::begin($base_$), ranges::end($base_$));
  }

  constexpr auto begin() const requires range<const V> {
    return $iterator$<true>(ranges::begin($base_$), ranges::end($base_$));
  }

  constexpr auto end() requires (!$simple-view$<V> && !common_range<V>) {
    return $sentinel$<false>(ranges::end($base_$));
  }

  constexpr auto end() requires (!$simple-view$<V> && common_range<V>){
    return $iterator$<false>($as-sentinel${}, ranges::begin($base_$), ranges::end($base_$));
  }

  constexpr auto end() const requires range<const V> {
    return $sentinel$<true>(ranges::end($base_$));
  }

  constexpr auto end() const requires common_range<const V> {
    return $iterator$<true>($as-sentinel${}, ranges::begin($base_$), ranges::end($base_$));
  }

  constexpr auto size() requires sized_range<V>;
  constexpr auto size() const requires sized_range<const V>;
};

}
```

::: itemdecl

```cpp
constexpr explicit adjacent_view(V base);
```

[#]{.pnum} _Effects_: Initializes `$base_$` with `std::move(base)`.

```cpp
constexpr auto size() requires sized_range<V>;
constexpr auto size() const requires sized_range<const V>;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
auto sz = ranges::size($base_$);
sz -= std::min<decltype(sz)>(sz, N-1);
return sz;
```
:::
:::

#### 24.7.?.3 Class template `adjacent_view::$iterator$` [range.adjacent.iterator] {-}

```cpp
namespace std::ranges {
  template<forward_range V, size_t N>
    requires view<V> && (N > 0)
  template<bool Const>
  class adjacent_view<V, N>::$iterator$ {
    using $Base$ = $maybe-const$<Const, V>;                                             // exposition only
    array<iterator_t<$Base$>, N> $current_$ = array<iterator_t<$Base$>, N>();             // exposition only
    constexpr $iterator$(iterator_t<$Base$> first, sentinel_t<$Base$> last);              // exposition only
    constexpr $iterator$($as-sentinel$, iterator_t<$Base$> first, iterator_t<$Base$> last); // exposition only
  public:
    using iterator_category = input_iterator_tag;
    using iterator_concept  = $see below$;
    using value_type = $tuple-or-pair$<$REPEAT$(range_value_t<$Base$>, N)...>;
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

    friend constexpr auto iter_move(const $iterator$& i) noexcept($see below$);

    friend constexpr void iter_swap(const $iterator$& l, const $iterator$& r)
      noexcept($see below$)
      requires indirectly_swappable<iterator_t<$Base$>>;
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
constexpr $iterator$(iterator_t<$Base$> first, sentinel_t<$Base$> last);
```

[#]{.pnum} _Postconditions_: `$current_$[0] == first` is `true`, and
for every integer 1 &le; _i_ &lt; `N`,
`$current_$[$i$] == ranges::next($current_$[$i$-1], 1, last)` is `true`.

```cpp
constexpr $iterator$($as-sentinel$, iterator_t<$Base$> first, iterator_t<$Base$> last);
```

[#]{.pnum} _Postconditions_: If `$Base$` does not model `bidirectional_range`,
each element of `$current_$` is equal to `last`.
Otherwise, `$current_$[N-1] == last` is `true`, and
for every integer 0 &le; _i_ &lt; `(N - 1)`,
`$current_$[$i$] == ranges::prev($current_$[$i$+1], 1, first)` is `true`.

```cpp
constexpr $iterator$($iterator$<!Const> i)
  requires Const && (convertible_to<iterator_t<V>, iterator_t<$Base$>>;
```

[#]{.pnum} _Effects_: Initializes each element of `$current_$` with the corresponding element of `i.$current_$` as an xvalue.

```cpp
  constexpr auto operator*() const;
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return $tuple-transform$([](auto& i) -> decltype(auto) { return *i; }, $current_$);
```
:::

```cpp
constexpr $iterator$& operator++();
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  ranges::copy($current_$ | views::drop(1), $current_$.begin());
  ++$current_$.back();
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
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  ranges::copy_backward($current_$ | views::take(N - 1), $current_$.end());
  --$current_$.front();
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
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  for(auto& i : $current_$) { i += x; }
  return *this;
```
:::

```cpp
  constexpr $iterator$& operator-=(difference_type x)
    requires random_access_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  for(auto& i : $current_$) { i -= x; }
  return *this;
```
:::

```cpp
constexpr auto operator[](difference_type n) const
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return $tuple-transform$([&](auto& i) -> decltype(auto) { return i[n]; }, $current_$);
```
:::

```cpp
friend constexpr bool operator==(const $iterator$& x, const $iterator$& y);
```
[#]{.pnum} _Returns:_ `x.$current_$.back() == y.$current_$.back()`.

```cpp
friend constexpr bool operator<(const $iterator$& x, const $iterator$& y)
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Returns_: `x.$current_$.back() < y.$current_$.back()`

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

[#]{.pnum} _Returns_: `x.$current_$.back() <=> y.$current_$.back()`


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
[#]{.pnum} _Effects_: Equivalent to: `return x.$current_$.back() - y.$current_$.back()`.

```cpp
friend constexpr auto iter_move(const $iterator$& i) noexcept($see below$);
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return $tuple-transform$(ranges::iter_move, i.$current_$);
```
:::

[#]{.pnum} _Remarks:_ The expression within `noexcept` is equivalent to

::: bq
```cpp
  noexcept(ranges::iter_move(declval<iterator_t<$Base$> const&>())) &&
  is_nothrow_move_constructible_v<range_rvalue_reference_t<$Base$>>
```
:::

```cpp
friend constexpr void iter_swap(const $iterator$& l, const $iterator$& r)
  noexcept($see below$)
  requires indirectly_swappable<iterator_t<$Base$>>;
```
[#]{.pnum} _Preconditions:_ None of the iterators in `l.$current_$` is equal to an iterator in `r.$current_$`.

[#]{.pnum} _Effects_: For every integer 0 &le; _i_ &lt; `N`,
performs `ranges::iter_swap(l.$current_$[$i$], r.$current_$[$i$])`.

[#]{.pnum} _Remarks:_ The expression within `noexcept` is equivalent to:

::: bq
```cpp
  noexcept(ranges::iter_swap(declval<iterator_t<$Base$>>(), declval<iterator_t<$Base$>>()))
```
:::

:::

#### 24.7.?.4 Class template `adjacent_view::$sentinel$` [range.adjacent.sentinel] {-}

```cpp
namespace std::ranges {
  namespace std::ranges {
  template<forward_range V, size_t N>
    requires view<V> && (N > 0)
  template<bool Const>
  class adjacent_view<V, N>::$sentinel$ {
    using $Base$ = $maybe-const$<Const, V>;                     // exposition only
    sentinel_t<$Base$> $end_$ = sentinel_t<$Base$>();             // exposition only
    constexpr explicit $sentinel$(sentinel_t<$Base$> end);      // exposition only
  public:
    $sentinel$() = default;
    constexpr $sentinel$($sentinel$<!Const> i)
      requires Const && convertible_to<sentinel_t<V>, sentinel_t<$Base$>>;

    template<bool OtherConst>
      requires sentinel_for<sentinel_t<$Base$>, iterator_t<$maybe-const$<OtherConst, V>>>
    friend constexpr bool operator==(const $iterator$<OtherConst>& x, const $sentinel$& y);

    template<bool OtherConst>
      requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$maybe-const$<OtherConst, V>>>
    friend constexpr range_difference_t<$maybe-const$<OtherConst, V>>
      operator-(const $iterator$<OtherConst>& x, const $sentinel$& y);

    template<bool OtherConst>
      requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$maybe-const$<OtherConst, V>>>
    friend constexpr range_difference_t<$maybe-const$<OtherConst, V>>
      operator-(const $sentinel$& y, const $iterator$<OtherConst>& x);
  };
}
```
::: itemdecl

```cpp
constexpr explicit $sentinel$(sentinel_t<$Base$> end);
```

[#]{.pnum} _Effects_: Initializes `$end_$` with `end`.

```cpp
constexpr $sentinel$($sentinel$<!Const> i)
  requires Const && convertible_to<sentinel_t<V>, sentinel_t<$Base$>>;
```

[#]{.pnum} _Effects_: Initializes `$end_$` with `std::move(i.$end_$)`.

```cpp
template<bool OtherConst>
  requires sentinel_for<sentinel_t<$Base$>, iterator_t<$maybe-const$<OtherConst, V>>>
friend constexpr bool operator==(const $iterator$<OtherConst>& x, const $sentinel$& y);
```

[#]{.pnum} _Effects_: Equivalent to: `return x.$current_$.back() == y.$end_$;`.


```cpp
template<bool OtherConst>
  requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$maybe-const$<OtherConst, V>>>
friend constexpr range_difference_t<$maybe-const$<OtherConst, V>>
  operator-(const $iterator$<OtherConst>& x, const $sentinel$& y);
```
[#]{.pnum} _Effects_: Equivalent to: `return x.$current_$.back() - y.$end_$;`.

```cpp
template<bool OtherConst>
  requires sized_sentinel_for<sentinel_t<$Base$>, iterator_t<$maybe-const$<OtherConst, V>>>
friend constexpr range_difference_t<$maybe-const$<OtherConst, V>>
  operator-(const $sentinel$& y, const $iterator$<OtherConst>& x);
```
[#]{.pnum} _Effects_: Equivalent to: `return y.$end_$ - x.$current_$.back();`.

:::

## `adjacent_transform`


Add the following subclause to [range.adaptors]{.sref}.

### 24.7.? Adjacent transform view [range.adjacent.transform] {-}

#### 24.7.?.1 Overview [range.adjacent.transform.overview] {-}

[#]{.pnum} `adjacent_transform_view` takes an invocable object and a `view`
and produces a `view` whose _M <sup>th</sup>_ element is the result of applying
the invocable object to the _M_ <sup>th</sup> through (_M_ + _N_ - 1)<sup>th</sup>
elements of the original view. If the original view has fewer than _N_ elements,
the resulting view is empty.

[#]{.pnum} The name `views::adjacent_transform<N>` denotes a range adaptor object
([range.adaptor.object]{.sref}). Given subexpressions `E` and `F`,

- [#.#]{.pnum} if `N` is equal to 0, `views::adjacent_transform<N>(E, F)` is expression-equivalent to `(void)E, views::zip_transform(F)`, except that the evaluations of `E` and `F` are indeterminately sequenced.
- [#.#]{.pnum} Otherwise, the expression `views::adjacent_transform<N>(E, F)` is expression-equivalent to `adjacent_transform_view<views::all_t<decltype((E))>, decay_t<F>, N>(E, F)`.

::: example

```cpp
vector v = {1, 2, 3, 4};

for (auto i : v | views::adjacent_transform<2>(std::multiplies())) {
  cout << i << ' '; // prints: 2 6 12
}

```
:::

#### 24.7.?.2 Class template `adjacent_transform_view` [range.adjacent.transform.view] {-}

```cpp
namespace std::ranges {
  template<forward_range V, copy_constructible F, size_t N>
   requires view<V> && (N > 0) && is_object_v<F> &&
            regular_invocable<F&, $REPEAT$(range_reference_t<V>, N)...> &&
            $can-reference$<invoke_result_t<F&, $REPEAT$(range_reference_t<V>, N)...>>
  class adjacent_transform_view : public view_interface<adjacent_transform_view<V, F, N>> {
  $semiregular-box$<F> $fun_$;                  // exposition only
  adjacent_view<V, N> $inner_$;               // exposition only

  using $InnerView$ = adjacent_view<V, N>;    // exposition only
  template<bool Const>
  using $inner-iterator$ = iterator_t<$maybe-const$<Const, $InnerView$>>;  // exposition only
  template<bool Const>
  using $inner-sentinel$ = sentinel_t<$maybe-const$<Const, $InnerView$>>;  // exposition only

  template<bool> class $iterator$;         // exposition only
  template<bool> class $sentinel$;         // exposition only

public:
  constexpr adjacent_transform_view() = default;

  constexpr explicit adjacent_transform_view(V base, F fun);

  constexpr auto begin() {
    return $iterator$<false>(*this, $inner_$.begin());
  }

  constexpr auto begin() const
    requires range<const $InnerView$> &&
             regular_invocable<const F&, $REPEAT$(range_reference_t<const V>, N)...>
  {
    return $iterator$<true>(*this, $inner_$.begin());
  }

  constexpr auto end() {
    return $sentinel$<false>($inner_$.end());
  }

  constexpr auto end() requires common_range<$InnerView$> {
    return $iterator$<false>(*this, $inner_$.end());
  }

  constexpr auto end() const
    requires range<const $InnerView$> &&
             regular_invocable<const F&, $REPEAT$(range_reference_t<const V>, N)...>
  {
    return $sentinel$<true>($inner_$.end());
  }

  constexpr auto end() const
    requires common_range<const $InnerView$> &&
             regular_invocable<const F&, $REPEAT$(range_reference_t<const V>, N)...>
  {
    return $iterator$<true>(*this, $inner_$.end());
  }

  constexpr auto size() requires sized_range<$InnerView$> {
    return $inner_$.size();
  }

  constexpr auto size() const requires sized_range<const $InnerView$> {
    return $inner_$.size();
  }
};

}
```

::: itemdecl

```cpp
constexpr explicit adjacent_transform_view(V base, F fun);
```

[#]{.pnum} _Effects_: Initializes `$fun_$` with `std::move(fun)` and
`$inner_$` with `std::move(base)`.

:::

#### 24.7.?.3 Class template `adjacent_transform_view::$iterator$` [range.adjacent.transform.iterator] {-}

```cpp
namespace std::ranges {
  template<forward_range V, copy_constructible F, size_t N>
    requires view<V> && (N > 0) && is_object_v<F> &&
             regular_invocable<F&, $REPEAT$(range_reference_t<V>, N)...> &&
             $can-reference$<invoke_result_t<F&, $REPEAT$(range_reference_t<V>, N)...>>
  template<bool Const>
  class adjacent_transform_view<F, V...>::$iterator$ {
    using $Parent$ = $maybe-const$<Const, adjacent_transform_view>;      // exposition only
    using $Base$ = $maybe-const$<Const, V>;                              // exposition only
    $Parent$* $parent_$ = nullptr;                                       // exposition only
    $inner-iterator$<Const> $inner_$ = $inner-iterator$<Const>();          // exposition only

    constexpr $iterator$($Parent$& parent, $inner-iterator$<Const> inner); // exposition only

  public:
    using iterator_category = $see below$;
    using iterator_concept  = typename $inner-iterator$<Const>::iterator_concept;
    using value_type =
      remove_cvref_t<invoke_result_t<$maybe-const$<Const, F>&, $REPEAT$(range_reference_t<$Base$>, N)...>>;
    using difference_type = range_difference_t<$Base$>;

    $iterator$() = default;
    constexpr $iterator$($iterator$<!Const> i)
      requires Const && convertible_to<$inner-iterator$<false>, $inner-iterator$<Const>>;

    constexpr decltype(auto) operator*() const noexcept($see below$);
    constexpr $iterator$& operator++();
    constexpr $iterator$ operator++(int);

    constexpr $iterator$& operator--() requires bidirectional_range<$Base$>;
    constexpr $iterator$ operator--(int) requires bidirectional_range<$Base$>;

    constexpr $iterator$& operator+=(difference_type x) requires random_access_range<$Base$>;
    constexpr $iterator$& operator-=(difference_type x) requires random_access_range<$Base$>;

    constexpr decltype(auto) operator[](difference_type n) const requires random_access_range<$Base$>;

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
      requires random_access_range<$Base$> && three_way_comparable<$inner-iterator$<Const>>;

    friend constexpr $iterator$ operator+(const $iterator$& i, difference_type n)
      requires random_access_range<$Base$>;
    friend constexpr $iterator$ operator+(difference_type n, const $iterator$& i)
      requires random_access_range<$Base$>;
    friend constexpr $iterator$ operator-(const $iterator$& i, difference_type n)
      requires random_access_range<$Base$>;
    friend constexpr difference_type operator-(const $iterator$& x, const $iterator$& y)
      requires sized_sentinel_for<$inner-iterator$<Const>, $inner-iterator$<Const>>;
  };
}
```

[#]{.pnum} The member _typedef-name_ `$iterator$::iterator_category` is defined as follows:

- If `invoke_result_t<$maybe-const$<Const, F>&, $REPEAT$(range_reference_t<$Base$>, N)...>` is not an lvalue reference,
  `iterator_category` denotes `input_iterator_tag`.
- Otherwise, let `C` denote the type `iterator_traits<iterator_t<$Base$>>::iterator_category`.
  - If `derived_from<C, random_access_iterator_tag>` is `true`, `iterator_category` denotes `random_access_iterator_tag`;
  - Otherwise, if `derived_from<C, bidirectional_iterator_tag>` is `true`, `iterator_category` denotes `bidirectional_iterator_tag`;
  - Otherwise, if `derived_from<C, forward_iterator_tag>` is `true`, `iterator_category` denotes `forward_iterator_tag`;
  - Otherwise, `iterator_category` denotes `input_iterator_tag`.


::: itemdecl

```cpp
constexpr $iterator$($Parent$& parent, $inner-iterator$<Const> inner);
```

[#]{.pnum} _Effects_: Initializes `$parent_$` with `addressof(parent)` and `$inner_$` with `std::move(inner)`.

```cpp
constexpr $iterator$($iterator$<!Const> i)
  requires Const && convertible_to<$inner-iterator$<false>, $inner-iterator$<Const>>;
```

[#]{.pnum} _Effects_: Initializes `$parent_$` with `i.$parent_$` and `$inner_$` with `std::move(i.$inner_$)`.

```cpp
constexpr decltype(auto) operator*() const noexcept($see below$);
```

[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return apply([&](const auto&... iters) -> decltype(auto) {
    return invoke(*$parent_$->$fun_$, *iters...);
  }, $inner_$.$current_$);
```
:::

[#]{.pnum} _Remarks:_
Let `Is` be the pack `0, 1, ..., (N-1)`.
The expression within `noexcept` is equivalent to
`noexcept(invoke(*$parent_$->$fun_$, *std::get<Is>($inner_$.$current_$)...))`.

```cpp
constexpr $iterator$& operator++();
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  ++$inner_$;
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
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  --$inner_$;
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
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  $inner_$ += x;
  return *this;
```
:::

```cpp
constexpr $iterator$& operator-=(difference_type x)
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  $inner_$ -= x;
  return *this;
```
:::

```cpp
constexpr decltype(auto) operator[](difference_type n) const
  requires random_access_range<$Base$>;
```
[#]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
  return apply([&](const auto&... iters) -> decltype(auto) {
    return invoke(*$parent_$->$fun_$, iters[n]...);
  }, $inner_$.$current_$);
```
:::

```cpp
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
  requires random_access_range<$Base$> && three_way_comparable<$inner-iterator$<Const>>;
```
[#]{.pnum} Let _`op`_ be the operator.

[#]{.pnum} _Effects_: Equivalent to: `return x.$inner_$ $op$ y.$inner_$; `


```cpp
friend constexpr $iterator$ operator+(const $iterator$& i, difference_type n)
  requires random_access_range<$Base$>;
friend constexpr $iterator$ operator+(difference_type n, const $iterator$& i)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return $iterator$(*i.$parent_$, i.$inner_$ + n);`

```cpp
friend constexpr $iterator$ operator-(const $iterator$& i, difference_type n)
  requires random_access_range<$Base$>;
```

[#]{.pnum} _Effects_: Equivalent to: `return $iterator$(*i.$parent_$, i.$inner_$ - n);`

```cpp
friend constexpr difference_type operator-(const $iterator$& x, const $iterator$& y)
  requires sized_sentinel_for<$inner-iterator$<Const>, $inner-iterator$<Const>>;
```

[#]{.pnum} _Effects_: Equivalent to: `return x.$inner_$ - y.$inner_$;`

:::

#### 24.7.?.4 Class template `adjacent_transform_view::$sentinel$` [range.adjacent.transform.sentinel] {-}

```cpp
namespace std::ranges {
  template<forward_range V, copy_constructible F, size_t N>
    requires view<V> && (N > 0) && is_object_v<F> &&
             regular_invocable<F&, $REPEAT$(range_reference_t<V>, N)...> &&
             $can-reference$<invoke_result_t<F&, $REPEAT$(range_reference_t<V>, N)...>>
  template<bool Const>
  class adjacent_transform_view<V, F, N>::$sentinel$ {
    $inner-sentinel$<Const> $inner_$;                              // exposition only
    constexpr explicit $sentinel$($inner-sentinel$<Const> inner);  // exposition only
  public:
    $sentinel$() = default;
    constexpr $sentinel$($sentinel$<!Const> i)
      requires Const && convertible_to<$inner-sentinel$<false>, $inner-sentinel$<Const>>;

    template<bool OtherConst>
      requires sentinel_for<$inner-sentinel$<Const>, $inner-iterator$<OtherConst>>
    friend constexpr bool operator==(const $iterator$<OtherConst>& x, const $sentinel$& y);

    template<bool OtherConst>
      requires sized_sentinel_for<$inner-sentinel$<Const>, $inner-iterator$<OtherConst>>
    friend constexpr range_difference_t<$maybe-const$<OtherConst, $InnerView$>>
      operator-(const $iterator$<OtherConst>& x, const $sentinel$& y);

    template<bool OtherConst>
      requires sized_sentinel_for<$inner-sentinel$<Const>, $inner-iterator$<OtherConst>>
    friend constexpr range_difference_t<$maybe-const$<OtherConst, $InnerView$>>
      operator-(const $sentinel$& x, const $iterator$<OtherConst>& y);
  };
}
```
::: itemdecl

```cpp
constexpr explicit $sentinel$($inner-sentinel$<Const> inner);
```

[#]{.pnum} _Effects_: Initializes `$inner_$` with `inner`.

```cpp
constexpr $sentinel$($sentinel$<!Const> i)
  requires Const && convertible_to<$inner-sentinel$<false>, $inner-sentinel$<Const>>;
```

[#]{.pnum} _Effects_: Initializes `$inner_$` with `std::move(i.$inner_$)`.

```cpp
template<bool OtherConst>
  requires sentinel_for<$inner-sentinel$<Const>, $inner-iterator$<OtherConst>>
friend constexpr bool operator==(const $iterator$<OtherConst>& x, const $sentinel$& y);
```

[#]{.pnum} _Effects_: Equivalent to `return x.$inner_$ == y.$inner_$;`


```cpp
template<bool OtherConst>
  requires sized_sentinel_for<$inner-sentinel$<Const>, $inner-iterator$<OtherConst>>
friend constexpr range_difference_t<$maybe-const$<OtherConst, $InnerView$>>
  operator-(const $iterator$<OtherConst>& x, const $sentinel$& y);

template<bool OtherConst>
  requires sized_sentinel_for<$inner-sentinel$<Const>, $inner-iterator$<OtherConst>>
friend constexpr range_difference_t<$maybe-const$<OtherConst, $InnerView$>>
  operator-(const $sentinel$& x, const $iterator$<OtherConst>& y);
```
[#]{.pnum} _Effects_: Equivalent to `return x.$inner_$ - y.$inner_$;`

:::

## Feature-test macro

Add the following macro definition to [version.syn]{.sref}, header `<version>`
synopsis, with the value selected by the editor to reflect the date of adoption
of this paper:

```cpp
#define __cpp_lib_ranges_zip 20XXXXL // also in <ranges>, <tuple>, <utility>
```

# Acknowledgements

Thanks to Barry Revzin for implementing this entire paper from spec and finding
several wording issues in the process.

---
references:
    - id: range-v3.1592
      citation-label: range-v3.1592
      title: "`zip` does not satisfy the semantic requirements of `bidirectional_iterator` when the ranges have different lengths"
      author:
        - family: kitegi
      issued:
        year: 2020
      URL: https://github.com/ericniebler/range-v3/issues/1592
    - id: range-v3.704
      citation-label: range-v3.704
      title: "Demand-driven view strength weakening"
      author:
        - family: Eric Niebler
      issued:
        year: 2017
      URL: https://github.com/ericniebler/range-v3/issues/704
---
