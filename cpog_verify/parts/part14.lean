namespace CPOG

/-!
# Split-root modal contrast

The independent-order branch and the FirstCommit branch live in one model and
are abstracted by one quotient, but have separate roots.  The quotient erases
the independent ordering difference and restores directedness/.2 at the
independent root, while a persistent FirstCommit A/B split still refutes .2 at
the FirstCommit root.
-/

inductive SplitWorld where
  | ri
  | ia
  | ib
  | iab
  | iba
  | rf
  | ca0
  | ca1
  | cb0
  | cb1

deriving DecidableEq

inductive SplitEvent where
  | orderA
  | orderB
  | firstA
  | firstB

deriving DecidableEq

inductive SplitChoice where
  | A
  | B

deriving DecidableEq

inductive SplitAtom where
  | pA

deriving DecidableEq

def splitRG : Rel SplitWorld
  | .ri, .ri => True
  | .ri, .ia => True
  | .ri, .ib => True
  | .ri, .iab => True
  | .ri, .iba => True
  | .ia, .ia => True
  | .ia, .iab => True
  | .ib, .ib => True
  | .ib, .iba => True
  | .iab, .iab => True
  | .iba, .iba => True
  | .rf, .rf => True
  | .rf, .ca0 => True
  | .rf, .ca1 => True
  | .rf, .cb0 => True
  | .rf, .cb1 => True
  | .ca0, .ca0 => True
  | .ca0, .ca1 => True
  | .ca1, .ca1 => True
  | .cb0, .cb0 => True
  | .cb0, .cb1 => True
  | .cb1, .cb1 => True
  | _, _ => False

def splitRD : Rel SplitWorld := fun x y => x = y

def splitCommitted : SplitWorld -> SplitEvent -> Prop
  | .ri, _ => False
  | .ia, .orderA => True
  | .ib, .orderB => True
  | .iab, .orderA => True
  | .iab, .orderB => True
  | .iba, .orderA => True
  | .iba, .orderB => True
  | .rf, _ => False
  | .ca0, .firstA => True
  | .ca1, .firstA => True
  | .cb0, .firstB => True
  | .cb1, .firstB => True
  | _, _ => False

def splitHistory : HistorySystem SplitWorld SplitEvent Unit where
  stepG := splitRG
  stepD := splitRD
  committed := splitCommitted
  record := fun _ _ => ()
  g_commit_mono := by
    intro h h' hR e hc
    cases h <;> cases h' <;> cases e <;>
      simp [splitRG, splitCommitted] at *
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

def splitFirstCommit : SplitWorld -> Option SplitChoice
  | .ca0 => some .A
  | .ca1 => some .A
  | .cb0 => some .B
  | .cb1 => some .B
  | _ => none

theorem splitFirstCommit_persistent :
    FirstCommitPersistent splitRG splitFirstCommit := by
  intro x y c hxy hx
  cases x <;> cases y <;> cases c <;>
    simp [splitRG, splitFirstCommit] at *

theorem split_firstCommit_has_proper_A_future :
    splitRG .ca0 .ca1 /\ .ca0 ≠ .ca1 /\
    splitFirstCommit .ca0 = some .A /\
    splitFirstCommit .ca1 = some .A := by
  exact ⟨by trivial, by decide, rfl, rfl⟩

theorem split_firstCommit_has_proper_B_future :
    splitRG .cb0 .cb1 /\ .cb0 ≠ .cb1 /\
    splitFirstCommit .cb0 = some .B /\
    splitFirstCommit .cb1 = some .B := by
  exact ⟨by trivial, by decide, rfl, rfl⟩

