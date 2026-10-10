import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

// Criação e gestão dos logins: activistas (utilizador + PIN) e outros acessos (técnico, supervisor, director, cliente: utilizador + senha).
// Só um utilizador com papel 'gestor' em public.perfis pode usar esta função.
const DOMINIO = "rega-coco.example.com"; // endereço interno, nunca recebe emails
const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const resp = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });
const RE_USER = /^[a-z0-9._-]{3,30}$/;
const PAPEIS_OUTROS = ["tecnico", "supervisor", "director", "cliente"];

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return resp(405, { erro: "Método não permitido" });
  const url = Deno.env.get("SUPABASE_URL")!;
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const admin = createClient(url, service, { auth: { persistSession: false } });

  const token = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  const { data: quem, error: eU } = await admin.auth.getUser(token);
  if (eU || !quem?.user) return resp(401, { erro: "Sessão inválida" });
  const { data: perfil } = await admin.from("perfis").select("papel").eq("id", quem.user.id).maybeSingle();
  if (perfil?.papel !== "gestor") return resp(403, { erro: "Só o gestor pode gerir logins" });

  let body: any;
  try { body = await req.json(); } catch { return resp(400, { erro: "Pedido inválido" }); }
  const accao = body?.accao;
  const nomeUtilizador = (e: string) => (e.endsWith("@" + DOMINIO) ? e.split("@")[0] : e || null);
  // nomes dos técnicos e supervisores tal como estão na lista de activistas (é por eles que se ligam as equipas)
  const nomesEquipa = async () => {
    const { data } = await admin.from("activistas").select("tecnico,supervisor");
    const uniq = (k: "tecnico" | "supervisor") => [...new Set((data || []).map((a) => a[k]).filter(Boolean))].sort();
    return { tecnico: uniq("tecnico"), supervisor: uniq("supervisor") };
  };

  if (accao === "listar") {
    const { data: acts, error } = await admin.from("activistas").select("id,nome,comunidade_principal,activo").order("nome");
    if (error) return resp(500, { erro: error.message });
    const { data: perfis } = await admin.from("perfis").select("id,activista_id,nome,papel");
    const { data: lista } = await admin.auth.admin.listUsers({ perPage: 1000 });
    const email = new Map((lista?.users || []).map((u) => [u.id, String(u.email || "")]));
    const porAct = new Map((perfis || []).filter((p) => p.activista_id).map((p) => [p.activista_id, p]));
    const outros = (perfis || []).filter((p) => PAPEIS_OUTROS.includes(p.papel))
      .map((p) => ({ id: p.id, nome: p.nome, papel: p.papel, utilizador: nomeUtilizador(email.get(p.id) || "") }));
    return resp(200, {
      activistas: (acts || []).map((a) => {
        const p = porAct.get(a.id);
        return { ...a, utilizador: p ? nomeUtilizador(email.get(p.id) || "") : null, tem_login: !!p };
      }),
      utilizadores: outros,
      clientes: outros.filter((o) => o.papel === "cliente"),
      nomes: await nomesEquipa(),
    });
  }

  const utilizador = String(body?.utilizador || "").trim().toLowerCase();
  const senha = String(body?.senha || "");

  if (accao === "criar_utilizador" || accao === "criar_cliente") {
    const nome = String(body?.nome || "").trim();
    const papel = accao === "criar_cliente" ? "cliente" : String(body?.papel || "");
    if (!PAPEIS_OUTROS.includes(papel)) return resp(400, { erro: "Função inválida" });
    if (nome.length < 2) return resp(400, { erro: "Escreva o nome" });
    if (papel === "tecnico" || papel === "supervisor") {
      const nomes = (await nomesEquipa())[papel as "tecnico" | "supervisor"];
      if (!nomes.includes(nome)) return resp(400, { erro: `Escolha o nome da lista de ${papel === "tecnico" ? "técnicos" : "supervisores"}` });
      const { data: ja } = await admin.from("perfis").select("id").eq("papel", papel).eq("nome", nome).maybeSingle();
      if (ja) return resp(409, { erro: "Esta pessoa já tem acesso. Use 'Nova senha'." });
    }
    if (!RE_USER.test(utilizador)) return resp(400, { erro: "Utilizador: 3 a 30 letras minúsculas, números, ponto, hífen ou _" });
    if (senha.length < 8) return resp(400, { erro: "A senha tem de ter pelo menos 8 caracteres" });
    const { data: novo, error } = await admin.auth.admin.createUser({
      email: `${utilizador}@${DOMINIO}`, password: senha, email_confirm: true, user_metadata: { utilizador, nome, papel },
    });
    if (error) return resp(400, { erro: /already|registered|exists/i.test(error.message) ? "Esse utilizador já existe" : error.message });
    const { error: eP } = await admin.from("perfis").insert({ id: novo.user.id, nome, papel });
    if (eP) { await admin.auth.admin.deleteUser(novo.user.id); return resp(500, { erro: eP.message }); }
    return resp(200, { ok: true, utilizador, nome, papel });
  }

  if (accao === "repor_senha") {
    const id = String(body?.perfil_id || "");
    if (senha.length < 8) return resp(400, { erro: "A senha tem de ter pelo menos 8 caracteres" });
    const { data: p } = await admin.from("perfis").select("id,papel").eq("id", id).maybeSingle();
    if (!p || !PAPEIS_OUTROS.includes(p.papel)) return resp(404, { erro: "Utilizador não encontrado" });
    const { error } = await admin.auth.admin.updateUserById(p.id, { password: senha });
    if (error) return resp(400, { erro: error.message });
    return resp(200, { ok: true });
  }

  const pin = String(body?.pin || "");
  if (!/^\d{6}$/.test(pin)) return resp(400, { erro: "O PIN tem de ter 6 dígitos" });

  if (accao === "criar") {
    const activista_id = String(body?.activista_id || "");
    if (!RE_USER.test(utilizador)) return resp(400, { erro: "Utilizador: 3 a 30 letras minúsculas, números, ponto, hífen ou _" });
    const { data: act } = await admin.from("activistas").select("id,nome").eq("id", activista_id).maybeSingle();
    if (!act) return resp(404, { erro: "Activista não encontrado" });
    const { data: ja } = await admin.from("perfis").select("id").eq("activista_id", activista_id).maybeSingle();
    if (ja) return resp(409, { erro: "Este activista já tem login. Use 'repor PIN'." });
    const { data: novo, error } = await admin.auth.admin.createUser({
      email: `${utilizador}@${DOMINIO}`, password: pin, email_confirm: true,
      user_metadata: { utilizador, activista: act.nome },
    });
    if (error) return resp(400, { erro: /already|registered|exists/i.test(error.message) ? "Esse utilizador já existe" : error.message });
    const { error: eP } = await admin.from("perfis").insert({ id: novo.user.id, nome: act.nome, papel: "activista", activista_id });
    if (eP) { await admin.auth.admin.deleteUser(novo.user.id); return resp(500, { erro: eP.message }); }
    return resp(200, { ok: true, utilizador, activista: act.nome });
  }

  if (accao === "repor_pin") {
    const activista_id = String(body?.activista_id || "");
    const { data: p } = await admin.from("perfis").select("id").eq("activista_id", activista_id).maybeSingle();
    if (!p) return resp(404, { erro: "Este activista ainda não tem login" });
    const { error } = await admin.auth.admin.updateUserById(p.id, { password: pin });
    if (error) return resp(400, { erro: error.message });
    return resp(200, { ok: true });
  }

  return resp(400, { erro: "Acção desconhecida" });
});
