---
title: Wording for GB301, US296, US292, US291, and US283 
document: P1983R0
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Introduction

This paper provides combined wording for NB comments GB301, US296, US292, US291, and US283,
all minor Ranges issues. It also resolves [LWG issue 3278](https://wg21.link/LWG3278).

# Wording
This wording is relative to [@N4835].

## [GB301](https://github.com/cplusplus/nbballot/issues/297) Add `filter_view::pred()` accessor

Edit [range.filter.view]{.wg21}, class template `filter_view` synopsis, as indicated:

::: bq

```diff
 namespace std::ranges {
   template<input_range V, indirect_unary_predicate<iterator_t<V>> Pred>
     requires view<V> && is_object_v<Pred>
   class filter_view : public view_interface<filter_view<V, Pred>> {
     @_[...]_@
   public:
     filter_view() = default;
     constexpr filter_view(V base, Pred pred);
     template<input_range R>
       requires viewable_range<R> && constructible_from<V, all_view<R>>
     constexpr filter_view(R&& r, Pred pred);

     constexpr V base() const;
+    constexpr const Pred& pred() const;

     @_[...]_@
   };

   template<class R, class Pred>
     filter_view(R&&, Pred) -> filter_view<all_view<R>, Pred>;
 }
```
:::

In [range.filter.view]{.wg21}, insert the following after p3:

::: add

> ```c++
> constexpr const Pred& pred() const;
> ```
> 
> [?]{.pnum} _Effects_: Equivalent to: `return *pred_;`
:::

## [US296](https://github.com/cplusplus/nbballot/issues/292) Converting constructor for `split_view::outer_iterator` is slightly wrong

[LWG was not convinced that the constructor was wrong, but nonetheless agreed to 
 change this for consistency with the rest of the Clause.]{.draftnote}

Edit [range.split.outer]{.wg21}, class template `split_view::outer_iterator` synopsis, as indicated:

::: bq

```diff
 namespace std::ranges {
   template<class V, class Pattern>
   template<bool Const>
   struct split_view<V, Pattern>::outer_iterator {
  
   @_[...]_@

     outer_iterator() = default;
     constexpr explicit outer_iterator(Parent& parent)
       requires (!forward_range<Base>);
     constexpr outer_iterator(Parent& parent, iterator_t<Base> current)
       requires forward_range<Base>;
     constexpr outer_iterator(outer_iterator<!Const> i)
-      requires Const && convertible_to<iterator_t<V>, iterator_t<@[const V]{.diffdel}@>>;
+      requires Const && convertible_to<iterator_t<V>, iterator_t<@[Base]{.diffins}@>>;

     constexpr value_type operator*() const;

     constexpr outer_iterator& operator++();
     constexpr decltype(auto) operator++(int) {
       if constexpr (forward_range<Base>) {
         auto tmp = *this;
         ++*this;
         return tmp;
       } else
         ++*this;
     }

     friend constexpr bool operator==(const outer_iterator& x, const outer_iterator& y)
       requires forward_range<Base>;

     friend constexpr bool operator==(const outer_iterator& x, default_sentinel_t);
   };
 }
```
:::

Edit [range.split.outer]{.wg21} before p4 as indicated:

:::bq

```diff
 constexpr outer_iterator(outer_iterator<!Const> i)
-  requires Const && convertible_to<iterator_t<V>, iterator_t<@[const V]{.diffdel}@>>;
+  requires Const && convertible_to<iterator_t<V>, iterator_t<@[Base]{.diffins}@>>;
```

[4]{.pnum} _Effects:_ Initializes `parent_`­ with `i.parent_`­ and `current_`­ with `std​::​move(i.current_­)`.

:::

## [US292](https://github.com/cplusplus/nbballot/issues/288) Incorrect constructor for `join_view::iterator`

Edit [range.join.iterator]{.wg21},  class template `join_­view​::​iterator` synopsis, as indicated:

:::bq
```diff
 namespace std::ranges {
 template<class V>
   template<bool Const>
   struct join_view<V>::iterator {

   @_[...]_@

     iterator() = default;
-    constexpr iterator(Parent& parent, iterator_t<@[V]{.diffdel}@> outer);
+    constexpr iterator(Parent& parent, iterator_t<@[Base]{.diffins}@> outer);
     constexpr iterator(iterator<!Const> i)
       requires Const &&
                convertible_to<iterator_t<V>, iterator_t<Base>> &&
                convertible_to<iterator_t<InnerRng>,
                               iterator_t<range_reference_t<Base>>>;

   @_[...]_@

   };
 }
```
:::

Edit [range.join.iterator]{.wg21} before p6 as indicated:

:::bq
```diff
-    constexpr iterator(Parent& parent, iterator_t<@[V]{.diffdel}@> outer)
+    constexpr iterator(Parent& parent, iterator_t<@[Base]{.diffins}@> outer)@[;]{.diffins}@
```
[6]{.pnum} _Effects_: Initializes `outer_­` with `outer` and `parent_­` with `addressof(parent)`; then calls `satisfy()`.

:::

## [US291](https://github.com/cplusplus/nbballot/issues/287) `join_view::begin` requires mutable data

Edit [range.join.view]{.wg21} as indicated:

::: bq

```diff
 namespace std::ranges {
   template<input_range V>
     requires view<V> && input_range<range_reference_t<V>> &&
              (is_reference_v<range_reference_t<V>> ||
               view<range_value_t<V>>)
   class join_view : public view_interface<join_view<V>> {

   @_[...]_@

   public:

     @_[...]_@

     constexpr auto begin() {
+      constexpr bool use_const = @_simple-view_@<V> && 
+        is_reference_v<range_reference_t<V>>;
-      return iterator<@[_simple-view_<V>]{.diffdel}@>{*this, ranges::begin(base_)};
+      return iterator<@[use_const]{.diffins}@>{*this, ranges::begin(base_)};
     }

     @_[...]_@
  };

  template<class R>
    explicit join_view(R&&) -> join_view<all_view<R>>;
}
```

:::

## [US283](https://github.com/cplusplus/nbballot/issues/279) Specification of _`has-arrow`_ concept is ill-formed

Edit [range.utility.helpers]{.wg21} as indicated:

:::bq
```diff
- template<@[input_iterator]{.diffdel}@ I>
+ template<@[class]{.diffins}@ I>
    concept @_has-arrow_@ =                           // @_exposition only_@
-     is_pointer_v<I> || requires(I i) { i.operator->(); };
+     @[input_iterator<I> && (]{.diffins}@is_pointer_v<I> || requires(I i) { i.operator->(); }@[)]{.diffins}@;
```
:::