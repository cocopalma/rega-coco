const B = "http://localhost:8000/functions/v1/dados-rega";
const H = { authorization: "Bearer tok-dalmar", "content-type": "application/json" };
const call = async (name: string, args: any) => (await (await fetch(B + "/mcp", { method: "POST", headers: H, body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name, arguments: args } }) })).json()).result;
const tl = (await (await fetch(B + "/mcp", { method: "POST", headers: H, body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list" }) })).json()).result.tools;
console.log("ferramentas:", tl.map((t: any) => t.name).join(","), "tipos:", tl[0].inputSchema.properties.tipo.enum.length);
for (const tipo of ["rondas","cumprimento","meta","tempos","tempos_campos","chegadas","nunca_agua","plantas_vivas","constrangimentos","planos","percursos","limites"]) {
  const r = await call("ler_dados", { tipo, de: "2026-11-12", ate: "2026-11-12" });
  const o = JSON.parse(r.content[0].text);
  console.log(tipo, r.isError ? "ERRO " + r.content[0].text : `total=${o.total} extra=${!!o.extra} 1.ª=${JSON.stringify(o.linhas[0]).slice(0, 230)}`);
}
console.log("filtro meta Macala:", JSON.parse((await call("ler_dados", { tipo: "meta", de: "2026-11-12", comunidade: "macala" })).content[0].text).total);
console.log("filtro limites equipa alafo:", JSON.parse((await call("ler_dados", { tipo: "limites", equipa: "alafo" })).content[0].text).total);
console.log("percursos 2 dias:", (await call("ler_dados", { tipo: "percursos", de: "2026-11-11", ate: "2026-11-12" })).content[0].text);
console.log("cumprimento sem acesso:", (await call("ler_dados", { tipo: "cumprimento", de: "2026-01-01", ate: "2026-01-01" })).content[0].text);
const g = (await call("link_geojson", { tipo: "percursos", dia: "2026-11-12" })).content[0].text; console.log(g.slice(0, 90));
const gl = await (await fetch(g.match(/https?:\S+/)![0])).json(); console.log("geojson percursos:", JSON.stringify(gl).slice(0, 400));
const g2 = (await call("link_geojson", { tipo: "limites" })).content[0].text;
const gl2 = await (await fetch(g2.match(/https?:\S+/)![0])).json(); console.log("geojson limites:", gl2.features.length, JSON.stringify(gl2.features[0].geometry));
const x = (await call("link_excel", { de: "2026-11-12", ate: "2026-11-12" })).content[0].text;
const xr = await fetch(x.match(/https?:\S+/)![0]); const buf = new Uint8Array(await xr.arrayBuffer()); console.log("excel", xr.status, buf.length);
const XLSX = await import("npm:xlsx@0.18.5"); const wb = XLSX.read(buf); console.log(wb.SheetNames.join(" | "));
console.log(JSON.stringify(XLSX.utils.sheet_to_json(wb.Sheets["Limites dos campos"])[0]));
console.log(JSON.stringify(XLSX.utils.sheet_to_json(wb.Sheets["Percursos GPS (resumo)"])[0]));
// geo token can't be used as excel
const tg = g.match(/t=([^\s]+)/)![1]; console.log("geo token no excel:", (await fetch(B + "/excel?t=" + tg)).status);
const tx = x.match(/t=([^\s]+)/)![1]; console.log("excel token no geo:", (await fetch(B + "/geojson?t=" + tx)).status);
console.log("existente regas ok:", JSON.parse((await call("ler_dados", { tipo: "regas", de: "2026-11-12" })).content[0].text).total);

const f1 = await call("ver_foto", { ref: "rega-fotos/u/ok.jpg" }); console.log("foto permitida:", !f1.isError);
const f2 = await call("ver_foto", { ref: "rega-fotos/u/outra.jpg" }); console.log("foto recusada:", f2.isError, f2.content[0].text);
const lote = Array.from({ length: 21 }, (_, i) => ({ jsonrpc: "2.0", id: i, method: "ping" }));
const rl = await fetch(B + "/mcp", { method: "POST", headers: H, body: JSON.stringify(lote) }); console.log("lote de 21:", rl.status);
const lote2 = Array.from({ length: 3 }, (_, i) => ({ jsonrpc: "2.0", id: i, method: "ping" }));
console.log("lote de 3:", (await fetch(B + "/mcp", { method: "POST", headers: H, body: JSON.stringify(lote2) })).status);
const tx2 = x.match(/t=([^\s]+)/)![1]; const mal = tx2.slice(0, -2) + (tx2.endsWith("AA") ? "BB" : "AA");
console.log("assinatura alterada:", (await fetch(B + "/excel?t=" + mal)).status);
