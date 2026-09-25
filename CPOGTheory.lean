import Std

/-!
CPOG epistemic potentialism — theorem layer v04.

This file lifts the previously kernel-checked finite countermodels to theorem schemas.
It separates:
* raw prefix-history divergence;
* recovery of .2 on convergent semantic quotients;
* persistence of FirstCommit divergence under label-preserving abstraction;
* a general criterion for failure of D→G Subsumption.
-/

namespace CPOG.EpistemicPotentialism.Theory

def Box {W : Type} (R : W → W → Prop) (phi : W → Prop) (w : W) : Prop :=
  ∀ v, R w v → phi v

def Dia {W : Type} (R : W → W → Prop) (phi : W → Prop) (w : W) : Prop :=
  ∃ v, R w v ∧ phi v

def DotTwoAt {W : Type} (R : W → W → Prop) (phi : W → Prop) (w : W) : Prop :=
  Dia R (Box R phi) w → Box R (Dia R phi) w

def Convergent {W : Type} (R : W → W → Prop) : Prop :=
  ∀ w u v, R w u → R w v → ∃ z, R u z ∧ R v z

theorem dotTwo_of_convergent {W : Type} {R : W → W → Prop}
    (hconv : Convergent R) (phi : W → Prop) (w : W) : DotTwoAt R phi w := by
  intro hdia
  rcases hdia with ⟨u, hwu, hubox⟩
  intro v hwv
  rcases hconv w u v hwu hwv with ⟨z, huz, hvz⟩
  exact ⟨z, hvz, hubox z huz⟩

theorem not_dotTwo_of_split {W : Type} {R : W → W → Prop} {phi : W → Prop}
    {root a b : W}
    (hra : R root a)
    (hrb : R root b)
    (ha : Box R phi a)
    (hb : Box R (fun x => ¬ phi x) b) :
    ¬ DotTwoAt R phi root := by
  intro hdot
  have hleft : Dia R (Box R phi) root := ⟨a, hra, ha⟩
  have hright : Box R (Dia R phi) root := hdot hleft
  rcases hright b hrb with ⟨z, hbz, hphiz⟩
  exact (hb z hbz) hphiz

def Prefix {A : Type} (h k : List A) : Prop :=
  ∃ tail, k = h ++ tail

theorem prefix_refl {A : Type} (h : List A) : Prefix h h := by
  exact ⟨[], by simp⟩

theorem prefix_trans {A : Type} {h k l : List A}
    (hhk : Prefix h k) (hkl : Prefix k l) : Prefix h l := by
  rcases hhk with ⟨t₁, rfl⟩
  rcases hkl with ⟨t₂, rfl⟩
  exact ⟨t₁ ++ t₂, by simp [List.append_assoc]⟩

theorem prefix_singleton_head {A : Type} {a : A} {h : List A}
    (hp : Prefix [a] h) : h.head? = some a := by
  rcases hp with ⟨t, rfl⟩
  rfl

theorem distinct_singletons_have_no_common_extension {A : Type} {a b : A}
    (hab : a ≠ b) :
    ¬ ∃ h : List A, Prefix [a] h ∧ Prefix [b] h := by
  rintro ⟨h, ha, hb⟩
  have hha : h.head? = some a := prefix_singleton_head ha
  have hhb : h.head? = some b := prefix_singleton_head hb
  have hs : some a = some b := hha.symm.trans hhb
  exact hab (Option.some.inj hs)

def FirstIs {A : Type} (a : A) (h : List A) : Prop := h.head? = some a

theorem raw_prefix_dotTwo_fails {A : Type} {a b : A} (hab : a ≠ b) :
    ¬ DotTwoAt (@Prefix A) (FirstIs a) ([] : List A) := by
  apply not_dotTwo_of_split (root := ([] : List A)) (a := [a]) (b := [b])
  · exact ⟨[a], by simp [Prefix]⟩
  · exact ⟨[b], by simp [Prefix]⟩
  · intro h hh
    exact prefix_singleton_head hh
  · intro h hh hA
    have hB : h.head? = some b := prefix_singleton_head hh
    have hs : some a = some b := hA.symm.trans hB
    exact hab (Option.some.inj hs)

inductive CommWorld where
  | root | onlyA | onlyB | both
  deriving DecidableEq, Repr

def CommRel : CommWorld → CommWorld → Prop
  | .root, _ => True
  | .onlyA, .onlyA => True
  | .onlyA, .both => True
  | .onlyB, .onlyB => True
  | .onlyB, .both => True
  | .both, .both => True
  | _, _ => False