theorem split_firstCommit_dot2_failure_raw :
    Dia splitRG
      (Box splitRG (FirstCommitPA splitFirstCommit SplitChoice.A)) .rf /\
    Not (Box splitRG
      (Dia splitRG (FirstCommitPA splitFirstCommit SplitChoice.A)) .rf) := by
  exact firstCommit_dot2_failure_of_persistent_exclusive
    (R := splitRG) (F := splitFirstCommit)
    (r := SplitWorld.rf)
    (a := SplitWorld.ca0) (b := SplitWorld.cb0)
    (A := SplitChoice.A) (B := SplitChoice.B)
    splitFirstCommit_persistent
    (by decide)
    (by trivial) (by trivial) rfl rfl

theorem split_independent_raw_not_directed :
    Not (DirectedAt splitRG .ri) := by
  intro hDir
  rcases hDir (x := .ia) (y := .ib) (by trivial) (by trivial) with
    ⟨z, hiaz, hibz⟩
  cases z <;> simp [splitRG] at hiaz hibz

inductive SplitClass where
  | ri
  | ia
  | ib
  | idone
  | rf
  | ca0
  | ca1
  | cb0
  | cb1

deriving DecidableEq

def splitClassOf : SplitWorld -> SplitClass
  | .ri => .ri
  | .ia => .ia
  | .ib => .ib
  | .iab => .idone
  | .iba => .idone
  | .rf => .rf
  | .ca0 => .ca0
  | .ca1 => .ca1
  | .cb0 => .cb0
  | .cb1 => .cb1

def splitEquiv (x y : SplitWorld) : Prop :=
  splitClassOf x = splitClassOf y

def splitVal (w : SplitWorld) : SplitAtom -> Prop
  | .pA => FirstCommitPA splitFirstCommit .A w

def splitModel : Model SplitWorld SplitAtom where
  val := splitVal
  rG := splitRG
  rD := splitRD
  rH := splitRG

theorem splitEquiv_cases {x y : SplitWorld} (h : splitEquiv x y) :
    x = y \/
    (x = .iab /\ y = .iba) \/
    (x = .iba /\ y = .iab) := by
  cases x <;> cases y <;>
    simp [splitEquiv, splitClassOf] at h ⊢

theorem splitRG_from_iab {z : SplitWorld}
    (h : splitRG .iab z) : z = .iab := by
  cases z <;> simp [splitRG] at h ⊢

theorem splitRG_from_iba {z : SplitWorld}
    (h : splitRG .iba z) : z = .iba := by
  cases z <;> simp [splitRG] at h ⊢

theorem splitRD_eq {x y : SplitWorld}
    (h : splitRD x y) : x = y := h

