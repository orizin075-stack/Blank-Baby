import CPOG.General
import CPOG.Closure

/-!
Generic forward-invariance layer for the paper-level CPOG package.

This module imports the v55/v56 conceptual core into the modular package:
* universal Subsumption iff forward invariance of acceptance;
* two disjoint persistent regions reachable from one root refute .2;
* FirstCommit is an exact instance;
* every acceptance predicate has a least invariant expansion and greatest
  invariant contraction, both restoring universal Subsumption.

The admissible-update relation itself need not be reflexive or transitive.
-/

namespace CPOG.InvariantRepair

open CPOG.EpistemicPotentialism
open CPOG.Closure

universe uS uW uC

def ForwardInvariantRegion
    {W : Type uW} (R : W -> W -> Prop) (P : W -> Prop) : Prop :=
  forall {x y : W}, R x y -> P x -> P y

def MutuallyExclusiveRegions
    {W : Type uW} (P Q : W -> Prop) : Prop :=
  forall x : W, P x -> Q x -> False

theorem persistent_incompatible_branches_counterexample
    {W : Type uW}
    (R : W -> W -> Prop) (P Q : W -> Prop)
    {root a b : W}
    (hP : ForwardInvariantRegion R P)
    (hQ : ForwardInvariantRegion R Q)
    (hDisjoint : MutuallyExclusiveRegions P Q)
    (hra : R root a) (hrb : R root b)
    (ha : P a) (hb : Q b) :
    DiaR R (BoxR R P) root /\
    Not (BoxR R (DiaR R P) root) := by
  constructor
  · refine ⟨a, hra, ?_⟩
    intro y hay
    exact hP hay ha
  · intro hBox
    rcases hBox b hrb with ⟨z, hbz, hPz⟩
    have hQz : Q z := hQ hbz hb
    exact hDisjoint z hPz hQz

theorem persistent_incompatible_branches_dotTwo_fails
    {W : Type uW}
    (R : W -> W -> Prop) (P Q : W -> Prop)
    {root a b : W}
    (hP : ForwardInvariantRegion R P)
    (hQ : ForwardInvariantRegion R Q)
    (hDisjoint : MutuallyExclusiveRegions P Q)
    (hra : R root a) (hrb : R root b)
    (ha : P a) (hb : Q b) :
    Not (DotTwoR R P root) := by
  intro hDot
  rcases persistent_incompatible_branches_counterexample
      R P Q hP hQ hDisjoint hra hrb ha hb with ⟨hAnte, hNotCons⟩
  exact hNotCons (hDot hAnte)

theorem persistent_incompatible_branches_not_directed
    {W : Type uW}
    (R : W -> W -> Prop) (P Q : W -> Prop)
    {root a b : W}
    (hP : ForwardInvariantRegion R P)
    (hQ : ForwardInvariantRegion R Q)
    (hDisjoint : MutuallyExclusiveRegions P Q)
    (hra : R root a) (hrb : R root b)
    (ha : P a) (hb : Q b) :
    Not (DirectedAt R root) := by
  intro hDir
  rcases hDir a b hra hrb with ⟨z, haz, hbz⟩
  exact hDisjoint z (hP haz ha) (hQ hbz hb)

/-! FirstCommit as an exact instance. -/

theorem firstCommit_forwardInvariant
    {H : Type uW} {C : Type uC}
    (G : H -> H -> Prop) (first : H -> Option C) (c : C)
    (hPersist : forall {x y : H} {k : C},
      G x y -> first x = some k -> first y = some k) :
    ForwardInvariantRegion G (FirstCommitIs first c) := by
  intro x y hxy hx
  exact hPersist hxy hx

theorem firstCommit_regions_exclusive
    {H : Type uW} {C : Type uC}
    (first : H -> Option C) {ca cb : C}
    (hc : ca ≠ cb) :
    MutuallyExclusiveRegions
      (FirstCommitIs first ca)
      (FirstCommitIs first cb) := by
  intro x hca hcb
  have hs : (some ca : Option C) = some cb := hca.symm.trans hcb
  exact hc (Option.some.inj hs)

