---
title: "LWG 3698: `join_view` and stashing iterators"
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Abstract

This paper provides wording to resolve [@LWG3698], [@LWG3700] and [@LWG3791].

# Discussion

There are two parts to this issue:

- `regex_iterator` and `regex_token_iterator`

These are stashing iterators that lie about their category. It is probably too breaking at this
point to change the `iterator_category`, but we should add `iterator_concept` so that they
give the correct answer for C++20 iterator concepts.

- `join` and `join_with`

These don't handle stashing iterator properly. For input iterators they need to cache the iterator
within the view, similar to what we do for a number of other views (`lazy_split`, for instance).

While in the vincinity, this paper also resolves [@LWG3700] and [@LWG3791], two relatively minor issues concerning `join_view` and `join_with_view`.

# Wording
<!-- FIXME: Update to the post-Kona draft. -->
This wording is relative to [@N4917] after the application of [@LWG3569]. 

::: wordinglist

- Edit [re.regiter.general]{.sref}, class template `regex_iterator` synopsis, as indicated:

```diff
 namespace std {
   template<class BidirectionalIterator,
             class charT = typename iterator_traits<BidirectionalIterator>::value_type,
             class traits = regex_traits<charT>>
     class regex_iterator {
     public:
       using regex_type        = basic_regex<charT, traits>;
       using iterator_category = forward_iterator_tag;
+      using iterator_concept  = input_iterator_tag;
       using value_type        = match_results<BidirectionalIterator>;
       using difference_type   = ptrdiff_t;
       using pointer           = const value_type*;
       using reference         = const value_type&;
 
       regex_iterator();
       regex_iterator(BidirectionalIterator a, BidirectionalIterator b,
                      const regex_type& re,
                      regex_constants::match_flag_type m = regex_constants::match_default);
       regex_iterator(BidirectionalIterator, BidirectionalIterator,
                      const regex_type&&,
                      regex_constants::match_flag_type = regex_constants::match_default) = delete;
       regex_iterator(const regex_iterator&);
       regex_iterator& operator=(const regex_iterator&);
       bool operator==(const regex_iterator&) const;
       bool operator==(default_sentinel_t) const { return *this == regex_iterator(); }
       const value_type& operator*() const;
       const value_type* operator->() const;
       regex_iterator& operator++();
       regex_iterator operator++(int);
 
     private:
       BidirectionalIterator                begin;               // exposition only
       BidirectionalIterator                end;                 // exposition only
       const regex_type*                    pregex;              // exposition only
       regex_constants::match_flag_type     flags;               // exposition only
       match_results<BidirectionalIterator> match;               // exposition only
     };
 }
```


- Edit [re.tokiter.general]{.sref}, class template `regex_token_iterator` synopsis, as indicated:

