---
title: A type trait to detect reference binding to temporary
document: DXXXXR0
date: today
audience:
  - LEWG
  - EWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Abstract

This paper proposes adding two new type traits with compiler support
to detect when initialization a reference would bind it to a
lifetime-extended temporary, and changing several standard library
components (`pair`, `tuple` and _`INVOKE`_) to make such binding
ill-formed when it would inevitably produce a dangling reference.

# In brief

::: tonytable
## Before
```c++
std::tuple<const std::string&> x("hello");  // dangling
std::function<const std::string&()> f = [] {
  return "";
};

f();                                        // dangling
```

## After
```c++
std::tuple<const std::string&> x("hello");   // ill-formed
std::function<const std::string&()> f = [] { // ill-formed
  return "";
};

f();
```
:::

# Motivation

Various parts of the standard library need to initialize an entity
of some user-provided type `T` from an expression of a potentially
different type. When `T` is a reference type, this can easily create
dangling references. This occurs, for instance, when a
`std::tuple<const T&>` is initialized from something convertible to it:

```c++
std::tuple<const std::string&> t("meow");
```

This construction _always_ creates a dangling reference, because the
`std::string` temporary is created _inside_ the selected constructor
of `tuple` (`template<class... UTypes> tuple(UTypes&&...)`),
and not outside it. Thus, unlike `string_view`'s implicit conversion
from rvalue strings, under no circumstances can this construction be
used correctly.

Similarly, a `std::function<const string&()>` currently accepts any
callable whose invocation produces something convertible to
`const string&`. However, if the invocation produces a `std::string`
or a `const char*`, the returned reference would be bound to a
temporary and dangle.

Moreover, in both of the above cases, the problematic reference binding
occurs inside the standard library's code, and several major implementations
are known to suppress warnings in such contexts.

## Previous attempts

[@P0932R1] proposes modifying the constraints on `std::function` to
prevent such creation of dangling references. However, the proposed
modification is incorrect (it has both false positives and false negatives),
and correctly detecting all cases in which dangling references will be
created without false positives is likely impossible or at least
heroically difficult without compiler assistance, due to the
existence of user-defined conversions.

[@XXXX] changed the core language rules so that initialization of a reference
data member in a _mem-initializer_ is ill-formed if the initialization would
bind it to a temporary expression, which is exactly the condition these traits
seek to detect. However, this does not appear to have been widely implemented
yet, and the ill-formedness occurs outside a SFINAE context, so it is
not usable in constraints. Moreover, this requires a class with a data member of
reference type, which may not be suitable for user types that want to represent
a reference type differently (to facilitate rebinding, for instance).

# Design decisions

## Two type traits
We propose two traits, `reference_construction_binds_to_temporary` and
`reference_conversion_binds_to_temporary`, to cover both non-list
direct-initialization and copy-initialization. The former is useful in
classes like `std::tuple` and `std::pair` where `explicit` constructors
and conversion functions may be used; the latter is useful for _`INVOKE<R>`_
(i.e., `std::function`) where only implicit conversions are considered.

As is customary in the library traits, "construct" is used to denote
direct-initialization and "convert" is used to denote copy-initialization.

## Treat prvalues as distinct from xvalues
Unlike most library type traits, we propose that the traits handle prvalues
and xvalues differently: `reference_construction_binds_to_temporary_v<int&&, int>`
is `true`, while `reference_construction_binds_to_temporary_v<int&&, int&&>` is
`false`. This is useful for  _`INVOKE<R>`_; binding an rvalue reference
to an xvalue-returning function is not incorrect (as long as the function
does not return a dangling reference itself), but binding it to a prvalue (or
a temporary object materialized therefrom) would be in this context.

# Implementation experience

Clang has a `__reference_binds_to_temporary` intrinsic that partially implements the
direct-initialization variant of this trait (it does not implement the same-type
prvalue part).

# Wording
This wording is relative to [@N4849].

Edit [meta.type.synop]{.sref}, header `<type_traits>` synopsis, as indicated:

```diff
 namespace std {
   @_[...]_@
   template<class T> struct has_unique_object_representations;

+  template<class T, class U> struct reference_construction_binds_to_temporary;
+  template<class T, class U> struct reference_conversion_binds_to_temporary;

   @_[...]_@

   template<class T>
     inline constexpr bool has_unique_object_representations_v
       = has_unique_object_representations<T>::value;

+  template<class T, class U>
+    inline constexpr bool reference_construction_binds_to_temporary_v
+      = reference_construction_binds_to_temporary<T, U>::value;
+  template<class T, class U>
+    inline constexpr bool reference_conversion_binds_to_temporary_v
+      = reference_conversion_binds_to_temporary<T, U>::value;

   @_[...]_@
 }
```

In [meta.unary.prop]{.sref}, Table 47 [tab:meta.unary.prop], add the following:


| Template | Condition | Preconditions |
| --- | --- | --- |
|
```c++
template<class T, class U>
struct reference_construction_binds_to_temporary;
```
| `conjunction_v<is_reference<T>, is_constructible<T, U>>` is `true`,
and given an expression `E` such that `decltype((E))` is `U`,
the initialization `T t(E);` binds `E` to a temporary expression ([class.temporary]{.sref}).
|`U` shall be a complete type, _cv_ `void`, or an array of unknown bound. |
|
```c++
template<class T, class U>
struct reference_conversion_binds_to_temporary;
```
| `conjunction_v<is_reference<T>, is_convertible<U, T>>` is `true`,
and given an expression `E` such that `decltype((E))` is `U`,
the initialization `T t = E;` binds `E` to a temporary expression ([class.temporary]{.sref}).
|`U` shall be a complete type, _cv_ `void`, or an array of unknown bound. |

Edit [pairs.pair]{.sref} p8 through p14 as indicated:

<!-- TODO post-Prague -->

Edit [tuple.cnstr]{.sref} as indicated:

<!-- TODO post-Prague -->

Edit [func.require]{.sref} p2 as indicated:

[2]{.pnum} Define `INVOKE<R>(f, t1, t2, ... , tN )` as `static_cast<void>(INVOKE(f, t1, t2, ... , tN ))` if R is
_cv_ `void`, otherwise `INVOKE(f, t1, t2, ... , tN )` implicitly converted to `R`.
[If `reference_conversion_binds_to_temporary_v<R, decltype(INVOKE(f, t1, t2, ... , tN))>` is `true`,
`INVOKE<R>(f, t1, t2, ... , tN )` is ill-formed. ]{.diffins}
