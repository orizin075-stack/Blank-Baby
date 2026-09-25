  exact congrArg HistToken.origin h

end CPOG


namespace CPOG

universe u v w x

inductive RTC {W : Type u} (R : Rel W) : W -> W -> Prop where
  | refl (w : W) : RTC R w w
  | tail {x y z : W} : RTC R x y -> R y z -> RTC R x z

namespace RTC

variable {W : Type u}

theorem preserve
    {R : Rel W} {P : W -> Prop}
    (hStep : forall {x y}, R x y -> P x -> P y)
    {x y : W} (hxy : RTC R x y) : P x -> P y := by
  induction hxy with
  | refl =>
      intro hx
      exact hx
  | tail hPath hLast ih =>
      intro hx
      exact hStep hLast (ih hx)

theorem trans
    {R : Rel W} {x y z : W} (hxy : RTC R x y) (hyz : RTC R y z) :
    RTC R x z := by
  induction hyz with
  | refl => exact hxy
  | tail hPath hLast ih => exact RTC.tail ih hLast

theorem reflexive (R : Rel W) : Reflexive (RTC R) := by
  intro x
  exact RTC.refl x

theorem transitive (R : Rel W) : Transitive (RTC R) := by
  intro x y z hxy hyz
  exact RTC.trans hxy hyz

end RTC

structure HistorySystem (H : Type u) (Event : Type v) (Record : Type w) where
  stepG : Rel H
  stepD : Rel H
  committed : H -> Event -> Prop
  record : H -> Event -> Record
  g_commit_mono : forall {h h'}, stepG h h' -> forall e, committed h e -> committed h' e
  d_commit_same : forall {h h'}, stepD h h' -> forall e, committed h e <-> committed h' e
  g_record_preserve : forall {h h'}, stepG h h' -> forall e, committed h e -> record h' e = record h e
  d_record_preserve : forall {h h'}, stepD h h' -> forall e, committed h e -> record h' e = record h e

namespace HistorySystem

variable {H : Type u} {Event : Type v} {Record : Type w} {Token : Type x}
variable (S : HistorySystem H Event Record)

def Step : Rel H := fun h h' => S.stepG h h' \/ S.stepD h h'

def GReach : Rel H := RTC S.stepG

def DReach : Rel H := RTC S.stepD

def Reach : Rel H := RTC S.Step

theorem gReach_reflexive : Reflexive S.GReach := RTC.reflexive S.stepG

theorem gReach_transitive : Transitive S.GReach := RTC.transitive S.stepG

theorem dReach_reflexive : Reflexive S.DReach := RTC.reflexive S.stepD

theorem dReach_transitive : Transitive S.DReach := RTC.transitive S.stepD

theorem reach_reflexive : Reflexive S.Reach := RTC.reflexive S.Step

theorem reach_transitive : Transitive S.Reach := RTC.transitive S.Step

theorem d_validates_T (p : H -> Prop) (h : H) :
    Box S.DReach p h -> p h :=
  box_T_of_reflexive (dReach_reflexive S) p h

theorem d_validates_4 (p : H -> Prop) (h : H) :
    Box S.DReach p h -> Box S.DReach (Box S.DReach p) h :=
  box_4_of_transitive (R := S.DReach) (dReach_transitive S) p h

theorem step_commit_mono {h h' : H} (hs : S.Step h h') :
    forall e, S.committed h e -> S.committed h' e := by
  intro e he
  cases hs with
  | inl hg => exact S.g_commit_mono hg e he
  | inr hd => exact (S.d_commit_same hd e).mp he

theorem historical_persistence {h h' : H} (hr : S.Reach h h') :
    forall e, S.committed h e -> S.committed h' e := by
  intro e he
  exact RTC.preserve
    (P := fun k => S.committed k e)
    (fun hs hc => step_commit_mono S hs e hc)
    hr he

theorem step_record_preserve {h h' : H} (hs : S.Step h h') :
    forall e, S.committed h e -> S.record h' e = S.record h e := by
  intro e he
  cases hs with
  | inl hg => exact S.g_record_preserve hg e he
  | inr hd => exact S.d_record_preserve hd e he

theorem record_persistence {h h' : H} (hr : S.Reach h h') :
    forall e, S.committed h e -> S.record h' e = S.record h e := by
  intro e he
  have hp : S.committed h' e /\ S.record h' e = S.record h e :=
    RTC.preserve
      (P := fun k => S.committed k e /\ S.record k e = S.record h e)
      (fun {x y} hs hx => by
        constructor
        · exact step_commit_mono S hs e hx.1
        · calc
            S.record y e = S.record x e := step_record_preserve S hs e hx.1
            _ = S.record h e := hx.2)
      hr ⟨he, rfl⟩
  exact hp.2

def PossHist (origin : Token -> Event) (h : H) (t : Token) : Prop :=
  S.committed h (origin t)

theorem possHist_persistent
    (origin : Token -> Event) {h h' : H} (hr : S.Reach h h')
    {t : Token} :
    S.PossHist origin h t -> S.PossHist origin h' t := by
  intro ht
  exact historical_persistence S hr (origin t) ht

end HistorySystem

end CPOG


namespace CPOG

universe u


inductive Prefix {A : Type u} : List A -> List A -> Prop where
  | nil (ys : List A) : Prefix [] ys
  | cons (a : A) {xs ys : List A} : Prefix xs ys -> Prefix (a :: xs) (a :: ys)

namespace Prefix

variable {A : Type u}

theorem refl : forall xs : List A, Prefix xs xs := by
  intro xs
  induction xs with
  | nil => exact Prefix.nil []
  | cons a xs ih => exact Prefix.cons a ih

theorem trans : forall {xs ys zs : List A}, Prefix xs ys -> Prefix ys zs -> Prefix xs zs := by
  intro xs ys zs hxy hyz
  induction hxy generalizing zs with
  | nil ys => exact Prefix.nil zs
  | cons a hxy ih =>
      cases hyz with
      | cons _ hyzTail =>
          exact Prefix.cons a (ih hyzTail)

theorem comparable_of_common_extension :
    forall {xs ys zs : List A}, Prefix xs zs -> Prefix ys zs ->
      Prefix xs ys \/ Prefix ys xs := by
  intro xs ys zs hx hy
  induction hx generalizing ys with
  | nil zs =>
      exact Or.inl (Prefix.nil ys)
  | cons a hx ih =>
      cases hy with
      | nil =>
          exact Or.inr (Prefix.nil _)
      | cons _ hyTail =>
          cases ih hyTail with
