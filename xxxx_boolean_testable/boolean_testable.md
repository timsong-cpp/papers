---
title: Wording for _`boolean-testable`_
document: DxxxxRX
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Introduction

This paper provides wording for replacing `boolean` with the _`boolean-testable`_ exposition-only concept, as proposed
in [@P1964R0].

# LEWG Belfast vote

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


# Drafting notes

Yes, this is a lot of words to specify what is basically "don't be dumb".

The basic requirement is that a _`boolean-testable`_ type must not contribute any potentially viable `operator&&` or
`operator||` overload to the overload set. If so, then any two _`boolean-testable`_ types can be freely used with these
operators, because there are no viable user-defined overloads and therefore they must have their built-in meaning.
There are three cases to consider:

1. Members. These are relatively straightforward: no `operator&&` or `operator||`, period.
2. Non-member functions. These are also simple: we know the concrete types, so they are either potentially viable (an
   implicit conversion sequence exists from the source expression to one of the parameter types) or they are not.
3. Non-member function templates. These are the hardest because we don't know the parameter types at all and must
   therefore resort to template argument deduction.

There is an additional wrinkle in the third case: as mentioned in [@P1964R0], the wording needs to avoid avoid catching
overloads like `std::valarray`'s `operator&&` on unsuspecting types in `namespace std`. That is, we want declarations like

```c++
template<class T>
valarray<bool> operator&&(const valarray<T>&, const typename valarray<T>::value_type&);
```

and its pre-[@LWG3074] form

```c++
template<class T>
valarray<bool> operator&&(const valarray<T>&, const T&);
```

to disqualify `std::valarray`, but not `std::true_type`.

The approach taken in the wording below is to only consider "key parameters" where possible. A "key parameter"
is a function parameter whose type is (reference to) a class template specialization that is a member of the same
namespace as the function template. In the examples above, only the first parameter is "key".

If a namespace-scope function template declaration `D` has at least one key parameter, then we can limit our inspection
to those parameters, because for template argument deduction to succeed on a key parameter, the type of supplied argument
must be a specialization of that class template or derived therefrom. Such an argument is necessarily associated with
the namespace containing `D`, and therefore we can safely blame it for `D`, and not consider anything else that might
also accidentally bring the declaration in.

# Wording
This wording is relative to [@N4842]. Drafting notes in blue ([like this]{.draftnote-blue}) are explanations of the wording
for reviewers and not part of the wording.

Replace [concept.boolean]{.sref} with the following:

::: add

### 18.5.2 Boolean testability {-}

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

:::draftnote-blue

Non-deduced contexts must be disqualifying because they can contain an arbitrary type transformation. Consider:

```c++
 namespace NS1 {
   enum A {};

   template<class>
   struct trait { using type = A; };

   template<class T>
   void operator&&(T*, typename trait<T>::type);
 }

```

`(int*)nullptr && NS1::A()` will use the `operator&&` overload, and therefore we must disqualify `NS1::A`.

:::


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

:::draftnote-blue

It's important that `X` contains at least one parameter that participates in template argument deduction; if not, then
we cannot guarantee that a deduction failure will result for any type that is not derived from the class template. In the
above example, given

```c++
 namespace Z {
   enum X {};
 }

  struct Y { template<class T> operator T(); };
```

`Y() || Z::X()` will use the `operator||` overload, so that overload must disqualify `Z::X`.

:::

[5]{.pnum} A _disqualifying declaration_ is

- [5.1]{.pnum} a (non-template) function declaration that contains at least one disqualifying parameter; or
- [5.2]{.pnum} a function template declaration where
  - [5.2.1]{.pnum} the declaration is at namespace scope and contains at least one key parameter, and at least one key
    parameter is disqualifying; or
  - [5.2.2]{.pnum} the declaration contains at least one disqualifying parameter, and it either
    - [5.2.2.1]{.pnum} contains no key parameter, or
    - [5.2.2.2]{.pnum} declares a function template that is not visible in its namespace ([namespace.memdef]{.sref}).

:::draftnote-blue

We cannot only look at the key parameter(s) if the function template is a hidden friend, because it may be a hidden
friend of the wrong class.

```c++
 namespace NS2 {
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

`NS2::A<int>() && NS2::B()` will use the `operator&&` overload, but ADL for `NS2::A<int>()` alone will not find the hidden
friend overload, so that overload must disqualify `NS2::B`.

:::

[6]{.pnum} [The intention is to ensure that given two types `T1` and `T2` that both model _`boolean-testable-impl`_,
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
