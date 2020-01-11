---
title: Wording for _`boolean-testable`_
document: P1964R1
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: true
---

# Introduction

This paper provides wording for replacing `boolean` with the _`boolean-testable`_ exposition-only concept, as proposed
in [@P1964R0]. For detailed motivation and discussion, see that paper.

# LEWG Belfast vote

An early draft of [@P1964R0] was presented to LEWG on Friday afternoon in Belfast. The following polls were taken:

::: bq
Introduce an exposition-only concept `$NAME` as a replacement for the existing use of the `boolean` concept.

 - subsume `convertible_to`
 - add syntactic checking for `!`
 - add semantic requirements for "there is no `operator||` nor `operator&&` that can be found in any use of T"

In favor of the above design.

| SF | F  | N  | A  | SA |
| -- | -- | -- | -- | -- |
| 3	 | 11 | 2	 | 0	| 0  |

Name is _`boolean-testable`_

Unanimous consent

Tim and Casey will update P1964 with wording for the above design. We forward that paper to LWG for C++20.

Unanimous consent

:::

# Drafting notes

Yes, this is a lot of words to specify what is basically "don't be dumb". Defining "dumb" with sufficient precision
turns out to be complicated.

The basic requirement is that a _`boolean-testable`_ type must not contribute any potentially
viable `operator&&` or `operator||` overload to the overload set. If so, then any two _`boolean-testable`_ types can be
freely used with these operators, because there are no viable user-defined overloads and therefore they must have their
built-in meaning.

There are three cases to consider:

1. Members. These are relatively straightforward: no `operator&&` or `operator||`, period.
2. Non-member functions. These are also simple: we know the concrete types, so they are either potentially viable (an
   implicit conversion sequence exists from the source expression to one of the parameter types) or they are not.
3. Non-member function templates. These are the hardest because we don't know the parameter types at all and must
   therefore resort to template argument deduction.

There are some wrinkles for this third case.

### Non-deduced contexts {-}

Consider the following example:

```c++
 namespace X {
   enum A {};

   template<class>
   struct trait { using type = A; };

   template<class T>
   void operator&&(T*, typename trait<T>::type);
 }

```

