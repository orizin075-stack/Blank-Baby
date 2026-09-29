import Std

/-!
CPOG epistemic-potentialism countermodels (minimal executable specification candidate, v03).

This module isolates four finite checks:
1. raw ordered-history branching can falsify .2;
2. a persistent FirstCommit predicate falsifies .2 in the semantic countermodel;
3. unrestricted Subsumption fails for a G-unstable historical predicate;
4. content-level Subsumption fails in an explicit FDE + decision-record model
   when G adds defeating evidence for an already generated token.

The proofs below are definitional computations (`rfl`), so they do not depend on
automation.
-/

namespace CPOG.EpistemicPotentialism

def boxB {W : Type} (succ : W -> List W) (phi : W -> Bool) (w : W) : Bool :=
  (succ w).all phi

def diaB {W : Type} (succ : W -> List W) (phi : W -> Bool) (w : W) : Bool :=
  (succ w).any phi

def dotTwoAt {W : Type} (succ : W -> List W) (phi : W -> Bool) (w : W) : Bool :=
  (!(diaB succ (fun u => boxB succ phi u) w)) ||
    boxB succ (fun u => diaB succ phi u) w

inductive RawWorld where
  | root | a | b | ab | ba
  deriving DecidableEq, Repr

def rawSucc : RawWorld -> List RawWorld
  | .root => [.root, .a, .b, .ab, .ba]
  | .a    => [.a, .ab]
  | .b    => [.b, .ba]
  | .ab   => [.ab]
  | .ba   => [.ba]

def rawSeenA : RawWorld -> Bool
  | .root => false
  | .a    => true
  | .b    => false
  | .ab   => true
  | .ba   => false

theorem raw_branching_dia_box :
    diaB rawSucc (fun u => boxB rawSucc rawSeenA u) .root = true := rfl

theorem raw_branching_box_dia :
    boxB rawSucc (fun u => diaB rawSucc rawSeenA u) .root = false := rfl

theorem raw_branching_dot2_fails :
    dotTwoAt rawSucc rawSeenA .root = false := rfl

inductive GWorld where
  | root | firstA | firstB
  deriving DecidableEq, Repr

def gSucc : GWorld -> List GWorld
  | .root   => [.root, .firstA, .firstB]
  | .firstA => [.firstA]
  | .firstB => [.firstB]

def firstCommitA : GWorld -> Bool
  | .root   => false
  | .firstA => true
  | .firstB => false

theorem firstCommit_dia_box :
    diaB gSucc (fun u => boxB gSucc firstCommitA u) .root = true := rfl

theorem firstCommit_box_dia :
    boxB gSucc (fun u => diaB gSucc firstCommitA u) .root = false := rfl

theorem firstCommit_dot2_fails :
    dotTwoAt gSucc firstCommitA .root = false := rfl

inductive EventCode where
  | c
  deriving DecidableEq, Repr

inductive HDWorld where
  | now | dLater | gCommit
  deriving DecidableEq, Repr

def dSucc : HDWorld -> List HDWorld
  | .now     => [.now, .dLater]
  | .dLater  => [.dLater]
  | .gCommit => [.gCommit]

def gSuccHD : HDWorld -> List HDWorld
  | .now     => [.now, .gCommit]
  | .dLater  => [.dLater]
  | .gCommit => [.gCommit]

def committedAt : HDWorld -> EventCode -> Bool
  | .now,     .c => false
  | .dLater,  .c => false
  | .gCommit, .c => true

def notCommittedC (w : HDWorld) : Bool := !(committedAt w .c)

theorem historical_boxD : boxB dSucc notCommittedC .now = true := rfl
theorem historical_boxG : boxB gSuccHD notCommittedC .now = false := rfl
theorem historical_subsumption_fails :
    ((!(boxB dSucc notCommittedC .now)) || boxB gSuccHD notCommittedC .now) = false := rfl

structure Evidence where
  pos : Bool
  neg : Bool
  deriving DecidableEq, Repr

def evN : Evidence := ⟨false, false⟩
def evT : Evidence := ⟨true,  false⟩
def evF : Evidence := ⟨false, true⟩
def evB : Evidence := ⟨true,  true⟩

def joinEvidence (a b : Evidence) : Evidence :=
  ⟨a.pos || b.pos, a.neg || b.neg⟩

inductive DecisionRecord where
  | openState | contested | resolvedPos | resolvedNeg
  deriving DecidableEq, Repr

def effectiveDecision : Evidence -> DecisionRecord -> DecisionRecord
  | ⟨_, true⟩, .resolvedPos => .contested
  | ⟨true, _⟩, .resolvedNeg => .contested
  | _, d => d

def decideView (ev : Evidence) (d : DecisionRecord) : Evidence :=
  match effectiveDecision ev d with
  | .resolvedPos => evT
  | .resolvedNeg => evF
  | .openState   => ev
  | .contested   => ev

inductive ContentWorld where
  | now | dSettled | gDefeat
  deriving DecidableEq, Repr

def dSuccContent : ContentWorld -> List ContentWorld
  | .now      => [.now, .dSettled]
  | .dSettled => [.dSettled]
  | .gDefeat  => [.gDefeat]

def gSuccContent : ContentWorld -> List ContentWorld
  | .now      => [.now, .gDefeat]
  | .dSettled => [.dSettled]
  | .gDefeat  => [.gDefeat]

def contentEvidence : ContentWorld -> Evidence
  | .now      => evT
  | .dSettled => evT
  | .gDefeat  => joinEvidence evT evF

def decisionRecord : ContentWorld -> DecisionRecord
  | .now      => .resolvedPos
  | .dSettled => .resolvedPos
  | .gDefeat  => .resolvedPos

def currentView (w : ContentWorld) : Evidence :=
  decideView (contentEvidence w) (decisionRecord w)

def positiveOnly (ev : Evidence) : Bool := ev.pos && !ev.neg
def posOnly (w : ContentWorld) : Bool := positiveOnly (currentView w)

theorem evidence_now : contentEvidence .now = evT := rfl
theorem evidence_after_G_defeat : contentEvidence .gDefeat = evB := rfl
theorem decision_reopens_after_G_defeat :
    effectiveDecision (contentEvidence .gDefeat) (decisionRecord .gDefeat) = .contested := rfl
theorem view_now : currentView .now = evT := rfl
theorem view_after_G_defeat : currentView .gDefeat = evB := rfl
theorem content_boxD : boxB dSuccContent posOnly .now = true := rfl
theorem content_boxG : boxB gSuccContent posOnly .now = false := rfl
theorem content_subsumption_fails :
    ((!(boxB dSuccContent posOnly .now)) || boxB gSuccContent posOnly .now) = false := rfl

end CPOG.EpistemicPotentialism
