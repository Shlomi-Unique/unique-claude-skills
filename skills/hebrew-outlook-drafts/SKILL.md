---
name: hebrew-outlook-drafts
description: Create Hebrew email drafts in Outlook that display right-to-left in desktop Outlook. Use whenever creating one or more Hebrew email drafts for the user through the Microsoft 365 (Outlook) connector — personal outreach, follow-ups, replies, bulk personalized drafts from an Excel list. The connector rejects dir/style attributes, so drafts show left-to-right in desktop Outlook; this skill fixes all of them in one pass with a local Outlook script. Triggers on "תכין טיוטות", "טיוטה ב-Outlook", "מיילים אישיים", "draft emails in Hebrew".
---

# Hebrew drafts in Outlook, right-to-left

The Microsoft 365 connector (`outlook_create_draft`) accepts only plain HTML tags: no `dir`, no `style`. Drafts look fine in Outlook on the web, but desktop Outlook shows them left-to-right. The fix runs locally through the Outlook installed on this Windows PC (COM), which has no such limit.

## Steps

1. **Tag the batch.** Give every draft in this batch a short marker in the subject that appears in all of them and in no other draft (for test runs: `[הדגמה]`; for real outreach ask the user, or use a word that is in every subject of this batch). Never use a marker that could match the user's other drafts.
2. **Create the drafts** with `outlook_create_draft`, `bodyType: "html"`, plain `<p>` paragraphs only (no `dir`, `style`, `class`, `span`). Never send.
3. **Fix them in one run** (PowerShell, from any folder):
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\skills\hebrew-outlook-drafts\scripts\fix-rtl-drafts.ps1" -SubjectContains "<marker>"
   ```
   It goes over the Drafts folder of every account in Outlook, and only for drafts whose subject contains the marker: sets every paragraph right-to-left, right-aligned, Arial. Drafts already fixed are skipped, so re-running is safe. It prints each fixed subject and a final count.
4. **Report** to the user: the count fixed, and a table of name, subject and the `webLink` of each draft.

## Notes
- Requires Windows with classic desktop Outlook installed and open or openable. If the script fails (no Outlook, COM blocked), say so and fall back to telling the user to run the `rtl-arial-signature` skill per draft.
- The script file is saved with a UTF-8 BOM so Windows PowerShell 5.1 reads the Hebrew default correctly. Keep it that way if you edit it.
- The user's Outlook signature is not added. Tell the user to add it (Insert → Signature) or use `rtl-arial-signature`.
- Do not show the user's mailbox on a shared screen: the `webLink` opens a single draft in the browser without the folder list.
