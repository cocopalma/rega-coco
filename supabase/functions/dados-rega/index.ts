import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";
import * as XLSX from "npm:xlsx@0.18.5";

// Endereço SÓ DE LEITURA dos dados da Rega Coco e conector (MCP) para o Claude (13/11/2026, Valdo).
// Para quem tem uma chave (tabela api_chaves; o Valdo cria-a no SQL Editor: select api_criar_chave('Nome');).
// Não escreve nada nos dados da rega. Só lê pela função api_dados, regista cada pedido em api_acessos e
// assina links das fotografias (1 h). Telefones, utilizadores, senhas, PIN e código ficam de fora.
//   Conector (Claude):   POST .../functions/v1/dados-rega/k/<chave>/mcp
//   Dados (navegador):   GET  .../k/<chave>/dados/<tipo>?de=AAAA-MM-DD&ate=AAAA-MM-DD[&comunidade=][&equipa=][&formato=csv]
//   Excel:               GET  .../k/<chave>/excel?de=&ate=     (ou o link de 1 h que o conector devolve)
//   Fotografia:          GET  .../k/<chave>/foto?ref=<bucket/caminho>

const TIPOS = ["resumo", "regas", "equipas", "dias_sem_rega", "campos", "recontagens", "manutencao", "acompanhamentos",
  "queimadas", "chuva", "monitorias", "idas_agua"] as const;
const BUCKETS = ["rega-fotos", "recontagem-fotos", "manutencao-fotos", "chuva-fotos", "monitoria-fotos"];
const MAX_DIAS = 92;
const VERSAO = "1.0";

function encodeBase64(u: Uint8Array) {
  let s = "";
  for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode(...u.subarray(i, i + 0x8000));
  return btoa(s);
}

const url = Deno.env.get("SUPABASE_URL")!;
const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const admin = createClient(url, service, { auth: { persistSession: false } });

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, content-type, mcp-protocol-version, mcp-session-id",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};
const json = (status: number, body: unknown, extra: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json; charset=utf-8", ...extra } });

const hojeMaputo = () => new Date(Date.now() + 2 * 3600e3).toISOString().slice(0, 10);
const RE_DATA = /^\d{4}-\d{2}-\d{2}$/;

function periodo(tipo: string, de?: string, ate?: string) {
  if (tipo === "campos") return { de: null, ate: null };
  const h = hojeMaputo();
  const d = de || ate || h, a = ate || de || h;
  if (!RE_DATA.test(d) || !RE_DATA.test(a)) throw new Erro(400, "Datas no formato AAAA-MM-DD");
  if (a < d) throw new Erro(400, "'ate' é antes de 'de'");
  const dias = (Date.parse(a) - Date.parse(d)) / 864e5 + 1;
  if (dias > MAX_DIAS) throw new Erro(400, `Período de no máximo ${MAX_DIAS} dias`);
  return { de: d, ate: a };
}

class Erro extends Error {
  constructor(public status: number, msg: string) { super(msg); }
}

async function dados(tipo: string, de?: string, ate?: string, comunidade?: string, equipa?: string) {
  if (!TIPOS.includes(tipo as any)) throw new Erro(400, "Tipo desconhecido. Tipos: " + TIPOS.join(", "));
  const p = periodo(tipo, de, ate);
  const { data, error } = await admin.rpc("api_dados", {
    p_tipo: tipo, p_de: p.de, p_ate: p.ate, p_comunidade: comunidade || null, p_equipa: equipa || null,
  });
  if (error) throw new Erro(500, "Erro ao ler os dados");
  return { periodo: p, dados: data };
}

// ---------- tabelas planas para Excel / CSV ----------
function plano(r: any) {
  const o: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(r)) {
    if (k === "constrangimentos" && Array.isArray(v)) {
      o[k] = v.map((c: any) => `${c.tipo}${c.plantas != null ? ` (${c.plantas})` : ""}${c.descricao ? ": " + c.descricao : ""}`).join("; ");
    } else if (k === "fotos" && v && typeof v === "object") {
      for (const [f, ref] of Object.entries(v as any)) o["foto_" + f] = ref;
    } else if (v && typeof v === "object") o[k] = JSON.stringify(v);
    else o[k] = v;
  }
  return o;
}
const FOLHAS: [string, string][] = [["regas", "Regas"], ["equipas", "Equipas por dia"], ["dias_sem_rega", "Dias sem rega"],
  ["campos", "Campos"], ["recontagens", "Recontagens"], ["manutencao", "Manutenção"], ["acompanhamentos", "Acompanhamentos"],
  ["queimadas", "Queimadas"], ["chuva", "Chuva"], ["monitorias", "Monitorias"], ["idas_agua", "Idas à água"]];

