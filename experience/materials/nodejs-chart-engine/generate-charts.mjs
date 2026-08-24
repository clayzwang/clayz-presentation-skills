import fs from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const echarts = require("echarts/dist/echarts.min.js");
const sharp = require("sharp");

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, "data");
const outputDir = path.join(here, "generated");
// ECharts SSR writes this value into SVG attributes. A single family avoids
// quoted fallback lists that some libvips XML parsers reject.
const fontFamily = "Microsoft YaHei";

await fs.mkdir(outputDir, { recursive: true });

const readJson = async (name) => JSON.parse(await fs.readFile(path.join(dataDir, name), "utf8"));

async function writeChart(chart, stem, width, height) {
  const svg = chart.renderToSVGString();
  await fs.writeFile(path.join(outputDir, `${stem}.svg`), svg, "utf8");
  await sharp(Buffer.from(svg))
    .resize(width * 2, height * 2)
    .png()
    .toFile(path.join(outputDir, `${stem}.png`));
  chart.dispose();
}

async function renderOilSankey() {
  const data = await readJson("oil-2024.json");
  const width = 1120;
  const height = 390;
  const withAlpha = (hex, alpha) => {
    const red = Number.parseInt(hex.slice(1, 3), 16);
    const green = Number.parseInt(hex.slice(3, 5), 16);
    const blue = Number.parseInt(hex.slice(5, 7), 16);
    return `rgba(${red},${green},${blue},${alpha})`;
  };
  const producers = data.producers.map((row) => ({ ...row, name: `p_${row.code.toLowerCase()}` }));
  const consumers = data.consumers.map((row) => ({ ...row, name: `c_${row.code.toLowerCase()}` }));
  const nodes = [
    ...producers.map((row) => ({
      ...row,
      depth: 0,
      itemStyle: { color: row.color, borderWidth: 0 },
      label: { position: "left", align: "right", distance: 12 },
    })),
    {
      name: "global",
      display: "全球油品体系",
      metric: "两侧各归一化为 100%",
      depth: 1,
      itemStyle: { color: "#0F172A", borderWidth: 0 },
      label: { show: false },
    },
    ...consumers.map((row) => ({
      ...row,
      depth: 2,
      itemStyle: { color: row.color, borderWidth: 0 },
      label: { position: "right", align: "left", distance: 12 },
    })),
  ];
  const links = [
    ...producers.map((row) => ({
      source: row.name,
      target: "global",
      value: row.value,
      lineStyle: { color: withAlpha(row.color, 0.56), opacity: 1 },
    })),
    ...consumers.map((row) => ({
      source: "global",
      target: row.name,
      value: row.value,
      lineStyle: { color: withAlpha(row.color, 0.55), opacity: 1 },
    })),
  ];
  const chart = echarts.init(null, null, { renderer: "svg", ssr: true, width, height });
  chart.setOption({
    animation: false,
    backgroundColor: "transparent",
    series: [{
      type: "sankey",
      left: 230,
      right: 230,
      top: 12,
      bottom: 12,
      nodeWidth: 16,
      nodeGap: 15,
      nodeAlign: "justify",
      layoutIterations: 48,
      draggable: false,
      emphasis: { disabled: true },
      lineStyle: { curveness: 0.52 },
      label: {
        color: "#0F172A",
        fontFamily,
        formatter: ({ data: row }) => `{name|${row.display}}{metric|  ｜ ${row.metric}}`,
        rich: {
          name: { color: "#0F172A", fontFamily, fontSize: 13, fontWeight: 700, lineHeight: 20 },
          metric: { color: "#64748B", fontFamily: "Aptos", fontSize: 10, lineHeight: 20 },
        },
      },
      data: nodes,
      links,
    }],
  });
  await writeChart(chart, "oil-sankey", width, height);
}

async function renderAgeRadial() {
  const rows = await readJson("age-structure-2024.json");
  const width = 780;
  const height = 500;
  const highlights = new Set(["NER", "WLD", "CHN", "JPN"]);
  const rowByName = new Map(rows.map((row) => [row.country, row]));
  const item = (row, field, color) => ({
    value: Number(row[field].toFixed(4)),
    itemStyle: row.code === "WLD"
      ? { color, borderColor: "#0F172A", borderWidth: 1.5 }
      : { color, borderColor: "#F8FAFC", borderWidth: 1 },
  });
  const chart = echarts.init(null, null, { renderer: "svg", ssr: true, width, height });
  chart.setOption({
    animation: false,
    backgroundColor: "transparent",
    polar: { center: ["50%", "51%"], radius: ["26%", "72%"] },
    angleAxis: {
      type: "category",
      data: rows.map((row) => row.country),
      startAngle: 90,
      clockwise: true,
      boundaryGap: true,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: {
        interval: 0,
        hideOverlap: false,
        margin: 16,
        color: "#0F172A",
        fontFamily,
        formatter: (name) => {
          const row = rowByName.get(name);
          return row && highlights.has(row.code)
            ? `{hi|${name}}\n{val|65+ ${row.age65.toFixed(1)}%}`
            : `{country|${name}}`;
        },
        rich: {
          country: { color: "#334155", fontFamily, fontSize: 12, fontWeight: 600, lineHeight: 18 },
          hi: { color: "#0F172A", fontFamily, fontSize: 13, fontWeight: 700, lineHeight: 18 },
          val: { color: "#D95F59", fontFamily: "Aptos", fontSize: 10, fontWeight: 700, lineHeight: 14 },
        },
      },
    },
    radiusAxis: {
      min: 0,
      max: 100,
      interval: 25,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
      splitLine: { show: true, lineStyle: { color: "rgba(148,163,184,0.35)", width: 1 } },
    },
    series: [
      {
        name: "0–14岁",
        type: "bar",
        coordinateSystem: "polar",
        stack: "age",
        silent: true,
        barWidth: "84%",
        data: rows.map((row) => item(row, "age014", "#F2C14E")),
      },
      {
        name: "15–64岁",
        type: "bar",
        coordinateSystem: "polar",
        stack: "age",
        silent: true,
        barWidth: "84%",
        data: rows.map((row) => item(row, "age1564", "#2F7D8C")),
      },
      {
        name: "65岁+",
        type: "bar",
        coordinateSystem: "polar",
        stack: "age",
        silent: true,
        barWidth: "84%",
        data: rows.map((row) => item(row, "age65", "#D95F59")),
      },
    ],
  });
  await writeChart(chart, "age-radial", width, height);
}

await Promise.all([renderOilSankey(), renderAgeRadial()]);
console.log(`Generated ECharts SSR assets in ${outputDir}`);
