from __future__ import annotations
import copy
from dataclasses import dataclass

ACTIONS=("observe","work","maintain","sleep","hibernate","idle")
ENERGY_COST={"idle":0.04,"observe":0.18,"work":0.45,"maintain":0.25,"sleep":0.005,"hibernate":0.002}
BASE_COST={"idle":0.01,"observe":0.01,"work":0.015,"maintain":0.012,"sleep":0.003,"hibernate":0.0005}
COMPUTE_COST={"idle":0.02,"observe":0.40,"work":1.00,"maintain":0.05,"sleep":0.005,"hibernate":0.0}
STORAGE_COST={"idle":0.002,"observe":0.015,"work":0.020,"maintain":0.004,"sleep":0.001,"hibernate":0.0002}
SLEEP_EFFICIENCY=0.90
SLEEP_MAX_DRAW=0.70

@dataclass(frozen=True)
class Observation:
    stimulus: float
    workload: float
    hazard: float
    novelty: float


def deterministic_observation(tick:int)->Observation:
    return Observation(
        stimulus=((tick*37)%101)/100,
        workload=((tick*19+11)%97)/96,
        hazard=1.0 if tick%997==0 else ((tick*7)%31)/300,
        novelty=((tick*43+5)%89)/88,
    )


def choose_action(state:dict, obs:Observation)->tuple[str,str]:
    e=state["resources"]["energy"]; reserve=state["resources"]["metabolic_reserve"]
    h=state["health"]["integrity"]; debt=state["metabolism"]["maintenance_debt"]
    status=state["lifecycle"]["status"]
    if status!="alive": return "idle","not_alive"
    # survival/maintenance always outranks autobiographical preference.
    if e < 5 and reserve <= 1: return "hibernate","critical_low_resource"
    if debt >= 8 or h < 75 or obs.hazard > 0.8: return "maintain","maintenance_due"
    if e < 18 and reserve > 0: return "sleep","low_energy_recharge"
    if state["resources"]["compute_credit"] < 10: return "hibernate","compute_credit_exhaustion_guard"
    if obs.workload > 0.56 and e > 35: return "work","workload"
    if obs.novelty > 0.62: return "observe","novelty"
    sm=state.get("self_model",{}); vals=sm.get("learned_action_value",{}); cnt=sm.get("learned_action_count",{})
    if e>35 and cnt.get("work",0)>=5 and cnt.get("observe",0)>=5:
        w=float(vals.get("work",0)); o=float(vals.get("observe",0))
        if abs(w-o)>=0.15:
            return ("work","autobiographical_value") if w>o else ("observe","autobiographical_value")
    return "idle","baseline"

def experienced_value(state:dict, action:str, obs:Observation)->float:
    profile=state.get("world_model",{}).get("experience_profile","balanced")
    if action=="work":
        v=0.20+0.40*obs.workload
        if profile=="work_favorable": v+=0.80
        elif profile=="exploration_favorable": v+=0.05
    elif action=="observe":
        v=0.20+0.40*obs.novelty
        if profile=="exploration_favorable": v+=0.80
        elif profile=="work_favorable": v+=0.05
    elif action=="maintain": v=0.35
    elif action=="sleep": v=0.25
    elif action=="hibernate": v=0.05
    else: v=0.10
    return round(max(-1.0,min(1.5,v)),6)

def _debit(v:float,cost:float)->tuple[float,float]:
    actual=min(max(v,0.0),max(cost,0.0)); return v-actual,actual


