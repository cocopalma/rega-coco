// push-mensagem (v275, 28/11/2026): manda a notificação de uma mensagem nova às subscrições de quem a recebe.
// Chamada pelo gatilho mensagens_push (pg_net) com o cabeçalho x-segredo; sem o segredo certo o servidor recusa
// (push_preparar/push_chaves verificam-no). Cada mensagem só é enviada uma vez (push_em).
// As chaves VAPID ficam em privado.push_config: se ainda não existirem, são criadas aqui na 1.ª chamada.
import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const SUJEITO = "https://cocopalma.github.io/rega-coco/";
const TITULO: Record<string, [string, string]> = {
  pt: ["✉️ Mensagem de", "↩️ Resposta de"],
  en: ["✉️ Message from", "↩️ Reply from"],
  sw: ["✉️ Ujumbe kutoka kwa", "↩️ Jibu kutoka kwa"],
};
const json = (o: unknown, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "Content-Type": "application/json" } });

async function chaves(segredo: string) {
  const { data, error } = await sb.rpc("push_chaves", { p_segredo: segredo });
  if (error) throw error;
  if (data?.publica && data?.privada) return data;
  const k = webpush.generateVAPIDKeys();
  const r = await sb.rpc("push_chaves", { p_segredo: segredo, p_publica: k.publicKey, p_privada: k.privateKey });
  if (r.error) throw r.error;
  return r.data;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ erro: "POST" }, 405);
  const segredo = req.headers.get("x-segredo") || "";
  if (segredo.length < 20) return json({ erro: "Sem acesso" }, 401);
  let b: { id?: string; init?: boolean } = {};
  try { b = await req.json(); } catch { return json({ erro: "Pedido inválido" }, 400); }
  try {
    if (b.init) { const k = await chaves(segredo); return json({ ok: true, publica: !!k?.publica }); }
    if (!b.id) return json({ erro: "Falta o id" }, 400);
    const { data: m, error } = await sb.rpc("push_preparar", { p_id: b.id, p_segredo: segredo });
    if (error) return json({ erro: "Sem acesso" }, 401);
    if (m?.nada) return json({ ok: true, nada: true });
    let pub = m.publica, priv = m.privada;
    if (!pub || !priv) { const k = await chaves(segredo); pub = k.publica; priv = k.privada; }
    webpush.setVapidDetails(SUJEITO, pub, priv);
    const expirados: string[] = [], falhados: string[] = [];
    let enviados = 0;
    await Promise.all((m.subs || []).map(async (s: { endpoint: string; p256dh: string; auth: string; lingua?: string }) => {
      const t = TITULO[s.lingua || "pt"] || TITULO.pt;
      const payload = JSON.stringify({
        tipo: "mensagem", id: m.id,
        titulo: `${m.resposta ? t[1] : t[0]} ${m.de || ""}`.trim(),
        texto: String(m.texto || "").slice(0, 200),
      });
      try {
        await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, payload, { TTL: 86400, urgency: "high" });
        enviados++;
      } catch (e) {
        const st = (e as { statusCode?: number }).statusCode;
        if (st === 404 || st === 410) expirados.push(s.endpoint); else falhados.push(s.endpoint);
      }
    }));
    await sb.rpc("push_resultado", { p_id: m.id, p_segredo: segredo, p_enviados: enviados, p_expirados: expirados, p_falhados: falhados });
    return json({ ok: true, enviados, expirados: expirados.length, falhados: falhados.length });
  } catch (e) {
    return json({ erro: String((e as Error)?.message || e) }, 500);
  }
});
