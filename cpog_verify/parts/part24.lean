namespace CPOG

/-!
# v57 invariant completion

v56 introduced two canonical stabilizations:
* ForwardClosure: least forward-invariant expansion;
* InvariantKernel: greatest forward-invariant contraction.

This section completes their order-theoretic characterization.  The invariant
predicates form the fixed points of both operators.  ForwardClosure satisfies
the universal property of a reflection into invariant predicates, while
InvariantKernel satisfies the dual coreflection property.  Their canonical
interval collapses exactly when the original predicate is already invariant.
-/

universe u

def PredEq {W : Type u} (P Q : W -> Prop) : Prop :=
  forall x, P x <-> Q x

theorem predSubset_refl
    {W : Type u} (P : W -> Prop) :
    PredSubset P P := by
  intro x hx
  exact hx

theorem predSubset_trans
    {W : Type u} {P Q T : W -> Prop}
    (hPQ : PredSubset P Q)
    (hQT : PredSubset Q T) :
    PredSubset P T := by
  intro x hx
  exact hQT x (hPQ x hx)

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

theorem forwardInvariant_iff_forwardClosure_fixed
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      PredEq (ForwardClosure R P) P := by
  constructor
  · intro hInv x
    constructor
    · exact
        (forwardClosure_least R P P hInv (predSubset_refl P)) x
    · intro hxP
      exact forwardClosure_contains R P x hxP
  · intro hEq
    apply (forwardInvariant_iff_closure_subset R P).mpr
    intro x hxCl
    exact (hEq x).mp hxCl

theorem forwardInvariant_iff_invariantKernel_fixed
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      PredEq (InvariantKernel R P) P := by
  constructor
  · intro hInv x
    constructor
    · exact invariantKernel_subset R P x
    · intro hxP
      exact
        (invariantKernel_greatest R P P hInv (predSubset_refl P)) x hxP
  · intro hEq
    apply (forwardInvariant_iff_subset_kernel R P).mpr
    intro x hxP
    exact (hEq x).mpr hxP

/--
Reflection universal property:
for invariant Q, extending P into Q is equivalent to extending the least
stable expansion ForwardClosure P into Q.
-/
theorem forwardClosure_reflection_universal
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q) :
    PredSubset (ForwardClosure R P) Q <->
      PredSubset P Q := by
  constructor
  · intro hCl
    exact predSubset_trans (forwardClosure_contains R P) hCl
  · intro hPQ
    exact forwardClosure_least R P Q hQInv hPQ

/--
Coreflection universal property:
for invariant Q, contracting Q into P is equivalent to contracting Q into the
greatest stable contraction InvariantKernel P.
-/
theorem invariantKernel_coreflection_universal
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q) :
    PredSubset Q (InvariantKernel R P) <->
      PredSubset Q P := by
  constructor
  · intro hQK
    exact predSubset_trans hQK (invariantKernel_subset R P)
  · intro hQP
    exact invariantKernel_greatest R P Q hQInv hQP

theorem invariantKernel_subset_forwardClosure
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    PredSubset (InvariantKernel R P) (ForwardClosure R P) := by
  exact predSubset_trans
    (invariantKernel_subset R P)
    (forwardClosure_contains R P)

/--
The canonical lower/upper stable repairs collapse extensionally exactly when
the original acceptance predicate was already stable.
-/
theorem stabilization_interval_collapses_iff_invariant
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    PredEq (ForwardClosure R P) (InvariantKernel R P) <->
      ForwardInvariantRegion R P := by
  constructor
  · intro hEq
    apply (forwardInvariant_iff_closure_subset R P).mpr
    intro x hxCl
    have hxK : InvariantKernel R P x := (hEq x).mp hxCl
    exact (invariantKernel_subset R P) x hxK
  · intro hInv x
    have hClFix :
        PredEq (ForwardClosure R P) P :=
      (forwardInvariant_iff_forwardClosure_fixed R P).mp hInv
    have hKFix :
        PredEq (InvariantKernel R P) P :=
      (forwardInvariant_iff_invariantKernel_fixed R P).mp hInv
    constructor
    · intro hxCl
      exact (hKFix x).mpr ((hClFix x).mp hxCl)
    · intro hxK
      exact (hClFix x).mpr ((hKFix x).mp hxK)

/--
Equivalent stability criterion: every state admitted by the least stable
expansion is also admitted by the greatest stable contraction.
-/
theorem forwardInvariant_iff_closure_subset_kernel
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      PredSubset (ForwardClosure R P) (InvariantKernel R P) := by
  constructor
  · intro hInv
    have hEq :
        PredEq (ForwardClosure R P) (InvariantKernel R P) :=
      (stabilization_interval_collapses_iff_invariant R P).mpr hInv
    intro x hx
    exact (hEq x).mp hx
  · intro h
    apply (forwardInvariant_iff_closure_subset R P).mpr
    exact predSubset_trans h (invariantKernel_subset R P)

/--
Both stabilization operators are fixed-point projections onto the same class
of forward-invariant predicates.
-/
theorem stabilization_fixed_points_coincide
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    PredEq (ForwardClosure R P) P <->
      PredEq (InvariantKernel R P) P := by
  rw [
    ← forwardInvariant_iff_forwardClosure_fixed R P,
    ← forwardInvariant_iff_invariantKernel_fixed R P
  ]

/-! ## Universal Subsumption reformulated as completion collapse -/

theorem universal_subsumption_iff_stabilization_interval_collapses
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      PredEq
        (ForwardClosure G.rel A)
        (InvariantKernel G.rel A) := by
  calc
    UniversalStateSubsumption G A
        <-> ForwardInvariantRegion G.rel A :=
      universal_state_subsumption_iff_forwardInvariant G A
    _ <-> PredEq
        (ForwardClosure G.rel A)
        (InvariantKernel G.rel A) :=
      (stabilization_interval_collapses_iff_invariant G.rel A).symm

/--
If Universal Subsumption fails, the two canonical repairs cannot coincide.
-/
theorem subsumption_failure_implies_noncollapsed_completion
    {S : Type u} (G : StateGrowth S) (A : S -> Prop)
    (hFail : Not (UniversalStateSubsumption G A)) :
    Not (PredEq
      (ForwardClosure G.rel A)
      (InvariantKernel G.rel A)) := by
  intro hEq
  exact hFail
    ((universal_subsumption_iff_stabilization_interval_collapses
      G A).mpr hEq)

end CPOG
