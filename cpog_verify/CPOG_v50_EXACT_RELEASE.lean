

namespace CPOG

universe u

abbrev Rel (W : Type u) := W -> W -> Prop

def Box (R : Rel W) (p : W -> Prop) (w : W) : Prop :=
  forall v, R w v -> p v

def Dia (R : Rel W) (p : W -> Prop) (w : W) : Prop :=
  exists v, R w v /\ p v

def Reflexive (R : Rel W) : Prop :=
  forall w, R w w

def Transitive (R : Rel W) : Prop :=
  forall {x y z}, R x y -> R y z -> R x z

def DirectedAt (R : Rel W) (w : W) : Prop :=
  forall {x y}, R w x -> R w y -> exists z, R x z /\ R y z

def Directed (R : Rel W) : Prop :=
  forall w, DirectedAt R w

variable {W : Type u}

theorem box_T_of_reflexive
    {R : Rel W} (hRefl : Reflexive R) (p : W -> Prop) (w : W) :
    Box R p w -> p w := by
  intro h
  exact h w (hRefl w)

theorem box_4_of_transitive
    {R : Rel W} (hTrans : Transitive R) (p : W -> Prop) (w : W) :
    Box R p w -> Box R (Box R p) w := by
  intro h v hwv u hvu
  exact h u (hTrans hwv hvu)

theorem dot2_of_directedAt
    {R : Rel W} {w : W} (hDir : DirectedAt R w) (p : W -> Prop) :
    Dia R (Box R p) w -> Box R (Dia R p) w := by
  intro hDia y hwy
  rcases hDia with ⟨x, hwx, hBox⟩
  rcases hDir hwx hwy with ⟨z, hxz, hyz⟩
  exact ⟨z, hyz, hBox z hxz⟩

theorem dot2_of_directed
    {R : Rel W} (hDir : Directed R) (p : W -> Prop) (w : W) :
    Dia R (Box R p) w -> Box R (Dia R p) w :=
  dot2_of_directedAt (hDir w) p


theorem directedAt_of_dot2_all
    {R : Rel W} {w : W}
    (hDot2 : forall p : W -> Prop,
      Dia R (Box R p) w -> Box R (Dia R p) w) :
    DirectedAt R w := by
  intro x y hwx hwy
  let p : W -> Prop := fun z => R x z
  have hBoxX : Box R p x := by
    intro z hxz
    exact hxz
  have hDiaRoot : Dia R (Box R p) w := ⟨x, hwx, hBoxX⟩
  have hAll : Box R (Dia R p) w := hDot2 p hDiaRoot
  have hDiaY : Dia R p y := hAll y hwy
  rcases hDiaY with ⟨z, hyz, hxz⟩
  exact ⟨z, hxz, hyz⟩

theorem directedAt_iff_dot2_all
    {R : Rel W} {w : W} :
    DirectedAt R w <->
      forall p : W -> Prop, Dia R (Box R p) w -> Box R (Dia R p) w := by
  constructor
  · intro hDir p
    exact dot2_of_directedAt hDir p
  · intro hDot2
    exact directedAt_of_dot2_all hDot2

theorem directed_iff_dot2_all
    {R : Rel W} :
    Directed R <->
      forall (w : W) (p : W -> Prop),
        Dia R (Box R p) w -> Box R (Dia R p) w := by
  constructor
  · intro hDir w p
    exact dot2_of_directedAt (hDir w) p
  · intro hDot2 w
    exact directedAt_of_dot2_all (hDot2 w)


theorem reflexive_of_T_all
    {R : Rel W}
    (hT : forall (p : W -> Prop) (w : W), Box R p w -> p w) :
    Reflexive R := by
  intro w
  let p : W -> Prop := fun v => R w v
  have hBox : Box R p w := by
    intro v hwv
    exact hwv
  exact hT p w hBox

theorem reflexive_iff_T_all
    {R : Rel W} :
    Reflexive R <->
      forall (p : W -> Prop) (w : W), Box R p w -> p w := by
  constructor
  · intro hRefl p w
    exact box_T_of_reflexive hRefl p w
  · exact reflexive_of_T_all


theorem transitive_of_4_all
    {R : Rel W}
    (h4 : forall (p : W -> Prop) (w : W),
      Box R p w -> Box R (Box R p) w) :
    Transitive R := by
  intro x y z hxy hyz
  let p : W -> Prop := fun v => R x v
  have hBoxX : Box R p x := by
    intro v hxv
    exact hxv
  have hBoxBox : Box R (Box R p) x := h4 p x hBoxX
  exact hBoxBox y hxy z hyz

theorem transitive_iff_4_all
    {R : Rel W} :
    Transitive R <->
      forall (p : W -> Prop) (w : W),
        Box R p w -> Box R (Box R p) w := by
  constructor
  · intro hTrans p w
    exact box_4_of_transitive (R := R) hTrans p w
  · exact transitive_of_4_all


theorem dot2_countervaluation_of_no_join
    {R : Rel W} {w x y : W}
    (hwx : R w x) (hwy : R w y)
    (hNoJoin : Not (exists z, R x z /\ R y z)) :
    let p : W -> Prop := fun z => R x z
    Dia R (Box R p) w /\ Not (Box R (Dia R p) w) := by
  let p : W -> Prop := fun z => R x z
  constructor
  · refine ⟨x, hwx, ?_⟩
    intro z hxz
    exact hxz
  · intro hBox
    have hDiaY : Dia R p y := hBox y hwy
    rcases hDiaY with ⟨z, hyz, hxz⟩
    exact hNoJoin ⟨z, hxz, hyz⟩

end CPOG


namespace CPOG

universe u v


structure HistToken (EventCode : Type u) (Payload : Type v) where
  origin : EventCode
  payload : Payload

variable {EventCode : Type u} {Payload : Type v}


theorem token_ne_of_origin_ne
    {t₁ t₂ : HistToken EventCode Payload}
    (h : t₁.origin ≠ t₂.origin) : t₁ ≠ t₂ := by
  intro hEq
  apply h
  exact congrArg HistToken.origin hEq


theorem token_eq_implies_origin_eq
    {t₁ t₂ : HistToken EventCode Payload}
    (h : t₁ = t₂) : t₁.origin = t₂.origin := by
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
          | inl hxy => exact Or.inl (Prefix.cons a hxy)
          | inr hyx => exact Or.inr (Prefix.cons a hyx)

end Prefix

variable {A : Type u}

def rawReach : Rel (List A) := Prefix

