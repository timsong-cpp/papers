---
title: "`elements_view` needs its own `sentinel`"
document: D1994R0
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
and so should `elements_view`. More generally, if a range adaptor has a custom iterator, it should probably also have a custom sentinel.
The rationale is that the underlying range's sentinel could encode a generic predicate that is equally meaningful
for the adapted range, leading to an ambiguity.

For example, consider a sentinel that checks whether the second element is zero (i.e., `i == s` is `std::get<1>(*i) == 0`)
and a range of `pair<pair<int, int>, int>` using this sentinel that is then adapted by `views::keys`:
does the comparison with the sentinel check the second element of the original range,
or the second element of the adapted range?

A custom sentinel is needed to avoid this ambiguity.

# Wording
This wording is relative to [@N4835].

Edit [range.elements.view]{.sref}, class template `elements_view` synopsis, as indicated:

::: bq

```diff
 namespace std::ranges {
    @_[...]_@

   template<input_range R, size_t N>
     requires view<R> && has-tuple-element<range_value_t<R>, N> &&
       has-tuple-element<remove_reference_t<range_reference_t<R>>, N>
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
     template<bool> struct iterator;                     // exposition only
+    template<bool> struct sentinel;                     // exposition only
     R base_ = R();                                      // exposition only
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
   class elements_view<R, N>::iterator { // exposition only
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
