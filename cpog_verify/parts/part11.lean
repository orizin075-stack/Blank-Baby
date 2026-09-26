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
  · exact ⟨.dormant, .t, by trivial, by trivial⟩
  constructor
  · exact ⟨.active, .t, by trivial, by trivial⟩
  · exact ⟨.dormant, .active, .t,
      by trivial, by trivial, by trivial, by trivial⟩

theorem cpog_role_statuses_distinct :
    cpogRoleModel.live ≠ cpogRoleModel.believed /\
    cpogRoleModel.committed ≠ cpogRoleModel.believed /\
    cpogRoleModel.committed ≠ cpogRoleModel.live :=
  adequate_statuses_are_pairwise_distinct cpogRoleModel cpog_role_model_adequate

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
