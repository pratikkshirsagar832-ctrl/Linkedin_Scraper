import os, httpx

ref = "czszinngluwhytnmdcbq"
key = os.environ['SUPABASE_KEY']

with open("supabase-schema.sql") as f:
    sql = f.read()

# Try pg_query extension endpoint
r = httpx.post(
    f"https://{ref}.supabase.co/pg_query/v1/",
    headers={"apikey": key, "Authorization": f"Bearer {key}"},
    json={"query": sql}
)
print(f"pg_query: {r.status_code} {r.text[:400]}")

# Try rest/v1/ with SQL as RPC
r2 = httpx.post(
    f"https://{ref}.supabase.co/rest/v1/",
    params={"query": sql[:200]},
    headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"},
    json={}
)
print(f"rest/v1: {r2.status_code} {r2.text[:400]}")

# Try supabase_db_query RPC
r3 = httpx.post(
    f"https://{ref}.supabase.co/rest/v1/rpc/supabase_db_query",
    headers={"apikey": key, "Authorization": f"Bearer {key}"},
    json={"query_text": sql}
)
print(f"supabase_db_query: {r3.status_code} {r3.text[:400]}")
