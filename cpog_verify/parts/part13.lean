namespace CPOG

/-!
# v51 class theorems

This section removes the remaining witness-model dependence from the two
central philosophical claims.

1. FirstCommit .2 failure is proved for every relation carrying a persistent,
   exclusive first-commit value with reachable A/B alternatives.
2. Content-level Subsumption is characterized over every evidence-monotone,
   decision-preserving generation system by upward closure of the positive
   decision region under the evidence-information order.
-/

universe u v

/-! ## General FirstCommit theorem -/

def FirstCommitPA
    {W : Type u} {Choice : Type v}
    (F : W -> Option Choice) (A : Choice) : W -> Prop :=
  fun w => F w = some A

def FirstCommitPersistent
    {W : Type u} {Choice : Type v}
    (R : Rel W) (F : W -> Option Choice) : Prop :=
  forall {x y : W} {c : Choice},
    R x y -> F x = some c -> F y = some c

theorem firstCommit_dot2_failure_of_persistent_exclusive
    {W : Type u} {Choice : Type v}
    (R : Rel W) (F : W -> Option Choice)
    {r a b : W} {A B : Choice}
    (hPersist : FirstCommitPersistent R F)
    (hAB : A ≠ B)
    (hra : R r a) (hrb : R r b)
    (ha : F a = some A) (hb : F b = some B) :
    Dia R (Box R (FirstCommitPA F A)) r /\
    Not (Box R (Dia R (FirstCommitPA F A)) r) := by
  constructor
  · refine ⟨a, hra, ?_⟩
    intro y hay
    exact hPersist hay ha
  · intro hBox
    have hDiaB : Dia R (FirstCommitPA F A) b := hBox b hrb
    rcases hDiaB with ⟨y, hby, hAy⟩
    have hBy : F y = some B := hPersist hby hb
    have hSome : (some A : Option Choice) = some B :=
      Eq.trans hAy.symm hBy
    exact hAB (Option.some.inj hSome)

theorem firstCommit_B_branch_excludes_A
    {W : Type u} {Choice : Type v}
    (R : Rel W) (F : W -> Option Choice)
    {b : W} {A B : Choice}
    (hPersist : FirstCommitPersistent R F)
    (hAB : A ≠ B)
    (hb : F b = some B) :
    Not (Dia R (FirstCommitPA F A) b) := by
  intro hDia
  rcases hDia with ⟨y, hby, hAy⟩
  have hBy : F y = some B := hPersist hby hb
  have hSome : (some A : Option Choice) = some B :=
    Eq.trans hAy.symm hBy
  exact hAB (Option.some.inj hSome)

/-! ## General evidence-dynamics representation theorem -/

theorem infoLe_refl (e : Evidence) : InfoLe e e := by
  exact ⟨fun h => h, fun h => h⟩

structure EvidenceDynamics (W : Type u) where
  gR : Rel W
  dR : Rel W
  evidence : W -> Evidence
  decision : W -> DecisionState
  g_evidence_mono :
    forall {x y}, gR x y -> InfoLe (evidence x) (evidence y)
  g_decision_same :
    forall {x y}, gR x y -> decision x = decision y
  d_reflexive : Reflexive dR

def EvidenceDynamics.PosOnly
    {W : Type u} (V : ViewFn) (S : EvidenceDynamics W) (w : W) : Prop :=
  V (S.evidence w) (S.decision w) = .T

def PositiveRegionUpperClosed (V : ViewFn) : Prop :=
  forall (d : DecisionState) {e e' : Evidence},
    InfoLe e e' ->
    V e d = .T ->
    V e' d = .T

def EvidenceDefeasible (V : ViewFn) : Prop :=
  Not (PositiveRegionUpperClosed V)

def UniversalContentSubsumption (V : ViewFn) : Prop :=
  forall {W : Type} (S : EvidenceDynamics W) (w : W),
    Box S.dR (S.PosOnly V) w ->
    Box S.gR (S.PosOnly V) w

theorem upperClosed_implies_universal_subsumption
    (V : ViewFn)
    (hUpper : PositiveRegionUpperClosed V) :
    UniversalContentSubsumption V := by
  intro W S w hD y hwy
  have hAtW : S.PosOnly V w :=
    hD w (S.d_reflexive w)
  have hMono : InfoLe (S.evidence w) (S.evidence y) :=
    S.g_evidence_mono hwy
  have hStable :
      V (S.evidence y) (S.decision w) = .T :=
    hUpper (S.decision w) hMono hAtW
  have hDec : S.decision w = S.decision y :=
    S.g_decision_same hwy
  simpa [EvidenceDynamics.PosOnly, hDec] using hStable

inductive EvidencePairWorld where
  | lower
  | upper

deriving DecidableEq

def evidencePairG : Rel EvidencePairWorld
  | .lower, .lower => True
  | .lower, .upper => True
  | .upper, .upper => True
  | .upper, .lower => False

def evidencePairD : Rel EvidencePairWorld :=
  fun x y => x = y

def evidencePairSystem
    (e e' : Evidence) (d : DecisionState)
    (hLe : InfoLe e e') :
    EvidenceDynamics EvidencePairWorld where
  gR := evidencePairG
  dR := evidencePairD
  evidence
    | .lower => e
    | .upper => e'
  decision := fun _ => d
  g_evidence_mono := by
    intro x y hxy
    cases x <;> cases y <;> simp [evidencePairG] at hxy
    · exact infoLe_refl e
    · exact hLe
    · exact infoLe_refl e'
  g_decision_same := by
    intro x y hxy
    rfl
  d_reflexive := by
    intro x
    rfl

theorem universal_subsumption_implies_upperClosed
    (V : ViewFn)
    (hSub : UniversalContentSubsumption V) :
    PositiveRegionUpperClosed V := by
  intro d e e' hLe hPos
  let S := evidencePairSystem e e' d hLe
  have hD : Box S.dR (S.PosOnly V) .lower := by
    intro y hly
    have hy : EvidencePairWorld.lower = y := by
      simpa [S, evidencePairSystem, evidencePairD] using hly
    subst y
    exact hPos
  have hG : Box S.gR (S.PosOnly V) .lower :=
    hSub S .lower hD
  exact hG .upper (by trivial)

theorem universal_subsumption_iff_positive_region_upperClosed
    (V : ViewFn) :
    UniversalContentSubsumption V <-> PositiveRegionUpperClosed V := by
  constructor
  · exact universal_subsumption_implies_upperClosed V
  · exact upperClosed_implies_universal_subsumption V

theorem universal_subsumption_failure_iff_defeasible
    (V : ViewFn) :
    Not (UniversalContentSubsumption V) <-> EvidenceDefeasible V := by
  unfold EvidenceDefeasible
  exact not_congr (universal_subsumption_iff_positive_region_upperClosed V)

theorem infoLe_T_B : InfoLe Evidence.T Evidence.B := by
  simp [InfoLe, hasPos, hasNeg]

theorem resolvedPosDefeasible_is_TB_instance
    (V : ViewFn)
    (h : ResolvedPosDefeasible V) :
    EvidenceDefeasible V := by
  intro hUpper
  exact h.2 (hUpper .resolvedPos infoLe_T_B h.1)

theorem general_upperClosure_recovers_canonical_subsumption
    (V : ViewFn)
    (hUpper : PositiveRegionUpperClosed V) :
    CanonicalContentSubsumptionHolds V := by
  apply (content_subsumption_holds_iff_stable V).mpr
  intro hT
  exact hUpper .resolvedPos infoLe_T_B hT

end CPOG
