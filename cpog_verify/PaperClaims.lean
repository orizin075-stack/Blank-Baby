import CPOG

/-!
Reviewer-facing compile gate for the paper-level theorem surface.
If any theorem is renamed, deleted, or stops elaborating, this module fails.
-/

-- Core history / modal frame claims
#check CPOG.PaperClaims.historicalPersistence
#check CPOG.PaperClaims.localDot2IffDirected
#check CPOG.PaperClaims.modalTIffReflexive
#check CPOG.PaperClaims.modal4IffTransitive
#check CPOG.PaperClaims.deferableGenerationDot2
#check CPOG.PaperClaims.irreversibleDivergence
#check CPOG.PaperClaims.firstCommitInstance
#check CPOG.PaperClaims.sameAbstractionModalContrast
#check CPOG.PaperClaims.historyModalS4Frames

-- Subsumption / stability / repair
#check CPOG.PaperClaims.universalSubsumptionIffForwardInvariant
#check CPOG.PaperClaims.subsumptionFailureIffNonInvariant
#check CPOG.PaperClaims.canonicalStabilizationRepairs
#check CPOG.PaperClaims.historicalSubsumptionFailure
#check CPOG.PaperClaims.canonicalContentFailureIffDefeasible
#check CPOG.PaperClaims.stableFragmentSubsumption

-- Dynamic quotient / provenance / origin
#check CPOG.PaperClaims.dynamicQuotientTruthPreservation
#check CPOG.PaperClaims.coarsestDynamicSafeQuotient
#check CPOG.PaperClaims.coarsestDynamicSafeQuotientTruth
#check CPOG.PaperClaims.originIndividuationSemanticDeflation
#check CPOG.PaperClaims.staticDynamicGap
#check CPOG.PaperClaims.semanticObservationMinimality
#check CPOG.PaperClaims.coarsestObservationSafeDynamicQuotient
#check CPOG.PaperClaims.observationSafeDynamicQuotientTruth
#check CPOG.PaperClaims.observationSafeDynamicQuotientRespectsObservation

-- Awareness / possibility-role separation
#check CPOG.PaperClaims.awarenessSilence
#check CPOG.PaperClaims.possibilityRoleSeparation
#check CPOG.PaperClaims.epistemicRoleDoesNotForceMetaphysical
#check CPOG.PaperClaims.committedNotReachableWitness
#check CPOG.PaperClaims.reachableNotCommittedWitness

-- Policy / FDE dynamics / finite convergence
#check CPOG.PaperClaims.policyMinimality
#check CPOG.PaperClaims.openEndedPolicySafetyRequiresIdentity
#check CPOG.PaperClaims.fdeDynamicSafetyIffReflexiveClosureStability
#check CPOG.PaperClaims.fdeFiniteConvergenceCardSubOne
#check CPOG.PaperClaims.supportFiniteConvergenceCardSubOne

-- Delimited Max appendix
#check CPOG.PaperClaims.finiteMaxRealization
#check CPOG.PaperClaims.maxSealAndConservativity
