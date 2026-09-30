namespace CPOG

/-!
# v58 invariant lattice and stabilization adjunction

The canonical repair operators introduced in v56 are not merely extremal
constructions. They form an adjoint pair on the predicate poset:

  ForwardClosure_R(P) ⊆ Q  iff  P ⊆ InvariantKernel_R(Q).

Forward-invariant predicates are exactly the common fixed points of both
operators. They are closed under arbitrary unions and intersections, hence form
a complete family of stable predicates. Universal Subsumption is exactly
membership in this fixed-point family.

No reflexivity or transitivity of R is assumed.
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

theorem stabilization_adjunction
    {W : Type u} (R : Rel W) (P Q : W -> Prop) :
    PredSubset (ForwardClosure R P) Q <->
      PredSubset P (InvariantKernel R Q) := by
  constructor
  · intro h x hxP
    constructor
    · exact h x ⟨x, hxP, RTC.refl x⟩
    · intro y hxy
      exact h y ⟨x, hxP, hxy⟩
  · intro h y hy
    rcases hy with ⟨x, hxP, hxy⟩
    have hxK : InvariantKernel R Q x := h x hxP
    exact hxK.2 y hxy

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
      (by intro x hx; exact (hEq x).mp hx)

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
      (by intro x hx; exact (hEq x).mpr hx)

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

theorem forwardInvariant_top
    {W : Type u} (R : Rel W) :
    ForwardInvariantRegion R (fun _ => True) := by
  intro x y hxy hx
  trivial

theorem forwardInvariant_bot
    {W : Type u} (R : Rel W) :
    ForwardInvariantRegion R (fun _ => False) := by
  intro x y hxy hx
  exact False.elim hx

theorem invariant_regions_form_complete_family
    {W : Type u} {I : Type v}
    (R : Rel W) (F : I -> W -> Prop)
    (hInv : forall i, ForwardInvariantRegion R (F i)) :
    ForwardInvariantRegion R (fun x => exists i, F i x) /\
    ForwardInvariantRegion R (fun x => forall i, F i x) := by
  exact ⟨forwardInvariant_iUnion R F hInv,
    forwardInvariant_iInter R F hInv⟩

theorem universalSubsumption_iUnion
    {S : Type u} {I : Type v}
    (G : StateGrowth S) (A : I -> S -> Prop)
    (hA : forall i, UniversalStateSubsumption G (A i)) :
    UniversalStateSubsumption G (fun s => exists i, A i s) := by
  apply (universal_state_subsumption_iff_forwardInvariant G
    (fun s => exists i, A i s)).mpr
  apply forwardInvariant_iUnion G.rel A
  intro i
  exact (universal_state_subsumption_iff_forwardInvariant G (A i)).mp (hA i)

theorem universalSubsumption_iInter
    {S : Type u} {I : Type v}
    (G : StateGrowth S) (A : I -> S -> Prop)
    (hA : forall i, UniversalStateSubsumption G (A i)) :
    UniversalStateSubsumption G (fun s => forall i, A i s) := by
  apply (universal_state_subsumption_iff_forwardInvariant G
    (fun s => forall i, A i s)).mpr
  apply forwardInvariant_iInter G.rel A
  intro i
  exact (universal_state_subsumption_iff_forwardInvariant G (A i)).mp (hA i)

theorem canonical_repair_extremality
    {S : Type u} (G : StateGrowth S)
    (A Q : S -> Prop)
    (hQInv : ForwardInvariantRegion G.rel Q) :
    (PredSubset (ForwardClosure G.rel A) Q <-> PredSubset A Q) /\
    (PredSubset Q (InvariantKernel G.rel A) <-> PredSubset Q A) := by
  exact ⟨forwardClosure_galois G.rel A Q hQInv,
    invariantKernel_galois G.rel A Q hQInv⟩

theorem canonical_stable_approximation
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R (InvariantKernel R P) /\
    ForwardInvariantRegion R (ForwardClosure R P) /\
    PredSubset (InvariantKernel R P) P /\
    PredSubset P (ForwardClosure R P) /\
    (forall Q : W -> Prop,
      ForwardInvariantRegion R Q ->
      PredSubset Q P ->
      PredSubset Q (InvariantKernel R P)) /\
    (forall Q : W -> Prop,
      ForwardInvariantRegion R Q ->
      PredSubset P Q ->
      PredSubset (ForwardClosure R P) Q) := by
  constructor
  · exact invariantKernel_forwardInvariant R P
  constructor
  · exact forwardClosure_forwardInvariant R P
  constructor
  · exact invariantKernel_subset R P
  constructor
  · exact forwardClosure_contains R P
  constructor
  · intro Q hQ hQP
    exact invariantKernel_greatest R P Q hQ hQP
  · intro Q hQ hPQ
    exact forwardClosure_least R P Q hQ hPQ

theorem universalSubsumption_iff_both_canonical_fixed
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      (PredEq (ForwardClosure G.rel A) A /\
       PredEq (InvariantKernel G.rel A) A) := by
  constructor
  · intro hSub
    exact ⟨
      (universalSubsumption_iff_forwardClosure_fixed G A).mp hSub,
      (universalSubsumption_iff_invariantKernel_fixed G A).mp hSub⟩
  · intro h
    exact (universalSubsumption_iff_forwardClosure_fixed G A).mpr h.1

end CPOG
