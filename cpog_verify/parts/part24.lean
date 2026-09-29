namespace CPOG
namespace PaperClaims

/-!
# v57 paper-level formal theorem contract

Only claims listed here may be described by the manuscript as belonging to the
verified formal core.  Each declaration has an explicit public type rather than
a type-inferred alias.  This deliberately duplicates the paper-facing contract,
so CI fails if an underlying theorem changes incompatibly.
-/

universe u v w x

/-- PC1. Modal T is exactly frame reflexivity. -/
theorem modalTFrameCorrespondence
    {W : Type u} {R : Rel W} :
    Reflexive R <->
      forall (p : W -> Prop) (w : W), Box R p w -> p w :=
  reflexive_iff_T_all

/-- PC2. Modal 4 is exactly frame transitivity. -/
theorem modal4FrameCorrespondence
    {W : Type u} {R : Rel W} :
    Transitive R <->
      forall (p : W -> Prop) (w : W),
        Box R p w -> Box R (Box R p) w :=
  transitive_iff_4_all

/-- PC3. Local .2 for every valuation is exactly local directedness. -/
theorem localDot2FrameCorrespondence
    {W : Type u} {R : Rel W} {w0 : W} :
    DirectedAt R w0 <->
      forall p : W -> Prop,
        Dia R (Box R p) w0 -> Box R (Dia R p) w0 :=
  directedAt_iff_dot2_all

/-- PC4. Historical commitment persists along combined history reachability. -/
theorem historicalPersistence
    {H : Type u} {Event : Type v} {Record : Type w}
    (S : HistorySystem H Event Record)
    {h h' : H} (hr : S.Reach h h') (e : Event) :
    S.committed h e -> S.committed h' e :=
  HistorySystem.historical_persistence S hr e

/-- PC5. Raw prefix divergence yields a concrete .2 countervaluation. -/
theorem rawHistoryDot2Failure
    {A : Type u} {h x y : List A}
    (hhx : rawReach h x) (hhy : rawReach h y)
    (hxy : Not (rawReach x y)) (hyx : Not (rawReach y x)) :
    let p : List A -> Prop := fun z => rawReach x z
    Dia rawReach (Box rawReach p) h /\
      Not (Box rawReach (Dia rawReach p) h) :=
  raw_branching_dot2_countervaluation hhx hhy hxy hyx

/-- PC6. Deferable finite-base generation validates .2. -/
theorem deferableGenerationDot2Recovery
    (n : Nat) (p : FiniteGenState n -> Prop) (S : FiniteGenState n) :
    Dia (@genReach (Fin n)) (Box (@genReach (Fin n)) p) S ->
    Box (@genReach (Fin n)) (Dia (@genReach (Fin n)) p) S :=
  finite_deferable_dot2 n p S

/-- PC7. Two disjoint reachable invariant regions force irreversible .2 failure. -/
theorem irreversibleDivergenceDot2Failure
    {W : Type u}
    (R : Rel W) (P Q : W -> Prop)
    {r a b : W}
    (hP : ForwardInvariantRegion R P)
    (hQ : ForwardInvariantRegion R Q)
    (hDisjoint : MutuallyExclusiveRegions P Q)
    (hra : R r a) (hrb : R r b)
    (ha : P a) (hb : Q b) :
    Dia R (Box R P) r /\
    Not (Box R (Dia R P) r) :=
  persistent_incompatible_branches_dot2_failure
    R P Q hP hQ hDisjoint hra hrb ha hb

/-- PC8. FirstCommit is an exact instance of invariant-region divergence. -/
theorem firstCommitAsInvariantRegionInstance
    {W : Type u} {Choice : Type v}
    (R : Rel W) (F : W -> Option Choice)
    {r a b : W} {A B : Choice}
    (hPersist : FirstCommitPersistent R F)
    (hAB : A ≠ B)
    (hra : R r a) (hrb : R r b)
    (ha : F a = some A) (hb : F b = some B) :
    Dia R (Box R (FirstCommitPA F A)) r /\
    Not (Box R (Dia R (FirstCommitPA F A)) r) :=
  firstCommit_dot2_failure_is_persistent_region_instance
    R F hPersist hAB hra hrb ha hb

/-- PC9. One abstraction erases reversible order difference but preserves irreversible divergence. -/
theorem splitAbstractionModalContrast :
    Not (DirectedAt splitRG .ri) /\
    DirectedAt
      (quotientModel splitModel splitPresentation).rG
      (splitPresentation.classOf .ri) /\
    (forall p : SplitClass -> Prop,
      Dia (quotientModel splitModel splitPresentation).rG
        (Box (quotientModel splitModel splitPresentation).rG p)
        (splitPresentation.classOf .ri) ->
      Box (quotientModel splitModel splitPresentation).rG
        (Dia (quotientModel splitModel splitPresentation).rG p)
        (splitPresentation.classOf .ri)) /\
    (Satisfies (quotientModel splitModel splitPresentation)
        (splitPresentation.classOf .rf) splitAntecedent /\
      Not (Satisfies (quotientModel splitModel splitPresentation)
        (splitPresentation.classOf .rf) splitConsequent)) :=
  split_same_abstraction_modal_contrast

/-- PC10. Universal Subsumption is exactly forward invariance. -/
theorem universalSubsumptionIffForwardInvariant
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      ForwardInvariantRegion G.rel A :=
  universal_state_subsumption_iff_forwardInvariant G A

/-- PC11. Universal Subsumption fails exactly at non-invariant acceptance regions. -/
theorem universalSubsumptionFailureIffNonInvariant
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    Not (UniversalStateSubsumption G A) <->
      Not (ForwardInvariantRegion G.rel A) :=
  universal_state_subsumption_failure_iff_nonInvariant G A

