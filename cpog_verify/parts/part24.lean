namespace CPOG.PaperClaims

/-!
Machine-checked crosswalk for the current generic formal package.
Any missing or incompatible declaration makes this part fail to elaborate.
-/

-- Frame correspondence and historical core.
#check CPOG.directedAt_iff_dot2_all
#check CPOG.HistorySystem.historical_persistence
#check CPOG.finite_deferable_dot2

-- Generic irreversible divergence and FirstCommit instance.
#check CPOG.persistent_incompatible_branches_dot2_failure
#check CPOG.persistent_incompatible_branches_not_directed
#check CPOG.firstCommit_dot2_failure_is_persistent_region_instance

-- Same-abstraction recovery/failure contrast and modal preservation.
#check CPOG.split_same_abstraction_modal_contrast
#check CPOG.bisimulation_invariance
#check CPOG.quotient_invariance
#check CPOG.semantic_minimal_quotient

-- Generic Subsumption / invariance representation theorem.
#check CPOG.universal_state_subsumption_iff_forwardInvariant
#check CPOG.universal_state_subsumption_failure_iff_nonInvariant

-- v54 four-valued evidence theory as a strict instance.
#check CPOG.v54_subsumption_iff_generic_universal_subsumption
#check CPOG.identityView_fails_info_universal_subsumption
#check CPOG.identityView_recovers_noNewNegative_subsumption

-- Awareness/evidence interface.
#check CPOG.unchanged_coordinates_preserve_PosOnly
#check CPOG.pure_awareness_growth_is_judgment_silent

-- Possibility-role and metaphysical bridge boundary.
#check CPOG.cpog_role_model_adequate
#check CPOG.role_adequacy_does_not_force_metaphysical_bridge

-- Max appendix / modal firewall.
#check CPOG.finite_universal_realization
#check CPOG.modal_firewall_satisfaction
#check CPOG.sealed_max_completion_and_conservativity

-- Canonical stabilization operators.
#check CPOG.forwardClosure_forwardInvariant
#check CPOG.forwardClosure_least
#check CPOG.invariantKernel_forwardInvariant
#check CPOG.invariantKernel_greatest
#check CPOG.forwardClosure_idempotent_pointwise
#check CPOG.invariantKernel_idempotent_pointwise
#check CPOG.canonical_stabilizations_restore_subsumption

-- Reviewer-facing SC1--SC10 surface.
#check CPOG.SubmissionCore.historicalPersistence
#check CPOG.SubmissionCore.deferableDot2
#check CPOG.SubmissionCore.persistentIncompatibleBranchesDot2Failure
#check CPOG.SubmissionCore.splitAbstractionModalContrast
#check CPOG.SubmissionCore.universalSubsumptionIffForwardInvariant
#check CPOG.SubmissionCore.universalSubsumptionFailureIffNonInvariant
#check CPOG.SubmissionCore.finiteMaxRealization
#check CPOG.SubmissionCore.maxSealAndConservativity
#check CPOG.SubmissionCore.possibilityRoleSeparation
#check CPOG.SubmissionCore.epistemicRoleDoesNotForceMetaphysical

end CPOG.PaperClaims