```diff
 namespace std {
   template<class BidirectionalIterator,
             class charT = typename iterator_traits<BidirectionalIterator>::value_type,
             class traits = regex_traits<charT>>
     class regex_token_iterator {
     public:
       using regex_type        = basic_regex<charT, traits>;
       using iterator_category = forward_iterator_tag;
+      using iterator_concept  = input_iterator_tag;
       using value_type        = sub_match<BidirectionalIterator>;
       using difference_type   = ptrdiff_t;
       using pointer           = const value_type*;
       using reference         = const value_type&;
 
       regex_token_iterator();
       regex_token_iterator(BidirectionalIterator a, BidirectionalIterator b,
                            const regex_type& re,
                            int submatch = 0,
                            regex_constants::match_flag_type m =
                              regex_constants::match_default);
       regex_token_iterator(BidirectionalIterator a, BidirectionalIterator b,
                            const regex_type& re,
                            const vector<int>& submatches,
                            regex_constants::match_flag_type m =
                              regex_constants::match_default);
       regex_token_iterator(BidirectionalIterator a, BidirectionalIterator b,
                            const regex_type& re,
                            initializer_list<int> submatches,
                            regex_constants::match_flag_type m =
                              regex_constants::match_default);
       template<size_t N>
         regex_token_iterator(BidirectionalIterator a, BidirectionalIterator b,
                              const regex_type& re,
                              const int (&submatches)[N],
                              regex_constants::match_flag_type m =
                                regex_constants::match_default);
       regex_token_iterator(BidirectionalIterator a, BidirectionalIterator b,
                            const regex_type&& re,
                            int submatch = 0,
                            regex_constants::match_flag_type m =
                              regex_constants::match_default) = delete;
       regex_token_iterator(BidirectionalIterator a, BidirectionalIterator b,
                            const regex_type&& re,
                            const vector<int>& submatches,
                            regex_constants::match_flag_type m =
                              regex_constants::match_default) = delete;
       regex_token_iterator(BidirectionalIterator a, BidirectionalIterator b,
                            const regex_type&& re,
                            initializer_list<int> submatches,
                            regex_constants::match_flag_type m =
                              regex_constants::match_default) = delete;
       template<size_t N>
       regex_token_iterator(BidirectionalIterator a, BidirectionalIterator b,
                            const regex_type&& re,
                            const int (&submatches)[N],
                            regex_constants::match_flag_type m =
                              regex_constants::match_default) = delete;
       regex_token_iterator(const regex_token_iterator&);
       regex_token_iterator& operator=(const regex_token_iterator&);
       bool operator==(const regex_token_iterator&) const;
       bool operator==(default_sentinel_t) const { return *this == regex_token_iterator(); }
       const value_type& operator*() const;
       const value_type* operator->() const;
       regex_token_iterator& operator++();
       regex_token_iterator operator++(int);
 
     private:
       using position_iterator =
         regex_iterator<BidirectionalIterator, charT, traits>;   // exposition only
       position_iterator position;                               // exposition only
       const value_type* result;                                 // exposition only
       value_type suffix;                                        // exposition only
       size_t N;                                                 // exposition only
       vector<int> subs;                                         // exposition only
     };
 }
```

- Edit [range.join.view]{.sref}, class template `join_view` synopsis, as indicated:

```diff
 namespace std::ranges {
   template<input_­range V>
     requires view<V> && input_­range<range_reference_t<V>>
   class join_view : public view_interface<join_view<V>> {
   private:
     using $InnerRng$ = range_reference_t<V>;                  // exposition only
 
     // [range.join.iterator], class template join_­view​::​iterator
     template<bool Const>
       struct $iterator$;                                      // exposition only
 
     // [range.join.sentinel], class template join_­view​::​sentinel
     template<bool Const>
       struct $sentinel$;                                      // exposition only
 
     V $Base$_$ = V();                                          // exposition only
 
+    $non-propgating-cache$<iterator_t<V>> $$outer_$$;             // exposition only, present only
+                                                            // when !forward_range<V>
               
     $non-propagating-cache$<remove_cv_t<$InnerRng$>> $$inner_$$;    // exposition only, present  only
                                                             // when !is_­reference_­v<$InnerRng$>
 
   public:
     join_view() requires default_­initializable<V> = default;
     constexpr explicit join_view(V $Base$);
 
     constexpr V $Base$() const & requires copy_­constructible<V> { return $Base$_$; }
     constexpr V $Base$() && { return std::move($Base$_$); }
 
     constexpr auto begin() {
+      if constexpr (forward_range<V>) {  
         constexpr bool use_const = $simple-view$<V> &&
                                    is_reference_v<$InnerRng$>;
         return $iterator$<use_const>{*this, ranges::begin($Base$_$)};
+      }
+      else {
+        $$outer_$$ = ranges::begin($Base$_$);
+        return $iterator$<false>(*this);
+      }
     }
 
     constexpr auto begin() const
       requires @[forward<-input]{.indel}@_­range<const V> &&
                is_reference_v<range_reference_t<const V>> @[&&]{.diffins}@
+               input_range<range_reference_t<const V>>
     { return $iterator$<true>{*this, ranges::begin($Base$_$)}; }
 
     constexpr auto end() {
       if constexpr (forward_­range<V> &&
                     is_reference_v<$InnerRng$> && forward_­range<$InnerRng$> &&
                     common_­range<V> && common_­range<$InnerRng$>)
         return $iterator$<$simple-view$<V>>{*this, ranges::end($Base$_$)};
       else
         return $sentinel$<$simple-view$<V>>{*this};
     }
 
     constexpr auto end() const
       requires @[forward<-input]{.indel}@_­range<const V> &&
                is_reference_v<range_reference_t<const V>> @[&&]{.diffins}@
+               input_range<range_reference_t<const V>> 
     {
       if constexpr (@[forward_­range\<const V> &&]{.diffdel}@
                     forward_­range<range_reference_t<const V>> &&
                     common_­range<const V> &&
                     common_­range<range_reference_t<const V>>)
         return $iterator$<true>{*this, ranges::end($Base$_$)};
       else
         return $sentinel$<true>{*this};
     }
   };
 
   template<class R>
     explicit join_view(R&&) -> join_view<views::all_t<R>>;
 }
```

