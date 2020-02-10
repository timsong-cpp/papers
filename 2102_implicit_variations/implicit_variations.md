---
title: Make "implicit expression variations" more explicit (Wording for US185)
document: D2102R0
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
  - name: Casey Carter
    email: <casey@carter.net>
toc: false
---

# Introduction
This paper provides wording to resolve NB comment [US185](https://github.com/cplusplus/nbballot/issues/183).

# Wording
This wording is relative to [@N4849].

1. Edit [concepts.equality]{.sref}p1 as indicated to define "operand":

::: bq

An expression is _equality-preserving_ if, given equal inputs, the expression results in equal outputs. The inputs to an expression are the set of the expression's operands. The output of an expression is the expression's result and all operands modified by the expression. [For the purposes of this subclause, the _operands_ of an expression are the largest subexpressions that include only:]{.diffins}

:::add

 - [1.1]{.pnum} an _id-expression_ ([expr.prim.id]{.sref}), and
 - [1.2]{.pnum} invocations of the library function templates `std::move`, `std::forward`, and `std::declval` ([forward]{.sref}, [declval]{.sref})

::: example

The operands of the expression `a = std::move(b)` are `a` and `std::move(b)`.

:::

:::

:::

2. Edit [concepts.equality]{.sref} p5 to clarify how the cv-qualification and value categories of operands are determined:

::: bq

An expression that may alter the value of one or more of its inputs in a manner observable to equality-preserving expressions is said to modify those inputs. This document uses a notational convention to specify which expressions declared in a requires-expression modify which inputs: except where otherwise specified, an expression operand that is a non-constant lvalue or rvalue may be modified. Operands that are constant lvalues or rvalues are required to not be modified. [For the purposes of this subclause, the cv-qualification and value category of each operand is determined by assuming that each template type parameter denotes a cv-unqualified
complete non-array object type.]{.diffins}

:::

3. Edit [concepts.object]{.sref} to explicitly require additional variations on `assignable_from` for `copyable`:

::: bq

```diff
 template<class T>
-  concept copyable = copy_constructible<T> && movable<T> && assignable_from<T&, const T&>;
+  concept copyable = copy_constructible<T> && movable<T> && @[assignable_from<T&, T&> &&]{.diffins}@
+                     assignable_from<T&, const T&> @[&& assignable_from<T&, const T>]{.diffins}@;
```

:::

4. Edit [alg.req.ind.copy]{.sref} to explicit require additional variations on `indirectly_writable` for `indirectly_copyable_storable`:

::: bq

```diff
 template<class In, class Out>
   concept indirectly_copyable_storable =
     indirectly_copyable<In, Out> &&
+    indirectly_writable<Out, iter_value_t<In>&> &&
     indirectly_writable<Out, const iter_value_t<In>&> &&
+    indirectly_writable<Out, iter_value_t<In>&&> &&
+    indirectly_writable<Out, const iter_value_t<In>&&> &&
     copyable<iter_value_t<In>> &&
     constructible_from<iter_value_t<In>, iter_reference_t<In>> &&
     assignable_from<iter_value_t<In>&, iter_reference_t<In>>;```

```

:::