async function excel(de?: string, ate?: string, comunidade?: string, equipa?: string) {
  const wb = XLSX.utils.book_new();
  const p = periodo("regas", de, ate);
  const res = await dados("resumo", p.de!, p.ate!);
  const leia = [
    ["Rega Coco — dados da app (só leitura)"],
    ["Período", `${p.de} a ${p.ate}`], ["Gerado em (Maputo)", new Date(Date.now() + 2 * 3600e3).toISOString().slice(0, 16).replace("T", " ")],
    comunidade ? ["Comunidade", comunidade] : [], equipa ? ["Equipa", equipa] : [],
    [], ["Notas"],
    ["Horas e datas de Maputo. As regas de teste não entram."],
    ["Ritmo = plantas regadas ÷ (pessoas × horas de rega, da chegada da água à saída; sem água marcada, da entrada)."],
    ["Espera = entrada no campo → chegada da água (min)."],
    ["Campos: lista completa (na rega e retirados), não depende do período."],
    ["Manutenção: cava-roda e mulching são o total de plantas do campo com cada actividade nesse registo."],
    ["Fotografias: a coluna tem a referência; o conector do Claude (ver_foto) mostra-a."],
    [], ["Resumo do período"],
    ...Object.entries(res.dados as any).filter(([k]) => k !== "nota" && k !== "periodo")
      .map(([k, v]) => [k, typeof v === "object" ? JSON.stringify(v) : v]),
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(leia), "Leia-me");
  let linhas = 0;
  for (const [tipo, nome] of FOLHAS) {
    const r = await dados(tipo, p.de!, p.ate!, comunidade, equipa);
    const rows = (r.dados as any[]).map(plano);
    linhas += rows.length;
    XLSX.utils.book_append_sheet(wb, rows.length ? XLSX.utils.json_to_sheet(rows) : XLSX.utils.aoa_to_sheet([["Sem registos no período"]]), nome);
  }
  const buf = XLSX.write(wb, { type: "array", bookType: "xlsx" });
  return { buf, linhas, nome: `Rega_Coco_dados_${p.de!.replaceAll("-", "")}_a_${p.ate!.replaceAll("-", "")}.xlsx` };
}

function csv(rows: any[]) {
  const pl = rows.map(plano);
  const cols = [...new Set(pl.flatMap((r) => Object.keys(r)))];
  const esc = (v: unknown) => v == null ? "" : /[";\n]/.test(String(v)) ? `"${String(v).replaceAll('"', '""')}"` : String(v);
  return "﻿" + [cols.join(";"), ...pl.map((r) => cols.map((c) => esc(r[c])).join(";"))].join("\n");
}

// ---------- fotografias ----------
function refValida(ref: string) {
  const i = ref.indexOf("/");
  const b = ref.slice(0, i), c = ref.slice(i + 1);
  if (i < 1 || !BUCKETS.includes(b) || !c || c.includes("..") || !/^[\w\-./]+\.(jpg|jpeg|png)$/i.test(c)) throw new Erro(400, "Referência de fotografia inválida");
  return { b, c };
}
async function linkFoto(ref: string) {
  const { b, c } = refValida(ref);
  const { data, error } = await admin.storage.from(b).createSignedUrl(c, 3600);
  if (error || !data) throw new Erro(404, "Fotografia não encontrada");
  return data.signedUrl;
}
async function bytesFoto(ref: string) {
  const { b, c } = refValida(ref);
  const { data, error } = await admin.storage.from(b).download(c);
  if (error || !data) throw new Erro(404, "Fotografia não encontrada");
  return new Uint8Array(await data.arrayBuffer());
}

// ---------- link do Excel sem a chave (válido 1 h) ----------
const enc = new TextEncoder();
const b64u = (u: Uint8Array) => encodeBase64(u).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
async function hmac(txt: string) {
  const k = await crypto.subtle.importKey("raw", enc.encode("dados-rega:" + service), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return b64u(new Uint8Array(await crypto.subtle.sign("HMAC", k, enc.encode(txt))));
}
async function tokenExcel(chave: string, q: Record<string, string | undefined>) {
  const corpo = b64u(enc.encode(JSON.stringify({ c: chave, e: Math.floor(Date.now() / 1000) + 3600, ...q })));
  return corpo + "." + (await hmac(corpo));
}
async function lerToken(t: string) {
  const [corpo, ass] = (t || "").split(".");
  if (!corpo || ass !== (await hmac(corpo))) return null;
  const o = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(corpo.replaceAll("-", "+").replaceAll("_", "/")), (ch) => ch.charCodeAt(0))));
  return o.e > Date.now() / 1000 ? o : null;
}