- Edit [range.join.iterator]{.sref} as indicated:

```cpp
namespace std::ranges {
  template<input_­range V>
    requires view<V> && input_­range<range_reference_t<V>>
  template<bool Const>
  struct join_view<V>::iterator {
  private:
    using $$Parent$$    = $maybe-const$<Const, join_view>;            // exposition only
    using $Base$      = $maybe-const$<Const, V>;                    // exposition only
    using $OuterIter$ = iterator_t<$Base$>;                         // exposition only
    using $InnerIter$ = iterator_t<range_reference_t<$Base$>>;      // exposition only

    static constexpr bool $ref-is-glvalue$ =                      // exposition only
      is_reference_v<range_reference_t<$Base$>>;

    $OuterIter$ $outer_$ = $OuterIter$();                             // exposition only@[, present only if _`Base`_ models `forward_range`]{.diffins}@
    optional<$InnerIter$> $inner_$;                             // exposition only
    $Parent$* $parent_$  = nullptr;                                 // exposition only

    constexpr void $satisfy$();                                   // exposition only

    constexpr auto& $outer$();                                    // exposition only
    constexpr auto& $outer$() const;                              // exposition only

  public:
    using iterator_concept  = $see below$;
    using iterator_category = $see below$;                        // not always present
    using value_type        = range_value_t<range_reference_t<$Base$>>;
    using difference_type   = $see below$;

    iterator() @[requires default_­initializable<$OuterIter$>]{.diffdel}@ = default;
    constexpr iterator($Parent$& parent, $OuterIter$ outer) @[requires forward_range<V>]{.diffins}@;
    constexpr iterator(iterator<!Const> i)
      requires Const &&
               convertible_­to<iterator_t<V>, $OuterIter$> &&
               convertible_­to<iterator_t<$InnerRng$>, $InnerIter$>;

    constexpr decltype(auto) operator*() const { return **$inner_$; }

    constexpr $InnerIter$ operator->() const
      requires has-arrow<$InnerIter$> && copyable<$InnerIter$>;

    constexpr iterator& operator++();
    constexpr void operator++(int);
    constexpr iterator operator++(int)
      requires $ref-is-glvalue$ && forward_­range<$Base$> &&
               forward_­range<range_reference_t<$Base$>>;

    constexpr iterator& operator--()
      requires $ref-is-glvalue$ && bidirectional_­range<$Base$> &&
               bidirectional_­range<range_reference_t<$Base$>> &&
               common_­range<range_reference_t<$Base$>>;

    constexpr iterator operator--(int)
      requires $ref-is-glvalue$ && bidirectional_­range<$Base$> &&
               bidirectional_­range<range_reference_t<$Base$>> &&
               common_­range<range_reference_t<$Base$>>;

    friend constexpr bool operator==(const iterator& x, const iterator& y)
      requires $ref-is-glvalue$ && equality_­comparable<iterator_t<$Base$>> &&
               equality_­comparable<iterator_t<range_reference_t<$Base$>>>;

    friend constexpr decltype(auto) iter_move(const iterator& i)
    noexcept(noexcept(ranges::iter_move(i.$inner_$))) {
      return ranges::iter_move(*i.$inner_$);
    }

    friend constexpr void iter_swap(const iterator& x, const iterator& y)
      noexcept(noexcept(ranges::iter_swap(*x.$inner_$, *y.$inner_$)))
      requires indirectly_­swappable<$InnerIter$>;
  };
}
```

[...]

::: add
::: itemdecl

```cpp
    constexpr auto& $outer$();      
    constexpr auto& $outer$() const;
```

