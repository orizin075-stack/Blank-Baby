namespace CPOG

/-!
# Subsumption boundary and specification-alignment lemmas
-/

def HistorySystem.PossComm
    {H : Type u} {Event : Type v} {Record : Type w} {Token : Type x}
    (S : HistorySystem H Event Record)
    (origin : Token -> Event) (h : H) (t : Token) : Prop :=
  S.committed h (origin t)

theorem HistorySystem.possComm_persistent
    {H : Type u} {Event : Type v} {Record : Type w} {Token : Type x}
    (S : HistorySystem H Event Record)
    (origin : Token -> Event) {h h' : H} (hr : S.Reach h h')
    {t : Token} :
    S.PossComm origin h t -> S.PossComm origin h' t := by
  intro ht
  exact HistorySystem.historical_persistence S hr (origin t) ht

abbrev FiniteGenState (n : Nat) := GenState (Fin n)

theorem finite_deferable_directed (n : Nat) :
    Directed (@genReach (Fin n)) :=
  deferable_directed

theorem finite_deferable_dot2 (n : Nat)
    (p : FiniteGenState n -> Prop) (S : FiniteGenState n) :
    Dia (@genReach (Fin n)) (Box (@genReach (Fin n)) p) S ->
    Box (@genReach (Fin n)) (Dia (@genReach (Fin n)) p) S :=
  deferable_dot2 p S

theorem observation_preserving_relation_refines_obsEq
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) (E : X -> X -> Prop)
    (hPres : forall {x y}, E x y -> forall i, O i x = O i y) :
    forall {x y}, E x y -> ObsEq O x y := by
  exact semantic_minimal_quotient O E hPres

def ObsProfile
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) (x : X) : I -> Y :=
  fun i => O i x

theorem obsEq_iff_profile_eq
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) {x y : X} :
    ObsEq O x y <-> ObsProfile O x = ObsProfile O y := by
  constructor
  · intro h
    apply funext
    intro i
    exact h i
  · intro h i
    exact congrFun h i

theorem observation_factors_through_profile
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) (x : X) (i : I) :
    O i x = ObsProfile O x i := by
  rfl

inductive SubEvent where
  | c

deriving DecidableEq

def subCommitted : SubWorld -> SubEvent -> Prop
  | .h, _ => False
  | .g, .c => True

def subHistory : HistorySystem SubWorld SubEvent Unit where
  stepG := gR
  stepD := dR
  committed := subCommitted
  record := fun _ _ => ()
  g_commit_mono := by
    intro h h' hG e hc
    cases h <;> cases h' <;> cases e <;> simp [gR, subCommitted] at *
  d_commit_same := by
    intro h h' hD e
    cases h <;> cases h' <;> cases e <;> simp [dR, subCommitted] at *
  g_record_preserve := by
    intro h h' hG e hc
    rfl
  d_record_preserve := by
    intro h h' hD e hc
    rfl

theorem gR_reflexive : Reflexive gR := by
  intro w
  cases w <;> trivial

theorem gR_transitive : Transitive gR := by
  intro x y z hxy hyz
  cases x <;> cases y <;> cases z <;> simp [gR] at *

theorem dR_reflexive : Reflexive dR := by
  intro w
  cases w <;> trivial

theorem dR_transitive : Transitive dR := by
  intro x y z hxy hyz
  cases x <;> cases y <;> cases z <;> simp [dR] at *

theorem sub_greach_iff_gR {x y : SubWorld} :
    subHistory.GReach x y <-> gR x y := by
  constructor
  · intro hxy
    exact RTC.preserve
      (P := fun z => gR x z)
      (fun hStep hReach => gR_transitive hReach hStep)
      hxy (gR_reflexive x)
  · intro hxy
    exact RTC.tail (RTC.refl x) hxy

theorem sub_dreach_iff_dR {x y : SubWorld} :
    subHistory.DReach x y <-> dR x y := by
  constructor
  · intro hxy
    exact RTC.preserve
      (P := fun z => dR x z)
      (fun hStep hReach => dR_transitive hReach hStep)
      hxy (dR_reflexive x)
  · intro hxy
    exact RTC.tail (RTC.refl x) hxy

