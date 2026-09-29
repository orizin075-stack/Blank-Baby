import CPOG.General

namespace CPOG.Closure

universe uW

/-- Explicit reflexive-transitive closure used for G/D/H accessibility. -/
inductive RTC {W : Type uW} (step : W -> W -> Prop) : W -> W -> Prop
  | refl (x : W) : RTC step x x
  | tail {x y z : W} : RTC step x y -> step y z -> RTC step x z

theorem rtc_refl {W : Type uW} (step : W -> W -> Prop) (x : W) :
    RTC step x x :=
  RTC.refl x

theorem rtc_trans {W : Type uW} {step : W -> W -> Prop}
    {x y z : W} (hxy : RTC step x y) (hyz : RTC step y z) :
    RTC step x z := by
  induction hyz with
  | refl =>
      exact hxy
  | tail hprev hstep ih =>
      exact RTC.tail ih hstep

theorem rtc_frame_S4 {W : Type uW}
    (step : W -> W -> Prop)
    (phi : W -> Prop) (w : W) :
    (CPOG.EpistemicPotentialism.BoxR (RTC step) phi w -> phi w) /\
    (CPOG.EpistemicPotentialism.BoxR (RTC step) phi w ->
      CPOG.EpistemicPotentialism.BoxR (RTC step)
        (CPOG.EpistemicPotentialism.BoxR (RTC step) phi) w) := by
  exact CPOG.EpistemicPotentialism.S4_frame_laws
    (RTC step)
    (fun x => rtc_refl step x)
    (fun _ _ _ h1 h2 => rtc_trans h1 h2)
    phi w

/-- Any one-step transition is included in its reflexive-transitive closure. -/
theorem step_to_rtc {W : Type uW}
    {step : W -> W -> Prop} {x y : W}
    (h : step x y) : RTC step x y := by
  exact RTC.tail (RTC.refl x) h

end CPOG.Closure