theorem raw_branching_no_common_successor
    {h x y : List A}
    (hhx : rawReach h x) (hhy : rawReach h y)
    (hxy : Not (rawReach x y)) (hyx : Not (rawReach y x)) :
    Not (exists z, rawReach x z /\ rawReach y z) := by
  intro hj
  rcases hj with ⟨z, hxz, hyz⟩
  cases Prefix.comparable_of_common_extension hxz hyz with
  | inl h => exact hxy h
  | inr h => exact hyx h

theorem raw_incomparable_branch_not_directedAt
    {h x y : List A}
    (hhx : rawReach h x) (hhy : rawReach h y)
    (hxy : Not (rawReach x y)) (hyx : Not (rawReach y x)) :
    Not (DirectedAt rawReach h) := by
  intro hdir
  rcases hdir hhx hhy with ⟨z, hxz, hyz⟩
  exact raw_branching_no_common_successor hhx hhy hxy hyx ⟨z, hxz, hyz⟩


theorem raw_branching_dot2_countervaluation
    {h x y : List A}
    (hhx : rawReach h x) (hhy : rawReach h y)
    (hxy : Not (rawReach x y)) (hyx : Not (rawReach y x)) :
    let p : List A -> Prop := fun z => rawReach x z
    Dia rawReach (Box rawReach p) h /\
      Not (Box rawReach (Dia rawReach p) h) := by
  apply dot2_countervaluation_of_no_join hhx hhy
  exact raw_branching_no_common_successor hhx hhy hxy hyx

end CPOG


namespace CPOG

universe u v

structure PossibilityModel (H : Type u) (Token : Type v) where
  reach : Rel H
  hist : H -> Token -> Prop
  live : H -> Token -> Prop
  live_hist : forall {h t}, live h t -> hist h t

variable {H : Type u} {Token : Type v}

def PossReach (M : PossibilityModel H Token) (h : H) (t : Token) : Prop :=
  exists h', M.reach h h' /\ M.live h' t

theorem live_implies_hist (M : PossibilityModel H Token) {h : H} {t : Token} :
    M.live h t -> M.hist h t :=
  M.live_hist

theorem live_implies_reach
    (M : PossibilityModel H Token)
    (hRefl : Reflexive M.reach) {h : H} {t : Token} :
    M.live h t -> PossReach M h t := by
  intro hlive
  exact ⟨h, hRefl h, hlive⟩

def Closed (M : PossibilityModel H Token) (h : H) (t : Token) : Prop :=
  Box M.reach (fun h' => Not (M.live h' t)) h

theorem closed_excludes_reach
    (M : PossibilityModel H Token) {h : H} {t : Token} :
    Closed M h t -> Not (PossReach M h t) := by
  intro hClosed hReach
  rcases hReach with ⟨h', hh', hLive⟩
  exact (hClosed h' hh') hLive

inductive ClosedWorld where
  | c

deriving DecidableEq

inductive OneToken where
  | t

deriving DecidableEq

def closedReach : Rel ClosedWorld := fun _ _ => True

def closedHist : ClosedWorld -> OneToken -> Prop := fun _ _ => True

def closedLive : ClosedWorld -> OneToken -> Prop := fun _ _ => False

def closedModel : PossibilityModel ClosedWorld OneToken where
  reach := closedReach
  hist := closedHist
  live := closedLive
  live_hist := by
    intro h t hl
    cases hl

theorem hist_not_reach_countermodel :
    closedModel.hist .c .t /\ Not (PossReach closedModel .c .t) := by
  constructor
  · trivial
  · intro hr
    rcases hr with ⟨w, _, hl⟩
    cases hl

inductive FutureWorld where
  | u
  | v

deriving DecidableEq

def futureReach : Rel FutureWorld
  | .u, .u => True
  | .u, .v => True
  | .v, .v => True
  | .v, .u => False

def futureHist : FutureWorld -> OneToken -> Prop
  | .u, _ => False
  | .v, _ => True

def futureLive : FutureWorld -> OneToken -> Prop
  | .u, _ => False
  | .v, _ => True

def futureModel : PossibilityModel FutureWorld OneToken where
  reach := futureReach
  hist := futureHist
  live := futureLive
  live_hist := by
    intro h t hl
    cases h with
    | u => cases hl
    | v => trivial

theorem reach_not_hist_countermodel :
    PossReach futureModel .u .t /\ Not (futureModel.hist .u .t) := by
  constructor
  · exact ⟨.v, by trivial, by trivial⟩
  · intro hh
    cases hh

end CPOG


namespace CPOG

universe u

abbrev GenState (A : Type u) := A -> Prop

def genReach : Rel (GenState A) := fun S T => forall a, S a -> T a

def mergeState (X Y : GenState A) : GenState A := fun a => X a \/ Y a

theorem genReach_refl : Reflexive (@genReach A) := by
  intro S a ha
  exact ha

theorem genReach_trans : Transitive (@genReach A) := by
  intro X Y Z hXY hYZ a ha
  exact hYZ a (hXY a ha)

theorem deferable_directed : Directed (@genReach A) := by
  intro S X Y hSX hSY
  refine ⟨mergeState X Y, ?_, ?_⟩
  · intro a ha
    exact Or.inl ha
  · intro a ha
    exact Or.inr ha

theorem deferable_dot2 (p : GenState A -> Prop) (S : GenState A) :
    Dia (@genReach A) (Box (@genReach A) p) S ->
    Box (@genReach A) (Dia (@genReach A) p) S :=
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

def PosOnly (w : SubWorld) : Prop := currentView w = .T

theorem decision_state_unchanged : currentDecision .h = currentDecision .g := rfl

theorem g_adds_defeating_evidence :
    currentEvidence .h = .T /\ currentEvidence .g = .B := by
  constructor <;> rfl

theorem derived_view_changes_under_G :
    currentView .h = .T /\ currentView .g = .B := by
  constructor <;> rfl

theorem content_boxD : Box dR PosOnly .h := by
  intro v hv
  cases v with
  | h => rfl
  | g => cases hv

theorem content_not_boxG : Not (Box gR PosOnly .h) := by
  intro hbox
  have hp : PosOnly .g := hbox .g (by trivial)
  change Evidence.B = Evidence.T at hp
  cases hp

theorem defeasible_content_subsumption_failure :
    Box dR PosOnly .h /\ Not (Box gR PosOnly .h) :=
  ⟨content_boxD, content_not_boxG⟩

end CPOG


namespace CPOG

universe u v w

