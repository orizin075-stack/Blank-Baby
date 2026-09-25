import Std
import CPOGCheck

namespace CPOG.EpistemicPotentialism

def Box {W : Type} (R : W → W → Prop) (φ : W → Prop) (w : W) : Prop :=
  ∀ v, R w v → φ v

def Dia {W : Type} (R : W → W → Prop) (φ : W → Prop) (w : W) : Prop :=
  ∃ v, R w v ∧ φ v

def DotTwo {W : Type} (R : W → W → Prop) (φ : W → Prop) (w : W) : Prop :=
  Dia R (Box R φ) w → Box R (Dia R φ) w

def ConvergentAt {W : Type} (R : W → W → Prop) (w : W) : Prop :=
  ∀ u v, R w u → R w v → ∃ z, R u z ∧ R v z

theorem dotTwo_of_convergentAt {W : Type} {R : W → W → Prop} {φ : W → Prop} {w : W}
    (hc : ConvergentAt R w) : DotTwo R φ w := by
  intro hDiaBox u hwu
  rcases hDiaBox with ⟨v, hwv, hBoxV⟩
  rcases hc v u hwv hwu with ⟨z, hvz, huz⟩
  exact ⟨z, huz, hBoxV z hvz⟩

theorem dotTwo_failure_of_split {W : Type} {R : W → W → Prop} {φ : W → Prop}
    {root left right : W}
    (hLeft : R root left)
    (hRight : R root right)
    (hLeftPersistent : Box R φ left)
    (hRightExcludes : ¬ Dia R φ right) :
    ¬ DotTwo R φ root := by
  intro hDotTwo
  have hDiaBox : Dia R (Box R φ) root := ⟨left, hLeft, hLeftPersistent⟩
  have hBoxDia : Box R (Dia R φ) root := hDotTwo hDiaBox
  exact hRightExcludes (hBoxDia right hRight)

theorem firstCommit_divergence {W : Type} {R : W → W → Prop} {firstA : W → Prop}
    {root branchA branchB : W}
    (hA : R root branchA)
    (hB : R root branchB)
    (hAPersistent : ∀ u, R branchA u → firstA u)
    (hBExclusive : ∀ u, R branchB u → ¬ firstA u) :
    ¬ DotTwo R firstA root := by
  apply dotTwo_failure_of_split (left := branchA) (right := branchB)
  · exact hA
  · exact hB
  · intro u hu
    exact hAPersistent u hu
  · rintro ⟨u, hbu, hAu⟩
    exact hBExclusive u hbu hAu

def rawR (x y : RawWorld) : Prop := y ∈ rawSucc x

def rawSeenAProp (w : RawWorld) : Prop := rawSeenA w = true

theorem raw_relation_dotTwo_fails : ¬ DotTwo rawR rawSeenAProp .root := by
  apply firstCommit_divergence (branchA := RawWorld.a) (branchB := RawWorld.b)
  · simp [rawR, rawSucc]
  · simp [rawR, rawSucc]
  · intro u hu
    simp [rawR, rawSucc] at hu
    rcases hu with rfl | rfl
    · simp [rawSeenAProp, rawSeenA]
    · simp [rawSeenAProp, rawSeenA]
  · intro u hu
    simp [rawR, rawSucc] at hu
    rcases hu with rfl | rfl
    · simp [rawSeenAProp, rawSeenA]
    · simp [rawSeenAProp, rawSeenA]

def firstCommitR (x y : GWorld) : Prop := y ∈ gSucc x

def firstCommitAProp (w : GWorld) : Prop := firstCommitA w = true

theorem firstCommit_relation_dotTwo_fails : ¬ DotTwo firstCommitR firstCommitAProp .root := by
  apply firstCommit_divergence (branchA := GWorld.firstA) (branchB := GWorld.firstB)
  · simp [firstCommitR, gSucc]
  · simp [firstCommitR, gSucc]
  · intro u hu
    simp [firstCommitR, gSucc] at hu
    subst u
    simp [firstCommitAProp, firstCommitA]
  · intro u hu
    simp [firstCommitR, gSucc] at hu
    subst u
    simp [firstCommitAProp, firstCommitA]

structure CommState where
  seenA : Bool
  seenB : Bool
  deriving DecidableEq, Repr

def commR (x y : CommState) : Prop :=
  (x.seenA = true → y.seenA = true) ∧
  (x.seenB = true → y.seenB = true)

def commJoin (x y : CommState) : CommState :=
  ⟨x.seenA || y.seenA, x.seenB || y.seenB⟩

theorem comm_join_left (x y : CommState) : commR x (commJoin x y) := by
  constructor
  · intro hx
    simp [commJoin, hx]
  · intro hx
    simp [commJoin, hx]

theorem comm_join_right (x y : CommState) : commR y (commJoin x y) := by
  constructor
  · intro hy
    simp [commJoin, hy]
  · intro hy
    simp [commJoin, hy]

theorem commR_convergent (w : CommState) : ConvergentAt commR w := by
  intro u v _ _
  exact ⟨commJoin u v, comm_join_left u v, comm_join_right u v⟩

theorem commutative_abstraction_validates_dotTwo
    (φ : CommState → Prop) (w : CommState) : DotTwo commR φ w :=
  dotTwo_of_convergentAt (commR_convergent w)

def SubsumptionAt {W : Type}
    (RD RG : W → W → Prop) (φ : W → Prop) (w : W) : Prop :=
  Box RD φ w → Box RG φ w

