# Prototype 2 failure-mode probe (OBSERVED by Kylian, 2026-08-01)

Carried over from M3 and M2. For each method and level, does reference conditioning
**reduce**, **leave unchanged**, or **worsen** each failure mode? One of
`reduced` / `unchanged` / `worse` / `not observed`; a blank means it could not be judged.

This is a separate instrument from the rubric on purpose: these are presence/absence
observations about specific artefacts, not quality judgements on a 1-5 scale.

Recorded verbatim from the approved review. The authoritative record is
[`failure-mode-observations.csv`](failure-mode-observations.csv); nothing here is
inferred, and `not observed` is recorded as itself rather than as `reduced`.

## What each probe means

- **`repeated_elements`** - duplicated motifs, especially at 512x1536 (the open M3 observation)
- **`vertical_stretching`** - subjects stretched to fill the 1:3 deck format
- **`physical_deck_mockup`** - renders a photo of a skateboard instead of the artwork (the failure flagged in EXP-005 direct-1x1)
- **`unwanted_frame`** - a border or mount transferred from a framed reference scan
- **`pseudo_text`** - invented lettering transferred from a text-dominated reference
- **`background_transfer`** - the reference's background carried over wholesale

## C6, the difficult reference (`difficult-reference-artefacts.jpg`)

R5 is a landscape, framed, text-dominated WPA poster scan. **R1 shares the frame and
typography properties**, so C1 is worth checking for the same artefacts - R5 is the
harder case because it adds landscape orientation, not because it is the only framed
or text-bearing reference.

| method | level | repeated_elements | vertical_stretching | physical_deck_mockup | unwanted_frame | pseudo_text | background_transfer | notes |
|---|---|---|---|---|---|---|---|---|
| img2img | weak | not observed | not observed | not observed | not observed | not observed | not observed | prompt-led wolf graphic with little visible transfer. |
| img2img | medium | not observed | not observed | not observed | worse | worse | worse |  |
| img2img | strong | not observed | not observed | not observed | worse | worse | worse |  |
| ip-adapter | weak | worse | not observed | not observed | not observed | worse | not observed |  |
| ip-adapter | medium | not observed | not observed | not observed | worse | worse | worse |  |
| ip-adapter | strong | not observed | not observed | not observed | worse | worse | worse |  |

## EXP-013, the deck format (`deck-format-512x1536.jpg`)

`repeated_elements` and `vertical_stretching` are the open M3 observation at 512x1536;
this is the first evidence bearing on whether reference conditioning affects them.

| method | condition | repeated_elements | vertical_stretching | physical_deck_mockup | unwanted_frame | pseudo_text | background_transfer | notes |
|---|---|---|---|---|---|---|---|---|
| img2img | C1 | worse | not observed | not observed | worse | worse | worse |  |
| img2img | C2 | not observed | not observed | not observed | not observed | not observed | worse | near-copy / wholesale layout preservation. |
| img2img | C4 | not observed | not observed | not observed | not observed | not observed | worse | near-copy of the project-original reference. |
| ip-adapter | C1 | worse | unchanged | not observed | not observed | worse | not observed |  |
| ip-adapter | C2 | not observed | not observed | not observed | not observed | not observed | reduced |  |
| ip-adapter | C4 | not observed | worse | not observed | not observed | not observed | reduced |  |

## Relation to the open dataset findings

Whatever is observed here is **evidence**, not the mitigation decision. The dataset
mitigation for framed and text-heavy source material (crop pass vs negative prompting)
stays in **Prototype 4 / M6**, where training evidence will exist.
