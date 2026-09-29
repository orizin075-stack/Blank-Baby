namespace CPOG
namespace PaperClaims

/-!
# v57 paper-level formal theorem facade

This namespace exposes only the claims that the manuscript may call
"formally verified".  It is intentionally narrower than the full library.

The purpose is reviewer traceability:
paper claim -> one stable Lean name -> underlying kernel-checked theorem.
-/

/-- PC1. Modal T is exactly reflexivity of the accessibility relation. -/
theorem modalTFrameCorrespondence := reflexive_iff_T_all

/-- PC2. Modal 4 is exactly transitivity of the accessibility relation. -/
theorem modal4FrameCorrespondence := transitive_iff_4_all

/-- PC3. Local .2 validity for all predicates is exactly local directedness. -/
theorem localDot2FrameCorrespondence := directedAt_iff_dot2_all

/-- PC4. Historical commitment persists along combined history reachability. -/
theorem historicalPersistence := HistorySystem.historical_persistence

/-- PC5. Raw branching supplies an explicit .2 countervaluation. -/
theorem rawHistoryDot2Failure := raw_branching_dot2_countervaluation

/-- PC6. Deferable finite-base generation validates .2. -/
theorem deferableGenerationDot2Recovery := finite_deferable_dot2

/--
PC7. Generic irreversible divergence:
two disjoint forward-invariant reachable regions refute .2.
-/
theorem irreversibleDivergenceDot2Failure :=
  persistent_incompatible_branches_dot2_failure

/-- PC8. FirstCommit divergence is an exact instance of PC7. -/
theorem firstCommitAsInvariantRegionInstance :=
  firstCommit_dot2_failure_is_persistent_region_instance

/--
PC9. Same abstraction separates reversible order divergence from
irreversible FirstCommit divergence.
-/
theorem splitAbstractionModalContrast :=
  split_same_abstraction_modal_contrast

/--
PC10. Universal Subsumption is exactly forward invariance of the acceptance
region under the chosen admissible update relation.
-/
theorem universalSubsumptionIffForwardInvariant :=
  universal_state_subsumption_iff_forwardInvariant

/-- PC11. Subsumption failure is exactly non-invariance. -/
theorem universalSubsumptionFailureIffNonInvariant :=
  universal_state_subsumption_failure_iff_nonInvariant

/--
PC12. The four-valued Evidence/Decision formulation is an exact instance of
the generic state-growth theorem.
-/
theorem evidenceDynamicsIsGenericInstance :=
  v54_subsumption_iff_generic_universal_subsumption

/--
PC13. Pure awareness growth is judgement-silent when tracked evidence and
decision coordinates are unchanged.
-/
theorem awarenessSilence := pure_awareness_growth_is_judgment_silent

/--
PC14. Every acceptance predicate has two canonical stabilizations, and both
restore universal Subsumption.
-/
theorem canonicalStabilizationsRestoreSubsumption :=
  canonical_stabilizations_restore_subsumption

/-- PC15. ForwardClosure is the least forward-invariant superset. -/
theorem forwardClosureLeast := forwardClosure_least

/-- PC16. InvariantKernel is the greatest forward-invariant subset. -/
theorem invariantKernelGreatest := invariantKernel_greatest

/--
PC17. Historical origin difference is sufficient for token difference.
-/
theorem originDifferenceImpliesTokenDifference := token_ne_of_origin_ne

/--
PC18. Observation equivalence induces the semantic minimal quotient.
-/
theorem semanticMinimalQuotient := semantic_minimal_quotient

/--
PC19. The canonical projection into the observation quotient is a
bisimulation.
-/
theorem semanticProjectionIsBisimulation := projection_is_bisimulation

/--
PC20. Modal truth is invariant under the observation quotient.
-/
theorem semanticQuotientModalInvariance := quotient_invariance

/--
PC21. In one unified model, order-only difference is erased by abstraction
while FirstCommit difference is preserved and .2 failure survives.
-/
theorem originSensitiveDynamicContrast :=
  same_system_same_abstraction_contrast

/--
PC22. Under the explicit role-adequacy assumptions,
committed/live/believed are pairwise distinct statuses.
-/
theorem possibilityRoleSeparation := adequate_statuses_are_pairwise_distinct

/--
PC23. Possibility-role adequacy does not by itself force a bridge to
metaphysical possibility.
-/
theorem epistemicRoleDoesNotForceMetaphysical :=
  role_adequacy_does_not_force_metaphysical_bridge

/-- PC24. A jointly admissible finite Max batch has an executable ordering. -/
theorem finiteMaxRealization := finite_universal_realization

/--
PC25. The sealed Max extension preserves Core modal truth through the
firewall.
-/
theorem maxSealAndConservativity :=
  sealed_max_completion_and_conservativity

end PaperClaims
end CPOG
