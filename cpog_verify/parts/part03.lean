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
