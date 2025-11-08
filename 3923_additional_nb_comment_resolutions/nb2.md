---
title: Additional NB comment resolutions for Kona 2025
document: D3923R0
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
---

# Introduction

This paper provides wording to resolve the following national body comments on the C++26 CD:

- [AT 7-213](https://github.com/cplusplus/nbballot/issues/782)
- [US 140-233](https://github.com/cplusplus/nbballot/issues/804)
- [US 141-235](https://github.com/cplusplus/nbballot/issues/806)
- [US 145-234](https://github.com/cplusplus/nbballot/issues/805)
- [US 147-240](https://github.com/cplusplus/nbballot/issues/811)
- [US 164-203](https://github.com/cplusplus/nbballot/issues/838)
- [US 126-189](https://github.com/cplusplus/nbballot/issues/758)
- [US 227-346](https://github.com/cplusplus/nbballot/issues/921)
- [US 229-347](https://github.com/cplusplus/nbballot/issues/922)
- [US 221-339](https://github.com/cplusplus/nbballot/issues/914)
- [US 225-341](https://github.com/cplusplus/nbballot/issues/916)

# Wording

This wording is relative to [@N5014] except where noted.

## [AT 7-213](https://github.com/cplusplus/nbballot/issues/782)

Edit [tuple.helper]{.sref} as indicated:

::: itemdecl
```cpp
template<class T> struct tuple_size<const T>;
```

[4]{.pnum} [...]

[#]{.pnum} [...]

[#]{.pnum} In addition to being available via inclusion of the `<tuple>` header, the template is available when any of the headers `<array>`, [`<complex>`,]{.diffins} `<ranges>`, or `<utility>` are included.

```cpp
template<size_t I, class T> struct tuple_element<I, const T>;
```

[#]{.pnum} [...]

[#]{.pnum} In addition to being available via inclusion of the `<tuple>` header, the template is available when any of the headers `<array>`, [`<complex>`,]{.diffins} `<ranges>`, or `<utility>` are included.

:::

## [US 140-233](https://github.com/cplusplus/nbballot/issues/804)

[We add a cross-reference and a note to [hive.overview]{.sref} to clarify that "insertion" doesn't include construction or assignment.]{.draftnote}

::: wordinglist

- Edit [hive.overview]{.sref} as indicated:

[1]{.pnum} A `hive` is a type of sequence container that provides constant-time insertion and erasure operations. Storage is automatically managed in multiple memory blocks, referred to as _element blocks_. Insertion [([hive.modifiers]{.sref})]{.diffins} position is determined by the container, and insertion may re-use the memory locations of erased elements. [[Construction and assignment are not considered to involve insertion operations.]{.note-}]{.diffins}

- Edit [hive.cons]{.sref} as indicated:

::: itemdecl

```cpp
template<$container-compatible-range$<T> R>
  hive(from_range_t, R&& rg, const Allocator& = Allocator());
template<$container-compatible-range$<T> R>
  hive(from_range_t, R&& rg, hive_limits block_limits, const Allocator& = Allocator());
```

[13]{.pnum} _Effects_: Constructs a `hive` object [equal to<-with the elements of]{.indel} the range `rg`, using the specified allocator. If the second overload is called, also initializes `$current-limits$` with `block_limits`.

[#]{.pnum} _Complexity_: Linear in `ranges​::​distance(rg)`.

```cpp
hive(const hive& x);
hive(const hive& x, const type_identity_t<Allocator>& alloc);
```
[#]{.pnum} _Preconditions_: `T` is _Cpp17CopyInsertable_ into `hive`.

[#]{.pnum} _Effects_: Constructs a hive object [equal to<-with the elements of]{.indel} `x`. If the second overload is called, uses `alloc`. Initializes `$current-limits$` with `x.$current-limits$`.

[#]{.pnum} _Complexity_: Linear in `x.size()`.

```cpp
hive(hive&& x) noexcept;
hive(hive&& x, const type_identity_t<Allocator>& alloc);
```

[#]{.pnum} _Preconditions_: For the second overload, when `allocator_traits<alloc>​::​is_always_equal​::​value` is `false`, `T` meets the _Cpp17MoveInsertable_ requirements.

[#]{.pnum} _Effects_: When the first overload is called, or the second overload is called and `alloc == x.get_allocator()` is `true`, `$current-limits$` is set to `x.$current-limits$` and each element block is moved from `x` into `*this`. Pointers and references to the elements of `x` now refer to those same elements but as members of `*this`. Iterators referring to the elements of `x` will continue to refer to their elements, but they now behave as iterators into `*this`.
If the second overload is called and `alloc == x.get_allocator()` is false, each element in `x` is moved into `*this`. References, pointers and iterators referring to the elements of `x`, as well as the past-the-end iterator of `x`, are invalidated.

[#]{.pnum} _Postconditions_: `x.empty()` is `true`. [The relative order of the elements of `*this` is the same as that of the elements of `x` prior to this call.]{.diffins}

[#]{.pnum} _Complexity_: If the second overload is called and `alloc == x.get_allocator()` is `false`, linear in `x.size()`. Otherwise constant.

```cpp
hive(initializer_list<T> il, const Allocator& = Allocator());
hive(initializer_list<T> il, hive_limits block_limits, const Allocator& = Allocator());
```

[#]{.pnum} _Preconditions_: `T` is _Cpp17CopyInsertable_ into `hive`.

[13]{.pnum} _Effects_: Constructs a `hive` object [equal to<-with the elements of]{.indel} `il`, using the specified allocator. If the second overload is called, also initializes `$current-limits$` with `block_limits`.

[#]{.pnum} _Complexity_: Linear in `il.size()`.

```cpp
hive& operator=(const hive& x);
```

[#]{.pnum} _Preconditions_: `T` is _Cpp17CopyInsertable_ into `hive` and _Cpp17CopyAssignable_.

[#]{.pnum} _Effects_: All elements in `*this` are either copy-assigned to, or destroyed. All elements in `x` are copied into `*this`[, maintaining their relative order]{.diffins}.

[`$current-limits$` is unchanged.]{.note}

[#]{.pnum} _Complexity_:  Linear in `size() + x.size()`.

```cpp
hive& operator=(hive&& x)
  noexcept(allocator_traits<Allocator>::propagate_on_container_move_assignment::value ||
           allocator_traits<Allocator>::is_always_equal::value);
```

[#]{.pnum} _Preconditions_: When

::: bq
```cpp
(allocator_traits<Allocator>::propagate_on_container_move_assignment::value ||
 allocator_traits<Allocator>::is_always_equal::value)
```
:::
is `false`, `T` is _Cpp17MoveInsertable_ into `hive` and _Cpp17MoveAssignable_.

[#]{.pnum} _Effects:_ Each element in `*this` is either move-assigned to, or destroyed. When

::: bq
```cpp
(allocator_traits<Allocator>::propagate_on_container_move_assignment::value ||
 get_allocator() == x.get_allocator())
```
:::
is `true`, `$current-limits$` is set to `x.$current-limits$` and each element block is moved from `x` into `*this`. Pointers and references to the elements of `x` now refer to those same elements but as members of `*this`. Iterators referring to the elements of `x` will continue to refer to their elements, but they now behave as iterators into `*this`, not into `x`.
When

::: bq
```cpp
(allocator_traits<Allocator>::propagate_on_container_move_assignment::value ||
 get_allocator() == x.get_allocator())
```
:::
is `false`, each element in `x` is moved into `*this`. References, pointers and iterators referring to the elements of `x`, as well as the past-the-end iterator of `x`, are invalidated.

[#]{.pnum} _Postconditions_: `x.empty()` is `true`. [The relative order of the elements of `*this` is the same as that of the elements of `x` prior to this call.]{.diffins}

[#]{.pnum} _Complexity_: Linear in `size()`. If

::: bq
```cpp
(allocator_traits<Allocator>::propagate_on_container_move_assignment::value ||
 get_allocator() == x.get_allocator())
```
:::
is `false`, also linear in `x.size()`.

:::

:::

## [US 141-235](https://github.com/cplusplus/nbballot/issues/806)

[LWG concluded that the wording is already clear that the order does not change because
nothing in the wording gives permission for it to change. However, it was pointed out
that the first sentence of the _Remarks_: paragraph is similarly a "nothing happens" sentence
and LWG decided to strike it to avoid the erroneous implication that
"everything not explictly described as not changing can change".]{.draftnote}

Edit [hive.capacity]{.sref} as indicated:

::: itemdecl
```cpp
void reserve(size_type n);
```

[3]{.pnum} _Effects_: [...]

[#]{.pnum} _Postconditions_: [...]

[#]{.pnum} _Throws_: [...]

[#]{.pnum} _Complexity_: [...]

[#]{.pnum} _Remarks:_ [The size of the sequence is not changed.]{.diffdel} All references, pointers, and iterators referring to elements in` *this`, as well as the past-the-end iterator, remain valid.

:::

## [US 145-234](https://github.com/cplusplus/nbballot/issues/805)

Edit [hive.capacity]{.sref} as indicated:

::: itemdecl
```cpp
void trim_capacity() noexcept;
void trim_capacity(size_type n) noexcept;
```

[12]{.pnum} _Effects_: For the first overload, all reserved blocks are deallocated, and `capacity()` is reduced accordingly. For the second overload, [if `n >= capacity()` is `true`, there are no effects; otherwise,]{.diffins} `capacity()` is reduced to no less than `n`.

[#]{.pnum} _Complexity_: Linear in the number of reserved blocks deallocated.

[#]{.pnum} _Remarks_: All references, pointers, and iterators referring to elements in `*this`, as well as the past-the-end iterator, remain valid.

:::

## [US 147-240](https://github.com/cplusplus/nbballot/issues/811)

[LWG determined that there is no good reason to check the block limits during or after the splice and therefore we can offer the strong exception guarantee.]{.draftnote}

Edit [hive.operations]{.sref} as indicated:

::: itemdecl

```cpp
void splice(hive& x);
void splice(hive&& x);
```

[2]{.pnum} _Preconditions_: `get_allocator() == x.get_allocator()` is `true`.

[#]{.pnum} _Effects_: If `addressof(x) == this` is `true`, the behavior is erroneous and there are no effects. [If an exception is thrown, there are no effects.]{.diffins} Otherwise, inserts the contents of `x` into `*this` and `x` becomes empty. Pointers and references to the moved elements of `x` now refer to those same elements but as members of `*this`. Iterators referring to the moved elements continue to refer to their elements, but they now behave as iterators into `*this`, not into `x`.

[#]{.pnum} _Throws:_ `length_error` if any of `x`'s active blocks are not within the bounds of `$current-limits$`.

[#]{.pnum} _Complexity_: Linear in the sum of all element blocks in `x` plus all element blocks in `*this`.

[#]{.pnum} _Remarks_: Reserved blocks in `x` are not transferred into `*this`. If `addressof(x) == this` is `false`, invalidates the past-the-end iterator for both `x` and `*this`.

:::

## [US 164-203](https://github.com/cplusplus/nbballot/issues/838)

::: wordinglist

- Edit [set.union]{.sref} as indicated:

::: itemdecl
```cpp
template<class InputIterator1, class InputIterator2, class OutputIterator>
  constexpr OutputIterator
    set_union(InputIterator1 first1, InputIterator1 last1,
              InputIterator2 first2, InputIterator2 last2,
              OutputIterator result);
template<class ExecutionPolicy, class ForwardIterator1, class ForwardIterator2,
         class ForwardIterator>
  ForwardIterator
    set_union(ExecutionPolicy&& exec,
              ForwardIterator1 first1, ForwardIterator1 last1,
              ForwardIterator2 first2, ForwardIterator2 last2,
              ForwardIterator result);

template<class InputIterator1, class InputIterator2, class OutputIterator, class Compare>
  constexpr OutputIterator
    set_union(InputIterator1 first1, InputIterator1 last1,
              InputIterator2 first2, InputIterator2 last2,
              OutputIterator result, Compare comp);
template<class ExecutionPolicy, class ForwardIterator1, class ForwardIterator2,
         class ForwardIterator, class Compare>
  ForwardIterator
    set_union(ExecutionPolicy&& exec,
              ForwardIterator1 first1, ForwardIterator1 last1,
              ForwardIterator2 first2, ForwardIterator2 last2,
              ForwardIterator result, Compare comp);

template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
         weakly_incrementable O, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
  constexpr ranges::set_union_result<I1, I2, O>
    ranges::set_union(I1 first1, S1 last1, I2 first2, S2 last2, O result, Comp comp = {},
                      Proj1 proj1 = {}, Proj2 proj2 = {});
template<input_range R1, input_range R2, weakly_incrementable O,
         class Comp = ranges::less, class Proj1 = identity, class Proj2 = identity>
  requires mergeable<iterator_t<R1>, iterator_t<R2>, O, Comp, Proj1, Proj2>
  constexpr ranges::set_union_result<borrowed_iterator_t<R1>, borrowed_iterator_t<R2>, O>
    ranges::set_union(R1&& r1, R2&& r2, O result, Comp comp = {},
                      Proj1 proj1 = {}, Proj2 proj2 = {});

template<$execution-policy$ Ep, random_access_iterator I1, sized_sentinel_for<I1> S1,
         random_access_iterator I2, sized_sentinel_for<I2> S2,
         random_access_iterator O, sized_sentinel_for<O> OutS, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
  ranges::set_union_result<I1, I2, O>
    ranges::set_union(Ep&& exec, I1 first1, S1 last1,
                      I2 first2, S2 last2, O result, OutS result_last,
                      Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
template<$execution-policy$ Ep, $sized-random-access-range$ R1, $sized-random-access-range$ R2,
         $sized-random-access-range$ OutR, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<iterator_t<R1>, iterator_t<R2>, iterator_t<OutR>, Comp, Proj1, Proj2>
  ranges::set_union_result<borrowed_iterator_t<R1>, borrowed_iterator_t<R2>,
                           borrowed_iterator_t<OutR>>
    ranges::set_union(Ep&& exec, R1&& r1, R2&& r2, OutR&& result_r, Comp comp = {},
                      Proj1 proj1 = {}, Proj2 proj2 = {});
```

[1]{.pnum} Let:

- [#.#]{.pnum} `comp` be `less{}`, and `proj1` and `proj2` be `identity{}` for the overloads with no parameters by those names;
- [#.#]{.pnum} _M_ be [the number of elements in the sorted union (see below)<-`last1 - first1` plus the number of elements in `[first2, last2)` that are not present in `[first1, last1)`]{.indel};
- [#.#]{.pnum} `result_last` be `result +` _M_ for the overloads with no parameter `result_last` or `result_r`;
- [#.#]{.pnum} _N_ be min(_M_,  `result_last - result`).

[#]{.pnum} _Preconditions_: The ranges `[first1, last1)` and `[first2, last2)` are sorted with respect to `comp` and `proj1` or `proj2`, respectively. The resulting range does not overlap with either of the original ranges.

[#]{.pnum} _Effects_: Constructs a sorted union of [the<-_N_]{.indel} elements from the two ranges; that is, the set of elements that are present in one or both of the ranges. [If `[first1, last1)` contains _m_ elements that are equivalent to each other and `[first2, last2)` contains _n_ elements that are equivalent to them, then all _m_ elements from the first range are included in the union, in order, and then the final $max(n - m, 0)$ elements from the second range are included in the union, in order. If, of those elements, _k_ elements from the first range are copied to the output range, then the first $min(k, n)$ elements from the second range are considered _skipped_. Copies the first _N_ elements of the sorted union to the range `[result, result +` _N_`)`.]{.diffins}

[#]{.pnum} _Returns_:

- [#.#]{.pnum} `result_last` for the overloads in namespace `std`.
- [#.#]{.pnum} `{last1, last2, result +` _N_`}` for the overloads in namespace `ranges`, if _N_ is equal to _M_.
- [#.#]{.pnum} Otherwise, [`{j1, j2, result_last}`]{.diffdel} [`{first1 +` _A_`, first2 +` _B_`, result_last}`]{.diffins} for the overloads in namespace `ranges`, where [the iterators `j1` and `j2` point to positions past the last]{.diffdel}[_A_ and _B_ are the numbers of]{.diffins} copied or skipped elements in `[first1, last1)` and `[first2, last2)`, respectively.

[#]{.pnum} _Complexity_: At most `2 * ((last1 - first1) + (last2 - first2)) - 1` comparisons and applications of each projection.

[#]{.pnum} _Remarks_: Stable ([algorithm.stable]{.sref}). [If `[first1, last1)` contains _m_ elements that are equivalent to each other and `[first2, last2)` contains _n_ elements that are equivalent to them, then all _m_ elements from the first range are copied to the output range, in order, and then the final $max(n - m, 0)$ elements from the second range are copied to the output range, in order.]{.diffdel}

:::

- Edit [set.intersection]{.sref} as indicated:

::: itemdecl
```cpp
template<class InputIterator1, class InputIterator2,
         class OutputIterator>
  constexpr OutputIterator
    set_intersection(InputIterator1 first1, InputIterator1 last1,
                     InputIterator2 first2, InputIterator2 last2,
                     OutputIterator result);
template<class ExecutionPolicy, class ForwardIterator1, class ForwardIterator2,
         class ForwardIterator>
  ForwardIterator
    set_intersection(ExecutionPolicy&& exec,
                     ForwardIterator1 first1, ForwardIterator1 last1,
                     ForwardIterator2 first2, ForwardIterator2 last2,
                     ForwardIterator result);

template<class InputIterator1, class InputIterator2,
         class OutputIterator, class Compare>
  constexpr OutputIterator
    set_intersection(InputIterator1 first1, InputIterator1 last1,
                     InputIterator2 first2, InputIterator2 last2,
                     OutputIterator result, Compare comp);
template<class ExecutionPolicy, class ForwardIterator1, class ForwardIterator2,
         class ForwardIterator, class Compare>
  ForwardIterator
    set_intersection(ExecutionPolicy&& exec,
                     ForwardIterator1 first1, ForwardIterator1 last1,
                     ForwardIterator2 first2, ForwardIterator2 last2,
                     ForwardIterator result, Compare comp);

template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
         weakly_incrementable O, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
  constexpr ranges::set_intersection_result<I1, I2, O>
    ranges::set_intersection(I1 first1, S1 last1, I2 first2, S2 last2, O result,
                             Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
template<input_range R1, input_range R2, weakly_incrementable O,
         class Comp = ranges::less, class Proj1 = identity, class Proj2 = identity>
  requires mergeable<iterator_t<R1>, iterator_t<R2>, O, Comp, Proj1, Proj2>
  constexpr ranges::set_intersection_result<borrowed_iterator_t<R1>, borrowed_iterator_t<R2>, O>
    ranges::set_intersection(R1&& r1, R2&& r2, O result,
                             Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});

template<$execution-policy$ Ep, random_access_iterator I1, sized_sentinel_for<I1> S1,
         random_access_iterator I2, sized_sentinel_for<I2> S2,
         random_access_iterator O, sized_sentinel_for<O> OutS, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
  ranges::set_intersection_result<I1, I2, O>
    ranges::set_intersection(Ep&& exec, I1 first1, S1 last1,
                      I2 first2, S2 last2, O result, OutS result_last,
                      Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
template<$execution-policy$ Ep, $sized-random-access-range$ R1, $sized-random-access-range$ R2,
         $sized-random-access-range$ OutR, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<iterator_t<R1>, iterator_t<R2>, iterator_t<OutR>, Comp, Proj1, Proj2>
  ranges::set_intersection_result<borrowed_iterator_t<R1>, borrowed_iterator_t<R2>,
                                  borrowed_iterator_t<OutR>>
    ranges::set_intersection(Ep&& exec, R1&& r1, R2&& r2, OutR&& result_r, Comp comp = {},
                             Proj1 proj1 = {}, Proj2 proj2 = {});
```

[1]{.pnum} Let:

- [#.#]{.pnum} `comp` be `less{}`, and `proj1` and `proj2` be `identity{}` for the overloads with no parameters by those names;
- [#.#]{.pnum} _M_ be the number of elements in [the sorted intersection (see below)<-`[first1, last1)` that are present in `[first2, last2)`]{.indel};
- [#.#]{.pnum} `result_last` be `result +` _M_ for the overloads with no parameter `result_last` or `result_r`;
- [#.#]{.pnum} _N_ be min(_M_,  `result_last - result`).

[#]{.pnum} _Preconditions_: The ranges `[first1, last1)` and `[first2, last2)` are sorted with respect to `comp` and `proj1` or `proj2`, respectively. The resulting range does not overlap with either of the original ranges.

[#]{.pnum} _Effects_: Constructs a sorted intersection of [the<-_N_]{.indel} elements from the two ranges; that is, the set of elements that are present in both of the ranges. [If `[first1, last1)` contains $m$ elements that are equivalent to each other and `[first2, last2)` contains $n$ elements that are equivalent to them, the first $min(m,n)$ elements from the first range are included in the sorted intersection. If, of those elements, _k_ elements from the first range are copied to the output range, then the first _k_ elements from the second range are considered _skipped_. If $N < M$, a non-copied element is also considered skipped if it compares less than the $(N+ 1)^{th}$ element of the sorted intersection. Copies the first _N_ elements of the sorted intersection to the range `[result, result +` _N_`)`.]{.diffins}

[#]{.pnum} _Returns_:

- [#.#]{.pnum} `result_last` for the overloads in namespace `std`.
- [#.#]{.pnum} `{last1, last2, result +` _N_`}` for the overloads in namespace `ranges`, if _N_ is equal to _M_.
- [#.#]{.pnum} Otherwise, [`{j1, j2, result_last}`]{.diffdel} [`{first1 +` _A_`, first2 +` _B_`, result_last}`]{.diffins} for the overloads in namespace `ranges`, where [the iterators `j1` and `j2` point to positions past the last]{.diffdel}[_A_ and _B_ are the numbers of]{.diffins} copied or skipped elements in `[first1, last1)` and `[first2, last2)`, respectively.

[#]{.pnum} _Complexity_: At most `2 * ((last1 - first1) + (last2 - first2)) - 1` comparisons and applications of each projection.

[#]{.pnum} _Remarks_: Stable ([algorithm.stable]{.sref}). [If `[first1, last1)` contains $m$ elements that are equivalent to each other and `[first2, last2)` contains $n$ elements that are equivalent to them, the first $min(m,n)$ elements are copied from the first range to the output range, in order.]{.diffdel}

:::

- Edit [set.difference]{.sref} as indicated:

::: itemdecl
```cpp
template<class InputIterator1, class InputIterator2,
         class OutputIterator>
  constexpr OutputIterator
    set_difference(InputIterator1 first1, InputIterator1 last1,
                   InputIterator2 first2, InputIterator2 last2,
                   OutputIterator result);
template<class ExecutionPolicy, class ForwardIterator1, class ForwardIterator2,
         class ForwardIterator>
  ForwardIterator
    set_difference(ExecutionPolicy&& exec,
                   ForwardIterator1 first1, ForwardIterator1 last1,
                   ForwardIterator2 first2, ForwardIterator2 last2,
                   ForwardIterator result);

template<class InputIterator1, class InputIterator2,
         class OutputIterator, class Compare>
  constexpr OutputIterator
    set_difference(InputIterator1 first1, InputIterator1 last1,
                   InputIterator2 first2, InputIterator2 last2,
                   OutputIterator result, Compare comp);
template<class ExecutionPolicy, class ForwardIterator1, class ForwardIterator2,
         class ForwardIterator, class Compare>
  ForwardIterator
    set_difference(ExecutionPolicy&& exec,
                   ForwardIterator1 first1, ForwardIterator1 last1,
                   ForwardIterator2 first2, ForwardIterator2 last2,
                   ForwardIterator result, Compare comp);

template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
         weakly_incrementable O, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
  constexpr ranges::set_difference_result<I1, O>
    ranges::set_difference(I1 first1, S1 last1, I2 first2, S2 last2, O result,
                           Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
template<input_range R1, input_range R2, weakly_incrementable O,
         class Comp = ranges::less, class Proj1 = identity, class Proj2 = identity>
  requires mergeable<iterator_t<R1>, iterator_t<R2>, O, Comp, Proj1, Proj2>
  constexpr ranges::set_difference_result<borrowed_iterator_t<R1>, O>
    ranges::set_difference(R1&& r1, R2&& r2, O result,
                           Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});

template<$execution-policy$ Ep, random_access_iterator I1, sized_sentinel_for<I1> S1,
         random_access_iterator I2, sized_sentinel_for<I2> S2,
         random_access_iterator O, sized_sentinel_for<O> OutS, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
  ranges::set_difference_result<I1, O>
    ranges::set_difference(Ep&& exec, I1 first1, S1 last1,
                           I2 first2, S2 last2, O result, OutS result_last,
                           Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
template<$execution-policy$ Ep, $sized-random-access-range$ R1, $sized-random-access-range$ R2,
         $sized-random-access-range$ OutR, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<iterator_t<R1>, iterator_t<R2>, iterator_t<OutR>, Comp, Proj1, Proj2>
  ranges::set_difference_result<borrowed_iterator_t<R1>, borrowed_iterator_t<OutR>>
    ranges::set_difference(Ep&& exec, R1&& r1, R2&& r2, OutR&& result_r, Comp comp = {},
                           Proj1 proj1 = {}, Proj2 proj2 = {});
```


[1]{.pnum} Let:

- [#.#]{.pnum} `comp` be `less{}`, and `proj1` and `proj2` be `identity{}` for the overloads with no parameters by those names;
- [#.#]{.pnum} _M_ be the number of elements in [the sorted difference (see below)<- `[first1, last1)` that are not present in `[first2, last2)`]{.indel};
- [#.#]{.pnum} `result_last` be `result +` _M_ for the overloads with no parameter `result_last` or `result_r`;
- [#.#]{.pnum} _N_ be min(_M_,  `result_last - result`).

[#]{.pnum} _Preconditions_: The ranges `[first1, last1)` and `[first2, last2)` are sorted with respect to `comp` and `proj1` or `proj2`, respectively. The resulting range does not overlap with either of the original ranges.

::: rm
[#]{.pnum} _Effects_: Copies _N_ elements of the range `[first1, last1)` which are not present in the range `[first2, last2)` to the range `[result, result +` _N_`)`. The elements in the constructed range are sorted.
:::

::: add
[3]{.pnum} _Effects_: Constructs a sorted difference between the elements from the two ranges; that is, the set of elements that are present in the range `[first1, last1)` but not `[first2, last2)`. If `[first1, last1)` contains $m$ elements that are equivalent to each other and `[first2, last2)` contains $n$ elements that are equivalent to them, the last $max(m-n, 0)$ elements from `[first1, last1)` are included in the sorted difference, in order. Copies the first _N_ elements of the sorted difference to the range `[result, result +` _N_`)`.
:::

[#]{.pnum} _Returns_:

- [#.#]{.pnum} `result_last` for the overloads in namespace `std`.
- [#.#]{.pnum} `{last1, result +` _N_`}` for the overloads in namespace `ranges`, if _N_ is equal to _M_.
- [#.#]{.pnum} Otherwise, `{j1, result_last}` for the overloads in namespace `ranges`, where the iterator `j1` points to the position [of the<-past the last copied or skipped]{.indel} element in `[first1, last1)` [corresponding to the $(N+1)^{th}$ element of the sorted difference]{.diffins}.

[#]{.pnum} _Complexity_: At most `2 * ((last1 - first1) + (last2 - first2)) - 1` comparisons and applications of each projection.

[#]{.pnum} _Remarks_: [Stable ([algorithm.stable]{.sref}).]{.diffins} [If `[first1, last1)` contains $m$ elements that are equivalent to each other and `[first2, last2)` contains $n$ elements that are equivalent to them, the last $max(m-n, 0)$ elements are copied from `[first1, last1)` to the output range, in order.]{.diffdel}

:::

- Edit [set.symmetric.difference]{.sref} as indicated:

::: itemdecl
```cpp
template<class InputIterator1, class InputIterator2,
         class OutputIterator>
  constexpr OutputIterator
    set_symmetric_difference(InputIterator1 first1, InputIterator1 last1,
                             InputIterator2 first2, InputIterator2 last2,
                             OutputIterator result);
template<class ExecutionPolicy, class ForwardIterator1, class ForwardIterator2,
         class ForwardIterator>
  ForwardIterator
    set_symmetric_difference(ExecutionPolicy&& exec,
                             ForwardIterator1 first1, ForwardIterator1 last1,
                             ForwardIterator2 first2, ForwardIterator2 last2,
                             ForwardIterator result);

template<class InputIterator1, class InputIterator2,
         class OutputIterator, class Compare>
  constexpr OutputIterator
    set_symmetric_difference(InputIterator1 first1, InputIterator1 last1,
                             InputIterator2 first2, InputIterator2 last2,
                             OutputIterator result, Compare comp);
template<class ExecutionPolicy, class ForwardIterator1, class ForwardIterator2,
         class ForwardIterator, class Compare>
  ForwardIterator
    set_symmetric_difference(ExecutionPolicy&& exec,
                             ForwardIterator1 first1, ForwardIterator1 last1,
                             ForwardIterator2 first2, ForwardIterator2 last2,
                             ForwardIterator result, Compare comp);

template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
         weakly_incrementable O, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
  constexpr ranges::set_symmetric_difference_result<I1, I2, O>
    ranges::set_symmetric_difference(I1 first1, S1 last1, I2 first2, S2 last2, O result,
                                     Comp comp = {}, Proj1 proj1 = {},
                                     Proj2 proj2 = {});
template<input_range R1, input_range R2, weakly_incrementable O,
         class Comp = ranges::less, class Proj1 = identity, class Proj2 = identity>
  requires mergeable<iterator_t<R1>, iterator_t<R2>, O, Comp, Proj1, Proj2>
  constexpr ranges::set_symmetric_difference_result<borrowed_iterator_t<R1>,
                                                    borrowed_iterator_t<R2>, O>
    ranges::set_symmetric_difference(R1&& r1, R2&& r2, O result, Comp comp = {},
                                     Proj1 proj1 = {}, Proj2 proj2 = {});

template<execution-policy Ep, random_access_iterator I1, sized_sentinel_for<I1> S1,
         random_access_iterator I2, sized_sentinel_for<I2> S2,
         random_access_iterator O, sized_sentinel_for<O> OutS, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
  ranges::set_symmetric_difference_result<I1, I2, O>
    ranges::set_symmetric_difference(Ep&& exec, I1 first1, S1 last1,
                                     I2 first2, S2 last2, O result, OutS result_last,
                                     Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
template<execution-policy Ep, sized-random-access-range R1, sized-random-access-range R2,
         sized-random-access-range OutR, class Comp = ranges::less,
         class Proj1 = identity, class Proj2 = identity>
  requires mergeable<iterator_t<R1>, iterator_t<R2>, iterator_t<OutR>, Comp, Proj1, Proj2>
  ranges::set_symmetric_difference_result<borrowed_iterator_t<R1>, borrowed_iterator_t<R2>,
                                  borrowed_iterator_t<OutR>>
    ranges::set_symmetric_difference(Ep&& exec, R1&& r1, R2&& r2, OutR&& result_r,
                                     Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
```



[1]{.pnum} Let:

- [#.#]{.pnum} `comp` be `less{}`, and `proj1` and `proj2` be `identity{}` for the overloads with no parameters by those names;

::: rm
- [#.#]{.pnum} _K_ be the number of elements in `[first1, last1)` that are not present in `[first2, last2)`;
:::

- [#.#]{.pnum} _M_ be the number of elements in [the sorted symmetric difference (see below)<- `[first2, last2)` that are not present in `[first1, last1)`]{.indel};
- [#.#]{.pnum} `result_last` be `result +` _M_ [+ _K_]{.diffdel} for the overloads with no parameter `result_last` or `result_r`;
- [#.#]{.pnum} _N_ be min([_K_ +]{.diffdel} _M_,  `result_last - result`).

[#]{.pnum} _Preconditions_: The ranges `[first1, last1)` and `[first2, last2)` are sorted with respect to `comp` and `proj1` or `proj2`, respectively. The resulting range does not overlap with either of the original ranges.

::: rm
[#]{.pnum} _Effects:_ Copies the elements of the range `[first1, last1)` that are not present in the range `[first2, last2)`, and the elements of the range `[first2, last2)` that are not present in the range `[first1, last1)` to the range `[result, result +` _N_`)`. The elements in the constructed range are sorted.
:::

::: add
[3]{.pnum} _Effects_: Constructs a sorted symmetric difference of the elements from the two ranges; that is, the set of elements that are present in exactly one of `[first1, last1)` and `[first2, last2)`. If `[first1, last1)` contains $m$ elements that are equivalent to each other and `[first2, last2)` contains $n$ elements that are equivalent to them, then $|m - n|$ of those elements are included in the symmetric difference: the last $m - n$ of these elements from `[first1, last1)`, in order, if $m > n$, and the last $n - m$ of these elements from `[first2, last2)`, in order, if $m < n$. If $N < M$, a non-copied element is considered _skipped_ if it compares less than or equivalent to the $(N+1)^{th}$ element of the sorted symmetric difference, unless it is from the same range as that element and does not precede it. Copies the first _N_ elements of the sorted symmetric difference to the range `[result, result +` _N_`)`.
:::

[#]{.pnum} _Returns_:

- [#.#]{.pnum} `result_last` for the overloads in namespace `std`.
- [#.#]{.pnum} `{last1, last2, result +` _N_`}` for the overloads in namespace `ranges`, if _N_ is equal to _M_ [+ _K_]{.diffdel}.
- [#.#]{.pnum} Otherwise, [`{j1, j2, result_last}`]{.diffdel} [`{first1 +` _A_`, first2 +` _B_`, result_last}`]{.diffins} for the overloads in namespace `ranges`, where [the iterators `j1` and `j2` point to positions past the last]{.diffdel}[_A_ and _B_ are the numbers of]{.diffins} copied or skipped elements in `[first1, last1)` and `[first2, last2)`, respectively.

[#]{.pnum} _Complexity_: At most `2 * ((last1 - first1) + (last2 - first2)) - 1` comparisons and applications of each projection.

[#]{.pnum} _Remarks_: Stable ([algorithm.stable]{.sref}). [If `[first1, last1)` contains $m$ elements that are equivalent to each other and `[first2, last2)` contains $n$ elements that are equivalent to them, then $|m - n|$ of those elements shall be copied to the output range: the last $m - n$ of these elements from `[first1, last1)` if $m > n$, and the last $n - m$ of these elements from `[first2, last2)` if $m < n$. In either case, the elements are copied in order.]{.diffdel}

:::

:::

## [US 126-189](https://github.com/cplusplus/nbballot/issues/758)

Edit [meta.reflection.define.aggregate]{.sref} as indicated:

::: itemdecl

```cpp
template<reflection_range R = initializer_list<info>>
  consteval info define_aggregate(info class_type, R&& mdescrs);
```

[7]{.pnum} Let $C$ be the class represented by `class_type` and $r_K$ be the $K^{th}$
reflection value in `mdescrs`. For every $r_K$ in `mdescrs`, let
$(T_K,N_K,A_K,W_K,NUA_K)$ be the corresponding data member description represented by
$r_K$.

[#]{.pnum} _Constant When:_

- [#.#]{.pnum} _C_ is incomplete from every point in the evaluation context;
[_C_ can be a class template specialization for which there is a reachable definition of the class template. In this case, the injected declaration is an explicit specialization.]{.note4}
- [#.#]{.pnum} [...]
- [#.#]{.pnum} [...]
- [#.#]{.pnum} [...]

[#]{.pnum} _Effects_: Produces an injected declaration _D_ ([expr.const]{.sref}) that defines _C_ and has properties as follows:

- [#.#]{.pnum} [...]
- [#.#]{.pnum} [...]
- [#.#]{.pnum} [...]
- [#.#]{.pnum} If _C_ is a specialization of a templated class _T_, and _C_ is not a local class, then _D_ is an explicit specialization of _T_.
- [#.#]{.pnum} [...]
- [#.#]{.pnum} [...]

[#]{.pnum} _Returns_: `class_type`.

::: add
[?]{.pnum} _Remarks_: If _C_ is a specialization of a templated class and it has not been instantiated, _C_ is treated as an explicit specialization.
:::
:::


## [US 227-346](https://github.com/cplusplus/nbballot/issues/921) and [US 229-347](https://github.com/cplusplus/nbballot/issues/922)

::: jwordinglist

1. Edit [exec.spawn.future]{.sref} as indicated:

[7]{.pnum} Let `$spawn-future-state$` be the exposition-only class template:

```cpp
namespace std::execution {
  template<class Alloc, scope_token Token, sender Sender, class Env>
  struct $spawn-future-state$                                                 // exposition only
    : $spawn-future-state-base$<completion_signatures_of_t<$future-spawned-sender$<Sender, Env>>> {
    using $sigs-t$ =                                                          // exposition only
      completion_signatures_of_t<$future-spawned-sender$<Sender, Env>>;
    using $receiver-t$ =                                                      // exposition only
      $spawn-future-receiver$<$sigs-t$>;
    using $op-t$ =                                                            // exposition only
      connect_result_t<$future-spawned-sender$<Sender, Env>, $receiver-t$>;

    $spawn-future-state$(Alloc alloc, Sender&& sndr, Token token, Env env)    // exposition only
      : alloc(std::move(alloc)),
        op(connect(
          write_env($stop-when$(std::forward<Sender>(sndr), ssource.get_token()), std::move(env)),
          $receiver-t$(this))),
        token(std::move(token)),
        associated(token.try_associate()) {
          if (associated)
            start(op);
          else
            set_stopped($receiver-t$(this));
        }

    void complete() noexcept override;                                      // exposition only
    void consume(receiver auto& rcvr) noexcept;                             // exposition only
    void abandon() noexcept;                                                // exposition only

  private:
    @[`using $alloc-t$ =                                                         // exposition only`]{.diffdel}@
      @[`allocator_traits<Alloc>::template rebind_alloc<$spawn-future-state$>;`]{.diffdel}@

    @[`Alloc`<-`$alloc-t$`]{.indel}@ alloc;                                                          // exposition only
    $ssource-t$ $ssource$;                                                      // exposition only
    $op-t$ $op$;                                                                // exposition only
    Token $token$;                                                            // exposition only
    bool $associated$;                                                        // exposition only

    void $destroy$() noexcept;                                                // exposition only
  };

  @[`template<class Alloc, scope_token Token, sender Sender, class Env>`]{.diffins}@
  @[`$spawn-future-state$(Alloc alloc, Sender&& sndr, Token token, Env env) -> $spawn-future-state$<Alloc, Token, Sender, Env>`;]{.diffins}@
}
```

[...]

::: itemdecl
```cpp
void $destroy$() noexcept;
```

[12]{.pnum} _Effects_: Equivalent to:

::: bq
```diff
 auto token = std::move(this->$token$);
 bool associated = this->$associated$;

 {

-  auto alloc = std::move(this->$alloc$);
-
-  allocator_traits<$alloc-t$>::destroy(alloc, this);
-  allocator_traits<$alloc-t$>::deallocate(alloc, this, 1);

+  using traits = allocator_traits<Alloc>::template rebind_traits<$spawn-future-state$>;
+  typename traits::allocator_type alloc(std::move(this->$alloc$));
+  traits::destroy(alloc, this);
+  traits::deallocate(alloc, this, 1);
 }

 if (associated)
   token.disassociate();
```
:::

:::

[...]

[16]{.pnum} The expression `spawn_future(sndr, token, env)` has the following effects:

- [#.#]{.pnum} Uses `alloc` to allocate and construct an object `s` of [a type that is a specialization of `@_spawn-future-state_@`]{.diffdel} [type `decltype($spawn-future-state$(alloc, token.wrap(sndr), token, senv))`]{.diffins} from `alloc`, `token.wrap(sndr)`, `token`, and `senv`. If an exception is thrown then any constructed objects are destroyed and any allocated memory is deallocated.
- [#.#]{.pnum} Constructs an object `u` of a type that is a specialization of `unique_ptr` such that:
  - [#.#.#]{.pnum} `u.get()` is equal to the address of `s`, and
  - [#.#.#]{.pnum}` u.get_deleter()(u.release())` is equivalent to `u.release()->$abandon$()`.
- [#.#]{.pnum} Returns `$make-sender$(spawn_future, std​::​move(u))`.

2. Edit [exec.spawn]{.sref} as indicated:

[5]{.pnum} Let `$spawn-state$` be the exposition-only class template:

```cpp
namespace std::execution {
  template<class Alloc, scope_token Token, sender Sender>
  struct $spawn-state$ : $spawn-state-base$ {                   // exposition only
    using $op-t$ = connect_result_t<Sender, $spawn-receiver$>;  // exposition only

    $spawn-state$(Alloc alloc, Sender&& sndr, Token token);   // exposition only
    void complete() noexcept override;                      // exposition only
    void run();                                             // exposition only

  private:
    @[`using $alloc-t$ =                                         // exposition only`]{.diffdel}@
      @[`allocator_traits<Alloc>::template rebind_alloc<$spawn-state$>;`]{.diffdel}@

    @[`Alloc`<-`$alloc-t$`]{.indel}@ $alloc$;                                          // exposition only
    $op-t$ $op$;                                                // exposition only
    Token $token$;                                            // exposition only

    void $destroy$() noexcept;                                // exposition only
  };
}
```

[...]

::: itemdecl
```cpp
void $destroy$() noexcept;
```

[9]{.pnum} _Effects_: Equivalent to:

::: bq
```diff
-  auto alloc = std::move(this->$alloc$);
-
-  allocator_traits<$alloc-t$>::destroy(alloc, this);
-  allocator_traits<$alloc-t$>::deallocate(alloc, this, 1);

+  using traits = allocator_traits<Alloc>::template rebind_traits<$spawn-state$>;
+  typename traits::allocator_type alloc(std::move(this->$alloc$));
+  traits::destroy(alloc, this);
+  traits::deallocate(alloc, this, 1);
```
:::
:::

[11]{.pnum} The expression `spawn(sndr, token, env)` is of type `void` and has the following effects:

- [#.#]{.pnum} Uses `alloc` to allocate and construct an object `o` of type [that is a specialization of `$spawn-state$`]{.diffdel} [`decltype($spawn-state$(alloc, write_env(token.wrap(sndr), senv), token)`]{.diffins} from `alloc`, `write_env(token.wrap(sndr), senv)`, and `token` and then invokes `o.$run$()`. If an exception is thrown then any constructed objects are destroyed and any allocated memory is deallocated.

:::

## [US 221-339](https://github.com/cplusplus/nbballot/issues/914)

[This wording is relative to the working draft after the application of the resolution of US 209-232.
]{.ednote}

Edit [exec.bulk]{.sref} as indicated:

[5]{.pnum} The exposition-only class template `$impls-for$` ([exec.snd.expos]{.sref}) is specialized for `bulk_chunked_t` as follows:

```cpp
namespace std::execution {
  template<>
  struct $impls-for$<bulk_chunked_t> : $default-impls$ {
    static constexpr auto $complete$ = $see below$;

    template<class Sndr, class... Env>
      static consteval void $check-types$();
  };
}
```

The member `$impls-for$<bulk_chunked_t>​::@_​complete_@` is initialized with a callable object equivalent to the following lambda:

[...]

::: add

::: itemdecl

```cpp
template<class Sndr, class... Env>
  static consteval void $check-types$();
```

[?]{.pnum} _Effects_: Equivalent to:

::: bq
```cpp
auto cs = get_completion_signatures<$child-type$<Sndr>, $FWD-ENV-T$(Env)...>();
auto fn = []<class... Ts>(set_value_t(*)(Ts...)) {
  using data_type = $data-type$<Sndr>;
  if constexpr (!invocable<remove_cvref_t<$child-type$<data_type>&,
                           remove_cvref_t<$data-type$<data_type>>, Ts&...>)
    throw $unspecified-exception$();
};
cs.$for-each$($overload-set$(fn, [](auto){}));
```
:::

:::

:::

[6]{.pnum} The exposition-only class template `$impls-for$` ([exec.snd.expos]{.sref}) is specialized for `bulk_unchunked_t` as follows:

```cpp
namespace std::execution {
  template<>
  struct $impls-for$<bulk_unchunked_t> : $default-impls$ {
    static constexpr auto complete = see below;

    @[`template<class Sndr, class... Env>`]{.diffins}@
      @[`static consteval void $check-types$();`]{.diffins}@
  };
}
```

The member `$impls-for$<bulk_unchunked_t>​::@_​complete_@` is initialized with a callable object equivalent to the following lambda:

[...]

::: itemdecl
```cpp
template<class Sndr, class... Env>
  static consteval void $check-types$();
```

[#]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
auto cs = get_completion_signatures<$child-type$<Sndr>, $FWD-ENV-T$(Env)...>();
auto fn = []<class... Ts>(set_value_t(*)(Ts...)) {
  @[`using data_type = $data-type$<Sndr>;`]{.diffins}@
  if constexpr (!invocable<@[`remove_cvref_t<$child-type$<data_type>>&,`]{.diffins}@
                           remove_cvref_t<$data-type$<@[data_type<-Sndr]{.indel}@>>, Ts&...>)
    throw $unspecified-exception$();
};
cs.$for-each$($overload-set$(fn, [](auto){}));
```
:::
:::

## [US 225-341](https://github.com/cplusplus/nbballot/issues/916)

::: jwordinglist

1. Edit [tuple.tuple.general]{.sref} as indicated:

```cpp
namespace std {
  template<class... Types>
  class tuple {
  public:
    // [tuple.cnstr], tuple construction
    constexpr explicit($see below$) tuple();
    constexpr explicit($see below$) tuple(const Types&...) @[`noexcept($see below$)`]{.diffins}@;         // only if sizeof...(Types) >= 1
    template<class... UTypes>
      constexpr explicit($see below$) tuple(UTypes&&...) @[`noexcept($see below$)`]{.diffins}@;           // only if sizeof...(Types) >= 1

    tuple(const tuple&) = default;
    tuple(tuple&&) = default;

    template<class... UTypes>
      constexpr explicit($see below$) tuple(tuple<UTypes...>&);
    template<class... UTypes>
      constexpr explicit($see below$) tuple(const tuple<UTypes...>&);
    template<class... UTypes>
      constexpr explicit($see below$) tuple(tuple<UTypes...>&&);
    template<class... UTypes>
      constexpr explicit($see below$) tuple(const tuple<UTypes...>&&);

    template<class U1, class U2>
      constexpr explicit($see below$) tuple(pair<U1, U2>&);         // only if sizeof...(Types) == 2
    template<class U1, class U2>
      constexpr explicit($see below$) tuple(const pair<U1, U2>&);   // only if sizeof...(Types) == 2
    template<class U1, class U2>
      constexpr explicit($see below$) tuple(pair<U1, U2>&&);        // only if sizeof...(Types) == 2
    template<class U1, class U2>
      constexpr explicit($see below$) tuple(const pair<U1, U2>&&);  // only if sizeof...(Types) == 2

    template<tuple-like UTuple>
      constexpr explicit($see below$) tuple(UTuple&&);

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
    template<class Alloc, class... UTypes>
      constexpr explicit($see below$)
        tuple(allocator_arg_t, const Alloc& a, tuple<UTypes...>&);
    template<class Alloc, class... UTypes>
      constexpr explicit($see below$)
        tuple(allocator_arg_t, const Alloc& a, const tuple<UTypes...>&);
    template<class Alloc, class... UTypes>
      constexpr explicit($see below$)
        tuple(allocator_arg_t, const Alloc& a, tuple<UTypes...>&&);
    template<class Alloc, class... UTypes>
      constexpr explicit($see below$)
        tuple(allocator_arg_t, const Alloc& a, const tuple<UTypes...>&&);
    template<class Alloc, class U1, class U2>
      constexpr explicit($see below$)
        tuple(allocator_arg_t, const Alloc& a, pair<U1, U2>&);
    template<class Alloc, class U1, class U2>
      constexpr explicit($see below$)
        tuple(allocator_arg_t, const Alloc& a, const pair<U1, U2>&);
    template<class Alloc, class U1, class U2>
      constexpr explicit($see below$)
        tuple(allocator_arg_t, const Alloc& a, pair<U1, U2>&&);
    template<class Alloc, class U1, class U2>
      constexpr explicit($see below$)
        tuple(allocator_arg_t, const Alloc& a, const pair<U1, U2>&&);

    template<class Alloc, $tuple-like$ UTuple>
      constexpr explicit($see below$) tuple(allocator_arg_t, const Alloc& a, UTuple&&);

    // [tuple.assign], tuple assignment
    constexpr tuple& operator=(const tuple&);
    constexpr const tuple& operator=(const tuple&) const;
    constexpr tuple& operator=(tuple&&) noexcept(see below);
    constexpr const tuple& operator=(tuple&&) const;

    template<class... UTypes>
      constexpr tuple& operator=(const tuple<UTypes...>&);
    template<class... UTypes>
      constexpr const tuple& operator=(const tuple<UTypes...>&) const;
    template<class... UTypes>
      constexpr tuple& operator=(tuple<UTypes...>&&);
    template<class... UTypes>
      constexpr const tuple& operator=(tuple<UTypes...>&&) const;

    template<class U1, class U2>
      constexpr tuple& operator=(const pair<U1, U2>&);          // only if sizeof...(Types) == 2
    template<class U1, class U2>
      constexpr const tuple& operator=(const pair<U1, U2>&) const;
                                                                // only if sizeof...(Types) == 2
    template<class U1, class U2>
      constexpr tuple& operator=(pair<U1, U2>&&);               // only if sizeof...(Types) == 2
    template<class U1, class U2>
      constexpr const tuple& operator=(pair<U1, U2>&&) const;   // only if sizeof...(Types) == 2

    template<$tuple-like$ UTuple>
      constexpr tuple& operator=(UTuple&&);
    template<$tuple-like$ UTuple>
      constexpr const tuple& operator=(UTuple&&) const;

    // [tuple.swap], tuple swap
    constexpr void swap(tuple&) noexcept($see below$);
    constexpr void swap(const tuple&) const noexcept($see below$);
  };

  template<class... UTypes>
    tuple(UTypes...) -> tuple<UTypes...>;
  template<class T1, class T2>
    tuple(pair<T1, T2>) -> tuple<T1, T2>;
  template<class Alloc, class... UTypes>
    tuple(allocator_arg_t, Alloc, UTypes...) -> tuple<UTypes...>;
  template<class Alloc, class T1, class T2>
    tuple(allocator_arg_t, Alloc, pair<T1, T2>) -> tuple<T1, T2>;
  template<class Alloc, class... UTypes>
    tuple(allocator_arg_t, Alloc, tuple<UTypes...>) -> tuple<UTypes...>;
}
```

1. Edit [tuple.cnstr]{.sref} as indicated:

::: itemdecl

```cpp
constexpr explicit($see below$) tuple(const Types&...) @[`noexcept((is_nothrow_copy_constructible_v<Types> && ...))`]{.diffins}@;
```

[9]{.pnum} _Constraints_: [...]

[#]{.pnum} _Effects_: [...]

[#]{.pnum} _Remarks_: [...]

```cpp
template<class... UTypes>
  constexpr explicit($see below$) tuple(UTypes&&... u) @[`noexcept((is_nothrow_constructible_v<Types, UTypes> && ...))`]{.diffins}@;
```

[#]{.pnum} [...]

[#]{.pnum} _Constraints_: [...]

[#]{.pnum} _Effects_: [...]

[#]{.pnum} _Remarks_: [...]

:::

:::
