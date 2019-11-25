---
title: "`elements_view` needs its own `sentinel`"
document: P1994R0
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

`elements_view` needs its own `sentinel` type.

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
This wording is relative to [@N4835].

[These changes, including the overload set for `end`, match the specification of `transform_view`.
This seems appropriate since `elements_view` is just a special kind of transform.]{.draftnote}

Edit [range.elements.view]{.sref}, class template `elements_view` synopsis, as indicated:

::: bq

```diff
 namespace std::ranges {
    @_[...]_@

   template<input_range R, size_t N>
     requires view<R> && @_has-tuple-element_@<range_value_t<R>, N> &&
       @_has-tuple-element_@<remove_reference_t<range_reference_t<R>>, N>
   class elements_view : public view_interface<elements_view<R, N>> {
   public:
     @_[...]_@

+    constexpr auto end()
+    { return sentinel<false>{ranges::end(base_)}; }
+
+    constexpr auto end() requires common_range<R>
+    { return iterator<false>{ranges::end(base_)}; }
+
+    constexpr auto end() const
+      requires range<const R>
+    { return sentinel<true>{ranges::end(base_)}; }
+
+    constexpr auto end() const
+      requires common_range<const R>
+    { return iterator<true>{ranges::end(base_)}; }

-    constexpr auto end() requires (!@_simple-view_@<R>)
-    { return ranges::end(base_); }

-    constexpr auto end() const requires @_simple-view_@<R>
-    { return ranges::end(base_); }

     @_[...]_@

   private:
     template<bool> struct iterator;                     // @_exposition only_@
+    template<bool> struct sentinel;                     // @_exposition only_@
     R base_ = R();                                      // @_exposition only_@
   };
 }
```
:::

Edit [range.elements.iterator]{.sref}, class template `elements_view<R, N>::iterator` synopsis, as indicated:

::: bq

```diff
 namespace std::ranges {
   template<class R, size_t N>
   template<bool Const>
   class elements_view<R, N>::iterator { // @_exposition only_@
   @_[...]_@

   public:
     @_[...]_@

-    friend constexpr bool operator==(const iterator& x, const sentinel_t<base_t>& y);

     @_[...]_@

-    friend constexpr difference_type
-      operator-(const iterator<Const>& x, const sentinel_t<base_t>& y)
-        requires sized_sentinel_for<sentinel_t<base_t>, iterator_t<base_t>>;
-    friend constexpr difference_type
-      operator-(const sentinel_t<base_t>& x, const iterator<Const>& y)
-        requires sized_sentinel_for<sentinel_t<base_t>, iterator_t<base_t>>;
   };
 }
```
:::

Delete the specification of these operators in [range.elements.iterator]{.sref} (p12, 22 and 23):

::: rm

> ```c++
> friend constexpr bool operator==(const iterator& x, const sentinel_t<base_t>& y);
> ```
>
> [12]{.pnum} _Effects:_ Equivalent to: `return x.current_ == y;`

:::

> ...

::: rm

> ```c++
> friend constexpr difference_type
>   operator-(const iterator<Const>& x, const sentinel_t<base_t>& y)
>     requires sized_sentinel_for<sentinel_t<base_t>, iterator_t<base_t>>;
> ```
> [22]{.pnum} _Effects_: Equivalent to: `return x.current_­ - y;`
>
> ```c++
> friend constexpr difference_type
>   operator-(const sentinel_t<base_t>& x, const iterator<Const>& y)
>     requires sized_sentinel_for<sentinel_t<base_t>, iterator_t<base_t>>;
> ```
>
> [23]{.pnum} _Effects_: Equivalent to: `return -(y - x);`

:::

Add a new subclause after [range.elements.iterator]{.sref}:

::: add

#### ?.?.?.? Class template `elements_view::sentinel` [ranges.element.sentinel] {-}

```c++
namespace std::ranges {
  template<class R, size_t N>
  template<bool Const>
  class elements_view<R, N>::sentinel {               // @_exposition only_@
  private:
    using base_t = conditional_t<Const, const R, R>;  // @_exposition only_@
    sentinel_t<base_t> end_ = sentinel_t<base_t>();   // @_exposition only_@
  public:
    sentinel() = default;
    constexpr explicit sentinel(sentinel_t<base_t> end);
    constexpr sentinel(sentinel<!Const> other)
      requires Const && convertible_to<sentinel_t<R>, sentinel_t<base_t>>;

    constexpr sentinel_t<base_t> base() const;

    friend constexpr bool operator==(const iterator<Const>& x, const sentinel& y);

    friend constexpr range_difference_t<base_t>
      operator-(const iterator<Const>& x, const sentinel& y)
        requires sized_sentinel_for<sentinel_t<base_t>, iterator_t<base_t>>;

    friend constexpr range_difference_t<base_t>
      operator-(const sentinel<Const>& x, const iterator& y)
        requires sized_sentinel_for<sentinel_t<base_t>, iterator_t<base_t>>;
  };
}
```

> ```c++
> constexpr explicit sentinel(sentinel_t<base_t> end);
> ```
>
> [1]{.pnum} _Effects:_ Initializes `end_` with `end`.

> ```c++
> constexpr sentinel(sentinel<!Const> other)
>   requires Const && convertible_to<sentinel_t<R>, sentinel_t<base_t>>;
> ```
>
> [2]{.pnum} _Effects:_ Initializes `end_` with `std::move(other.end_)`.
>
> ```c++
> constexpr sentinel_t<base_t> base() const;
> ```
> [3]{.pnum} _Effects:_ Equivalent to: `return end_;`
>
> ```c++
> friend constexpr bool operator==(const iterator<Const>& x, const sentinel& y);
> ```
> [4]{.pnum} _Effects:_ Equivalent to: `return x.current_ == y.end_;`
>
> ```c++
> friend constexpr range_difference_t<base_t>
>   operator-(const iterator<Const>& x, const sentinel& y)
>     requires sized_sentinel_for<sentinel_t<base_t>, iterator_t<base_t>>;
> ```

> [5]{.pnum} _Effects:_ Equivalent to: `return x.current_ - y.end_;`
>
> ```c++
> friend constexpr range_difference_t<base_t>
>   operator-(const sentinel<Const>& x, const iterator& y)
>     requires sized_sentinel_for<sentinel_t<base_t>, iterator_t<base_t>>;
> ```
> [6]{.pnum} _Effects:_ Equivalent to: `return x.end_ - y.current_;`

:::
