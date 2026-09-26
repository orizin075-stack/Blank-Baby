
namespace CPOG

/-!
# Unified history witness

This section places raw order divergence and FirstCommit divergence inside the
same concrete history system and evaluates both with the same abstraction.
-/

inductive UWorld where
  | root
  | orderA
  | orderB
  | orderAB
  | orderBA
  | commitA
  | commitB

deriving DecidableEq

inductive UEvent where
  | orderA
  | orderB
  | firstA
  | firstB

deriving DecidableEq

inductive UChoice where
  | A
  | B

deriving DecidableEq

inductive UAtom where
  | pFirstA

deriving DecidableEq

def uRG : Rel UWorld
  | .root, _ => True
  | .orderA, .orderA => True
  | .orderA, .orderAB => True
  | .orderB, .orderB => True
  | .orderB, .orderBA => True
  | .orderAB, .orderAB => True
  | .orderBA, .orderBA => True
  | .commitA, .commitA => True
  | .commitB, .commitB => True
  | _, _ => False

def uRD : Rel UWorld := fun x y => x = y

def uCommitted : UWorld -> UEvent -> Prop
  | .root, _ => False
  | .orderA, .orderA => True
  | .orderB, .orderB => True
  | .orderAB, .orderA => True
  | .orderAB, .orderB => True
  | .orderBA, .orderA => True
  | .orderBA, .orderB => True
  | .commitA, .firstA => True
  | .commitB, .firstB => True
  | _, _ => False

def unifiedHistory : HistorySystem UWorld UEvent Unit where
  stepG := uRG
  stepD := uRD
  committed := uCommitted
  record := fun _ _ => ()
  g_commit_mono := by
    intro h h' hR e hc
    cases h <;> cases h' <;> cases e <;> simp [uRG, uCommitted] at *
  d_commit_same := by
    intro h h' hD e
    subst h'
    rfl
  g_record_preserve := by
    intro h h' hR e hc
    rfl
  d_record_preserve := by
    intro h h' hD e hc
    rfl

theorem uRG_reflexive : Reflexive uRG := by
  intro w
  cases w <;> trivial

theorem uRG_transitive : Transitive uRG := by
  intro x y z hxy hyz
  cases x <;> cases y <;> cases z <;> simp [uRG] at *

theorem unified_greach_iff_uRG {x y : UWorld} :
    unifiedHistory.GReach x y <-> uRG x y := by
  constructor
  · intro hxy
    exact RTC.preserve
      (P := fun z => uRG x z)
      (fun hStep hReach => uRG_transitive hReach hStep)
      hxy (uRG_reflexive x)
  · intro hxy
    exact RTC.tail (RTC.refl x) hxy

def uFirstCommit : UWorld -> Option UChoice
  | .commitA => some .A
  | .commitB => some .B
  | _ => none

def uPA (w : UWorld) : Prop := uFirstCommit w = some .A

theorem uPA_iff_firstCommit_A (w : UWorld) :
    uPA w <-> uFirstCommit w = some .A := by
  rfl

theorem uFirstCommit_persistent_uRG
    {x y : UWorld} {c : UChoice}
    (hxy : uRG x y) (hx : uFirstCommit x = some c) :
    uFirstCommit y = some c := by
  cases x <;> cases y <;> cases c <;> simp [uRG, uFirstCommit] at *

theorem uFirstCommit_persistent
    {x y : UWorld} {c : UChoice}
    (hxy : unifiedHistory.GReach x y)
    (hx : uFirstCommit x = some c) :
    uFirstCommit y = some c := by
  exact uFirstCommit_persistent_uRG (unified_greach_iff_uRG.mp hxy) hx

theorem uFirstCommit_exclusive (w : UWorld) :
    Not (uFirstCommit w = some .A /\ uFirstCommit w = some .B) := by
  intro h
  have : (some UChoice.A : Option UChoice) = some UChoice.B := Eq.trans h.1.symm h.2
  cases this

theorem commitA_forces_future_A : Box uRG uPA .commitA := by
  intro y hAy
  exact uFirstCommit_persistent_uRG hAy rfl

theorem commitB_excludes_future_A : Not (Dia uRG uPA .commitB) := by
  intro h
  rcases h with ⟨y, hBy, hPA⟩
  have hB : uFirstCommit y = some .B :=
    uFirstCommit_persistent_uRG hBy rfl
  have hA : uFirstCommit y = some .A := hPA
  have : (some UChoice.A : Option UChoice) = some UChoice.B := Eq.trans hA.symm hB
  cases this

