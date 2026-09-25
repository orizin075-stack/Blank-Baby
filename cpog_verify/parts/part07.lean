
def fcAntecedent : Formula FCAtom :=
  .diaG (.boxG (.atom .pA))

def fcConsequent : Formula FCAtom :=
  .boxG (.diaG (.atom .pA))

theorem fc_model_antecedent :
    Satisfies fcModel .root fcAntecedent := by
  change Dia fcR (Box fcR PA) .root
  exact firstCommit_dot2_antecedent

theorem fc_model_consequent_fails :
    Not (Satisfies fcModel .root fcConsequent) := by
  change Not (Box fcR (Dia fcR PA) .root)
  exact firstCommit_dot2_consequent_fails

theorem firstCommit_A_B_not_bisimilar
    {Z : FCWorld -> FCWorld -> Prop}
    (hZ : IsBisimulation fcModel fcModel Z) :
    Not (Z .a .b) := by
  exact atom_difference_blocks_bisimulation hZ (a := FCAtom.pA)
    (by trivial) (by trivial)

theorem firstCommit_classes_distinct
    {E : FCWorld -> FCWorld -> Prop}
    (hE : DynamicEquiv fcModel E)
    (P : QuotientPresentation FCWorld Q E) :
    Not (P.classOf .a = P.classOf .b) := by
  intro hEq
  have hAB : E .a .b := (P.class_eq_iff).mp hEq
  exact firstCommit_A_B_not_bisimilar hE.bisim hAB

theorem firstCommit_quotient_dot2_failure
    {E : FCWorld -> FCWorld -> Prop}
    (hE : DynamicEquiv fcModel E)
    (P : QuotientPresentation FCWorld Q E) :
    Satisfies (quotientModel fcModel P) (P.classOf .root) fcAntecedent /\
    Not (Satisfies (quotientModel fcModel P) (P.classOf .root) fcConsequent) := by
  constructor
  · exact (quotient_invariance hE P fcAntecedent .root).mp fc_model_antecedent
  · intro hConsQ
    have hCons : Satisfies fcModel .root fcConsequent :=
      (quotient_invariance hE P fcConsequent .root).mpr hConsQ
    exact fc_model_consequent_fails hCons

end CPOG
