namespace CPOG
namespace PaperClaims

/-!
# v57 extended paper-level crosswalk

These aliases complete the current manuscript-facing formal surface with the
older proof-complete components that remain substantively relevant: S4 frame
structure of history reachability, explicit historical/content Subsumption
boundaries, possibility-status separation witnesses, the canonical greatest
observation-respecting dynamic quotient, policy specialization, and FDE
dynamic-safety / finite-convergence results.
-/

/-- PC23. G, D and combined-history H reachability are reflexive and transitive. -/
theorem historyModalS4Frames
    {H : Type u} {Event : Type v} {Record : Type w}
    (S : HistorySystem H Event Record) :
    Reflexive S.GReach /\
    Transitive S.GReach /\
    Reflexive S.DReach /\
    Transitive S.DReach /\
    Reflexive S.Reach /\
    Transitive S.Reach := by
  exact ⟨HistorySystem.gReach_reflexive S,
    HistorySystem.gReach_transitive S,
    HistorySystem.dReach_reflexive S,
    HistorySystem.dReach_transitive S,
    HistorySystem.reach_reflexive S,
    HistorySystem.reach_transitive S⟩

/-- PC24. Historical-language Subsumption fails in the explicit history system. -/
theorem historicalSubsumptionFailure :
    Box subHistory.DReach notCommittedInSubHistory .h /\
    Not (Box subHistory.GReach notCommittedInSubHistory .h) :=
  historical_subsumption_failure_in_history_system

/-- PC25. The canonical content countermodel fails exactly for resolved-positive defeasibility. -/
theorem canonicalContentFailureIffDefeasible
    (V : ViewFn) :
    CanonicalContentSubsumptionFailure V <->
      ResolvedPosDefeasible V :=
  content_subsumption_failure_iff_defeasible V

/-- PC26. Every forward-invariant acceptance fragment has universal Subsumption. -/
theorem stableFragmentSubsumption
    {S : Type u} (G : StateGrowth S) (A : S -> Prop)
    (hStable : ForwardInvariantRegion G.rel A) :
    UniversalStateSubsumption G A :=
  (universal_state_subsumption_iff_forwardInvariant G A).mpr hStable

/-- PC27. Historical/committed status need not imply future reachability/live status. -/
theorem committedNotReachableWitness :
    closedModel.hist .c .t /\
    Not (PossReach closedModel .c .t) :=
  hist_not_reach_countermodel

/-- PC28. Future reachability/live possibility need not already be historically committed. -/
theorem reachableNotCommittedWitness :
    PossReach futureModel .u .t /\
    Not (futureModel.hist .u .t) :=
  reach_not_hist_countermodel

/--
PC29. The canonical observation-respecting bisimilarity quotient is coarsest
among all DynamicEquiv relations that preserve the selected observations.
-/
theorem coarsestObservationSafeDynamicQuotient
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    {M : Model W Atom} {O : I -> W -> Y}
    {E : W -> W -> Prop}
    (hE : DynamicEquiv M E)
    (hObs : forall {x y}, E x y -> ObsEq O x y) :
    forall {x y},
      E x y ->
      (observationBisimilarityPresentation M O).classOf x =
        (observationBisimilarityPresentation M O).classOf y :=
  observation_bisimilarity_quotient_is_coarsest_safe hE hObs

/-- PC30. The canonical observation-safe quotient preserves all G/D/H formulas. -/
theorem observationSafeDynamicQuotientTruth
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y)
    (phi : Formula Atom) (x : W) :
    Satisfies M x phi <->
      Satisfies
        (quotientModel M (observationBisimilarityPresentation M O))
        ((observationBisimilarityPresentation M O).classOf x)
        phi :=
  observation_bisimilarity_quotient_truth M O phi x

/-- PC31. Quotient equality in the canonical dynamic quotient preserves the selected observations. -/
theorem observationSafeDynamicQuotientRespectsObservation
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y) :
    forall {x y},
      (observationBisimilarityPresentation M O).classOf x =
        (observationBisimilarityPresentation M O).classOf y ->
      ObsEq O x y :=
  observation_bisimilarity_quotient_respects_observation M O

/-- PC32. Any relation preserving selected Boolean source policies refines policy equality. -/
theorem policyMinimality
    {I : Type u} {S : Type v}
    (P : I -> S -> Bool) (E : S -> S -> Prop)
    (hPres : forall {s t}, E s t -> forall i, P i s = P i t) :
    forall {s t}, E s t -> PolicyEq P s t :=
  policy_preserving_relation_refines_policyEq P E hPres

/-- PC33. Safety for all future Boolean policies forces source identity. -/
theorem openEndedPolicySafetyRequiresIdentity
    {S : Type u} [DecidableEq S]
    {B : Type v} (A : S -> B)
    (hA : forall {s t}, A s = A t ->
      forall P : S -> Bool, P s = P t) :
    Function.Injective A :=
  open_ended_policy_safety_requires_identity A hA

/--
PC34. FDE one-step dynamic safety is equivalent to stability under the
reflexive closure E* = Id ∪ E.
-/
theorem fdeDynamicSafetyIffReflexiveClosureStability
    {N : Type u} {B : Type v}
    (E : N -> N -> Prop) (block : N -> B) :
    DynamicSafety.FDEDynamicsStable E block <->
      DynamicSafety.ReflexiveClosureStable E block :=
  DynamicSafety.dynamicSafety_iff_reflexiveClosureStability E block

/--
PC35. On a finite nonempty carrier, synchronous two-bit FDE propagation has
already reached a fixed point by round |N|-1.
-/
theorem fdeFiniteConvergenceCardSubOne
    {N : Type u} [Fintype N] [Nonempty N]
    (E : N -> N -> Prop) (sigma : DynamicSafety.PropEvidence N) :
    Convergence.FDEIter E sigma (Fintype.card N - 1) =
      Convergence.FDEIter E sigma (Fintype.card N) :=
  FiniteConvergence.fdeIter_fixed_card_sub_one E sigma

/-- PC36. The same sharp |N|-1 fixed-point bound holds for one-bit support propagation. -/
theorem supportFiniteConvergenceCardSubOne
    {N : Type u} [Fintype N] [Nonempty N]
    (E : N -> N -> Prop) (S : N -> Prop) :
    Convergence.SupportIter E S (Fintype.card N - 1) =
      Convergence.SupportIter E S (Fintype.card N) :=
  FiniteConvergence.supportIter_fixed_card_sub_one E S


/--
PC37. The canonical coarsest observation-safe dynamic quotient still preserves
the explicit FirstCommit .2 counterexample.  This specializes the generic
"any DynamicEquiv" preservation theorem to the maximal observation-safe
quotient constructed in part29.
-/
theorem firstCommitFailureOnCoarsestObservationSafeQuotient
    {I : Type u} {Y : Type v}
    (O : I -> FCWorld -> Y) :
    let P :=
      observationBisimilarityPresentation
        (I := I) (Y := Y) fcModel O
    Satisfies
      (quotientModel fcModel P)
      (P.classOf .root)
      fcAntecedent /\
    Not (Satisfies
      (quotientModel fcModel P)
      (P.classOf .root)
      fcConsequent) := by
  dsimp only
  exact firstCommit_quotient_dot2_failure
    (observationBisimilarityDynamicEquiv
      (I := I) (Y := Y) fcModel O)
    (observationBisimilarityPresentation
      (I := I) (Y := Y) fcModel O)

end PaperClaims
end CPOG
