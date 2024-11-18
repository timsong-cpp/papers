---
title: Retiring niebloids
document: P3136R1
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Abstract

This paper proposes that we respecify the algorithms in `std::ranges`
that are currently so-called niebloids to be actual function objects.

# Revision history

- R1: Incorporated LWG review feedback.

# Background

"Niebloid" is the informal name given to the "function templates" in
`std::ranges` with the special property described in
[algorithms.requirements]{.sref} p2:

::: bq

[2]{.pnum} The entities defined in the `std​::​ranges` namespace in this Clause
are not found by argument-dependent name lookup ([basic.lookup.argdep]{.sref}).
When found by unqualified ([basic.lookup.unqual]{.sref}) name lookup for the
_postfix-expression_ in a function call ([expr.call]{.sref}), they inhibit
argument-dependent name lookup.

::: example
```cpp
void foo() {
  using namespace std::ranges;
  std::vector<int> vec{1,2,3};
  find(begin(vec), end(vec), 2);        // #1
}
```
The function call expression at #1 invokes `std​::​ranges​::​find`, not `std​::​find`,
despite that (a) the iterator type returned from `begin(vec)` and `end(vec)` may
be associated with namespace `std` and (b) `std​::​find` is more specialized
([temp.func.order]{.sref}) than `std​::​ranges​::​find` since the former requires
its first two parameters to have the same type.

:::

:::

This example also shows the reason for this requirement: because ranges algorithms
accept iterator-sentinel pairs, they are almost always less specialized than their
classic counterparts and therefore would otherwise lose overload resolution.

Of course, there's nothing in the core language that actually allow a
_function template_ to have this property. Instead, all major implementations
implement them as function objects, aided by the ban on explicit template argument
lists in [algorithms.requirements]{.sref} p15:

::: bq

[15]{.pnum} The well-formedness and behavior of a call to an algorithm with an
explicitly-specified template argument list is unspecified,
except where explicitly stated otherwise.

:::

The original idea behind this specification was that there might eventually be
a core language change and/or some compiler extension that would allow implementing
them as function templates.

# Discussion

We should bite the bullet and just specify niebloids as function objects.

## No language extension has materialized

Four years after C++20, the language extension has not materialized, and is
unlikely to do so. It is hard to motivate a language change when the
function-object based implementation works just as well.

## Implementations have converged

