

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
