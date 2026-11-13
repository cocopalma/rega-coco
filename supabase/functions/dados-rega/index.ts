import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";
import * as XLSX from "npm:xlsx@0.18.5";

// Endereço SÓ DE LEITURA dos dados da Rega Coco e conector (MCP) para o Claude (13/11/2026, Valdo).
// Entrada por utilizador e senha da app (OAuth 2.1 do Supabase Auth, página autorizar.html no GitHub Pages);
// só lêem as pessoas da lista api_utilizadores (o Valdo dá o acesso no SQL Editor: select api_autorizar('dalmar');).
// Não escreve nada nos dados da rega. Só lê pela função api_dados, regista cada pedido em api_acessos e
// assina links das fotografias (1 h). Telefones, utilizadores, senhas, PIN e código ficam de fora.
//   Conector (Claude):   .../functions/v1/dados-rega/mcp            (sem token: 401 com o endereço dos metadados)
//   Metadados:           .../functions/v1/dados-rega/.well-known/oauth-protected-resource
//   Página de entrada:   POST .../entrada  (regista a entrada e diz se a conta pode ler)
//   Dados, Excel, foto:  .../dados/<tipo>?de=&ate=[&formato=csv|geojson], .../excel?de=&ate=, .../foto?ref=  (com o token)
//   v2.1 (13/11/2026): quadros do painel, percursos, limites e planos pela função api_painel (permissões de quem pede)

const TIPOS_API = ["resumo", "regas", "equipas", "dias_sem_rega", "campos", "recontagens", "manutencao", "acompanhamentos",
  "queimadas", "chuva", "monitorias", "idas_agua"];
// v2.1 (13/11/2026, Valdo): quadros do painel, percursos GPS, limites dos campos e planos, lidos com as permissões de quem pede
const TIPOS_PAINEL = ["rondas", "cumprimento", "meta", "tempos", "tempos_campos", "chegadas", "nunca_agua", "plantas_vivas",
  "constrangimentos", "planos", "percursos", "limites"];
const TIPOS = [...TIPOS_API, ...TIPOS_PAINEL];
const SEM_PERIODO = ["campos", "limites", "planos"];
const BUCKETS = ["rega-fotos", "recontagem-fotos", "manutencao-fotos", "chuva-fotos", "monitoria-fotos"];
const MAX_DIAS = 92;
const VERSAO = "2.1";

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
  if (SEM_PERIODO.includes(tipo)) return { de: null, ate: null };
  const h = hojeMaputo();
  const d = de || ate || h, a = ate || de || h;
  if (!RE_DATA.test(d) || !RE_DATA.test(a)) throw new Erro(400, "Datas no formato AAAA-MM-DD");
  if (a < d) throw new Erro(400, "'ate' é antes de 'de'");
  const dias = (Date.parse(a) - Date.parse(d)) / 864e5 + 1;
  if (dias > MAX_DIAS) throw new Erro(400, `Período de no máximo ${MAX_DIAS} dias`);
  if (tipo === "percursos" && dias > 1) throw new Erro(400, "Percursos: um dia de cada vez (de = ate)");
  return { de: d, ate: a };
}

class Erro extends Error {
  constructor(public status: number, msg: string) { super(msg); }
}

async function dados(tipo: string, de: string | undefined, ate: string | undefined, comunidade: string | undefined,
  equipa: string | undefined, perfil: string): Promise<{ periodo: { de: string | null; ate: string | null }; dados: any; extra?: any }> {
  if (!TIPOS.includes(tipo)) throw new Erro(400, "Tipo desconhecido. Tipos: " + TIPOS.join(", "));
  const p = periodo(tipo, de, ate);
  if (TIPOS_PAINEL.includes(tipo)) {
    const fonte = { rondas: "painel_resumo", chegadas: "painel_resumo", tempos_campos: "tempos" }[tipo] || tipo;
    const { data, error } = await admin.rpc("api_painel", { p_perfil: perfil, p_tipo: fonte, p_de: p.de, p_ate: p.ate });
    if (error) throw new Erro(/acesso/i.test(error.message || "") ? 403 : 500, /acesso/i.test(error.message || "") ? error.message : "Erro ao ler os dados");
    if (data == null) throw new Erro(403, "Este quadro não está disponível para esta conta (é o mesmo que no painel da app).");
    const t = transformar(tipo, data);
    return { periodo: p, dados: filtrar(t.linhas, comunidade, equipa), extra: t.extra };
  }
  const { data, error } = await admin.rpc("api_dados", {
    p_tipo: tipo, p_de: p.de, p_ate: p.ate, p_comunidade: comunidade || null, p_equipa: equipa || null,
  });
  if (error) throw new Erro(500, "Erro ao ler os dados");
  return { periodo: p, dados: data };
}

