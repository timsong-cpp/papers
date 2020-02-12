---
title: "`elements_view` needs its own `sentinel`"
document: D1994R1
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
  - name: Christopher Di Bella
    email: <cjdb.ns@gmail.com>
toc: false
---

# Abstract

`elements_view` needs its own `sentinel` type. This paper resolves [@LWG3386].

# Revision history

- R1: Incorporate LWG review feedback in Prague. Rebased onto [@N4849].

# Discussion

`elements_view` is effectively a specialized version of `transform_view`; the latter has a custom `sentinel` type,
and so should `elements_view`.

More generally, if a range adaptor has a custom iterator, it should probably also have a custom sentinel.
The rationale is that the underlying range's sentinel could encode a generic predicate that is equally meaningful
for the adapted range, leading to an ambiguity.

For example, consider:

```c++

struct S { // sentinel that checks if the second element is zero
  friend bool operator==(input_iterator auto const& i, S) requires /* ... */
  { return get<1>(*i) == 0; }
};

void algo(input_range auto&& r) requires /* ... */ {
  for (auto&& something : subrange{ranges::begin(r), S{}})
  {
    /* do something */
  }
}

using P = pair<pair<char, int>, long>;
vector<P> something = /* ... */;

subrange r{something.begin(), S{}};

algo(r | view::keys);                 // checks the long, effectively iterating over r completely
algo(r | view::transform(&P::first)); // checks the int and stops at the first zero
```

`algo` is trying to use the sentinel `S` to stop at the first element `e` for which `get<1>(e)` is zero,
and it works correctly for all ranges of `pair<char, int>` ... except things like `r | view::keys`. In the
latter case, `ranges::begin(r | view::keys) == S{}` calls `elements_view::iterator`'s `operator==`
instead, which compares the _underlying range's_ iterator against the sentinel. In the above example,
this means that we check the `long` instead of the `int`, and effectively iterate over the entire range.

A custom sentinel is needed to avoid this problem. `elements_view` is the only adaptor in the current WP
that has a custom iterator but not a custom sentinel.

# Wording
This wording is relative to [@N4849].

[These changes, including the overload set for `end`, match the specification of `transform_view`.
This seems appropriate since `elements_view` is just a special kind of transform.]{.draftnote}

Edit [range.elements.view]{.sref}, class template `elements_view` synopsis, as indicated:

::: bq

```diff
 namespace std::ranges {
    @_[...]_@

   template<input_range V, size_t N>
     requires view<V> && @_has-tuple-element_@<range_value_t<V>, N> &&
       @_has-tuple-element_@<remove_reference_t<range_reference_t<V>>, N>
   class elements_view : public view_interface<elements_view<V, N>> {
   public:
     @_[...]_@

+    constexpr auto end()
+    { return @_sentinel_@<false>{ranges::end(@_base\__@)}; }
+
+    constexpr auto end() requires common_range<V>
+    { return @_iterator_@<false>{ranges::end(@_base\__@)}; }
+
+    constexpr auto end() const
+      requires range<const V>
+    { return @_sentinel_@<true>{ranges::end(@_base\__@)}; }
+
+    constexpr auto end() const
+      requires common_range<const V>
+    { return @_iterator_@<true>{ranges::end(@_base\__@)}; }

-    constexpr auto end() requires (!@_simple-view_@<V>)
-    { return ranges::end(@_base\__@); }

-    constexpr auto end() const requires @_simple-view_@<V>
-    { return ranges::end(@_base\__@); }

     @_[...]_@

   private:
     template<bool> struct @_iterator_@;                     // @_exposition only_@
+    template<bool> struct @_sentinel_@;                     // @_exposition only_@
     V @_base\__@ = V();                                      // @_exposition only_@
   };
 }
```
:::

Edit [range.elements.iterator]{.sref}, class template <code>elements_view&lt;V, N>::<i>iterator</i></code> synopsis, as indicated:

::: bq

```diff
 namespace std::ranges {
   template<class V, size_t N>
   template<bool Const>
   class elements_view<V, N>::@_iterator_@ { // @_exposition only_@
   @_[...]_@

   public:
     @_[...]_@

-    friend constexpr bool operator==(const @_iterator_@& x, const sentinel_t<@_base-t_@>& y);

     @_[...]_@

-    friend constexpr difference_type
-      operator-(const @_iterator_@<Const>& x, const sentinel_t<@_base-t_@>& y)
-        requires sized_sentinel_for<sentinel_t<@_base-t_@>, iterator_t<@_base-t_@>>;
-    friend constexpr difference_type
-      operator-(const @_iterator_@<@_base-t_@>& x, const iterator<Const>& y)
-        requires sized_sentinel_for<sentinel_t<@_base-t_@>, iterator_t<@_base-t_@>>;
   };
 }
```
:::