theorem firstCommit_dotTwo_is_invariance_instance
    {H : Type uW} {C : Type uC}
    (G : H -> H -> Prop) (first : H -> Option C)
    {root a b : H} {ca cb : C}
    (hc : ca ≠ cb)
    (hra : G root a) (hrb : G root b)
    (ha : first a = some ca) (hb : first b = some cb)
    (hPersist : forall {x y : H} {k : C},
      G x y -> first x = some k -> first y = some k) :
    Not (DotTwoR G (FirstCommitIs first ca) root) := by
  exact persistent_incompatible_branches_dotTwo_fails
    G
    (FirstCommitIs first ca)
    (FirstCommitIs first cb)
    (firstCommit_forwardInvariant G first ca hPersist)
    (firstCommit_forwardInvariant G first cb hPersist)
    (firstCommit_regions_exclusive first hc)
    hra hrb ha hb

/-! Generic state-growth Subsumption representation theorem. -/

structure StateGrowth (S : Type uS) where
  rel : S -> S -> Prop

structure GrowthDynamics
    {S : Type uS} (G : StateGrowth S) (W : Type uW) where
  gR : W -> W -> Prop
  dR : W -> W -> Prop
  summary : W -> S
  g_summary_mono :
    forall {x y : W}, gR x y -> G.rel (summary x) (summary y)
  d_reflexive : forall x, dR x x

def GrowthDynamics.Accepts
    {S : Type uS} {G : StateGrowth S} {W : Type uW}
    (A : S -> Prop) (M : GrowthDynamics G W) (w : W) : Prop :=
  A (M.summary w)

def UniversalStateSubsumption
    {S : Type uS} (G : StateGrowth S) (A : S -> Prop) : Prop :=
  forall {W : Type} (M : GrowthDynamics G W) (w : W),
    BoxR M.dR (M.Accepts A) w ->
    BoxR M.gR (M.Accepts A) w

theorem upperClosed_implies_universalSubsumption
    {S : Type uS} (G : StateGrowth S) (A : S -> Prop)
    (hInv : ForwardInvariantRegion G.rel A) :
    UniversalStateSubsumption G A := by
  intro W M w hD y hwy
  have hAw : A (M.summary w) :=
    hD w (M.d_reflexive w)
  exact hInv (M.g_summary_mono hwy) hAw

inductive PairWorld where
  | lower
  | upper
deriving DecidableEq

def pairG : PairWorld -> PairWorld -> Prop
  | .lower, .upper => True
  | _, _ => False

def pairD : PairWorld -> PairWorld -> Prop :=
  fun x y => x = y

def pairDynamics
    {S : Type uS}
    (G : StateGrowth S)
    (s t : S) (hst : G.rel s t) :
    GrowthDynamics G PairWorld where
  gR := pairG
  dR := pairD
  summary
    | .lower => s
    | .upper => t
  g_summary_mono := by
    intro x y hxy
    cases x <;> cases y <;> simp [pairG] at hxy
    exact hst
  d_reflexive := by
    intro x
    rfl

theorem universalSubsumption_implies_upperClosed
    {S : Type uS} (G : StateGrowth S) (A : S -> Prop)
    (hSub : UniversalStateSubsumption G A) :
    ForwardInvariantRegion G.rel A := by
  intro s t hst hs
  let M := pairDynamics G s t hst
  have hD : BoxR M.dR (M.Accepts A) .lower := by
    intro y hly
    have hy : PairWorld.lower = y := by
      simpa [M, pairDynamics, pairD] using hly
    subst y
    exact hs
  have hG : BoxR M.gR (M.Accepts A) .lower :=
    hSub M .lower hD
  exact hG .upper (by trivial)

theorem universalSubsumption_iff_forwardInvariant
    {S : Type uS} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      ForwardInvariantRegion G.rel A := by
  constructor
  · exact universalSubsumption_implies_upperClosed G A
  · exact upperClosed_implies_universalSubsumption G A

theorem universalSubsumption_failure_iff_nonInvariant
    {S : Type uS} (G : StateGrowth S) (A : S -> Prop) :
    Not (UniversalStateSubsumption G A) <->
      Not (ForwardInvariantRegion G.rel A) := by
  exact not_congr (universalSubsumption_iff_forwardInvariant G A)

/-! Canonical stabilization operators. -/

def PredSubset
    {W : Type uW} (P Q : W -> Prop) : Prop :=
  forall x, P x -> Q x

