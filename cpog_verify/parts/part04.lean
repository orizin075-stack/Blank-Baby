  dot2_of_directed deferable_directed p S

end CPOG


namespace CPOG

inductive FCWorld where
  | root
  | a
  | b

deriving DecidableEq

def fcR : Rel FCWorld
  | .root, _ => True
  | .a, .a => True
  | .b, .b => True
  | _, _ => False

def PA : FCWorld -> Prop
  | .a => True
  | _ => False

theorem a_box_PA : Box fcR PA .a := by
  intro v hv
  cases v with
  | root => cases hv
  | a => trivial
  | b => cases hv

theorem b_not_dia_PA : Not (Dia fcR PA .b) := by
  intro h
  rcases h with ⟨v, hbv, hp⟩
  cases v with
  | root => cases hbv
  | a => cases hbv
  | b => cases hp

theorem firstCommit_dot2_antecedent : Dia fcR (Box fcR PA) .root := by
  exact ⟨.a, by trivial, a_box_PA⟩

theorem firstCommit_dot2_consequent_fails :
    Not (Box fcR (Dia fcR PA) .root) := by
  intro h
  have hb : Dia fcR PA .b := h .b (by trivial)
  exact b_not_dia_PA hb

theorem firstCommit_dot2_failure :
    Dia fcR (Box fcR PA) .root /\
    Not (Box fcR (Dia fcR PA) .root) :=
  ⟨firstCommit_dot2_antecedent, firstCommit_dot2_consequent_fails⟩

theorem firstCommit_not_directed : Not (DirectedAt fcR .root) := by
  intro hdir
  rcases hdir (x := .a) (y := .b) (by trivial) (by trivial) with ⟨z, haz, hbz⟩
  cases z with
  | root => cases haz
  | a => cases hbz
  | b => cases haz

end CPOG


namespace CPOG

inductive SubWorld where
  | h
  | g

deriving DecidableEq

def dR : Rel SubWorld
  | .h, .h => True
  | .g, .g => True
  | _, _ => False

def gR : Rel SubWorld
  | .h, .h => True
  | .h, .g => True
  | .g, .g => True
  | .g, .h => False

def committedC : SubWorld -> Prop
  | .h => False
  | .g => True

def notCommittedC (w : SubWorld) : Prop := Not (committedC w)

theorem historical_boxD : Box dR notCommittedC .h := by
  intro v hv
  cases v with
  | h => intro hc; cases hc
  | g => cases hv

theorem historical_not_boxG : Not (Box gR notCommittedC .h) := by
  intro hbox
  have hphi := hbox .g (by trivial)
  exact hphi (by trivial)

theorem historical_subsumption_failure :
    Box dR notCommittedC .h /\ Not (Box gR notCommittedC .h) :=
  ⟨historical_boxD, historical_not_boxG⟩

inductive Evidence where
  | N
  | T
  | F
  | B

deriving DecidableEq

def evidenceJoin : Evidence -> Evidence -> Evidence
  | .N, x => x
  | x, .N => x
  | .T, .T => .T
  | .F, .F => .F
  | .T, .F => .B
  | .F, .T => .B
  | .B, _ => .B
  | _, .B => .B

theorem T_join_F_eq_B : evidenceJoin .T .F = .B := rfl

def hasPos : Evidence -> Prop
  | .T | .B => True
  | .N | .F => False

def hasNeg : Evidence -> Prop
  | .F | .B => True
  | .N | .T => False

def InfoLe (a b : Evidence) : Prop :=
  (hasPos a -> hasPos b) /\ (hasNeg a -> hasNeg b)

theorem evidenceJoin_left_inflationary (a b : Evidence) :
    InfoLe a (evidenceJoin a b) := by
  cases a <;> cases b <;> simp [InfoLe, hasPos, hasNeg, evidenceJoin]

theorem evidenceJoin_right_inflationary (a b : Evidence) :
    InfoLe b (evidenceJoin a b) := by
  cases a <;> cases b <;> simp [InfoLe, hasPos, hasNeg, evidenceJoin]

theorem evidenceJoin_comm (a b : Evidence) :
    evidenceJoin a b = evidenceJoin b a := by
  cases a <;> cases b <;> rfl

theorem evidenceJoin_assoc (a b c : Evidence) :
    evidenceJoin (evidenceJoin a b) c = evidenceJoin a (evidenceJoin b c) := by
  cases a <;> cases b <;> cases c <;> rfl

def resolveNegative : Evidence -> Evidence
  | .B => .F
  | x => x

theorem resolve_can_remove_positive_support :
    Not (InfoLe .B (resolveNegative .B)) := by
  intro h
  exact h.1 (by trivial)

def currentEvidence : SubWorld -> Evidence
  | .h => .T
  | .g => evidenceJoin .T .F

inductive DecisionState where
  | open
  | contested
  | resolvedPos
  | resolvedNeg

deriving DecidableEq


def currentDecision : SubWorld -> DecisionState := fun _ => .resolvedPos


def DecideView (e : Evidence) (_d : DecisionState) : Evidence := e

def currentView (w : SubWorld) : Evidence :=
  DecideView (currentEvidence w) (currentDecision w)
