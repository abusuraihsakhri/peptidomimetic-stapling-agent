"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {enumerate, audit} = require("./app.js");
test("Position enumeration is one-based and flags proline", () => {
  const report = enumerate("ACDEFGHIK");
  assert.equal(report.candidate_count, 7);
  assert.deepEqual(report.candidates[0], {start_position:1,end_position:5,
    spacing:"i,i+4",native_residues:"A-F",contains_proline:false});
  assert.equal(report.candidates[5].spacing, "i,i+7");
  assert.equal(enumerate("AAPAAAAA",[7]).candidates[0].contains_proline, true);
});
test("Invalid sequences are rejected", () => {
  for (const seq of ["","ACX","AAA1","A".repeat(501)]) assert.throws(() => enumerate(seq));
});
test("Audit applies three deterministic rules and handles thresholds", () => {
  const payload={task_id:"T1",target_identifier:"SEQ",primary_metric:26,
    secondary_metric:13,status_descriptor:"DISCORDANT",is_critical_flag:true};
  const result=audit(payload);
  assert.equal(result.total_alerts,3);
  assert.equal(result.critical_alerts_count,1);
  assert.equal(result.overall_urgency,"CRITICAL_STAT_PANIC");
  const nominal=audit({...payload,primary_metric:25,secondary_metric:12,
    status_descriptor:"NOMINAL",is_critical_flag:false});
  assert.equal(nominal.total_alerts,0);
  assert.equal(nominal.overall_urgency,"ROUTINE");
});
test("Empty and non-finite numeric inputs are rejected", () => {
  const payload={task_id:"T1",target_identifier:"SEQ",primary_metric:"",
    secondary_metric:"5",is_critical_flag:false};
  assert.throws(() => audit(payload));
  assert.throws(() => audit({...payload,primary_metric:"NaN"}));
});
