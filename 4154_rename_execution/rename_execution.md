---
title: Renaming various execution things
document: P3914R0
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
---

# Introduction

This paper provides replacement wording for the following papers:

- [@P3940R0]: Rename concept tags for C++26: `sender_t` to `sender_tag`
- [@P4031R1]: Rename `system_context_replaceability` namespace

which resolves the following national body comment on the C++26 CD:

- [US 205-320](https://github.com/cplusplus/nbballot/issues/835)

Because there are multiple papers in flight targeting [exec]{.sref},
LWG requested replacement wording for renames to minimize merge conflicts.

# Wording

Instruction to the editor:

After applying _all other papers_ moved during the Croydon meeting,
please make the following replacements in [exec]{.sref}:

- Replace each instance of `sender_t` with `sender_tag`.
- Replace each instance of `scheduler_t` with `scheduler_tag`.
- Replace each instance of `operation_state_t` with `operation_state_tag`.
- Replace each instance of `system_context_replaceability` with `parallel_scheduler_replacement`.
- Replace each instance of `sysctxrepl` in a stable name with `parschedrepl`.
- Replace each instance of `receiver_t` **outside** [exec.continues.on][^1] with `receiver_tag`.
- In [exec.continues.on], replace `using receiver_concept = receiver_t;` with `using receiver_concept = receiver_tag;`.

[^1]: In particular, this cross-reference is after [@P3826R5] has been applied.


---
references:
    - id: P4031R1
      citation-label: P4031R1
      title: "Rename `system_context_replaceability` namespace"
      author:
        - family: "	Ruslan Arutyunyan"
      issued:
        year: 2026
      URL: https://wg21.link/P4031R1
    - id: P3826R5 
      citation-label: P3826R5
      title: "Fix Sender Algorithm Customization"
      author:
        - family: "Eric Niebler"
      issued:
        year: 2026
      URL: https://wg21.link/P3826R5
---
