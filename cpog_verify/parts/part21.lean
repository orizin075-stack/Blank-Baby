namespace CPOG

/-!
# v56 persistence / irreversibility theorem

The old SC3 spoke in the language of FirstCommit values.
The old SC5 spoke in the language of upward-closed acceptance regions.
They are instances of one transition-system notion: forward invariance.

A region P is forward invariant under R when every R-successor of a P-state
is again in P.  If two disjoint forward-invariant regions are both reachable
from one root, then the .2 pattern Diamond Box P -> Box Diamond P fails at
that root.  Conversely, the v55 Subsumption master theorem says that universal
Subsumption is exactly forward invariance of the acceptance region.

Thus irreversible branching and defeasible Subsumption are expressed in one
common mathematical vocabulary.
-/

universe u v

def ForwardInvariantRegion
    {W : Type u} (R : Rel W) (P : W -> Prop) : Prop :=
  forall {x y : W}, R x y -> P x -> P y

def MutuallyExclusiveRegions
    {W : Type u} (P Q : W -> Prop) : Prop :=
  forall x : W, P x -> Q x -> False

theorem forwardInvariant_region_boxes_from_member
    {W : Type u} {R : Rel W} {P : W -> Prop} {x : W}
    (hInv : ForwardInvariantRegion R P)
    (hx : P x) :
    Box R P x := by
  intro y hxy
  exact hInv hxy hx

theorem incompatible_forward_region_excludes_diamond
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQ : ForwardInvariantRegion R Q)
    (hDisjoint : MutuallyExclusiveRegions P Q)
    {x : W} (hx : Q x) :
    Not (Dia R P x) := by
  intro hDia
  rcases hDia with ⟨y, hxy, hPy⟩
  have hQy : Q y := hQ hxy hx
  exact hDisjoint y hPy hQy

/--
GENERIC IRREVERSIBLE-DIVERGENCE THEOREM.

No reflexivity, transitivity, functionality, Option-valued commit map, or
special FirstCommit syntax is required.  Two mutually exclusive
forward-invariant regions reachable from one root suffice to refute .2 for P.
-/
theorem persistent_incompatible_branches_dot2_failure
    {W : Type u}
    (R : Rel W) (P Q : W -> Prop)
    {r a b : W}
    (hP : ForwardInvariantRegion R P)
    (hQ : ForwardInvariantRegion R Q)
    (hDisjoint : MutuallyExclusiveRegions P Q)
    (hra : R r a) (hrb : R r b)
    (ha : P a) (hb : Q b) :
    Dia R (Box R P) r /\
    Not (Box R (Dia R P) r) := by
  constructor
  · exact ⟨a, hra, forwardInvariant_region_boxes_from_member hP ha⟩
  · intro hBox
    have hDiaB : Dia R P b := hBox b hrb
    exact incompatible_forward_region_excludes_diamond
      R P Q hQ hDisjoint hb hDiaB

/-! ## FirstCommit is an exact instance -/

theorem firstCommitPA_forwardInvariant
    {W : Type u} {Choice : Type v}
    (R : Rel W) (F : W -> Option Choice)
    (A : Choice)
    (hPersist : FirstCommitPersistent R F) :
    ForwardInvariantRegion R (FirstCommitPA F A) := by
  intro x y hxy hx
  exact hPersist hxy hx

theorem firstCommit_regions_exclusive
    {W : Type u} {Choice : Type v}
    (F : W -> Option Choice)
    {A B : Choice}
    (hAB : A ≠ B) :
    MutuallyExclusiveRegions
      (FirstCommitPA F A)
      (FirstCommitPA F B) := by
  intro x hA hB
  have hSome : (some A : Option Choice) = some B :=
    Eq.trans hA.symm hB
  exact hAB (Option.some.inj hSome)

theorem firstCommit_dot2_failure_is_persistent_region_instance
    {W : Type u} {Choice : Type v}
    (R : Rel W) (F : W -> Option Choice)
    {r a b : W} {A B : Choice}
    (hPersist : FirstCommitPersistent R F)
    (hAB : A ≠ B)
    (hra : R r a) (hrb : R r b)
    (ha : F a = some A) (hb : F b = some B) :
    Dia R (Box R (FirstCommitPA F A)) r /\
    Not (Box R (Dia R (FirstCommitPA F A)) r) := by
  exact persistent_incompatible_branches_dot2_failure
    R
    (FirstCommitPA F A)
    (FirstCommitPA F B)
    (firstCommitPA_forwardInvariant R F A hPersist)
    (firstCommitPA_forwardInvariant R F B hPersist)
    (firstCommit_regions_exclusive F hAB)
    hra hrb ha hb

/-! ## v55 Subsumption master theorem in the same vocabulary -/

theorem stateUpperClosed_iff_forwardInvariant
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    StateUpperClosed G A <->
      ForwardInvariantRegion G.rel A := by
  rfl

theorem universal_state_subsumption_iff_forwardInvariant
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      ForwardInvariantRegion G.rel A := by
  calc
    UniversalStateSubsumption G A
        <-> StateUpperClosed G A :=
      universal_state_subsumption_iff_upperClosed G A
    _ <-> ForwardInvariantRegion G.rel A :=
      stateUpperClosed_iff_forwardInvariant G A

theorem universal_state_subsumption_failure_iff_nonInvariant
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    Not (UniversalStateSubsumption G A) <->
      Not (ForwardInvariantRegion G.rel A) := by
  exact not_congr (universal_state_subsumption_iff_forwardInvariant G A)

/-!
A useful synthesis:
* one forward-invariant region is exactly what universal Subsumption needs;
* two disjoint forward-invariant regions reachable from one root are enough to
  refute .2 at that root.

The distinction between "stable evaluation" and "irreversible divergence" is
therefore not a difference in the underlying invariant notion, but in how many
disjoint invariant regions the transition system makes jointly reachable.
-/

end CPOG