def commJoin : CommWorld → CommWorld → CommWorld
  | .root, x => x
  | x, .root => x
  | .onlyA, .onlyA => .onlyA
  | .onlyB, .onlyB => .onlyB
  | .onlyA, .onlyB => .both
  | .onlyB, .onlyA => .both
  | .both, _ => .both
  | _, .both => .both

theorem commRel_to_join_left (u v : CommWorld) : CommRel u (commJoin u v) := by
  cases u <;> cases v <;> simp [CommRel, commJoin]

theorem commRel_to_join_right (u v : CommWorld) : CommRel v (commJoin u v) := by
  cases u <;> cases v <;> simp [CommRel, commJoin]

theorem commRel_convergent : Convergent CommRel := by
  intro w u v _ _
  exact ⟨commJoin u v, commRel_to_join_left u v, commRel_to_join_right u v⟩

theorem commutative_quotient_validates_dotTwo (phi : CommWorld → Prop) (w : CommWorld) :
    DotTwoAt CommRel phi w :=
  dotTwo_of_convergent commRel_convergent phi w

def LabelPersistent {W A : Type} (R : W → W → Prop) (lab : W → Option A) : Prop :=
  ∀ x y t, R x y → lab x = some t → lab y = some t

def AbstractionPreservesLabel {W Q A : Type} (q : W → Q) (lab : W → Option A) : Prop :=
  ∀ x y, q x = q y → lab x = lab y

def AbstractRel {W Q : Type} (R : W → W → Prop) (q : W → Q) : Q → Q → Prop :=
  fun qx qy => ∃ x y, q x = qx ∧ q y = qy ∧ R x y

def AbstractHasLabel {W Q A : Type} (q : W → Q) (lab : W → Option A) (a : A) (z : Q) : Prop :=
  ∃ x, q x = z ∧ lab x = some a

theorem firstCommit_no_common_abstract_future
    {W Q A : Type} {R : W → W → Prop} {q : W → Q} {lab : W → Option A}
    {xA xB : W} {a b : A}
    (hpersist : LabelPersistent R lab)
    (hpres : AbstractionPreservesLabel q lab)
    (hA : lab xA = some a)
    (hB : lab xB = some b)
    (hab : a ≠ b) :
    ¬ ∃ z, AbstractRel R q (q xA) z ∧ AbstractRel R q (q xB) z := by
  rintro ⟨z, hAz, hBz⟩
  rcases hAz with ⟨sA, tA, hsA, htA, hRA⟩
  rcases hBz with ⟨sB, tB, hsB, htB, hRB⟩
  have hsALab : lab sA = some a := by
    have hsame : lab sA = lab xA := hpres sA xA hsA
    exact hsame.trans hA
  have hsBLab : lab sB = some b := by
    have hsame : lab sB = lab xB := hpres sB xB hsB
    exact hsame.trans hB
  have htALab : lab tA = some a := hpersist sA tA a hRA hsALab
  have htBLab : lab tB = some b := hpersist sB tB b hRB hsBLab
  have hqt : q tA = q tB := htA.trans htB.symm
  have hsameT : lab tA = lab tB := hpres tA tB hqt
  have hs : some a = some b := htALab.symm.trans (hsameT.trans htBLab)
  exact hab (Option.some.inj hs)

theorem firstCommit_abstraction_dotTwo_fails
    {W Q A : Type} {R : W → W → Prop} {q : W → Q} {lab : W → Option A}
    {root xA xB : W} {a b : A}
    (hpersist : LabelPersistent R lab)
    (hpres : AbstractionPreservesLabel q lab)
    (hrootA : R root xA)
    (hrootB : R root xB)
    (hA : lab xA = some a)
    (hB : lab xB = some b)
    (hab : a ≠ b) :
    ¬ DotTwoAt (AbstractRel R q) (AbstractHasLabel q lab a) (q root) := by
  apply not_dotTwo_of_split (root := q root) (a := q xA) (b := q xB)
  · exact ⟨root, xA, rfl, rfl, hrootA⟩
  · exact ⟨root, xB, rfl, rfl, hrootB⟩
  · intro z hrel
    rcases hrel with ⟨s, t, hs, ht, hR⟩
    have hsLab : lab s = some a := by
      have hsame : lab s = lab xA := hpres s xA hs
      exact hsame.trans hA
    have htLab : lab t = some a := hpersist s t a hR hsLab
    exact ⟨t, ht, htLab⟩
  · intro z hrel hHas
    rcases hrel with ⟨s, t, hs, ht, hR⟩
    rcases hHas with ⟨u, hu, huLab⟩
    have hsLab : lab s = some b := by
      have hsame : lab s = lab xB := hpres s xB hs
      exact hsame.trans hB
    have htLab : lab t = some b := hpersist s t b hR hsLab
    have hqt : q t = q u := ht.trans hu.symm
    have hsame : lab t = lab u := hpres t u hqt
    have hsab : some b = some a := htLab.symm.trans (hsame.trans huLab)
    exact hab (Option.some.inj hsab.symm)

