---
title: "Make `sender_in` and `receiver_of` exposition-only"
document: P4159R0
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
---

# Introduction

In response to LEWG direction on [@LWG4361], this paper provides wording to make the `receiver_of` and `sender_to` concepts exposition-only for C++26.

# Wording

Instructions to the editor:

After applying _all other papers_ moved during the Croydon meeting _except
[@P4154R0]_, make the following changes in Clause [exec]{.sref}:

- Add an `// exposition only` comment to the declaration of `sender_to` in [execution.syn]{.sref} and
  its definition in [exec.snd.concepts]{.sref}.
- Add an `// exposition only` comment to the declaration of `receiver_of` in [execution.syn]{.sref} and
  its definition in [exec.recv.concepts]{.sref}.
- Replace all instances of `sender_to` with `$sender-to$`.
- Replace all instances of `receiver_of` with `$receiver-of$`.


---
references:
    - id: P4154R0
      citation-label: P4154R0
      title: "Renaming various execution things"
      author:
        - family: "Tim Song, Ruslan Arutyunyan, Arthur O’Dwyer"
      issued:
        year: 2026
      URL: https://wg21.link/P4154R0
---
