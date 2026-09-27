namespace CPOG

/-!
# v57 invariant lattice and canonical repair optimality

v56 introduced forward invariance plus the least stable expansion
ForwardClosure and greatest stable contraction InvariantKernel.

This section identifies the full algebraic structure.

1. One-step forward invariance is exactly preservation along finite reachability.
2. ForwardClosure is left adjoint to inclusion of stable predicates:
   among invariant supersets it is least.
3. InvariantKernel is right adjoint to inclusion:
   among invariant subsets it is greatest.
4. Stable predicates are exactly the fixed points of either operator.
5. Stable predicates are closed under arbitrary unions and intersections.
6. Universal Subsumption is equivalent to being such a fixed point.

Thus the stable predicates form a complete family (indeed the upper sets of
the reflexive-transitive reachability relation), and the two canonical repairs
are the extremal projections into that family.
-/

universe u v

def PredEq {W : Type u} (P Q : W -> Prop) : Prop :=
  forall x, P x <-> Q x

theorem forwardInvariant_iff_rtcInvariant
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      (forall {x y : W}, RTC R x y -> P x -> P y) := by
  constructor
  · intro hInv x y hxy hx
    exact RTC.preserve (R := R) (P := P) hInv hxy hx
  · intro hRTC x y hxy hx
    exact hRTC (RTC.tail (RTC.refl x) hxy) hx

theorem forwardClosure_monotone
    {W : Type u} (R : Rel W) {P Q : W -> Prop}
    (hPQ : PredSubset P Q) :
    PredSubset (ForwardClosure R P) (ForwardClosure R Q) := by
  intro y hy
  rcases hy with ⟨x, hxP, hxy⟩
  exact ⟨x, hPQ x hxP, hxy⟩

theorem invariantKernel_monotone
    {W : Type u} (R : Rel W) {P Q : W -> Prop}
    (hPQ : PredSubset P Q) :
    PredSubset (InvariantKernel R P) (InvariantKernel R Q) := by
  intro x hx
  constructor
  · exact hPQ x hx.1
  · intro y hxy
    exact hPQ y (hx.2 y hxy)

theorem forwardClosure_galois
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q) :
    PredSubset (ForwardClosure R P) Q <->
      PredSubset P Q := by
  constructor
  · intro h x hx
    exact h x (forwardClosure_contains R P x hx)
  · intro h
    exact forwardClosure_least R P Q hQInv h

theorem invariantKernel_galois
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q) :
    PredSubset Q (InvariantKernel R P) <->
      PredSubset Q P := by
  constructor
  · intro h x hx
    exact invariantKernel_subset R P x (h x hx)
  · intro h
    exact invariantKernel_greatest R P Q hQInv h

theorem forwardInvariant_iff_forwardClosure_fixed
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      PredEq (ForwardClosure R P) P := by
  constructor
  · intro hInv x
    constructor
    · exact forwardClosure_least R P P hInv (by intro z hz; exact hz) x
    · exact forwardClosure_contains R P x
  · intro hEq
    exact (forwardInvariant_iff_closure_subset R P).mpr
      (by
        intro x hx
        exact (hEq x).mp hx)

theorem forwardInvariant_iff_invariantKernel_fixed
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      PredEq (InvariantKernel R P) P := by
  constructor
  · intro hInv x
    constructor
    · exact invariantKernel_subset R P x
    · intro hx
      exact invariantKernel_greatest R P P hInv
        (by intro z hz; exact hz) x hx
  · intro hEq
    exact (forwardInvariant_iff_subset_kernel R P).mpr
      (by
        intro x hx
        exact (hEq x).mpr hx)

theorem universalSubsumption_iff_forwardClosure_fixed
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      PredEq (ForwardClosure G.rel A) A := by
  calc
    UniversalStateSubsumption G A
        <-> ForwardInvariantRegion G.rel A :=
      universal_state_subsumption_iff_forwardInvariant G A
    _ <-> PredEq (ForwardClosure G.rel A) A :=
      forwardInvariant_iff_forwardClosure_fixed G.rel A

theorem universalSubsumption_iff_invariantKernel_fixed
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      PredEq (InvariantKernel G.rel A) A := by
  calc
    UniversalStateSubsumption G A
        <-> ForwardInvariantRegion G.rel A :=
      universal_state_subsumption_iff_forwardInvariant G A
    _ <-> PredEq (InvariantKernel G.rel A) A :=
      forwardInvariant_iff_invariantKernel_fixed G.rel A

theorem forwardInvariant_iUnion
    {W : Type u} {I : Type v}
    (R : Rel W) (F : I -> W -> Prop)
    (hInv : forall i, ForwardInvariantRegion R (F i)) :
    ForwardInvariantRegion R (fun x => exists i, F i x) := by
  intro x y hxy hx
  rcases hx with ⟨i, hix⟩
  exact ⟨i, hInv i hxy hix⟩

theorem forwardInvariant_iInter
    {W : Type u} {I : Type v}
    (R : Rel W) (F : I -> W -> Prop)
    (hInv : forall i, ForwardInvariantRegion R (F i)) :
    ForwardInvariantRegion R (fun x => forall i, F i x) := by
  intro x y hxy hx i
  exact hInv i hxy (hx i)

theorem invariant_regions_form_complete_family
    {W : Type u} {I : Type v}
    (R : Rel W) (F : I -> W -> Prop)
    (hInv : forall i, ForwardInvariantRegion R (F i)) :
    ForwardInvariantRegion R (fun x => exists i, F i x) /\
    ForwardInvariantRegion R (fun x => forall i, F i x) := by
  exact ⟨
    forwardInvariant_iUnion R F hInv,
    forwardInvariant_iInter R F hInv
  ⟩

/--
Extremal repair theorem.

For any stable predicate Q:
* the least stable expansion of A lies below Q exactly when A lies below Q;
* Q lies below the greatest stable contraction of A exactly when Q lies below A.

This packages the minimality/maximality claims as two adjunction laws.
-/
theorem canonical_repair_extremality
    {S : Type u} (G : StateGrowth S)
    (A Q : S -> Prop)
    (hQInv : ForwardInvariantRegion G.rel Q) :
    (PredSubset (ForwardClosure G.rel A) Q <-> PredSubset A Q) /\
    (PredSubset Q (InvariantKernel G.rel A) <-> PredSubset Q A) := by
  exact ⟨
    forwardClosure_galois G.rel A Q hQInv,
    invariantKernel_galois G.rel A Q hQInv
  ⟩

/--
Fixed-point synthesis.

A predicate is stable exactly when it is simultaneously unchanged by both
canonical repairs. Equivalently, Universal Subsumption is exactly membership
in the common fixed-point family.
-/
theorem universalSubsumption_iff_both_canonical_fixed
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      (PredEq (ForwardClosure G.rel A) A /\
       PredEq (InvariantKernel G.rel A) A) := by
  constructor
  · intro hSub
    exact ⟨
      (universalSubsumption_iff_forwardClosure_fixed G A).mp hSub,
      (universalSubsumption_iff_invariantKernel_fixed G A).mp hSub
    ⟩
  · intro h
    exact (universalSubsumption_iff_forwardClosure_fixed G A).mpr h.1

end CPOG