def SubsumptionAt {W : Type} (D G : W → W → Prop) (phi : W → Prop) (w : W) : Prop :=
  Box D phi w → Box G phi w

theorem subsumption_fails_of_G_counterexample
    {W : Type} {D G : W → W → Prop} {phi : W → Prop} {w v : W}
    (hD : Box D phi w)
    (hG : G w v)
    (hnot : ¬ phi v) :
    ¬ SubsumptionAt D G phi w := by
  intro hsub
  exact hnot (hsub hD v hG)

structure Evidence where
  pos : Bool
  neg : Bool
  deriving DecidableEq, Repr

def evN : Evidence := ⟨false, false⟩
def evT : Evidence := ⟨true, false⟩
def evF : Evidence := ⟨false, true⟩
def evB : Evidence := ⟨true, true⟩

def joinEvidence (x y : Evidence) : Evidence :=
  ⟨x.pos || y.pos, x.neg || y.neg⟩

inductive DecisionRecord where
  | openState | contested | resolvedPos | resolvedNeg
  deriving DecidableEq, Repr

def effectiveDecision : Evidence → DecisionRecord → DecisionRecord
  | ⟨_, true⟩, .resolvedPos => .contested
  | ⟨true, _⟩, .resolvedNeg => .contested
  | _, d => d

def decideView (ev : Evidence) (d : DecisionRecord) : Evidence :=
  match effectiveDecision ev d with
  | .resolvedPos => evT
  | .resolvedNeg => evF
  | .openState => ev
  | .contested => ev

def PositiveOnly (ev : Evidence) : Prop := ev.pos = true ∧ ev.neg = false

theorem positive_resolution_defeated_by_negative_support :
    effectiveDecision (joinEvidence evT evF) .resolvedPos = .contested := rfl

theorem defeated_positive_view_is_both :
    decideView (joinEvidence evT evF) .resolvedPos = evB := rfl

theorem defeated_positive_view_not_positiveOnly :
    ¬ PositiveOnly (decideView (joinEvidence evT evF) .resolvedPos) := by
  intro h
  cases h.2

inductive ContentWorld where
  | now | dSettled | gDefeat
  deriving DecidableEq, Repr

def DContent : ContentWorld → ContentWorld → Prop
  | .now, .now => True
  | .now, .dSettled => True
  | .dSettled, .dSettled => True
  | .gDefeat, .gDefeat => True
  | _, _ => False

def GContent : ContentWorld → ContentWorld → Prop
  | .now, .now => True
  | .now, .gDefeat => True
  | .dSettled, .dSettled => True
  | .gDefeat, .gDefeat => True
  | _, _ => False

def contentEvidence : ContentWorld → Evidence
  | .now => evT
  | .dSettled => evT
  | .gDefeat => joinEvidence evT evF

def contentDecision : ContentWorld → DecisionRecord
  | .now => .resolvedPos
  | .dSettled => .resolvedPos
  | .gDefeat => .resolvedPos

def contentView (w : ContentWorld) : Evidence :=
  decideView (contentEvidence w) (contentDecision w)

def ContentPositive (w : ContentWorld) : Prop := PositiveOnly (contentView w)

theorem content_D_settled : Box DContent ContentPositive .now := by
  intro v hv
  cases v <;> simp [DContent, ContentPositive, contentView, contentEvidence, contentDecision,
    PositiveOnly, decideView, effectiveDecision, evT] at hv ⊢

theorem content_G_has_defeater : GContent .now .gDefeat := by simp [GContent]

theorem content_G_defeater_not_positive : ¬ ContentPositive .gDefeat := by
  simpa [ContentPositive, contentView, contentEvidence, contentDecision] using
    defeated_positive_view_not_positiveOnly

theorem content_subsumption_fails :
    ¬ SubsumptionAt DContent GContent ContentPositive .now :=
  subsumption_fails_of_G_counterexample
    content_D_settled content_G_has_defeater content_G_defeater_not_positive

end CPOG.EpistemicPotentialism.Theory
