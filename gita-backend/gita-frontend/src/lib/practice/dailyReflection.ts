/** Rotating prompts (no LLM); keeps Today calm and repeatable. */

const REFLECTIONS: readonly string[] = [
  "Where might one small choice today align with this verse—without demanding a perfect outcome?",
  "What feeling or habit shows up when you read this? Notice it gently, without fixing everything at once.",
  "Who or what benefits if you carry even a fragment of this teaching into the next ordinary hour?",
  "What would it look like to hold this verse lightly: remembered, not performed?",
];

const TAKEAWAYS: readonly string[] = [
  "Carry a single phrase from the verse in silence for a few minutes before your next transition.",
  "Write one sentence in your own words; return to it once before sleep.",
  "Choose one concrete action today that fits the spirit of the verse—not the largest, but the clearest.",
  "When tension rises, pause once and recall the reference; let the text anchor, not pressure, you.",
];

export function reflectionPromptForDayIndex(dayIndex: number): string {
  return REFLECTIONS[((dayIndex % REFLECTIONS.length) + REFLECTIONS.length) % REFLECTIONS.length]!;
}

export function practicalTakeawayForDayIndex(dayIndex: number): string {
  return TAKEAWAYS[((dayIndex % TAKEAWAYS.length) + TAKEAWAYS.length) % TAKEAWAYS.length]!;
}