theorem unified_raw_order_no_join :
    uRG .root .orderAB /\
    uRG .root .orderBA /\
    Not (exists z, uRG .orderAB z /\ uRG .orderBA z) := by
  constructor
  · trivial
  constructor
  · trivial
  · intro h
    rcases h with ⟨z, hz1, hz2⟩
    cases z <;> simp [uRG] at hz1 hz2

theorem unified_raw_order_dot2_countervaluation :
    let p : UWorld -> Prop := fun z => uRG .orderAB z
    Dia uRG (Box uRG p) .root /\
      Not (Box uRG (Dia uRG p) .root) := by
  apply dot2_countervaluation_of_no_join (w := UWorld.root)
    (x := UWorld.orderAB) (y := UWorld.orderBA)
  · trivial
  · trivial
  · exact unified_raw_order_no_join.2.2

inductive UClass where
  | root
  | orderA
  | orderB
  | orderDone
  | commitA
  | commitB

deriving DecidableEq

def uClassOf : UWorld -> UClass
  | .root => .root
  | .orderA => .orderA
  | .orderB => .orderB
  | .orderAB => .orderDone
  | .orderBA => .orderDone
  | .commitA => .commitA
  | .commitB => .commitB

def uEquiv (x y : UWorld) : Prop := uClassOf x = uClassOf y

def uVal (w : UWorld) : UAtom -> Prop
  | .pFirstA => uPA w

def unifiedModel : Model UWorld UAtom where
  val := uVal
  rG := uRG
  rD := uRD
  rH := uRG

theorem uEquiv_cases {x y : UWorld} (h : uEquiv x y) :
    x = y \/
    (x = .orderAB /\ y = .orderBA) \/
    (x = .orderBA /\ y = .orderAB) := by
  cases x <;> cases y <;> simp [uEquiv, uClassOf] at h ⊢

theorem uRG_from_orderAB {z : UWorld} (h : uRG .orderAB z) : z = .orderAB := by
  cases z <;> simp [uRG] at h ⊢

theorem uRG_from_orderBA {z : UWorld} (h : uRG .orderBA z) : z = .orderBA := by
  cases z <;> simp [uRG] at h ⊢

theorem uRD_eq {x y : UWorld} (h : uRD x y) : x = y := h

theorem uEquiv_is_bisimulation :
    IsBisimulation unifiedModel unifiedModel uEquiv := by
  constructor
  · intro x y hxy a
    rcases uEquiv_cases hxy with hEq | hAB | hBA
    · subst y
      rfl
    · rcases hAB with ⟨rfl, rfl⟩
      cases a
      simp [unifiedModel, uVal, uPA, uFirstCommit]
    · rcases hBA with ⟨rfl, rfl⟩
      cases a
      simp [unifiedModel, uVal, uPA, uFirstCommit]
  · intro x y hxy x' hxx'
    rcases uEquiv_cases hxy with hEq | hAB | hBA
    · subst y
      exact ⟨x', hxx', rfl⟩
    · rcases hAB with ⟨rfl, rfl⟩
      have hx' : x' = .orderAB := uRG_from_orderAB hxx'
      subst x'
      exact ⟨.orderBA, by trivial, rfl⟩
    · rcases hBA with ⟨rfl, rfl⟩
      have hx' : x' = .orderBA := uRG_from_orderBA hxx'
      subst x'
      exact ⟨.orderAB, by trivial, rfl⟩
  · intro x y hxy y' hyy'
    rcases uEquiv_cases hxy with hEq | hAB | hBA
    · subst y
      exact ⟨y', hyy', rfl⟩
    · rcases hAB with ⟨rfl, rfl⟩
      have hy' : y' = .orderBA := uRG_from_orderBA hyy'
      subst y'
      exact ⟨.orderAB, by trivial, rfl⟩
    · rcases hBA with ⟨rfl, rfl⟩
      have hy' : y' = .orderAB := uRG_from_orderAB hyy'
      subst y'
      exact ⟨.orderBA, by trivial, rfl⟩
  · intro x y hxy x' hxx'
    have hxx : x = x' := uRD_eq hxx'
    subst x'
    exact ⟨y, rfl, hxy⟩
  · intro x y hxy y' hyy'
    have hyy : y = y' := uRD_eq hyy'
    subst y'
    exact ⟨x, rfl, hxy⟩
  · intro x y hxy x' hxx'
    rcases uEquiv_cases hxy with hEq | hAB | hBA
    · subst y
      exact ⟨x', hxx', rfl⟩
    · rcases hAB with ⟨rfl, rfl⟩
      have hx' : x' = .orderAB := uRG_from_orderAB hxx'
      subst x'
      exact ⟨.orderBA, by trivial, rfl⟩
    · rcases hBA with ⟨rfl, rfl⟩
      have hx' : x' = .orderBA := uRG_from_orderBA hxx'
      subst x'
      exact ⟨.orderAB, by trivial, rfl⟩
  · intro x y hxy y' hyy'
    rcases uEquiv_cases hxy with hEq | hAB | hBA
    · subst y
      exact ⟨y', hyy', rfl⟩
    · rcases hAB with ⟨rfl, rfl⟩
      have hy' : y' = .orderBA := uRG_from_orderBA hyy'
      subst y'
      exact ⟨.orderAB, by trivial, rfl⟩
    · rcases hBA with ⟨rfl, rfl⟩
      have hy' : y' = .orderAB := uRG_from_orderAB hyy'
      subst y'
      exact ⟨.orderBA, by trivial, rfl⟩

