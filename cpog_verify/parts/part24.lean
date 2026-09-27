namespace CPOG

/-!
# v57 stability adjunction

v56 introduced ForwardClosure and InvariantKernel as canonical repairs.
This section identifies their exact order-theoretic relationship.

For every relation R on every carrier W:

  ForwardClosure_R(P) ⊆ Q  iff  P ⊆ InvariantKernel_R(Q).

Thus ForwardClosure is left adjoint to InvariantKernel on the predicate
poset.  The forward-invariant predicates are exactly the common fixed points
of both operators.  They are closed under arbitrary unions and arbitrary
intersections; equivalently, the stable acceptance regions form a complete
sublattice of the full predicate lattice.

No reflexivity or transitivity of R is assumed.
-/

universe u v

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

theorem forwardInvariant_iff_forwardClosure_fixedPoint
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      forall x, ForwardClosure R P x <-> P x := by
  constructor
  · intro hInv x
    constructor
    · intro hx
      exact
        (forwardClosure_least R P P hInv
          (by intro z hz; exact hz)) x hx
    · intro hx
      exact forwardClosure_contains R P x hx
  · intro hFix x y hxy hx
    have hCl : ForwardClosure R P y :=
      ⟨x, hx, RTC.tail (RTC.refl x) hxy⟩
    exact (hFix y).mp hCl

theorem forwardInvariant_iff_invariantKernel_fixedPoint
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      forall x, InvariantKernel R P x <-> P x := by
  constructor
  · intro hInv x
    constructor
    · intro hx
      exact hx.1
    · intro hx
      exact
        (invariantKernel_greatest R P P hInv
          (by intro z hz; exact hz)) x hx
  · intro hFix x y hxy hx
    have hxK : InvariantKernel R P x := (hFix x).mpr hx
    exact hxK.2 y (RTC.tail (RTC.refl x) hxy)

theorem forwardInvariant_iUnion
    {W : Type u} {I : Type v}
    (R : Rel W) (F : I -> W -> Prop)
    (hF : forall i, ForwardInvariantRegion R (F i)) :
    ForwardInvariantRegion R (fun x => exists i, F i x) := by
  intro x y hxy hx
  rcases hx with ⟨i, hix⟩
  exact ⟨i, hF i hxy hix⟩

theorem forwardInvariant_iInter
    {W : Type u} {I : Type v}
    (R : Rel W) (F : I -> W -> Prop)
    (hF : forall i, ForwardInvariantRegion R (F i)) :
    ForwardInvariantRegion R (fun x => forall i, F i x) := by
  intro x y hxy hx i
  exact hF i hxy (hx i)

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

theorem universalSubsumption_iUnion
    {S : Type u} {I : Type v}
    (G : StateGrowth S) (A : I -> S -> Prop)
    (hA : forall i, UniversalStateSubsumption G (A i)) :
    UniversalStateSubsumption G (fun s => exists i, A i s) := by
  apply (universal_state_subsumption_iff_forwardInvariant G
    (fun s => exists i, A i s)).mpr
  apply forwardInvariant_iUnion G.rel A
  intro i
  exact
    (universal_state_subsumption_iff_forwardInvariant G (A i)).mp
      (hA i)

theorem universalSubsumption_iInter
    {S : Type u} {I : Type v}
    (G : StateGrowth S) (A : I -> S -> Prop)
    (hA : forall i, UniversalStateSubsumption G (A i)) :
    UniversalStateSubsumption G (fun s => forall i, A i s) := by
  apply (universal_state_subsumption_iff_forwardInvariant G
    (fun s => forall i, A i s)).mpr
  apply forwardInvariant_iInter G.rel A
  intro i
  exact
    (universal_state_subsumption_iff_forwardInvariant G (A i)).mp
      (hA i)

/--
The canonical lower and upper repairs are optimal stable approximations:
InvariantKernel is the greatest forward-invariant predicate below P, and
ForwardClosure is the least forward-invariant predicate above P.
-/
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

/--
Fixed-point characterization of stable predicates:
P is forward invariant iff both canonical repairs return P pointwise.
-/
theorem forwardInvariant_iff_both_stabilizers_fixed
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      ((forall x, ForwardClosure R P x <-> P x) /\
       (forall x, InvariantKernel R P x <-> P x)) := by
  constructor
  · intro h
    exact
      ⟨(forwardInvariant_iff_forwardClosure_fixedPoint R P).mp h,
       (forwardInvariant_iff_invariantKernel_fixedPoint R P).mp h⟩
  · intro h
    exact (forwardInvariant_iff_forwardClosure_fixedPoint R P).mpr h.1

end CPOG