While there were originally implementation divergence on whether niebloids should
be CPO-like `semiregular` function objects or noncopyable ones to more closely
emulate function templates, the major implementations
[have now converged](https://github.com/microsoft/STL/issues/4097) on
semiregularity. We should standardize this existing practice.

## The status quo discourages reasonable code

Consider:

```cpp
auto x = std::views::transform(std::ranges::size);
auto y = std::views::transform(std::ranges::distance);
auto z = std::views::transform(std::ref(std::ranges::distance));
auto w = std::views::transform([](auto&& r) { return std::ranges::distance(r); });
```

`x` is valid because `size` is a CPO. `y` might not be, because `distance` is a niebloid,
and until last October, at least one major implementation disallowed copying niebloids.
`z` is de-facto valid - as long as `std::ranges::distance` is an object, `std::ref`
should work on it, and then `reference_wrapper`'s call operator kicks in.
`w` is valid but excessively verbose.

There's nothing inherently objectionable about `y`; we are not doing our users
a service by disallowing it on paper. There's no reason to insist on writing
a lambda.

## Unresolved wording issues

The difference between a function object and a set of function templates goes beyond
the suppression of ADL and the inability to specify a template argument list. For example,
function objects do not overload. The current wording is therefore technically
insufficient to permit the function-object implementation. Instead of trying to
further weasel-word this, I think we should just admit that niebloids are
function objects.

# Wording

This wording is relative to [@N4971].

::: wordinglist

- Strike [customization.point.object]{.sref} p6:

[This sentence isn't really true - what concept does `views::single` constrain
its return type with? In any event, it doesn't have any normative effect on its
own; if there is a constraint then the CPO's specification will specify it.]{.draftnote}

::: rm

[6]{.pnum} Each customization point object type constrains its return type
to model a particular concept.

:::

- Add the following subclause to [conventions]{.sref}:

::: add

### 16.3.3.? Algorithm function objects [niebloid] {-}

[#]{.pnum} An _algorithm function object_ is a 
customization point object ([customization.point.object]{.sref}) 
that is specified as one or more overloaded function templates. 
The name of these function templates designates the corresponding 
algorithm function object.

[#]{.pnum} For an algorithm function object `o`, let _`S`_ be the corresponding
set of function templates. Then for any sequence of arguments
`args...`, `o(args...)` is expression-equivalent to `s(args...)`, where the
result of name lookup for `s` is the overload set _`S`_.

::: note

Algorithm function objects are not found by argument-dependent name
lookup ([basic.lookup.argdep]{.sref}). When found by unqualified
([basic.lookup.unqual]{.sref}) name lookup for the _postfix-expression_ in a
function call ([expr.call]{.sref}), they inhibit argument-dependent name lookup.

::: example
```cpp
void foo() {
  using namespace std::ranges;
  std::vector<int> vec{1,2,3};
  find(begin(vec), end(vec), 2);        // #1
}
```
The function call expression at #1 invokes `std​::​ranges​::​find`, not `std​::​find`.

:::

:::

:::

- Edit [range.iter.ops.general]{.sref} as indicated:

::: rm

[2]{.pnum} The function templates defined in [range.iter.ops]{.sref} are not
found by argument-dependent name lookup ([basic.lookup.argdep]{.sref}). When
found by unqualified ([basic.lookup.unqual]{.sref}) name lookup for the
_postfix-expression_ in a function call ([expr.call]{.sref}), they inhibit
argument-dependent name lookup.

::: example-2

```cpp
void foo() {
    using namespace std::ranges;
    std::vector<int> vec{1,2,3};
    distance(begin(vec), end(vec));     // #1
}
```

The function call expression at #1 invokes `std​::​ranges​::​distance`,
not `std​::​distance`, despite that (a) the iterator type returned from
`begin(vec)` and `end(vec)` may be associated with namespace std and
(b) `std​::​distance` is more specialized ([temp.func.order]{.sref}) than
`std​::​ranges​::​distance` since the former requires its first two parameters
to have the same type.

:::

[3]{.pnum}
The number and order of deducible template parameters for the function templates
defined in [range.iter.ops]{.sref} is unspecified, except where explicitly stated otherwise.

:::

::: add

[2]{.pnum} The entities defined in [range.iter.ops]{.sref} are algorithm
function objects (16.3.3.? [niebloid]).

:::

- Edit [algorithms.requirements]{.sref} p2 as indicated:

::: rm

[2]{.pnum} The entities defined in the `std​::​ranges` namespace in this Clause
are not found by argument-dependent name lookup ([basic.lookup.argdep]{.sref}).
When found by unqualified ([basic.lookup.unqual]{.sref}) name lookup for the
_postfix-expression_ in a function call ([expr.call]{.sref}), they inhibit
argument-dependent name lookup.

::: example
```cpp
void foo() {
  using namespace std::ranges;
  std::vector<int> vec{1,2,3};
  find(begin(vec), end(vec), 2);        // #1
}
```
The function call expression at #1 invokes `std​::​ranges​::​find`, not `std​::​find`,
despite that (a) the iterator type returned from `begin(vec)` and `end(vec)` may
be associated with namespace `std` and (b) `std​::​find` is more specialized
([temp.func.order]{.sref}) than `std​::​ranges​::​find` since the former requires
its first two parameters to have the same type.

:::

:::

::: add

[2]{.pnum} The entities defined in the `std​::​ranges` namespace in this Clause
and specified as function templates are algorithm function objects (16.3.3.? [niebloid]).

:::

:::
