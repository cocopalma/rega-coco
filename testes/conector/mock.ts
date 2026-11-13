export const LOG: any[] = [];
(globalThis as any).LOG = LOG;
const P: any = {
  cumprimento: { de: "2026-11-12", ate: "2026-11-12", inicio: "2026-10-29", pessoas: [{ nome: "Essumaila", papel: "tecnico", equipas: 8, dias: 3, fechados_a_tempo: 1, fechados_tarde: 1, alertas: 3, alertas_tratados: 3 }] },
  meta: { limiar: 70, espera_min: 60, mortas_pct: 20, hora_chegada: "06:30", motivo_inicio: "2026-11-10", dias: [
    { activista_id: "x", equipa: "Azize Abdala Selemane", comunidade: "Macala", data: "2026-11-12", pct: 16.4, causas: ["espera"] },
    { activista_id: "y", equipa: "Biena", comunidade: "Senga", data: "2026-11-12", pct: 90, causas: [] }] },
  tempos: { equipas: [{ equipa: "Alafo Arlindo Jose", ritmo_med: 71 }], regas: [
    { data: "2026-11-12", equipa: "Alafo Arlindo Jose", area_id: "PR181873-1", produtor: "A", comunidade: "Quiwia", vivas: 490, instaladas: 490, area_m2: 34629, plantas: 181, pessoas: 5, entrada_em: "2026-11-12T04:15:36.789+00:00", agua_em: "2026-11-12T04:17:07+00:00", saida_em: "2026-11-12T04:22:41+00:00", espera_min: 2, rega_min: 6, ritmo: 362, desloc_min: null, dist_m: null, pausa: false, area_ant: null }] },
  nunca_agua: { hoje: "2026-11-13", whatsapp: "2026-11-07", campos: [{ area_id: "PR1-1", pr: "PR1-1", comunidade: "Macala", equipa: "Azize" }], primeira: [{ area_id: "PR2-1", data: "2026-11-12" }], retirados: [], dias: [{ data: "2026-11-12", restam: 56 }] },
  plantas_vivas: { dias: [{ data: "2026-11-12", plantas: 3676, vivas: 6094 }], total: { plantas: 3676 } },
  constrangimentos: [{ data: "2026-11-12", tipo: "mudas_secas", area_id: "PR4-1", comunidade: "Maganja", activista: "Selemane" }],
  painel_resumo: { universo: { areas: 697, vivas: 90776 }, dias_medios_entre_regas: 8.1, chegada_equipa: { hora_media: "06:54" }, espera_agua_min: 28,
    por_equipa: [{ nome: "Alafo Arlindo Jose", lista: 40, ronda: 2, comunidade: "Quiwia", regadas_ronda: 11, rondas_concluidas: [{ fim: "2026-11-12", dias: 17, ronda: 1, inicio: "2026-10-27" }] },
      { nome: "Azize", lista: 64, ronda: 1, comunidade: "Macala", regadas_ronda: 4, rondas_concluidas: null }],
    chegadas_agua: [{ data: "2026-11-12", equipa: "Alafo Arlindo Jose", comunidade: "Quiwia", primeira_agua: "06:17" }] },
  planos: [{ plano_id: "p1", equipa: "Alafo", dia: 1, ordem: 1, campo: "PR2188981-1", comunidade: "Quiwia" }],
  percursos: [{ activista_id: "a", equipa: "Biena Bachilo Usessene", n: 5, percurso: { regas: [{ area_id: "PR032358-1", entrada_em: "2026-11-12T04:27:42+00:00", saida_em: "2026-11-12T07:57:08+00:00", plantas: 7 }],
    pontos: [[40.455955, -10.847065, 1794457647, 5], [40.455782, -10.847162, 1794457707, 2], [40.455627, -10.847267, 1794457717, 2], [40.455453, -10.848058, 1794458412, 5], [40.455555, -10.847972, 1794458500, 14]] } }],
  limites: { campos: [{ campo: "PR1-1", produtor: "A", comunidade: "Farol", equipa: "Majula", vivas: 125, area_m2: 5000, lat: -10.67, lon: 40.62, poligono: [[40.62, -10.67], [40.621, -10.67], [40.621, -10.671]] },
    { campo: "PR2-1", produtor: "B", comunidade: "Farol", equipa: "Majula", lat: -10.672, lon: 40.622, poligono: null }, { campo: "PR3-1", comunidade: "Quiwia", equipa: "Alafo", lat: null, lon: null, poligono: null }],
    pocos: [{ codigo: "BP-01", comunidade: "Olumbe", fonte: "base", lat: -10.99, lon: 40.46 }], pluviometros: [{ nome: "Farol", comunidade: "Farol", zona: null, lat: -10.686, lon: 40.587 }] },
};
export function createClient() {
  return {
    rpc: async (n: string, a: any) => {
      if (n === "api_validar_perfil") return { data: a.p_perfil === "u-dalmar" ? { id: "u-dalmar", nome: "Dalmar", limite: 1000, pedidos_hora: 0 } : null };
      if (n === "api_registar2") { LOG.push(a); return { data: null }; }
      if (n === "api_painel") { LOG.push({ painel: a }); if (a.p_perfil !== "u-dalmar") return { error: { message: "Esta conta não tem acesso aos dados" } };
        if (a.p_tipo === "cumprimento" && a.p_de === "2026-01-01") return { data: null }; return { data: P[a.p_tipo] }; }
      if (n === "api_foto_ok") return { data: a.p_ref === "rega-fotos/u/ok.jpg" };
      if (n === "api_dados2") { if (a.p_perfil !== "u-dalmar") return { error: { message: "Esta conta não tem acesso aos dados" } };
        if (a.p_tipo === "resumo") return { data: { periodo: { de: a.p_de }, regas: 2, nota: "x" } }; return { data: [] }; }
      if (n === "api_dados") { if (a.p_tipo === "resumo") return { data: { periodo: { de: a.p_de }, regas: 2, nota: "x" } }; return { data: [] }; }
      return { error: { message: "?" } };
    },
    auth: { getUser: async (t: string) => t.startsWith("tok-dalmar") ? { data: { user: { id: "u-dalmar" } } } : { data: null, error: { message: "x" } } },
    storage: { from: (b: string) => ({ createSignedUrl: async (c: string) => ({ data: { signedUrl: `https://sig/${b}/${c}` } }),
      download: async () => ({ data: new Blob([new Uint8Array([255, 216, 255, 1])]) }) }) },
  };
}
