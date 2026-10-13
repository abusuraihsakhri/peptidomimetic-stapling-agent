"use strict";
// Offline, position-only sequence screening; not a chemical-property predictor.
const StapleEngine = (() => {
  const alphabet = "ACDEFGHIKLMNPQRSTVWY";
  function enumerate(sequence, spacings = [4, 7]) {
    if (typeof sequence !== "string") throw Error("Sequence must be text.");
    const clean = sequence.replace(/\s+/g, "").toUpperCase();
    if (clean.length < 1 || clean.length > 500) throw Error("Enter 1–500 residues.");
    if ([...clean].some(ch => !alphabet.includes(ch))) throw Error("Use canonical one-letter amino-acid codes.");
    if (!Array.isArray(spacings) || !spacings.length ||
        spacings.some(s => s !== 4 && s !== 7)) throw Error("Spacings must be 4, 7, or both.");
    const candidates = [];
    for (const spacing of [...new Set(spacings)]) {
      for (let i = 0; i + spacing < clean.length; i++) {
        candidates.push({
          start_position: i + 1,
          end_position: i + spacing + 1,
          spacing: "i,i+" + spacing,
          native_residues: clean[i] + "-" + clean[i + spacing],
          contains_proline: clean.slice(i, i + spacing + 1).includes("P")
        });
      }
    }
    return {sequence: clean, candidate_count: candidates.length, candidates,
      note: "Position pairs only; no chemical feasibility, stereochemistry, helicity, binding or uptake prediction."};
  }
  function audit(payload) {
    if (!payload || typeof payload !== "object") throw Error("Missing audit inputs.");
    const primary = Number(payload.primary_metric), secondary = Number(payload.secondary_metric);
    if (String(payload.primary_metric).trim() === "" || String(payload.secondary_metric).trim() === "" ||
        !Number.isFinite(primary) || !Number.isFinite(secondary)) throw Error("Enter finite numeric measurements.");
    if (typeof payload.is_critical_flag !== "boolean") throw Error("Critical flag must be a boolean.");
    const taskId = String(payload.task_id || "").trim();
    const targetId = String(payload.target_identifier || "").trim();
    const desc = String(payload.status_descriptor || "").trim();
    if (!taskId || !targetId || taskId.length > 128 || targetId.length > 128 || desc.length > 128) {
      throw Error("Task and target identifiers must contain 1–128 characters.");
    }
    const alerts = [];
    if (primary > 25) alerts.push({worker:"InvariantQCWorker", urgency:"ELEVATED_RISK",
      summary:"Primary metric exceeds configured threshold (25)."});
    if (payload.is_critical_flag || secondary > 12) alerts.push({
      worker:"SafetyEscalationWorker",
      urgency:payload.is_critical_flag ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
      summary:"Critical flag active or secondary metric exceeds configured threshold (12)."});
    if (["DISCORDANT","ANOMALY","MUTANT","VIOLATION","FAIL","REJECT"]
          .some(word => desc.toUpperCase().includes(word))) {
      alerts.push({worker:"ProtocolConformanceWorker", urgency:"ELEVATED_RISK",
        summary:"Status descriptor matched configured alert term."});
    }
    const critical = alerts.filter(a => a.urgency === "CRITICAL_STAT_PANIC").length;
    return {task_id:taskId, target_identifier:targetId,
      overall_urgency:critical ? "CRITICAL_STAT_PANIC" : alerts.length ? "ELEVATED_RISK" : "ROUTINE",
      integrity_status:critical ? "RECALIBRATION_REQUIRED" : alerts.length ? "DISCORDANT_ANOMALY" : "VALIDATED_OPTIMAL",
      total_alerts:alerts.length, critical_alerts_count:critical, alerts,
      note:"Generic threshold demonstration, not a validated peptide-property or clinical predictor."};
  }
  return {enumerate, audit};
})();
if (typeof module !== "undefined" && module.exports) module.exports = StapleEngine;
if (typeof document !== "undefined") {
  const el = id => document.getElementById(id);
  let report = null;
  function present(data) {
    report = data;
    el("results").textContent = JSON.stringify(data, null, 2);
    el("status").textContent = "Results computed in your browser.";
    el("download").disabled = false;
  }
  function fail(error) {
    report = null;
    el("status").textContent = error.message || "Invalid inputs.";
    el("results").textContent = "Correct the input and retry.";
    el("download").disabled = true;
  }
  el("sequence-form").addEventListener("submit", event => {
    event.preventDefault();
    try {
      const s = el("spacing").value;
      present(StapleEngine.enumerate(el("sequence").value, s === "both" ? [4, 7] : [Number(s)]));
    } catch (err) { fail(err); }
  });
  el("audit-form").addEventListener("submit", event => {
    event.preventDefault();
    try {
      present(StapleEngine.audit({task_id:el("task-id").value,
        target_identifier:el("target-id").value, primary_metric:el("primary").value,
        secondary_metric:el("secondary").value, status_descriptor:el("descriptor").value,
        is_critical_flag:el("critical").checked}));
    } catch (err) { fail(err); }
  });
  el("download").addEventListener("click", () => {
    if (!report) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2) + "\n"],
      {type:"application/json"}));
    const link = document.createElement("a");
    link.href = url;
    link.download = "staple-screen-results.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}