// ---------- MCP ----------
const DESC_TIPOS = `Tipos:
- resumo: totais do período (campos e plantas na rega, regas, plantas regadas, campos regados, equipas-dia com rega, dias sem rega por motivo).
- regas: uma linha por rega real: data, campo (PR-n), produtor, comunidade, equipa (activista), técnico, supervisor, quem registou, ronda, entrada, chegada da água, saída, espera_min, duracao_rega_min, plantas regadas, pessoas, ritmo (plantas por pessoa por hora), plantas vivas na base, campo fechado ou por terminar, constrangimentos, alertas e motivos, GPS, referências das fotografias (entrada, rega, saída).
- equipas: uma linha por equipa e dia de trabalho (segunda a sábado): pessoas, início do dia, ida à água, chegada ao 1.º campo, saída do último, regas, plantas, motivo de dia sem rega.
- dias_sem_rega: motivos (tuk_tuk, avaria_tuk_tuk, avaria_camiao, sem_agua, chuva, material, equipa, regou_sem_registo, outro), descrição, quem registou e confirmou, fotografia.
- campos: lista completa (na rega e retirados, com data e motivo), plantas, coordenadas, regas na app e no WhatsApp. Não usa o período.
- recontagens: pedidos de recontagem das plantas, oficial, vivas e mortas contadas, validação, fotografias (declaração e campo).
- manutencao: registos de cava-roda e mulching (Quiwia e Farol): totais do campo, sazonais, fotografia.
- acompanhamentos: regas acompanhadas por técnicos e supervisores, com fotografia.
- queimadas: plantas afectadas e mortas, fotografia.
- chuva: leituras dos pluviómetros (mm), fotografia.
- monitorias: verificações por amostragem (solo húmido, nota, vivas/secas/mortas), fotografia.
- idas_agua: quando cada equipa foi buscar água.`;

const FERRAMENTAS = [
  {
    name: "ler_dados",
    description: "Lê os dados da app de rega Rega Coco (Projeto de Desenvolvimento da Cadeia de Valor do Coco, Palma). Só leitura. " +
      "Datas e horas de Maputo; regas de teste não entram. Período até 92 dias (sem período = hoje). Respostas em páginas: use 'pagina' e 'colunas' para ler menos. " +
      "Para muitos dados de uma vez use link_excel.\n" + DESC_TIPOS,
    inputSchema: {
      type: "object",
      properties: {
        tipo: { type: "string", enum: TIPOS },
        de: { type: "string", description: "AAAA-MM-DD" },
        ate: { type: "string", description: "AAAA-MM-DD" },
        comunidade: { type: "string", description: "Filtrar por comunidade (nome exacto, sem maiúsculas)" },
        equipa: { type: "string", description: "Filtrar por equipa (parte do nome do activista)" },
        colunas: { type: "array", items: { type: "string" }, description: "Só estas colunas (ex.: [\"data\",\"equipa\",\"plantas_regadas\",\"ritmo_plantas_pessoa_hora\"])" },
        pagina: { type: "integer", minimum: 1, description: "Página (1 = primeira)" },
        por_pagina: { type: "integer", minimum: 1, maximum: 500, description: "Linhas por página (por defeito 100)" },
      },
      required: ["tipo"],
    },
    annotations: { readOnlyHint: true },
  },
  {
    name: "ver_foto",
    description: "Mostra uma fotografia da app (rega, recontagem, dia sem rega, acompanhamento, queimada, chuva, monitoria, manutenção) a partir da referência que vem nos dados (ex.: 'rega-fotos/…/….jpg'). Devolve a imagem e um link válido por 1 hora.",
    inputSchema: { type: "object", properties: { ref: { type: "string" } }, required: ["ref"] },
    annotations: { readOnlyHint: true },
  },
  {
    name: "link_excel",
    description: "Devolve um link (válido 1 hora) para descarregar um Excel com todos os dados do período (Leia-me com o resumo, Regas, Equipas por dia, Dias sem rega, Campos, Recontagens, Manutenção, Acompanhamentos, Queimadas, Chuva, Monitorias, Idas à água). Período até 92 dias; sem período = hoje.",
    inputSchema: {
      type: "object",
      properties: { de: { type: "string" }, ate: { type: "string" }, comunidade: { type: "string" }, equipa: { type: "string" } },
    },
    annotations: { readOnlyHint: true },
  },
];

const INSTRUCOES = "Dados da app de rega Rega Coco (só leitura). Comece por ler_dados com tipo 'resumo' para o período pedido; " +
  "use 'equipas' para o dia de cada equipa e 'regas' para o detalhe. Não invente números: se um dado não vem nas respostas, diga que falta.";

