---
title: "`ranges::iota`, `ranges::shift_left`, and `ranges::shift_right`"
document: P2440R0
date: today
audience:
  - LEWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: true
---

# Abstract
This paper proposes adding the algorithms `ranges::iota`, `ranges::shift_left`,
and `ranges::shift_right`, to match their `std` counterparts.

# Discussion

## `ranges::iota`

As [@P2214R0] explains, while conceptification of other numeric algorithms is a
far more complex endeavor (see, e.g., [@P1813R0]), `iota` is straightforward:

:::bq
We already have `views::iota` in C++20, which importantly means that we already
have all the correct constraints in place. In that sense, it almost takes less
time to adopt `ranges::iota` than it would take to discuss whether or not it's
worth spending time adopting it.
:::

The `ranges::iota` algorithm isn't redundant to `views::iota` either: the
algorithm determines the number of values to write based on the output range,
while using `ranges::copy` or similar algorithms with `views::iota` requires
that information to be computed upfront. When you already have a range,
`ranges::iota` can be more convenient and efficient.

Following the law of useful returns, this paper proposes returning both the end of the
range and the final value.

## `ranges::shift_left` and `ranges::shift_right`

These were proposed in [@P1243R3] but removed in Prague due to concerns about
the return type of `shift_left` losing information about the original end of
the range. There were particularly concerns about difficulty in recovering the
original end if sentinels are involved, since the elements between the end of the
new range and the previous end could have been moved from.

However, this argument overlooks the fact that:

 - when the returned range is not empty, we can simply take its `end()` and
   advance it by the shift amount `n` to obtain the original end. This is a
   potentially linear time operation, but it is not impossible to recover the
   information.
 - when the returned range is empty (that is, the shift amount is greater than
   the size of the range), simply adding `n` is not possible, but in this case
   the algorithm may not necessarily have computed the end iterator of the
   original range: all it needs is the size, which can be computed from
   `last - first` if their types model `sized_sentinel_for`, or from the range
   if its type models `sized_range`. Additionally, we guarantee that in this case
   the range is unchanged, so the sentinel remains usable.

Moreover, the standard library already provides a view factory for users who want
to iterate `[new_last, last)`: `views::counted`. In some cases, using
`counted_iterator` might even be more efficient by reducing iterator comparisons
to integer comparisons (comparing `counted_iterator`s only need to compare the
counter).

Meanwhile, just returning a `subrange` that represents the new range of elements
instead of a more complex, bespoke type that users need to decompose themselves
is substantially more convenient, and it is hardly unprecedented for some
algorithms to not return the end of the range despite necessarily computing it
(e.g., `ranges::count`, `ranges::min/max/minmax_element`), and here we don't
even necessarily compute it. It also allows `shift_left` and `shift_right` to
have the same return type, without having to complicate the latter.

This paper therefore proposes maintaining the [@P1243R3] design:
`ranges::shift_left` and `ranges::shift_right` should return a `subrange` that
represents the new range after the shift.

# Wording

## `ranges::iota`

::: wordinglist

- Edit [numeric.ops.overview]{.sref}, header `<numeric>` synopsis, as indicated:

```diff

 namespace std {
+  namespace ranges {
+    // @[algorithms.results]{.sref}@, algorithm result types
+
+    template<class O, class T>
+      struct out_value_result;
+  }

   // [...]

   // @[numeric.iota]{.sref}@, iota
   template<class ForwardIterator, class T>
     constexpr void iota(ForwardIterator first, ForwardIterator last, T value);

+  namespace ranges {
+    template<class O, class T>
+      using iota_result = out_value_result<O, T>;
+
+    template<input_or_output_iterator O, sentinel_for<O> S, weakly_incrementable T>
+      requires indirectly_writable<O, const T&>
+      constexpr iota_result<O, T> iota(O first, S last, T value);
+
+    template<weakly_incrementable T, output_range<const T&> R>
+      constexpr iota_result<borrowed_iterator_t<R>, T> iota(R&& r, T value);
+  }

   // [...]
 }
```

- Add the following to [algorithms.results]{.sref}:

