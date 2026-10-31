import json
from pathlib import Path

rows = json.loads(Path("review_sheet.json").read_text(encoding="utf-8"))
lines = []
for row in rows:
    if "n" not in row:
        lines.append(
            "== {persona} {sid} turns={turns} open={open} gen={gen} retry={retry} interp={interp}".format(
                persona=row["persona"],
                sid=row["session_id"],
                turns=row["summary"]["completed_turns"],
                open=row["summary"]["opening_generation_calls"],
                gen=row["summary"]["gameplay_generation_calls"],
                retry=row["summary"]["gameplay_retry_calls"],
                interp=row["summary"]["interpretation_calls"],
            )
        )
        lines.append("disc_before " + json.dumps(row["discourse_before"]))
        lines.append("disc_after " + json.dumps(row["discourse_after_open"]))
        lines.append("npcs " + json.dumps(row["npc_before"]))
        lines.append("final_npcs " + json.dumps(row["final_npcs"]))
        lines.append("incidental_final " + json.dumps(row["final_incidental"])[:2000])
        lines.append("ledger_e " + json.dumps(row["final_ledger_entries"])[:2000])
        lines.append("ledger_r " + json.dumps(row["final_ledger_rejected"])[:1500])
        continue
    slot = row["interlocutor_slot"] or {}
    claim = row["claim"] or {}
    insp = row["inspected"] or {}
    prev = row["prev"] or {}
    lines.append(
        "{p}{n:02d} op={op} tgt={tgt} il={il} dim={dim} bind={bind}/{cls} fast={fast} abs={abs} interp={interp} src={src} h1={h1} regen={regen} h2={h2} prov={prov} exact={exact} eval={ev} fail={fail} ug={ug} ue={ue}".format(
            p=row["persona"][-1].upper(),
            n=row["n"],
            op=row["op"],
            tgt=row["target"],
            il=row["interlocutor"],
            dim=row["dimension"],
            bind=row["binding"],
            cls=row["entity_class"],
            fast=row["fast"],
            abs=row["abstention"],
            interp=row["interpreter"],
            src=row["source"],
            h1=row["a1_hard"],
            regen=row["regen"],
            h2=row["a2_hard"],
            prov=row["prov"],
            exact=row["exact"],
            ev=row["eval"],
            fail=row["failing"],
            ug=len(row["unauth_gen"] or []),
            ue=len(row["unauth_emit"] or []),
        )
    )
    lines.append(
        "  slot il={iid}|{ilab} claim={cid}|{clab} insp={iid2}|{ilab2} prev={pid}|{plab}".format(
            iid=slot.get("id"),
            ilab=slot.get("label"),
            cid=claim.get("id"),
            clab=(claim.get("label") or "")[:90],
            iid2=insp.get("id"),
            ilab2=insp.get("label"),
            pid=prev.get("id"),
            plab=(prev.get("label") or "")[:70],
        )
    )
Path("sheet.txt").write_text("\n".join(lines), encoding="utf-8")
print("wrote", len(lines))