// ---------- quadros do painel, percursos, limites e planos (v2.1) ----------
const hm = (x: string | null | undefined) => x ? new Date(Date.parse(x) + 2 * 3600e3).toISOString().slice(11, 16) : null;
const hmE = (s: number) => new Date(s * 1000 + 2 * 3600e3).toISOString().slice(11, 16);
function metros(a: number[], b: number[]) { // [lon, lat]
  const R = 6371000, r = Math.PI / 180, dLa = (b[1] - a[1]) * r, dLo = (b[0] - a[0]) * r;
  const h = Math.sin(dLa / 2) ** 2 + Math.cos(a[1] * r) * Math.cos(b[1] * r) * Math.sin(dLo / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
const BURACO_S = 600; // como na app: mais de 10 min sem ponto = tempo sem registo
function filtrar(linhas: any[], comunidade?: string, equipa?: string) {
  const c = (comunidade || "").trim().toLowerCase(), e = (equipa || "").trim().toLowerCase();
  if (!c && !e) return linhas;
  return linhas.filter((x) => {
    const o = x?.properties || x || {};
    if (c && o.comunidade !== undefined && String(o.comunidade || "").toLowerCase() !== c) return false;
    const eq = o.equipa ?? o.activista;
    if (e && eq !== undefined && !String(eq || "").toLowerCase().includes(e)) return false;
    return true;
  });
}
function partesPercurso(pts: number[][]) {
  const partes: number[][][] = []; let cur: number[][] = [], dist = 0, sem = 0;
  pts.forEach((q, k) => {
    if (k && q[2] - pts[k - 1][2] > BURACO_S) { if (cur.length) partes.push(cur); sem += q[2] - pts[k - 1][2]; cur = []; }
    else if (k) dist += metros(pts[k - 1], q);
    cur.push(q);
  });
  if (cur.length) partes.push(cur);
  return { partes, dist, sem };
}
function percursoEquipa(x: any) {
  const pts = (x.percurso?.pontos || []).filter((q: any) => Array.isArray(q) && q.length >= 3).sort((a: any, b: any) => a[2] - b[2]);
  const { partes, dist, sem } = partesPercurso(pts);
  const regas = x.percurso?.regas || [];
  const linha = { equipa: x.equipa, pontos_gps: pts.length, primeiro: pts.length ? hmE(pts[0][2]) : null, ultimo: pts.length ? hmE(pts[pts.length - 1][2]) : null,
    km_percorridos: Math.round(dist / 10) / 100, sem_registo_min: Math.round(sem / 60), regas_n: regas.length,
    regas: regas.map((g: any) => `${hm(g.entrada_em)}–${hm(g.saida_em) || "?"} ${g.area_id}${g.plantas != null ? ` (${g.plantas} plantas)` : ""}`),
    pontos: pts.map((q: number[]) => [q[0], q[1], hmE(q[2]), q[3] ?? null]) };
  return { linha, partes };
}
function transformar(tipo: string, r: any): { linhas: any[]; extra?: any } {
  switch (tipo) {
    case "cumprimento":
      return {
        linhas: (r.pessoas || []).map((x: any) => ({ ...x, nao_fechou: Math.max(0, (x.dias || 0) - (x.fechados_a_tempo || 0) - (x.fechados_tarde || 0)) })),
        extra: { de: r.de, ate: r.ate, conta_desde: r.inicio,
          nota: "Técnicos e supervisores. dias = dias de trabalho a avaliar (segunda a sábado); fechados_a_tempo = fechou o dia até às 18:00; fechados_tarde = depois das 18:00; nao_fechou = não fechou; mon_sorteados/mon_feitos = monitoria; alertas/alertas_tratados = regas com aviso ⚠️; equipas_dia = equipas × dias; sem_motivo = equipas-dia sem rega nem motivo; motivos_por_confirmar. Igual ao painel › Cumprimento." },
      };
    case "meta":
      return {
        linhas: (r.dias || []).map(({ activista_id: _i, ...x }: any) => ({ ...x, abaixo_limiar: x.pct != null && x.pct < r.limiar })),
        extra: { limiar_pct: r.limiar, espera_min: r.espera_min, mortas_pct: r.mortas_pct, hora_chegada: r.hora_chegada, motivo_pedido_desde: r.motivo_inicio,
          nota: "Uma linha por equipa e dia com regas. meta = 140 plantas × pessoas; pct = plantas ÷ meta. Causas (quando abaixo do limiar): tarde (1.ª entrada depois da hora combinada), espera (60 min ou mais à espera da água), agua (constrangimento de água ou avaria), mortas (muitas mudas mortas), dia_sem_rega. precisa_motivo = abaixo do limiar e sem causa; motivo = o que o técnico/supervisor escreveu. Igual ao painel › Porque não se atingiu a meta." },
      };
    case "tempos":
      return { linhas: r.equipas || [], extra: { nota: "Medianas por equipa no período: espera pela água, rega (min), ritmo (plantas por pessoa por hora), deslocação entre campos (só as deslocações; pausas à parte), distância entre campos (m). Igual ao painel › Tempo por campo e deslocação." } };
    case "tempos_campos": {
      const med = Object.fromEntries((r.equipas || []).map((t: any) => [t.equipa, t.ritmo_med]));
      return {
        linhas: (r.regas || []).map((x: any) => {
          const base = (x.vivas > 0 ? x.vivas : x.instaladas) || 0, m = med[x.equipa];
          return { data: x.data, equipa: x.equipa, campo: x.area_id, produtor: x.produtor, comunidade: x.comunidade,
            entrada: hm(x.entrada_em), agua: hm(x.agua_em), saida: hm(x.saida_em), area_ha: x.area_m2 ? Math.round(x.area_m2 / 100) / 100 : null,
            plantas_base: base, plantas_regadas: x.plantas, pessoas: x.pessoas, espera_min: x.espera_min, rega_min: x.rega_min,
            ritmo: x.ritmo, ritmo_mediana_equipa: m ?? null, deslocacao_antes_min: x.desloc_min, distancia_antes_m: x.dist_m,
            pausa_antes: x.pausa, campo_anterior: x.area_ant,
            alerta_acima_base: base > 0 && x.plantas > base,
            alerta_ritmo: x.ritmo != null && m > 0 && (x.ritmo > 3 * m || x.ritmo < m / 3) };
        }),
        extra: { nota: "Uma linha por rega. alerta_acima_base = regou mais plantas do que a base; alerta_ritmo = ritmo 3 vezes acima ou abaixo da mediana da própria equipa no período. pausa_antes = o tempo desde o campo anterior passou o tempo de deslocação esperado pela distância." },
      };
    }
    case "rondas": {
      const eq = r.por_equipa || [], lista = eq.reduce((a: number, x: any) => a + (x.lista || 0), 0);
      return {
        linhas: eq.map((x: any) => ({ equipa: x.nome, comunidade: x.comunidade, campos_na_lista: x.lista, ronda_actual: x.ronda,
          regados_na_ronda: x.regadas_ronda, progresso_pct: x.lista ? Math.round(100 * x.regadas_ronda / x.lista) : null,
          inicio_ronda: x.inicio_ronda, rondas_concluidas: (x.rondas_concluidas || []).length,
          rondas_detalhe: (x.rondas_concluidas || []).map((c: any) => `R${c.ronda}: ${c.inicio} a ${c.fim} (${c.dias} dias)`).join("; ") || null,
          plantas_no_periodo: x.plantas, dias_trabalhados_no_periodo: x.dias_trabalhados, pessoas_dia_no_periodo: x.pessoas_dia,
          min_por_campo: x.min_por_campo, espera_agua_min: x.espera_agua_min })),
        extra: { campos_na_rega: r.universo?.areas, plantas_vivas_na_rega: r.universo?.vivas, campos_sem_equipa: (r.universo?.areas || 0) - lista,
          dias_medios_entre_regas: r.dias_medios_entre_regas,
          nota: "Ronda actual, campos regados na ronda e rondas concluídas = estado de hoje; plantas, dias e pessoas = período pedido. Igual ao painel › Equipas — rondas." },
      };
    }
    case "chegadas":
      return { linhas: r.chegadas_agua || [], extra: { chegada_equipa: r.chegada_equipa, espera_agua_min: r.espera_agua_min,
        nota: "Uma linha por equipa e dia: início do trabalho (1.ª entrada), 1.ª água, horas de cada chegada da água, espera média e atraso face à hora combinada de chegada ao 1.º campo. Igual ao painel › Chegada da água." } };
    case "nunca_agua":
      return {
        linhas: (r.campos || []).map(({ pr: _p, ...x }: any) => x),
        extra: { hoje: r.hoje, ficheiro_whatsapp: r.whatsapp, primeira_agua_no_periodo: r.primeira || [], retirados_no_periodo: r.retirados || [],
          campos_que_faltavam_por_dia: r.dias || [],
          nota: "Campos na rega que nunca receberam água (nem na app nem no WhatsApp para esse campo). primeira_agua_no_periodo = campos que receberam a 1.ª água no período; retirados_no_periodo = campos retirados da rega no período. Igual ao painel › Campos que nunca receberam água." },
      };
    case "plantas_vivas":
      return { linhas: r.dias || [], extra: { total: r.total, nota: "Por dia: plantas regadas e plantas vivas que havia nos campos regados; a diferença divide-se em mortas (secas ou mortas declaradas na saída), por_terminar (rega a meio) e outras. Igual ao painel › Plantas regadas das vivas que havia." } };
    case "constrangimentos":
      return { linhas: Array.isArray(r) ? r : [], extra: { nota: "Constrangimentos registados na saída de cada rega, por campo. Igual ao painel › Constrangimentos › Ver por campo." } };
    case "planos":
      return { linhas: Array.isArray(r) ? r : [], extra: { nota: "Uma linha por campo do itinerário: plano › dia › ordem. estado: por_supervisor, por_gestor, aprovado, recusado, substituido. Não depende do período." } };
    case "percursos":
      return {
        linhas: (Array.isArray(r) ? r : []).map((x: any) => percursoEquipa(x).linha),
        extra: { nota: "Percurso GPS do telefone de cada equipa no dia (pontos [lon, lat, hora de Maputo, precisão m]). Só grava com a app aberta: mais de 10 min sem ponto conta como tempo sem registo e não entra nos km. Para um mapa use link_geojson." },
      };
    case "limites": {
      const f = (geom: any, props: any) => ({ type: "Feature", geometry: geom, properties: props });
      const campos = (r.campos || []).map(({ poligono, lat, lon, ...x }: any) => {
        const anel = Array.isArray(poligono) && poligono.length >= 3 ? [...poligono, ...(String(poligono[0]) !== String(poligono[poligono.length - 1]) ? [poligono[0]] : [])] : null;
        const geom = anel ? { type: "Polygon", coordinates: [anel] } : lat != null && lon != null ? { type: "Point", coordinates: [lon, lat] } : null;
        return f(geom, { camada: "campo", ...x, tem_limite: !!anel, centro_lat: lat, centro_lon: lon });
      });
      const pocos = (r.pocos || []).map((x: any) => f({ type: "Point", coordinates: [x.lon, x.lat] }, { camada: "poco", codigo: x.codigo, comunidade: x.comunidade, fonte: x.fonte }));
      const pluv = (r.pluviometros || []).map((x: any) => f({ type: "Point", coordinates: [x.lon, x.lat] }, { camada: "pluviometro", nome: x.nome, comunidade: x.comunidade, zona: x.zona }));
      return { linhas: [...campos, ...pocos, ...pluv], extra: { campos: campos.length, com_limite: campos.filter((c: any) => c.properties.tem_limite).length,
        pocos: pocos.length, pluviometros: pluv.length,
        nota: "Cada linha é um Feature GeoJSON (coordenadas [lon, lat]); camada = campo, poco ou pluviometro. Campos sem limite medido vêm como ponto; sem coordenada, geometry = null. Só os campos na rega. Para o ficheiro completo use link_geojson." } };
    }
  }
  return { linhas: [] };
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
  ["queimadas", "Queimadas"], ["chuva", "Chuva"], ["monitorias", "Monitorias"], ["idas_agua", "Idas à água"],
  ["rondas", "Rondas por equipa"], ["cumprimento", "Cumprimento"], ["meta", "Meta por equipa e dia"], ["tempos", "Tempos por equipa"],
  ["tempos_campos", "Tempos por campo"], ["chegadas", "Chegadas da água"], ["nunca_agua", "Nunca receberam água"],
  ["plantas_vivas", "Plantas vivas regadas"], ["constrangimentos", "Constrangimentos"], ["planos", "Planos e itinerário"],
  ["limites", "Limites dos campos"]];
const MAX_DIAS_PERC_EXCEL = 7;

async function excel(de: string | undefined, ate: string | undefined, comunidade: string | undefined, equipa: string | undefined, perfil: string) {
  const wb = XLSX.utils.book_new();
  const p = periodo("regas", de, ate);
  const res = await dados("resumo", p.de!, p.ate!, undefined, undefined, perfil);
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
    ["Folhas do painel (rondas, cumprimento, meta, tempos, chegadas, nunca receberam água, plantas vivas, constrangimentos): os mesmos números do painel da app, com as permissões de quem pediu."],
    ["Planos e limites dos campos não dependem do período. Limites: sem o desenho (para o mapa use o link GeoJSON do conector)."],
    [`Percursos GPS: resumo por equipa e dia só para períodos até ${MAX_DIAS_PERC_EXCEL} dias.`],
    [], ["Resumo do período"],
    ...Object.entries(res.dados as any).filter(([k]) => k !== "nota" && k !== "periodo")
      .map(([k, v]) => [k, typeof v === "object" ? JSON.stringify(v) : v]),
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(leia), "Leia-me");
  let linhas = 0;
  const folha = (rows: any[], nome: string, vazio = "Sem registos no período") => {
    linhas += rows.length;
    XLSX.utils.book_append_sheet(wb, rows.length ? XLSX.utils.json_to_sheet(rows.map(plano)) : XLSX.utils.aoa_to_sheet([[vazio]]), nome);
  };
  for (const [tipo, nome] of FOLHAS) {
    let r: any;
    try { r = await dados(tipo, p.de!, p.ate!, comunidade, equipa, perfil); }
    catch (e) { if (e instanceof Erro && e.status === 403) { folha([], nome, "Sem acesso a este quadro com esta conta"); continue; } throw e; }
    let rows = r.dados as any[];
    if (tipo === "limites") rows = rows.map((f: any) => ({ ...f.properties, pontos_do_limite: f.geometry?.type === "Polygon" ? f.geometry.coordinates[0].length : 0 }));
    folha(rows, nome);
    if (tipo === "nunca_agua") {
      folha(r.extra?.primeira_agua_no_periodo || [], "1.ª água no período");
      folha(r.extra?.retirados_no_periodo || [], "Retirados no período");
    }
  }
  const nd = (Date.parse(p.ate!) - Date.parse(p.de!)) / 864e5 + 1;
  if (nd <= MAX_DIAS_PERC_EXCEL) {
    const rows: any[] = [];
    for (let k = 0; k < nd; k++) {
      const d = new Date(Date.parse(p.de!) + k * 864e5).toISOString().slice(0, 10);
      try {
        const r = await dados("percursos", d, d, comunidade, equipa, perfil);
        for (const x of r.dados as any[]) { const { pontos: _p, regas, ...y } = x; rows.push({ data: d, ...y, regas: regas.join("; ") }); }
      } catch (e) { if (!(e instanceof Erro && e.status === 403)) throw e; }
    }
    folha(rows, "Percursos GPS (resumo)");
  } else folha([], "Percursos GPS (resumo)", `Só para períodos até ${MAX_DIAS_PERC_EXCEL} dias: use ler_dados tipo percursos, um dia de cada vez`);
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

// ---------- GeoJSON (limites dos campos, percursos de um dia) ----------
async function geojson(tipo: string, dia: string | undefined, comunidade: string | undefined, equipa: string | undefined, perfil: string) {
  if (tipo === "limites") {
    const r = await dados("limites", undefined, undefined, comunidade, equipa, perfil);
    return { fc: { type: "FeatureCollection", name: "Rega Coco — limites dos campos", features: r.dados }, nome: "Rega_Coco_limites_campos.geojson", n: r.dados.length };
  }
  if (tipo === "percursos") {
    const p = periodo("percursos", dia, dia);
    const { data, error } = await admin.rpc("api_painel", { p_perfil: perfil, p_tipo: "percursos", p_de: p.de, p_ate: p.ate });
    if (error) throw new Erro(500, "Erro ao ler os dados");
    const features = filtrar((Array.isArray(data) ? data : []).map((x: any) => {
      const { linha, partes } = percursoEquipa(x);
      const tracos = partes.filter((pt) => pt.length > 1).map((pt) => pt.map((q) => [q[0], q[1]]));
      const { pontos, ...props } = linha;
      return { type: "Feature", properties: { ...props, data: p.de, regas: linha.regas.join("; ") },
        geometry: tracos.length ? { type: "MultiLineString", coordinates: tracos } : pontos.length ? { type: "Point", coordinates: pontos[0].slice(0, 2) } : null };
    }), comunidade, equipa);
    return { fc: { type: "FeatureCollection", name: `Rega Coco — percursos ${p.de}`, features }, nome: `Rega_Coco_percursos_${p.de!.replaceAll("-", "")}.geojson`, n: features.length };
  }
  throw new Erro(400, "GeoJSON: tipo limites ou percursos");
}

// ---------- link do Excel sem o token no endereço (válido 1 h) ----------
const enc = new TextEncoder();
const b64u = (u: Uint8Array) => encodeBase64(u).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
async function hmac(txt: string) {
  const k = await crypto.subtle.importKey("raw", enc.encode("dados-rega:" + service), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return b64u(new Uint8Array(await crypto.subtle.sign("HMAC", k, enc.encode(txt))));
}
async function tokenExcel(perfilId: string, q: Record<string, string | undefined>) {
  const corpo = b64u(enc.encode(JSON.stringify({ c: perfilId, e: Math.floor(Date.now() / 1000) + 3600, ...q })));
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
- idas_agua: quando cada equipa foi buscar água.
Quadros do painel (os mesmos números do painel da app, com as permissões de quem pergunta; vêm com 'extra' = notas e totais):
- rondas: por equipa: campos na lista, ronda actual, campos regados na ronda, progresso %, rondas concluídas (datas e dias), plantas, dias e pessoas no período; extra: campos na rega, campos sem equipa, dias médios entre regas.
- cumprimento: técnicos e supervisores: dias a avaliar, fechou o dia até às 18:00 / depois / não fechou, monitoria, regas com aviso ⚠️ tratadas, equipas-dia sem motivo, motivos por confirmar.
- meta: equipa e dia: plantas, pessoas, meta (140 × pessoas), % da meta, causas de não atingir (tarde, espera, agua, mortas, dia_sem_rega), motivo escrito.
- tempos: medianas por equipa (espera pela água, rega, ritmo, deslocação, distância entre campos, pausas).
- tempos_campos: uma linha por rega com entrada/água/saída, ritmo, deslocação antes e alertas (acima da base, ritmo fora do habitual).
- chegadas: equipa e dia: início do trabalho, 1.ª água, horas de cada chegada da água, espera, atraso face à hora combinada; extra: chegada média da equipa.
- nunca_agua: campos na rega que nunca receberam água; extra: 1.ª água no período, retirados no período, evolução por dia.
- plantas_vivas: por dia, plantas regadas das vivas que havia (mortas, por terminar, outras).
- constrangimentos: constrangimentos da saída por campo.
Mapa e planeamento:
- planos: planos das equipas e itinerário (uma linha por campo: plano › dia › ordem; estado e aprovações). Não usa o período.
- percursos: percurso GPS de cada equipa num dia (um dia de cada vez): km, tempo sem registo, regas pela ordem e pontos [lon, lat, hora].
- limites: limites dos campos na rega (Feature GeoJSON com campo, produtor, comunidade, equipa, plantas, área), poços e pluviómetros. Não usa o período.`;

const FERRAMENTAS = [
  {
    name: "ler_dados",
    description: "Lê os dados da app de rega Rega Coco (Projeto de Desenvolvimento da Cadeia de Valor do Coco, Palma). Só leitura. " +
      "Datas e horas de Maputo; regas de teste não entram. Período até 92 dias (sem período = hoje). Respostas em páginas: use 'pagina' e 'colunas' para ler menos. " +
      "Para muitos dados de uma vez use link_excel; para mapas use link_geojson.\n" + DESC_TIPOS,
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
    description: "Devolve um link (válido 1 hora) para descarregar um Excel com todos os dados do período (Leia-me com o resumo, Regas, Equipas por dia, Dias sem rega, Campos, Recontagens, Manutenção, Acompanhamentos, Queimadas, Chuva, Monitorias, Idas à água, e os quadros do painel: Rondas, Cumprimento, Meta, Tempos, Chegadas da água, Nunca receberam água, Plantas vivas regadas, Constrangimentos, Planos e itinerário, Limites dos campos, Percursos GPS em resumo até 7 dias). Período até 92 dias; sem período = hoje.",
    inputSchema: {
      type: "object",
      properties: { de: { type: "string" }, ate: { type: "string" }, comunidade: { type: "string" }, equipa: { type: "string" } },
    },
    annotations: { readOnlyHint: true },
  },
  {
    name: "link_geojson",
    description: "Devolve um link (válido 1 hora) para um ficheiro GeoJSON para mapas: 'limites' = limites dos campos na rega, poços e pluviómetros; 'percursos' = percursos GPS das equipas num dia (linhas; 'dia' obrigatório, sem dia = hoje).",
    inputSchema: {
      type: "object",
      properties: { tipo: { type: "string", enum: ["limites", "percursos"] }, dia: { type: "string", description: "AAAA-MM-DD (percursos)" },
        comunidade: { type: "string" }, equipa: { type: "string" } },
      required: ["tipo"],
    },
    annotations: { readOnlyHint: true },
  },
];

const INSTRUCOES = "Dados da app de rega Rega Coco (só leitura). Comece por ler_dados com tipo 'resumo' para o período pedido; " +
  "use 'equipas' para o dia de cada equipa e 'regas' para o detalhe; para o painel use rondas, cumprimento, meta, tempos, chegadas, nunca_agua, plantas_vivas e constrangimentos; " +
  "para o mapa use limites e percursos (ou link_geojson) e para o planeamento planos. Não invente números: se um dado não vem nas respostas, diga que falta.";

async function chamarFerramenta(nome: string, a: any, base: string, perfilId: string) {
  if (nome === "ler_dados") {
    const r = await dados(a.tipo, a.de, a.ate, a.comunidade, a.equipa, perfilId);
    if (!Array.isArray(r.dados)) return { conteudo: [{ type: "text", text: JSON.stringify(r) }], linhas: 1 };
    const por = Math.min(Math.max(Number(a.por_pagina) || 100, 1), 500), pag = Math.max(Number(a.pagina) || 1, 1);
    let linhas = (r.dados as any[]).slice((pag - 1) * por, pag * por);
    if (Array.isArray(a.colunas) && a.colunas.length) linhas = linhas.map((x) => Object.fromEntries(a.colunas.filter((c: string) => c in x).map((c: string) => [c, x[c]])));
    const total = (r.dados as any[]).length;
    const out = { tipo: a.tipo, periodo: r.periodo, total, pagina: pag, por_pagina: por, paginas: Math.ceil(total / por),
      ...(r.extra && pag === 1 ? { extra: r.extra } : {}), linhas };
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
    const t = await tokenExcel(perfilId, { k: "xlsx", de: p.de!, ate: p.ate!, comunidade: a.comunidade, equipa: a.equipa });
    return { conteudo: [{ type: "text", text: `Excel de ${p.de} a ${p.ate} (link válido 1 hora): ${base}/excel?t=${t}` }], linhas: 0 };
  }
  if (nome === "link_geojson") {
    if (!["limites", "percursos"].includes(a.tipo)) throw new Erro(400, "tipo: limites ou percursos");
    const dia = a.tipo === "percursos" ? periodo("percursos", a.dia, a.dia).de! : undefined;
    const t = await tokenExcel(perfilId, { k: "geo", tipo: a.tipo, dia, comunidade: a.comunidade, equipa: a.equipa });
    return { conteudo: [{ type: "text", text: `GeoJSON ${a.tipo === "limites" ? "dos limites dos campos" : "dos percursos de " + dia} (link válido 1 hora): ${base}/geojson?t=${t}` }], linhas: 0 };
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

// ---------- quem pede (entrada por utilizador e senha: OAuth 2.1 do Supabase Auth) ----------
// O conector do Claude recebe um token do Supabase Auth depois de a pessoa entrar com o utilizador e a senha da app
// na página autorizar.html. Só as pessoas da lista api_utilizadores (api_autorizar no SQL Editor) lêem os dados.
function claimsDe(tok: string): any {
  try {
    const p = tok.split(".")[1].replaceAll("-", "+").replaceAll("_", "/");
    return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(p + "===".slice((p.length + 3) % 4)), (c) => c.charCodeAt(0))));
  } catch { return {}; }
}
async function quemPede(req: Request) {
  const tok = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "").trim();
  if (!tok) return { estado: "sem" as const };
  const { data, error } = await admin.auth.getUser(tok);
  if (error || !data?.user) return { estado: "invalido" as const };
  return { estado: "ok" as const, uid: data.user.id, client: claimsDe(tok).client_id || null };
}

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
  const recurso = `${base}/mcp`;
  const metadados = `${base}/.well-known/oauth-protected-resource`;
  const accao = resto.join("/");
  let perfil: string | null = null, client: string | null = null;
  const via = accao === "mcp" ? "mcp" : accao === "entrada" ? "entrada" : "http";
  const reg = async (a: string, param: unknown, linhas: number, estado: number) => {
    await admin.rpc("api_registar2", { p_perfil: perfil, p_client: client, p_ip: ip, p_agente: agente, p_via: via, p_accao: a,
      p_param: param ?? null, p_linhas: linhas, p_ms: Date.now() - t0, p_estado: estado });
  };

  // metadados do recurso protegido (RFC 9728): diz ao Claude onde a pessoa entra (Supabase Auth)
  if (resto[0] === ".well-known" && resto[1] === "oauth-protected-resource") {
    return json(200, {
      resource: recurso,
      authorization_servers: [`${url}/auth/v1`],
      bearer_methods_supported: ["header"],
      resource_name: "Rega Coco — dados da rega (só leitura)",
    });
  }

  // link do Excel de 1 hora (sem token no endereço; assinado pelo servidor)
  if (resto[0] === "geojson" && q("t")) {
    const tk = await lerToken(q("t")!);
    if (!tk || tk.k !== "geo") return json(401, { erro: "Link expirado ou inválido. Peça um link novo ao conector." });
    perfil = tk.c;
    const { data: v } = await admin.rpc("api_validar_perfil", { p_perfil: tk.c });
    if (!v) { await reg("geojson", null, 0, 403); return json(403, { erro: "Acesso desligado" }); }
    try {
      const g = await geojson(tk.tipo, tk.dia, tk.comunidade, tk.equipa, tk.c);
      await admin.rpc("api_registar2", { p_perfil: tk.c, p_client: null, p_ip: ip, p_agente: agente, p_via: "link", p_accao: "geojson",
        p_param: { tipo: tk.tipo, dia: tk.dia, comunidade: tk.comunidade, equipa: tk.equipa }, p_linhas: g.n, p_ms: Date.now() - t0, p_estado: 200 });
      return new Response(JSON.stringify(g.fc), { headers: { ...cors, "Content-Type": "application/geo+json; charset=utf-8",
        "Content-Disposition": `attachment; filename="${g.nome}"` } });
    } catch (e) {
      return json(e instanceof Erro ? e.status : 500, { erro: e instanceof Erro ? e.message : "Erro" });
    }
  }

  if (resto[0] === "excel" && q("t")) {
    const tk = await lerToken(q("t")!);
    if (!tk || (tk.k && tk.k !== "xlsx")) return json(401, { erro: "Link expirado ou inválido. Peça um link novo ao conector." });
    perfil = tk.c;
    const { data: v } = await admin.rpc("api_validar_perfil", { p_perfil: tk.c });
    if (!v) { await reg("excel", null, 0, 403); return json(403, { erro: "Acesso desligado" }); }
    try {
      const x = await excel(tk.de, tk.ate, tk.comunidade, tk.equipa, tk.c);
      await admin.rpc("api_registar2", { p_perfil: tk.c, p_client: null, p_ip: ip, p_agente: agente, p_via: "link", p_accao: "excel",
        p_param: { de: tk.de, ate: tk.ate, comunidade: tk.comunidade, equipa: tk.equipa }, p_linhas: x.linhas, p_ms: Date.now() - t0, p_estado: 200 });
      return new Response(x.buf, { headers: { ...cors, "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": `attachment; filename="${x.nome}"` } });
    } catch (e) {
      return json(e instanceof Erro ? e.status : 500, { erro: e instanceof Erro ? e.message : "Erro" });
    }
  }

  // as chaves no endereço da versão anterior deixaram de valer
  if (resto[0] === "k") return json(410, { erro: "Este endereço já não é usado. Ligue o conector a " + recurso + " e entre com o utilizador e a senha da app." });

  const w = await quemPede(req);
  if (w.estado !== "ok") {
    await reg(accao === "mcp" && w.estado === "sem" ? "mcp:sem-token" : accao || "(sem acção)", null, 0, 401);
    return json(401, { erro: "Entre com o utilizador e a senha da app" },
      { "WWW-Authenticate": `Bearer resource_metadata="${metadados}"` });
  }
  perfil = w.uid; client = w.client;
  const { data: v } = await admin.rpc("api_validar_perfil", { p_perfil: w.uid });

  // a página de entrada pergunta se esta pessoa pode ler os dados (fica registada a entrada, com o IP do navegador)
  if (accao === "entrada") {
    await reg("entrada", null, 0, v ? 200 : 403);
    return json(200, { autorizado: !!v, nome: v?.nome || null });
  }
  if (!v) { await reg(accao || "(sem acção)", null, 0, 403); return json(403, { erro: "Esta conta não tem acesso aos dados. Fale com o gestor." }); }
  if (v.pedidos_hora >= v.limite) { await reg(accao, null, 0, 429); return json(429, { erro: "Demasiados pedidos nesta hora. Tente mais tarde." }); }

  try {
    if (accao === "mcp") {
      if (req.method !== "POST") return new Response(null, { status: 405, headers: { ...cors, Allow: "POST" } });
      let corpo: any;
      try { corpo = await req.json(); } catch { return json(400, { jsonrpc: "2.0", id: null, error: { code: -32700, message: "JSON inválido" } }); }
      if (Array.isArray(corpo)) {
        const rs = (await Promise.all(corpo.map((m) => mcp(m, base, v, reg)))).filter(Boolean);
        return rs.length ? json(200, rs) : new Response(null, { status: 202, headers: cors });
      }
      const r = await mcp(corpo, base, v, reg);
      return r ? json(200, r) : new Response(null, { status: 202, headers: cors });
    }
    if (resto[0] === "dados") {
      const tipo = resto[1] || "resumo";
      const r = await dados(tipo, q("de"), q("ate"), q("comunidade"), q("equipa"), w.uid);
      const n = Array.isArray(r.dados) ? (r.dados as any[]).length : 1;
      await reg("dados/" + tipo, Object.fromEntries(u.searchParams), n, 200);
      if (q("formato") === "csv" && Array.isArray(r.dados)) {
        return new Response(csv(r.dados as any[]), { headers: { ...cors, "Content-Type": "text/csv; charset=utf-8",
          "Content-Disposition": `attachment; filename="Rega_Coco_${tipo}_${(r.periodo.de || hojeMaputo()).replaceAll("-", "")}.csv"` } });
      }
      if (q("formato") === "geojson" && (tipo === "limites" || tipo === "percursos")) {
        const g = await geojson(tipo, q("de") || q("ate"), q("comunidade"), q("equipa"), w.uid);
        return new Response(JSON.stringify(g.fc), { headers: { ...cors, "Content-Type": "application/geo+json; charset=utf-8" } });
      }
      return json(200, { tipo, periodo: r.periodo, total: n, ...(r.extra ? { extra: r.extra } : {}), linhas: r.dados });
    }
    if (accao === "excel") {
      const x = await excel(q("de"), q("ate"), q("comunidade"), q("equipa"), w.uid);
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
    return json(404, { erro: "Use /mcp (conector), /dados/<tipo>, /excel, /geojson ou /foto?ref=", tipos: TIPOS });
  } catch (e) {
    const st = e instanceof Erro ? e.status : 500;
    await reg(accao, Object.fromEntries(u.searchParams), 0, st);
    return json(st, { erro: e instanceof Erro ? e.message : "Erro" });
  }
});
