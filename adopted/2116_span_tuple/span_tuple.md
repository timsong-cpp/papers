---
title: Remove tuple-like protocol support from fixed-extent span
document: P2116R0
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Introduction

In response to [@LWG3212], this paper provides wording to remove the support for tuple-like protocol
from fixed-extent spans, as directed by LEWG in Prague. This [resolves](https://xkcd.com/498/)
[@LWG3212].

# Wording
This wording is relative to [@N4849].

Edit [tuple.helper]{.sref} p6 and p8 as indicated:

```c++
template<class T> struct tuple_size<const T>;
template<class T> struct tuple_size<volatile T>;
template<class T> struct tuple_size<const volatile T>;
```

_[...]_

[6]{.pnum} In addition to being available via inclusion of the `<tuple>` header,
the three templates are available when any of the headers `<array>` ([array.syn]{.sref}),
`<ranges>` ([ranges.syn]{.sref}), [`<span>` ([span.syn]{.sref}),]{.diffdel}
or `<utility>` ([utility.syn]{.sref}) are included.

```c++
template<size_t I, class T> struct tuple_element<I, const T>;
template<size_t I, class T> struct tuple_element<I, volatile T>;
template<size_t I, class T> struct tuple_element<I, const volatile T>;
```

_[...]_

[8]{.pnum} In addition to being available via inclusion of the `<tuple>` header,
the three templates are available when any of the headers `<array>` ([array.syn]{.sref}),
`<ranges>` ([ranges.syn]{.sref}), [`<span>` ([span.syn]{.sref}),]{.diffdel}
or `<utility>` ([utility.syn]{.sref}) are included.


Edit [span.syn]{.sref} as indicated:

```diff
 namespace std {
   // constants
   inline constexpr size_t dynamic_extent = numeric_limits<size_t>::max();

   // [views.span], class template span
   template<class ElementType, size_t Extent = dynamic_extent>
     class span;

   template<class ElementType, size_t Extent>
     inline constexpr bool ranges::enable_safe_range<span<ElementType, Extent>> = true;

   // [span.objectrep], views of object representation
   template<class ElementType, size_t Extent>
     span<const byte, Extent == dynamic_extent ? dynamic_extent : sizeof(ElementType) * Extent>
       as_bytes(span<ElementType, Extent> s) noexcept;

   template<class ElementType, size_t Extent>
     span<byte, Extent == dynamic_extent ? dynamic_extent : sizeof(ElementType) * Extent>
       as_writable_bytes(span<ElementType, Extent> s) noexcept;

-  // [span.tuple], tuple interface
-  template<class T> struct tuple_size;
-  template<size_t I, class T> struct tuple_element;
-  template<class ElementType, size_t Extent>
-    struct tuple_size<span<ElementType, Extent>>;
-  template<class ElementType>
-    struct tuple_size<span<ElementType, dynamic_extent>>;       // not defined
-  template<size_t I, class ElementType, size_t Extent>
-    struct tuple_element<I, span<ElementType, Extent>>;
-  template<size_t I, class ElementType, size_t Extent>
-    constexpr ElementType& get(span<ElementType, Extent>) noexcept;
 }
```

Delete [span.tuple]{.sref}:

::: rm

#### 22.7.3.9 Tuple interface [span.tuple] {-}

```c++
template<class ElementType, size_t Extent>
  struct tuple_size<span<ElementType, Extent>>
    : integral_constant<size_t, Extent> { };

template<size_t I, class ElementType, size_t Extent>
  struct tuple_element<I, span<ElementType, Extent>> {
    using type = ElementType;
  };
```
::: bq

[1]{.pnum} _Mandates:_ `Extent != dynamic_­extent && I < Extent` is `true`.

:::

```c++
template<size_t I, class ElementType, size_t Extent>
  constexpr ElementType& get(span<ElementType, Extent> s) noexcept;
```

::: bq

[2]{.pnum} _Mandates:_ `Extent != dynamic_­extent && I < Extent` is `true`.

[3]{.pnum} _Returns:_ `s[I]`.

:::

:::
