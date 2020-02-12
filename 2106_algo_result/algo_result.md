---
title: Alternative wording for GB315 and GB316
document: D2106R0
date: today
audience:
  - LWG
author:
  - name: Tim Song
    email: <t.canens.cpp@gmail.com>
toc: false
---

# Introduction

This paper provides alternative wording for NB comments [GB315](https://github.com/cplusplus/nbballot/issues/311) and [GB316](https://github.com/cplusplus/nbballot/issues/312).

# Wording
This wording is relative to [@N4849].

Edit [algorithm.syn]{.sref} as indicated:

```diff
 #include <initializer_list>

 namespace std {
   @_[...]_@

   namespace ranges {
     template<class I, class F>
-    struct for_each_result {
+    struct for_each_result;
-      [[no_unique_address]] I in;
-      [[no_unique_address]] F fun;
-
-      template<class I2, class F2>
-        requires convertible_to<const I&, I2> && convertible_to<const F&, F2>
-        operator for_each_result<I2, F2>() const & {
-          return {in, fun};
-        }
-
-      template<class I2, class F2>
-        requires convertible_to<I, I2> && convertible_to<F, F2>
-        operator for_each_result<I2, F2>() && {
-          return {std::move(in), std::move(fun)};
-        }
-    };

     template<input_iterator I, sentinel_for<I> S, class Proj = identity,
              indirectly_unary_invocable<projected<I, Proj>> Fun>
       constexpr for_each_result<I, Fun>
         for_each(I first, S last, Fun f, Proj proj = {});
     template<input_range R, class Proj = identity,
              indirectly_unary_invocable<projected<iterator_t<R>, Proj>> Fun>
       constexpr for_each_result<safe_iterator_t<R>, Fun>
         for_each(R&& r, Fun f, Proj proj = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I1, class I2>
-    struct mismatch_result {
+    struct mismatch_result;
-      [[no_unique_address]] I1 in1;
-      [[no_unique_address]] I2 in2;
-
-      template<class II1, class II2>
-        requires convertible_to<const I1&, II1> && convertible_to<const I2&, II2>
-        operator mismatch_result<II1, II2>() const & {
-          return {in1, in2};
-        }
-
-      template<class II1, class II2>
-        requires convertible_to<I1, II1> && convertible_to<I2, II2>
-        operator mismatch_result<II1, II2>() && {
-          return {std::move(in1), std::move(in2)};
-        }
-    };

     template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
              class Pred = ranges::equal_to, class Proj1 = identity, class Proj2 = identity>
       requires indirectly_comparable<I1, I2, Pred, Proj1, Proj2>
       constexpr mismatch_result<I1, I2>
         mismatch(I1 first1, S1 last1, I2 first2, S2 last2, Pred pred = {},
                  Proj1 proj1 = {}, Proj2 proj2 = {});
     template<input_range R1, input_range R2,
              class Pred = ranges::equal_to, class Proj1 = identity, class Proj2 = identity>
       requires indirectly_comparable<iterator_t<R1>, iterator_t<R2>, Pred, Proj1, Proj2>
       constexpr mismatch_result<safe_iterator_t<R1>, safe_iterator_t<R2>>
         mismatch(R1&& r1, R2&& r2, Pred pred = {},
                  Proj1 proj1 = {}, Proj2 proj2 = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-    struct copy_result {
+    struct copy_result;
-      [[no_unique_address]] I in;
-      [[no_unique_address]] O out;
-
-     template<class I2, class O2>
-        requires convertible_to<const I&, I2> && convertible_to<const O&, O2>
-        operator copy_result<I2, O2>() const & {
-          return {in, out};
-        }
-
-     template<class I2, class O2>
-        requires convertible_to<I, I2> && convertible_to<O, O2>
-        operator copy_result<I2, O2>() && {
-          return {std::move(in), std::move(out)};
-        }
-    };

     template<input_iterator I, sentinel_for<I> S, weakly_incrementable O>
       requires indirectly_copyable<I, O>
       constexpr copy_result<I, O>
         copy(I first, S last, O result);
     template<input_range R, weakly_incrementable O>
       requires indirectly_copyable<iterator_t<R>, O>
       constexpr copy_result<safe_iterator_t<R>, O>
         copy(R&& r, O result);
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-    using copy_n_result = copy_result<I, O>;
+    struct copy_n_result;

     template<input_iterator I, weakly_incrementable O>
       requires indirectly_copyable<I, O>
       constexpr copy_n_result<I, O>
         copy_n(I first, iter_difference_t<I> n, O result);
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-    using copy_if_result = copy_result<I, O>;
+    struct copy_if_result;

     template<input_iterator I, sentinel_for<I> S, weakly_incrementable O, class Proj = identity,
              indirect_unary_predicate<projected<I, Proj>> Pred>
       requires indirectly_copyable<I, O>
       constexpr copy_if_result<I, O>
         copy_if(I first, S last, O result, Pred pred, Proj proj = {});
     template<input_range R, weakly_incrementable O, class Proj = identity,
              indirect_unary_predicate<projected<iterator_t<R>, Proj>> Pred>
       requires indirectly_copyable<iterator_t<R>, O>
       constexpr copy_if_result<safe_iterator_t<R>, O>
         copy_if(R&& r, O result, Pred pred, Proj proj = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I1, class I2>
-    using copy_backward_result = copy_result<I1, I2>;
+    struct copy_backward_result;

     template<bidirectional_iterator I1, sentinel_for<I1> S1, bidirectional_iterator I2>
       requires indirectly_copyable<I1, I2>
       constexpr copy_backward_result<I1, I2>
         copy_backward(I1 first, S1 last, I2 result);
     template<bidirectional_range R, bidirectional_iterator I>
       requires indirectly_copyable<iterator_t<R>, I>
       constexpr copy_backward_result<safe_iterator_t<R>, I>
         copy_backward(R&& r, I result);
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-    using move_result = copy_result<I, O>;
+    struct move_result;

     template<input_iterator I, sentinel_for<I> S, weakly_incrementable O>
       requires indirectly_movable<I, O>
       constexpr move_result<I, O>
         move(I first, S last, O result);
     template<input_range R, weakly_incrementable O>
       requires indirectly_movable<iterator_t<R>, O>
       constexpr move_result<safe_iterator_t<R>, O>
         move(R&& r, O result);
   }

   @_[...]_@

   namespace ranges {
     template<class I1, class I2>
-    using move_backward_result = copy_result<I1, I2>;
+    struct move_backward_result;

     template<bidirectional_iterator I1, sentinel_for<I1> S1, bidirectional_iterator I2>
       requires indirectly_movable<I1, I2>
       constexpr move_backward_result<I1, I2>
         move_backward(I1 first, S1 last, I2 result);
     template<bidirectional_range R, bidirectional_iterator I>
       requires indirectly_movable<iterator_t<R>, I>
       constexpr move_backward_result<safe_iterator_t<R>, I>
         move_backward(R&& r, I result);
   }

   @_[...]_@

   namespace ranges {
     template<class I1, class I2>
-    using swap_ranges_result = mismatch_result<I1, I2>;
+    struct swap_ranges_result;

     template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2>
       requires indirectly_swappable<I1, I2>
       constexpr swap_ranges_result<I1, I2>
         swap_ranges(I1 first1, S1 last1, I2 first2, S2 last2);
     template<input_range R1, input_range R2>
       requires indirectly_swappable<iterator_t<R1>, iterator_t<R2>>
       constexpr swap_ranges_result<safe_iterator_t<R1>, safe_iterator_t<R2>>
         swap_ranges(R1&& r1, R2&& r2);
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-    using unary_transform_result = copy_result<I, O>;
+    struct unary_transform_result;

     template<input_iterator I, sentinel_for<I> S, weakly_incrementable O,
              copy_constructible F, class Proj = identity>
       requires writable<O, indirect_result_t<F&, projected<I, Proj>>>
       constexpr unary_transform_result<I, O>
         transform(I first1, S last1, O result, F op, Proj proj = {});
     template<input_range R, weakly_incrementable O, copy_constructible F,
              class Proj = identity>
       requires writable<O, indirect_result_t<F&, projected<iterator_t<R>, Proj>>>
       constexpr unary_transform_result<safe_iterator_t<R>, O>
         transform(R&& r, O result, F op, Proj proj = {});

     template<class I1, class I2, class O>
-    struct binary_transform_result {
+    struct binary_transform_result;
-      [[no_unique_address]] I1 in1;
-      [[no_unique_address]] I2 in2;
-      [[no_unique_address]] O  out;
-      template<class II1, class II2, class OO>
-        requires convertible_to<const I1&, II1> &&
-          convertible_to<const I2&, II2> && convertible_to<const O&, OO>
-        operator binary_transform_result<II1, II2, OO>() const & {
-          return {in1, in2, out};
-        }
-
-      template<class II1, class II2, class OO>
-        requires convertible_to<I1, II1> &&
-          convertible_to<I2, II2> && convertible_to<O, OO>
-        operator binary_transform_result<II1, II2, OO>() && {
-          return {std::move(in1), std::move(in2), std::move(out)};
-        }
-    };

     template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
              weakly_incrementable O, copy_constructible F, class Proj1 = identity,
              class Proj2 = identity>
       requires writable<O, indirect_result_t<F&, projected<I1, Proj1>,
                                              projected<I2, Proj2>>>
       constexpr binary_transform_result<I1, I2, O>
         transform(I1 first1, S1 last1, I2 first2, S2 last2, O result,
                   F binary_op, Proj1 proj1 = {}, Proj2 proj2 = {});
     template<input_range R1, input_range R2, weakly_incrementable O,
              copy_constructible F, class Proj1 = identity, class Proj2 = identity>
       requires writable<O, indirect_result_t<F&, projected<iterator_t<R1>, Proj1>,
                                              projected<iterator_t<R2>, Proj2>>>
       constexpr binary_transform_result<safe_iterator_t<R1>, safe_iterator_t<R2>, O>
         transform(R1&& r1, R2&& r2, O result,
                   F binary_op, Proj1 proj1 = {}, Proj2 proj2 = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-     using replace_copy_result = copy_result<I, O>;
+     struct replace_copy_result;

     template<input_iterator I, sentinel_for<I> S, class T1, class T2,
              output_iterator<const T2&> O, class Proj = identity>
       requires indirectly_copyable<I, O> &&
                indirect_binary_predicate<ranges::equal_to, projected<I, Proj>, const T1*>
       constexpr replace_copy_result<I, O>
         replace_copy(I first, S last, O result, const T1& old_value, const T2& new_value,
                      Proj proj = {});
     template<input_range R, class T1, class T2, output_iterator<const T2&> O,
              class Proj = identity>
       requires indirectly_copyable<iterator_t<R>, O> &&
                indirect_binary_predicate<ranges::equal_to,
                                          projected<iterator_t<R>, Proj>, const T1*>
       constexpr replace_copy_result<safe_iterator_t<R>, O>
         replace_copy(R&& r, O result, const T1& old_value, const T2& new_value,
                      Proj proj = {});

     template<class I, class O>
-    using replace_copy_if_result = copy_result<I, O>;
+    struct replace_copy_if_result;

     template<input_iterator I, sentinel_for<I> S, class T, output_iterator<const T&> O,
              class Proj = identity, indirect_unary_predicate<projected<I, Proj>> Pred>
       requires indirectly_copyable<I, O>
       constexpr replace_copy_if_result<I, O>
         replace_copy_if(I first, S last, O result, Pred pred, const T& new_value,
                         Proj proj = {});
     template<input_range R, class T, output_iterator<const T&> O, class Proj = identity,
              indirect_unary_predicate<projected<iterator_t<R>, Proj>> Pred>
       requires indirectly_copyable<iterator_t<R>, O>
       constexpr replace_copy_if_result<safe_iterator_t<R>, O>
         replace_copy_if(R&& r, O result, Pred pred, const T& new_value,
                         Proj proj = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-    using remove_copy_result = copy_result<I, O>;
+    struct remove_copy_result;

     template<input_iterator I, sentinel_for<I> S, weakly_incrementable O, class T,
              class Proj = identity>
       requires indirectly_copyable<I, O> &&
                indirect_binary_predicate<ranges::equal_to, projected<I, Proj>, const T*>
       constexpr remove_copy_result<I, O>
         remove_copy(I first, S last, O result, const T& value, Proj proj = {});
     template<input_range R, weakly_incrementable O, class T, class Proj = identity>
       requires indirectly_copyable<iterator_t<R>, O> &&
                indirect_binary_predicate<ranges::equal_to,
                                          projected<iterator_t<R>, Proj>, const T*>
       constexpr remove_copy_result<safe_iterator_t<R>, O>
         remove_copy(R&& r, O result, const T& value, Proj proj = {});

     template<class I, class O>
-    using remove_copy_if_result = copy_result<I, O>;
+    struct remove_copy_if_result;

     template<input_iterator I, sentinel_for<I> S, weakly_incrementable O,
              class Proj = identity, indirect_unary_predicate<projected<I, Proj>> Pred>
       requires indirectly_copyable<I, O>
       constexpr remove_copy_if_result<I, O>
         remove_copy_if(I first, S last, O result, Pred pred, Proj proj = {});
     template<input_range R, weakly_incrementable O, class Proj = identity,
              indirect_unary_predicate<projected<iterator_t<R>, Proj>> Pred>
       requires indirectly_copyable<iterator_t<R>, O>
       constexpr remove_copy_if_result<safe_iterator_t<R>, O>
         remove_copy_if(R&& r, O result, Pred pred, Proj proj = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-    using unique_copy_result = copy_result<I, O>;
+    struct unique_copy_result;

     template<input_iterator I, sentinel_for<I> S, weakly_incrementable O, class Proj = identity,
              indirect_equivalence_relation<projected<I, Proj>> C = ranges::equal_to>
       requires indirectly_copyable<I, O> &&
                (forward_iterator<I> ||
                 (input_iterator<O> && same_as<iter_value_t<I>, iter_value_t<O>>) ||
                 indirectly_copyable_storable<I, O>)
       constexpr unique_copy_result<I, O>
         unique_copy(I first, S last, O result, C comp = {}, Proj proj = {});
     template<input_range R, weakly_incrementable O, class Proj = identity,
              indirect_equivalence_relation<projected<iterator_t<R>, Proj>> C = ranges::equal_to>
       requires indirectly_copyable<iterator_t<R>, O> &&
                (forward_iterator<iterator_t<R>> ||
                 (input_iterator<O> && same_as<range_value_t<R>, iter_value_t<O>>) ||
                 indirectly_copyable_storable<iterator_t<R>, O>)
       constexpr unique_copy_result<safe_iterator_t<R>, O>
         unique_copy(R&& r, O result, C comp = {}, Proj proj = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-    using reverse_copy_result = copy_result<I, O>;
+    struct reverse_copy_result;

     template<bidirectional_iterator I, sentinel_for<I> S, weakly_incrementable O>
       requires indirectly_copyable<I, O>
       constexpr reverse_copy_result<I, O>
         reverse_copy(I first, S last, O result);
     template<bidirectional_range R, weakly_incrementable O>
       requires indirectly_copyable<iterator_t<R>, O>
       constexpr reverse_copy_result<safe_iterator_t<R>, O>
         reverse_copy(R&& r, O result);
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-    using rotate_copy_result = copy_result<I, O>;
+    struct rotate_copy_result;

     template<forward_iterator I, sentinel_for<I> S, weakly_incrementable O>
       requires indirectly_copyable<I, O>
       constexpr rotate_copy_result<I, O>
         rotate_copy(I first, I middle, S last, O result);
     template<forward_range R, weakly_incrementable O>
       requires indirectly_copyable<iterator_t<R>, O>
       constexpr rotate_copy_result<safe_iterator_t<R>, O>
         rotate_copy(R&& r, iterator_t<R> middle, O result);
   }

    @_[...]_@

   namespace ranges {
-    template<class I, class O> using partial_sort_copy_result = copy_result<I, O>;
+    template<class I, class O>
+    struct partial_sort_copy_result;

     template<input_iterator I1, sentinel_for<I1> S1,
              random_access_iterator I2, sentinel_for<I2> S2,
              class Comp = ranges::less, class Proj1 = identity, class Proj2 = identity>
       requires indirectly_copyable<I1, I2> && sortable<I2, Comp, Proj2> &&
                indirect_strict_weak_order<Comp, projected<I1, Proj1>, projected<I2, Proj2>>
       constexpr partial_sort_copy_result<I1, I2>
         partial_sort_copy(I1 first, S1 last, I2 result_first, S2 result_last,
                           Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
     template<input_range R1, random_access_range R2, class Comp = ranges::less,
              class Proj1 = identity, class Proj2 = identity>
       requires indirectly_copyable<iterator_t<R1>, iterator_t<R2>> &&
                sortable<iterator_t<R2>, Comp, Proj2> &&
                indirect_strict_weak_order<Comp, projected<iterator_t<R1>, Proj1>,
                                           projected<iterator_t<R2>, Proj2>>
       constexpr partial_sort_copy_result<safe_iterator_t<R1>, safe_iterator_t<R2>>
         partial_sort_copy(R1&& r, R2&& result_r, Comp comp = {},
                           Proj1 proj1 = {}, Proj2 proj2 = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O1, class O2>
-    struct partition_copy_result {
+    struct partition_copy_result;
-      [[no_unique_address]] I  in;
-      [[no_unique_address]] O1 out1;
-      [[no_unique_address]] O2 out2;
-
-      template<class II, class OO1, class OO2>
-        requires convertible_to<const I&, II> &&
-          convertible_to<const O1&, OO1> && convertible_to<const O2&, OO2>
-        operator partition_copy_result<II, OO1, OO2>() const & {
-          return {in, out1, out2};
-        }
-
-      template<class II, class OO1, class OO2>
-        requires convertible_to<I, II> &&
-          convertible_to<O1, OO1> && convertible_to<O2, OO2>
-        operator partition_copy_result<II, OO1, OO2>() && {
-          return {std::move(in), std::move(out1), std::move(out2)};
-        }
-    };

     template<input_iterator I, sentinel_for<I> S,
              weakly_incrementable O1, weakly_incrementable O2,
              class Proj = identity, indirect_unary_predicate<projected<I, Proj>> Pred>
       requires indirectly_copyable<I, O1> && indirectly_copyable<I, O2>
       constexpr partition_copy_result<I, O1, O2>
         partition_copy(I first, S last, O1 out_true, O2 out_false, Pred pred,
                        Proj proj = {});
     template<input_range R, weakly_incrementable O1, weakly_incrementable O2,
              class Proj = identity,
              indirect_unary_predicate<projected<iterator_t<R>, Proj>> Pred>
       requires indirectly_copyable<iterator_t<R>, O1> &&
                indirectly_copyable<iterator_t<R>, O2>
       constexpr partition_copy_result<safe_iterator_t<R>, O1, O2>
         partition_copy(R&& r, O1 out_true, O2 out_false, Pred pred, Proj proj = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I1, class I2, class O>
-    using merge_result = binary_transform_result<I1, I2, O>;
+    struct merge_result;

     template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
              weakly_incrementable O, class Comp = ranges::less, class Proj1 = identity,
              class Proj2 = identity>
       requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
       constexpr merge_result<I1, I2, O>
         merge(I1 first1, S1 last1, I2 first2, S2 last2, O result,
               Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
     template<input_range R1, input_range R2, weakly_incrementable O, class Comp = ranges::less,
              class Proj1 = identity, class Proj2 = identity>
       requires mergeable<iterator_t<R1>, iterator_t<R2>, O, Comp, Proj1, Proj2>
       constexpr merge_result<safe_iterator_t<R1>, safe_iterator_t<R2>, O>
         merge(R1&& r1, R2&& r2, O result,
               Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I1, class I2, class O>
-    using set_union_result = binary_transform_result<I1, I2, O>;
+    struct set_union_result;

     template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
              weakly_incrementable O, class Comp = ranges::less,
              class Proj1 = identity, class Proj2 = identity>
       requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
       constexpr set_union_result<I1, I2, O>
         set_union(I1 first1, S1 last1, I2 first2, S2 last2, O result, Comp comp = {},
                   Proj1 proj1 = {}, Proj2 proj2 = {});
     template<input_range R1, input_range R2, weakly_incrementable O,
              class Comp = ranges::less, class Proj1 = identity, class Proj2 = identity>
       requires mergeable<iterator_t<R1>, iterator_t<R2>, O, Comp, Proj1, Proj2>
       constexpr set_union_result<safe_iterator_t<R1>, safe_iterator_t<R2>, O>
         set_union(R1&& r1, R2&& r2, O result, Comp comp = {},
                   Proj1 proj1 = {}, Proj2 proj2 = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I1, class I2, class O>
-    using set_intersection_result = binary_transform_result<I1, I2, O>;
+    struct set_intersection_result;

     template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
              weakly_incrementable O, class Comp = ranges::less,
              class Proj1 = identity, class Proj2 = identity>
       requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
       constexpr set_intersection_result<I1, I2, O>
         set_intersection(I1 first1, S1 last1, I2 first2, S2 last2, O result,
                          Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
     template<input_range R1, input_range R2, weakly_incrementable O,
              class Comp = ranges::less, class Proj1 = identity, class Proj2 = identity>
       requires mergeable<iterator_t<R1>, iterator_t<R2>, O, Comp, Proj1, Proj2>
       constexpr set_intersection_result<safe_iterator_t<R1>, safe_iterator_t<R2>, O>
         set_intersection(R1&& r1, R2&& r2, O result,
                          Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I, class O>
-    using set_difference_result = copy_result<I, O>;
+    struct set_difference_result;

     template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
              weakly_incrementable O, class Comp = ranges::less,
              class Proj1 = identity, class Proj2 = identity>
       requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
       constexpr set_difference_result<I1, O>
         set_difference(I1 first1, S1 last1, I2 first2, S2 last2, O result,
                        Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
     template<input_range R1, input_range R2, weakly_incrementable O,
              class Comp = ranges::less, class Proj1 = identity, class Proj2 = identity>
       requires mergeable<iterator_t<R1>, iterator_t<R2>, O, Comp, Proj1, Proj2>
       constexpr set_difference_result<safe_iterator_t<R1>, O>
         set_difference(R1&& r1, R2&& r2, O result,
                        Comp comp = {}, Proj1 proj1 = {}, Proj2 proj2 = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I1, class I2, class O>
-    using set_symmetric_difference_result = binary_transform_result<I1, I2, O>;
+    struct set_symmetric_difference_result;

     template<input_iterator I1, sentinel_for<I1> S1, input_iterator I2, sentinel_for<I2> S2,
              weakly_incrementable O, class Comp = ranges::less,
              class Proj1 = identity, class Proj2 = identity>
       requires mergeable<I1, I2, O, Comp, Proj1, Proj2>
       constexpr set_symmetric_difference_result<I1, I2, O>
         set_symmetric_difference(I1 first1, S1 last1, I2 first2, S2 last2, O result,
                                  Comp comp = {}, Proj1 proj1 = {},
                                  Proj2 proj2 = {});
     template<input_range R1, input_range R2, weakly_incrementable O,
              class Comp = ranges::less, class Proj1 = identity, class Proj2 = identity>
       requires mergeable<iterator_t<R1>, iterator_t<R2>, O, Comp, Proj1, Proj2>
       constexpr set_symmetric_difference_result<safe_iterator_t<R1>, safe_iterator_t<R2>, O>
         set_symmetric_difference(R1&& r1, R2&& r2, O result, Comp comp = {},
                                  Proj1 proj1 = {}, Proj2 proj2 = {});
   }

   @_[...]_@

   namespace ranges {
     template<class T>
-    struct minmax_result {
+    struct minmax_result;
-      [[no_unique_address]] T min;
-      [[no_unique_address]] T max;
-
-      template<class T2>
-        requires convertible_to<const T&, T2>
-        operator minmax_result<T2>() const & {
-          return {min, max};
-        }
-
-      template<class T2>
-        requires convertible_to<T, T2>
-        operator minmax_result<T2>() && {
-          return {std::move(min), std::move(max)};
-        }
-    };

     template<class T, class Proj = identity,
              indirect_strict_weak_order<projected<const T*, Proj>> Comp = ranges::less>
       constexpr minmax_result<const T&>
         minmax(const T& a, const T& b, Comp comp = {}, Proj proj = {});
     template<copyable T, class Proj = identity,
              indirect_strict_weak_order<projected<const T*, Proj>> Comp = ranges::less>
       constexpr minmax_result<T>
         minmax(initializer_list<T> r, Comp comp = {}, Proj proj = {});
     template<input_range R, class Proj = identity,
              indirect_strict_weak_order<projected<iterator_t<R>, Proj>> Comp = ranges::less>
       requires indirectly_copyable_storable<iterator_t<R>, range_value_t<R>*>
       constexpr minmax_result<range_value_t<R>>
         minmax(R&& r, Comp comp = {}, Proj proj = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I>
-    using minmax_element_result = minmax_result<I>;
+    struct minmax_element_result;

     template<forward_iterator I, sentinel_for<I> S, class Proj = identity,
              indirect_strict_weak_order<projected<I, Proj>> Comp = ranges::less>
       constexpr minmax_element_result<I>
         minmax_element(I first, S last, Comp comp = {}, Proj proj = {});
     template<forward_range R, class Proj = identity,
              indirect_strict_weak_order<projected<iterator_t<R>, Proj>> Comp = ranges::less>
       constexpr minmax_element_result<safe_iterator_t<R>>
         minmax_element(R&& r, Comp comp = {}, Proj proj = {});
   }

   @_[...]_@

   namespace ranges {
     template<class I>
-    struct next_permutation_result {
+    struct next_permutation_result;
-      bool found;
-      I in;
-    };

     template<bidirectional_iterator I, sentinel_for<I> S, class Comp = ranges::less,
              class Proj = identity>
       requires sortable<I, Comp, Proj>
       constexpr next_permutation_result<I>
         next_permutation(I first, S last, Comp comp = {}, Proj proj = {});
     template<bidirectional_range R, class Comp = ranges::less,
              class Proj = identity>
       requires sortable<iterator_t<R>, Comp, Proj>
       constexpr next_permutation_result<safe_iterator_t<R>>
         next_permutation(R&& r, Comp comp = {}, Proj proj = {});
   }

   template<class BidirectionalIterator>
     constexpr bool prev_permutation(BidirectionalIterator first,
                                     BidirectionalIterator last);
   template<class BidirectionalIterator, class Compare>
     constexpr bool prev_permutation(BidirectionalIterator first,
                                     BidirectionalIterator last, Compare comp);

   namespace ranges {
     template<class I>
-    using prev_permutation_result = next_permutation_result<I>;
+    struct prev_permutation_result;

     template<bidirectional_iterator I, sentinel_for<I> S, class Comp = ranges::less,
              class Proj = identity>
       requires sortable<I, Comp, Proj>
       constexpr prev_permutation_result<I>
         prev_permutation(I first, S last, Comp comp = {}, Proj proj = {});
     template<bidirectional_range R, class Comp = ranges::less,
              class Proj = identity>
       requires sortable<iterator_t<R>, Comp, Proj>
       constexpr prev_permutation_result<safe_iterator_t<R>>
         prev_permutation(R&& r, Comp comp = {}, Proj proj = {});
   }
 }
```

Delete [algorithms.requirements]{.sref} p16:

::: rm

[16]{.pnum} The class templates `binary_­transform_­result`, `for_­each_­result`, `minmax_­result`, `mismatch_­result`, `next_­permutation_­result`, `copy_­result`, and `partition_­copy_­result` have the template parameters, data members, and special members specified below. They have no base classes or members other than those specified.

:::

Add a new subclause after [algorithm.syn]{.sref}, or alternatively under [algorithms.requirements]{.sref}, as follows:

::: add

### ?.? Algorithm result types [algorithm.results] {-}

[1]{.pnum} Each of the class templates specified in this subclause has the template parameters, data members, and special members specified below, and has no base classes or members other than those specified. In this subclause, the name _`result`_ refers to
the name of the class template being defined.

[2]{.pnum} The class template `ranges::for_each_result` is defined as follows:

```c++
    template<class I, class F>
    struct for_each_result {
      [[no_unique_address]] I in;
      [[no_unique_address]] F fun;

      template<class I2, class F2>
        requires convertible_to<const I&, I2> && convertible_to<const F&, F2>
        operator for_each_result<I2, F2>() const & {
          return {in, fun};
        }

      template<class I2, class F2>
        requires convertible_to<I, I2> && convertible_to<F, F2>
        operator for_each_result<I2, F2>() && {
          return {std::move(in), std::move(fun)};
        }
    };
```

[3]{.pnum} The class templates `ranges::mismatch_result` and `ranges::swap_ranges_result` are each defined as follows:

```c++
    template<class I1, class I2>
    struct @_result_@ {
      [[no_unique_address]] I1 in1;
      [[no_unique_address]] I2 in2;

      template<class II1, class II2>
        requires convertible_to<const I1&, II1> && convertible_to<const I2&, II2>
        operator @_result_@<II1, II2>() const & {
          return {in1, in2};
        }

      template<class II1, class II2>
        requires convertible_to<I1, II1> && convertible_to<I2, II2>
        operator @_result_@<II1, II2>() && {
          return {std::move(in1), std::move(in2)};
        }
    };
```

[4]{.pnum} The class templates `ranges::copy_result`, `ranges::copy_n_result`, `range::copy_if_result`,
`ranges::copy_backward_result`, `ranges::move_result`, `ranges::move_backward_result`, `ranges::unary_transform_result`,
`ranges::replace_copy_result`, `ranges::replace_copy_if_result`, `ranges::remove_copy_result`, `ranges::remove_copy_if_result`,
`ranges::unique_copy_result`, `ranges::reverse_copy_result`, `ranges::rotate_copy_result`, `ranges::partial_sort_copy_result`,
and `ranges::set_difference_result` are each defined as follows:

```c++
    template<class I, class O>
    struct @_result_@ {
      [[no_unique_address]] I in;
      [[no_unique_address]] O out;

      template<class I2, class O2>
        requires convertible_to<const I&, I2> && convertible_to<const O&, O2>
        operator @_result_@<I2, O2>() const & {
          return {in, out};
        }

      template<class I2, class O2>
        requires convertible_to<I, I2> && convertible_to<O, O2>
        operator @_result_@<I2, O2>() && {
          return {std::move(in), std::move(out)};
        }
    };
```

[5]{.pnum} The class templates `ranges::binary_transform_result`, `ranges::merge_result`, `ranges::set_union_result`, `ranges::set_intersection_result`, and `ranges::set_symmetric_difference_result` are each defined as follows:

```c++
    template<class I1, class I2, class O>
    struct @_result_@ {
      [[no_unique_address]] I1 in1;
      [[no_unique_address]] I2 in2;
      [[no_unique_address]] O  out;

      template<class II1, class II2, class OO>
        requires convertible_to<const I1&, II1> &&
          convertible_to<const I2&, II2> && convertible_to<const O&, OO>
        operator @_result_@<II1, II2, OO>() const & {
          return {in1, in2, out};
        }

      template<class II1, class II2, class OO>
        requires convertible_to<I1, II1> &&
          convertible_to<I2, II2> && convertible_to<O, OO>
        operator @_result_@<II1, II2, OO>() && {
          return {std::move(in1), std::move(in2), std::move(out)};
        }
    };
```

[6]{.pnum} The class template `ranges::partition_copy_result` is defined as follows:

```c++
    template<class I, class O1, class O2>
    struct partition_copy_result {
      [[no_unique_address]] I  in;
      [[no_unique_address]] O1 out1;
      [[no_unique_address]] O2 out2;

      template<class II, class OO1, class OO2>
        requires convertible_to<const I&, II> &&
          convertible_to<const O1&, OO1> && convertible_to<const O2&, OO2>
        operator partition_copy_result<II, OO1, OO2>() const & {
          return {in, out1, out2};
        }

      template<class II, class OO1, class OO2>
        requires convertible_to<I, II> &&
          convertible_to<O1, OO1> && convertible_to<O2, OO2>
        operator partition_copy_result<II, OO1, OO2>() && {
          return {std::move(in), std::move(out1), std::move(out2)};
        }
    };
```

[7]{.pnum} The class templates `ranges::minmax_result` and `ranges::minmax_element_result` are each defined as follows:

```c++
    template<class T>
    struct @_result_@ {
      [[no_unique_address]] T min;
      [[no_unique_address]] T max;

      template<class T2>
        requires convertible_to<const T&, T2>
        operator @_result_@<T2>() const & {
          return {min, max};
        }

      template<class T2>
        requires convertible_to<T, T2>
        operator @_result_@<T2>() && {
          return {std::move(min), std::move(max)};
        }
    };
```

[8]{.pnum} The class templates `ranges::next_permutation_result` and `ranges::prev_permutation_result` are each defined as follows:

```c++
    template<class I>
    struct @_result_@ {
        bool found;
        [[no_unique_address]] I in;

        template <class I2>
        requires convertible_to<const I&, I2>
        operator @_result_@<I2>()  const & {
          return {found, in};
        }
        template <class I2>
        requires convertible_to<I, I2>
        operator @_result_@<I2>() && {
          return {found, std::move(in)};
        }
    };
```

:::
