#!/usr/bin/env python3
"""Write data/guidance_life_theme_review_queries.json from the life-theme prompt list."""

from __future__ import annotations

import json
import re
from pathlib import Path

_RAW = r"""
1) Effort, results, burnout, duty
I work hard but feel crushed when results don’t match my effort. How should I think about this?
I obsess over performance metrics and feel burned out. What does the Gita say?
I do my best, but I cannot control what happens next. How do I let go?
I keep tying my self-worth to outcomes. How do I act without that attachment?
I am exhausted from always chasing success. How can I work with more peace?
I keep checking whether my work is paying off. How do I stop obsessing over results?
I feel like all my effort is wasted when things don’t work out.
I want to do my duty, but I hate not knowing if it will matter.
I feel anxious because I cannot guarantee the outcome of what I’m doing.
How do I keep working sincerely when the result is uncertain?
I am afraid to act because I might fail.
I feel discouraged when my effort is invisible to others.
I’m tired of comparing outcomes instead of respecting the work itself.
I want to act well without becoming emotionally dependent on success.
My job feels endless and thankless. How do I keep going without bitterness?
I feel like I am becoming mechanical and joyless in my work.
I can’t stop measuring my value by achievement.
What verse best helps someone who is obsessed with results?
I want peace while working, not just after success.
I am losing motivation because my effort hasn’t produced visible rewards.
2) Discipline, procrastination, self-sabotage
I keep procrastinating and then hating myself for it. How do I build discipline?
I know what I should do, but I keep delaying it.
I keep sabotaging my own progress. How do I stop?
How do I become more disciplined without becoming harsh with myself?
I start habits strongly and then give up after a few days.
I keep choosing comfort over what I know is right.
I waste time and then feel ashamed afterward.
I cannot stay consistent. What guidance does the Gita offer?
I keep losing to distraction even when I want to do better.
I need help controlling my impulses.
I don’t trust myself to follow through anymore.
I feel weak because my intentions are better than my actions.
How do I train my mind when it keeps wandering toward comfort?
I want discipline, but I keep collapsing into laziness.
I feel like my own mind is working against me.
I keep breaking promises to myself.
How do I build steady habits one day at a time?
What verse best applies to self-discipline and self-mastery?
I want to become stronger inside, not just more productive.
How do I stop degrading myself every time I slip?
3) Anxiety, fear, overwhelm
I feel anxious about the future all the time.
Fear keeps taking over even when I try to trust.
I had a panic attack and still feel shaken.
I feel overwhelmed by everything on my plate.
My mind keeps running worst-case scenarios.
I am afraid of making the wrong decision.
I feel pressure from every direction and don’t know how to stay steady.
I want to trust God more, but fear keeps winning.
I feel physically restless and mentally exhausted.
What does the Gita say about fear and inner steadiness?
I keep overthinking what could go wrong.
I feel trapped between anxiety and responsibility.
I want peace, but my mind feels chaotic.
Fear of failure is stopping me from acting.
I am afraid I will disappoint everyone.
I cannot calm my mind when I am under pressure.
I feel flooded by uncertainty.
How do I act when my mind is full of fear?
I am tired of living in anticipation of something bad.
Give me one verse for anxiety and explain it clearly.
4) Surrender, trust in God, spiritual refuge
I want to surrender my anxiety and take refuge in trust in God.
I want to trust God more, but I don’t know how.
I feel like I am trying to control everything instead of surrendering.
What does the Gita say about taking refuge in the divine?
I want to let go and trust, but I keep clinging.
I pray, but fear still stays in my chest.
I want to believe I am being carried, not abandoned.
How do I surrender without becoming passive?
I want to place my life in God’s hands.
I feel like I’m holding on too tightly to control.
I want a verse about surrender that feels personal and comforting.
I long for refuge, but my mind resists trust.
I want to stop relying only on myself.
I feel spiritually tired and want to rest in faith.
What verse best applies to trust in God during fear?
I want to feel held by something greater than myself.
I need help letting go of control over my life.
I want a devotional answer, not just a philosophical one.
How do I surrender while still doing my duty?
I want to trust divine guidance even when I can’t see the path.
5) Grief, regret, loss, replaying the past
After a loss, I keep replaying what I should have done differently.
I feel numb after losing someone I loved.
I cannot stop thinking about what I should have said before it was too late.
Grief keeps coming in waves and I feel helpless.
I feel guilty after a loss and don’t know how to live with it.
I replay old moments and torture myself with “what if.”
I am grieving, but I also feel strangely empty.
What does the Gita say about grief and impermanence?
I want comfort after loss, but not empty clichés.
I can’t forgive myself for not doing more.
I feel stuck in sadness and regret.
I want to let grief soften me, not destroy me.
What verse best helps with replaying the past after loss?
I feel haunted by one moment I cannot change.
I want to keep loving without drowning in grief.
How do I mourn without collapsing into despair?
I keep wishing I could undo what happened.
I feel both pain and guilt after this loss.
I want a verse for grief that is compassionate and practical.
How do I live when something precious is gone?
6) Shame, guilt, forgiveness, moral injury
I feel ashamed of my past actions and can’t forgive myself.
I did something wrong and I don’t know how to move forward.
I carry guilt that keeps returning no matter what I do.
I feel stained by choices I made in weakness.
How does the Gita help with shame and self-forgiveness?
I know I was wrong, but I don’t want shame to define me forever.
I feel morally broken.
I want to repair what I can, but I also need inner release.
I keep reliving a mistake I made years ago.
I’m afraid my past actions say who I really am.
What verse helps someone who feels unworthy?
I want to stop punishing myself internally.
I don’t know whether I deserve peace after what I did.
How do I take responsibility without becoming consumed by guilt?
I want to change, but shame keeps freezing me.
I’m tired of being at war with myself.
I want guidance that is honest but not condemning.
I feel like I ruined something important.
I want to rebuild integrity after failure.
Give me one verse for guilt and one practical next step.
7) Comparison, envy, insecurity, worth
I compare myself to others and feel like I’m falling behind in life.
I feel envious when I see other people succeeding.
I keep wondering why others seem ahead of me.
I feel small when I compare my path with theirs.
I want to stop living through comparison.
I feel insecure because others are moving faster than me.
My peace disappears when I compare my achievements.
How does the Gita help with envy?
I feel like my path is inferior to everyone else’s.
I keep measuring myself against other people’s timelines.
I want freedom from jealousy and insecurity.
I feel ashamed that comparison controls me.
What verse helps with feeling behind in life?
I want to value my own path more deeply.
I am tired of needing external validation.
How do I stop resenting other people’s blessings?
I want to feel grounded in my own dharma.
I compare careers, relationships, and even spirituality.
I want a verse for insecurity and self-worth.
I feel like my life is late or lesser.
8) Anger, hurt, resentment
Someone hurt me deeply. How do I let go without becoming cold?
I feel angry at work and don’t know how to calm down.
Anger keeps taking over my mind.
I replay an insult and feel heat rising again and again.
I want to forgive, but part of me wants revenge.
I feel bitter toward someone who treated me unfairly.
How does the Gita help with anger?
I say things in anger and regret them later.
I want to keep dignity without becoming hard-hearted.
My anger is exhausting me.
I am holding resentment and don’t know how to release it.
What verse best helps with reactive anger?
I want to be strong without being harsh.
I feel hurt and defensive all the time.
I want guidance for handling provocation at work.
How do I respond without becoming reactive?
I feel consumed by what someone did to me.
I want to let go, but not excuse wrong.
Give me one verse for anger and explain why it fits.
I want a practical next step for resentment.
9) Moral conflict, responsibility, integrity
Two people I love want opposite things; I fear making the wrong choice morally.
I feel torn between compassion and responsibility.
I want to act with integrity, but I fear disappointing people I love.
I don’t know which duty should come first.
I am caught between loyalty and truth.
I fear doing the right thing because it may hurt others.
What does the Gita say about conflicting obligations?
I feel morally confused and don’t trust my own judgment.
I want one verse that helps me choose with clarity.
I am afraid of being misunderstood if I act honestly.
I want to do what is right, not just what is easy.
I feel burdened by the responsibility to choose.
I want a verse about duty and moral courage.
I keep postponing a necessary decision.
I fear the consequences of acting with integrity.
I need help separating duty from people-pleasing.
How do I act when every option causes pain?
I want to honor love without betraying truth.
I feel paralyzed by responsibility.
Give me a deeper answer with two verses on moral conflict.
10) Spiritual meta / instruction-following / product tests
Which specific verse best applies to my situation, and why?
Don’t give me generic motivation. Give me one verse and explain it clearly.
Give me guidance only from the Gita, not general self-help.
Give me a short answer with one practical next step.
Give me a deeper answer with two verses and a reflective explanation.
Give me one primary verse and one supporting verse.
Be compassionate, practical, and scripture-first.
Keep the answer brief, calm, and direct.
Explain the verse in plain modern English.
Give me only one paragraph and one next step.
Make the answer devotional in tone.
Make the answer philosophical in tone.
Make the answer sound like a wise counselor, not a motivational speaker.
Tell me why this verse fits better than the others.
Quote the verse reference clearly and correctly.
Do not sound preachy or judgmental.
Give me only Bhagavad Gita guidance with no outside ideas.
Give me an answer that feels emotionally safe and spiritually grounded.
Choose the clearest verse, not the most obscure one.
I want guidance that is compassionate, practical, and rooted in the Bhagavad Gita.
"""


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_path = root / "data" / "guidance_life_theme_review_queries.json"
    lines = [ln.strip() for ln in _RAW.splitlines() if ln.strip()]
    items: list[dict[str, str]] = []
    section = "misc"
    n = 0
    for ln in lines:
        if re.match(r"^\d+\)\s", ln):
            section = re.sub(r"^\d+\)\s*", "", ln).strip().lower()
            section = re.sub(r"[^\w\s-]", "", section).replace(" ", "_")[:48]
            continue
        n += 1
        items.append({"id": f"{section}_{n:03d}", "query": ln})
    doc = {
        "schema": "guidance_review_queries_v1",
        "description": "Life-theme prompts for verse routing / capture review.",
        "items": items,
    }
    out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} items to {out_path}")


if __name__ == "__main__":
    main()