This `operator&&` will be picked up in an expression like `(int*) nullptr && X::A()`. Since `int*` should model
_`boolean-testable`_ (and certainly isn't responsible for this operator), we must make `X::A` not model
_`boolean-testable`_. In other words, a non-deduced context, which can encode an arbitrary type transformation,
must be considered to match everything.

### `std::valarray` {-}

As mentioned in [@P1964R0], the wording needs to avoid catching overloads like `std::valarray`'s `operator&&` on
unsuspecting types in `namespace std`. That is, we want declarations like

```c++
template<class T>
valarray<bool> operator&&(const valarray<T>&, const typename valarray<T>::value_type&);
```

and its pre-[@LWG3074] form

```c++
template<class T>
valarray<bool> operator&&(const valarray<T>&, const T&);
```

to disqualify specializations of `std::valarray` (or any derived class that might have added a conversion to `bool`),
but not `std::true_type`.

The distinguishing characteristics of these overloads are

1. They are part of the interface of some class template (e.g., `std::valarray`);
2. They have a function parameter whose (uncvref'd) type is a specialization of that class template;
3. They are a member of the same namespace as that class template (so that they can be found by ADL)

For these overloads, we can safely only consider the parameter(s) satisfying #2 above (called _key parameters_ in the
wording below). <span style="color:darkblue">This is because for template argument deduction to succeed on such a parameter,
the type of the provided argument must be either a specialization of that class template or derived from it.</span>
<span style="color:darkgreen">If so, then _that argument_ must necessarily also bring this function template into the
overload set.</span>
As long as the wording excludes such arguments, then, there is no need to worry about other types that may happen to belong
in the same namespace.

I have color-coded the two steps in this reasoning because there are corner cases involving each, which I'll now discuss.

#### Non-deduced contexts, again {-}

Consider this example:

```c++
namespace Y {
  template<class>
  struct C {};

  template<class T>
  void operator&&(C<T> x, T y);

  template<class T>
  void operator||(C<std::decay_t<T>> x, T y);

  enum A {};
}

struct B { template<class T> operator T(); };
```

We don't want the `operator&&` declaration to disqualify `Y::A`; however the expression `::B() || Y::A()` will use the
`Y::operator||` overload, and therefore `Y::A` cannot be _`boolean-testable`_, even though its declaration might be
superficially similar. The key difference here is that `C<std::decay_t<T>>` doesn't contain anything that participates
in template argument deduction, and therefore no longer requires the argument to have any relation to `C`, contrary to
the <span style="color:darkblue">first sentence of the reasoning above</span>.

To qualify as a _key parameter_, then, the type must contain at least one template parameter that participates in
template argument deduction.

#### Hidden friends{-}

Hidden friends strike at the <span style="color:darkgreen">second sentence of the reasoning above</span>. Consider:

```c++
namespace Z {
  template<class>
  struct A {
    operator bool();
  };

  struct B {
    operator bool();
    template<class T>
    friend void operator&&(A<T>, B);
  };
}
```

`Z::A<int>() && Z::B()` will use the `operator&&` overload, but ADL for `Z::A<int>()` alone will not even find the hidden
friend overload (indeed, the author of `Z::A` might have nothing to do with it). So we must disqualify `Z::B` instead.

The problem here is that the hidden friend can be a friend of the wrong class. That means that the
<span style="color:darkgreen">second sentence of the reasoning above</span> no longer applies, because we are no longer
guaranteed that the argument related to `A` will bring the overload in.

The wording below excludes hidden friends from the _key parameter_ special case: hidden friends disqualify a type from
modeling _`boolean-testable`_ if template argument deduction for either parameter succeeds. Note that the concern
motivating this special case doesn't apply to hidden friends: if they are the hidden friend of the "right" class template,
then ADL for other types in the namespace will not even find them, so they will not accidentally disqualify anything.

# Wording
This wording is relative to [@N4842].

Replace [concept.boolean]{.sref} with the following:

::: add

### 18.5.2 Boolean testability [concept.booleantestable] {-}

[1]{.pnum} The exposition-only _`boolean-testable`_ concept specifies the requirements on expressions that are convertible
to `bool` and for which the logical operators ([expr.log.and]{.sref}, [expr.log.or]{.sref}, [expr.unary.op]{.sref})
have the conventional semantics.

::: bq

```c++
template<class T>
concept @_boolean-testable-impl_@ = convertible_to<T, bool>;  // @_exposition only_@
```

:::

[2]{.pnum} Let `e` be an expression such that `decltype((e))` is `T`. `T` models _`boolean-testable-impl`_ only if:

- [2.1]{.pnum} either `remove_cvref_t<T>` is not a class type, or name lookup for the names `operator&&` and `operator||`
  within the scope of `remove_cvref_t<T>` as if by class member access lookup ([class.member.lookup]{.sref}) results in
  an empty declaration set; and
- [2.2]{.pnum} name lookup for the names `operator&&` and `operator||` in the associated namespaces and entities of `T`
  ([basic.lookup.argdep]{.sref}) finds no disqualifying declaration (defined below).

[3]{.pnum} A _disqualifying parameter_ is a function parameter whose declared type `P`

- [3.1]{.pnum} is not dependent on a template parameter, and there exists an implicit conversion sequence ([over.best.ics]{.sref})
  from `e` to `P`; or
- [3.2]{.pnum} is dependent on one or more template parameters, and either
  - [3.2.1]{.pnum} `P` contains no template parameter that participates in template argument deduction ([temp.deduct.type]{.sref}), or
  - [3.2.2]{.pnum} template argument deduction using the rules for deducing template arguments in a function call
    ([temp.deduct.call]{.sref}) and the type of `e` as the argument type succeeds.

[4]{.pnum} A _key parameter_ of a function template `D` is a function parameter of type _`cv`_ `X` or reference thereto,
where `X` names a specialization of a class template that is a member of the same namespace as `D`, and `X` contains at
least one template parameter that participates in template argument deduction.

::: example

In

```c++
 namespace Z {
   template<class>
   struct C {};

   template<class T>
   void operator&&(C<T> x, T y);

   template<class T>
   void operator||(C<type_identity_t<T>> x, T y);
 }
```

the declaration of `Z::operator&&` contains one key parameter, `C<T> x`, and the declaration of `Z::operator||` contains
no key parameters.

:::

[5]{.pnum} A _disqualifying declaration_ is

- [5.1]{.pnum} a (non-template) function declaration that contains at least one disqualifying parameter; or
- [5.2]{.pnum} a function template declaration that contains at least one disqualifying parameter, where
  - [5.2.1]{.pnum} at least one disqualifying parameter is a key parameter; or
  - [5.2.2]{.pnum} the declaration contains no key parameters; or
  - [5.2.3]{.pnum} the declaration declares a function template that is not visible in its namespace ([namespace.memdef]{.sref}).

[6]{.pnum} [The intention is to ensure that given two types `T1` and `T2` that each model _`boolean-testable-impl`_,
the `&&` and `||` operators within the expressions `declval<T1>() && declval<T2>()` and `declval<T1>() || declval<T2>()`
resolve to the corresponding built-in operators.]{.note}

::: bq

```c++
template<class T>
concept @_boolean-testable_@ =                             // @_exposition only_@
    @_boolean-testable-impl_@<T> && requires (T&& t) {
        { !std::forward<T>(t) } -> @_boolean-testable-impl_@
    };
```

:::

[7]{.pnum} Let `e` be an expression such that `decltype((e))` is `T`. `T` models _`boolean-testable`_ only
if `bool(e) == !bool(!e)`.

[8]{.pnum} [The types `bool`, `true_­type` ([meta.type.synop]{.sref}), `int*`, and `bitset<N>​::​reference`
([template.bitset]{.sref}) model _`boolean-testable`_.]{.example}

:::

Edit [concepts.syn]{.sref} as indicated:

:::bq
```diff
 namespace std {
   @[...]@

   // 18.5, comparison concepts
-  // 18.5.2, concept boolean
-  template<class B>
-  concept boolean = @_see below_@ ;

   @[...]@
 }
```
:::

Replace all instances of `boolean` in [cmp.concept]{.sref}, [concept.equalitycomparable]{.sref},
[concept.totallyordered]{.sref} and [concept.predicate]{.sref} with _`boolean-testable`_.

Edit [expos.only.func]{.sref} as indicated:

::: bq

```diff
 constexpr auto synth-three-way =
   []<class T, class U>(const T& t, const U& u)
     requires requires {
-      { t < u } -> @[convertible_to<bool>]{.diffdel}@;
-      { u < t } -> @[convertible_to<bool>]{.diffdel}@;
+      { t < u } -> @_[boolean-testable]{.diffins}_@;
+      { u < t } -> @_[boolean-testable]{.diffins}_@;
     }
   {
     if constexpr (three_way_comparable_with<T, U>) {
       return t <=> u;
     } else {
       if (t < u) return weak_ordering::less;
       if (u < t) return weak_ordering::greater;
       return weak_ordering::equivalent;
     }
   };
```

:::

Edit [alg.find]{.sref} p1 as indicated:

:::bq
[1]{.pnum} Let _E_ be:

- [1.1]{.pnum} `*i == value` for `find`,
- [1.2]{.pnum} `pred(*i) != false` for `find_­if`,
- [1.3]{.pnum} `pred(*i) == false` for `find_­if_­not`,
- [1.4]{.pnum} [`bool(`]{.diffins}`invoke(proj, *i) == value`[`)`]{.diffins} for ranges​::​find,
- [1.5]{.pnum} [`bool(`]{.diffins}`invoke(pred, invoke(proj, *i))`[`)`]{.diffins} [`!= false`]{.diffdel} for
  `ranges​::​find_­if`,
- [1.6]{.pnum} [`bool(!`]{.diffins}`invoke(pred, invoke(proj, *i))`[`)`]{.diffins} [`== false`]{.diffdel} for
  `ranges​::​find_­if_­not`.

:::

Edit [alg.find.first.of]{.sref} p1 as indicated:

:::bq
[1]{.pnum} Let _E_ be:

- [1.1]{.pnum} `*i == *j` for the overloads with no parameter `pred`,
- [1.2]{.pnum} `pred(*i, *j) != false` for the overloads with a parameter `pred` and no parameter `proj1`,
- [1.3]{.pnum} [`bool(`]{.diffins}`invoke(pred, invoke(proj1, *i), invoke(proj2, *j))`[`)`]{.diffins} [`!= false`]{.diffdel}
  for the overloads with parameters `pred` and `proj1`.

:::

Edit [alg.adjacent.find]{.sref} p1 as indicated:

::: bq
[1]{.pnum} Let _E_ be:

- [1.1]{.pnum} `*i == *(i + 1)` for the overloads with no parameter `pred`,
- [1.2]{.pnum} `pred(*i, *(i + 1)) != false` for the overloads with a parameter `pred` and no parameter `proj`,
- [1.3]{.pnum} [`bool(`]{.diffins}`invoke(pred, invoke(proj, *i), invoke(proj, *(i + 1)))`[`)`]{.diffins} [`!= false`]{.diffdel}
  for the overloads with parameters `pred` and `proj`.

:::

Edit [alg.count]{.sref} p1 as indicated:


:::bq
[1]{.pnum} Let _E_ be:

- [1.1]{.pnum} `*i == value` for the overloads with no parameter `pred` or `proj`,
- [1.2]{.pnum} `pred(*i) != false` for the overloads with a parameter `pred` but no parameter `proj`,
- [1.3]{.pnum} `invoke(proj, *i) == value` for the overloads with a parameter `proj` but no parameter `pred`,
- [1.4]{.pnum} [`bool(`]{.diffins}`invoke(pred, invoke(proj, *i))`[`)`]{.diffins} [`!= false`]{.diffdel} for the overloads
  with both parameters `proj` and `pred`.
:::