```cpp
namespace std::ranges {
  // ...

  template<class O, class T>
  struct out_value_result {
    [[no_unique_address]] O out;
    [[no_unique_address]] T value;

    template<class O2, class T2>
      requires convertible_to<const O&, O2> && convertible_to<const T&, T2>
    constexpr operator out_value_result<T2, O2>() const & {
      return {out, value};
    }

    template<class O2, class T2>
      requires convertible_to<O, O2> && convertible_to<T, T2>
    constexpr operator out_value_result<T2, O2>() && {
      return {std::move(out), std::move(value)};
    }
  };

```

- Add the following to [numeric.iota]{.sref}:

::: itemdecl

```cpp
template<input_or_output_iterator O, sentinel_for<O> S, weakly_incrementable T>
  requires indirectly_writable<O, const T&>
  constexpr ranges::iota_result<O, T> ranges::iota(O first, S last, T value);

template<weakly_incrementable T, output_range<const T&> R>
  constexpr ranges::iota_result<borrowed_iterator_t<R>, T> ranges::iota(R&& r, T value);
```

[?]{.pnum} _Effects:_ Equivalent to: [Matching range-v3, we write `as_const(value)`
to the output to enforce that `value` should not be modified by the writing
operation.]{.draftnote}

::: bq
```cpp
while (first != last) {
  *first = as_const(value);
  ++first;
  ++value;
}

return {std::move(first), std::move(value)};
```
:::
:::

- Add the following macro definition to [version.syn]{.sref}, header `<version>`
synopsis, with the value selected by the editor to reflect the date of adoption
of this proposal:

```cpp
#define __cpp_lib_ranges_iota  20XXXXL // also in <numeric>
```

:::

## `ranges::shift_left` and `ranges::shift_right`

::: wordinglist

- Edit [algorithm.syn]{.sref}, header `<algorithm>` synopsis, as indicated:

```diff

 namespace std {

   // [...]

   // @[alg.shift]{.sref}@, shift
   template<class ForwardIterator>
     constexpr ForwardIterator
       shift_left(ForwardIterator first, ForwardIterator last,
                  typename iterator_traits<ForwardIterator>::difference_type n);
   template<class ExecutionPolicy, class ForwardIterator>
     ForwardIterator
       shift_left(ExecutionPolicy&& exec,                        // see [algorithms.parallel.overloads]
                  ForwardIterator first, ForwardIterator last,
                  typename iterator_traits<ForwardIterator>::difference_type n);

+  namespace ranges {
+    template<permutable I, sentinel_for<I> S>
+      constexpr subrange<I> shift_left(I first, S last, iter_difference_t<I> n);
+    template<forward_range R>
+      requires permutable<iterator_t<R>>
+      constexpr borrowed_subrange_t<R> shift_left(R&& r, range_difference_t<R> n);
+  }

   template<class ForwardIterator>
     constexpr ForwardIterator
       shift_right(ForwardIterator first, ForwardIterator last,
                   typename iterator_traits<ForwardIterator>::difference_type n);
   template<class ExecutionPolicy, class ForwardIterator>
     ForwardIterator
       shift_right(ExecutionPolicy&& exec,                       // see [algorithms.parallel.overloads]
                   ForwardIterator first, ForwardIterator last,
                   typename iterator_traits<ForwardIterator>::difference_type n);

+  namespace ranges {
+    template<permutable I, sentinel_for<I> S>
+      constexpr subrange<I> shift_right(I first, S last, iter_difference_t<I> n);
+    template<forward_range R>
+      requires permutable<iterator_t<R>>
+      constexpr borrowed_subrange_t<R> shift_right(R&& r, range_difference_t<R> n);
+  }

   // [...]
 }
```

- Edit [alg.shift]{.sref} as indicated:

::: itemdecl

```diff
 template<class ForwardIterator>
   constexpr ForwardIterator
     shift_left(ForwardIterator first, ForwardIterator last,
                typename iterator_traits<ForwardIterator>::difference_type n);
 template<class ExecutionPolicy, class ForwardIterator>
   ForwardIterator
     shift_left(ExecutionPolicy&& exec, ForwardIterator first, ForwardIterator last,
                typename iterator_traits<ForwardIterator>::difference_type n);
+
+template<permutable I, sentinel_for<I> S>
+  constexpr subrange<I> ranges::shift_left(I first, S last, iter_difference_t<I> n);
+template<forward_range R>
+  requires permutable<iterator_t<R>>
+  constexpr borrowed_subrange_t<R> ranges::shift_left(R&& r, range_difference_t<R> n);
```

