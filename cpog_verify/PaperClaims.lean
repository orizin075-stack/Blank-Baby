import CPOG

/-!
# CPOG.PaperClaims

Machine-checked crosswalk from the current paper-level formal claims to the
kernel declarations that establish them. If a declaration disappears, is
renamed incompatibly, or stops elaborating, this module fails to build.

The crosswalk intentionally includes both the ten reviewer-facing SC claims
and the supporting formal results used by the paper's prose sections.
-/

namespace CPOG.PaperClaims

-- Core history / modal frame facts.
#check CPOG.HistorySystem.historical_persistence
#check CPOG.HistorySystem.gReach_reflexive
#check CPOG.HistorySystem.gReach_transitive
#check CPOG.HistorySystem.dReach_reflexive
#check CPOG.HistorySystem.dReach_transitive
#check CPOG.reflexive_iff_T_all
#check CPOG.transitive_iff_4_all
#check CPOG.directedAt_iff_dot2_all
#check CPOG.directed_iff_dot2_all

-- Raw branching and deferable generation.
#check CPOG.raw_branching_no_common_successor
#check CPOG.raw_incomparable_branch_not_directedAt
#check CPOG.raw_branching_dot2_countervaluation
#check CPOG.finite_deferable_directed
#check CPOG.finite_deferable_dot2

-- Static semantic minimality and origin/semantic deflation.
#check CPOG.semantic_minimal_quotient
#check CPOG.observation_quotient_is_coarsest_observation_preserving
#check CPOG.origin_individuation_semantic_deflation

-- Static observation is weaker than dynamic safety.
#check CPOG.static_observation_equivalence_not_dynamically_safe
#check CPOG.static_dynamic_gap_direct

-- Tri-modal bisimulation and dynamic quotient safety.
#check CPOG.bisimulation_invariance
#check CPOG.quotient_invariance
#check CPOG.greatestObservationDynamicEquiv
#check CPOG.every_observation_dynamic_equiv_refines_greatest
#check CPOG.greatest_dynamic_observation_quotient_is_coarsest
#check CPOG.greatest_dynamic_observation_quotient_is_safe
#check CPOG.firstCommit_dot2_fails_on_greatest_observation_quotient

-- Generic irreversible divergence and FirstCommit instance.
#check CPOG.persistent_incompatible_branches_not_directed
#check CPOG.persistent_incompatible_branches_dot2_failure
#check CPOG.firstCommit_dot2_failure_is_persistent_region_instance

-- Same-model / same-abstraction contrast.
#check CPOG.split_same_abstraction_modal_contrast

-- Generic Subsumption representation and canonical repair.
#check CPOG.universal_state_subsumption_iff_forwardInvariant
#check CPOG.universal_state_subsumption_failure_iff_nonInvariant
#check CPOG.forwardClosure_least
#check CPOG.invariantKernel_greatest
#check CPOG.forwardClosure_idempotent_pointwise
#check CPOG.invariantKernel_idempotent_pointwise
#check CPOG.canonical_stabilizations_restore_subsumption

-- Evidence-order instances and awareness/evidence interface.
#check CPOG.preorder_universal_subsumption_iff_upperClosed
#check CPOG.identityView_fails_info_universal_subsumption
#check CPOG.identityView_recovers_noNewNegative_subsumption
#check CPOG.pure_awareness_growth_is_judgment_silent
#check CPOG.v54_subsumption_iff_generic_universal_subsumption

-- Possibility-role distinctions and metaphysical bridge boundary.
#check CPOG.live_implies_hist
#check CPOG.live_implies_reach
#check CPOG.hist_not_reach_countermodel
#check CPOG.reach_not_hist_countermodel
#check CPOG.adequate_statuses_are_pairwise_distinct
#check CPOG.role_adequacy_does_not_force_metaphysical_bridge
#check CPOG.metaphysical_bridge_requires_extra_assumption

-- Delimited Max appendix.
#check CPOG.standard_atomic_initial
#check CPOG.standard_atomic_freshness
#check CPOG.max_non_leaf
#check CPOG.finite_processing_closure_seals
#check CPOG.finite_universal_realization
#check CPOG.modal_firewall_satisfaction
#check CPOG.max_extension_core_conservative
#check CPOG.sealed_max_completion_and_conservativity

-- Reviewer-facing SC1-SC10 surface.
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
