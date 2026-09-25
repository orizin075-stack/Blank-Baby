import Std

namespace CPOG.EpistemicPotentialism.General

def BoxR {W : Type} (R : W -> W -> Prop) (phi : W -> Prop) (w : W) : Prop :=
  forall v, R w v -> phi v

def DiaR {W : Type} (R : W -> W -> Prop) (phi : W -> Prop) (w : W) : Prop :=
  exists v, R w v /\ phi v

def DotTwoAt {W : Type} (R : W -> W -> Prop) (w : W) : Prop :=
  forall phi : W -> Prop, DiaR R (BoxR R phi) w -> BoxR R (DiaR R phi) w

def ConfluentAt {W : Type} (R : W -> W -> Prop) (w : W) : Prop :=
  forall u v, R w u -> R w v -> exists z, R u z /\ R v z

theorem dotTwoAt_of_confluentAt {W : Type} {R : W -> W -> Prop} {w : W}
    (hconf : ConfluentAt R w) : DotTwoAt R w := by
  intro phi hDia u hwu
  rcases hDia with ⟨v, hwv, hboxv⟩
  rcases hconf v u hwv hwu with ⟨z, hvz, huz⟩
  exact ⟨z, huz, hboxv z hvz⟩

theorem not_dotTwoAt_of_divergence {W : Type} {R : W -> W -> Prop}
    {root a b : W}
    (hra : R root a)
    (hrb : R root b)
    (hdiv : Not (exists z, R a z /\ R b z)) :
    Not (DotTwoAt R root) := by
  intro hdot
  let phi : W -> Prop := fun z => R a z
  have hdia : DiaR R (BoxR R phi) root := by
    refine ⟨a, hra, ?_⟩
    intro z haz
    exact haz
  have hbox : BoxR R (DiaR R phi) root := hdot phi hdia
  have hdb : DiaR R phi b := hbox b hrb
  rcases hdb with ⟨z, hbz, haz⟩
  exact hdiv ⟨z, haz, hbz⟩

def Extends {A : Type} (h k : List A) : Prop :=
  exists tail, k = h ++ tail

theorem distinct_singletons_have_no_common_extension {A : Type} {a b : A}
    (hab : Not (a = b)) :
    Not (exists z : List A, Extends [a] z /\ Extends [b] z) := by
  rintro ⟨z, ⟨ta, hza⟩, ⟨tb, hzb⟩⟩
  have hcons : a :: ta = b :: tb := by
    simpa using hza.symm.trans hzb
  cases hcons
  exact hab rfl

theorem raw_prefix_dotTwo_fails {A : Type} {a b : A}
    (hab : Not (a = b)) :
    Not (DotTwoAt (Extends (A := A)) ([] : List A)) := by
  apply not_dotTwoAt_of_divergence
  · exact ⟨[a], by simp⟩
  · exact ⟨[b], by simp⟩
  · exact distinct_singletons_have_no_common_extension hab

def FirstCommit {A : Type} (h : List A) : Option A := h.head?

theorem firstCommit_persistent {A : Type} {h k : List A} {c : A}
    (hext : Extends h k)
    (hc : FirstCommit h = some c) :
    FirstCommit k = some c := by
  rcases hext with ⟨tail, rfl⟩
  cases h with
  | nil =>
      simp [FirstCommit] at hc
  | cons x xs =>
      simpa [FirstCommit] using hc

def QuotRel {W Q : Type} (R : W -> W -> Prop) (q : W -> Q) : Q -> Q -> Prop :=
  fun u v => exists x y, q x = u /\ q y = v /\ R x y

theorem quotRel_of_step {W Q : Type} {R : W -> W -> Prop} {q : W -> Q}
    {x y : W} (hxy : R x y) : QuotRel R q (q x) (q y) := by
  exact ⟨x, y, rfl, rfl, hxy⟩

theorem firstCommit_divergence_survives_abstraction
    {W Q C : Type}
    {R : W -> W -> Prop}
    {q : W -> Q}
    {tag : W -> Option C}
    {a b : W} {ca cb : C}
    (hobs : forall {x y}, q x = q y -> tag x = tag y)
    (hpersist : forall {x y c}, R x y -> tag x = some c -> tag y = some c)
    (hta : tag a = some ca)
    (htb : tag b = some cb)
    (hne : Not (ca = cb)) :
    Not (exists z, QuotRel R q (q a) z /\ QuotRel R q (q b) z) := by
  rintro ⟨z, ha, hb⟩
  rcases ha with ⟨xa, ya, hqxa, hqya, hRya⟩
  rcases hb with ⟨xb, yb, hqxb, hqyb, hRyb⟩
  have htxa : tag xa = some ca := (hobs hqxa).trans hta
  have htxb : tag xb = some cb := (hobs hqxb).trans htb
  have htya : tag ya = some ca := hpersist hRya htxa
  have htyb : tag yb = some cb := hpersist hRyb htxb
  have hqy : q ya = q yb := hqya.trans hqyb.symm
  have htagy : tag ya = tag yb := hobs hqy
  have hsome : some ca = some cb := htya.symm.trans (htagy.trans htyb)
  have hcc : ca = cb := by
    cases hsome
    rfl
  exact hne hcc

theorem firstCommit_abstraction_dotTwo_fails
    {W Q C : Type}
    {R : W -> W -> Prop}
    {q : W -> Q}
    {tag : W -> Option C}
    {root a b : W} {ca cb : C}
    (hra : R root a)
    (hrb : R root b)
    (hobs : forall {x y}, q x = q y -> tag x = tag y)
    (hpersist : forall {x y c}, R x y -> tag x = some c -> tag y = some c)
    (hta : tag a = some ca)
    (htb : tag b = some cb)
    (hne : Not (ca = cb)) :
    Not (DotTwoAt (QuotRel R q) (q root)) := by
  apply not_dotTwoAt_of_divergence
  · exact quotRel_of_step hra
  · exact quotRel_of_step hrb
  · exact firstCommit_divergence_survives_abstraction hobs hpersist hta htb hne

def SubsumptionAt {W : Type}
    (RD RG : W -> W -> Prop) (w : W) : Prop :=
  forall phi : W -> Prop, BoxR RD phi w -> BoxR RG phi w

theorem not_subsumptionAt_of_counterexample
    {W : Type} {RD RG : W -> W -> Prop} {w g : W} {phi : W -> Prop}
    (hD : BoxR RD phi w)
    (hG : RG w g)
    (hnot : Not (phi g)) :
    Not (SubsumptionAt RD RG w) := by
  intro hsub
  have hboxG : BoxR RG phi w := hsub phi hD
  exact hnot (hboxG g hG)

end CPOG.EpistemicPotentialism.General