def uDynamicEquiv : DynamicEquiv unifiedModel uEquiv where
  refl := by intro x; rfl
  symm := by intro x y h; exact h.symm
  trans := by intro x y z hxy hyz; exact Eq.trans hxy hyz
  bisim := uEquiv_is_bisimulation

def uPresentation : QuotientPresentation UWorld UClass uEquiv where
  classOf := uClassOf
  surj := by
    intro q
    cases q with
    | root => exact ⟨.root, rfl⟩
    | orderA => exact ⟨.orderA, rfl⟩
    | orderB => exact ⟨.orderB, rfl⟩
    | orderDone => exact ⟨.orderAB, rfl⟩
    | commitA => exact ⟨.commitA, rfl⟩
    | commitB => exact ⟨.commitB, rfl⟩
  class_eq_iff := by
    intro x y
    rfl

theorem raw_order_difference_is_erased :
    uPresentation.classOf .orderAB = uPresentation.classOf .orderBA := by
  rfl

theorem firstCommit_difference_is_preserved :
    uPresentation.classOf .commitA ≠ uPresentation.classOf .commitB := by
  decide

def unifiedAntecedent : Formula UAtom :=
  .diaG (.boxG (.atom .pFirstA))

def unifiedConsequent : Formula UAtom :=
  .boxG (.diaG (.atom .pFirstA))

theorem unified_model_dot2_antecedent :
    Satisfies unifiedModel .root unifiedAntecedent := by
  change Dia uRG (Box uRG uPA) .root
  exact ⟨.commitA, by trivial, commitA_forces_future_A⟩

theorem unified_model_dot2_consequent_fails :
    Not (Satisfies unifiedModel .root unifiedConsequent) := by
  change Not (Box uRG (Dia uRG uPA) .root)
  intro h
  exact commitB_excludes_future_A (h .commitB (by trivial))

theorem unified_quotient_dot2_failure :
    Satisfies (quotientModel unifiedModel uPresentation)
      (uPresentation.classOf .root) unifiedAntecedent /\
    Not (Satisfies (quotientModel unifiedModel uPresentation)
      (uPresentation.classOf .root) unifiedConsequent) := by
  constructor
  · exact (quotient_invariance uDynamicEquiv uPresentation unifiedAntecedent .root).mp
      unified_model_dot2_antecedent
  · intro hq
    have hRaw : Satisfies unifiedModel .root unifiedConsequent :=
      (quotient_invariance uDynamicEquiv uPresentation unifiedConsequent .root).mpr hq
    exact unified_model_dot2_consequent_fails hRaw

theorem same_system_same_abstraction_contrast :
    (uRG .root .orderAB /\ uRG .root .orderBA /\
      Not (exists z, uRG .orderAB z /\ uRG .orderBA z)) /\
    (uPresentation.classOf .orderAB = uPresentation.classOf .orderBA) /\
    (uPresentation.classOf .commitA ≠ uPresentation.classOf .commitB) /\
    (Satisfies (quotientModel unifiedModel uPresentation)
        (uPresentation.classOf .root) unifiedAntecedent /\
      Not (Satisfies (quotientModel unifiedModel uPresentation)
        (uPresentation.classOf .root) unifiedConsequent)) := by
  exact ⟨unified_raw_order_no_join,
    raw_order_difference_is_erased,
    firstCommit_difference_is_preserved,
    unified_quotient_dot2_failure⟩

end CPOG
