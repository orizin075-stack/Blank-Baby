namespace CPOG

/-!
# v57 exact branching characterization on preorder frames

v56 proved that two reachable disjoint forward-invariant regions suffice for
non-directedness and .2 failure.  On reflexive-transitive frames the converse
also holds: every failure of directedness canonically generates such a pair,
namely the successor cones of two non-joinable successors.

Together with the already verified frame correspondence
DirectedAt R r <-> validity of .2 at r for all predicates,
this gives an exact three-way characterization:
  branch split <-> non-directedness <-> failure of universal .2.
-/

universe u

def PersistentBranchSplitAt
    {W : Type u} (R : Rel W) (r : W) : Prop :=
  exists (P Q : W -> Prop) (a b : W),
    ForwardInvariantRegion R P /\
    ForwardInvariantRegion R Q /\
    MutuallyExclusiveRegions P Q /\
    R r a /\ R r b /\ P a /\ Q b

def SuccessorCone
    {W : Type u} (R : Rel W) (a : W) : W -> Prop :=
  fun z => R a z

theorem successorCone_forwardInvariant
    {W : Type u} (R : Rel W)
    (hTrans : Transitive R) (a : W) :
    ForwardInvariantRegion R (SuccessorCone R a) := by
  intro x y hxy hax
  exact hTrans hax hxy

theorem successorCone_contains_root
    {W : Type u} (R : Rel W)
    (hRefl : Reflexive R) (a : W) :
    SuccessorCone R a a := by
  exact hRefl a

theorem no_common_successor_gives_exclusive_cones
    {W : Type u} (R : Rel W) {a b : W}
    (hNoJoin : Not (exists z, R a z /\ R b z)) :
    MutuallyExclusiveRegions
      (SuccessorCone R a)
      (SuccessorCone R b) := by
  intro z haz hbz
  exact hNoJoin ⟨z, haz, hbz⟩

theorem not_directedAt_has_nonjoinable_successors
    {W : Type u} (R : Rel W) {r : W}
    (hNot : Not (DirectedAt R r)) :
    exists a b,
      R r a /\ R r b /\
      Not (exists z, R a z /\ R b z) := by
  classical
  by_contra hNoWitness
  apply hNot
  intro a b hra hrb
  by_contra hNoJoin
  apply hNoWitness
  exact ⟨a, b, hra, hrb, hNoJoin⟩

theorem not_directedAt_implies_persistentBranchSplit
    {W : Type u} (R : Rel W) {r : W}
    (hRefl : Reflexive R)
    (hTrans : Transitive R)
    (hNot : Not (DirectedAt R r)) :
    PersistentBranchSplitAt R r := by
  rcases not_directedAt_has_nonjoinable_successors R hNot with
    ⟨a, b, hra, hrb, hNoJoin⟩
  refine ⟨SuccessorCone R a, SuccessorCone R b, a, b, ?_⟩
  constructor
  · exact successorCone_forwardInvariant R hTrans a
  constructor
  · exact successorCone_forwardInvariant R hTrans b
  constructor
  · exact no_common_successor_gives_exclusive_cones R hNoJoin
  exact ⟨hra, hrb,
    successorCone_contains_root R hRefl a,
    successorCone_contains_root R hRefl b⟩

theorem persistentBranchSplit_implies_not_directedAt
    {W : Type u} (R : Rel W) {r : W}
    (hSplit : PersistentBranchSplitAt R r) :
    Not (DirectedAt R r) := by
  rcases hSplit with
    ⟨P, Q, a, b, hP, hQ, hDisjoint, hra, hrb, ha, hb⟩
  exact persistent_incompatible_branches_not_directed
    R P Q hP hQ hDisjoint hra hrb ha hb

/--
EXACT IRREVERSIBLE-BRANCHING CHARACTERIZATION.

On every reflexive-transitive frame, a root is non-directed iff two mutually
exclusive forward-invariant regions are both reachable from it.
-/
theorem persistentBranchSplit_iff_notDirectedAt
    {W : Type u} (R : Rel W) {r : W}
    (hRefl : Reflexive R)
    (hTrans : Transitive R) :
    PersistentBranchSplitAt R r <->
      Not (DirectedAt R r) := by
  constructor
  · exact persistentBranchSplit_implies_not_directedAt R
  · exact not_directedAt_implies_persistentBranchSplit R hRefl hTrans

def Dot2ValidAt
    {W : Type u} (R : Rel W) (r : W) : Prop :=
  forall P : W -> Prop,
    Dia R (Box R P) r ->
    Box R (Dia R P) r

theorem dot2ValidAt_iff_directedAt
    {W : Type u} (R : Rel W) (r : W) :
    Dot2ValidAt R r <-> DirectedAt R r := by
  exact (directedAt_iff_dot2_all (R := R) (w := r)).symm

theorem not_dot2ValidAt_iff_notDirectedAt
    {W : Type u} (R : Rel W) (r : W) :
    Not (Dot2ValidAt R r) <-> Not (DirectedAt R r) := by
  exact not_congr (dot2ValidAt_iff_directedAt R r)

/--
THREE-WAY CHARACTERIZATION.

On reflexive-transitive frames, persistent exclusive branching exists exactly
when universal .2 fails at the root.
-/
theorem persistentBranchSplit_iff_dot2Failure
    {W : Type u} (R : Rel W) {r : W}
    (hRefl : Reflexive R)
    (hTrans : Transitive R) :
    PersistentBranchSplitAt R r <->
      Not (Dot2ValidAt R r) := by
  calc
    PersistentBranchSplitAt R r
        <-> Not (DirectedAt R r) :=
      persistentBranchSplit_iff_notDirectedAt R hRefl hTrans
    _ <-> Not (Dot2ValidAt R r) :=
      (not_dot2ValidAt_iff_notDirectedAt R r).symm

theorem branchSplit_supplies_explicit_dot2_countervaluation
    {W : Type u} (R : Rel W) {r : W}
    (hSplit : PersistentBranchSplitAt R r) :
    exists P : W -> Prop,
      Dia R (Box R P) r /\
      Not (Box R (Dia R P) r) := by
  rcases hSplit with
    ⟨P, Q, a, b, hP, hQ, hDisjoint, hra, hrb, ha, hb⟩
  exact ⟨P,
    persistent_incompatible_branches_dot2_failure
      R P Q hP hQ hDisjoint hra hrb ha hb⟩

end CPOG