theorem subsumption_failure_of_Dstable_Gcounterexample {W : Type}
    {RD RG : W → W → Prop} {φ : W → Prop} {w g : W}
    (hD : Box RD φ w)
    (hG : RG w g)
    (hNot : ¬ φ g) :
    ¬ SubsumptionAt RD RG φ w := by
  intro hSub
  have hBoxG : Box RG φ w := hSub hD
  exact hNot (hBoxG g hG)

def dR (x y : HDWorld) : Prop := y ∈ dSucc x

def gRHD (x y : HDWorld) : Prop := y ∈ gSuccHD x

def notCommittedCProp (w : HDWorld) : Prop := notCommittedC w = true

theorem historical_relation_subsumption_fails :
    ¬ SubsumptionAt dR gRHD notCommittedCProp .now := by
  apply subsumption_failure_of_Dstable_Gcounterexample (g := HDWorld.gCommit)
  · intro v hv
    simp [dR, dSucc] at hv
    rcases hv with rfl | rfl
    · simp [notCommittedCProp, notCommittedC, committedAt]
    · simp [notCommittedCProp, notCommittedC, committedAt]
  · simp [gRHD, gSuccHD]
  · simp [notCommittedCProp, notCommittedC, committedAt]

theorem resolvedPos_reopens_of_negative (ev : Evidence) (hneg : ev.neg = true) :
    effectiveDecision ev .resolvedPos = .contested := by
  cases ev with
  | mk p n =>
      cases n <;> simp_all [effectiveDecision]

theorem negative_join_reopens_resolvedPos (old new : Evidence) (hneg : new.neg = true) :
    effectiveDecision (joinEvidence old new) .resolvedPos = .contested := by
  apply resolvedPos_reopens_of_negative
  cases old with
  | mk op on =>
      cases new with
      | mk np nn =>
          simp_all [joinEvidence]

theorem negative_join_not_positiveOnly (old new : Evidence) (hneg : new.neg = true) :
    positiveOnly (decideView (joinEvidence old new) .resolvedPos) = false := by
  cases old with
  | mk op on =>
      cases new with
      | mk np nn =>
          cases nn <;> simp_all [joinEvidence, decideView, effectiveDecision, positiveOnly]

def PossHist {C : Type} (committed : C → Prop) (c : C) : Prop := committed c

def PossLive {C : Type}
    (committed admissible available : C → Prop) (c : C) : Prop :=
  committed c ∧ admissible c ∧ available c

theorem live_implies_historical {C : Type}
    {committed admissible available : C → Prop} {c : C} :
    PossLive committed admissible available c → PossHist committed c := by
  intro h
  exact h.1

def PossReach {W C : Type}
    (R : W → W → Prop) (live : W → C → Prop) (w : W) (c : C) : Prop :=
  ∃ v, R w v ∧ live v c

def PermanentlyClosed {W C : Type}
    (R : W → W → Prop) (live : W → C → Prop) (w : W) (c : C) : Prop :=
  ∀ v, R w v → ¬ live v c

theorem closed_implies_not_reachable {W C : Type}
    {R : W → W → Prop} {live : W → C → Prop} {w : W} {c : C}
    (hClosed : PermanentlyClosed R live w c) :
    ¬ PossReach R live w c := by
  rintro ⟨v, hwv, hlive⟩
  exact hClosed v hwv hlive

def ObsEq {I X : Type} {Y : I → Type}
    (obs : ∀ i, X → Y i) (x y : X) : Prop :=
  ∀ i, obs i x = obs i y

def observationSetoid {I X : Type} {Y : I → Type}
    (obs : ∀ i, X → Y i) : Setoid X where
  r := ObsEq obs
  iseqv := by
    constructor
    · intro x i
      rfl
    · intro x y h i
      exact (h i).symm
    · intro x y z hxy hyz i
      exact (hxy i).trans (hyz i)

def observationQuotientMap {I X : Type} {Y : I → Type}
    (obs : ∀ i, X → Y i) (x : X) : Quotient (observationSetoid obs) :=
  Quotient.mk _ x

def factorThroughObservation {I X Z : Type} {Y : I → Type}
    (obs : ∀ i, X → Y i)
    (g : X → Z)
    (hg : ∀ x y, ObsEq obs x y → g x = g y) :
    Quotient (observationSetoid obs) → Z :=
  Quotient.lift g (by
    intro a b hab
    exact hg a b hab)

theorem factorThroughObservation_commutes {I X Z : Type} {Y : I → Type}
    (obs : ∀ i, X → Y i)
    (g : X → Z)
    (hg : ∀ x y, ObsEq obs x y → g x = g y)
    (x : X) :
    factorThroughObservation obs g hg (observationQuotientMap obs x) = g x := rfl

theorem factorThroughObservation_unique {I X Z : Type} {Y : I → Type}
    (obs : ∀ i, X → Y i)
    (g : X → Z)
    (hg : ∀ x y, ObsEq obs x y → g x = g y)
    (h : Quotient (observationSetoid obs) → Z)
    (hh : ∀ x, h (observationQuotientMap obs x) = g x) :
    h = factorThroughObservation obs g hg := by
  funext q
  refine Quotient.inductionOn q ?_
  intro x
  calc
    h (Quotient.mk (observationSetoid obs) x) = g x := by
      simpa [observationQuotientMap] using hh x
    _ = factorThroughObservation obs g hg (Quotient.mk (observationSetoid obs) x) := by
      rfl

end CPOG.EpistemicPotentialism
