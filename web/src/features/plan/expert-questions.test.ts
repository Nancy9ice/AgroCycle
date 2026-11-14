import { describe, expect, it } from "vitest";
import { getComparison } from "@/features/compare/get-comparison";
import { ruleTable } from "@/features/compare/rules";
import { buildAdviserQuestions } from "./expert-questions";

const decisionFor = async (answers: Record<string, string>, preview = false) =>
  (await getComparison("primary-001", answers, { preview }))!.decision;

describe("adviser questions", () => {
  it("asks about every unanswered farmer question", async () => {
    const questions = buildAdviserQuestions(await decisionFor({}));
    const fromAnswers = questions.filter((q) => q.source === "answer");
    expect(fromAnswers).toHaveLength(4);
  });

  it("asks nothing about answers the farmer gave", async () => {
    const all = {
      manure: "yes",
      hayOutlet: "can_sell",
      oatOutlet: "yes",
      grainEquipment: "have",
    };
    const questions = buildAdviserQuestions(await decisionFor(all, true));
    expect(questions.filter((q) => q.source === "answer")).toHaveLength(0);
  });

  it("carries the engine's sentence for each fired rule, once", async () => {
    const decision = await decisionFor({ manure: "no" }, true);
    const rule = questions(decision).filter((q) => q.source === "rule");
    expect(rule.some((q) => q.text.includes("no access to manure"))).toBe(true);
    expect(new Set(rule.map((q) => q.id)).size).toBe(rule.length);
  });

  it("asks for a source for every research-needed claim", async () => {
    const claims = questions(await decisionFor({})).filter((q) => q.source === "claim");
    const needed = ruleTable.cropClaims.filter((c) => c.status === "research_needed");
    expect(claims).toHaveLength(needed.length);
  });

  it("always includes the standing questions, even for a clean result", async () => {
    const all = {
      manure: "yes",
      hayOutlet: "can_sell",
      oatOutlet: "yes",
      grainEquipment: "have",
    };
    expect(
      questions(await decisionFor(all, true)).filter((q) => q.source === "standing"),
    ).toHaveLength(3);
  });
});

const questions = buildAdviserQuestions;
