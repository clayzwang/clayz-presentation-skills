# Content-Aware Composition

Use this route when a slide is led by a photograph, screenshot, illustration, product render, or another image-like canvas. The canvas is evidence with internal structure, not empty wallpaper.

## Read the canvas before placing text

Record four kinds of evidence before choosing a layout:

1. **Subject protection zones**: faces, products, interface controls, annotations, or other regions that must remain legible and uncropped.
2. **Candidate placement zones**: areas that can carry specific copy roles at the real text footprint. Blank-looking pixels are not automatically safe.
3. **Transition and contrast risks**: busy edges, tonal changes, depth boundaries, and local colors that may damage readability.
4. **Directional flow**: gaze, motion, perspective, object orientation, and visual vectors that can lead attention toward or away from the message.

The result belongs in the slide's `content_aware_canvas` contract. It must name the evidence basis and the copy IDs supported by each candidate zone.

## Compose relations, not positions

Derive the page from the current communication job and semantic layout tree:

- place the proposition where the canvas can support its role, not where a remembered template put a headline;
- preserve evidence before filling space;
- use crop, repositioning, local scrims, or a local support surface only when the chosen zone cannot meet contrast requirements naturally;
- couple text with the subject through gaze, motion, alignment, proximity, or semantic anchoring when that relation is useful;
- keep overlays local. A full card panel is not the default answer to a difficult image.

The same source image may lead to different compositions for a decision page, a diagnosis page, and a training page. This is expected: the method fixes the questions to ask, not the coordinates to use.

## High-risk handling

Create two real crop-and-composition prototypes when the subject competes with the title, text crosses a high-variance region, directional flow conflicts with reading order, or the only apparent solution is a large overlay panel. Candidates must differ structurally, not only by crop percentage or tint.

Inspect the rendered prototypes at full slide size. Automated saliency, overlap, or contrast signals may point to a risk but may not select the winner.

## Research and rights boundary

The observation vocabulary is informed by content-aware poster-layout research, including PosterLayout, Scan-and-Print, CreatiPoster, and PosterO. Clayz independently expresses a presentation-specific decision contract. It does not redistribute their code, models, datasets, annotations, figures, layouts, or media. Exact reviews and thanks are recorded in `provenance/manifest.yaml`.

Do not copy a published poster, recover its layout coordinates, or train on unlicensed samples. Retrieve only sources allowed by the configured provider and record their provenance.
