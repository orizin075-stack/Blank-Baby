namespace CPOG

/-!
# v56 canonical stabilization operators

The representation theorem diagnoses failure of universal Subsumption as
non-invariance of the acceptance region.  This section adds two canonical
repairs for any predicate P under any relation R:

* ForwardClosure R P: the least forward-invariant superset of P;
* InvariantKernel R P: the greatest forward-invariant subset of P.

Both repairs therefore satisfy the generic Subsumption theorem automatically.
-/

universe u

def PredSubset {W : Type u} (P Q : W -> Prop) : Prop :=
  forall x, P x -> Q x

def ForwardClosure
    {W : Type u} (R : Rel W) (P : W -> Prop) : W -> Prop :=
  fun y => exists x, P x /\ RTC R x y

def InvariantKernel
    {W : Type u} (R : Rel W) (P : W -> Prop) : W -> Prop :=
  fun x => P x /\ forall y, RTC R x y -> P y

theorem forwardClosure_contains
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    PredSubset P (ForwardClosure R P) := by
  intro x hx
  exact ⟨x, hx, RTC.refl x⟩

theorem forwardClosure_forwardInvariant
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R (ForwardClosure R P) := by
  intro x y hxy hx
  rcases hx with ⟨z, hzP, hzx⟩
  exact ⟨z, hzP, RTC.tail hzx hxy⟩

theorem forwardClosure_least
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q)
    (hPQ : PredSubset P Q) :
    PredSubset (ForwardClosure R P) Q := by
  intro y hy
  rcases hy with ⟨x, hxP, hxy⟩
  have hxQ : Q x := hPQ x hxP
  exact RTC.preserve (R := R) (P := Q) hQInv hxy hxQ

theorem invariantKernel_subset
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    PredSubset (InvariantKernel R P) P := by
  intro x hx
  exact hx.1

theorem invariantKernel_forwardInvariant
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R (InvariantKernel R P) := by
  intro x y hxy hx
  have hxyRTC : RTC R x y := RTC.tail (RTC.refl x) hxy
  have hyP : P y := hx.2 y hxyRTC
  constructor
  · exact hyP
  · intro z hyz
    have hxz : RTC R x z := RTC.trans hxyRTC hyz
    exact hx.2 z hxz

theorem invariantKernel_greatest
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q)
    (hQP : PredSubset Q P) :
    PredSubset Q (InvariantKernel R P) := by
  intro x hxQ
  constructor
  · exact hQP x hxQ
  · intro y hxy
    have hyQ : Q y := RTC.preserve (R := R) (P := Q) hQInv hxy hxQ
    exact hQP y hyQ

theorem forwardInvariant_iff_closure_subset
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      PredSubset (ForwardClosure R P) P := by
  constructor
  · intro hInv
    exact forwardClosure_least R P P hInv (by intro x hx; exact hx)
  · intro hClose x y hxy hx
    exact hClose y ⟨x, hx, RTC.tail (RTC.refl x) hxy⟩

theorem forwardInvariant_iff_subset_kernel
    {W : Type u} (R : Rel W) (P : W -> Prop) :
    ForwardInvariantRegion R P <->
      PredSubset P (InvariantKernel R P) := by
  constructor
  · intro hInv
    exact invariantKernel_greatest R P P hInv (by intro x hx; exact hx)
  · intro hKernel x y hxy hx
    have hxK : InvariantKernel R P x := hKernel x hx
    exact hxK.2 y (RTC.tail (RTC.refl x) hxy)

theorem forwardClosure_idempotent_pointwise
    {W : Type u} (R : Rel W) (P : W -> Prop) (x : W) :
    ForwardClosure R (ForwardClosure R P) x <->
      ForwardClosure R P x := by
  constructor
  · intro hx
    rcases hx with ⟨y, ⟨z, hzP, hzy⟩, hyx⟩
    exact ⟨z, hzP, RTC.trans hzy hyx⟩
  · intro hx
    exact ⟨x, hx, RTC.refl x⟩

theorem invariantKernel_idempotent_pointwise
    {W : Type u} (R : Rel W) (P : W -> Prop) (x : W) :
    InvariantKernel R (InvariantKernel R P) x <->
      InvariantKernel R P x := by
  constructor
  · intro hx
    exact hx.1
  · intro hx
    constructor
    · exact hx
    · intro y hxy
      have hyP : P y := hx.2 y hxy
      constructor
      · exact hyP
      · intro z hyz
        exact hx.2 z (RTC.trans hxy hyz)

/--
Canonical stabilization theorem for the generic v55/v56 state-growth setting.
Both the least invariant expansion and greatest invariant contraction of any
acceptance predicate satisfy universal Subsumption.
-/
theorem canonical_stabilizations_restore_subsumption
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G (ForwardClosure G.rel A) /\
    UniversalStateSubsumption G (InvariantKernel G.rel A) := by
  constructor
  · exact
      (universal_state_subsumption_iff_forwardInvariant
        G (ForwardClosure G.rel A)).mpr
      (forwardClosure_forwardInvariant G.rel A)
  · exact
      (universal_state_subsumption_iff_forwardInvariant
        G (InvariantKernel G.rel A)).mpr
      (invariantKernel_forwardInvariant G.rel A)

end CPOG
