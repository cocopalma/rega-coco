# Teste do conector (função dados-rega) com um servidor simulado

O `mock.ts` substitui o supabase-js (RPC, auth e storage simulados; utilizador `tok-dalmar` → perfil `u-dalmar`).

    cd testes/conector
    tail -n +2 ../../supabase/functions/dados-rega/index.ts > fn.ts
    SUPABASE_URL=http://localhost:8000 SUPABASE_SERVICE_ROLE_KEY=x deno run -A fn.ts &
    deno run -A teste_conector.ts

Cobre: lista de ferramentas, os 12 tipos do painel, filtros, percursos só de um dia, quadro sem acesso,
links de Excel e GeoJSON (tokens não se trocam, assinatura alterada → 401), foto permitida / recusada (api_foto_ok),
lote MCP com mais de 20 pedidos → 429. Não testa o SQL (api_dados2, api_foto_ok, api_painel): esse testa-se no
servidor com rollback antes de publicar.