theorem splitEquiv_is_bisimulation :
    IsBisimulation splitModel splitModel splitEquiv := by
  constructor
  · intro x y hxy a
    rcases splitEquiv_cases hxy with hEq | hAB | hBA
    · subst y
      rfl
    · rcases hAB with ⟨rfl, rfl⟩
      cases a
      simp [splitModel, splitVal, FirstCommitPA, splitFirstCommit]
    · rcases hBA with ⟨rfl, rfl⟩
      cases a
      simp [splitModel, splitVal, FirstCommitPA, splitFirstCommit]
  · intro x y hxy x' hxx'
    rcases splitEquiv_cases hxy with hEq | hAB | hBA
    · subst y
      exact ⟨x', hxx', rfl⟩
    · rcases hAB with ⟨rfl, rfl⟩
      have hx' : x' = .iab := splitRG_from_iab hxx'
      subst x'
      exact ⟨.iba, by trivial, rfl⟩
    · rcases hBA with ⟨rfl, rfl⟩
      have hx' : x' = .iba := splitRG_from_iba hxx'
      subst x'
      exact ⟨.iab, by trivial, rfl⟩
  · intro x y hxy y' hyy'
    rcases splitEquiv_cases hxy with hEq | hAB | hBA
    · subst y
      exact ⟨y', hyy', rfl⟩
    · rcases hAB with ⟨rfl, rfl⟩
      have hy' : y' = .iba := splitRG_from_iba hyy'
      subst y'
      exact ⟨.iab, by trivial, rfl⟩
    · rcases hBA with ⟨rfl, rfl⟩
      have hy' : y' = .iab := splitRG_from_iab hyy'
      subst y'
      exact ⟨.iba, by trivial, rfl⟩
  · intro x y hxy x' hxx'
    have hxx : x = x' := splitRD_eq hxx'
    subst x'
    exact ⟨y, rfl, hxy⟩
  · intro x y hxy y' hyy'
    have hyy : y = y' := splitRD_eq hyy'
    subst y'
    exact ⟨x, rfl, hxy⟩
  · intro x y hxy x' hxx'
    rcases splitEquiv_cases hxy with hEq | hAB | hBA
    · subst y
      exact ⟨x', hxx', rfl⟩
    · rcases hAB with ⟨rfl, rfl⟩
      have hx' : x' = .iab := splitRG_from_iab hxx'
      subst x'
      exact ⟨.iba, by trivial, rfl⟩
    · rcases hBA with ⟨rfl, rfl⟩
      have hx' : x' = .iba := splitRG_from_iba hxx'
      subst x'
      exact ⟨.iab, by trivial, rfl⟩
  · intro x y hxy y' hyy'
    rcases splitEquiv_cases hxy with hEq | hAB | hBA
    · subst y
      exact ⟨y', hyy', rfl⟩
    · rcases hAB with ⟨rfl, rfl⟩
      have hy' : y' = .iba := splitRG_from_iba hyy'
      subst y'
      exact ⟨.iab, by trivial, rfl⟩
    · rcases hBA with ⟨rfl, rfl⟩
      have hy' : y' = .iab := splitRG_from_iab hyy'
      subst y'
      exact ⟨.iba, by trivial, rfl⟩

def splitDynamicEquiv : DynamicEquiv splitModel splitEquiv where
  refl := by intro x; rfl
  symm := by intro x y h; exact h.symm
  trans := by intro x y z hxy hyz; exact Eq.trans hxy hyz
  bisim := splitEquiv_is_bisimulation

def splitPresentation :
    QuotientPresentation SplitWorld SplitClass splitEquiv where
  classOf := splitClassOf
  surj := by
    intro q
    cases q with
    | ri => exact ⟨.ri, rfl⟩
    | ia => exact ⟨.ia, rfl⟩
    | ib => exact ⟨.ib, rfl⟩
    | idone => exact ⟨.iab, rfl⟩
    | rf => exact ⟨.rf, rfl⟩
    | ca0 => exact ⟨.ca0, rfl⟩
    | ca1 => exact ⟨.ca1, rfl⟩
    | cb0 => exact ⟨.cb0, rfl⟩
    | cb1 => exact ⟨.cb1, rfl⟩
  class_eq_iff := by
    intro x y
    rfl

theorem split_order_difference_erased :
    splitPresentation.classOf .iab =
      splitPresentation.classOf .iba := by
  rfl

theorem split_independent_raw_successor_reaches_done
    {y : SplitWorld} (h : splitRG .ri y) :
    exists z,
      splitRG y z /\ splitClassOf z = .idone := by
  cases y with
  | ri => exact ⟨.iab, by trivial, rfl⟩
  | ia => exact ⟨.iab, by trivial, rfl⟩
  | ib => exact ⟨.iba, by trivial, rfl⟩
  | iab => exact ⟨.iab, by trivial, rfl⟩
  | iba => exact ⟨.iba, by trivial, rfl⟩
  | rf => cases h
  | ca0 => cases h
  | ca1 => cases h
  | cb0 => cases h
  | cb1 => cases h

