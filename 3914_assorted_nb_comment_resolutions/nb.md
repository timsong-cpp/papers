---
title: Assorted NB comment resolutions for Kona 2025
document: P3914R0
date: 2025-11-04
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
---

# Introduction

This paper provides wording to resolve the following national body comments on the C++26 CD:

- [US 160-260](https://github.com/cplusplus/nbballot/issues/835)
- [US 209-332](https://github.com/cplusplus/nbballot/issues/907)
- [US 228-348](https://github.com/cplusplus/nbballot/issues/923)
- [US 263-396](https://github.com/cplusplus/nbballot/issues/971)
- [US 265-398](https://github.com/cplusplus/nbballot/issues/973)
- [US 266-399](https://github.com/cplusplus/nbballot/issues/974)
- [US 112-172](https://github.com/cplusplus/nbballot/issues/990)
- [US 130-193](https://github.com/cplusplus/nbballot/issues/762)

# Wording

This wording is relative to [@N5014] except where noted.

## [US 160-260](https://github.com/cplusplus/nbballot/issues/835)

[During offline discussion, Ruslan Arutyunyan pointed out other issues with the specification of `unique` and `unique_copy` and suggested an elegant wording strategy to address them. The wording below incorporates his suggestions.]{.draftnote}

Edit [alg.unique]{.sref} as indicated:

::: itemdecl

```cpp
template<class ForwardIterator>
  constexpr ForwardIterator unique(ForwardIterator first, ForwardIterator last);
template<class ExecutionPolicy, class ForwardIterator>
  ForwardIterator unique(ExecutionPolicy&& exec,
                         ForwardIterator first, ForwardIterator last);

template<class ForwardIterator, class BinaryPredicate>
  constexpr ForwardIterator unique(ForwardIterator first, ForwardIterator last,
                                   BinaryPredicate pred);
template<class ExecutionPolicy, class ForwardIterator, class BinaryPredicate>
  ForwardIterator unique(ExecutionPolicy&& exec,
                         ForwardIterator first, ForwardIterator last,
                         BinaryPredicate pred);

template<permutable I, sentinel_for<I> S, class Proj = identity,
         indirect_equivalence_relation<projected<I, Proj>> C = ranges::equal_to>
  constexpr subrange<I> ranges::unique(I first, S last, C comp = {}, Proj proj = {});
template<forward_range R, class Proj = identity,
         indirect_equivalence_relation<projected<iterator_t<R>, Proj>> C = ranges::equal_to>
  requires permutable<iterator_t<R>>
  constexpr borrowed_subrange_t<R>
    ranges::unique(R&& r, C comp = {}, Proj proj = {});

template<$execution-policy$ Ep, random_access_iterator I, sized_sentinel_for<I> S,
         class Proj = identity,
         indirect_equivalence_relation<projected<I, Proj>> C = ranges::equal_to>
  requires permutable<I>
  subrange<I> ranges::unique(Ep&& exec, I first, S last, C comp = {}, Proj proj = {});
template<$execution-policy$ Ep, $sized-random-access-range$ R, class Proj = identity,
         indirect_equivalence_relation<projected<iterator_t<R>, Proj>> C = ranges::equal_to>
  requires permutable<iterator_t<R>>
  borrowed_subrange_t<R> ranges::unique(Ep&& exec, R&& r, C comp = {}, Proj proj = {});
```

[#]{.pnum} Let `pred` be `equal_to{}` for the overloads with no parameter `pred`, 
and let _E_[(`i`)]{.diffins} be

- [#.?]{.pnum} [`false` if `i` is equal to `first`; otherwise]{.diffins} 
- [#.1]{.pnum} `bool(pred(*(i - 1), *i))` for the overloads in namespace `std`;
- [#.#]{.pnum} `bool(invoke(comp, invoke(proj, *(i - 1)), invoke(proj, *i)))` for the overloads in namespace `ranges`.

[#]{.pnum} _Preconditions_: For the overloads in namespace `std`, `pred` is an
equivalence relation and the type of `*first` meets the _Cpp17MoveAssignable_
requirements ([tab:cpp17.moveassignable]{.sref}).

[#]{.pnum} _Effects:_ [For a nonempty range, e]{.diffdel}[E]{.diffins}liminates all [but the first element from every consecutive group of equivalent]{.diffdel} elements referred to by the iterator `i` in the range `[first @[+ 1]{.diffdel}@, last)` for which _E_[(`i`)]{.diffins} is `true`.

[#]{.pnum} _Returns:_ Let `j` be the end of the resulting range. Returns:

- [#.#]{.pnum} `j` for the overloads in namespace `std`.
- [#.#]{.pnum} `{j, last}` for the overloads in namespace `ranges`.


[#]{.pnum} _Complexity:_ For nonempty ranges, exactly `(last - first) - 1` applications of the corresponding predicate and no more than twice as many applications of any projection.

```cpp
template<class InputIterator, class OutputIterator>
  constexpr OutputIterator
    unique_copy(InputIterator first, InputIterator last,
                OutputIterator result);
template<class ExecutionPolicy, class ForwardIterator1, class ForwardIterator2>
  ForwardIterator2
    unique_copy(ExecutionPolicy&& exec,
                ForwardIterator1 first, ForwardIterator1 last,
                ForwardIterator2 result);

template<class InputIterator, class OutputIterator,
         class BinaryPredicate>
  constexpr OutputIterator
    unique_copy(InputIterator first, InputIterator last,
                OutputIterator result, BinaryPredicate pred);
template<class ExecutionPolicy, class ForwardIterator1, class ForwardIterator2,
         class BinaryPredicate>
  ForwardIterator2
    unique_copy(ExecutionPolicy&& exec,
                ForwardIterator1 first, ForwardIterator1 last,
                ForwardIterator2 result, BinaryPredicate pred);

template<input_iterator I, sentinel_for<I> S, weakly_incrementable O, class Proj = identity,
         indirect_equivalence_relation<projected<I, Proj>> C = ranges::equal_to>
  requires indirectly_copyable<I, O> &&
           (forward_iterator<I> ||
            (input_iterator<O> && same_as<iter_value_t<I>, iter_value_t<O>>) ||
            indirectly_copyable_storable<I, O>)
  constexpr ranges::unique_copy_result<I, O>
    ranges::unique_copy(I first, S last, O result, C comp = {}, Proj proj = {});
template<input_range R, weakly_incrementable O, class Proj = identity,
         indirect_equivalence_relation<projected<iterator_t<R>, Proj>> C = ranges::equal_to>
  requires indirectly_copyable<iterator_t<R>, O> &&
           (forward_iterator<iterator_t<R>> ||
            (input_iterator<O> && same_as<range_value_t<R>, iter_value_t<O>>) ||
            indirectly_copyable_storable<iterator_t<R>, O>)
  constexpr ranges::unique_copy_result<borrowed_iterator_t<R>, O>
    ranges::unique_copy(R&& r, O result, C comp = {}, Proj proj = {});

template<$execution-policy$ Ep, random_access_iterator I, sized_sentinel_for<I> S,
         random_access_iterator O, sized_sentinel_for<O> OutS, class Proj = identity,
         indirect_equivalence_relation<projected<I, Proj>> C = ranges::equal_to>
  requires indirectly_copyable<I, O>
  ranges::unique_copy_result<I, O>
    ranges::unique_copy(Ep&& exec, I first, S last, O result, OutS result_last,
                        C comp = {}, Proj proj = {});
template<$execution-policy$ Ep, $sized-random-access-range$ R, $sized-random-access-range$ OutR,
         class Proj = identity,
         indirect_equivalence_relation<projected<iterator_t<R>, Proj>> C = ranges::equal_to>
  requires indirectly_copyable<iterator_t<R>, iterator_t<OutR>>
  ranges::unique_copy_result<borrowed_iterator_t<R>, borrowed_iterator_t<OutR>>
    ranges::unique_copy(Ep&& exec, R&& r, OutR&& result_r, C comp = {}, Proj proj = {});
```

[#]{.pnum} Let `pred` be `equal_to{}` for the overloads in namespace `std` with no parameter `pred`, and let _E_(`i`) be

- [#.?]{.pnum} [`false` if `i` is equal to `first`; otherwise]{.diffins} 
- [#.1]{.pnum} `bool(pred(*i, *(i - 1)))` for the overloads in namespace `std`;
- [#.#]{.pnum} `bool(invoke(comp, invoke(proj, *i), invoke(proj, *(i - 1))))` for the overloads in namespace `ranges`.

[#]{.pnum} Let:

- [#.#]{.pnum} _M_ be the number of iterators `i` in the range `[first @[+ 1]{.diffdel}@, last)` for which _E_(`i`) is `false`;
- [#.#]{.pnum} `result_last` be `result` + _M_ [+ `1`]{.diffdel} for the overloads with no parameter `result_last` or `result_r`;
- [#.#]{.pnum} _N_ be min(_M_ [+ 1]{.diffdel}, `result_last` - `result`) 

[#]{.pnum} _Mandates:_ `*first` is writable ([iterator.requirements.general]{.sref}) to `result`.
 
[#]{.pnum} _Preconditions:_

- [#.#]{.pnum} The ranges `[first, last)` and `[result, result + $N$)` do not overlap.
- [#.#]{.pnum} For the overloads in namespace `std`:
  - [#.#.#]{.pnum} The comparison function is an equivalence relation.
  - [#.#.#]{.pnum} For the overloads with no `ExecutionPolicy`, let `T` be the value type of `InputIterator`. If `InputIterator` models `forward_iterator` ([iterator.concept.forward]{.sref}), then there are no additional requirements for `T`. Otherwise, if `OutputIterator` meets the _Cpp17ForwardIterator_ requirements and its value type is the same as `T`, then `T` meets the _Cpp17CopyAssignable_ ([tab:cpp17.copyassignable]{.sref}) requirements. Otherwise, `T` meets both the _Cpp17CopyConstructible_ ([tab:cpp17.copyconstructible]{.sref}) and _Cpp17CopyAssignable_ requirements.
  
[For the parallel algorithm overloads in namespace `std`, there can be a performance cost if the value type of `ForwardIterator1` does not meet both the _Cpp17CopyConstructible_ and _Cpp17CopyAssignable_ requirements. For the parallel algorithm overloads in namespace `ranges`, there can be a performance cost if `iter_value_t<I>` does not model `copyable`.]{.note}

[#]{.pnum} _Effects:_ Copies only the first [_N_]{.diffins} [element from N consecutive groups of equivalent]{.diffdel} elements referred to by the iterator `i` in the range `[first @[+ 1]{.diffdel}@, last)` for which _E_(`i`) [holds]{.diffdel} [is `false`]{.diffins} into the range `[result, result + $N$)`.

[#]{.pnum} _Returns:_

- [#.#]{.pnum} `result + $N$` for the overloads in namespace `std`.
- [#.#]{.pnum} `{last, result + $N$}` for the overloads in namespace `ranges`,
  if _N_ is equal to _M_ [+ 1]{.diffdel}.
- [#.#]{.pnum} Otherwise, `{j, result_last}` for the overloads in namespace `ranges`, where `j` is the iterator in `[first @[+ 1]{.diffdel}@, last)` for which _E_(`j`) is `false` and there are exactly _N_ [- 1]{.diffdel} iterators `i` in `[first @[+ 1]{.diffdel}@, j)` for which _E_(`i`) is `false`.

[#]{.pnum} _Complexity:_ At most `last - first - 1` applications of the corresponding predicate and no more than twice as many applications of any projection.

:::

## [US 209-332](https://github.com/cplusplus/nbballot/issues/907)

::: wordinglist

- Add the following to the end of [exec.snd.general]{.sref}:
  
::: add

[?]{.pnum} Various function templates in subclause [exec.snd]{.sref} can throw an exception of type `$unspecified-exception$`. Each such exception object is of an unspecified type such that a _handler_ of type `exception` matches ([except.handle]{.sref}) the exception object but a _handler_ of type `dependent_sender_error` does not.
[There is no requirement that two such exception objects have the same type.]{.note}

:::

- Edit [exec.snd.expos]{.sref} as indicated:

[47]{.pnum}

```cpp
struct $not-a-sender$ {
  using sender_concept = sender_t;

  template<class Sndr>
    static consteval auto get_completion_signatures() -> completion_signatures<> {
      throw $unspecified-exception$();
  }
};
```

[where `$unspecified-exception$` is a type derived from `exception`.]{.diffdel}

[48]{.pnum}

```cpp
constexpr void $decay-copyable-result-datums$(auto cs) {
  cs.$for-each$([]<class Tag, class... Ts>(Tag(*)(Ts...)) {
    if constexpr (!(is_constructible_v<decay_t<Ts>, Ts> &&...))
      throw $unspecified-exception$();
  });
}
```

[where `$unspecified-exception$` is a type derived from `exception`.]{.diffdel}

- Edit [exec.read.env]{.sref} as indicated:

::: itemdecl

```cpp
template<class Sndr, class Env>
  static consteval void check-types();
```

[4]{.pnum} Let `Q` be `decay_t<$data-type$<Sndr>>`.

[#]{.pnum} _Throws:_ An exception of [type `$unspecified-exception$` ([exec.snd.general]{.sref})]{.diffins} [an unspecified type derived from `exception`]{.diffdel} if the expression `Q()(env)` is ill-formed or has type `void`, where `env` is an lvalue subexpression whose type is `Env`.

:::

- Edit [exec.then]{.sref} as indicated:

::: itemdecl

```cpp
template<class Sndr, class... Env>
  static consteval void $check-types$();
```

[5]{.pnum} _Effects:_ Equivalent to:

::: bq

```cpp
auto cs = get_completion_signatures<$child-type$<Sndr>, $FWD-ENV-T$(Env)...>();
auto fn = []<class... Ts>(set_value_t(*)(Ts...)) {
  if constexpr (!invocable<remove_cvref_t<$data-type$<Sndr>>, Ts...>)
    throw $unspecified-exception$();
};
cs.$for-each$($overload-set${fn, [](auto){}});
```

:::

[where `$unspecified-exception$` is a type derived from `exception`.]{.diffdel}

:::

- Edit [exec.let]{.sref} as indicated:

::: itemdecl

```cpp
template<class Sndr, class... Env>
  static consteval void $check-types$();
```

[7]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
using LetFn = remove_cvref_t<$data-type$<Sndr>>;
auto cs = get_completion_signatures<$child-type$<Sndr>, $FWD-ENV-T$(Env)...>();
auto fn = []<class... Ts>($decayed-typeof$<$set-cpo$>(*)(Ts...)) {
  if constexpr (!$is-valid-let-sender$)   // see below
    throw $unspecified-exception$();
};
cs.$for-each$($overload-set$(fn, [](auto){}));
```
:::

[where `$unspecified-exception$` is a type derived from `exception`, and]{.diffdel}
where `$is-valid-let-sender$` is `true` if and only if all of the following are `true`:

- [#.#]{.pnum} `(constructible_from<decay_t<Ts>, Ts> && ...)`
- [#.#]{.pnum} `invocable<LetFn, decay_t<Ts>&...>`
- [#.#]{.pnum} `sender<invoke_result_t<LetFn, decay_t<Ts>&...>>`
- [#.#]{.pnum} `sizeof...(Env) == 0 || sender_in<invoke_result_t<LetFn, decay_t<Ts>&...>, $env-t$...>`
  
where `$env-t$` is the pack `decltype($let-cpo$.transform_env(declval<Sndr>(), declval<Env>()))`.

:::

- Edit [exec.bulk]{.sref} as indicated:

::: itemdecl

```cpp
template<class Sndr, class... Env>
  static consteval void $check-types$();
```

[7]{.pnum} _Effects:_ Equivalent to:

::: bq
```cpp
auto cs = get_completion_signatures<$child-type$<Sndr>, $FWD-ENV-T$(Env)...>();
auto fn = []<class... Ts>(set_value_t(*)(Ts...)) {
  if constexpr (!invocable<remove_cvref_t<$data-type$<Sndr>>, Ts&...>)
    throw $unspecified-exception$();
};
cs.$for-each$($overload-set$(fn, [](auto){}));
```
:::

[where `$unspecified-exception$` is a type derived from `exception`.]{.diffdel}

:::

- Edit [exec.when.all]{.sref} as indicated:

::: itemdecl

```cpp
template<class Sndr, class... Env>
  static consteval void $check-types$();
```

[7]{.pnum} Let `Is` be the pack of integral template arguments of the `integer_sequence` specialization denoted by `$indices-for$<Sndr>`.

[#]{.pnum} _Effects:_ Equivalent to:

::: bq

```cpp
auto fn = []<class Child>() {
  auto cs = get_completion_signatures<Child, $when-all-env$<Env>...>();
  if constexpr (cs.$count-of$(set_value) >= 2)
    throw $unspecified-exception$();
  $decay-copyable-result-datums$(cs); // see [exec.snd.expos]
};
(fn.template operator()<$child-type$<Sndr, Is>>(), ...);
```
:::

[where `$unspecified-exception$` is a type derived from `exception`.]{.diffdel}

[#]{.pnum} Throws: Any exception thrown as a result of evaluating the _Effects_, or an exception of [type `$unspecified-exception$` ([exec.snd.general]{.sref})]{.diffins} [an unspecified type derived from `exception`]{.diffdel} when `CD` is ill-formed.

:::

- Edit [exec.stopped.opt]{.sref} as indicated:

[3]{.pnum} The exposition-only class template `$impls-for$` ([exec.snd.expos]{.sref}) is specialized for `stopped_as_optional_t` as follows:

```cpp
namespace std::execution {
  template<>
  struct $impls-for$<stopped_as_optional_t> : $default-impls$ {
    template<class Sndr, class... Env>
      static consteval void $check-types$() {
        $default-impls$::$check-types$<Sndr, Env...>();
        if constexpr (!requires {
          requires (!same_as<void, s$ingle-sender-value-type$<$child-type$<Sndr>,
                                                            $FWD-ENV-T$(Env)...>>); })
          throw $unspecified-exception$();
      }
  };
}
```
[where `$unspecified-exception$` is a type derived from `exception`.]{.diffdel}
:::


## [US 228-348](https://github.com/cplusplus/nbballot/issues/923)

[The font of `$ssource-t$` is corrected by [PR 8404](https://github.com/cplusplus/draft/pull/8404).]{.draftnote}

Edit [exec.spawn.future]{.sref} as indicated:

[6]{.pnum} Let `$ssource-t$` be an unspecified type that models `$stoppable-source$` and [`default_initializable`, such that a default-initialized object of type `$ssource-t$` has an associated stop state. Let]{.diffins} [let]{.diffdel} `$ssource$` be an lvalue of type `$ssource-t$`. Let `$stoken-t$` be `decltype(ssource.get_token())`. Let `$future-spawned-sender$` be the alias template:

```cpp
template<sender Sender, class Env>
using $future-spawned-sender$ =                                   // exposition only
  decltype(write_env($stop-when$(declval<Sender>(), declval<$stoken-t$>()), declval<Env>()));
```

## [US 263-396](https://github.com/cplusplus/nbballot/issues/971)

[LWG wishes to allow an implementation that returns an object of static storage duration under appropriate conditions.]{.draftnote}

Edit [exec.sysctxrepl.query]{.sref} as indicated:

:::itemdecl

```cpp
shared_ptr<parallel_scheduler_backend> query_parallel_scheduler_backend();
```

[#]{.pnum} `query_parallel_scheduler_backend()` returns the implementation object for a parallel scheduler.

[#]{.pnum} _Returns:_ [A non-null shared pointer]{.diffdel}[An object]{.diffins} [`p`, such that `p.get()` points to a `parallel_scheduler_backend` object that is a base-class subobject of some most derived object `o` within its lifetime. The lifetime of `o` does not end as long as there exists a `shared_ptr` object `q` within its lifetime such that `q.owner_equal(p)` is `true`.]{.diffins} [to an object that implements the `parallel_scheduler_backend` interface.]{.diffdel}

[#]{.pnum} _Remarks:_ This function is replaceable ([dcl.fct.def.replace]{.sref}).

:::

## [US 265-398](https://github.com/cplusplus/nbballot/issues/973) and [US 266-399](https://github.com/cplusplus/nbballot/issues/974)

Edit [exec.sysctxrepl.psb]{.sref} as indicated:

::: itemdecl
```cpp
virtual void schedule(receiver_proxy& r, span<byte> s) noexcept = 0;
```

[#]{.pnum} _Preconditions:_ The ends of the lifetime[s]{.diffdel} of `*this`, [of the lifetime of]{.diffins} the object referred to by `r`, and [of the duration of]{.diffins} any storage referenced by `s` all happen after the beginning of the evaluation of the call to `set_value`, `set_error`, or [`set_done`]{.diffdel} [`set_stopped`]{.diffins} on `r` (see below).

[#]{.pnum} _Effects:_ [&hellip;]

[#]{.pnum} _Remarks:_ [&hellip;]

```cpp
virtual void schedule_bulk_chunked(size_t n, bulk_item_receiver_proxy& r,
                                   span<byte> s) noexcept = 0;
```

[#]{.pnum} _Preconditions:_ The ends of the lifetime[s]{.diffdel} of `*this`, [of the lifetime of]{.diffins} the object referred to by `r`, and [of the duration of]{.diffins} any storage referenced by `s` all happen after the beginning of the evaluation of [the call to `set_value`, `set_error`, or `set_stopped` on `r` (see below)]{.diffins} [one of the expressions below]{.diffdel}.

[#]{.pnum} _Effects:_ [&hellip;]

[#]{.pnum} _Remarks:_ [&hellip;]

```cpp
virtual void schedule_bulk_unchunked(size_t n, bulk_item_receiver_proxy& r,
                                     span<byte> s) noexcept = 0;
```

[#]{.pnum} _Preconditions:_ The ends of the lifetime[s]{.diffdel} of `*this`, [of the lifetime of]{.diffins} the object referred to by `r`, and [of the duration of]{.diffins} any storage referenced by `s` all happen after the beginning of the evaluation of [the call to `set_value`, `set_error`, or `set_stopped` on `r` (see below)]{.diffins} [one of the expressions below]{.diffdel}.

[#]{.pnum} _Effects:_ [&hellip;]

[#]{.pnum} _Remarks:_ [&hellip;]

:::

## [US 112-172](https://github.com/cplusplus/nbballot/issues/990)

Edit [meta.reflection.extract]{.sref} as indicated:

::: itemdecl

```cpp
template<class T>
  consteval T $extract-value$(info r);    // exposition only
```

[8]{.pnum} Let `U` be the type of the value or object that `r` represents.

[#]{.pnum} _Returns:_ `static_cast<T>([:`_R_`:])`, where _R_ is a constant expression of type `info` such that _R_ ` == r` is `true`.

[#]{.pnum} _Throws:_ `meta​::​exception` unless

- [#.#]{.pnum} `U` is a pointer type, `T` and `U` are either similar ([conv.qual]{.sref}) or both function pointer types, and `is_convertible_v<U, T>` is `true`,
- [#.#]{.pnum} `U` is not a pointer type and the cv-unqualified types of `T` and `U` are the same,
- [#.#]{.pnum} `U` is an array type, `T` is a pointer type, [`remove_extent_t<U>*` and `T` are similar types,]{.diffins} and the value `r` represents is convertible to `T`, or
- [#.#]{.pnum} `U` is a closure type, `T` is a function pointer type, and the value that `r` represents is convertible to `T`.

:::

## [US 130-193](https://github.com/cplusplus/nbballot/issues/762)

::: draftnote

There are a few cases to consider here.

1. A _Mandates:_ clause was violated (e.g., `make_signed(^^float)`)
2. A member type alias `type` does not exist (e.g., `invoke_result(^^int, {})`)
3. A member `value` does not exist, or has the wrong type, or is inaccessible, etc. (`tuple_size(^^int)`)
4. [The general rule against incomplete types](https://eel.is/c++draft/meta.rqmts#5) is violated.
5. A precondition of a type trait is violated.
6. Evaluation of the type trait would trigger a hard error outside the trait.

For cases 1-3, we require an exception to be thrown.

For case 4, this wording requires a hard error (non-constant); this leaves open the possibility of evolving in the future to either relax the precondition (because functions can be called many times without ODR concerns) or enforce it via throw.

For case 5, some preconditions of type traits can be overly strict. Once case 4 is applied, the remaining cases can in theory produce an answer. The wording makes it unspecified whether the call is non-constant or produces the expected result.

Case 6 remains a hard error; we do not explicitly call this out since it's just
like any template instantiation triggered by a call to a reflection function.

:::

::: wordinglist

- Add the following paragraph to [meta.reflection.traits]{.sref} after p2:

::: add

[?]{.pnum} For a function or function template _F_ defined in this subclause, let _C_ be its associated class template. For the evaluation of a call to _F_, let _S_ be the specialization of _C_ in terms of which the call is specified.

- [?.#]{.pnum} If
  - [?.#.#]{.pnum} the template arguments of _S_ violate a condition specified in a _Mandates_ element in the specification of _C_;
  - [?.#.#]{.pnum} the call is specified to produce a reflection of a type, but _S_ would have no member named `type`; or
  - [?.#.#]{.pnum} the call is specified to return `S::value`, but that expression is not a valid converted constant expression of type _R_, where _R_ is the return type of _F_;

  then an exception of type `meta::exception` is thrown. [For the first case, _S_ is not instantiated.]{.note}
- [?.#]{.pnum} Otherwise, if the instantiation of _S_ would result in undefined behavior due to dependence on an incomplete type ([meta.rqmts]{.sref}), then the call is not a constant subexpression.
- [?.#]{.pnum} Otherwise, if the template arguments of _S_ do not meet the preconditions of _C_, then it is unspecified whether the call is a constant subexpression. If it is, the call produces the result that would be produced if _C_ had no preconditions.
 
:::

- Edit [meta.reflection.traits]{.sref} as indicated:

::: longtable
> [tab:meta.reflection.traits]{.sref} — Reflection type traits

### Signature and Return Type

::: ltcell 
```cpp
bool meta::$UNARY$(info type);
bool meta::$UNARY$_type(info type);
```
:::

### _Returns_

::: ltcell
`std::$UNARY$@[\_v]{.diffdel}@<`$T$`>`[`::value`]{.diffins}, where $T$ is the type or type alias represented by `type`
:::

---

::: ltcell

```cpp
bool meta::$BINARY$(info t1, info t2);
bool meta::$BINARY$_type(info t1, info t2);
```
:::

::: ltcell
`std::$BINARY$@[\_v]{.diffdel}@<`$T_1, T_2$`>`[`::value`]{.diffins}, where $T_1$ and $T_2$ are the types or type aliases represented by `t1` and `t2`, respectively
:::

---

::: ltcell

```cpp
template <reflection_range R>
bool meta::$VARIADIC$_type(info type, R&& args);
```
:::


::: ltcell
`std::$VARIADIC$@[\_v]{.diffdel}@<`$T, U...$`>`[`::value`]{.diffins} where $T$ is the type or type alias represented by `type` and $U...$ is the pack of types or type aliases whose elements are represented by the corresponding elements of `args`
:::

---

::: ltcell

```cpp
template <reflection_range R>
bool meta::$VARIADIC$_type(info t1, info t2, R&& args);
```
:::


::: ltcell
`std::$VARIADIC$@[\_v]{.diffdel}@<`$T_1, T_2, U...$`>`[`::value`]{.diffins} where $T_1$ and $T_2$ are the types or type aliases represented by `t1` and `t2`, respectively, and $U...$ is the pack of types or type aliases whose elements are represented by the corresponding elements of `args`
:::

---

::: ltcell

```cpp
info meta::$UNARY$(info type);
```
:::

::: ltcell
A reflection representing the type denoted by `std::$UNARY$@[\_t]{.diffdel}@<`$T$`>`[`::type`]{.diffins}, where `$T$` is the type or type alias represented by `type`
:::

---

::: ltcell

```cpp
template <reflection_range R>
info meta::$VARIADIC$(R&& args);
```
:::


::: ltcell
A reflection representing the type denoted by 
`std::$VARIADIC$@[\_t]{.diffdel}@<`$T...$`>`[`::type`]{.diffins} where $T...$ is the pack of types or type aliases whose elements are represented by the corresponding elements of `args`
:::

---

::: ltcell

```cpp
template <reflection_range R>
info meta::$VARIADIC$(info type, R&& args);
```
:::


::: ltcell
A reflection representing the type denoted by `std::$VARIADIC$@[\_t]{.diffdel}@<`$T, U...$`>`[`::type`]{.diffins} where $T$ is the type or type alias represented by `type` and $U...$ is the pack of types or type aliases whose elements are represented by the corresponding elements of `args`
:::

:::

::: itemdecl

```cpp
consteval size_t rank(info type);
```

[6]{.pnum} _Returns:_ [`rank_v<`$T$`>`]{.diffdel}[`std::rank<`$T$`>::value`]{.diffins}, where $T$ is the type represented by `dealias(type)`.

```cpp
consteval size_t extent(info type, unsigned i = 0);
```

[#]{.pnum} _Returns:_ [`extent_v<`$T, I$`>`]{.diffdel}[`std::extent<`$T, I$`>::value`]{.diffins}, where $T$ is the type represented by `dealias(type)` and $I$ is a constant equal to `i`.

```cpp
consteval size_t tuple_size(info type);
```

[#]{.pnum} _Returns:_ [`tuple_size_v<`_T_`>`]{.diffdel}[`std::tuple_size<`$T$`>::value`]{.diffins}, where _T_ is the type represented by `dealias(type)`.

```cpp
consteval info tuple_element(size_t index, info type);
```

[#]{.pnum} _Returns:_  A reflection representing the type denoted by [`tuple_element_t<`$I, T$`>`]{.diffdel}
[`std::tuple_element<`$I, T$`>:type`]{.diffins}, where $T$ is the type represented by `dealias(type)` and $I$ is a constant equal to `index`.

```cpp
consteval size_t variant_size(info type);
```
[#]{.pnum} _Returns:_ [`variant_size_v<`_T_`>`]{.diffdel}[`std::variant_size<`$T$`>::value`]{.diffins}, where _T_ is the type represented by `dealias(type)`.

```cpp
consteval info variant_alternative(size_t index, info type);
```

[#]{.pnum} _Returns:_ A reflection representing the type denoted by [`variant_alternative_t<`$I, T$`>`]{.diffdel}
[`std::variant_alternative<`$I, T$`>:type`]{.diffins}, where $T$ is the type represented by `dealias(type)` and $I$ is a constant equal to `index`.


```cpp
consteval strong_ordering type_order(info t1, info t2);
```
[#]{.pnum} _Returns:_ [`type_order_v<`$T_1, T_2$`>`]{.diffdel}[`std::type_order<`$T_1, T_2$`>::value`]{.diffins}, where $T_1, T_2$ are the types represented by `dealias(t1)` and `dealias(t2)`, respectively.

:::


:::