/-- PC12. The four-valued Evidence/Decision model is an exact generic-state instance. -/
theorem evidenceDynamicsIsGenericInstance
    (P : EvidencePreorder) (V : ViewFn) :
    UniversalContentSubsumptionBy P V <->
      UniversalStateSubsumption
        (evidenceDecisionGrowth P) (acceptByView V) :=
  v54_subsumption_iff_generic_universal_subsumption P V

/-- PC13. Awareness-only growth is judgement-silent when tracked coordinates do not change. -/
theorem awarenessSilence
    {W : Type u}
    (V : ViewFn) (S : EvidenceDynamics W)
    {x y : W}
    (hG : S.gR x y)
    (hE : S.evidence x = S.evidence y)
    (hD : S.decision x = S.decision y) :
    S.PosOnly V x <-> S.PosOnly V y :=
  pure_awareness_growth_is_judgment_silent V S hG hE hD

/-- PC14. Both canonical invariant repairs restore universal Subsumption. -/
theorem canonicalStabilizationsRestoreSubsumption
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G (ForwardClosure G.rel A) /\
    UniversalStateSubsumption G (InvariantKernel G.rel A) :=
  canonical_stabilizations_restore_subsumption G A

/-- PC15. ForwardClosure is the least invariant superset. -/
theorem forwardClosureLeast
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q)
    (hPQ : PredSubset P Q) :
    PredSubset (ForwardClosure R P) Q :=
  forwardClosure_least R P Q hQInv hPQ

/-- PC16. InvariantKernel is the greatest invariant subset. -/
theorem invariantKernelGreatest
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q)
    (hQP : PredSubset Q P) :
    PredSubset Q (InvariantKernel R P) :=
  invariantKernel_greatest R P Q hQInv hQP

/-- PC17. Different origins force distinct historical tokens. -/
theorem originDifferenceImpliesTokenDifference
    {EventCode : Type u} {Payload : Type v}
    {t1 t2 : HistToken EventCode Payload}
    (h : t1.origin ≠ t2.origin) :
    t1 ≠ t2 :=
  token_ne_of_origin_ne h

/-- PC18. Every observation-preserving equivalence refines observation equivalence. -/
theorem semanticMinimalQuotient
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) (E : X -> X -> Prop)
    (hPres : forall {a b}, E a b -> forall i, O i a = O i b) :
    forall {a b}, E a b -> ObsEq O a b :=
  semantic_minimal_quotient O E hPres

/-- PC19. The canonical quotient projection is a bisimulation. -/
theorem semanticProjectionIsBisimulation
    {W : Type u} {Q : Type v} {Atom : Type w}
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) (P : QuotientPresentation W Q E) :
    IsBisimulation M (quotientModel M P) (ProjectionRel P) :=
  projection_is_bisimulation hE P

/-- PC20. Modal truth is invariant under the dynamic observation quotient. -/
theorem semanticQuotientModalInvariance
    {W : Type u} {Q : Type v} {Atom : Type w}
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) (P : QuotientPresentation W Q E)
    (phi : Formula Atom) (x0 : W) :
    Satisfies M x0 phi <->
      Satisfies (quotientModel M P) (P.classOf x0) phi :=
  quotient_invariance hE P phi x0

/-- PC21. Origin-sensitive irreversible difference survives the same abstraction that erases order-only difference. -/
theorem originSensitiveDynamicContrast :
    (uRG .root .orderAB /\ uRG .root .orderBA /\
      Not (exists z, uRG .orderAB z /\ uRG .orderBA z)) /\
    (uPresentation.classOf .orderAB = uPresentation.classOf .orderBA) /\
    (uPresentation.classOf .commitA ≠ uPresentation.classOf .commitB) /\
    (Satisfies (quotientModel unifiedModel uPresentation)
        (uPresentation.classOf .root) unifiedAntecedent /\
      Not (Satisfies (quotientModel unifiedModel uPresentation)
        (uPresentation.classOf .root) unifiedConsequent)) :=
  same_system_same_abstraction_contrast

/-- PC22. Under role adequacy, committed/live/believed remain pairwise distinct. -/
theorem possibilityRoleSeparation
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (hAdeq : PossibilityRoleAdequate M) :
    M.live ≠ M.believed /\
    M.committed ≠ M.believed /\
    M.committed ≠ M.live :=
  adequate_statuses_are_pairwise_distinct M hAdeq

/-- PC23. Epistemic possibility-role adequacy does not entail metaphysical possibility. -/
theorem epistemicRoleDoesNotForceMetaphysical :
    PossibilityRoleAdequate cpogRoleModel /\
    Not (BridgeToMetaphysical cpogRoleModel roleMetFalse) :=
  role_adequacy_does_not_force_metaphysical_bridge

/-- PC24. Every jointly admissible finite Max batch has an executable ordering. -/
theorem finiteMaxRealization
    {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop)
    (base batch : List Desc)
    (h : JointlyAdmissible admissible base batch) :
    exists order,
      SameSupport order batch /\
      RTC (MaxStep admissible) base (base ++ order) :=
  finite_universal_realization admissible base batch h

/-- PC25. A sealed Max extension both seals and conservatively preserves Core modal truth. -/
theorem maxSealAndConservativity
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v} {Desc : Type u}
    (E : SealedMaxExtension C MaxWorld Desc) :
    SealComplete E.closure /\
    forall (phi : Formula Atom) (x0 : CoreWorld),
      Satisfies C x0 phi <->
        Satisfies E.firewall.maxModel (E.firewall.embed x0) phi :=
  sealed_max_completion_and_conservativity E

end PaperClaims
end CPOG
