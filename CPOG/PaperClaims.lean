import CPOG.History
import CPOG.General
import CPOG.DeferableGeneration
import CPOG.DynamicQuotient
import CPOG.DynamicObservation
import CPOG.GreatestDynamicObservation
import CPOG.Provenance
import CPOG.Possibility
import CPOG.PossibilitySeparation
import CPOG.SeedEvidence
import CPOG.MetaphysicalBridge
import CPOG.Policy
import CPOG.Dynamics
import CPOG.FiniteConvergence
import CPOG.MaxAppendix

/-!
Machine-checked crosswalk between the paper's claims and the Lean declarations
that establish them.  The commands below are intentionally explicit: if a
theorem is renamed, removed, or ceases to elaborate, this module fails to build.
-/

namespace CPOG.PaperClaims

-- Proposition 1: Historical Persistence.
#check CPOG.History.historical_persistence

-- Proposition 2A: raw prefix-history branching / incomparability refutes .2.
#check CPOG.EpistemicPotentialism.raw_incomparable_branching_dotTwo_fails

-- Deferable/non-exhaustive generation can recover .2 in a directed join model.
#check CPOG.DeferableGeneration.deferable_generation_validates_dotTwo

-- Theorem 2B: FirstCommit divergence survives a genuine dynamic quotient.
#check CPOG.DynamicQuotient.firstCommit_dotTwo_fails_on_dynamicQuotient

-- Dynamic observation quotient refines the static quotient and preserves G/D/H truth.
#check CPOG.DynamicObservation.dynamic_observation_quotient_is_semantically_safe
#check CPOG.GreatestDynamicObservation.greatest_dynamic_observation_quotient_is_coarsest
#check CPOG.GreatestDynamicObservation.greatest_dynamic_observation_quotient_is_safe

-- Theorem 3: generic and concrete defeasible-content Subsumption failure.
#check CPOG.EpistemicPotentialism.not_subsumption_of_D_stable_G_defeater
#check CPOG.EpistemicPotentialism.content_subsumption_failure_of_G_defeat
#check CPOG.EpistemicPotentialism.subsumption_of_G_stable

-- Theorem 4: Semantic Minimal Quotient / universal factorization.
#check CPOG.SemanticProvenance.adequate_kernel_refines_observationQuotient
#check CPOG.SemanticProvenance.observationQuotient_factors_through_every_adequate_abstraction

-- Four-way possibility separation and conservative seed evidence.
#check CPOG.Possibility.possLive_implies_hist
#check CPOG.Possibility.hist_not_imply_reach_under_closure
#check CPOG.PossibilitySeparation.hist_and_reach_do_not_collapse
#check CPOG.SeedEvidence.dream_can_be_live_with_no_positive_support
#check CPOG.MetaphysicalBridge.live_without_metaphysical_possibility
#check CPOG.MetaphysicalBridge.historical_without_metaphysical_possibility
#check CPOG.MetaphysicalBridge.certification_implies_metaphysical_possibility

-- Provenance policy specialization and open-ended future-policy safety.
#check CPOG.Policy.adequate_source_abstraction_refines_policyEq
#check CPOG.Policy.open_ended_policy_safety_requires_identity

-- FDE dynamic safety and sharp finite convergence.
#check CPOG.DynamicSafety.dynamicSafety_iff_reflexiveClosureStability
#check CPOG.FiniteConvergence.fdeIter_fixed_card_sub_one

-- Appendix A: formally delimited Max claims.
#check CPOG.MaxAppendix.freeAtomicExtension_initial
#check CPOG.MaxAppendix.finiteProcessingClosure_reaches_seal
#check CPOG.MaxAppendix.jointlyAdmissible_executes
#check CPOG.MaxAppendix.modalFirewall_satisfaction

end CPOG.PaperClaims
