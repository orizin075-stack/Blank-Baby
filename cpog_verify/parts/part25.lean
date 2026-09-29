namespace CPOG

/-!
# v57 fixed-point theory of stable predicates

v56 introduced ForwardClosure and InvariantKernel as canonical repairs.
Here we make their order-theoretic role explicit.

ForwardClosure is a monotone, extensive, idempotent closure operator.
InvariantKernel is a monotone, reductive, idempotent interior operator.
Their fixed points are exactly the forward-invariant predicates.

The two universal properties make the canonical nature precise:
* among invariant supersets, ForwardClosure P is the least one;
* among invariant subsets, InvariantKernel P is the greatest one.
-/

universe u

def PredEq {W : Type u} (P Q : W -> Prop) : Prop :=
  PredSubset P Q /\ PredSubset Q P

theorem predSubset_refl
    {W : Type u} (P : W -> Prop) :
    PredSubset P P := by
  intro x hx
  exact hx

theorem predSubset_trans
    {W : Type u} {P Q S : W -> Prop}
    (hPQ : PredSubset P Q)
    (hQS : PredSubset Q S) :
    PredSubset P S := by
  intro x hx
  exact hQS x (hPQ x hx)

theorem forwardClosure_monotone
    {W : Type u} (R : Rel W)
    {P Q : W -> Prop}
    (hPQ : PredSubset P Q) :
    PredSubset (ForwardClosure R P) (ForwardClosure R Q) := by
  intro y hy
  rcases hy with ⟨x, hxP, hxy⟩
  exact ⟨x, hPQ x hxP, hxy⟩

theorem invariantKernel_monotone
    {W : Type u} (R : Rel W)
    {P Q : W -> Prop}
    (hPQ : PredSubset P Q) :
    PredSubset (InvariantKernel R P) (InvariantKernel R Q) := by
  intro x hx
  constructor
  · exact hPQ x hx.1
  · intro y hxy
    exact hPQ y (hx.2 y hxy)

theorem forwardClosure_fixed_iff_invariant
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    PredEq (ForwardClosure R P) P <->
      ForwardInvariantRegion R P := by
  constructor
  · intro hEq
    exact (forwardInvariant_iff_closure_subset R P).mpr hEq.1
  · intro hInv
    constructor
    · exact (forwardInvariant_iff_closure_subset R P).mp hInv
    · exact forwardClosure_contains R P

theorem invariantKernel_fixed_iff_invariant
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    PredEq (InvariantKernel R P) P <->
      ForwardInvariantRegion R P := by
  constructor
  · intro hEq
    exact (forwardInvariant_iff_subset_kernel R P).mpr hEq.2
  · intro hInv
    constructor
    · exact invariantKernel_subset R P
    · exact (forwardInvariant_iff_subset_kernel R P).mp hInv

theorem forwardClosure_universal_property
    {W : Type u} (R : Rel W)
    (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q) :
    PredSubset (ForwardClosure R P) Q <->
      PredSubset P Q := by
  constructor
  · intro hClosure
    exact predSubset_trans (forwardClosure_contains R P) hClosure
  · intro hPQ
    exact forwardClosure_least R P Q hQInv hPQ

theorem invariantKernel_universal_property
    {W : Type u} (R : Rel W)
    (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q) :
    PredSubset Q (InvariantKernel R P) <->
      PredSubset Q P := by
  constructor
  · intro hKernel
    exact predSubset_trans hKernel (invariantKernel_subset R P)
  · intro hQP
    exact invariantKernel_greatest R P Q hQInv hQP

theorem forwardClosure_idempotent
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    PredEq
      (ForwardClosure R (ForwardClosure R P))
      (ForwardClosure R P) := by
  constructor
  · intro x hx
    exact (forwardClosure_idempotent_pointwise R P x).mp hx
  · intro x hx
    exact (forwardClosure_idempotent_pointwise R P x).mpr hx

theorem invariantKernel_idempotent
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    PredEq
      (InvariantKernel R (InvariantKernel R P))
      (InvariantKernel R P) := by
  constructor
  · intro x hx
    exact (invariantKernel_idempotent_pointwise R P x).mp hx
  · intro x hx
    exact (invariantKernel_idempotent_pointwise R P x).mpr hx

/--
Stable predicates are exactly the simultaneous fixed points of the canonical
closure and interior repairs.
-/
theorem invariant_iff_both_canonical_fixed_points
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      (PredEq (ForwardClosure R P) P /\
       PredEq (InvariantKernel R P) P) := by
  constructor
  · intro hInv
    exact ⟨
      (forwardClosure_fixed_iff_invariant R P).mpr hInv,
      (invariantKernel_fixed_iff_invariant R P).mpr hInv
    ⟩
  · intro h
    exact (forwardClosure_fixed_iff_invariant R P).mp h.1

/--
The generic Subsumption theorem can therefore be read as a fixed-point theorem:
universal Subsumption holds exactly when the acceptance predicate is fixed by
both canonical stabilization operators.
-/
theorem universalSubsumption_iff_canonical_fixed_point
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      (PredEq (ForwardClosure G.rel A) A /\
       PredEq (InvariantKernel G.rel A) A) := by
  calc
    UniversalStateSubsumption G A
        <-> ForwardInvariantRegion G.rel A :=
      universal_state_subsumption_iff_forwardInvariant G A
    _ <-> (PredEq (ForwardClosure G.rel A) A /\
           PredEq (InvariantKernel G.rel A) A) :=
      invariant_iff_both_canonical_fixed_points G.rel A

end CPOG
