import Std

/-!
Generic theorem layer for CPOG epistemic potentialism.

This module proves the paper-level claims independently of the finite
countermodels in CPOGCheck.lean.
-/

namespace CPOG.EpistemicPotentialism.Generic

universe u v w

/-! Relational modal semantics. -/

def BoxP {W : Type u} (R : W → W → Prop) (φ : W → Prop) (x : W) : Prop :=
  ∀ y, R x y → φ y

def DiaP {W : Type u} (R : W → W → Prop) (φ : W → Prop) (x : W) : Prop :=
  ∃ y, R x y ∧ φ y

def DotTwoP {W : Type u} (R : W → W → Prop) (φ : W → Prop) (x : W) : Prop :=
  DiaP R (BoxP R φ) x → BoxP R (DiaP R φ) x

def ConvergentAt {W : Type u} (R : W → W → Prop) (x : W) : Prop :=
  ∀ y z, R x y → R x z → ∃ t, R y t ∧ R z t

theorem dotTwo_of_convergentAt
    {W : Type u} {R : W → W → Prop} {φ : W → Prop} {x : W}
    (hconv : ConvergentAt R x) : DotTwoP R φ x := by
  intro hDiaBox
  rcases hDiaBox with ⟨y, hxy, hyBox⟩
  intro z hxz
  rcases hconv y z hxy hxz with ⟨t, hyt, hzt⟩
  exact ⟨t, hzt, hyBox t hyt⟩

theorem dotTwo_fails_of_nonconvergent_pair
    {W : Type u} {R : W → W → Prop} {x y z : W}
    (hxy : R x y) (hxz : R x z)
    (hnocommon : ¬ ∃ t, R y t ∧ R z t) :
    ¬ DotTwoP R (fun t => R y t) x := by
  intro hdot
  have hDiaBox : DiaP R (BoxP R (fun t => R y t)) x := by
    refine ⟨y, hxy, ?_⟩
    intro t hyt
    exact hyt
  have hBoxDia := hdot hDiaBox
  rcases hBoxDia z hxz with ⟨t, hzt, hyt⟩
  exact hnocommon ⟨t, hyt, hzt⟩

/-! Persistent FirstCommit ratchets. -/

def LabelPersistent {W : Type u} {L : Type v}
    (R : W → W → Prop) (label : W → Option L) : Prop :=
  ∀ ⦃x y : W⦄ ⦃ell : L⦄,
    R x y → label x = some ell → label y = some ell

theorem distinct_persistent_labels_no_common_successor
    {W : Type u} {L : Type v}
    {R : W → W → Prop} {label : W → Option L}
    {a b : L} {x y : W}
    (hab : a ≠ b)
    (hx : label x = some a)
    (hy : label y = some b)
    (hpersist : LabelPersistent R label) :
    ¬ ∃ t, R x t ∧ R y t := by
  rintro ⟨t, hxt, hyt⟩
  have hta : label t = some a := hpersist hxt hx
  have htb : label t = some b := hpersist hyt hy
  have hs : some a = some b := hta.symm.trans htb
  exact hab (Option.some.inj hs)

theorem firstCommit_ratchet_dotTwo_fails
    {W : Type u} {L : Type v}
    {R : W → W → Prop} {label : W → Option L}
    {root x y : W} {a b : L}
    (hab : a ≠ b)
    (hrx : R root x) (hry : R root y)
    (hx : label x = some a) (hy : label y = some b)
    (hpersist : LabelPersistent R label) :
    ¬ DotTwoP R (fun t => label t = some a) root := by
  intro hdot
  have hDiaBox : DiaP R (BoxP R (fun t => label t = some a)) root := by
    refine ⟨x, hrx, ?_⟩
    intro t hxt
    exact hpersist hxt hx
  have hBoxDia := hdot hDiaBox
  rcases hBoxDia y hry with ⟨t, hyt, hta⟩
  have htb : label t = some b := hpersist hyt hy
  have hs : some a = some b := hta.symm.trans htb
  exact hab (Option.some.inj hs)

theorem firstCommit_observation_prevents_merge
    {H : Type u} {Q : Type v} {L : Type w}
    (q : H → Q) (labelH : H → Option L) (labelQ : Q → Option L)
    (hpres : ∀ h, labelQ (q h) = labelH h)
    {x y : H} {a b : L}
    (hab : a ≠ b)
    (hx : labelH x = some a)
    (hy : labelH y = some b) :
    q x ≠ q y := by
  intro hxy
  have hqa : labelQ (q x) = some a := (hpres x).trans hx
  have hqb : labelQ (q y) = some b := (hpres y).trans hy
  rw [hxy] at hqa
  have hs : some a = some b := hqa.symm.trans hqb
  exact hab (Option.some.inj hs)

/-! Raw ordered histories. -/

def Prefix {A : Type u} (xs ys : List A) : Prop :=
  ∃ tail, ys = xs ++ tail

theorem prefix_nil {A : Type u} (xs : List A) :
    Prefix ([] : List A) xs := by
  exact ⟨xs, by simp⟩

theorem distinct_singleton_prefixes_no_common
    {A : Type u} {a b : A} (hab : a ≠ b) :
    ¬ ∃ zs : List A, Prefix [a] zs ∧ Prefix [b] zs := by
  rintro ⟨zs, ⟨ta, hza⟩, ⟨tb, hzb⟩⟩
  have hEq : a :: ta = b :: tb := by
    simpa using hza.symm.trans hzb
  cases hEq
  exact hab rfl