inductive Formula (Atom : Type u) where
  | atom : Atom -> Formula Atom
  | top : Formula Atom
  | bot : Formula Atom
  | neg : Formula Atom -> Formula Atom
  | and : Formula Atom -> Formula Atom -> Formula Atom
  | or : Formula Atom -> Formula Atom -> Formula Atom
  | boxG : Formula Atom -> Formula Atom
  | boxD : Formula Atom -> Formula Atom
  | boxH : Formula Atom -> Formula Atom
  | diaG : Formula Atom -> Formula Atom
  | diaD : Formula Atom -> Formula Atom
  | diaH : Formula Atom -> Formula Atom

structure Model (W : Type u) (Atom : Type v) where
  val : W -> Atom -> Prop
  rG : Rel W
  rD : Rel W
  rH : Rel W

def Satisfies (M : Model W Atom) : W -> Formula Atom -> Prop
  | w, .atom a => M.val w a
  | _, .top => True
  | _, .bot => False
  | w, .neg phi => Not (Satisfies M w phi)
  | w, .and phi psi => Satisfies M w phi /\ Satisfies M w psi
  | w, .or phi psi => Satisfies M w phi \/ Satisfies M w psi
  | w, .boxG phi => forall v, M.rG w v -> Satisfies M v phi
  | w, .boxD phi => forall v, M.rD w v -> Satisfies M v phi
  | w, .boxH phi => forall v, M.rH w v -> Satisfies M v phi
  | w, .diaG phi => exists v, M.rG w v /\ Satisfies M v phi
  | w, .diaD phi => exists v, M.rD w v /\ Satisfies M v phi
  | w, .diaH phi => exists v, M.rH w v /\ Satisfies M v phi

