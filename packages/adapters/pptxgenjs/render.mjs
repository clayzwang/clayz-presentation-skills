#!/usr/bin/env node
// SPDX-FileCopyrightText: 2026 clayz
// SPDX-License-Identifier: Apache-2.0
// Original Clayz adapter built against the public PptxGenJS API. No upstream
// source code, demos, templates, or media are copied into this repository.

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

function usage() {
  return `Usage: node render.mjs --acknowledge-upstream-risk <render-manifest.json> <output.pptx>

EXPERIMENTAL AND DISABLED BY DEFAULT.
The optional PptxGenJS 4.0.1 dependency currently brings an unpatched
image-size denial-of-service risk. See this directory's README before use.

This adapter blocks image and SVG objects and still requires explicit risk
acknowledgement. It does not replace final reopen/render QA.`;
}

function fail(message) {
  process.stderr.write(`error: ${message}\n`);
  process.exitCode = 2;
}

function cleanColor(value) {
  return typeof value === "string" ? value.replace(/^#/, "") : value;
}

function normalizeOptions(options, objectId) {
  const normalized = structuredClone(options || {});
  normalized.name = objectId;
  for (const key of ["color", "fill", "line"]) {
    if (typeof normalized[key] === "string") normalized[key] = cleanColor(normalized[key]);
    if (normalized[key] && typeof normalized[key] === "object" && "color" in normalized[key]) {
      normalized[key].color = cleanColor(normalized[key].color);
    }
  }
  return normalized;
}

function assertManifest(manifest) {
  if (!manifest || manifest.contract !== "io.clayz.presentation.render-manifest/1.0") {
    throw new Error("unsupported or missing render-manifest contract");
  }
  if (!manifest.presentation || !Array.isArray(manifest.slides) || manifest.slides.length === 0) {
    throw new Error("presentation and at least one slide are required");
  }
  const slideIds = new Set();
  const objectIds = new Set();
  for (const slide of manifest.slides) {
    if (!slide.slide_id || slideIds.has(slide.slide_id)) throw new Error("slide_id values must be unique and non-empty");
    slideIds.add(slide.slide_id);
    if (!Array.isArray(slide.objects)) throw new Error(`${slide.slide_id}: objects must be an array`);
    for (const object of slide.objects) {
      if (!object.object_id || objectIds.has(object.object_id)) throw new Error("object_id values must be globally unique and non-empty");
      objectIds.add(object.object_id);
    }
  }
}

async function addObject(pptx, slide, object) {
  const options = normalizeOptions(object.options, object.object_id);
  switch (object.type) {
    case "text":
      if (typeof object.text !== "string") throw new Error(`${object.object_id}: text is required`);
      slide.addText(object.text, options);
      return;
    case "shape": {
      const shapeType = pptx.ShapeType[object.shape];
      if (!shapeType) throw new Error(`${object.object_id}: unknown shape ${object.shape}`);
      slide.addShape(shapeType, options);
      return;
    }
    case "line":
      slide.addShape(pptx.ShapeType.line, options);
      return;
    case "table":
      if (!Array.isArray(object.rows)) throw new Error(`${object.object_id}: rows are required`);
      slide.addTable(object.rows, options);
      return;
    case "chart": {
      const chartType = pptx.ChartType[object.chart_type];
      if (!chartType) throw new Error(`${object.object_id}: unknown chart type ${object.chart_type}`);
      if (!Array.isArray(object.series)) throw new Error(`${object.object_id}: series are required`);
      slide.addChart(chartType, object.series, options);
      return;
    }
    case "image":
    case "svg":
      throw new Error(`${object.object_id}: image and SVG routes are security-blocked in v0.2.0`);
    default:
      throw new Error(`${object.object_id}: unsupported object type ${object.type}`);
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--help") || args.includes("-h")) {
    process.stdout.write(`${usage()}\n`);
    return;
  }
  if (args.length !== 3 || args[0] !== "--acknowledge-upstream-risk") {
    fail(usage());
    return;
  }
  const [manifestPath, outputPath] = args.slice(1).map((value) => path.resolve(value));
  const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
  assertManifest(manifest);
  let imported;
  try {
    imported = await import("pptxgenjs");
  } catch (error) {
    throw new Error(`optional dependency pptxgenjs is unavailable; installation is not recommended while the listed advisories remain unpatched (${error.message})`);
  }
  const PptxGenJS = imported.default;
  const pptx = new PptxGenJS();
  pptx.layout = manifest.presentation.layout;
  pptx.lang = manifest.presentation.language;
  for (const field of ["author", "company", "subject", "title"]) {
    if (manifest.presentation[field]) pptx[field] = manifest.presentation[field];
  }
  if (manifest.theme) pptx.theme = manifest.theme;

  for (const slideSpec of manifest.slides) {
    const slide = pptx.addSlide();
    slide.background = { color: cleanColor(slideSpec.background || "FFFFFF") };
    for (const object of slideSpec.objects) await addObject(pptx, slide, object);
    if (Array.isArray(slideSpec.speaker_notes) && typeof slide.addNotes === "function") {
      slide.addNotes(slideSpec.speaker_notes);
    }
  }
  await pptx.writeFile({ fileName: outputPath, compression: true });
  process.stdout.write(`wrote ${outputPath}\n`);
}

main().catch((error) => fail(error instanceof Error ? error.message : String(error)));
