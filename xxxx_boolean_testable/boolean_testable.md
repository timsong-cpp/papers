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

This paper provides wording for replacing `boolean` with the _`boolean-testable`_ exposition-only concept, as proposed in [@P1964R0].

# Drafting notes


# Wording
This wording is relative to [@N4842].

Replace [concept.boolean]{.sref} with the following:

::: add

### 18.5.2 Boolean testability {-}

[1]{.pnum} The _`boolean-testable`_ concept specifies the requirements on expressions that are convertible to `bool` and for which the logical operators ([expr.log.and]{.sref}, [expr.log.or]{.sref}, [expr.unary.op]{.sref}) have the conventional semantics.

::: bq

```c++
template<class T>
concept @_boolean-testable-impl_@ = convertible_to<T, bool>;
```

:::

[2]{.pnum} Let `e` be an expression such that `decltype((e))` is `T`. `T` models _`boolean-testable-impl`_ only if:

- [2.1]{.pnum} either `remove_cvref_t<T>` is not a class type, or name lookup for the names `operator&&` and `operator||` within the scope of `remove_cvref_t<T>` as if by class member access lookup ([class.member.lookup]{.sref}) results in an empty declaration set; and
- [2.2]{.pnum} name lookup for the names `operator&&` and `operator||` in the associated namespaces and classes of `T` ([basic.lookup.argdep]{.sref}) finds no disqualifying declaration (defined below).

[3]{.pnum} A _disqualifying parameter_ is

- [3.1]{.pnum} A function parameter whose type is not dependent on a template parameter, and there exists an implicit conversion sequence ([conv]{.sref}) from `e` to its type; or
- [3.2]{.pnum} A function parameter whose type is dependent on a template parameter, and template argument deduction using the rules for deducing template arguments in a function call ([temp.deduct.call]{.sref}) with the type of `e` as the argument type succeeds. [This includes the case where no template argument is deduced because every template parameter in the type is in a non-deduced context.]{.note}

[4]{.pnum} A _disqualifying declaration_ is

- [4.1]{.pnum} a function declaration that contains at least one disqualifying parameter;
- [4.2]{.pnum} a function template declaration where either
  - [4.2.1]{.pnum} at least one parameter is of the type (possibly cv-qualified) specialization of a class template `C` or reference thereto such that `C` and the function template are members of the same inline namespace set, and at least one such parameter is disqualifying; or
  - [4.2.2]{.pnum} no parameter is of the type (possibly cv-qualified) specialization of a class template `C` or reference thereto such that `C` and the function template are members of the same inline namespace set, and at least one function parameter is disqualifying.

[5]{.pnum} [The intent is to ensure that for any two types `T1` and `T2` that both model _`boolean-testable-impl`_, the `&&` and `||` operators within the expressions `declval<T1>() && declval<T2>()` and `declval<T1>() || declval<T2>()` resolves to the built-in operator.]{.note}

::: bq

```c++
template<class T>
concept @_boolean-testable_@ = @_boolean-testable-impl_@<T> &&
    requires {
        { !declval<T>() } -> @_boolean-testable-impl_@
    };
```

:::

[6]{.pnum} Let `e` be an expression such that `decltype((e))` is `T`. `T` models _`boolean-testable`_ only if `bool(e) == !bool(!e)`.

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

Replace all instances of `boolean` in [cmp.concept]{.sref}, [concept.equalitycomparable]{.sref}, [concept.totallyordered]{.sref} and [concept.predicate]{.sref} with _`boolean-testable`_.


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

[1]{.pnum} Let _E_ be:

- [1.1]{.pnum} `*i == value` for `find`,
- [1.2]{.pnum} `pred(*i) != false` for `find_­if`,
- [1.3]{.pnum} `pred(*i) == false` for `find_­if_­not`,
- [1.4]{.pnum} [`bool(`]{.diffins}`invoke(proj, *i) == value`[`)`]{.diffins} for ranges​::​find,
- [1.5]{.pnum} [`bool(`]{.diffins}`invoke(pred, invoke(proj, *i))`[`)`]{.diffins} [`!= false`]{.diffdel} for `ranges​::​find_­if`,
- [1.6]{.pnum} [`bool(!`]{.diffins}`invoke(pred, invoke(proj, *i))`[`)`]{.diffins} [`== false`]{.diffdel} for `ranges​::​find_­if_­not`.

Edit [alg.find.first.of]{.sref} p1 as indicated:

[1]{.pnum} Let _E_ be:

- [1.1]{.pnum} `*i == *j` for the overloads with no parameter `pred`,
- [1.2]{.pnum} `pred(*i, *j) != false` for the overloads with a parameter `pred` and no parameter `proj1`,
- [1.3]{.pnum} [`bool(`]{.diffins}`invoke(pred, invoke(proj1, *i), invoke(proj2, *j))`[`)`]{.diffins} [`!= false`]{.diffdel} for the overloads with parameters `pred` and `proj1`.

Edit [alg.adjacent.find]{.sref} p1 as indicated:

[1]{.pnum} Let _E_ be:

- [1.1]{.pnum} `*i == *(i + 1)` for the overloads with no parameter `pred`,
- [1.2]{.pnum} `pred(*i, *(i + 1)) != false` for the overloads with a parameter `pred` and no parameter `proj`,
- [1.3]{.pnum} [`bool(`]{.diffins}`invoke(pred, invoke(proj, *i), invoke(proj, *(i + 1)))`[`)`]{.diffins} [`!= false`]{.diffdel} for the overloads with parameters `pred` and `proj`.

Edit [alg.count]{.sref} p1 as indicated:

[1]{.pnum} Let _E_ be:

- [1.1]{.pnum} `*i == value` for the overloads with no parameter `pred` or `proj`,
- [1.2]{.pnum} `pred(*i) != false` for the overloads with a parameter `pred` but no parameter `proj`,
- [1.3]{.pnum} `invoke(proj, *i) == value` for the overloads with a parameter `proj` but no parameter `pred`,
- [1.4]{.pnum} [`bool(`]{.diffins}`invoke(pred, invoke(proj, *i))`[`)`]{.diffins} [`!= false`]{.diffdel} for the overloads with both parameters `proj` and `pred`.
