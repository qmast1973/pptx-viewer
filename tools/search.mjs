// .pptx 슬라이드 글자 찾기 (화면 없이, 에이전트·시험용). 사용: node tools/search.mjs <파일.pptx> <찾을말>
// 출력: JSON [{slide(1부터), title, text}] — 화면의 찾기와 같은 기준(대소문자 무시, 띄어쓰기 그대로)
import { readFileSync } from "node:fs";
import { inflateRawSync } from "node:zlib";

function unzip(buf) {
  const files = {};
  let e = buf.length - 22;
  while (e >= 0 && buf.readUInt32LE(e) !== 0x06054b50) e--;
  if (e < 0) throw new Error("zip 이 아닙니다 (.pptx 가 맞는지 확인)");
  let p = buf.readUInt32LE(e + 16);
  for (let n = buf.readUInt16LE(e + 10); n > 0; n--) {
    const method = buf.readUInt16LE(p + 10), size = buf.readUInt32LE(p + 20);
    const nameLen = buf.readUInt16LE(p + 28), extra = buf.readUInt16LE(p + 30), comment = buf.readUInt16LE(p + 32);
    const local = buf.readUInt32LE(p + 42), name = buf.toString("utf8", p + 46, p + 46 + nameLen);
    const start = local + 30 + buf.readUInt16LE(local + 26) + buf.readUInt16LE(local + 28);
    const raw = buf.subarray(start, start + size);
    files[name] = method === 8 ? inflateRawSync(raw) : raw;
    p += 46 + nameLen + extra + comment;
  }
  return files;
}

const unxml = (s) => s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, "&");
const texts = (xml) => [...xml.matchAll(/<a:p>([\s\S]*?)<\/a:p>/g)]
  .map((m) => [...m[1].matchAll(/<a:t>([^<]*)<\/a:t>/g)].map((t) => unxml(t[1])).join("")).filter(Boolean);

const [file, ...q] = process.argv.slice(2);
if (!file || !q.length) { console.error("사용: node tools/search.mjs <파일.pptx> <찾을말>"); process.exit(2); }
const query = q.join(" ").toLowerCase();
const files = unzip(readFileSync(file));
const rels = files["ppt/_rels/presentation.xml.rels"].toString();
const target = Object.fromEntries([...rels.matchAll(/Id="([^"]+)"[^>]*Target="([^"]+)"|Target="([^"]+)"[^>]*Id="([^"]+)"/g)]
  .map((m) => [m[1] || m[4], m[2] || m[3]]));
const order = [...files["ppt/presentation.xml"].toString().matchAll(/<p:sldId [^>]*r:id="([^"]+)"/g)].map((m) => "ppt/" + target[m[1]].replace(/^\//, "").replace(/^ppt\//, ""));
const out = [];
order.forEach((path, i) => {
  const lines = texts(files[path]?.toString() || "");
  const hit = lines.filter((l) => l.toLowerCase().includes(query));
  if (hit.length) out.push({ slide: i + 1, title: lines[0] || "", text: hit });
});
console.log(JSON.stringify({ file, query, slides: order.length, hits: out }, null, 1));