def notCommittedInSubHistory (w : SubWorld) : Prop :=
  Not (subHistory.committed w .c)

theorem historical_subsumption_failure_in_history_system :
    Box subHistory.DReach notCommittedInSubHistory .h /\
    Not (Box subHistory.GReach notCommittedInSubHistory .h) := by
  constructor
  · intro v hv
    have hd : dR .h v := sub_dreach_iff_dR.mp hv
    cases v with
    | h => intro hc; cases hc
    | g => cases hd
  · intro hbox
    have hg : subHistory.GReach .h .g := sub_greach_iff_gR.mpr (by trivial)
    have hn := hbox .g hg
    exact hn (by trivial)

abbrev ViewFn := Evidence -> DecisionState -> Evidence

def PosOnlyBy (V : ViewFn) (w : SubWorld) : Prop :=
  V (currentEvidence w) (currentDecision w) = .T

def ResolvedPosDefeasible (V : ViewFn) : Prop :=
  V .T .resolvedPos = .T /\ V .B .resolvedPos ≠ .T

def CanonicalContentSubsumptionFailure (V : ViewFn) : Prop :=
  Box subHistory.DReach (PosOnlyBy V) .h /\
  Not (Box subHistory.GReach (PosOnlyBy V) .h)

def CanonicalContentSubsumptionHolds (V : ViewFn) : Prop :=
  Box subHistory.DReach (PosOnlyBy V) .h ->
  Box subHistory.GReach (PosOnlyBy V) .h

theorem boxD_posOnlyBy_iff (V : ViewFn) :
    Box subHistory.DReach (PosOnlyBy V) .h <->
      V .T .resolvedPos = .T := by
  constructor
  · intro hbox
    have hh : subHistory.DReach .h .h := RTC.refl _
    exact hbox .h hh
  · intro hT v hv
    have hd : dR .h v := sub_dreach_iff_dR.mp hv
    cases v with
    | h => exact hT
    | g => cases hd

theorem boxG_posOnlyBy_iff (V : ViewFn) :
    Box subHistory.GReach (PosOnlyBy V) .h <->
      (V .T .resolvedPos = .T /\ V .B .resolvedPos = .T) := by
  constructor
  · intro hbox
    constructor
    · exact hbox .h (RTC.refl _)
    · exact hbox .g (sub_greach_iff_gR.mpr (by trivial))
  · intro h v hv
    have hg : gR .h v := sub_greach_iff_gR.mp hv
    cases v with
    | h => exact h.1
    | g => exact h.2

theorem content_subsumption_failure_iff_defeasible (V : ViewFn) :
    CanonicalContentSubsumptionFailure V <-> ResolvedPosDefeasible V := by
  unfold CanonicalContentSubsumptionFailure ResolvedPosDefeasible
  rw [boxD_posOnlyBy_iff, boxG_posOnlyBy_iff]
  constructor
  · intro h
    constructor
    · exact h.1
    · intro hB
      exact h.2 ⟨h.1, hB⟩
  · intro h
    constructor
    · exact h.1
    · intro hBoth
      exact h.2 hBoth.2

theorem content_subsumption_holds_iff_stable (V : ViewFn) :
    CanonicalContentSubsumptionHolds V <->
      (V .T .resolvedPos = .T -> V .B .resolvedPos = .T) := by
  unfold CanonicalContentSubsumptionHolds
  rw [boxD_posOnlyBy_iff, boxG_posOnlyBy_iff]
  constructor
  · intro h hT
    exact (h hT).2
  · intro h hT
    exact ⟨hT, h hT⟩

theorem resolvedPos_dominance_recovers_subsumption
    (V : ViewFn)
    (hDom : forall e, V e .resolvedPos = .T) :
    CanonicalContentSubsumptionHolds V := by
  exact (content_subsumption_holds_iff_stable V).mpr
    (fun hT => hDom .B)

theorem defeasible_view_forces_content_subsumption_failure
    (V : ViewFn) (hDef : ResolvedPosDefeasible V) :
    CanonicalContentSubsumptionFailure V := by
  exact (content_subsumption_failure_iff_defeasible V).mpr hDef

end CPOG
