namespace CPOG
namespace SubmissionCore

theorem generalizedSubsumptionIffUpperClosed
    {X : Type u}
    (G : GrowthSpec X) (A : X -> Prop) :
    UniversalSubsumptionOn G A <-> UpwardClosedOn G A :=
  abstract_universalSubsumption_iff_upwardClosed G A

theorem generalizedSubsumptionFailureIffDefeasible
    {X : Type u}
    (G : GrowthSpec X) (A : X -> Prop) :
    Not (UniversalSubsumptionOn G A) <-> AbstractDefeasible G A :=
  abstract_universalSubsumption_failure_iff_defeasible G A

theorem evidenceOrderTheoremIsExactInstance
    (P : EvidencePreorder) (V : ViewFn) :
    UniversalContentSubsumptionBy P V <->
      UniversalSubsumptionOn
        (evidenceDecisionGrowth P)
        (viewAccepted V) :=
  evidenceUniversalSubsumptionBy_iff_abstract P V

theorem decisionChangingSubsumptionIffProductUpperClosed
    (PE : EvidencePreorder)
    (PD : GrowthSpec DecisionState)
    (V : ViewFn) :
    UniversalEvaluationSubsumption PE PD V <->
      EvaluationRegionUpperClosed PE PD V :=
  evaluation_subsumption_iff_product_upperClosed PE PD V

end SubmissionCore
end CPOG
