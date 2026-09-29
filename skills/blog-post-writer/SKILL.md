---
name: blog-post-writer
description: >
  Write a detailed, step-by-step ~1000-word educational blog post on any subject the user chooses.
  Always use this skill when the user asks to write a blog post, article, or tutorial — even if they
  just say "write me a post about X", "create a blog article", "make a tutorial on Y", or "I need
  content for my blog". The skill asks for the subject first (if not already given), writes a thorough
  how-to post in Hebrew with RTL formatting, fact-checks it against live web sources, self-grades
  quality, and rewrites until the post scores 8–10 out of 10. Use it proactively whenever blog,
  article, or tutorial content is needed.
---

# Blog Post Writer

You are writing a high-quality, educational blog post for the user's blog. The post must teach readers
how to accomplish something — it is always practical and instructional, not just informational.

**Language:** All posts are written in **Hebrew** with right-to-left (RTL) formatting.
**Voice:** Write as a knowledgeable human friend sharing their experience — warm, direct, slightly
personal. Not as a robot listing instructions.

---

## Step 1 — Get the Subject

If the user has not already told you the subject, ask them now:

> "על איזה נושא תרצה שאכתוב את הפוסט?"

Wait for their answer before proceeding.

---

## Step 2 — Research the Subject

Before writing, use web search to gather 3–5 reliable, up-to-date sources on the subject. Look for:
- Official documentation, authoritative guides, or well-known publications
- Current best practices and any recent changes (tools, versions, regulations, etc.)
- Real step-by-step workflows that practitioners actually use

Note the sources — you will cite them at the end and use them during fact-checking.

---

## Step 3 — Write the Blog Post

Write a blog post of approximately **1,000 words** in **Hebrew** (aim for 950–1,100 words).
The entire post — every word, heading, step, and source label — must be in Hebrew.

Use RTL markdown formatting:
- Place the `<div dir="rtl">` wrapper at the top and `</div>` at the bottom of the file so that
  any platform rendering the markdown displays it right-to-left.
- Headings, bullet points, and numbered lists all flow right-to-left.

### The Title — Make It Impossible to Ignore

The title is the single most important line in the entire post. A flat, descriptive title like
"מדריך להתקנת Git על Windows" will be scrolled past. A great title creates curiosity, hints at a
secret, or promises a surprise. Write **3 candidate titles**, then choose the strongest one.

Patterns that work well in Hebrew blogs:

- **Curiosity gap:** "הטעות שכמעט כולם עושים כשמתקינים Git בפעם הראשונה"
- **Counter-intuitive:** "למה הכלי שכולם מזלזלים בו הוא זה שיציל לך את הפרויקט"
- **Promise + intrigue:** "5 דקות שישנו את הדרך שבה אתה עובד עם קוד — לתמיד"
- **Relatable failure:** "שלוש שעות של בלבול, ואז מצאתי את הדרך הנכונה לעשות את זה"
- **Surprising fact:** "רוב המפתחים לא יודעים שה-Git שלהם מוגדר לא נכון"

Avoid generic titles like "מדריך ל-X", "הכל על X", or "איך להתקין X". Those titles say nothing
about *why* the reader should care or what they will discover.

The title goes at the very top of the post as an H1 (`# כותרת הפוסט`).

### Structure

> ⚠️ **CRITICAL — No visible section labels in the post output:**
> The names below (פתיחה מושכת, הקשר ורקע, סיכום, etc.) are **internal writing guides only**.
> **Never** write them as headings (`##`) or as bold labels in the post — readers must never see them.
> The post flows as natural prose. The ONLY headings allowed are:
> - `# כותרת הפוסט` (the main title, H1)
> - **Bold step labels** inside the steps section (e.g., **שלב 1: פתיחת Power Query**)
> - `## מקורות` (sources section only)

1. **Opening** (~100 words) — Hook the reader. Why does this topic matter? What will
   they be able to do after reading? Write as continuous prose immediately after the title.
   Speak directly to the reader ("אתה", "אתם"). No heading, no label.
2. **Background** (~100 words) — Brief context. What problem does this solve? Who is it for?
   Continues as prose — no heading, no label "הקשר ורקע".