[#]{.pnum} _Preconditions:_ `n >= 0` is `true`.
[For the overloads in namespace `std`, t<-T]{.indel}he type of `*first` meets
the _Cpp17MoveAssignable_ requirements.

[#]{.pnum} _Effects:_ If `n == 0` or `n >= last - first`, does nothing. Otherwise,
moves the element from position `first + n + i` into position `first + i` for
each non-negative integer `i < (last - first) - n`. [For the overloads without
an `ExecutionPolicy` template parameter<-In the first overload case]{.indel},
does so in order starting from `i = 0` and proceeding to `i = (last - first) - n - 1`.

[#]{.pnum} _Returns:_ [Let $NEW\_LAST$ be]{.diffins} `first + (last - first - n)`
if `n < last - first`, otherwise `first`.

:::add

- [#.#]{.pnum} $NEW\_LAST$ for the overloads in namespace `std`.
- [#.#]{.pnum} `{first, $NEW_LAST$}` for the overloads in namespace `ranges`.

:::

[#]{.pnum} _Complexity:_ At most `(last - first) - n` assignments.


```diff
 template<class ForwardIterator>
   constexpr ForwardIterator
     shift_right(ForwardIterator first, ForwardIterator last,
                 typename iterator_traits<ForwardIterator>::difference_type n);
 template<class ExecutionPolicy, class ForwardIterator>
   ForwardIterator
     shift_right(ExecutionPolicy&& exec, ForwardIterator first, ForwardIterator last,
                 typename iterator_traits<ForwardIterator>::difference_type n);
+
+template<permutable I, sentinel_for<I> S>
+  constexpr subrange<I> ranges::shift_right(I first, S last, iter_difference_t<I> n);
+template<forward_range R>
+  requires permutable<iterator_t<R>>
+  constexpr borrowed_subrange_t<R> ranges::shift_right(R&& r, range_difference_t<R> n);
```

[#]{.pnum} _Preconditions:_ `n >= 0` is `true`.
[For the overloads in namespace `std`, t<-T]{.indel}he type of `*first` meets
the _Cpp17MoveAssignable_ requirements[, and<-.]{.indel} `ForwardIterator` meets the
_Cpp17BidirectionalIterator_ requirements ([bidirectional.iterators]{.sref}) or
the _Cpp17ValueSwappable_ requirements.

[#]{.pnum} _Effects:_ If `n == 0` or `n >= last - first`, does nothing. Otherwise,
moves the element from position `first + i` into position `first + n + i` for
each non-negative integer `i < (last - first) - n`. [In the first overload case,
if `ForwardIterator` meets the  _Cpp17BidirectionalIterator_ requirements,
d]{.diffdel}[D]{.diffins}oes so in order starting from `i = (last - first) - n - 1` and
proceeding to `i = 0` [if:<-.]{.indel}

:::add

- [#.#]{.pnum} for the overload in namespace `std` without an `ExecutionPolicy`
  template parameter, `ForwardIterator` meets the  _Cpp17BidirectionalIterator_
  requirements.
- [#.#]{.pnum} for the overloads in namespace `ranges`, `decltype(first)` models `bidirectional_iterator`.

:::

[#]{.pnum} _Returns:_ [Let $NEW\_FIRST$ be]{.diffins} `first + n`
if `n < last - first`, otherwise `last`.

:::add

- [#.#]{.pnum} $NEW\_FIRST$ for the overloads in namespace `std`.
- [#.#]{.pnum} `{$NEW_FIRST$, last}` for the overloads in namespace `ranges`.

:::

[#]{.pnum} _Complexity:_ At most `(last - first) - n` assignments or swaps.

:::

- Update the value of `__cpp_lib_shift` in [version.syn]{.sref} to reflect the
  date of adoption of this proposal.

:::