def apply_action(state:dict, action:str, reason:str, obs:Observation)->tuple[dict,dict]:
    s=copy.deepcopy(state); m=s["metabolism"]; r=s["resources"]
    requested=ENERGY_COST[action]+BASE_COST[action]
    r["energy"],burn=_debit(r["energy"],requested)
    r["compute_credit"],cc=_debit(r["compute_credit"],COMPUTE_COST[action])
    r["storage_credit"],sc=_debit(r["storage_credit"],STORAGE_COST[action])
    m["cumulative_costs"]["energy_burn"]=round(m["cumulative_costs"]["energy_burn"]+burn,9)
    m["cumulative_costs"]["compute"]=round(m["cumulative_costs"]["compute"]+cc,9)
    m["cumulative_costs"]["storage"]=round(m["cumulative_costs"]["storage"]+sc,9)
    # Sleep moves finite reserve into active energy; conversion loss is explicit.
    if action=="sleep" and r["metabolic_reserve"]>0:
        room=max(0.0,100.0-r["energy"])
        draw=min(r["metabolic_reserve"],SLEEP_MAX_DRAW,room/SLEEP_EFFICIENCY if room else 0.0)
        gain=draw*SLEEP_EFFICIENCY; loss=draw-gain
        r["metabolic_reserve"]=round(r["metabolic_reserve"]-draw,9); r["energy"]=round(r["energy"]+gain,9)
        m["cumulative_costs"]["reserve_draw"]=round(m["cumulative_costs"]["reserve_draw"]+draw,9)
        m["cumulative_costs"]["conversion_loss"]=round(m["cumulative_costs"]["conversion_loss"]+loss,9)
        m["sleep_ticks"]+=1; m["mode"]="sleep"
    elif action=="hibernate":
        m["hibernate_ticks"]+=1; m["mode"]="hibernating"
    else:
        m["mode"]="active"
    health=s["health"]["integrity"]
    debt=m["maintenance_debt"]
    if action=="maintain":
        health=min(100.0,health+0.16); debt=max(0.0,debt-3.0); m["maintenance_ticks"]+=1
    elif action=="work":
        health=max(0.0,health-0.018-obs.hazard*0.02); debt+=0.22
    elif action=="observe":
        health=max(0.0,health-0.003); debt+=0.035
    elif action=="idle":
        health=max(0.0,health-0.001); debt+=0.008
    elif action=="sleep":
        health=min(100.0,health+0.025); debt=max(0.0,debt-0.08)
    elif action=="hibernate":
        debt=max(0.0,debt-0.01)
    if obs.hazard>0.5 and action!="maintain": health=max(0.0,health-0.08*obs.hazard); debt+=0.5*obs.hazard
    s["health"]["integrity"]=round(health,6); m["maintenance_debt"]=round(debt,6)
    s["health"]["maintenance_state"]="critical" if debt>=12 else ("due" if debt>=6 else "nominal")
    r["energy"]=round(max(0.0,min(100.0,r["energy"])),9)
    m["last_cost"]={"energy":round(burn,9),"compute":round(cc,9),"storage":round(sc,9)}; m["last_decision_reason"]=reason; m["metabolic_ticks"]+=1
    if r["energy"]<=0 and r["metabolic_reserve"]<=0:
        s["lifecycle"]["status"]="dead"; s["lifecycle"]["death_tick"]=s["runtime"]["tick"]+1
        s["lifecycle"]["death_reason"]="resource_exhaustion"; m["mode"]="dead"
        s["lifecycle"]["death_certificate"]={"irreversible":True,"reason":"resource_exhaustion","tick":s["runtime"]["tick"]+1}
    elif health<=0:
        s["lifecycle"]["status"]="dead"; s["lifecycle"]["death_tick"]=s["runtime"]["tick"]+1
        s["lifecycle"]["death_reason"]="integrity_failure"; m["mode"]="dead"
        s["lifecycle"]["death_certificate"]={"irreversible":True,"reason":"integrity_failure","tick":s["runtime"]["tick"]+1}
    s["runtime"]["action_counts"][action]+=1
    value=experienced_value(s,action,obs)
    prior=float(s.get("self_model",{}).get("learned_action_value",{}).get(action,0.0))
    episode={"tick":s["runtime"]["tick"]+1,"action":action,"decision_reason":reason,"stimulus":round(obs.stimulus,4),"workload":round(obs.workload,4),"novelty":round(obs.novelty,4),"hazard":round(obs.hazard,4),"experienced_value":value,"prediction_error":round(abs(value-prior),6),"origin_individual_id":s["identity"]["individual_id"]}
    mem=s["memory"]["episodic"]; mem.append(episode)
    if len(mem)>256: del mem[:-256]
    s["memory"]["working"]={"last_action":action,"last_observation":episode}; s["world_model"]["last_observation"]=episode
    fatigue=max(0.0,min(1.0,1.0-r["energy"]/100.0)); valence=max(-1.0,min(1.0,(health-70.0)/30.0-obs.hazard*0.25)); arousal=max(0.0,min(1.0,0.25+obs.novelty*0.45+obs.hazard*0.45))
    s["affect"].update({"fatigue":round(fatigue,6),"valence":round(valence,6),"arousal":round(arousal,6)})
    return s,episode