[?]{.pnum} _Returns:_ `$outer_$` if `$Base$` models `forward_range`; otherwise, `*$parent_$->$outer_$`.

:::
:::

::: itemdecl


```cpp
    constexpr void $satisfy$();
5
#
Effects: Equivalent to:
auto update_inner = [this](const iterator_t<$Base$>& x) -> auto&& {
  if constexpr ($ref-is-glvalue$)     // *x is a reference
    return *x;
  else
    return $parent_$->$inner_$.$emplace-deref$(x);
};
for (; $outer_$ != ranges::end($parent_$->$Base$_); ++$outer_$) {
  auto&& inner = update_inner($outer_$);
  $inner_$ = ranges::begin(inner);
  if ($inner_$ != ranges::end(inner))
    return;
}
if constexpr ($ref-is-glvalue$)
  $inner_$ = $InnerIter$();
🔗
constexpr iterator($Parent$& parent, $OuterIter$ outer);
6
#
Effects: Initializes $outer_­$ with std​::​move(outer) and $parent_­$ with addressof(parent); then calls $satisfy$().
🔗
constexpr iterator(iterator<!Const> i)
  requires Const &&
           convertible_­to<iterator_t<V>, $OuterIter$> &&
           convertible_­to<iterator_t<$InnerRng$>, $InnerIter$>;
7
#
Effects: Initializes $outer_­$ with std​::​move(i.$outer_­$), $inner_­$ with std​::​move(i.$inner_­$), and $parent_­$ with i.$parent_­$.
🔗
constexpr $InnerIter$ operator->() const
  requires has-arrow<$InnerIter$> && copyable<$InnerIter$>;
8
#
Effects: Equivalent to return $inner_­$;
🔗
constexpr iterator& operator++();
9
#
Let $inner-range$ be:
(9.1)
If $ref-is-glvalue$ is true, *$outer_­$.
(9.2)
Otherwise, *$parent_­$->$inner_­$.
10
#
Effects: Equivalent to:
auto&& inner_rng = $inner-range$;
if (++$inner_$ == ranges::end(inner_rng)) {
  ++$outer_$;
  $satisfy$();
}
return *this;
🔗
constexpr void operator++(int);
11
#
Effects: Equivalent to: ++*this.
🔗
constexpr iterator operator++(int)
  requires $ref-is-glvalue$ && forward_­range<$Base$> &&
           forward_­range<range_reference_t<$Base$>>;
12
#
Effects: Equivalent to:
auto tmp = *this;
++*this;
return tmp;
🔗
constexpr iterator& operator--()
  requires $ref-is-glvalue$ && bidirectional_­range<$Base$> &&
           bidirectional_­range<range_reference_t<$Base$>> &&
           common_­range<range_reference_t<$Base$>>;
13
#
Effects: Equivalent to:
if ($outer_$ == ranges::end($parent_$->$Base$_))
  $inner_$ = ranges::end(*--$outer_$);
while ($inner_$ == ranges::begin(*$outer_$))
  $inner_$ = ranges::end(*--$outer_$);
--$inner_$;
return *this;
🔗
constexpr iterator operator--(int)
  requires $ref-is-glvalue$ && bidirectional_­range<$Base$> &&
           bidirectional_­range<range_reference_t<$Base$>> &&
           common_­range<range_reference_t<$Base$>>;
14
#
Effects: Equivalent to:
auto tmp = *this;
--*this;
return tmp;
🔗
friend constexpr bool operator==(const iterator& x, const iterator& y)
  requires $ref-is-glvalue$ && equality_­comparable<iterator_t<$Base$>> &&
           equality_­comparable<iterator_t<range_reference_t<$Base$>>>;
15
#
Effects: Equivalent to: return x.$outer_­$ == y.$outer_­$ && x.$inner_­$ == y.$inner_­$;
🔗
friend constexpr void iter_swap(const iterator& x, const iterator& y)
  noexcept(noexcept(ranges::iter_swap(x.$inner_­$, y.$inner_­$)))
  requires indirectly_­swappable<$InnerIter$>;
16
#
Effects: Equivalent to: return ranges​::​iter_­swap(x.$inner_­$, y.$inner_­$);

:::