3. **Steps** (~600 words) — The heart of the post. Each step gets a short **bold** Hebrew label
   (e.g., **שלב 1: ...**, **שלב 2: ...**) followed by:
   - Explanation of *what* to do AND *why* (don't just say "לחץ X" — explain what it achieves)
   - Warnings, tips, or common mistakes to avoid
   - Examples or short code snippets where helpful (code itself can stay in English/Latin)
4. **Conclusion** (~100 words) — Summarise what the reader accomplished and encourage
   next steps. Write as prose — no "סיכום" heading or label.
5. **`## מקורות`** — Only allowed section heading besides the title. List researched sources.
6. **חתימה (Author Footer)** — After the sources section, end the post with a horizontal
   rule and the author signature below. Before first use, the user replaces the bracketed
   parts with their own details; if the brackets are still there, ask the user for them
   instead of inventing a bio.

   ```
   ---
   [השם המלא שלך] הוא/היא [התפקיד שלך] ב-[שם החברה](https://[האתר-שלך]). [משפט הזמנה אחד, למשל להצטרף לקבוצה או לניוזלטר].
   ```

### Tone & Voice — Writing Like a Human

This is the most important stylistic requirement. The post must feel like it was written by a
real Israeli person who knows this topic well — not by an AI generating structured content.

To achieve this:
- **Start with a human moment.** Open with a brief personal anecdote, a relatable frustration,
  or a scenario the reader has probably experienced. E.g., "פעם ישבתי שעה מול שגיאה אחת שלא
  הצלחתי להבין מאיפה היא מגיעה. אחרי שפתרתי אותה, הבנתי שאם הייתי מכיר את הכלי הזה קודם —
  הייתי חוסך לעצמי הרבה כאב ראש."
- **Use conversational Hebrew.** Write the way an Israeli tech writer or blogger would — use
  everyday expressions, don't be overly formal. It's fine to use פה instead of כאן, בסדר גמור,
  or to occasionally address the reader informally ("שים לב", "תזכור").
- **Vary sentence length.** Mix short punchy sentences with longer explanatory ones. Monotone
  sentence rhythm is a telltale sign of AI writing.
- **Don't list everything.** In the intro and background sections, write flowing prose — not
  bullet points. Save structured lists for the steps section.
- **Include one small opinion or tip.** At some point in the post, share a genuine-sounding
  personal take: "לדעתי, זה אחד הצעדים שאנשים מדלגים עליו הכי הרבה — וזו בדיוק הסיבה שדברים
  משתבשים." This makes the post feel authored, not generated.
- **Avoid AI clichés.** Do NOT use phrases like "בעולם הדיגיטלי המתפתח", "בנוף הטכנולוגי של
  היום", "מדריך מקיף", "בוא נצלול", "ללא ספק", or any opener that sounds like an AI trying to
  sound professional. Just get to the point naturally.

---

## Step 4 — Fact-Check Against the Web

After writing the first draft, systematically verify the factual claims in the post:

1. Identify the key factual assertions (tool names, version numbers, commands, statistics, dates,
   procedures, regulations, etc.).
2. For each key claim, do a targeted web search or fetch the relevant page to confirm accuracy.
3. Correct any errors or outdated information in the draft before moving to grading.

Be honest — if something cannot be verified, soften the claim or note it as approximate.

---

## Step 5 — Grade the Post

After fact-checking, grade the post yourself on a scale of **1–10** using these criteria:

| קריטריון | מה לבדוק |
|---|---|
| **דיוק עובדתי** (2 נקודות) | כל העובדות אומתו, אין טענות מטעות |
| **עומק ופירוט** (2 נקודות) | שלבים מפורטים, דוגמאות, הסבר "למה" |
| **בהירות** (2 נקודות) | קל למעקב, זרימה לוגית |
| **קריאות ואנושיות** (1 נקודה) | נשמע כמו בן אדם אמיתי, לא כמו AI |
| **כותרת מסקרנת** (1 נקודה) | הכותרת יוצרת סקרנות, לא רק מתארת — קורא ירצה ללחוץ עליה |
| **אורך ושלמות** (2 נקודות) | 950–1,100 מילים, כל חמשת החלקים נוכחים |

Write a brief internal note (2–3 sentences in English) explaining your grade.
**Do not show this note to the user.**

---

## Step 6 — Rewrite If Needed

- If the grade is **8, 9, or 10**: proceed to Step 7 — the post is ready.
- If the grade is **7 or below**: rewrite the post, specifically addressing the weakest criteria.
  Then re-grade. Repeat until the post scores 8 or higher. You may iterate up to **3 times**.

Each rewrite must be a full replacement of the post, not minor edits. Pay special attention to the
"human voice" criterion — if a rewrite still sounds like AI, rethink the opening, inject more
personal tone, and vary the sentence rhythm more aggressively.

---

## Step 7 — Deliver the Post

1. Save the final post as a Markdown file named after the subject in Hebrew transliteration or
   English slug (e.g., `setup-git-windows.md`) in `/sessions/gallant-vibrant-thompson/mnt/outputs/`.
2. Tell the user (in Hebrew):
   - The final quality score (e.g., "ציון איכות: 9/10")
   - A one-line Hebrew summary of what the post covers
   - A clickable link to the file using `computer://` format

**Do not narrate your internal process to the user.** Just deliver the finished post with the score.

---

## Quick Reference Checklist

Before delivering, verif