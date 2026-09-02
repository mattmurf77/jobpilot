# Resume Generalization Guide — translating company-internal language

A guide for making every line of your resume legible to a recruiter who has never worked at your company. Pairs with `resume_line_menu.md` §0.5, where your own translation table lives (JobPilot reads that table and applies it to every bullet it selects).

---

## The principle, in one sentence

> *Your resume needs to tell a story about the kind of employee you are, to a stranger. Don't assume the first person screening your resume is as enmeshed in your industry, let alone your company, as you are.*

Three research findings drive this guide:

1. **Internal jargon damages how you appear to recruiters.** Resumes overloaded with company-specific abbreviations get rejected at the same rate as resumes with no specifics at all; both fail the 6-second recruiter scan.
2. **Industry-standard acronyms are fine; internal product codes are not.** A fintech recruiter knows `KYC`, `RICE`, and `CRO`. Nobody outside your company knows your internal product codes, team names, or program nicknames.
3. **Spell out on first use, then abbreviate.** Even industry-standard acronyms should be spelled out the first time they appear, with the abbreviation in parentheses.

---

## Classification framework

| Tier | What it means | Recommendation |
|---|---|---|
| **1. Universal** | A regular human in any industry understands it | Use as-is |
| **2. Industry-standard** | A recruiter in your target industry knows it on first read | Spell out on first use; abbreviation OK after |
| **3. Domain-niche** | Only known inside a sub-specialty of your industry | Spell out and add a one-word definition; risky outside the specialty |
| **4. Company-internal** | Only employees of your company know what this is | **Translate before submitting.** Never appears as-is on a resume going to an external recruiter |

---

## The decision tree

```
Is this term universally understood?          -> Yes -> Keep as-is
                                                 | No
Is it industry-standard in your target field? -> Yes -> Spell out on first use, abbreviate after
                                                 | No
Is it used at 3+ companies besides yours?     -> Yes -> Domain-niche; spell out + one-word definition
                                                 | No
                                              -> COMPANY-INTERNAL -> translate before shipping
```

---

## How to build your translation table

Audit every term in your line menu and sort it into the four tiers. For every Tier-4 term, write the external phrase a stranger would understand, then record the pair in `resume_line_menu.md` §0.5.2 using this row shape (JobPilot parses the quoted phrase in the last column):

| Internal term | What it is | Recommended generalized form |
|---|---|---|
| **ACME-Pro** | The company's flagship subscription product | "the flagship subscription product" |
| **Growth Pod** | A cross-functional squad name | "the growth team" |
| **Big Rocks** | The quarterly planning ritual | "quarterly planning" |

Rules of thumb for the replacement phrase:

- Describe the *thing*, not the name: "term-loan product for small businesses" beats a product code.
- Keep the scale signal: if the internal term implied size, carry the number into the translated bullet.
- Prefer the industry's own vocabulary so the translated line also mirrors JD keywords.
- Avoid stacking articles: if the replacement starts with "the", make sure the bullet doesn't already have one in front of it.

---

## Before / after

**Before:** *Migrated GML's intake from Smartsheet to a custom Jira project with 4 production automation rules.*

**After:** *Migrated the merchant-lending team's product intake from Smartsheet to a custom Jira project with 4 production automation rules, saving each PM 2-3 hours per week.*

What changed: the team code became a description, and the outcome the reader cares about moved into the sentence.

---

## When to keep internal terms (the exceptions)

1. **The application is internal** (internal mobility, internal recruiter). Jargon signals fluency.
2. **The application is to a direct competitor** with an overlapping product taxonomy. Still spell out on first use.
3. **A referral has pre-briefed the reader.** Even then, define abbreviations on first use.

For every other application, translate.

---

## Sources

- [Avoiding Company-Specific Lingo on Your Resume — Great Resumes Fast](https://greatresumesfast.com/blog/avoiding-company-specific-lingo-on-your-resume/)
- [Avoiding Jargon and Acronyms on Your Resume — Work It Daily](https://www.workitdaily.com/avoiding-jargon-acronyms-resume)
- [How Industry Jargon Can Weaken Your Resume — MarketSmiths](https://www.marketsmiths.com/2014/how-industry-jargon-can-weaken-your-resume/)
- [Resume Abbreviations: When & How to Use Them for Clarity — Enhancv](https://enhancv.com/blog/resume-abbreviations/)
- [Acronyms On Resume: How To List Industry-specific Acronyms — VisualCV](https://www.visualcv.com/acronyms-on-resume/)
- [What industry-specific jargon should be included on your resume? — LinkedIn Advice](https://www.linkedin.com/advice/1/what-industry-specific-jargon-should-included-your)
- [How to Handle NDA Constraints in Resumes & Interviews — Resumly](https://www.resumly.ai/blog/how-to-handle-nda-constraints-in-resumes-and-interviews)