def ForwardClosure
    {W : Type uW} (R : W -> W -> Prop) (P : W -> Prop) : W -> Prop :=
  fun y => exists x, P x /\ RTC R x y

def InvariantKernel
    {W : Type uW} (R : W -> W -> Prop) (P : W -> Prop) : W -> Prop :=
  fun x => P x /\ forall y, RTC R x y -> P y

theorem rtc_preserve
    {W : Type uW} {R : W -> W -> Prop} {P : W -> Prop}
    (hInv : ForwardInvariantRegion R P)
    {x y : W} (hxy : RTC R x y) :
    P x -> P y := by
  intro hx
  induction hxy with
  | refl =>
      exact hx
  | tail hprev hstep ih =>
      exact hInv hstep ih

theorem forwardClosure_contains
    {W : Type uW} (R : W -> W -> Prop) (P : W -> Prop) :
    PredSubset P (ForwardClosure R P) := by
  intro x hx
  exact ⟨x, hx, RTC.refl x⟩

theorem forwardClosure_forwardInvariant
    {W : Type uW} (R : W -> W -> Prop) (P : W -> Prop) :
    ForwardInvariantRegion R (ForwardClosure R P) := by
  intro x y hxy hx
  rcases hx with ⟨z, hzP, hzx⟩
  exact ⟨z, hzP, RTC.tail hzx hxy⟩

theorem forwardClosure_least
    {W : Type uW} (R : W -> W -> Prop) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q)
    (hPQ : PredSubset P Q) :
    PredSubset (ForwardClosure R P) Q := by
  intro y hy
  rcases hy with ⟨x, hxP, hxy⟩
  exact rtc_preserve (R := R) (P := Q) hQInv hxy (hPQ x hxP)

theorem invariantKernel_subset
    {W : Type uW} (R : W -> W -> Prop) (P : W -> Prop) :
    PredSubset (InvariantKernel R P) P := by
  intro x hx
  exact hx.1

theorem invariantKernel_forwardInvariant
    {W : Type uW} (R : W -> W -> Prop) (P : W -> Prop) :
    ForwardInvariantRegion R (InvariantKernel R P) := by
  intro x y hxy hx
  have hxyRTC : RTC R x y := RTC.tail (RTC.refl x) hxy
  constructor
  · exact hx.2 y hxyRTC
  · intro z hyz
    exact hx.2 z (rtc_trans hxyRTC hyz)

theorem invariantKernel_greatest
    {W : Type uW} (R : W -> W -> Prop) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q)
    (hQP : PredSubset Q P) :
    PredSubset Q (InvariantKernel R P) := by
  intro x hxQ
  constructor
  · exact hQP x hxQ
  · intro y hxy
    exact hQP y (rtc_preserve (R := R) (P := Q) hQInv hxy hxQ)

theorem forwardClosure_idempotent
    {W : Type uW} (R : W -> W -> Prop) (P : W -> Prop) (x : W) :
    ForwardClosure R (ForwardClosure R P) x <->
      ForwardClosure R P x := by
  constructor
  · intro hx
    rcases hx with ⟨y, ⟨z, hzP, hzy⟩, hyx⟩
    exact ⟨z, hzP, rtc_trans hzy hyx⟩
  · intro hx
    exact ⟨x, hx, RTC.refl x⟩

theorem invariantKernel_idempotent
    {W : Type uW} (R : W -> W -> Prop) (P : W -> Prop) (x : W) :
    InvariantKernel R (InvariantKernel R P) x <->
      InvariantKernel R P x := by
  constructor
  · intro hx
    exact hx.1
  · intro hx
    constructor
    · exact hx
    · intro y hxy
      constructor
      · exact hx.2 y hxy
      · intro z hyz
        exact hx.2 z (rtc_trans hxy hyz)

theorem canonical_stabilizations_restore_subsumption
    {S : Type uS} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G (ForwardClosure G.rel A) /\
    UniversalStateSubsumption G (InvariantKernel G.rel A) := by
  constructor
  · exact
      (universalSubsumption_iff_forwardInvariant
        G (ForwardClosure G.rel A)).2
      (forwardClosure_forwardInvariant G.rel A)
  · exact
      (universalSubsumption_iff_forwardInvariant
        G (InvariantKernel G.rel A)).2
      (invariantKernel_forwardInvariant G.rel A)

end CPOG.InvariantRepair
