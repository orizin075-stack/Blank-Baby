"""claude-patch2: say WHY, from the checked proof object (never from free text)."""
from __future__ import annotations

def explain(res):
    p=res.get('proof') or {};k=p.get('kind');a=res.get('answer')
    try:
        if k=='arithmetic':
            s=p.get('schema')
            label={'rate_x_time':'速さ×時間','distance_div_rate':'道のり÷速さ','distance_div_time':'道のり÷時間','unit_price':'単価×個数','unit_price_change':'払った額−代金',
                   'equal_groups':'1つ分×いくつ分','per_container':'1つの入れ物の数×入れ物の数','equal_sharing':'全体÷人数','grouping':'全体÷1まとまりの数',
                   'comparison':'基準の数±差','change_sequence':'はじめの数に増減を順に足し引き','combine':'全部を合計',
                   'one_unknown_equation':'操作を逆にたどって（答えを元の式に戻して確認済み）','rate_per_period_x_periods':'1回分×回数','total_div_rate_per_period':'全体÷1回分',
                   'distribute_each':'全体÷1人分','part_whole':'全体−一部','difference':'大きい方−小さい方','each_item_price':'1つずつの値段の合計×個数',
                   'times_as_many':'もとの数×倍','unit_prices':'単価×個数の合計','sequential_percentage_price':'割合を順に適用'}.get(s)
            return (f'{label}で、{p["expression"]} = {a}。' if label else f'{p["expression"]} = {a}。')
        if k=='inventory':
            steps=[f'{e["clause"]}（{"+" if e["direction"]>0 else "−" if e["direction"]<0 else "±0"}{e["quantity"]*e["factor"]}）' for e in p.get('events',[])]
            return f'はじめは{p["initial"]}。'+('、'.join(steps)+'。' if steps else '')+f'残りは{a}。'
        if k=='logic':
            return '前提から ' + ' → '.join(b for _,b in p.get('steps',[])) + ' と導きました。' if p.get('steps') else '前提にそのまま書かれています。'
        if k=='qtime':
            lab={'conversion':'単位をそろえて換算','clock':'時刻を0時からの分に直して計算','weekday':'7日ごとに同じ曜日に戻るので数えて','calendar':'暦（グレゴリオ暦）で数えて',
                 'percent':'割合をかけて','constant':'決まった数（1ダース=12など）から'}.get(p.get('qkind'),'')
            return f'{lab}: {p["expression"]} → {a}。' if p.get('expression') else f'{lab}、{a}。'
        if k=='knowledge':
            hops=' → '.join(r['text'] for r in p.get('records',[]))
            return f'記憶「{hops}」より。'
        if k=='memory':
            f=p['facts'][0];return f'教わった事実「{f["entity"]}の{f["relation"]}は{f["value"]}」より。'
        if k=='deliberation':
            return '検算した計算段階: '+'、'.join(f'{s["expression"]} = {s["value"]}' for s in p['steps'])+'。'
        if k=='meta_derivation':
            return '依存する値を順に検算: '+'、'.join(f'{s["variable"]} = {s["value"]}' for s in p['steps'])+'。'
        if k=='hypothesis':return f'提示例に一致する有限候補が1つに定まり、入力{p["target_x"]}で{a}となりました。'
        if k in ('plan','plan_cost'):return '許容された探索範囲で、費用の安い順に調べ、目標へ届く経路を選び検算しました。'
        if k=='situation':
            # claude-patch6: say what was asked, then how the story's model gives it
            who=lambda t:'' if not t or t[0] in ('*','わたし') else f'{t[0]}の'
            role=p.get('role');t=p.get('target') or []
            head={'remain':'今の数を聞いているので、','total':'全員分を合わせた数を聞いているので、','initial':'はじめの数を聞いているので、',
                  'before':f'「{t[0] if t else ""}」の前の数を聞いているので、','event':'出来事そのものの数を聞いているので、',
                  'received':f'{t[0] if t else ""}が受け取った数を聞いているので、','holding':f'{who(t)}今の数を聞いているので、'}.get(role,'')
            return f'{head}{p["expression"]} = {a}。'
        if k=='mathprob':
            return f'{p.get("label") or ""}{": " if p.get("label") else ""}{p["expression"]} = {a}。'
    except (KeyError,IndexError,TypeError):return None
    return None
