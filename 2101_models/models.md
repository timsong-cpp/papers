---
title: "\"Models\" subsumes \"satisfies\" (Wording for US298 and US300)"
document: D2101R0
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

This paper provides wording to resolve NB comments [US298](https://github.com/cplusplus/nbballot/issues/294) and [US300](https://github.com/cplusplus/nbballot/issues/296). It also resolves [@LWG3345].

# Wording
This wording is relative to [@N4849].

Add the following paragraphs to [res.on.requirements]{.sref} before p1:

::: add

[1]{.pnum} A set of template arguments `Ts` is said to _model_ a concept `C` if `Ts` satisfies `C`
([temp.constr.decl]{.sref}) and meets all semantic requirements (if any) given in the specification of `C`.

[2]{.pnum} If the validity or meaning of a program depends on whether a set of template arguments models
a concept, and the concept is satisfied but not modeled, the program is ill-formed, no diagnostic required.

:::