theorem split_independent_quotient_successor_reaches_done
    {q : SplitClass}
    (h : quotientRel splitPresentation splitRG
      (splitPresentation.classOf .ri) q) :
    quotientRel splitPresentation splitRG q .idone := by
  rcases h with ⟨x, y, hx, hy, hxy⟩
  have hxri : x = .ri := by
    change splitClassOf x = SplitClass.ri at hx
    cases x <;> simp [splitClassOf] at hx ⊢
  subst x
  rcases split_independent_raw_successor_reaches_done hxy with
    ⟨z, hyz, hz⟩
  exact ⟨y, z, hy, hz, hyz⟩

theorem split_independent_quotient_directed :
    DirectedAt
      (quotientModel splitModel splitPresentation).rG
      (splitPresentation.classOf .ri) := by
  change DirectedAt
    (quotientRel splitPresentation splitRG)
    (splitPresentation.classOf .ri)
  intro x y hx hy
  exact ⟨.idone,
    split_independent_quotient_successor_reaches_done hx,
    split_independent_quotient_successor_reaches_done hy⟩

theorem split_independent_quotient_dot2_all
    (p : SplitClass -> Prop) :
    Dia (quotientModel splitModel splitPresentation).rG
      (Box (quotientModel splitModel splitPresentation).rG p)
      (splitPresentation.classOf .ri) ->
    Box (quotientModel splitModel splitPresentation).rG
      (Dia (quotientModel splitModel splitPresentation).rG p)
      (splitPresentation.classOf .ri) := by
  exact dot2_of_directedAt split_independent_quotient_directed p

def splitAntecedent : Formula SplitAtom :=
  .diaG (.boxG (.atom .pA))

def splitConsequent : Formula SplitAtom :=
  .boxG (.diaG (.atom .pA))

theorem split_model_firstCommit_antecedent :
    Satisfies splitModel .rf splitAntecedent := by
  change Dia splitRG
    (Box splitRG (FirstCommitPA splitFirstCommit .A)) .rf
  exact split_firstCommit_dot2_failure_raw.1

theorem split_model_firstCommit_consequent_fails :
    Not (Satisfies splitModel .rf splitConsequent) := by
  change Not (Box splitRG
    (Dia splitRG (FirstCommitPA splitFirstCommit .A)) .rf)
  exact split_firstCommit_dot2_failure_raw.2

theorem split_firstCommit_quotient_dot2_failure :
    Satisfies (quotientModel splitModel splitPresentation)
      (splitPresentation.classOf .rf) splitAntecedent /\
    Not (Satisfies (quotientModel splitModel splitPresentation)
      (splitPresentation.classOf .rf) splitConsequent) := by
  constructor
  · exact
      (quotient_invariance splitDynamicEquiv splitPresentation
        splitAntecedent .rf).mp
      split_model_firstCommit_antecedent
  · intro hq
    have hRaw : Satisfies splitModel .rf splitConsequent :=
      (quotient_invariance splitDynamicEquiv splitPresentation
        splitConsequent .rf).mpr hq
    exact split_model_firstCommit_consequent_fails hRaw

theorem split_same_abstraction_modal_contrast :
    Not (DirectedAt splitRG .ri) /\
    DirectedAt
      (quotientModel splitModel splitPresentation).rG
      (splitPresentation.classOf .ri) /\
    (forall p : SplitClass -> Prop,
      Dia (quotientModel splitModel splitPresentation).rG
        (Box (quotientModel splitModel splitPresentation).rG p)
        (splitPresentation.classOf .ri) ->
      Box (quotientModel splitModel splitPresentation).rG
        (Dia (quotientModel splitModel splitPresentation).rG p)
        (splitPresentation.classOf .ri)) /\
    (Satisfies (quotientModel splitModel splitPresentation)
        (splitPresentation.classOf .rf) splitAntecedent /\
      Not (Satisfies (quotientModel splitModel splitPresentation)
        (splitPresentation.classOf .rf) splitConsequent)) := by
  exact ⟨split_independent_raw_not_directed,
    split_independent_quotient_directed,
    split_independent_quotient_dot2_all,
    split_firstCommit_quotient_dot2_failure⟩

end CPOG