Delete the specification of these operators in [range.elements.iterator]{.sref} (p13, 23 and 24):

::: rm

> ```c++
> friend constexpr bool operator==(const @_iterator_@& x, const sentinel_t<@_base-t_@>& y);
> ```
>
> [13]{.pnum} _Effects:_ Equivalent to: `return x.current_ == y;`

:::

> ...

::: rm

> ```c++
> friend constexpr difference_type
>   operator-(const @_iterator_@<Const>& x, const sentinel_t<@_base-t_@>& y)
>     requires sized_sentinel_for<sentinel_t<@_base-t_@>, iterator_t<@_base-t_@>>;
> ```
> [23]{.pnum} _Effects_: Equivalent to: `return x.current_­ - y;`
>
> ```c++
> friend constexpr difference_type
>   operator-(const sentinel_t<@_base-t_@>& x, const @_iterator_@<Const>& y)
>     requires sized_sentinel_for<sentinel_t<@_base-t_@>, iterator_t<@_base-t_@>>;
> ```
>
> [24]{.pnum} _Effects_: Equivalent to: `return -(y - x);`

:::

Add a new subclause after [range.elements.iterator]{.sref}:

::: add

#### ?.?.?.? Class template <code>elements_view::<i>sentinel</i></code> [ranges.elements.sentinel] {-}

```c++
namespace std::ranges {
  template<class V, size_t N>
  template<bool Const>
  class elements_view<V, N>::@_sentinel_@ {               // @_exposition only_@
  private:
    using @_Base_@ = conditional_t<Const, const V, V>;    // @_exposition only_@
    sentinel_t<@_Base_@> @_end\__@ = sentinel_t<@_Base_@>();       // @_exposition only_@
  public:
    @_sentinel_@() = default;
    constexpr explicit @_sentinel_@(sentinel_t<@_Base_@> end);
    constexpr @_sentinel_@(@_sentinel_@<!Const> other)
      requires Const && convertible_to<sentinel_t<V>, sentinel_t<@_Base_@>>;

    constexpr sentinel_t<@_Base_@> base() const;

    friend constexpr bool operator==(const @_iterator_@<Const>& x, const @_sentinel_@& y);

    friend constexpr range_difference_t<@_Base_@>
      operator-(const @_iterator_@<Const>& x, const @_sentinel_@& y)
        requires sized_sentinel_for<sentinel_t<@_Base_@>, iterator_t<@_Base_@>>;

    friend constexpr range_difference_t<@_Base_@>
      operator-(const @_sentinel_@& x, const @_iterator_@<Const>& y)
        requires sized_sentinel_for<sentinel_t<@_Base_@>, iterator_t<@_Base_@>>;
  };
}
```

> ```c++
> constexpr explicit @_sentinel_@(sentinel_t<@_Base_@> end);
> ```
>
> [1]{.pnum} _Effects:_ Initializes _`end_`_ with `end`.

> ```c++
> constexpr @_sentinel_@(@_sentinel_@<!Const> other)
>   requires Const && convertible_to<sentinel_t<V>, sentinel_t<@_Base_@>>;
> ```
>
> [2]{.pnum} _Effects:_ Initializes _`end_`_ with <code>std::move(other.<i>end_</i>)</code>.
>
> ```c++
> constexpr sentinel_t<@_Base_@> base() const;
> ```
> [3]{.pnum} _Effects:_ Equivalent to: <code>return <i>end_</i>;</code>
>
> ```c++
> friend constexpr bool operator==(const @_iterator_@<Const>& x, const @_sentinel_@& y);
> ```
> [4]{.pnum} _Effects:_ Equivalent to: <code>return x.<i>current_</i> == y.<i>end_</i>;</code>
>
> ```c++
> friend constexpr range_difference_t<@_Base_@>
>   operator-(const @_iterator_@<Const>& x, const @_sentinel_@& y)
>     requires sized_sentinel_for<sentinel_t<@_Base_@>, iterator_t<@_Base_@>>;
> ```

> [5]{.pnum} _Effects:_ Equivalent to: <code>return x.<i>current_</i> - y.<i>end_</i>;</code>
>
> ```c++
> friend constexpr range_difference_t<@_Base_@>
>   operator-(const @_sentinel_@& x, const @_iterator_@<Const>& y)
>     requires sized_sentinel_for<sentinel_t<@_Base_@>, iterator_t<@_Base_@>>;
> ```
> [6]{.pnum} _Effects:_ Equivalent to: <code>return x.<i>end_</i> - y.<i>current_</i>;</code>

:::