async function chamarFerramenta(nome: string, a: any, base: string, chaveId: string) {
  if (nome === "ler_dados") {
    const r = await dados(a.tipo, a.de, a.ate, a.comunidade, a.equipa);
    if (!Array.isArray(r.dados)) return { conteudo: [{ type: "text", text: JSON.stringify(r) }], linhas: 1 };
    const por = Math.min(Math.max(Number(a.por_pagina) || 100, 1), 500), pag = Math.max(Number(a.pagina) || 1, 1);
    let linhas = (r.dados as any[]).slice((pag - 1) * por, pag * por);
    if (Array.isArray(a.colunas) && a.colunas.length) linhas = linhas.map((x) => Object.fromEntries(a.colunas.filter((c: string) => c in x).map((c: string) => [c, x[c]])));
    const total = (r.dados as any[]).length;
    const out = { tipo: a.tipo, periodo: r.periodo, total, pagina: pag, por_pagina: por, paginas: Math.ceil(total / por), linhas };
    return { conteudo: [{ type: "text", text: JSON.stringify(out) }], linhas: linhas.length };
  }
  if (nome === "ver_foto") {
    const ref = String(a.ref || "");
    const [bytes, link] = [await bytesFoto(ref), await linkFoto(ref)];
    const mime = /\.png$/i.test(ref) ? "image/png" : "image/jpeg";
    return { conteudo: [{ type: "image", data: encodeBase64(bytes), mimeType: mime }, { type: "text", text: `Link (válido 1 hora): ${link}` }], linhas: 1 };
  }
  if (nome === "link_excel") {
    const p = periodo("regas", a.de, a.ate);
    const t = await tokenExcel(chaveId, { de: p.de!, ate: p.ate!, comunidade: a.comunidade, equipa: a.equipa });
    return { conteudo: [{ type: "text", text: `Excel de ${p.de} a ${p.ate} (link válido 1 hora): ${base}/excel?t=${t}` }], linhas: 0 };
  }
  throw new Erro(400, "Ferramenta desconhecida");
}

async function mcp(msg: any, base: string, chave: any, reg: (accao: string, param: unknown, linhas: number, estado: number) => Promise<void>) {
  const { id, method, params } = msg || {};
  const ok = (result: unknown) => ({ jsonrpc: "2.0", id, result });
  const err = (code: number, message: string) => ({ jsonrpc: "2.0", id, error: { code, message } });
  if (method === "initialize") {
    await reg("initialize", null, 0, 200);
    return ok({
      protocolVersion: params?.protocolVersion || "2025-06-18",
      capabilities: { tools: { listChanged: false } },
      serverInfo: { name: "rega-coco-dados", title: "Rega Coco — dados da rega (só leitura)", version: VERSAO },
      instructions: INSTRUCOES,
    });
  }
  if (method === "ping") return ok({});
  if (method === "tools/list") { await reg("tools/list", null, 0, 200); return ok({ tools: FERRAMENTAS }); }
  if (method === "resources/list") return ok({ resources: [] });
  if (method === "prompts/list") return ok({ prompts: [] });
  if (method === "tools/call") {
    const nome = params?.name, a = params?.arguments || {};
    try {
      const r = await chamarFerramenta(nome, a, base, chave.id);
      await reg(nome, a, r.linhas, 200);
      return ok({ content: r.conteudo });
    } catch (e) {
      const st = e instanceof Erro ? e.status : 500;
      await reg(nome, a, 0, st);
      return ok({ content: [{ type: "text", text: e instanceof Erro ? e.message : "Erro" }], isError: true });
    }
  }
  if (id === undefined || id === null) return null; // notificações
  return err(-32601, "Método não suportado");
}