structure IsBisimulation
    {W1 : Type u} {W2 : Type v} {Atom : Type w}
    (M1 : Model W1 Atom) (M2 : Model W2 Atom)
    (Z : W1 -> W2 -> Prop) : Prop where
  atom : forall {x y}, Z x y -> forall a, M1.val x a <-> M2.val y a
  forthG : forall {x y}, Z x y -> forall {x'}, M1.rG x x' ->
    exists y', M2.rG y y' /\ Z x' y'
  backG : forall {x y}, Z x y -> forall {y'}, M2.rG y y' ->
    exists x', M1.rG x x' /\ Z x' y'
  forthD : forall {x y}, Z x y -> forall {x'}, M1.rD x x' ->
    exists y', M2.rD y y' /\ Z x' y'
  backD : forall {x y}, Z x y -> forall {y'}, M2.rD y y' ->
    exists x', M1.rD x x' /\ Z x' y'
  forthH : forall {x y}, Z x y -> forall {x'}, M1.rH x x' ->
    exists y', M2.rH y y' /\ Z x' y'
  backH : forall {x y}, Z x y -> forall {y'}, M2.rH y y' ->
    exists x', M1.rH x x' /\ Z x' y'

variable {W1 : Type u} {W2 : Type v} {Atom : Type w}

theorem bisimulation_invariance
    {M1 : Model W1 Atom} {M2 : Model W2 Atom}
    {Z : W1 -> W2 -> Prop} (hZ : IsBisimulation M1 M2 Z) :
    forall (phi : Formula Atom) {x : W1} {y : W2},
      Z x y -> (Satisfies M1 x phi <-> Satisfies M2 y phi) := by
  intro phi
  induction phi with
  | atom a =>
      intro x y hxy
      exact hZ.atom hxy a
  | top =>
      intro x y hxy
      constructor <;> intro h <;> trivial
  | bot =>
      intro x y hxy
      constructor <;> intro h <;> cases h
  | neg phi ih =>
      intro x y hxy
      constructor
      · intro hn hy
        exact hn ((ih hxy).mpr hy)
      · intro hn hx
        exact hn ((ih hxy).mp hx)
  | and phi psi ihPhi ihPsi =>
      intro x y hxy
      constructor
      · intro h
        exact ⟨(ihPhi hxy).mp h.1, (ihPsi hxy).mp h.2⟩
      · intro h
        exact ⟨(ihPhi hxy).mpr h.1, (ihPsi hxy).mpr h.2⟩
  | or phi psi ihPhi ihPsi =>
      intro x y hxy
      constructor
      · intro h
        cases h with
        | inl hp => exact Or.inl ((ihPhi hxy).mp hp)
        | inr hp => exact Or.inr ((ihPsi hxy).mp hp)
      · intro h
        cases h with
        | inl hp => exact Or.inl ((ihPhi hxy).mpr hp)
        | inr hp => exact Or.inr ((ihPsi hxy).mpr hp)
  | boxG phi ih =>
      intro x y hxy
      constructor
      · intro hx y' hyy'
        rcases hZ.backG hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact (ih hx'y').mp (hx x' hxx')
      · intro hy x' hxx'
        rcases hZ.forthG hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact (ih hx'y').mpr (hy y' hyy')
  | boxD phi ih =>
      intro x y hxy
      constructor
      · intro hx y' hyy'
        rcases hZ.backD hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact (ih hx'y').mp (hx x' hxx')
      · intro hy x' hxx'
        rcases hZ.forthD hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact (ih hx'y').mpr (hy y' hyy')
  | boxH phi ih =>
      intro x y hxy
      constructor
      · intro hx y' hyy'
        rcases hZ.backH hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact (ih hx'y').mp (hx x' hxx')
      · intro hy x' hxx'
        rcases hZ.forthH hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact (ih hx'y').mpr (hy y' hyy')
  | diaG phi ih =>
      intro x y hxy
      constructor
      · intro hx
        rcases hx with ⟨x', hxx', hphi⟩
        rcases hZ.forthG hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact ⟨y', hyy', (ih hx'y').mp hphi⟩
      · intro hy
        rcases hy with ⟨y', hyy', hphi⟩
        rcases hZ.backG hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact ⟨x', hxx', (ih hx'y').mpr hphi⟩
  | diaD phi ih =>
      intro x y hxy
      constructor
      · intro hx
        rcases hx with ⟨x', hxx', hphi⟩
        rcases hZ.forthD hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact ⟨y', hyy', (ih hx'y').mp hphi⟩
      · intro hy
        rcases hy with ⟨y', hyy', hphi⟩
        rcases hZ.backD hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact ⟨x', hxx', (ih hx'y').mpr hphi⟩
  | diaH phi ih =>
      intro x y hxy
      constructor
      · intro hx
        rcases hx with ⟨x', hxx', hphi⟩
        rcases hZ.forthH hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact ⟨y', hyy', (ih hx'y').mp hphi⟩
      · intro hy
        rcases hy with ⟨y', hyy', hphi⟩
        rcases hZ.backH hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact ⟨x', hxx', (ih hx'y').mpr hphi⟩

end CPOG


namespace CPOG

universe u v w x

variable {I : Type u} {X : Type v} {Y : Type w}


def ObsEq (O : I -> X -> Y) (x y : X) : Prop :=
  forall i, O i x = O i y

theorem obsEq_refl (O : I -> X -> Y) : forall x, ObsEq O x x := by
  intro x i
  rfl

theorem obsEq_symm (O : I -> X -> Y) :
    forall {x y}, ObsEq O x y -> ObsEq O y x := by
  intro x y h i
  exact Eq.symm (h i)

theorem obsEq_trans (O : I -> X -> Y) :
    forall {x y z}, ObsEq O x y -> ObsEq O y z -> ObsEq O x z := by
  intro x y z hxy hyz i
  exact Eq.trans (hxy i) (hyz i)


theorem semantic_minimal_quotient
    (O : I -> X -> Y) (E : X -> X -> Prop)
    (hPres : forall {x y}, E x y -> forall i, O i x = O i y) :
    forall {x y}, E x y -> ObsEq O x y := by
  intro x y hE i
  exact hPres hE i

variable {W : Type u} {Q : Type v} {Atom : Type w}


structure DynamicEquiv (M : Model W Atom) (E : W -> W -> Prop) : Prop where
  refl : forall x, E x x
  symm : forall {x y}, E x y -> E y x
  trans : forall {x y z}, E x y -> E y z -> E x z
  bisim : IsBisimulation M M E


structure QuotientPresentation (W : Type u) (Q : Type v) (E : W -> W -> Prop) where
  classOf : W -> Q
  surj : forall q, exists w, classOf w = q
  class_eq_iff : forall {x y}, classOf x = classOf y <-> E x y

def quotientVal
    (M : Model W Atom) (P : QuotientPresentation W Q E)
    (q : Q) (a : Atom) : Prop :=
  exists x, P.classOf x = q /\ M.val x a

def quotientRel
    (P : QuotientPresentation W Q E) (R : Rel W) : Rel Q :=
  fun q r => exists x y,
    P.classOf x = q /\ P.classOf y = r /\ R x y

def quotientModel
    (M : Model W Atom) (P : QuotientPresentation W Q E) : Model Q Atom where
  val := quotientVal M P
  rG := quotientRel P M.rG
  rD := quotientRel P M.rD
  rH := quotientRel P M.rH

def ProjectionRel (P : QuotientPresentation W Q E) : W -> Q -> Prop :=
  fun x q => P.classOf x = q

private theorem projection_atom
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) (P : QuotientPresentation W Q E)
    {x : W} {q : Q} (hxq : P.classOf x = q) (a : Atom) :
    M.val x a <-> quotientVal M P q a := by
  constructor
  · intro hx
    exact ⟨x, hxq, hx⟩
  · intro hq
    rcases hq with ⟨y, hyq, hy⟩
    have hClasses : P.classOf x = P.classOf y := by
      exact Eq.trans hxq (Eq.symm hyq)
    have hxy : E x y := (P.class_eq_iff).mp hClasses
    exact (hE.bisim.atom hxy a).mpr hy

private theorem projection_forth
    {E : W -> W -> Prop}
    (P : QuotientPresentation W Q E)
    (R : Rel W) {x : W} {q : Q}
    (hxq : P.classOf x = q) {x' : W} (hxx' : R x x') :
    exists q', quotientRel P R q q' /\ P.classOf x' = q' := by
  refine ⟨P.classOf x', ?_, rfl⟩
  exact ⟨x, x', hxq, rfl, hxx'⟩

private theorem projection_back
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) (P : QuotientPresentation W Q E)
    (R : Rel W)
    (back : forall {a b}, E a b -> forall {b'}, R b b' ->
      exists a', R a a' /\ E a' b')
    {x : W} {q q' : Q} (hxq : P.classOf x = q)
    (hqq' : quotientRel P R q q') :
    exists x', R x x' /\ P.classOf x' = q' := by
  rcases hqq' with ⟨a, b, haq, hbq', hab⟩
  have hClass : P.classOf x = P.classOf a := Eq.trans hxq (Eq.symm haq)
  have hxa : E x a := (P.class_eq_iff).mp hClass
  rcases back hxa hab with ⟨x', hxx', hx'b⟩
  have hClassXB : P.classOf x' = P.classOf b := (P.class_eq_iff).mpr hx'b
  exact ⟨x', hxx', Eq.trans hClassXB hbq'⟩

theorem projection_is_bisimulation
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) (P : QuotientPresentation W Q E) :
    IsBisimulation M (quotientModel M P) (ProjectionRel P) := by
  constructor
  · intro x q hxq a
    exact projection_atom hE P hxq a
  · intro x q hxq x' hxx'
    exact projection_forth P M.rG hxq hxx'
  · intro x q hxq q' hqq'
    exact projection_back hE P M.rG hE.bisim.backG hxq hqq'
  · intro x q hxq x' hxx'
    exact projection_forth P M.rD hxq hxx'
  · intro x q hxq q' hqq'
    exact projection_back hE P M.rD hE.bisim.backD hxq hqq'
  · intro x q hxq x' hxx'
    exact projection_forth P M.rH hxq hxx'
  · intro x q hxq q' hqq'
    exact projection_back hE P M.rH hE.bisim.backH hxq hqq'

theorem quotient_invariance
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) (P : QuotientPresentation W Q E)
    (phi : Formula Atom) (x : W) :
    Satisfies M x phi <->
      Satisfies (quotientModel M P) (P.classOf x) phi := by
  exact bisimulation_invariance (projection_is_bisimulation hE P) phi rfl


theorem atom_difference_blocks_bisimulation
    {M : Model W Atom} {Z : W -> W -> Prop}
    (hZ : IsBisimulation M M Z) {x y : W} {a : Atom}
    (hx : M.val x a) (hy : Not (M.val y a)) :
    Not (Z x y) := by
  intro hxy
  exact hy ((hZ.atom hxy a).mp hx)

end CPOG


namespace CPOG

universe u

variable {Q : Type u}

inductive FCAtom where
  | pA

deriving DecidableEq

def fcId : Rel FCWorld := fun x y => x = y

def fcModel : Model FCWorld FCAtom where
  val := fun w _ => PA w
  rG := fcR
  rD := fcId
  rH := fcR

def fcAntecedent : Formula FCAtom :=
  .diaG (.boxG (.atom .pA))

def fcConsequent : Formula FCAtom :=
  .boxG (.diaG (.atom .pA))

theorem fc_model_antecedent :
    Satisfies fcModel .root fcAntecedent := by
  change Dia fcR (Box fcR PA) .root
  exact firstCommit_dot2_antecedent

theorem fc_model_consequent_fails :
    Not (Satisfies fcModel .root fcConsequent) := by
  change Not (Box fcR (Dia fcR PA) .root)
  exact firstCommit_dot2_consequent_fails

theorem firstCommit_A_B_not_bisimilar
    {Z : FCWorld -> FCWorld -> Prop}
    (hZ : IsBisimulation fcModel fcModel Z) :
    Not (Z .a .b) := by
  exact atom_difference_blocks_bisimulation hZ (a := FCAtom.pA)
    (by simp [fcModel, PA]) (by simp [fcModel, PA])

theorem firstCommit_classes_distinct
    {E : FCWorld -> FCWorld -> Prop}
    (hE : DynamicEquiv fcModel E)
    (P : QuotientPresentation FCWorld Q E) :
    Not (P.classOf .a = P.classOf .b) := by
  intro hEq
  have hAB : E .a .b := (P.class_eq_iff).mp hEq
  exact firstCommit_A_B_not_bisimilar hE.bisim hAB

theorem firstCommit_quotient_dot2_failure
    {E : FCWorld -> FCWorld -> Prop}
    (hE : DynamicEquiv fcModel E)
    (P : QuotientPresentation FCWorld Q E) :
    Satisfies (quotientModel fcModel P) (P.classOf .root) fcAntecedent /\
    Not (Satisfies (quotientModel fcModel P) (P.classOf .root) fcConsequent) := by
  constructor
  · exact (quotient_invariance hE P fcAntecedent .root).mp fc_model_antecedent
  · intro hConsQ
    have hCons : Satisfies fcModel .root fcConsequent :=
      (quotient_invariance hE P fcConsequent .root).mpr hConsQ
    exact fc_model_consequent_fails hCons

end CPOG

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
namespace CPOG

/-!
# Max formal core

This section formalizes the Max design conditions that were previously only
stated as an appendix program: free atomic extension, freshness/non-leaf,
finite processing closure for seal completion, prefix-admissible finite
realization, record round-trip, and modal-firewall conservativity.
-/

universe u v w

/-! ## Free atomic extension and initiality -/

structure AtomicExtension (Base : Type u) where
  Carrier : Type u
  base : Base -> Carrier
  fresh : Carrier

def AtomicHom {Base : Type u}
    (A B : AtomicExtension Base) : Type u :=
  { f : A.Carrier -> B.Carrier //
      (forall b, f (A.base b) = B.base b) /\ f A.fresh = B.fresh }

def StandardAtomicExtension (Base : Type u) : AtomicExtension Base where
  Carrier := Sum Base Unit
  base := Sum.inl
  fresh := Sum.inr ()

def standardAtomicHom {Base : Type u} (X : AtomicExtension Base) :
    AtomicHom (StandardAtomicExtension Base) X := by
  refine ⟨?_, ?_, ?_⟩
  · intro x
    cases x with
    | inl b => exact X.base b
    | inr _ => exact X.fresh
  · intro b
    rfl
  · rfl

theorem standardAtomicHom_unique
    {Base : Type u} (X : AtomicExtension Base)
    (f : AtomicHom (StandardAtomicExtension Base) X) :
    f = standardAtomicHom X := by
  apply Subtype.ext
  funext x
  cases x with
  | inl b =>
      exact f.2.1 b
  | inr z =>
      cases z
      exact f.2.2

theorem standard_atomic_initial
    {Base : Type u} (X : AtomicExtension Base) :
    exists f : AtomicHom (StandardAtomicExtension Base) X,
      forall g : AtomicHom (StandardAtomicExtension Base) X, g = f := by
  refine ⟨standardAtomicHom X, ?_⟩
  intro g
  exact standardAtomicHom_unique X g

theorem standard_atomic_freshness
    {Base : Type u} (b : Base) :
    (StandardAtomicExtension Base).fresh ≠
      (StandardAtomicExtension Base).base b := by
  intro h
  cases h

/-! ## Round-trip record conservativity -/

structure CoreRecord (Data : Type u) where
  data : Data

structure MaxRecord (Data : Type u) (Extra : Type v) where
  core : CoreRecord Data
  extra : Extra

def extendRecord {Data : Type u} {Extra : Type v}
    (r : CoreRecord Data) (x : Extra) : MaxRecord Data Extra :=
  ⟨r, x⟩

def forgetRecord {Data : Type u} {Extra : Type v}
    (r : MaxRecord Data Extra) : CoreRecord Data :=
  r.core

theorem forget_extend_record
    {Data : Type u} {Extra : Type v}
    (r : CoreRecord Data) (x : Extra) :
    forgetRecord (extendRecord r x) = r := by
  rfl

/-! ## Fresh providers and the Max non-leaf property -/

structure FreshProvider (Desc : Type u) where
  fresh : List Desc -> Desc
  fresh_not_mem : forall s, fresh s ∉ s

def FreshStep {Desc : Type u} (F : FreshProvider Desc) :
    Rel (List Desc) :=
  fun s t => t = s ++ [F.fresh s]

theorem max_non_leaf
    {Desc : Type u} (F : FreshProvider Desc) (s : List Desc) :
    exists t, FreshStep F s t /\ t ≠ s := by
  refine ⟨s ++ [F.fresh s], rfl, ?_⟩
  intro hEq
  have hLen := congrArg List.length hEq
  simp at hLen

theorem max_fresh_descriptor_not_already_present
    {Desc : Type u} (F : FreshProvider Desc) (s : List Desc) :
    F.fresh s ∉ s :=
  F.fresh_not_mem s

/-! ## Why finite seed is insufficient for seal termination -/

def SuccDescriptorStep : Rel Nat :=
  fun x y => y = x + 1

theorem succ_descriptor_reachable_from_zero :
    forall n : Nat, RTC SuccDescriptorStep 0 n := by
  intro n
  induction n with
  | zero =>
      exact RTC.refl 0
  | succ n ih =>
      exact RTC.tail ih (by simp [SuccDescriptorStep])

theorem finite_seed_does_not_imply_finite_processing_closure :
    forall k : Nat, exists d : Nat,
      RTC SuccDescriptorStep 0 d /\ k < d := by
  intro k
  exact ⟨k + 1, succ_descriptor_reachable_from_zero (k + 1),
    Nat.lt_succ_self k⟩

/-! ## Finite processing closure and seal completion -/

structure FiniteProcessingClosure (Desc : Type u) where
  count : Nat
  descriptor : Fin count -> Desc
  generates : Fin count -> Fin count -> Prop

def ProcessedAfter {Desc : Type u}
    (C : FiniteProcessingClosure Desc) (k : Nat) (i : Fin C.count) : Prop :=
  i.val < k

def SealComplete {Desc : Type u}
    (C : FiniteProcessingClosure Desc) : Prop :=
  forall i, ProcessedAfter C C.count i

theorem finite_processing_closure_seals
    {Desc : Type u} (C : FiniteProcessingClosure Desc) :
    SealComplete C := by
  intro i
  exact i.isLt

theorem generated_descriptors_stay_inside_closure
    {Desc : Type u} (C : FiniteProcessingClosure Desc)
    {i j : Fin C.count} (h : C.generates i j) :
    exists k : Fin C.count, k = j := by
  exact ⟨j, rfl⟩

/-! ## Prefix admissibility and finite realization -/

def PrefixAdmissible {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop) :
    List Desc -> List Desc -> Prop
  | _, [] => True
  | base, d :: ds =>
      admissible base d /\
      PrefixAdmissible admissible (base ++ [d]) ds

def MaxStep {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop) :
    Rel (List Desc) :=
  fun s t => exists d, admissible s d /\ t = s ++ [d]

theorem prefix_admissible_realizable
    {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop) :
    forall (base batch : List Desc),
      PrefixAdmissible admissible base batch ->
      RTC (MaxStep admissible) base (base ++ batch) := by
  intro base batch h
  induction batch generalizing base with
  | nil =>
      simpa using (RTC.refl base : RTC (MaxStep admissible) base base)
  | cons d ds ih =>
      rcases h with ⟨hAd, hRest⟩
      have hOne : RTC (MaxStep admissible) base (base ++ [d]) :=
        RTC.tail (RTC.refl base) ⟨d, hAd, rfl⟩
      have hTail :
          RTC (MaxStep admissible) (base ++ [d])
            ((base ++ [d]) ++ ds) :=
        ih (base := base ++ [d]) hRest
      have hAll :
          RTC (MaxStep admissible) base ((base ++ [d]) ++ ds) :=
        RTC.trans hOne hTail
      simpa [List.append_assoc] using hAll

def SameSupport {Desc : Type u} (xs ys : List Desc) : Prop :=
  forall d, d ∈ xs <-> d ∈ ys

def JointlyAdmissible {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop)
    (base batch : List Desc) : Prop :=
  exists order,
    SameSupport order batch /\
    PrefixAdmissible admissible base order

theorem finite_universal_realization
    {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop)
    (base batch : List Desc)
    (h : JointlyAdmissible admissible base batch) :
    exists order,
      SameSupport order batch /\
      RTC (MaxStep admissible) base (base ++ order) := by
  rcases h with ⟨order, hSupport, hPrefix⟩
  exact ⟨order, hSupport,
    prefix_admissible_realizable admissible base order hPrefix⟩

/-! ## Modal firewall -/

structure ModalFirewall
    {CoreWorld : Type u} {Atom : Type w}
    (C : Model CoreWorld Atom) (MaxWorld : Type v) where
  embed : CoreWorld -> MaxWorld
  injective : Function.Injective embed
  valM : MaxWorld -> Atom -> Prop
  rGM : Rel MaxWorld
  rDM : Rel MaxWorld
  rHM : Rel MaxWorld
  atom_preserve :
    forall x a, C.val x a <-> valM (embed x) a
  forthG :
    forall {x x'}, C.rG x x' -> rGM (embed x) (embed x')
  backG :
    forall {x y}, rGM (embed x) y ->
      exists x', C.rG x x' /\ embed x' = y
  forthD :
    forall {x x'}, C.rD x x' -> rDM (embed x) (embed x')
  backD :
    forall {x y}, rDM (embed x) y ->
      exists x', C.rD x x' /\ embed x' = y
  forthH :
    forall {x x'}, C.rH x x' -> rHM (embed x) (embed x')
  backH :
    forall {x y}, rHM (embed x) y ->
      exists x', C.rH x x' /\ embed x' = y

def ModalFirewall.maxModel
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v}
    (F : ModalFirewall C MaxWorld) :
    Model MaxWorld Atom where
  val := F.valM
  rG := F.rGM
  rD := F.rDM
  rH := F.rHM

def FirewallRel
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v}
    (F : ModalFirewall C MaxWorld) :
    CoreWorld -> MaxWorld -> Prop :=
  fun x y => F.embed x = y

theorem firewall_is_bisimulation
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v}
    (F : ModalFirewall C MaxWorld) :
    IsBisimulation C F.maxModel (FirewallRel F) := by
  constructor
  · intro x y hxy a
    subst y
    exact F.atom_preserve x a
  · intro x y hxy x' hxx'
    subst y
    exact ⟨F.embed x', F.forthG hxx', rfl⟩
  · intro x y hxy y' hyy'
    subst y
    rcases F.backG hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', hx'y'⟩
  · intro x y hxy x' hxx'
    subst y
    exact ⟨F.embed x', F.forthD hxx', rfl⟩
  · intro x y hxy y' hyy'
    subst y
    rcases F.backD hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', hx'y'⟩
  · intro x y hxy x' hxx'
    subst y
    exact ⟨F.embed x', F.forthH hxx', rfl⟩
  · intro x y hxy y' hyy'
    subst y
    rcases F.backH hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', hx'y'⟩

theorem modal_firewall_satisfaction
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v}
    (F : ModalFirewall C MaxWorld)
    (phi : Formula Atom) (x : CoreWorld) :
    Satisfies C x phi <->
      Satisfies F.maxModel (F.embed x) phi := by
  exact bisimulation_invariance (firewall_is_bisimulation F) phi rfl

theorem max_extension_core_conservative
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v}
    (F : ModalFirewall C MaxWorld) :
    forall (phi : Formula Atom) (x : CoreWorld),
      Satisfies C x phi <->
        Satisfies F.maxModel (F.embed x) phi := by
  intro phi x
  exact modal_firewall_satisfaction F phi x

structure SealedMaxExtension
    {CoreWorld : Type u} {Atom : Type w}
    (C : Model CoreWorld Atom) (MaxWorld : Type v) (Desc : Type u) where
  firewall : ModalFirewall C MaxWorld
  closure : FiniteProcessingClosure Desc

theorem sealed_max_completion_and_conservativity
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v} {Desc : Type u}
    (E : SealedMaxExtension C MaxWorld Desc) :
    SealComplete E.closure /\
    forall (phi : Formula Atom) (x : CoreWorld),
      Satisfies C x phi <->
        Satisfies E.firewall.maxModel (E.firewall.embed x) phi := by
  constructor
  · exact finite_processing_closure_seals E.closure
  · intro phi x
    exact modal_firewall_satisfaction E.firewall phi x

end CPOG
namespace CPOG

/-!
# Possibility-role adequacy

Lean cannot establish that one philosophical word is uniquely correct.
What can be formalized is a role profile that distinguishes a possibility
carrier from belief status: historical persistence, deliberative live status,
future reactivation, and non-doxasticity.
-/

universe u v

structure PossibilityRoleModel (H : Type u) (Token : Type v) where
  reach : Rel H
  committed : H -> Token -> Prop
  live : H -> Token -> Prop
  believed : H -> Token -> Prop
  reach_refl : Reflexive reach
  commit_persistent :
    forall {h h' t}, reach h h' -> committed h t -> committed h' t
  live_committed :
    forall {h t}, live h t -> committed h t

def RoleReach
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token) (h : H) (t : Token) : Prop :=
  exists h', M.reach h h' /\ M.live h' t

def NonDoxasticCarrier
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token) : Prop :=
  exists h t, M.committed h t /\ Not (M.believed h t)

def NonDoxasticLive
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token) : Prop :=
  exists h t, M.live h t /\ Not (M.believed h t)

def Reactivatable
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token) : Prop :=
  exists h h' t,
    M.reach h h' /\
    M.committed h t /\
    Not (M.live h t) /\
    M.live h' t

def PossibilityRoleAdequate
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token) : Prop :=
  NonDoxasticCarrier M /\ NonDoxasticLive M /\ Reactivatable M

theorem role_live_implies_reach
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    {h : H} {t : Token} :
    M.live h t -> RoleReach M h t := by
  intro hl
  exact ⟨h, M.reach_refl h, hl⟩

theorem role_live_implies_committed
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    {h : H} {t : Token} :
    M.live h t -> M.committed h t :=
  M.live_committed

theorem role_committed_persists
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    {h h' : H} {t : Token} :
    M.reach h h' -> M.committed h t -> M.committed h' t :=
  M.commit_persistent

theorem adequate_live_not_identical_to_belief
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (hAdeq : PossibilityRoleAdequate M) :
    M.live ≠ M.believed := by
  intro hEq
  rcases hAdeq.2.1 with ⟨h, t, hLive, hNotBel⟩
  have hPoint := congrFun (congrFun hEq h) t
  exact hNotBel (hPoint ▸ hLive)

theorem adequate_committed_not_identical_to_belief
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (hAdeq : PossibilityRoleAdequate M) :
    M.committed ≠ M.believed := by
  intro hEq
  rcases hAdeq.1 with ⟨h, t, hComm, hNotBel⟩
  have hPoint := congrFun (congrFun hEq h) t
  exact hNotBel (hPoint ▸ hComm)

theorem adequate_committed_not_identical_to_live
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (hAdeq : PossibilityRoleAdequate M) :
    M.committed ≠ M.live := by
  intro hEq
  rcases hAdeq.2.2 with ⟨h, h', t, hReach, hComm, hNotLive, hLiveLater⟩
  have hPoint := congrFun (congrFun hEq h) t
  exact hNotLive (hPoint ▸ hComm)

theorem adequate_statuses_are_pairwise_distinct
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (hAdeq : PossibilityRoleAdequate M) :
    M.live ≠ M.believed /\
    M.committed ≠ M.believed /\
    M.committed ≠ M.live := by
  exact ⟨adequate_live_not_identical_to_belief M hAdeq,
    adequate_committed_not_identical_to_belief M hAdeq,
    adequate_committed_not_identical_to_live M hAdeq⟩

/-! ## A concrete CPOG-compatible role witness -/

inductive RoleWorld where
  | dormant
  | active

deriving DecidableEq

inductive RoleToken where
  | t

deriving DecidableEq

def roleReachRel : Rel RoleWorld
  | .dormant, .dormant => True
  | .dormant, .active => True
  | .active, .active => True
  | .active, .dormant => False

def roleCommitted : RoleWorld -> RoleToken -> Prop :=
  fun _ _ => True

def roleLive : RoleWorld -> RoleToken -> Prop
  | .dormant, _ => False
  | .active, _ => True

def roleBelieved : RoleWorld -> RoleToken -> Prop :=
  fun _ _ => False

def cpogRoleModel : PossibilityRoleModel RoleWorld RoleToken where
  reach := roleReachRel
  committed := roleCommitted
  live := roleLive
  believed := roleBelieved
  reach_refl := by
    intro h
    cases h <;> trivial
  commit_persistent := by
    intro h h' t hr hc
    trivial
  live_committed := by
    intro h t hl
    trivial

theorem cpog_role_model_adequate :
    PossibilityRoleAdequate cpogRoleModel := by
  constructor
  · exact ⟨.dormant, .t, by trivial, by simp [cpogRoleModel, roleBelieved]⟩
  constructor
  · exact ⟨.active, .t, by trivial, by simp [cpogRoleModel, roleBelieved]⟩
  · exact ⟨.dormant, .active, .t,
      by trivial, by trivial, by simp [cpogRoleModel, roleLive], by trivial⟩

theorem cpog_role_statuses_distinct :
    cpogRoleModel.live ≠ cpogRoleModel.believed /\
    cpogRoleModel.committed ≠ cpogRoleModel.believed /\
    cpogRoleModel.committed ≠ cpogRoleModel.live :=
  adequate_statuses_are_pairwise_distinct cpogRoleModel cpog_role_model_adequate

inductive RoleEvent where
  | e

deriving DecidableEq

def roleHistory : HistorySystem RoleWorld RoleEvent Unit where
  stepG := roleReachRel
  stepD := fun x y => x = y
  committed := fun _ _ => True
  record := fun _ _ => ()
  g_commit_mono := by
    intro h h' hG e hc
    trivial
  d_commit_same := by
    intro h h' hD e
    subst h'
    rfl
  g_record_preserve := by
    intro h h' hG e hc
    rfl
  d_record_preserve := by
    intro h h' hD e hc
    rfl

def roleOrigin : RoleToken -> RoleEvent :=
  fun _ => .e

theorem cpog_role_committed_is_possComm
    (h : RoleWorld) (t : RoleToken) :
    cpogRoleModel.committed h t <->
      roleHistory.PossComm roleOrigin h t := by
  constructor <;> intro _ <;> trivial

theorem cpog_role_live_is_committed_history_carrier
    {h : RoleWorld} {t : RoleToken} :
    cpogRoleModel.live h t ->
      roleHistory.PossComm roleOrigin h t := by
  intro hLive
  have hComm : cpogRoleModel.committed h t :=
    cpogRoleModel.live_committed hLive
  exact (cpog_role_committed_is_possComm h t).mp hComm

/-! ## The metaphysical bridge is an extra premise, not a Core theorem -/

def MetPossible
    {H : Type u} {Token : Type v}
    (_M : PossibilityRoleModel H Token) :=
  H -> Token -> Prop

def BridgeToMetaphysical
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (met : MetPossible M) : Prop :=
  forall {h t}, M.live h t -> met h t

def roleMetFalse : MetPossible cpogRoleModel :=
  fun _ _ => False

theorem role_adequacy_does_not_force_metaphysical_bridge :
    PossibilityRoleAdequate cpogRoleModel /\
    Not (BridgeToMetaphysical cpogRoleModel roleMetFalse) := by
  constructor
  · exact cpog_role_model_adequate
  · intro hBridge
    have hLive : cpogRoleModel.live .active .t := by trivial
    exact hBridge hLive

theorem metaphysical_bridge_requires_extra_assumption
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (met : MetPossible M)
    (hBridge : BridgeToMetaphysical M met)
    {h : H} {t : Token} :
    M.live h t -> met h t :=
  hBridge

end CPOG
namespace CPOG
namespace SubmissionCore

/-!
# Reviewer-facing theorem core

This file adds no new philosophical assumptions and no new proof mechanism.
It exposes the small theorem set used by the v50 submission manuscript while
leaving the larger verified library available as supporting infrastructure.
-/

/-- SC1. Historical commitment is persistent along the combined history reachability. -/
theorem historicalPersistence
    {H : Type u} {Event : Type v} {Record : Type w}
    (S : HistorySystem H Event Record)
    {h h' : H} (hr : S.Reach h h') (e : Event) :
    S.committed h e -> S.committed h' e :=
  HistorySystem.historical_persistence S hr e

/-- SC2. Deferable finite-base generation validates .2. -/
theorem deferableDot2
    (n : Nat) (p : FiniteGenState n -> Prop) (S : FiniteGenState n) :
    Dia (@genReach (Fin n)) (Box (@genReach (Fin n)) p) S ->
    Box (@genReach (Fin n)) (Dia (@genReach (Fin n)) p) S :=
  finite_deferable_dot2 n p S

/--
SC3. In one history system and one bisimulation-safe quotient, raw order
non-convergence is erased while FirstCommit separation and the .2 failure remain.
-/
theorem semanticDivergenceContrast :
    (uRG .root .orderAB /\ uRG .root .orderBA /\
      Not (exists z, uRG .orderAB z /\ uRG .orderBA z)) /\
    (uPresentation.classOf .orderAB = uPresentation.classOf .orderBA) /\
    (uPresentation.classOf .commitA ≠ uPresentation.classOf .commitB) /\
    (Satisfies (quotientModel unifiedModel uPresentation)
        (uPresentation.classOf .root) unifiedAntecedent /\
      Not (Satisfies (quotientModel unifiedModel uPresentation)
        (uPresentation.classOf .root) unifiedConsequent)) :=
  same_system_same_abstraction_contrast

/-- SC4. Content-level Subsumption failure is exactly the defeasibility boundary. -/
theorem subsumptionFailureIffDefeasible (V : ViewFn) :
    CanonicalContentSubsumptionFailure V <-> ResolvedPosDefeasible V :=
  content_subsumption_failure_iff_defeasible V

/-- SC5. Content-level Subsumption is recovered exactly under the canonical stability condition. -/
theorem subsumptionRecoveryIffStable (V : ViewFn) :
    CanonicalContentSubsumptionHolds V <->
      (V .T .resolvedPos = .T -> V .B .resolvedPos = .T) :=
  content_subsumption_holds_iff_stable V

/-- SC6. G/D/H modal truth is invariant under the dynamic bisimulation interface. -/
theorem dynamicBisimulationInvariance
    {W1 : Type u} {W2 : Type v} {Atom : Type w}
    {M1 : Model W1 Atom} {M2 : Model W2 Atom}
    {Z : W1 -> W2 -> Prop}
    (hZ : IsBisimulation M1 M2 Z)
    (phi : Formula Atom) {x : W1} {y : W2} (hxy : Z x y) :
    Satisfies M1 x phi <-> Satisfies M2 y phi :=
  bisimulation_invariance hZ phi hxy

/-- SC7. A jointly admissible finite Max batch has an executable ordering. -/
theorem finiteMaxRealization
    {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop)
    (base batch : List Desc)
    (h : JointlyAdmissible admissible base batch) :
    exists order,
      SameSupport order batch /\
      RTC (MaxStep admissible) base (base ++ order) :=
  finite_universal_realization admissible base batch h

/-- SC8. A sealed Max extension both completes and conservatively preserves Core modal truth. -/
theorem maxSealAndConservativity
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v} {Desc : Type u}
    (E : SealedMaxExtension C MaxWorld Desc) :
    SealComplete E.closure /\
    forall (phi : Formula Atom) (x : CoreWorld),
      Satisfies C x phi <->
        Satisfies E.firewall.maxModel (E.firewall.embed x) phi :=
  sealed_max_completion_and_conservativity E

/-- SC9. Under the explicit role-adequacy conditions, committed/live/believed are pairwise distinct. -/
theorem possibilityRoleSeparation
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (hAdeq : PossibilityRoleAdequate M) :
    M.live ≠ M.believed /\
    M.committed ≠ M.believed /\
    M.committed ≠ M.live :=
  adequate_statuses_are_pairwise_distinct M hAdeq

/-- SC10. Possibility-role adequacy alone does not entail metaphysical possibility. -/
theorem epistemicRoleDoesNotForceMetaphysical :
    PossibilityRoleAdequate cpogRoleModel /\
    Not (BridgeToMetaphysical cpogRoleModel roleMetFalse) :=
  role_adequacy_does_not_force_metaphysical_bridge

end SubmissionCore
end CPOG