theorem raw_prefix_dotTwo_fails
    {A : Type u} {a b : A} (hab : a ≠ b) :
    ¬ DotTwoP (Prefix (A := A))
      (fun zs => Prefix [a] zs) ([] : List A) := by
  apply dotTwo_fails_of_nonconvergent_pair
      (R := Prefix (A := A))
      (x := ([] : List A)) (y := [a]) (z := [b])
  · exact prefix_nil [a]
  · exact prefix_nil [b]
  · exact distinct_singleton_prefixes_no_common hab

def firstAction? {A : Type u} (xs : List A) : Option A := xs.head?

theorem firstAction_persistent
    {A : Type u} :
    LabelPersistent (Prefix (A := A)) (firstAction? (A := A)) := by
  intro x y ell hxy hx
  rcases hxy with ⟨tail, rfl⟩
  cases x with
  | nil =>
      simp [firstAction?] at hx
  | cons c cs =>
      simpa [firstAction?] using hx

theorem raw_prefix_firstCommit_dotTwo_fails
    {A : Type u} {a b : A} (hab : a ≠ b) :
    ¬ DotTwoP (Prefix (A := A))
      (fun zs => firstAction? (A := A) zs = some a) ([] : List A) := by
  apply firstCommit_ratchet_dotTwo_fails
      (R := Prefix (A := A))
      (label := firstAction? (A := A))
      (root := ([] : List A))
      (x := [a]) (y := [b]) (a := a) (b := b)
  · exact hab
  · exact prefix_nil [a]
  · exact prefix_nil [b]
  · rfl
  · rfl
  · exact firstAction_persistent

/-! G/D Subsumption. -/

def SubsumptionAt {W : Type u}
    (RD RG : W → W → Prop) (φ : W → Prop) (x : W) : Prop :=
  BoxP RD φ x → BoxP RG φ x

theorem subsumption_fails_of_G_counterexample
    {W : Type u} {RD RG : W → W → Prop} {φ : W → Prop}
    {x g : W}
    (hD : BoxP RD φ x)
    (hxg : RG x g)
    (hnot : ¬ φ g) :
    ¬ SubsumptionAt RD RG φ x := by
  intro hsub
  have hG := hsub hD
  exact hnot (hG g hxg)

/-! FDE evidence and defeasible determination. -/

structure GEvidence where
  pos : Bool
  neg : Bool
  deriving DecidableEq, Repr

def gEvT : GEvidence := ⟨true, false⟩
def gEvF : GEvidence := ⟨false, true⟩
def gEvB : GEvidence := ⟨true, true⟩

def joinGEvidence (a b : GEvidence) : GEvidence :=
  ⟨a.pos || b.pos, a.neg || b.neg⟩

inductive GDecision where
  | openState | contested | resolvedPos | resolvedNeg
  deriving DecidableEq, Repr

def effectiveGDecision : GEvidence → GDecision → GDecision
  | ⟨_, true⟩, .resolvedPos => .contested
  | ⟨true, _⟩, .resolvedNeg => .contested
  | _, d => d

def gDecideView (ev : GEvidence) (d : GDecision) : GEvidence :=
  match effectiveGDecision ev d with
  | .resolvedPos => gEvT
  | .resolvedNeg => gEvF
  | .openState => ev
  | .contested => ev

def gPositiveOnly (ev : GEvidence) : Bool := ev.pos && !ev.neg

theorem negative_support_reopens_resolvedPos
    (base incoming : GEvidence)
    (hneg : incoming.neg = true) :
    effectiveGDecision (joinGEvidence base incoming) .resolvedPos = .contested := by
  cases base with
  | mk bp bn =>
      cases incoming with
      | mk ip ineg =>
          simp_all [joinGEvidence, effectiveGDecision]

theorem negative_support_breaks_positiveOnly
    (base incoming : GEvidence)
    (hneg : incoming.neg = true) :
    gPositiveOnly (gDecideView (joinGEvidence base incoming) .resolvedPos) = false := by
  cases base with
  | mk bp bn =>
      cases incoming with
      | mk ip ineg =>
          simp_all [joinGEvidence, effectiveGDecision, gDecideView, gPositiveOnly]

/-! Historical/live/reachable possibility. -/

def ReachableLive {H : Type u} {T : Type v}
    (R : H → H → Prop) (Live : H → T → Prop) (h : H) (t : T) : Prop :=
  ∃ h', R h h' ∧ Live h' t

theorem persistent_closure_blocks_reach
    {H : Type u} {T : Type v}
    {R : H → H → Prop} {Live Closed : H → T → Prop}
    {h : H} {t : T}
    (hpersist : ∀ ⦃x y : H⦄ ⦃tau : T⦄,
      R x y → Closed x tau → Closed y tau)
    (hexcl : ∀ ⦃x : H⦄ ⦃tau : T⦄, Closed x tau → ¬ Live x tau)
    (hclosed : Closed h t) :
    ¬ ReachableLive R Live h t := by
  rintro ⟨h', hreach, hlive⟩
  have hclosed' : Closed h' t := hpersist hreach hclosed
  exact (hexcl hclosed') hlive

/-! Observation kernels and static minimality. -/

def KernelRel {X : Type u} {K : Type v}
    (f : X → K) (x y : X) : Prop := f x = f y

def SufficientFor {X : Type u} {Q : Type v} {K : Type w}
    (repr : X → Q) (obs : X → K) : Prop :=
  ∀ ⦃x y : X⦄, repr x = repr y → obs x = obs y

theorem observation_kernel_is_coarsest
    {X : Type u} {Q : Type v} {K : Type w}
    {repr : X → Q} {obs : X → K}
    (hsuff : SufficientFor repr obs) :
    ∀ ⦃x y : X⦄, KernelRel repr x y → KernelRel obs x y := by
  intro x y hxy
  exact hsuff hxy

end CPOG.EpistemicPotentialism.Generic