// ---------- pedido ----------
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const t0 = Date.now();
  const u = new URL(req.url);
  const partes = u.pathname.split("/").filter(Boolean);
  const i = partes.indexOf("dados-rega");
  const resto = partes.slice(i + 1);
  const ip = (req.headers.get("x-forwarded-for") || "").split(",")[0].trim() || null;
  const agente = req.headers.get("user-agent");
  const q = (k: string) => u.searchParams.get(k) || undefined;
  const base = `${url}/functions/v1/dados-rega`;

  // link do Excel com token (sem a chave)
  let chaveTxt: string | null = null, via = "http", accao = "";
  let chave: any = null;
  if (resto[0] === "excel" && q("t")) {
    const tk = await lerToken(q("t")!);
    if (!tk) return json(401, { erro: "Link expirado ou inválido. Peça um link novo ao conector." });
    const { data: c } = await admin.from("api_chaves").select("id,nome,limite_hora,activa").eq("id", tk.c).maybeSingle();
    if (!c?.activa) return json(401, { erro: "Chave desligada" });
    chave = { id: c.id, nome: c.nome };
    try {
      const x = await excel(tk.de, tk.ate, tk.comunidade, tk.equipa);
      await admin.rpc("api_registar", { p_chave: c.id, p_ip: ip, p_agente: agente, p_via: "link", p_accao: "excel",
        p_param: { de: tk.de, ate: tk.ate, comunidade: tk.comunidade, equipa: tk.equipa }, p_linhas: x.linhas, p_ms: Date.now() - t0, p_estado: 200 });
      return new Response(x.buf, { headers: { ...cors, "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": `attachment; filename="${x.nome}"` } });
    } catch (e) {
      return json(e instanceof Erro ? e.status : 500, { erro: e instanceof Erro ? e.message : "Erro" });
    }
  }

  if (resto[0] === "k" && resto[1]) { chaveTxt = resto[1]; accao = resto[2] || ""; }
  else {
    chaveTxt = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "") || null;
    accao = resto[0] || "";
  }
  if (accao === "mcp") via = "mcp";

  const reg = async (a: string, param: unknown, linhas: number, estado: number) => {
    await admin.rpc("api_registar", { p_chave: chave?.id || null, p_ip: ip, p_agente: agente, p_via: via, p_accao: a,
      p_param: param ?? null, p_linhas: linhas, p_ms: Date.now() - t0, p_estado: estado });
  };

  const { data: v } = await admin.rpc("api_validar", { p_chave: chaveTxt || "" });
  if (!v) { await reg(accao || "(sem acção)", null, 0, 401); return json(401, { erro: "Chave inválida" }); }
  chave = v;
  if (v.pedidos_hora >= v.limite) { await reg(accao, null, 0, 429); return json(429, { erro: "Demasiados pedidos nesta hora. Tente mais tarde." }); }

  try {
    if (accao === "mcp") {
      if (req.method !== "POST") return new Response(null, { status: 405, headers: { ...cors, Allow: "POST" } });
      let corpo: any;
      try { corpo = await req.json(); } catch { return json(400, { jsonrpc: "2.0", id: null, error: { code: -32700, message: "JSON inválido" } }); }
      const kbase = `${base}`;
      if (Array.isArray(corpo)) {
        const rs = (await Promise.all(corpo.map((m) => mcp(m, kbase, v, reg)))).filter(Boolean);
        return rs.length ? json(200, rs) : new Response(null, { status: 202, headers: cors });
      }
      const r = await mcp(corpo, kbase, v, reg);
      return r ? json(200, r) : new Response(null, { status: 202, headers: cors });
    }
    if (accao === "dados") {
      const tipo = resto[resto[0] === "k" ? 3 : 1] || "resumo";
      const r = await dados(tipo, q("de"), q("ate"), q("comunidade"), q("equipa"));
      const n = Array.isArray(r.dados) ? (r.dados as any[]).length : 1;
      await reg("dados/" + tipo, Object.fromEntries(u.searchParams), n, 200);
      if (q("formato") === "csv" && Array.isArray(r.dados)) {
        return new Response(csv(r.dados as any[]), { headers: { ...cors, "Content-Type": "text/csv; charset=utf-8",
          "Content-Disposition": `attachment; filename="Rega_Coco_${tipo}_${(r.periodo.de || hojeMaputo()).replaceAll("-", "")}.csv"` } });
      }
      return json(200, { tipo, periodo: r.periodo, total: n, linhas: r.dados });
    }
    if (accao === "excel") {
      const x = await excel(q("de"), q("ate"), q("comunidade"), q("equipa"));
      await reg("excel", Object.fromEntries(u.searchParams), x.linhas, 200);
      return new Response(x.buf, { headers: { ...cors, "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": `attachment; filename="${x.nome}"` } });
    }
    if (accao === "foto") {
      const link = await linkFoto(q("ref") || "");
      await reg("foto", { ref: q("ref") }, 1, 302);
      return new Response(null, { status: 302, headers: { ...cors, Location: link } });
    }
    await reg(accao || "(sem acção)", null, 0, 404);
    return json(404, { erro: "Use /mcp (conector), /dados/<tipo>, /excel ou /foto?ref=", tipos: TIPOS });
  } catch (e) {
    const st = e instanceof Erro ? e.status : 500;
    await reg(accao, Object.fromEntries(u.searchParams), 0, st);
    return json(st, { erro: e instanceof Erro ? e.message : "Erro" });
  }
});
